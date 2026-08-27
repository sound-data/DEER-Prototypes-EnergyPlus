#!/usr/bin/env python
# coding: utf-8

"""Residential data scraping tool (work in progress)


Features:
* Read from instance-out.sql files using result spec format like modelkit
* Requires python >= 3.2 and additional package "tqdm"

To do:
* programmatic api
* command line interface

Usage:
    Prerequisite: running models
    $terminal1> cd C:/Users/user1/source/DEER-Prototypes-EnergyPlus/Analysis/MFm_Furnace_Ex
    $terminal1> python results.py results

    Data transformation step
    $terminal1> cd C:/Users/user1/source/DEER-Prototypes-EnergyPlus
    $terminal1> python scripts/transform.py

@Author: Nicholas Fette <nfette@solaris-technical.com>
@Date: 2023-11-05

Why this file:

An issue with rakefile.rb is that PXV files are written outside of a rake task.
`modelkit rake results` triggers writing PXV, which triggers composing IDF, which triggers running IDF, even when not needed!
One strategy may be to write the PXV to a "fake" file and compare it to the existing PXV file. If there are no changes, then don't modify the file.
Otherwise, why not establish a task and dependencies for PXV, like for everything else?
"""

##STEP 0: Setup (import all necessary libraries)
import re
from dataclasses import dataclass, asdict, astuple
from sqlite3 import connect
from pathlib import Path
from multiprocessing import Pool
from io import BytesIO

import pandas as pd
from tqdm import tqdm, trange

FILENAME_FINISHED = 'instance-out.sql'
TABULAR_DATA_HEADERS = ['ReportName', 'ReportForString',
    'TableName', 'ColumnName', 'RowName']
TOKEN_ANY = '*'

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

def build_query(resultspec: ResultSpec, finalize = True) -> str:
    if not isinstance(resultspec, ResultSpec):
        resultspec = makeResultSpec(resultspec)

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

def get_a_result(sqlfile: Path, resultspec: ResultSpec, aggtype='sum') -> tuple:

    if not isinstance(resultspec, ResultSpec):
        resultspec = makeResultSpec(resultspec)

    query,agg_columns = build_query(resultspec)

    if resultspec.to_string().startswith("AnnualBuildingUtilityPerformanceSummary/Entire Facility/End Uses/Total Energy/"):
        # Special case. 'Total Energy' is a synthetic result not defined by EnergyPlus.
        # It is not a good idea to use this because it is adding quantities with different meanings (kWh electric + kWh gas, etc).
        if resultspec.RowName == TOKEN_ANY:
            query,agg_columns = build_query(
                "AnnualBuildingUtilityPerformanceSummary/Entire Facility/End Uses/*/*",
                False)
            query += """ AND ColumnName <> 'Water';"""
        else:
            query,agg_columns = build_query(
                f"AnnualBuildingUtilityPerformanceSummary/Entire Facility/End Uses/*/{resultspec.RowName}",
                False)
            query += """ AND ColumnName <> 'Water';"""

    with connect(sqlfile) as conn:
        sim_sizing_data = pd.read_sql_query(query, conn,  params=asdict(resultspec), dtype={'Value':float})

    sizing_agg = (
        sim_sizing_data
        .groupby(agg_columns)
        ['Value'].agg(aggtype).iloc[0]
    )
    return sim_sizing_data, sizing_agg

def gather_sizing_data1(subroot: Path, resultspec: ResultSpec, progressbar=False):
    """
    Copy model files and hourly output files to a different folder.

    Assumes that files are placed within a "runs" subfolder.

    subroot: e.g., "C:\path\DEER-Prototypes-EnergyPlus\Analysis\SFm_Furnace_1975"
    """

    if progressbar:
        from tqdm import tqdm

    if not isinstance(subroot, Path):
        subroot = Path(subroot)
    meas_group = subroot.name

    # Count composed models.
    runs_root = subroot.joinpath('runs')
    subroot_finished_list = list(runs_root.glob('**/'+FILENAME_FINISHED))
    n_models = len(subroot_finished_list)

    if progressbar:
        # Create the progress bar here.
        myiter = tqdm(subroot_finished_list, desc=subroot.name)
    else:
        myiter = subroot_finished_list

    sim_sizing_data, sizing_agg = [], []
    for sqlfile in myiter:
        relpath = sqlfile.relative_to(subroot)
        # E.g. relpath = CZ01\SFm&1&rDXGF&Ex&SpaceHtg_eq__GasFurnace\Msr-Res-GasFurnace-AFUE95-ECM\instance-out.sql
        relstr = relpath.as_posix() # with forward slashes
        # E.g. relpath = CZ01/SFm&1&rDXGF&Ex&SpaceHtg_eq__GasFurnace/Msr-Res-GasFurnace-AFUE95-ECM/instance-out.sql

        #_, cz, cohort, techid, _ = relpath.parts
        #print(meas_group, cz, cohort, techid)

        a,b = get_a_result(sqlfile, resultspec)
        a["File Name"] = relstr

        sim_sizing_data.append(a)
        sizing_agg.append((relstr, b))

    if progressbar:
        myiter.close()

    sim_sizing_data = pd.concat(sim_sizing_data)
    sizing_agg = pd.DataFrame(sizing_agg,columns=['File Name','Value'])

    return sim_sizing_data, sizing_agg

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

def gather_sizing_data2(subroot: Path, queryfile: Path, progressbar=False):
    r"""
    Read selected data entries from SQL outputs and write to CSV.
    Result set specifications are parsed from query.txt, e.g. (resultspec, name).
    Output columns will have units appended to name, like "name (Units)".

    Assumes that files are placed within a "runs" subfolder under the given subroot.

    subroot: e.g., "C:\Users\User1\DEER-Prototypes-EnergyPlus\Analysis\SFm_Furnace_1975"
    """

    if progressbar:
        from tqdm import tqdm

    if not isinstance(subroot, Path):
        subroot = Path(subroot)
    meas_group = subroot.name

    listlist_query_path_and_name = parse_query_file(queryfile)

    result_sets = []
    for list_query_path_and_name in listlist_query_path_and_name:
        columns_out = ['File Name'] + [name for _,name in list_query_path_and_name]

        # Count composed models.
        runs_root = subroot.joinpath('runs')
        subroot_finished_list = list(runs_root.glob('**/'+FILENAME_FINISHED))
        n_models = len(subroot_finished_list)

        if progressbar:
            # Create the progress bar here.
            myiter = tqdm(subroot_finished_list, desc=subroot.name)
        else:
            myiter = subroot_finished_list

        sim_sizing_data, sizing_agg = [], []
        for sqlfile in myiter:
            relpath = sqlfile.relative_to(subroot)
            # E.g. relpath = Path(r"CZ01\SFm&1&rDXGF&Ex&SpaceHtg_eq__GasFurnace\Msr-Res-GasFurnace-AFUE95-ECM\instance-out.sql")
            relstr = relpath.as_posix() # with forward slashes
            # E.g. relstr = "CZ01/SFm&1&rDXGF&Ex&SpaceHtg_eq__GasFurnace/Msr-Res-GasFurnace-AFUE95-ECM/instance-out.sql"
            #_, cz, cohort, techid, _ = relpath.parts
            #print(meas_group, cz, cohort, techid)

            sizing_agg_row = {"File Name": relstr}
            for resultspec, user_column_name in list_query_path_and_name:
                a,b = get_a_result(sqlfile, resultspec)
                a["File Name"] = relstr
                units = a['Units'].iloc[0]
                sim_sizing_data.append(a)
                sizing_agg_row.update({f"{user_column_name} ({units})": b})
            sizing_agg.append(sizing_agg_row)

        if progressbar:
            myiter.close()

        sim_sizing_data = pd.concat(sim_sizing_data)
        sizing_agg = pd.DataFrame(sizing_agg)
        result_sets.append((sim_sizing_data, sizing_agg))

    return result_sets

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('subroot', type=Path, default='.',
                        help=r'Analysis subfolder, e.g. C:\Users\user1\Desktop\DEER-EnergyPlus-Prototypes\Analysis\SFm_Furnace_1975')
    parser.add_argument('-q','--queryfile', type=Path, default='query.txt',
                        help=r'Query file, e.g. query.txt')
    parser.add_argument('-d','--detailfile', type=Path, default='results-sizing-detail.csv',
                        help=r'Output file for detailed sizing info, e.g. results-sizing-detail.csv')
    parser.add_argument('-a','--aggfile', type=Path, default='results-sizing-agg.csv',
                        help=r'Output file for aggregated sizing info, e.g. results-sizing-agg.csv')

    pargs = parser.parse_args()
    result_sets = gather_sizing_data2(pargs.subroot, pargs.queryfile, True)

    output1 = BytesIO()
    output2 = BytesIO()

    for sim_sizing_data, sizing_agg in result_sets:
        sim_sizing_data.to_csv(output1,mode='a',index=False)
        output1.write(b'\r\n')
        sizing_agg.to_csv(output2,mode='a',index=False)
        output2.write(b'\r\n')

    pargs.detailfile.write_bytes(output1.getbuffer())
    pargs.aggfile.write_bytes(output2.getbuffer())

def test1():
    specstr = "AnnualBuildingUtilityPerformanceSummary/Entire Facility/Site and Source Energy/Energy Per Total Building Area/Net Site Energy"
    sqlfile = r"C:\Users\user1\Desktop\DEER-EnergyPlus-Prototypes\Analysis\SFm_Furnace_1975\runs\CZ01\SFm&1&rDXGF&Ex&SpaceHtg_eq__GasFurnace\AFUE_80_baseline\instance-out.sql"
    myspec = makeResultSpec(specstr)
    print(myspec)
    sim_sizing_data, sizing_agg = get_a_result(sqlfile, myspec)
    print(sim_sizing_data)
    print(sizing_agg)
    return sim_sizing_data, sizing_agg

def test2():
    specstr = "ComponentSizingSummary/Entire Facility/Coil:Heating:Fuel/Design Size Nominal Capacity/*"
    sqlfile = r"C:\Users\user1\Desktop\DEER-EnergyPlus-Prototypes\Analysis\SFm_Furnace_1975\runs\CZ01\SFm&1&rDXGF&Ex&SpaceHtg_eq__GasFurnace\AFUE_80_baseline\instance-out.sql"
    myspec = makeResultSpec(specstr)
    sim_sizing_data, sizing_agg = get_a_result(sqlfile, myspec)
    print(sim_sizing_data)
    print(sizing_agg)
    return sim_sizing_data, sizing_agg

def test3():
    sim_sizing_data, sizing_agg = gather_sizing_data1(
        r"C:\Users\user1\Desktop\DEER-EnergyPlus-Prototypes\Analysis\SFm_Furnace_1975",
        "ComponentSizingSummary/Entire Facility/Coil:Heating:Fuel/Design Size Nominal Capacity/*",
        True)
    print(sim_sizing_data)
    print(sizing_agg)
    return sim_sizing_data, sizing_agg

def test4():
    result_sets = gather_sizing_data2(
        r"C:\Users\user1\Desktop\DEER-EnergyPlus-Prototypes\Analysis\SFm_Furnace_1975",
        r"C:\Users\user1\Desktop\DEER-EnergyPlus-Prototypes\Analysis\DMo_Brushless_Fan_Motor_Ex\query.txt",
        True)
    for sim_sizing_data, sizing_agg in result_sets:
        print(sim_sizing_data)
        print(sizing_agg)
        sim_sizing_data.to_csv('results-sim-sizing.csv',mode='a',index=False)
        sizing_agg.to_csv('results-sizing-agg.csv',mode='a',index=False)
    return result_sets

def test_all():
    #sim_sizing_data, sizing_agg = test1()
    #sim_sizing_data, sizing_agg = test2()
    #sim_sizing_data, sizing_agg = test3()
    result_set = test4()
    print("Done.")

if "__main__" == __name__:
    #test_all()
    main()
