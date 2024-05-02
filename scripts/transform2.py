#!/usr/bin/env python
# coding: utf-8

"""EnergyPlus batch results data scraping tool, including DEER peak period.

Features:
* Read from instance-out.sql files using result spec format like modelkit
* Apply DEER peak period calculation to hourly results and include those.
* Requires python >= 3.7.1 and additional package "tqdm"

Usage:
    Prerequisite: running models, select a query file, path to DEER peak period definitions
    $terminal1> cd C:/DEER-Prototypes-EnergyPlus/
    $terminal1> python "scripts/transform2.py" "commercial measures/SWXX000-00 Measure Name" --queryfile "querylibrary/query_default.txt"

Changelog
    * 2024-05-01 Adapted result.py for DEER Peak period calculation

@Author: Nicholas Fette <nfette@solaris-technical.com>
@Date: 2024-05-01

"""

##STEP 0: Setup (import all necessary libraries)
import re
from dataclasses import dataclass, asdict, astuple
from sqlite3 import connect, Connection
from pathlib import Path
from io import BytesIO
from functools import cache
import argparse
import concurrent.futures

# Third-party packages
import numpy as np
import pandas as pd
import tqdm
import tqdm.asyncio

def get_deer_peak_day(bldgloc: str):
    """Return a for DEER peak period start day lookups.

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

@cache
def get_deer_peak_multipliers(BldgLoc: str,
                          days=3, start_hr=16, end_hr=21, dst=True):
    """Return a masking array useful to calculate an average over DEER Peak Period.

    Note that for compatibility, simulation data must be an 8760-length array
    that represents one annual period (no gaps or duplicates due to dst).

    Inputs:
        BldgLoc: str
            CEC climate zone, e.g. CZ01 through CZ16.
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
    peak_day = get_deer_peak_day(BldgLoc)
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
    is_deer_peak_hour = (hour_of_day_0 >= start_hr) * (hour_of_day_0 <= end_hr)
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
    with queryfile.open() as f:
        for query_line in f:
            if query_line.isspace():
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


def get_sim_hourly(conn: Connection):
    """Get simulation hourly results from one EnergyPlus SQLite output file.

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
    #n_rows, = conn.execute('select count(*) from ReportData').fetchone()
    chunks = []
    for chunk in pd.read_sql_query('select * from ReportData', conn, chunksize=10000):
        chunks.append(chunk)
    ReportData = pd.concat(chunks, axis=0)

    # Transform ReportDataDictionary so we have a single column lookup string.
    # LookupKey looks like:
    #   If 'EL7 NORTH PERIM ZN (G.N2):Zone Total Internal Total Heating Energy [J](Hourly)'
    # LookupKey looks like 'EL7 NORTH PERIM ZN (G.N2):Zone Total Internal Total Heating Energy [J](Hourly)'
    ReportDataDictionary['LookupKey']=ReportDataDictionary.apply(
        lambda x: f'{x.KeyValue}:{x.Name} [{x.Units}]({x.ReportingFrequency})' if bool(x.KeyValue)
        else f'{x.Name} [{x.Units}]({x.ReportingFrequency})'
        , axis=1)
    ReportData2 = ReportData.join(ReportDataDictionary, on='ReportDataDictionaryIndex')

    # Transform ReportData from long to wide so we can make a condensed table
    ReportDataWide = ReportData2.pivot(index='LookupKey',columns='TimeIndex',values='Value')
    # Prepare the table for saving in a database
    #ReportDataWide['sim_id'] = sim_run.sim_id
    #ReportDataWide2=ReportDataWide.reset_index().set_index(['TimeIndex'],drop=True)

    return ReportDataWide

def get_sim_deer_peak(conn: Connection, bldgloc: str):
    """Get simulation DEER Peak results from one EnergyPlus SQLite output file.

    Inputs:
        conn: sqlite3.Connection
            An open connection to the SQLite output file from an EnergyPlus simulation.
        bldgloc: str
            The CEC climate zone used to lookup up DEER peak period dates.
    Returns:
        ReportDataWide: pandas.Series
            Series with shape (N,) where each of N elements represents the average
            value of the hourly variable over the DEER Peak Period.
    """
    # Get all available hourly results with shape (N, 8760)
    ReportDataWide = get_sim_hourly(conn)
    if ReportDataWide.shape[1] != 8760:
        # No hourly data. This can happen if simulation created the output file but failed to complete.
        # Or if the file represents a sizing run.
        return None
    # Get 8760-length mask for DEER Peak Period (normalized)
    dpm = get_deer_peak_multipliers(bldgloc)
    # Compute the average value over the DEER Peak Period
    deer_peak_values = ReportDataWide.mul(dpm,axis=1).sum(axis=1)
    return deer_peak_values

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

def get_sim_peak_and_tabular(sqlfile: Path, queryfile: Path, bldgloc: str):
    r"""
    Read selected data entries from SQL outputs.
    Result set specifications are parsed from query.txt, e.g. (resultspec, name).
    Output columns will have units appended to name, like "name (Units)".

    Inputs:
        sqlfile: Path
            The filename of an EnergyPlus output file (SQLite format).
        queryfile: Path
            The filename of a modelkit-style query.txt file.
        bldgloc: str
            The CEC climate zone, e.g. CZ01 through CZ16.

    Returns:
        sim_data: dict(str: float | None).
            Mapping of (name, value) from both query results
            and hourly averages over the DEER peak period.
    """
    sim_data = dict() # To store results
    with connect(sqlfile) as conn:
        # Start with the query data results
        listlist_query_path_and_name = parse_query_file(queryfile)
        # Don't separate "groups" of queries but group them all together.
        # result_sets = []
        for list_query_path_and_name in listlist_query_path_and_name:
            # Don't separate "groups" of queries but group them all together.
            # sim_data_detail, sim_data_agg = [], []
            for resultspec, user_column_name in list_query_path_and_name:
                sim_data_detail1, sim_data_agg1 = get_sim_tabular(conn, resultspec)
                if sim_data_detail1 is None:
                    # No data found matching the result spec. Skip this and go to next.
                    continue
                units = sim_data_detail1['Units'].iloc[0]
                #sim_data_detail.append(sim_data_detail1)
                if sim_data_agg1 is not None:
                    sim_data.update({f"{user_column_name} ({units})": sim_data_agg1})
            #sim_data_agg.append(sizing_agg_row)

        # Now get the DEER Peak values from hourly data
        deer_peak_values = get_sim_deer_peak(conn, bldgloc)
        if deer_peak_values is not None:
            sim_data.update(deer_peak_values.to_dict())

    return sim_data

def get_runs_instances(study: Path, filename_pattern = 'instance*-out.sql'):
    r"""Returns a list of all of SQLite output files in a modelkit study folder.

    Assumes that files are placed within a "runs" subfolder under the given study.

    Inputs:
        study: pathlib.Path
            The folder in which to search for simulation outputs.
            E.g. old style: "C:\Users\User1\DEER-Prototypes-EnergyPlus\Analysis\SFm_Furnace_1975"
            E.g. new style: "C:\Users\User1\DEER-Prototypes-EnergyPlus\commercial measures\SWHC012-04 Occupancy Sensor"
        filename_pattern: str, default = 'instance*-out.sql'
            The filename pattern used to search for output files, using glob syntax.
    """
    # Note that autosized runs are named instance-out.sql.
    # Linked-sizing runs are named instance-hardsize-out.sql.
    # To do: check if there are both autosized and linked-sizing files in the same folder and pick one.
    list_sqlfile = list(study.glob('**/'+filename_pattern))
    return list_sqlfile

def gather_sim_data_basic(study: Path, queryfile: Path, pathsub: tuple =('runs/','')):
    r"""Returns a generator yielding simulation data from each simulation.

    Read selected data entries from SQL outputs as well as DEER Peak period averages of hourly variables.
    Result set specifications are parsed from query.txt, e.g. (resultspec, name).
    Output columns will have units appended to name, like "name (Units)".

    Assumes that files are placed within a "runs" subfolder under the given study.

    study: e.g., "C:\Users\User1\DEER-Prototypes-EnergyPlus\Analysis\SFm_Furnace_1975"
    """
    if not isinstance(study, Path):
        study = Path(study)
    list_sqlfile = get_runs_instances(study)
    for sqlfile in tqdm.tqdm(list_sqlfile):
        relpath = sqlfile.relative_to(study)
        # E.g. relpath = Path(r"runs\CZ01\SFm&1&rDXGF&Ex&SpaceHtg_eq__GasFurnace\Msr-Res-GasFurnace-AFUE95-ECM\instance-out.sql")
        relstr = relpath.as_posix() # with forward slashes
        # E.g. relstr = "runs/CZ01/SFm&1&rDXGF&Ex&SpaceHtg_eq__GasFurnace/Msr-Res-GasFurnace-AFUE95-ECM/instance-out.sql"
        # Search string for climate zone like 'CZ11/'.
        m = re.search(r"CZ\d\d(?=/)", relstr)
        if not m:
            raise ValueError(f'Could not match climate zone in filename: "{relstr}"')
        bldgloc = m[0]
        # For compatibility with modelkit, may want to remove 'runs/' prefix.
        # E.g. filename = "CZ01/SFm&1&rDXGF&Ex&SpaceHtg_eq__GasFurnace/Msr-Res-GasFurnace-AFUE95-ECM/instance-out.sql"
        filename = re.sub(*pathsub, relstr, 1)

        # Start the load operations and mark each future with its input arguments.
        sim_data = get_sim_peak_and_tabular(sqlfile, queryfile, bldgloc)

        if sim_data is None:
            continue

        # Insert a filename header into results tables
        sim_data_with_filename = {"File Name": filename}
        sim_data_with_filename.update(sim_data)

        yield sim_data_with_filename

def gather_sim_data_multi(study: Path, queryfile: Path, pathsub: tuple =('runs/','')):
    r"""Returns a generator yielding simulation data from each simulation.

    Read selected data entries from SQL outputs as well as DEER Peak period averages of hourly variables.
    Result set specifications are parsed from query.txt, e.g. (resultspec, name).
    Output columns will have units appended to name, like "name (Units)".

    Assumes that files are placed within a "runs" subfolder under the given study.

    study: e.g., "C:\Users\User1\DEER-Prototypes-EnergyPlus\Analysis\SFm_Furnace_1975"
    """
    if not isinstance(study, Path):
        study = Path(study)
    list_sqlfile = get_runs_instances(study)

    # Use a ThreadPoolExecutor to achieve some parallelism.
    # This should speed up the process if there are a large number of files.
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        print("Created a thread pool with ",executor._max_workers)
        future_lookup = dict() # Remember each file when requested.
        # Queue each operation to read simulation data, returning a future.
        for sqlfile in list_sqlfile:
            relpath = sqlfile.relative_to(study)
            # E.g. relpath = Path(r"runs\CZ01\SFm&1&rDXGF&Ex&SpaceHtg_eq__GasFurnace\Msr-Res-GasFurnace-AFUE95-ECM\instance-out.sql")
            relstr = relpath.as_posix() # with forward slashes
            # E.g. relstr = "runs/CZ01/SFm&1&rDXGF&Ex&SpaceHtg_eq__GasFurnace/Msr-Res-GasFurnace-AFUE95-ECM/instance-out.sql"
            # Search string for climate zone like 'CZ11/'.
            m = re.search(r"CZ\d\d(?=/)", relstr)
            if not m:
                raise ValueError(f'Could not match climate zone in filename: "{relstr}"')
            bldgloc = m[0]
            # For compatibility with modelkit, may want to remove 'runs/' prefix.
            # E.g. filename = "CZ01/SFm&1&rDXGF&Ex&SpaceHtg_eq__GasFurnace/Msr-Res-GasFurnace-AFUE95-ECM/instance-out.sql"
            filename = re.sub(*pathsub, relstr, 1)

            # Start the load operations and mark each future with its input arguments.
            future = executor.submit(get_sim_peak_and_tabular, sqlfile, queryfile, bldgloc)
            future_lookup[future] = (sqlfile, filename)

        # Wait for futures to complete and show a progress bar.
        for i,future in zip(
            tqdm.trange(len(list_sqlfile), desc=study.name), # progress bar
            concurrent.futures.as_completed(future_lookup)  # waiting for results from parallel threads
        ):
            (sqlfile, filename) = future_lookup[future]
            try:
                sim_data = future.result()
            except Exception as exc:
                print(f'Reading {sqlfile} generated an exception: {exc}')
                #executor.shutdown()
            else:
                # Insert a filename header into results tables
                sim_data_with_filename = {"File Name": filename}
                sim_data_with_filename.update(sim_data)

                yield sim_data_with_filename

def gather_sim_data_to_csv(study: Path, queryfile: Path, csvfile: Path):
    records = list(gather_sim_data_basic(study, queryfile))
    # In initial testing, ThreadPoolExecutor was slower than a single-threaded loop. Not sure why.
    #records = list(gather_sim_data_multi(study, queryfile))
    df_sim_data = pd.DataFrame.from_records(records)
    df_sim_data.to_csv(csvfile)

def gather_sim_data_to_sqlite(study: Path, queryfile: Path, sqlfile: Path):
    raise NotImplementedError('SQLite output not yet implemented.')

def build_cli_parser(parser: argparse.ArgumentParser, study_kwargs = {}, queryfile_kwargs = {}):
    parser.add_argument('study', type=Path, default='.',
                        help=r'Analysis subfolder, e.g. C:\Users\user1\Desktop\DEER-EnergyPlus-Prototypes\Analysis\SFm_Furnace_1975',
                        **study_kwargs)
    parser.add_argument('-q','--queryfile', type=Path, default='query.txt',
                        help=r'Query file, e.g. query.txt',
                        **queryfile_kwargs)

def cli_main():
    parser = argparse.ArgumentParser()
    build_cli_parser(parser)
    pargs = parser.parse_args()
    gather_sim_data_to_csv(pargs.study, pargs.queryfile, 'simdata.csv')

def gooey_main():
    import gooey
    parser = gooey.GooeyParser()
    # Gooey is not really compatible with Tqdm progress bar.
    build = gooey.Gooey(build_cli_parser, progress_regex=r"\| (?P<current>\d+)/(?P<total>\d+) \[")
    build(parser, dict(widget='DirChooser'), dict(widget='FileChooser'))
    pargs = parser.parse_args()
    gather_sim_data_to_csv(pargs.study, pargs.queryfile, 'simdata.csv')

def test():
    #study = Path(r'C:\DEER2026\SWHC012-nick\commercial measures\SWHC012-04 Occupancy Sensor')
    study = Path(r'C:\DEER2026\nf_com_testing\commercial measures\SWXX000-00 Measure Name')
    queryfile = Path(r'..\querylibrary\query_default.txt')
    gather_sim_data_to_csv(study, queryfile, 'simdata.csv')

if "__main__" == __name__:
    cli_main()
    #gooey_main()
    #test()
