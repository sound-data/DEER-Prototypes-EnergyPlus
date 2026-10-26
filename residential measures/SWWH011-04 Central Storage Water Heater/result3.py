#!/usr/bin/env python
# coding: utf-8

"""EnergyPlus batch results data scraping tool, including DEER peak period.

Features:
* Read from instance-out.sql files using result spec format like modelkit
* Apply DEER peak period calculation to hourly results and include those.
* Requires python >= 3.7.1 and additional package "tqdm"
* Note that given two queries with the same output name, the behavior is undefined.

Usage:
    Prerequisite: running models, select a query file, path to DEER peak period definitions
    $terminal1> cd C:/DEER-Prototypes-EnergyPlus/
    $terminal1> python "scripts/result2.py" "commercial measures/SWXX000-00 Measure Name" --queryfile "querylibrary/query_default.txt"

Changelog
    * 2024-05-01 Adapted result.py for DEER Peak period calculation
    * 2024-05-15 Filename patterns updated to match folders like runs1, runs-Asm, etc.
    * 2025-01-07 Apply DEER Peak calculation more selectively
    * 2025-07-24 Filename pattern matching revised for better consistency between different conventions
    * 2026-01-19 Column names updated to improve consistency across models
    * 2026-03-03 Added options for DEER Peak demand: E-5152 (original behavior) and E-5350
    * 2026-04-19 Set DEER Peak default to CZ2025
    * 2026-07-21 Fixed peak demand extraction issue which returned None whenever
                 extra rows present in hourly data (design days and warmup).

@Author: Nicholas Fette <nfette@solaris-technical.com>
@Author: Safia Sheerin
@Date: 2024-05-01

"""

# Select columns from hourly files to apply DEER peak calculation
DEERPEAK_COLUMNS = ["Electricity:Facility [J](Hourly)"]
# Peak period versions to use for DEER peak calculation.
PEAK_VERSION = ['E5152', 'E5350', 'CZ2025']

# Select columns from hourly files to save into sim_hourly.
# None means save all hourly variables from ReportDataDictionary/ReportData.
HOURLY_COLUMNS = None

##STEP 0: Setup (import all necessary libraries)
import re
from dataclasses import dataclass, asdict
from sqlite3 import connect, Connection
from pathlib import Path
from functools import cache
import argparse
import atexit
import logging
import multiprocessing
import concurrent.futures
from logging.handlers import QueueHandler, QueueListener

try:
    # itertools.batched available only after python 3.12
    from itertools import batched
except:
    from itertools import islice
    def batched(iterable, n):
        # batched('ABCDEFG', 3) → ABC DEF G
        if n < 1:
            raise ValueError('n must be at least one')
        it = iter(iterable)
        while batch := tuple(islice(it, n)):
            yield batch

# Third-party packages
import numpy as np
import pandas as pd
import tqdm

# Configure logging for warnings and other messages in the script.
# Listener and handler are used to route logging messages from
# worker processes to a single file handler in the main process.
log = logging.getLogger(__name__)
_LOG_QUEUE = None
_LOG_LISTENER = None
_LOG_FILE_HANDLER = None

def configure_logging(logfile: Path = Path('result2.log')):
    """Configure file-based logging for the CLI script and worker processes."""
    global _LOG_QUEUE, _LOG_LISTENER, _LOG_FILE_HANDLER

    logfile = Path(logfile)
    logfile.parent.mkdir(parents=True, exist_ok=True)

    if _LOG_QUEUE is None:
        _LOG_QUEUE = multiprocessing.Queue()

    if _LOG_LISTENER is None:
        _LOG_FILE_HANDLER = logging.FileHandler(logfile, mode='w')
        _LOG_FILE_HANDLER.setFormatter(
            logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        )
        _LOG_LISTENER = QueueListener(
            _LOG_QUEUE,
            _LOG_FILE_HANDLER,
            respect_handler_level=True,
        )
        _LOG_LISTENER.start()

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(QueueHandler(_LOG_QUEUE))
    root_logger.propagate = False

    return logging.getLogger(__name__)

def _configure_worker_logging(queue):
    """Attach the worker process logger to a multiprocessing queue."""
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(QueueHandler(queue))
    root_logger.propagate = False

def _stop_logging():
    """Stop the queue listener and close any file/queue resources safely."""
    global _LOG_LISTENER, _LOG_FILE_HANDLER, _LOG_QUEUE

    if _LOG_LISTENER is not None:
        _LOG_LISTENER.stop()
    _LOG_LISTENER = None

    if _LOG_FILE_HANDLER is not None:
        _LOG_FILE_HANDLER.close()
    _LOG_FILE_HANDLER = None
 
    if _LOG_QUEUE is not None:
        _LOG_QUEUE.close()
        _LOG_QUEUE.join_thread()
    _LOG_QUEUE = None

atexit.register(_stop_logging)


## Functions for DEER peak period calculation, based on climate zone and version of DEER definition.
def get_deer_peak_day_E5152(bldgloc: str):
    """Return a for DEER peak period start day lookups.
    Dates are from Resolution E-5152 (DEER2023) Attachment A, Table A-3-2.
    The dates were derived using CZ2022 weather data.

    Input:
        BldgLoc: str
            CEC climate zone, e.g. CZ01 through CZ16.

    Returns:
        PkDay: int
            1-based day number index for first day of the 3-day DEER peak period.
    """
    peakperspec = dict([
        ("CZ01",238),
        ("CZ02",238),
        ("CZ03",238),
        ("CZ04",238),
        ("CZ05",259),
        ("CZ06",245),
        ("CZ07",245),
        ("CZ08",245),
        ("CZ09",244),
        ("CZ10",180),
        ("CZ11",180),
        ("CZ12",180),
        ("CZ13",180),
        ("CZ14",180),
        ("CZ15",180),
        ("CZ16",224),
    ])
    return peakperspec[bldgloc]

def get_deer_peak_day_E5350(bldgloc: str):
    """Return a for DEER peak period start day lookups.
    Dates are from Resolution E-5350 (DEER2026) Attachment A, Table A-1-5.
    The dates were derived using CZ2022 weather data.

    Input:
        BldgLoc: str
            CEC climate zone, e.g. CZ01 through CZ16.

    Returns:
        PkDay: int
            1-based day number index for first day of the 3-day DEER peak period.
    """
    peakperspec = dict([
        ("CZ01",238),
        ("CZ02",238),
        ("CZ03",238),
        ("CZ04",238),
        ("CZ05",259),
        ("CZ06",180),
        ("CZ07",245),
        ("CZ08",245),
        ("CZ09",245),
        ("CZ10",180),
        ("CZ11",224),
        ("CZ12",180),
        ("CZ13",180),
        ("CZ14",180),
        ("CZ15",180),
        ("CZ16",224),
    ])
    return peakperspec[bldgloc]

def get_deer_peak_day_CZ2025(bldgloc: str):
    """Return a for DEER peak period start day lookups.
    Dates are from CPUC assessment posted to CEDARS on 2026-03-10.
    See https://cedars.cpuc.ca.gov/deer-resources/tools/energy-plus/resource/29/history/
    The dates were derived using CZ2025 weather data.

    Input:
        BldgLoc: str
            CEC climate zone, e.g. CZ01 through CZ16.

    Returns:
        PkDay: int
            1-based day number index for first day of the 3-day DEER peak period.
    """
    peakperspec = dict([
        ("CZ01",266),
        ("CZ02",203),
        ("CZ03",266),
        ("CZ04",217),
        ("CZ05",266),
        ("CZ06",266),
        ("CZ07",271),
        ("CZ08",168),
        ("CZ09",168),
        ("CZ10",168),
        ("CZ11",187),
        ("CZ12",217),
        ("CZ13",187),
        ("CZ14",187),
        ("CZ15",238),
        ("CZ16",187),
    ])
    return peakperspec[bldgloc]

# Lookup table for DEER peak period start day functions.
DEER_PEAK_DAY_LOOKUP = {
'E5152': get_deer_peak_day_E5152,
'E5350': get_deer_peak_day_E5350,
'CZ2025': get_deer_peak_day_CZ2025,
}

@cache
def get_deer_peak_multipliers(BldgLoc: str,
                              version: str,
                              days=3,
                              start_hr=16,
                              end_hr=21,
                              dst=True):
    """Return a masking array useful to calculate an average over DEER Peak Period.

    Note that for compatibility, simulation data must be an 8760-length array
    that represents one annual period (no gaps or duplicates due to dst).

    Inputs:
        BldgLoc: str
            CEC climate zone, e.g. CZ01 through CZ16.
        version: str
            Which definition of peak period dates to use.
        days: int
            The number of days in the DEER Peak Period (default 3)
        start_hr: int
            The time of day (hour) at which DEER Peak starts, in prevailing time.
            For example, start_hr=16 means the DEER Peak starts at 4 PM.
        end_hr: int
            The time of day (hour) at which DEER Peak ends, in prevailing time.
            For example, start_hr=21 means the DEER Peak ends at 9 PM.
        dst: bool
            Clarifies the interpretation of start_hr.
            If dst = False, then no adjustment is made for start_hr.
            If dst = True, then assume Daylight Saving Time is active
            during the DEER Peak, and make the appropriate offset.

    Usage:
        load_data = get_load_8760('CZ11', ...) # replace with your load data as a np.ndarray
        dpm = deer_peak_multipliers('CZ11')
        dpload = sum(load_data * dpm)
    """
    try:
        peak_day = DEER_PEAK_DAY_LOOKUP[version](BldgLoc)
    except KeyError as exc:
        raise ValueError(f'Unrecognized peak date version: {version}') from exc

    # In case start_hr and end_hr are given in daylight saving time (DST), shift back to standard time.
    # time_dst = time_standard + 1
    start_hr -= 1 * dst
    end_hr -= 1 * dst
    # Fill an array with 0-based hour of year.
    hour_of_year = np.arange(0,8760)
    # Calculate 0-based hour and day (standard time; this is never DST).
    hour_of_day_0 = np.mod(hour_of_year, 24)
    day_of_year_0 = np.mod(hour_of_year//24, 365)
    # Calculate 1-based hour and day (matches conventions of DEER post-process script).
    hour_of_day_1 = hour_of_day_0 + 1
    day_of_year_1 = day_of_year_0 + 1
    # Is the hour in the DEER Peak period?
    is_deer_peak_day = (day_of_year_1 >= peak_day) * (day_of_year_1 <= peak_day + days)
    is_deer_peak_hour = (hour_of_day_0 >= start_hr) * (hour_of_day_0 < end_hr)
    is_deer_peak = is_deer_peak_day * is_deer_peak_hour
    # Normalize
    multipliers8760 = is_deer_peak / sum(is_deer_peak)
    return multipliers8760

@dataclass
class ResultSpec(object):
    ReportName: str
    ReportForString: str
    TableName: str
    ColumnName: str
    RowName: str

    def to_string(self):
        return "{ReportName}/{ReportForString}/{TableName}/{ColumnName}/{RowName}".format(**asdict(self))

def makeResultSpec(specstr: str) -> ResultSpec:
    fields = specstr.split('/')
    return ResultSpec(*fields)

@cache
def parse_query_file(queryfile: Path):
    """Reads the query.txt file and returns a list of tuples (resultspec, name)
    where
        resultspec is a ResultSpec object
        name is the name to assign to output.

    If name is ommitted in the query.txt, name will be like "ColumnName/RowName".
    """
    if not isinstance(queryfile, Path):
        queryfile = Path(queryfile)

    listlist_query_path_and_name = []
    list_query_path_and_name = []
    lines = queryfile.read_text().split('\n')
    for query_line in lines:
        # Blank line indicates a new group
        if len(query_line.strip()) == 0:
            if list_query_path_and_name != []:
                listlist_query_path_and_name.append(list_query_path_and_name)
                list_query_path_and_name = []
            continue
        if query_line.startswith("#"):
            continue
        m = re.match(r'\s*(.+)\s*,\s*(.+)\s*',query_line)
        if m:
            query_path, user_column_name = m.groups()
            resultspec = makeResultSpec(query_path)
        else:
            query_path = query_line.strip()
            resultspec = makeResultSpec(query_path)
            user_column_name = "{ColumnName}/{RowName}".format(**asdict(resultspec))
        list_query_path_and_name.append((resultspec, user_column_name))
    if list_query_path_and_name != []:
        listlist_query_path_and_name.append(list_query_path_and_name)
    return listlist_query_path_and_name

def build_query_with_special_cases(resultspec: ResultSpec, finalize = True) -> str:
    """Returns SQLite query that can be executed to extract results from EnergyPlus tabular reports.

    Special cases:
        For compatibility with modelkit queries, "Total Energy" is emulated as follows.
            AnnualBuildingUtilityPerformanceSummary/Entire Facility/End Uses/Total Energy/X
        translates to
            AnnualBuildingUtilityPerformanceSummary/Entire Facility/End Uses/*/X where ColumnName <> Water.

    Inputs:
        resultspec: ResultSpec
            A ResultSpec object or modelkit-style query path to transform into an SQLite query.
        finalize: bool, default True
            Whether to terminate the query with a semicolon (;)

    Returns:
        query:
            SQLite query string (e.g. SELECT * from TabularDataWithStrings WHERE ...).
        agg_columns: list[str]
            List of columns in which the query includes a wildcard (*), useful to aggregate the results.
    """
    TOKEN_ANY = '*'
    #TABULAR_DATA_HEADERS = ['ReportName', 'ReportForString',
    #    'TableName', 'ColumnName', 'RowName']

    if not isinstance(resultspec, ResultSpec):
        resultspec = makeResultSpec(resultspec)

    if resultspec.to_string().startswith("AnnualBuildingUtilityPerformanceSummary/Entire Facility/End Uses/Total Energy/"):
        # Special case. 'Total Energy' is a synthetic result not defined by EnergyPlus.
        # It is not a good idea to use this because it is adding quantities with different meanings (kWh electric + kWh gas, etc).
        if resultspec.RowName == TOKEN_ANY:
            query,agg_columns = build_query_with_special_cases(
                "AnnualBuildingUtilityPerformanceSummary/Entire Facility/End Uses/*/*",
                False)
            query += """ AND ColumnName <> 'Water';"""
            return query,agg_columns
        else:
            query,agg_columns = build_query_with_special_cases(
                f"AnnualBuildingUtilityPerformanceSummary/Entire Facility/End Uses/*/{resultspec.RowName}",
                False)
            query += """ AND ColumnName <> 'Water';"""
            return query,agg_columns

    agg_columns = ['ReportName']
    query = """SELECT * from TabularDataWithStrings
                WHERE ReportName = :ReportName"""

    if (resultspec.ReportForString and resultspec.ReportForString != TOKEN_ANY):
        query += " AND ReportForString = :ReportForString"
        agg_columns.append('ReportForString')

    if (resultspec.TableName and resultspec.TableName != TOKEN_ANY):
        query += " AND TableName = :TableName"
        agg_columns.append('TableName')

    if (resultspec.ColumnName and resultspec.ColumnName != TOKEN_ANY):
        query += " AND ColumnName = :ColumnName"
        agg_columns.append('ColumnName')

    if (resultspec.RowName and resultspec.RowName != TOKEN_ANY):
        query += " AND RowName = :RowName"
        agg_columns.append('ReportForString')

    if finalize:
        query += ";"
    agg_columns.append('Units')
    return query, agg_columns

def get_sim_hourly(conn: Connection, column_filter=None):
    """Get simulation hourly results from one EnergyPlus SQLite output file.

    Inputs:
        conn: sqlite3.Connection | str
            Database file connection or string path to EnergyPlus SQLite output file.
            Note that this function does not read CSV output files.
        column_filter: None | List[str]
            List of hourly output column names to include.
            If None, all output columns in the file are included.

    Returns:
        ReportDataWide: pandas.DataFrame
            Table with shape (N,8760) where each of N rows represent an hourly variable
            and each of 8760 columns represents one hour of an annual simulation period.
            Names of hourly variables in the index column follow the EnergyPlus CSV output convention.

    Example

        >>> with connect('instance-out.sql') as conn:
                ReportDataWide = get_hourly_results_deer(conn, 'CZ11')
        >>> ReportDataWide
            TimeIndex                                                      1            2                8760
            LookupKey
            Electricity:Facility [J](Hourly)                               5.222829e+07 4.893178e+07 ... 5.366953e+07
            Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)   5.358333e+00 5.841667e+00 ... 5.575000e+00

    Technical details:
        Implementation joins the ReportDataDictionary and ReportData tables.
        LookupKey returned
        Requires that the EnergyPlus model contains an OutputControl:Files object with SQLite = Yes.
    """
    ReportDataDictionary = pd.read_sql_query('select * from ReportDataDictionary', conn, index_col='ReportDataDictionaryIndex')

    # Transform ReportDataDictionary so we have a single column lookup string.
    # LookupKey looks like:
    #   If 'EL7 NORTH PERIM ZN (G.N2):Zone Total Internal Total Heating Energy [J](Hourly)'
    # LookupKey looks like 'EL7 NORTH PERIM ZN (G.N2):Zone Total Internal Total Heating Energy [J](Hourly)'
    ReportDataDictionary['LookupKey']=ReportDataDictionary.apply(
        lambda x: f'{x.KeyValue}:{x.Name} [{x.Units}]({x.ReportingFrequency})' if bool(x.KeyValue)
        else f'{x.Name} [{x.Units}]({x.ReportingFrequency})'
        , axis=1)

    # Begin preparing a SQLite query to retrieve the relevant ReportData rows based on the column filter and time filter.
    # If a column filter is provided, we need to filter the ReportData table to only include the relevant columns.
    rd_indices = []
    column_filter_clause = ''
    if column_filter:
        # Construct a list of ReportDataDictionaryIndex values from column_filter.
        # Note that ReportDataDictionaryIndex values are file-specific.
        rd_indices = ReportDataDictionary[ReportDataDictionary['LookupKey'].isin(column_filter)].index
        placeholders = ', '.join(['?'] * len(rd_indices))
        column_filter_clause = f''' AND rd."ReportDataDictionaryIndex" IN ({placeholders})'''
        # Note: changed from WHERE to AND because query already has WHERE clause

    # Note: filter DayType to only include the seven days of the week plus holidays,
    # excluding design days and warmup periods.

    # Construct the ORDER BY clause for the SQL query. This ensures that the results are returned in a logical order.
    order_by_clause = ' ORDER BY rd.ReportDataDictionaryIndex, rd.TimeIndex'

    query_report_data = f'''
        SELECT rd.*
        FROM ReportData rd
        JOIN Time t ON rd.TimeIndex = t.TimeIndex
        WHERE t.DayType IN (
            'Sunday', 'Monday', 'Tuesday', 'Wednesday',
            'Thursday', 'Friday', 'Saturday', 'Holiday'
        )
        {column_filter_clause}
        {order_by_clause}
    '''

    chunks = []
    for chunk in pd.read_sql_query(query_report_data, conn, chunksize=10000,
                                   params=tuple(rd_indices) if column_filter else None):
        chunks.append(chunk)
    ReportData = pd.concat(chunks, axis=0)

    # Join the tables ReportData (values) and ReportDataDictionary (variable names and units).
    ReportData2 = ReportData.join(ReportDataDictionary, on='ReportDataDictionaryIndex')

    # Transform ReportData from long to wide so we can make a condensed table
    ReportDataWide = ReportData2.pivot(index='LookupKey', columns='TimeIndex', values='Value')

    return ReportDataWide

def get_sim_hourly_blob(conn, simID):
    """Return sim_hourly rows with hourly values stored as a BLOB."""

    ReportDataWide = get_sim_hourly(conn)

    if ReportDataWide is None or ReportDataWide.empty:
        return pd.DataFrame(columns=["SimID", "VarName", "VarVal"])

    rows = []

    for varname, values in ReportDataWide.iterrows():
        rows.append({
            "SimID": simID,
            "VarName": varname,
            "VarVal": values.to_numpy(dtype=np.float64).tobytes()
        })

    return pd.DataFrame(rows)

def get_sim_deer_peak_long(
        conn: Connection,
        bldgloc: str,
        simID: str,
        column_filter=DEERPEAK_COLUMNS,
        versions=PEAK_VERSION):
    """Calculate DEER peak demand for all requested versions and return long data.

    Output table columns:
        simID
            Join key.
        VarName
            Hourly variable name, such as Electricity:Facility [J](Hourly).
        Version
            Peak-period definition, such as E5152, E5350, or CZ2025.
        PeakDemand_kW
            Average demand over the DEER peak period, converted from hourly J.
    """

    empty_cols = [
        'simID',
        'VarName',
        'Version',
        'PeakDemand_kW'
    ]

    # Load hourly data once for this simulation file.
    ReportDataWide = get_sim_hourly(conn, column_filter=column_filter)

    # Sizing runs, failed runs, or files without the requested hourly columns may not have 8760 hours.
    if ReportDataWide is None or ReportDataWide.empty or ReportDataWide.shape[1] != 8760:
        return pd.DataFrame(columns=empty_cols)

    records = []

    for version in versions:
        dpm = get_deer_peak_multipliers(bldgloc, version=version)
        peak_values_raw = ReportDataWide.to_numpy().dot(dpm)

        for varname, peak_value_raw in zip(ReportDataWide.index, peak_values_raw):
            # EnergyPlus hourly electricity variables reported as [J](Hourly)
            # are energy per one-hour reporting interval.
            # Average demand in kW = average J per hour / 3,600,000 J per kWh.
            if '[J](Hourly)' in varname:
                peak_demand_kw = peak_value_raw / 3_600_000
            else:
                # Do not force non-J hourly variables into kW.
                peak_demand_kw = None

            records.append({
                'simID': simID,
                'VarName': varname,
                'Version': version,
                'PeakDemand_kW': peak_demand_kw,
            })

    return pd.DataFrame.from_records(records, columns=empty_cols)

def get_sim_tabular(
        conn: Connection,
        resultspec: ResultSpec,
        aggtype = 'sum'
        ) -> tuple:
    """Returns result information based on a single query from tabular reports.

    Inputs:
        conn: sqlite3.Connection
            Open connection to the model instance results database (e.g. instance-out.sql)

        aggtype: str
            Aggregation type, e.g. sum. Explains how to combine multiple values where
            the query includes a wildcard (*).

    Returns (sim_data_detail, sim_data_agg) where:
        sim_data_detail: pandas.DataFrame or None
            DataFrame of raw results from the model, possibly including multiple rows in case of a wildcard.
        sim_data_agg: float or None
            Single value. In case of wildcard in query, this is calculated according to aggtype.
    """
    if not isinstance(resultspec, ResultSpec):
        resultspec = makeResultSpec(resultspec)
    query, agg_columns = build_query_with_special_cases(resultspec)

    try:
        sim_data_detail = pd.read_sql_query(query, conn,  params=asdict(resultspec), dtype={'Value':float})
    except ValueError:
        # If user requested a query that returns a string value
        # To do: aggregation doesn't work with string type results.
        sim_data_detail = pd.read_sql_query(query, conn,  params=asdict(resultspec))

    if sim_data_detail.empty:
        # No data found matching result spec
        return None, None
    elif len(sim_data_detail) == 1:
        # Only one value, no aggregation required
        return sim_data_detail, sim_data_detail.loc[0,'Value']
    else:
        # Aggregation requested. Calculate a single float value.
        sim_data_agg = (
            sim_data_detail
            .groupby(agg_columns)
            ['Value'].agg(aggtype).iloc[0]
        )
        return sim_data_detail, sim_data_agg

def get_sim_tabular_long(
        queryfile: Path,
        sqlfile: Path,
        ):
    r"""
    Read selected data entries from SQL outputs.
    Result set specifications are parsed from query.txt, e.g. (resultspec, name).
    Output columns will have units appended to name, like "name (Units)".

    Inputs:
        queryfile: Path
            The filename of a modelkit-style query.txt file.
        sqlfile: Path
            The filename of an EnergyPlus output file (SQLite format).

    Returns:
        sim_data_detail: DataFrame.
            Subset of TabularDataWithStrings rows matching result set query.
    """
    with connect(sqlfile) as conn:
        # Start with the query data results
        listlist_query_path_and_name = parse_query_file(queryfile)
        tabular_data_list = []

        # Don't separate "groups" of queries but group them all together.
        for list_query_path_and_name in listlist_query_path_and_name:
            for resultspec, user_column_name in list_query_path_and_name:

                if not isinstance(resultspec, ResultSpec):
                    resultspec = makeResultSpec(resultspec)

                query, agg_columns = build_query_with_special_cases(resultspec)

                sim_data_detail1 = pd.read_sql_query(query, conn,  params=asdict(resultspec))

                tabular_data_list.append(sim_data_detail1)

    tabular_data = pd.concat(tabular_data_list)

    return tabular_data

def get_sim_data_long(queryfile: Path,
                             sqlfile: Path):
    r"""
    Read selected data entries from SQL outputs.
    Result set specifications are parsed from query.txt, e.g. (resultspec, name).

    Inputs:
        queryfile: Path
            The filename of a modelkit-style query.txt file.
        sqlfile: Path
            The filename of an EnergyPlus output file (SQLite format).

    Returns:
        sim_data: dict(str: float | None).
            Mapping of (name, value) from query results.
    """
    sim_data = {} # To store results
    with connect(sqlfile) as conn:
        # Start with the query data results
        listlist_query_path_and_name = parse_query_file(queryfile)
        # Don't separate "groups" of queries but group them all together.
        # result_sets = []
        for list_query_path_and_name in listlist_query_path_and_name:
            # Don't separate "groups" of queries but group them all together.
            # sim_data_detail, sim_data_agg = [], []
            for resultspec, user_column_name in list_query_path_and_name:
                # 2025-01-22 Updated Nicholas Fette
                # Default to the column name from the result query without attempting to append unit symbol from results.
                # This avoids errors due to mismatched column names when a file is missing one or more results.
                # Useful for concatenating results in a wide-format table.
                output_column_name = user_column_name

                sim_data_detail1, sim_data_agg1 = get_sim_tabular(conn, resultspec)
                if sim_data_detail1 is None:
                    # No data found matching the result spec.
                    # 2025-01-22 Updated Nicholas Fette
                    # For consistency between files, store a None/NULL result for this column.
                    # To-do: In sqlite output mode, pandas may not be able to guess the dtype.
                    # As a workaround, user may manually alter the sim_data table column types, then run the script.
                    sim_data.update({output_column_name: None})
                    continue
                # This script does not compile detail of all rows included in wildcard queries:
                #sim_data_detail.append(sim_data_detail1)
                if sim_data_agg1 is not None:
                    sim_data.update({output_column_name: sim_data_agg1})
            #sim_data_agg.append(sizing_agg_row)

    return sim_data

def get_runs_instances(study: Path, search_pattern = '**/instance*-out.sql', exclude = 'instance-size-out.sql'):
    r"""Returns a list of all of SQLite output files in a modelkit study folder.

    Assumes that files are placed within a "runs" subfolder under the given study.

    Inputs:
        study: pathlib.Path
            The folder in which to search for simulation outputs.
            E.g. old style: "C:\Users\User1\DEER-Prototypes-EnergyPlus\Analysis\SFm_Furnace_1975"
            E.g. new style: "C:\Users\User1\DEER-Prototypes-EnergyPlus\commercial measures\SWHC012-04 Occupancy Sensor"
        search_pattern: str, default = 'instance*-out.sql'
            The filename pattern used to search for output files, using glob syntax.
        exclude_pattern: str, default = 'instance-size-out.sql'
            A filename pattern to exclude.

    Returns: list of tuples (sqlfile, bldgloc, metadata) where
        sqlfile: pathlib.Path
            An EnergyPlus SQLite output file found in the study folder.
        bldgloc: str
            CEC Climate zone found in file name.
        metadata: dict

        Default metadata fields:
            'File Name'
                File path relative to study folder, with forward slashes.
            'BldgLoc'
                CEC Climate Zone (CZ01, CZ02, ..., CZ16)
            'BldgType'
                Prototype name code (Asm, ... SUn)
            'Story'
                Number of stories (1 or 2 for single family, 0 for all other building types)
            'BldgHVAC'
                HVAC type code found in cohort name (rDXGF, ...)
            'BldgVint'
                Vintage code found in cohort name (Ex, New)
            'TechGroup'
                Technology group found in cohort name (SpaceHtg_eq, ...)
            'TechType'
                Technology type found in cohort name (GasFurnace, ...)
            'TechID'
                Name for a set of input parameters , a.k.a. case_name (Msr-Res-GasFurnace-AFUE95-ECM)
            'Cohort'
                The entire cohort name (SFm&1&rDXGF&Ex&SpaceHtg_eq__GasFurnace)
            'Case'
                The case name
    """
    if not isinstance(study, Path):
        study = Path(study)
    # Note that autosized runs are named instance-out.sql.
    # Linked-sizing runs are named instance-hardsize-out.sql.
    # Sizing-only runs are named instance-size-out.sql.
    for sqlfile in study.glob(search_pattern):
        if sqlfile.match(exclude):
            continue
        relpath = sqlfile.relative_to(study)
        # E.g. relpath = Path(r"runs\CZ01\SFm&1&rDXGF&Ex&SpaceHtg_eq__GasFurnace\Msr-Res-GasFurnace-AFUE95-ECM\instance-out.sql")
        relstr = relpath.as_posix() # with forward slashes
        # E.g. relstr = "runs/CZ01/SFm&1&rDXGF&Ex&SpaceHtg_eq__GasFurnace/Msr-Res-GasFurnace-AFUE95-ECM/instance-out.sql"
        # Search string for climate zone like 'CZ11/'.
        m = re.search(r"CZ\d\d(?=/)", relstr)
        if not m:
            raise ValueError(f'Could not match climate zone in filename: "{relstr}"')
        bldgloc = m[0]

        metadata = {}
        # For compatibility with modelkit, may want to remove 'runs/' prefix.
        # E.g. filename = "CZ01/SFm&1&rDXGF&Ex&SpaceHtg_eq__GasFurnace/Msr-Res-GasFurnace-AFUE95-ECM/instance-out.sql"
        # pathsub = (r'runs/','')
        #metadata['File Name'] = re.sub(*pathsub, relstr, 1)
        metadata['simID'] = relstr
        metadata['File Name'] = relstr
        metadata['BldgLoc'] = bldgloc
        metadata['BldgType'] = None
        metadata['Story'] = None
        metadata['BldgHVAC'] = None
        metadata['BldgVint'] = None
        metadata['TechGroup'] = None
        metadata['TechType'] = None
        metadata['TechID'] = None
        metadata['Cohort'] = None
        metadata['Case'] = None

        # Try to get additional metadata, but don't fail if it doesn't match.
        patterns = [
            r'(.*/)?runs[^/]*/(?P<BldgLoc>CZ\d\d)/(?P<Cohort>[^/]+)/(?P<Case>[^/]+)/instance.*',
            r'(.*/)?runs[^/]*/(?P<BldgLoc>CZ\d\d)/(?P<BldgType>\w+)&(?P<Story>\w+)&(?P<BldgHVAC>\w+)&(?P<BldgVint>[\w\-]+)&(?P<TechGroup>[\w\-]+)/(?P<TechID>[^/]+)/instance.*',
            r'(.*/)?runs[^/]*/(?P<BldgLoc>CZ\d\d)/(?P<BldgType>\w+)&(?P<Story>\w+)&(?P<BldgHVAC>\w+)&(?P<BldgVint>[\w\-]+)&(?P<TechGroup>[\w\-]+)__(?P<TechType>[\w\-]+)/(?P<TechID>[^/]+)/instance.*',
            r'(.*/)?runs[^/]*/(?P<BldgLoc>CZ\d\d)/(?P<BldgType>\w+)&(?P<Story>\w+)&(?P<BldgHVAC>\w+)&(?P<BldgVint>[\w\-]+)&(?P<TechGroupUnused>[\w\-]+)__(?P<TechTypeUnused>[\w\-]+)&(?P<TechGroup>[\w\-]+)__(?P<TechType>[\w\-]+)/(?P<TechID>[^/]+)/instance.*',
        ]
        for pattern in patterns:
            m2 = re.match(pattern, relstr)
            if m2:
                sim_metadata = m2.groupdict()
                sim_metadata.pop('TechGroupUnused', None)
                sim_metadata.pop('TechTypeUnused', None)
                metadata.update(sim_metadata)
        yield (sqlfile, bldgloc, metadata)

def gather_sim_data_long(study: Path, queryfile: Path, parallel=False):
    r"""Returns a generator yielding simulation data from each simulation in long table format.

    Read selected data entries from SQL outputs as well as DEER Peak period averages of hourly variables.
    Result set specifications are parsed from query.txt, e.g. (resultspec, name).
    Output columns will have units appended to name, like "name (Units)".

    Assumes that files are placed within a "runs" subfolder under the given study.

    study: e.g., "C:\Users\User1\DEER-Prototypes-EnergyPlus\Analysis\SFm_Furnace_1975"

    Returns:
        Generator yielding dictionary objects.

    Example:
        >>> for sim_data in gather_sim_data(sqlfile, queryfile):
        >>>    pass
        >>> sim_data
        {
            "File Name": "mymeasure_vintage/CZ01/cohort/case/instance-out.sql",
            "Net Site EUI (kWh/m2)": 90.97,
            "Electricity:Facility [J](Hourly)": 3738615573
        }
    """
    log.info(f"Reading from {study}")
    # Make sure queryfile does not give an error before starting main loop.
    _ = parse_query_file(queryfile)

    if not parallel:
        for sqlfile, bldgloc, metadata in tqdm.tqdm(list(get_runs_instances(study))):
            # Start the load operations and mark each future with its input arguments.
            sim_data = get_sim_data_long(queryfile, sqlfile)
            yield (sqlfile, bldgloc, metadata, sim_data)
    else:
        list_sqlfile = list(get_runs_instances(study))
        # Use a concurrent.futures.Executor to achieve some parallelism.
        # This should speed up the process if there are a large number of files.
        # In initial testing, ThreadPoolExecutor was 0.5x the speed of a single-threaded loop.
        # However, ProcessPoolExecutor was 3-4x the speed of a single-threaded loop.
        #with concurrent.futures.ThreadPoolExecutor() as executor:
        with concurrent.futures.ProcessPoolExecutor(
            initializer=_configure_worker_logging,
            initargs=(_LOG_QUEUE,),
        ) as executor:
            log.info(f"Created a process pool with {executor._max_workers} workers")
            future_lookup = dict() # Remember each file when requested.
            # Queue each operation to read simulation data, returning a future.
            for (sqlfile, bldgloc, metadata) in list_sqlfile:
                # Start the load operations and mark each future with its input arguments.
                future = executor.submit(get_sim_data_long, queryfile, sqlfile)
                future_lookup[future] = (sqlfile, bldgloc, metadata)

            # Wait for futures to complete and show a progress bar.
            import time
            for i,future in zip(
                tqdm.trange(len(list_sqlfile), desc=study.name), # progress bar
                concurrent.futures.as_completed(future_lookup)  # waiting for results from parallel threads
            ):
                (sqlfile, bldgloc, metadata) = future_lookup[future]
                try:
                    sim_data = future.result()
                except Exception as exc:
                    log.exception(f'Reading {sqlfile} generated an exception: {exc}')
                else:
                    yield (sqlfile, bldgloc, metadata, sim_data)
                    time.sleep(0.001)

"NORM UNITS CHUNK START"
def normalize_match_key(series: pd.Series) -> pd.Series:
    """Strip whitespace and make Excel/EnergyPlus merge keys case-insensitive."""
    return series.astype("string").str.strip().str.casefold()

def read_coil_list(
    coil_list_file: Path,
    sheet_name=0,
) -> pd.DataFrame:
    """Read and validate the coil-list workbook.

    Required columns:
        cooling coil name
        building type
    """
    coil_list = pd.read_excel(
        coil_list_file,
        sheet_name=sheet_name,
        engine="openpyxl",
    )

    required_columns = {"cooling coil name", "building type"}
    missing_columns = required_columns.difference(coil_list.columns)
    if missing_columns:
        raise ValueError(
            "The coil-list workbook is missing required column(s): "
            + ", ".join(sorted(missing_columns))
        )

    coil_list = coil_list.copy()
    coil_list["_CoilNameKey"] = normalize_match_key(
        coil_list["cooling coil name"]
    )
    coil_list["_BuildingTypeKey"] = normalize_match_key(
        coil_list["building type"]
    )

    # Duplicate matching keys would multiply sizing values during the merge.
    return coil_list.drop_duplicates(
        subset=["_CoilNameKey", "_BuildingTypeKey"]
    )

def get_result_sizing_agg(
    conn: Connection,
    queryfile: Path,
    simID: str,
    bldg_type: str,
    coil_list: pd.DataFrame,
    result_name: str = "Cooling Capacity",
) -> pd.DataFrame:
    """Return only the coil-list-filtered sizing aggregate for one simulation.

    Normal query.txt aggregate results are not returned by this function because
    they are already stored in sim_data.

    Output columns:
        simID, ResultName, Units, Value
    """
    output_columns = ["simID", "ResultName", "Units", "Value"]
    sizing_detail_frames = []

    for query_group in parse_query_file(queryfile):
        for resultspec, _user_column_name in query_group:
            detail, _aggregate_value = get_sim_tabular(conn, resultspec)
            if detail is None:
                continue

            detail = detail.copy()
            detail["Value"] = pd.to_numeric(detail["Value"], errors="coerce")
            detail = detail.dropna(subset=["Value", "RowName"])
            if not detail.empty:
                sizing_detail_frames.append(detail)

    if not sizing_detail_frames:
        return pd.DataFrame(columns=output_columns)

    sizing_detail = pd.concat(sizing_detail_frames, ignore_index=True)
    sizing_detail["_CoilNameKey"] = normalize_match_key(
        sizing_detail["RowName"]
    )
    sizing_detail["_BuildingTypeKey"] = str(bldg_type).strip().casefold()

    # Match EnergyPlus RowName to Excel cooling coil name and the simulation's
    # BldgType to the Excel building type.
    filtered = sizing_detail.merge(
        coil_list[["_CoilNameKey", "_BuildingTypeKey"]],
        on=["_CoilNameKey", "_BuildingTypeKey"],
        how="inner",
        validate="many_to_one",
    )

    if filtered.empty:
        return pd.DataFrame(columns=output_columns)

    # Keep Units in the grouping so unlike quantities cannot be summed together.
    sizing_agg = (
        filtered.groupby("Units", dropna=False)["Value"]
        .sum()
        .reset_index()
    )
    sizing_agg.insert(0, "ResultName", result_name)
    sizing_agg.insert(0, "simID", simID)

    return sizing_agg[output_columns]
"NORM UNITS CHUNK END"

def gather_sim_data_to_sqlite_long(
        study: Path,
        queryfile: Path,
        sqlfile_out: Path,
        coil_list_file: Path = Path("coil_list.xlsx"),
        coil_sheet=0,
        coil_result_name: str = "Cooling Capacity",
        parallel=True,
        include_cooling_coils: bool = False
):
    """Write sim_metadata, sim_data, sim_deerpeak, and sim_hourly to one SQLite database."""

    conn_out = connect(sqlfile_out)

    coil_list = None
    if include_cooling_coils:
        coil_list = read_coil_list(coil_list_file, coil_sheet)

    try:
        with conn_out:
            conn_out.execute('DROP TABLE IF EXISTS "sim_metadata";')
            conn_out.execute('DROP TABLE IF EXISTS "sim_data";')
            conn_out.execute('DROP TABLE IF EXISTS "sim_deerpeak";')
            conn_out.execute('DROP TABLE IF EXISTS "sim_hourly";')
            if include_cooling_coils:
                conn_out.execute('DROP TABLE IF EXISTS "result_sizing_agg";')
                conn_out.execute(
                    """
                    CREATE TABLE result_sizing_agg (
                    simID TEXT,
                    ResultName TEXT,
                    Units TEXT,
                    Value REAL
                    )
                    """
                )

        gather = gather_sim_data_long(study, queryfile, parallel)

        for sqlfile, bldgloc, metadata, sim_data in gather:
            simID = metadata['simID']
            log.debug(f"Processing SQL file: {sqlfile}")
            log.debug(f"metadata: {metadata}")
            log.debug(f"sim_data: {sim_data}")
            df_metadata = pd.DataFrame.from_dict([metadata])

            df_sim_data = pd.DataFrame()
            if sim_data:
                df_sim_data = (pd.DataFrame({'simID': simID,
                                  'VarName': list(sim_data.keys()),
                                  'Value': list(sim_data.values())
                                  }))

            # Calculate long-format DEER peak data and hourly data for this simulation file.
            with connect(sqlfile) as conn_sim:
                deerpeak_data = get_sim_deer_peak_long(
                    conn=conn_sim,
                    bldgloc=bldgloc,
                    simID=simID,
                    column_filter=DEERPEAK_COLUMNS,
                    versions=PEAK_VERSION
                )

                hourly_data = get_sim_hourly_blob(conn_sim, simID)

                sizing_data = pd.DataFrame()
                if include_cooling_coils:
                    sizing_data = get_result_sizing_agg(
                        conn=conn_sim,
                        queryfile=queryfile,
                        simID=simID,
                        bldg_type=metadata["BldgType"],
                        coil_list=coil_list,
                        result_name=coil_result_name
                    )

            with conn_out:
                df_metadata.to_sql(
                    'sim_metadata',
                    conn_out,
                    index=False,
                    if_exists='append'
                )

                if not df_sim_data.empty:
                    df_sim_data.to_sql(
                        'sim_data',
                        conn_out,
                        index=False,
                        if_exists='append'
                    )

                if not deerpeak_data.empty:
                    deerpeak_data.to_sql(
                        'sim_deerpeak',
                        conn_out,
                        index=False,
                        if_exists='append'
                    )


                if not hourly_data.empty:
                    hourly_data.to_sql(
                        'sim_hourly',
                        conn_out,
                        index=False,
                        if_exists='append'
                    )

                if include_cooling_coils and not sizing_data.empty:
                    sizing_data.to_sql(
                        'result_sizing_agg',
                        conn_out,
                        index=False,
                        if_exists='append'
                    )

        # Add indexes after data are loaded.
        with conn_out:
            conn_out.execute(
                'CREATE INDEX IF NOT EXISTS idx_sim_metadata_simID '
                'ON sim_metadata(simID);'
            )
            conn_out.execute(
                'CREATE INDEX IF NOT EXISTS idx_sim_data_lookup '
                'ON sim_data(simID, VarName);'
            )
            conn_out.execute(
                'CREATE INDEX IF NOT EXISTS idx_sim_deerpeak_simID '
                'ON sim_deerpeak(simID);'
            )
            conn_out.execute(
                'CREATE INDEX IF NOT EXISTS idx_sim_deerpeak_lookup '
                'ON sim_deerpeak(simID, VarName, Version);'
            )
            conn_out.execute(
                'CREATE INDEX IF NOT EXISTS idx_sim_hourly_simID '
                'ON sim_hourly(simID);'
            )
            if include_cooling_coils:
                conn_out.execute(
                    'CREATE INDEX IF NOT EXISTS idx_result_sizing_agg_simID '
                    'ON result_sizing_agg(simID);'
                    )
                conn_out.execute(
                    'CREATE INDEX IF NOT EXISTS idx_result_sizing_agg_lookup '
                    'ON result_sizing_agg(simID, ResultName);'
                    )       
    finally:
        conn_out.close()

def build_cli_parser(parser: argparse.ArgumentParser,
                     study_kwargs = {},
                     queryfile_kwargs = {},
                     #outputfile_kwargs = {}
                     ):
    parser.add_argument('study', type=Path, nargs='?', default='.',
                        help=r'Analysis subfolder, e.g. C:\Users\user1\Desktop\DEER-EnergyPlus-Prototypes\Analysis\SFm_Furnace_1975',
                        **study_kwargs)
    parser.add_argument('-q','--queryfile', type=Path, default='query.txt',
                        help=r'Query file, e.g. query.txt',
                        **queryfile_kwargs)
    #parser.add_argument('-o','--output', type=Path, default='simdata.sqlite',
    #                    help=r'Output file, e.g. simdata.sqlite',
    #                    **outputfile_kwargs)
    parser.add_argument('-P', '--parallel', action='store_false', help='Disable parallel mode.')
    parser.add_argument('--logfile', type=Path, default='result2.log',
                        help='Log file for script diagnostics.')
    parser.add_argument('-c','--coil', action='store_true', help='Generate cooling coil sizing table (result_sizing_agg)')

def cli_main():
    """Starts the script on command line."""
    parser = argparse.ArgumentParser()
    build_cli_parser(parser)
    pargs = parser.parse_args()
    configure_logging(pargs.logfile)
    log.info(f"Writing diagnostics to {pargs.logfile}")
    try:
        gather_sim_data_to_sqlite_long(pargs.study, pargs.queryfile, 'simdata.sqlite', parallel=pargs.parallel, include_cooling_coils=pargs.coil)
    finally:
        _stop_logging()

def gooey_main():
    """Opens a window for user to input options and start the script."""
    import gooey
    parser = gooey.GooeyParser()
    # Gooey is not compatible with Tqdm progress bar without more changes.
    build = gooey.Gooey(build_cli_parser, progress_regex=r"\| (?P<current>\d+)/(?P<total>\d+) \[")
    build(parser,
          study_kwargs = dict(widget='DirChooser'),
          queryfile_kwargs = dict(widget='FileChooser'),
          #outputfile_kwargs = dict(widget='FileChooser')
          )
    pargs = parser.parse_args()
    configure_logging(pargs.logfile)
    log.info(f"Writing diagnostics to {pargs.logfile}")
    try:
        gather_sim_data_to_sqlite_long(pargs.study, pargs.queryfile,'simdata.sqlite', parallel=pargs.parallel, include_cooling_coils=pargs.coil)
    finally:
        _stop_logging()

def test():
    """Starts the script with hard-coded options."""
    configure_logging(Path('result2.log'))
    #study = Path(r'C:\DEER2026\SWHC012-nick\commercial measures\SWHC012-04 Occupancy Sensor')
    study = Path(r'C:\DEER2026\nf_com_testing_dhw\commercial measures\SWXX000-00 Measure Name')
    queryfile = Path(r'..\querylibrary\query_default.txt')
    gather_sim_data_to_sqlite_long(study, queryfile,'simdata.sqlite', parallel=False, include_cooling_coils=False)

if "__main__" == __name__:
    cli_main()
    #gooey_main()
    #test()
