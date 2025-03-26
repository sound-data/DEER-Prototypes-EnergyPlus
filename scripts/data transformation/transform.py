#!/usr/bin/env python
# coding: utf-8

"""Residential data transformation script (work in progress)

Transform "results-summary.csv" and "instance-var.csv" files
into "current_msr_mat", "sim_annual", and "sim_hourly_wb".

This script is based on SFm.py, DMo.py, and MFm.py from January 2023 and lacks several later changes.
WARNING: The script is not fully tested.

Features:
* Make data transformation more command-line-friendly for MFm
* Requires python >= 3.2 and additional package "tqdm"
* Speed up reading hourly files (DMo and MFm)

To do:
* Speed up reading hourly files (SFm)
* Merge recent changes from SFm/DMo/MFm
* Testing and validation that results match SFm/DMo/MFm scripts

Usage:
    Prerequisite: running models
    $terminal1> cd C:/Users/user1/source/DEER-Prototypes-EnergyPlus/Analysis/MFm_Furnace_Ex
    $terminal1> modelkit rake results

    Data transformation step
    $terminal1> cd C:/Users/user1/source/DEER-Prototypes-EnergyPlus
    $terminal1> python scripts/transform.py MFm "Wall Furnace" ./Analysis/MFm_Furnace_Ex -o ./myresults/

@Author: Nicholas Fette <nfette@solaris-technical.com>
@Date: 2023-07-11
"""

#%%
##STEP 0: Setup (import all necessary libraries)
import pandas as pd
import numpy as np
import os
import sys
import datetime as dt
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool
from tqdm import tqdm, trange
from io import BytesIO

DEFAULT_HOURLY_COLUMN = 'Electricity:Facility [J](Hourly)'

TRANSFORM_PATH = Path(os.path.dirname(__file__))
DEERROOT = TRANSFORM_PATH / '../..'
MEASURELIST_PATH = TRANSFORM_PATH / 'DEER_EnergyPlus_Modelkit_Measure_list.xlsx'
ANNUALMAP_PATH = TRANSFORM_PATH / 'annual8760map.xlsx'
NORMUNITS_PATH = TRANSFORM_PATH / 'Normunits.xlsx'

# %%
#Read master workbook for measure / tech list
df_master = pd.read_excel(MEASURELIST_PATH, sheet_name='Measure_list', skiprows=4)
MEASURE_GROUP_NAMES = list(df_master['Measure Group Name'].unique())

#generate unique list of measure names
MEASURES = list(df_master['Measure (general name)'].unique())

#Shows list of measure names
#print(MEASURES)

# %%
#extract only the 5th portion of the measure group name for expected_att
#split argument 4 means only split 4 times maximum
techgroup_techtypes = [i.split('&', 4)[-1] for i in MEASURE_GROUP_NAMES]
tech_uniques = list(np.unique((np.array(techgroup_techtypes))))
# Name parsing function per Amine
# This dictionary of attributes should be updated
expected_att = {
    'BldgType': ['MFm','SFm', 'DMo'],
    'Story': ['0','1','2'], # NA for Not Applicable
    'BldgHVAC': ['rDXGF','rDXHP','rNCEH','rNCGF'],
    'BldgVint': ['Ex','New'],
    'Measure': tech_uniques
}

# function to parse meta data from & delimited case file names (Measure Group Name from master spreadsheet)
def parse_measure_name(measure_name: str) -> dict:
    #split at most 4 times for 5 descriptor fields
    measure_name_split = measure_name.split('&', 4)
    # Check here if the presented name has 5 attributes as expected:
    if not len(measure_name_split) == 5:
        sys.exit('The case name must have at least 5 attributes similar to < BldgType&Story&BldgHVAC&BldgVint&TechGroup__TechType >')

    attributes = list(expected_att.keys())
    measure_name_dict = {attributes[i]: measure_name_split[i] for i in range(0,5)}

    # Check here if the presented attributes are as expected:
    for att in attributes:
        if measure_name_dict[att] not in expected_att[att]:
            sys.exit(f'Attribute <{measure_name_dict[att]}> was not expected')


    return measure_name_dict # returns a dictionary

def parse_measure_name2(cohort_names: pd.Series, verify: bool = False) -> pd.DataFrame:
    '''Returns a DataFrame with five columns (all type string):
        ["BldgType","Story","BldgHVAC","BldgVint","TechGroup__TechType"]
    Each cohort name must match the pattern:
        "BldgType&Story&BldgHVAC&BldgVint&TechGroup__TechType"
    Only alphanumeric characters are allowed  [a-zA-Z0-9_], except TechGroup__TechType may contain ampersand (&).

    Parameters
    ----------
    cohort_names : pandas.Series
        The cohort names as from cohorts.csv.
    verify : bool, default=False
        If true and name parts do not match `expected_att`, raise an exception.

    Returns
    -------
    pandas.DataFrame
        Structure containing the parts of cohort name.
    '''
    result = cohort_names.str.extract(
        r'(?P<BldgType>\w+)&(?P<Story>\w+)&(?P<BldgHVAC>\w+)&(?P<BldgVint>\w+)&(?P<Measure>[^/]+)'
    )
    if verify:
        # Check for missing descriptor fields
        missing = result.isna()
        if missing.any().any():
            example = cohort_names[missing.any(axis=1)].iloc[0]
            raise ValueError(f'Missing descriptor field, e.g. cohort = "{example}"')
        # Check for unrecognized fields
        for attr_name,attr_val in expected_att.items():
            unrecognized = ~result[attr_name].isin(attr_val)
            if unrecognized.any():
                example = result[attr_name][unrecognized].iloc[0]
                raise ValueError(f'Unrecognized descriptor field, e.g. {attr_name} = "{example}"')
    result.rename({'Measure':'TechGroup__TechType'},axis=1,inplace=True)
    return result

#function to melt long 8760 col into 24col x365row format
def long2wide_pivot(df: pd.DataFrame, name: str) -> pd.DataFrame:
    '''
    customized function.
    input df is long 8760, 1 column format, with the daynum(of365) and hour of day(of24) mapped.
    id is the unique identifier.

    output df is the 24col x 365row format of the 8760, with the corresponding id.
    '''
    df_wide = df.pivot(index='daynum',columns='Hour', values=df.columns[0]).reset_index().rename_axis('', axis=1)
    df_wide['ID']=name
    #df_wide = pd.merge(df_wide, df_ag_key, on='ID')

    return df_wide

#function to uses the “File Name” column from the results-summary csv to identify directory structure (an organized table) of a batch run
# and uses the structure to construct a semi-organized annual outputs table.
def annual_raw_parsing(df: pd.DataFrame,
    cohort_dict: dict,
    split_meta_cols_eu: pd.DataFrame
    ) -> pd.DataFrame :
    #create separated meta data cols
    df['BldgLoc'] = split_meta_cols_eu[0]

    df['BldgType'] = cohort_dict['BldgType']
    df['BldgHVAC'] = cohort_dict['BldgHVAC']
    df['BldgVint'] = cohort_dict['BldgVint']

    df['Story'] = cohort_dict['Story']

    df['TechGroup_TechType'] = cohort_dict['Measure']

    df['TechID'] = split_meta_cols_eu[2]
    df['file'] = split_meta_cols_eu[3]

    annual_df_v1 = df[['TechID', 'file', 'BldgLoc', 'BldgType','BldgHVAC','BldgVint','Story', 'TechGroup_TechType','Total (kWh)', 'Heating (kWh)', 'Cooling (kWh)',
       'Interior Lighting (kWh)', 'Exterior Lighting (kWh)',
       'Interior Equipment (kWh)', 'Exterior Equipment (kWh)', 'Fans (kWh)',
       'Pumps (kWh)', 'Heat Rejection (kWh)', 'Humidification (kWh)',
       'Heat Recovery (kWh)', 'Water Systems (kWh)', 'Refrigeration (kWh)',
       'Generators (kWh)', 'Heating Elec (kWh)', 'Cooling Elec (kWh)',
       'Heating NG (kWh)', 'Cooling NG (kWh)', 'Interior Equipment Elec (kWh)',
       'Interior Equipment NG (kWh)']]

    return annual_df_v1

#function to merge and rearrange specific annual consumption end-use fields into the format required
def end_use_rearrange(df_in: pd.DataFrame) -> pd.DataFrame:
    kwh_per_therm = 29.3
    columns=['TechID', 'BldgLoc', 'BldgType', 'BldgHVAC', 'BldgVint', 'kwh_tot', 'kwh_ltg', 'kwh_task',
    'kwh_equip', 'kwh_htg', 'kwh_clg', 'kwh_twr', 'kwh_aux', 'kwh_vent',
    'kwh_venthtg', 'kwh_ventclg',
    'kwh_refg', 'kwh_hpsup', 'kwh_shw', 'kwh_ext', 'thm_tot', 'thm_equip',
    'thm_htg', 'thm_shw', 'deskw_ltg', 'deskw_equ']
    return (
        df_in[['TechID', 'BldgLoc', 'BldgType', 'BldgHVAC', 'BldgVint']]
        .assign(kwh_tot = (df_in['Heating Elec (kWh)'] +
                            df_in['Cooling Elec (kWh)'] +
                            df_in['Interior Equipment Elec (kWh)'] +
                            df_in['Interior Lighting (kWh)'] +
                            df_in['Exterior Lighting (kWh)'] +
                            df_in['Fans (kWh)']+
                            df_in['Pumps (kWh)']))
        .assign(kwh_ltg = (df_in['Interior Lighting (kWh)'] +
                                        df_in['Exterior Lighting (kWh)']))
        .assign(kwh_task = 0) # placeholder (task lighting load?)
        .assign(kwh_equip = df_in['Interior Equipment Elec (kWh)'] +
                                        df_in['Exterior Equipment (kWh)'])
        .assign(kwh_htg = df_in['Heating Elec (kWh)'])
        .assign(kwh_clg = df_in['Cooling Elec (kWh)'])
        .assign(kwh_twr = 0) #place holder (tower kwh load?)
        .assign(kwh_aux = 0) #place holder (aux equipment kwh load?)
        .assign(kwh_vent = df_in['Fans (kWh)']) #use fan kWh as vent load for now
        .assign(kwh_venthtg =0) #placeholders fields for now
        .assign(kwh_ventclg =0)
        .assign(kwh_refg = 0)
        .assign(kwh_hpsup = 0)
        .assign(kwh_shw = 0)
        .assign(kwh_ext = 0)
        .assign(thm_tot = (df_in['Heating NG (kWh)'] +
                                    df_in['Cooling NG (kWh)'] +
                                    df_in['Interior Equipment NG (kWh)'] +
                                    df_in['Water Systems (kWh)'])/kwh_per_therm)
        .assign(thm_equip = df_in['Interior Equipment NG (kWh)']/kwh_per_therm)
        .assign(thm_htg = df_in['Heating NG (kWh)']/kwh_per_therm)
        .assign(thm_shw = df_in['Water Systems (kWh)']/kwh_per_therm)
        .assign(deskw_ltg = 1) #placeholders fields for now
        .assign(deskw_equ = 1)
        [columns]
    )


def end_use_rearrange_sfm(df_in: pd.DataFrame) -> pd.DataFrame:
    kwh_per_therm = 29.3
    columns=['TechID', 'BldgLoc', 'BldgType','BldgHVAC', 'BldgVint', 'kwh_tot', 'kwh_ltg', 'kwh_task',
       'kwh_equip', 'kwh_htg', 'kwh_clg', 'kwh_twr', 'kwh_aux', 'kwh_vent',
       'kwh_venthtga', 'kwh_ventclga', 'kwh_venthtgb', 'kwh_ventclgb',
       'kwh_refg', 'kwh_hpsup', 'kwh_shw', 'kwh_ext', 'thm_tot', 'thm_equip',
       'thm_htg', 'thm_shw']
    return (
        end_use_rearrange(df_in)
        .assign(kwh_venthtga =0) #placeholders fields...
        .assign(kwh_ventclga =0)
        .assign(kwh_venthtgb =0)
        .assign(kwh_ventclgb =0)
        [columns]
    )


def truncate8760(df: pd.DataFrame) -> pd.DataFrame:
    if len(df) != 8760:
        #8/31/2022 update, need to make the final length 8808. Snip data based on difference to 8760
        record_count_diff = len(df) - 8760
        #print(f'extra records: {str(len(extracted_df))}, snipping away {record_count_diff} records and changing to 8760')
        return df.iloc[record_count_diff:].reset_index(drop=True)
    else:
        return df

def read_hourly(
    full_path: Path,
    col_name: str,
    selected_column: str = DEFAULT_HOURLY_COLUMN
) -> pd.DataFrame:
    return (
        #extract the last column (the total elec hrly profile)
        #if for enduse hourly, then extract the relevant end use column
        #pd.read_csv(full_path, usecols=[selected_column])
        pd.read_csv(
            # EnergyPlus output CSV files have a trailing space at the end of each line.
            # If parsed using pandas, the last column name will retain the extra, trailing space.
            # E.g. 'Electricity:Facility [J](Hourly)' becomes 'Electricity:Facility [J](Hourly) '.
            # For repeatable results, strip trailing spaces on all lines before parsing the CSV file.
            BytesIO(b'\r\n'.join((line.rstrip() for line in open(full_path,'rb')))),
            # For performance, parse and return only the selected column
            usecols=[selected_column]
        )
        
        #change column name
        .set_axis([col_name], axis=1)
        .pipe(truncate8760)
    )

def read_hourly_multi(files_and_names: list) -> pd.DataFrame:
    """
    Parameters
    ----------
    files_and_names: list of tuples x = (full_path,col_name)
    """
    with Pool() as pool:
        results=[]
        presults = [(x,pool.apply_async(read_hourly, x)) for x in files_and_names]
        with tqdm(presults, desc='Read hourly CSV') as t:
            for (full_path,col_name,hourly_column_name),presult in t:
                t.set_description('{:<50s}'.format(col_name[:50]))
                results.append(presult.get())
    return pd.concat([pd.DataFrame(index=range(0,8760))] + results,axis=1)

def transform_mfm(
    bldgtype: str = 'MFm',
    measure_name: str = 'Wall Furnace',
    msrpath: Path = DEERROOT/'Analysis/MFm_Furnace_Ex',
    outpath: Path = None,
    hourly_column_name: str = DEFAULT_HOURLY_COLUMN
    ) -> None:

    if outpath is None:
        outpath = Path()
    outpath.mkdir(parents=True,exist_ok=True)
    # %%
    #MFm only script

    # %%
    #create measure specific Master table based on Measure selected
    df_measure = df_master[df_master['Measure (general name)'] == measure_name]
    case_cohort_list = df_measure['Measure Group Name'].unique()

    # %%
    ##STEP 1: Annual data extraction / transformation
    print("Step 1. Processing annual data.")

    df_raw = pd.read_csv(msrpath/'results-summary.csv', usecols=['File Name'])
    num_runs = len(df_raw['File Name'].dropna().unique()) - 1
    #Read annual data
    annual_df = pd.read_csv(msrpath/'results-summary.csv', nrows=num_runs, skiprows=num_runs+2)
    split_meta_cols_eu = annual_df['File Name'].str.split('/', expand=True)

    #if looping over multiple folders/cohort cases, use a list
    cohort_cases = list(split_meta_cols_eu[1].unique())

    sim_annual_proto = pd.DataFrame()
    for case in cohort_cases:
        print(f'processing all annual data that are grouped in {case}')
        cohort_dict = parse_measure_name(case)
        sim_annual_i = annual_raw_parsing(annual_df[annual_df['File Name'].str.contains(case)].copy(), cohort_dict, split_meta_cols_eu)
        sim_annual_proto = pd.concat([sim_annual_proto, sim_annual_i])
        print('ok.')
    sim_annual_proto = end_use_rearrange(sim_annual_proto)
    sim_annual_v1 = sim_annual_proto[['TechID', 'BldgLoc', 'BldgType', 'BldgHVAC', 'BldgVint', 'kwh_tot', 'kwh_ltg', 'kwh_task',
        'kwh_equip', 'kwh_htg', 'kwh_clg', 'kwh_twr', 'kwh_aux', 'kwh_vent',
        'kwh_venthtg', 'kwh_ventclg',
        'kwh_refg', 'kwh_hpsup', 'kwh_shw', 'kwh_ext', 'thm_tot', 'thm_equip',
        'thm_htg', 'thm_shw', 'deskw_ltg', 'deskw_equ']].drop_duplicates().copy()

    # %%
    ##STEP 2: Hourly data extraction / transformation
    print("Step 2. Processing hourly data.")
    #Read 8760 map
    annual_map = pd.read_excel(ANNUALMAP_PATH)

    # %%
    hrly_path = msrpath / 'runs'

    #extract data per bldgtype-bldghvac-bldgvint group
    #extract num_runs / split_meta_cols_eu
    df_raw = pd.read_csv(msrpath / 'results-summary.csv', usecols=['File Name'])
    num_runs = len(df_raw['File Name'].dropna().unique()) - 1
    annual_df = pd.read_csv(msrpath / 'results-summary.csv', nrows=num_runs, skiprows=num_runs+2)
    split_meta_cols_eu = annual_df['File Name'].str.split('/', expand=True)
    files_and_names=[]
    for i in range(0,num_runs):
        #loop path of each file, read corresponding file
        #create the column name based on the permutations
        col_name = split_meta_cols_eu.iloc[i][0] + "/" + split_meta_cols_eu.iloc[i][1] + "/" + split_meta_cols_eu.iloc[i][2] + "/instance-var.csv"
        full_path = hrly_path / col_name
        files_and_names.append((full_path, col_name, hourly_column_name))

    #left-merge onto big df
    hourly_df = read_hourly_multi(files_and_names)

    # %%
    fyr_hrly = hourly_df
    #rearrange 1-column 8760 format to 365x24 wide format for all runs in hourly_df
    converted_df = pd.DataFrame()

    for i in trange(0,len(fyr_hrly.columns), desc='Transform columns'):

        #isolate single column
        hrly_df = pd.DataFrame(fyr_hrly.iloc[:,i])

        #create separate metadata columns
        col_names = hrly_df.columns[0].split('/')

        #create new key column for merge
        hrly_df['hr in 8760'] = (hrly_df.index) + 1

        #merge based on "hr in 8760" column, the 8760 map
        hrly_mapped = pd.merge(hrly_df, annual_map, on='hr in 8760')

        #transform data format
        hrly_wide = long2wide_pivot(hrly_mapped, hrly_mapped.columns[0])

        #add meta data col
        hrly_wide['BldgLoc'] = col_names[0]
        hrly_wide['BldgType'] = col_names[1]
        hrly_wide['TechID'] = col_names[2]
        hrly_wide['file'] = col_names[3]

        #append to master df
        #converted_df = converted_df.append(hrly_wide) #deprecated method
        converted_df = pd.concat([converted_df, hrly_wide])

    #%%
    #rearrange columns
    sim_hourly_wb_proto = converted_df[['TechID','file','BldgLoc','BldgType','ID','daynum',1,          2,          3,          4,          5,
                    6,          7,          8,          9,         10,         11,
                12,         13,         14,         15,         16,         17,
                18,         19,         20,         21,         22,         23,
                24]].copy()
    #hourly data conversion
    #convert unit (J) to (kWh) for hourly

    sim_hourly_wb_proto['hr01'] = sim_hourly_wb_proto[1]/3600000
    sim_hourly_wb_proto['hr02'] = sim_hourly_wb_proto[2]/3600000
    sim_hourly_wb_proto['hr03'] = sim_hourly_wb_proto[3]/3600000
    sim_hourly_wb_proto['hr04'] = sim_hourly_wb_proto[4]/3600000
    sim_hourly_wb_proto['hr05'] = sim_hourly_wb_proto[5]/3600000
    sim_hourly_wb_proto['hr06'] = sim_hourly_wb_proto[6]/3600000
    sim_hourly_wb_proto['hr07'] = sim_hourly_wb_proto[7]/3600000
    sim_hourly_wb_proto['hr08'] = sim_hourly_wb_proto[8]/3600000
    sim_hourly_wb_proto['hr09'] = sim_hourly_wb_proto[9]/3600000
    sim_hourly_wb_proto['hr10'] = sim_hourly_wb_proto[10]/3600000
    sim_hourly_wb_proto['hr11'] = sim_hourly_wb_proto[11]/3600000
    sim_hourly_wb_proto['hr12'] = sim_hourly_wb_proto[12]/3600000
    sim_hourly_wb_proto['hr13'] = sim_hourly_wb_proto[13]/3600000
    sim_hourly_wb_proto['hr14'] = sim_hourly_wb_proto[14]/3600000
    sim_hourly_wb_proto['hr15'] = sim_hourly_wb_proto[15]/3600000
    sim_hourly_wb_proto['hr16'] = sim_hourly_wb_proto[16]/3600000
    sim_hourly_wb_proto['hr17'] = sim_hourly_wb_proto[17]/3600000
    sim_hourly_wb_proto['hr18'] = sim_hourly_wb_proto[18]/3600000
    sim_hourly_wb_proto['hr19'] = sim_hourly_wb_proto[19]/3600000
    sim_hourly_wb_proto['hr20'] = sim_hourly_wb_proto[20]/3600000
    sim_hourly_wb_proto['hr21'] = sim_hourly_wb_proto[21]/3600000
    sim_hourly_wb_proto['hr22'] = sim_hourly_wb_proto[22]/3600000
    sim_hourly_wb_proto['hr23'] = sim_hourly_wb_proto[23]/3600000
    sim_hourly_wb_proto['hr24'] = sim_hourly_wb_proto[24]/3600000

    #rearrange columns
    sim_hourly_wb_v1 = sim_hourly_wb_proto[['TechID','file','BldgLoc','BldgType','ID','daynum','hr01','hr02','hr03','hr04','hr05','hr06',
            'hr07',     'hr08',     'hr09',     'hr10',     'hr11',     'hr12',
            'hr13',     'hr14',     'hr15',     'hr16',     'hr17',     'hr18',
            'hr19',     'hr20',     'hr21',     'hr22',     'hr23',     'hr24']].copy()
    # %%
    ##STEP 3: Normalizing Units
    print('STEP 3. Normalizing Units.')

    df_normunits = pd.read_excel(NORMUNITS_PATH, sheet_name=bldgtype)
    if bldgtype == 'MFm':
        numunits_vals = df_normunits[df_normunits['Normunit'] == df_measure['Normunit'].unique()[0]][['CZ','Value', 'Msr','BldgVint']]
    elif bldgtype == 'DMo':
        numunits_vals = df_normunits[df_normunits['Normunit'] == df_measure['Normunit'].unique()[0]][['Value', 'Msr']]
    else:
        raise ValueError(f'Building type "{bldgtype}" was unexpected at this point.')
    #%%
    #create numunits object based on what normunit it uses.
    #numunits can be a single value, or a dictionary
    if len(numunits_vals) == 1:
        numunits = list(numunits_vals['Value'])[0]
    elif (measure_name == 'Wall Insulation') or (measure_name == 'Ceiling Insulation'):
        numunits = list(numunits_vals[numunits_vals['Msr'] == measure_name]['Value'])[0]
    elif bldgtype == 'MFm' and measure_name == 'PTAC / PTHP':
        #create aligned lists for numunit dictionary
        cz = list(numunits_vals['CZ'])
        vint = list(numunits_vals['BldgVint'])
        nvals = list(numunits_vals['Value'])
        #create dictionary of {(cz,vintage):numunits}
        numunits = {(cz[i],vint[i]):nvals[i] for i in range(len(cz))}
    else:
        pass

    # %%
    ##Annual Data final field fixes
    #note normunit = building area (conditioned)
    sim_annual_v1['SizingID'] = 'None'
    sim_annual_v1['tstat'] = 0
    #now Norm unit is read from measure master table
    sim_annual_v1['normunit'] = df_measure['Normunit'].unique()[0]
    if bldgtype == 'MFm':
        # TODO: make this automatic as well
        sim_annual_v1['measarea'] = 24576 #from MFm model outputs htmls

        #apply normunits where appropriate
        #num unit will be per dwelling, so divide by num of dwellings (2 for SFM, DMo, 24 for MFm)

        if measure_name == 'PTAC / PTHP':
            #Map special dictionary to the correct values
            sim_annual_v1['numunits'] = pd.Series(list(zip(sim_annual_v1['BldgLoc'],sim_annual_v1['BldgVint']))).map(numunits)/24
        else:
            sim_annual_v1['numunits'] = numunits/24
    elif bldgtype == 'DMo':
        #make this automatic as well
        sim_annual_v1['measarea'] = 2484 #from DMo model outputs htmls

        #apply normunits where appropriate
        #num unit will be per dwelling, so use roof area / num of dwellings (2 for SFM, DMo, 24 for MFm)
        sim_annual_v1['numunits'] = numunits/2
    #elif bldgtype == 'SFm':
    else:
        raise ValueError(f'Building type "{bldgtype}" was unexpected at this point.')

    sim_annual_v1['lastmod']=dt.datetime.now()

    #rearrange columns
    sim_annual_f = sim_annual_v1[['TechID', 'SizingID', 'BldgType','BldgVint','BldgLoc','BldgHVAC','tstat',
           'normunit', 'numunits', 'measarea', 'kwh_tot', 'kwh_ltg', 'kwh_task',
           'kwh_equip', 'kwh_htg', 'kwh_clg', 'kwh_twr', 'kwh_aux', 'kwh_vent',
           'kwh_venthtg', 'kwh_ventclg', 'kwh_refg', 'kwh_hpsup', 'kwh_shw',
           'kwh_ext', 'thm_tot', 'thm_equip', 'thm_htg', 'thm_shw', 'deskw_ltg',
           'deskw_equ', 'lastmod']]
    # %%
    ##Hourly Data final field fixes

    #update field names based on what it contains
    df_tmp = parse_measure_name2(sim_hourly_wb_v1['ID'],verify=True)
    sim_hourly_wb_v1['BldgVint'] = df_tmp['BldgVint']
    sim_hourly_wb_v1['BldgHVAC'] = df_tmp['BldgHVAC']
    sim_hourly_wb_v1['BldgType'] = df_tmp['BldgType']
    del df_tmp
    sim_hourly_wb_v1['SizingID'] = 'None'
    sim_hourly_wb_v1['tstat'] = 0
    sim_hourly_wb_v1['enduse'] = 0
    sim_hourly_wb_v1['lastmod']=dt.datetime.now()

    #rearrange columns
    sim_hourly_f = sim_hourly_wb_v1[['TechID', 'SizingID', 'BldgType', 'BldgVint', 'BldgLoc','BldgHVAC','tstat', 'enduse', 'daynum',
                                     'hr01', 'hr02', 'hr03', 'hr04', 'hr05', 'hr06', 'hr07', 'hr08', 'hr09', 'hr10', 'hr11',
                                    'hr12', 'hr13', 'hr14', 'hr15', 'hr16', 'hr17', 'hr18', 'hr19', 'hr20',
                                    'hr21', 'hr22', 'hr23', 'hr24', 'lastmod']]
    # %%
    ##STEP 4: Measure setup file (current_msr_mat.csv)
    print('STEP 4: Measure setup file (current_msr_mat.csv)')

    # Creating current_msr_mat and finalzing TechID's

    metadata_cols = sim_annual_f[['TechID', 'BldgLoc', 'BldgType', 'BldgVint', 'BldgHVAC', 'SizingID',
           'tstat', 'normunit']]

    #check unique TechID cases
    metadata_cols['TechID'].unique()
    # %%
    #TechID identification from Master table
    #if looping over all HVAC types, ignore BldgHVAC filter
    PreTechIDs = df_measure[['PreTechID','Common_PreTechID']].drop_duplicates()
    StdTechIDs = df_measure[['StdTechID','Common_StdTechID']].drop_duplicates()
    MsrTechIDs = df_measure[['MsrTechID','Common_MsrTechID']].drop_duplicates()
    # %%
    #filter out each pre, std, msr using the Common TechIDs from master table
    metadata_pre = metadata_cols[metadata_cols['TechID'].isin(PreTechIDs['Common_PreTechID'].unique())]
    metadata_std = metadata_cols[metadata_cols['TechID'].isin(StdTechIDs['Common_StdTechID'].unique())]
    metadata_msr = metadata_cols[metadata_cols['TechID'].isin(MsrTechIDs['Common_MsrTechID'].unique())]

    # %%
    #rename to Pre, Std or Msr
    #both Std and Pre are baseline for SEER rated AC measures
    metadata_pre = metadata_pre.rename(columns={'TechID':'PreTechID'})
    metadata_std = metadata_std.rename(columns={'TechID':'StdTechID'})
    metadata_msr = metadata_msr.rename(columns={'TechID':'MsrTechID'})
    # %%
    #Changing common TechID to actual TechIDs if needed.
    #might only apply to SEER AC/HP

    #create full pre_metadata sets for different names but the same TechID
    # commom_preTechID = PreTechIDs['Common_PreTechID'].unique()[0]
    if False in list(PreTechIDs['PreTechID']==PreTechIDs['Common_PreTechID']):
        metadata_pre_full = pd.DataFrame()
        for new_id in PreTechIDs['PreTechID']:
            print(f'changing to specific PreTechID {new_id}')
            metadata_pre_mod = metadata_pre.copy()
            metadata_pre_mod['PreTechID'] = new_id
            #merge to final df
            metadata_pre_full = pd.concat([metadata_pre_full, metadata_pre_mod])
    else:
        print('same TechID, proceeding without changing names')
        metadata_pre_full = metadata_pre.copy()


    # %%
    #create std_metadata sets, assigning appropriate final TechIDs
    if False in list(StdTechIDs['StdTechID']==StdTechIDs['Common_StdTechID']):
        metadata_std_full = pd.DataFrame()
        for common_id, new_id in zip(StdTechIDs['Common_StdTechID'], StdTechIDs['StdTechID']):
            print(f'common is {common_id}, changing into new id is {new_id}')
            #Isolate specific common id (old)
            metadata_std_mod = metadata_std[metadata_std['StdTechID']==common_id].copy()
            #Change into final techID name (new)
            metadata_std_mod['StdTechID'] = new_id
            #merge to final df
            metadata_std_full = pd.concat([metadata_std_full, metadata_std_mod])
    else:
        print('same TechID, proceeding without changing names')
        metadata_std_full = metadata_std.copy()
    # %%
    #create msr_metadata sets, assigning appropriate final TechIDs
    if False in list(MsrTechIDs['MsrTechID']==MsrTechIDs['Common_MsrTechID']):
        metadata_msr_full = pd.DataFrame()
        for common_id, new_id in zip(MsrTechIDs['Common_MsrTechID'], MsrTechIDs['MsrTechID']):
            print(f'common is {common_id}, changing into new id is {new_id}')
            #Identify corresponding common TechID (the last 9 characters indicating SEER levels)
            metadata_msr_mod = metadata_msr[metadata_msr['MsrTechID']==common_id].copy()
            #Change into final TechID name
            metadata_msr_mod['MsrTechID'] = new_id
            #merge to final df
            metadata_msr_full = pd.concat([metadata_msr_full, metadata_msr_mod])
    else:
        print('same TechID, proceeding without changing names')
        metadata_msr_full = metadata_msr.copy()
    # %%
    #create raw merged current_msr_mat
    #need to delete/drop incorrect sets
    if np.NaN in list(StdTechIDs['StdTechID'].unique()):
        df_measure_set_full = pd.merge(metadata_pre_full, metadata_msr_full, on=['BldgLoc','BldgType','BldgVint','BldgHVAC','SizingID','tstat','normunit'])
    elif np.NaN in list(PreTechIDs['PreTechID'].unique()):
        df_measure_set_full = pd.merge(metadata_std_full, metadata_msr_full, on=['BldgLoc','BldgType','BldgVint','BldgHVAC','SizingID','tstat','normunit'])
    else:
        df_measure_baseline_full = pd.merge(metadata_pre_full, metadata_std_full, on=['BldgLoc','BldgType','BldgVint','BldgHVAC','SizingID','tstat','normunit'])
        df_measure_set_full = pd.merge(df_measure_baseline_full, metadata_msr_full, on=['BldgLoc','BldgType','BldgVint','BldgHVAC','SizingID','tstat','normunit'])

    # %%
    #Unique sets of each MeasureID with their TechID triplets
    TechID_triplets = df_measure[['EnergyImpactID','MeasureID', 'PreTechID', 'StdTechID','MsrTechID']].drop_duplicates()
    # %%
    #to match TechID triplets, merge on these 3 fields, keeping only valid TechID Triplets
    if np.NaN in list(StdTechIDs['StdTechID'].unique()):
        current_msr_mat_proto = pd.merge(df_measure_set_full, TechID_triplets, on=['PreTechID','MsrTechID'])
    elif np.NaN in list(PreTechIDs['PreTechID'].unique()):
        current_msr_mat_proto = pd.merge(df_measure_set_full, TechID_triplets, on=['StdTechID','MsrTechID'])
    else:
        current_msr_mat_proto = pd.merge(df_measure_set_full, TechID_triplets, on=['PreTechID','StdTechID','MsrTechID'])

    # %%
    #add placeholders, rearrange fields
    current_msr_mat_proto['PreSizingID']='None'
    current_msr_mat_proto['StdSizingID']='None'
    current_msr_mat_proto['MsrSizingID']='None'
    current_msr_mat_proto['SizingSrc']=np.nan
    current_msr_mat_proto['EU_HrRepVar']=np.nan

    current_msr_mat = current_msr_mat_proto[['MeasureID', 'BldgType', 'BldgVint','BldgLoc','BldgHVAC','tstat','PreTechID','PreSizingID',
                                 'StdTechID', 'StdSizingID','MsrTechID','MsrSizingID','SizingSrc','EU_HrRepVar','normunit']]
    current_msr_mat = current_msr_mat.rename(columns={'normunit':'NormUnit'})

    print('check length of current_msr_mat:', len(current_msr_mat))

    # %%
    ##STEP 5: Clean Up Sequence
    print('STEP 5: Clean Up Sequence')

    #Creating updated Sim_annual and Sim_hourly data with distinguished TechID names
    sim_annual_pre_common = sim_annual_f[sim_annual_f['TechID'].isin(PreTechIDs['Common_PreTechID'].unique())]
    sim_annual_std_common = sim_annual_f[sim_annual_f['TechID'].isin(StdTechIDs['Common_StdTechID'].unique())]
    sim_annual_msr_common = sim_annual_f[sim_annual_f['TechID'].isin(MsrTechIDs['Common_MsrTechID'].unique())]
    # %%
    #Add a TechID col renaming the common TechID to the specific TechID using PreTechIDs, StdTechIDs, MsrTechIDs

    #create full pre sim_annual sets for different names but the same TechID
    # commom_preTechID = PreTechIDs['Common_PreTechID'].unique()[0]
    if False in list(PreTechIDs['PreTechID']==PreTechIDs['Common_PreTechID']):
        sim_annual_pre = pd.DataFrame()
        for new_id in PreTechIDs['PreTechID']:
            print(f'changing to specific PreTechID {new_id}')
            sim_annual_pre_mod = sim_annual_pre_common.copy()
            sim_annual_pre_mod['TechID'] = new_id
            #merge to final df
            sim_annual_pre = pd.concat([sim_annual_pre, sim_annual_pre_mod])
    else:
        print('same TechID, proceeding without changing names')
        sim_annual_pre = sim_annual_pre_common.copy()

    # %%
    # create full std sim_annual sets for different names but the same TechID
    if False in list(StdTechIDs['StdTechID']==StdTechIDs['Common_StdTechID']):
        sim_annual_std = pd.DataFrame()
        for common_id, new_id in zip(StdTechIDs['Common_StdTechID'], StdTechIDs['StdTechID']):
            print(f'common is {common_id}, changing into new id is {new_id}')
            #Isolate specific common id (old)
            sim_annual_std_mod = sim_annual_std_common[sim_annual_std_common['TechID']==common_id].copy()
            #Change into final techID name (new)
            sim_annual_std_mod['TechID'] = new_id
            #merge to final df
            sim_annual_std = pd.concat([sim_annual_std, sim_annual_std_mod])
    else:
        print('same TechID, proceeding without changing names')
        sim_annual_std = sim_annual_std_common.copy()
    # %%
    # create full msr sim_annual sets for different names but the same TechID
    if False in list(MsrTechIDs['MsrTechID']==MsrTechIDs['Common_MsrTechID']):
        sim_annual_msr = pd.DataFrame()
        for common_id, new_id in zip(MsrTechIDs['Common_MsrTechID'], MsrTechIDs['MsrTechID']):
            print(f'common is {common_id}, changing into new id is {new_id}')
            #Isolate specific common id (old)
            sim_annual_msr_mod = sim_annual_msr_common[sim_annual_msr_common['TechID']==common_id].copy()
            #Change into final techID name (new)
            sim_annual_msr_mod['TechID'] = new_id
            #merge to final df
            sim_annual_msr = pd.concat([sim_annual_msr, sim_annual_msr_mod])
    else:
        print('same TechID, proceeding without changing names')
        sim_annual_msr = sim_annual_msr_common.copy()

    # %%
    #final merge sim_annual
    sim_annual_final = pd.concat([sim_annual_pre, sim_annual_std, sim_annual_msr])
    # %%

    ###same deal with with hourly data, separate into pre std msr, change into specific TechID
    sim_hourly_pre_common = sim_hourly_f[sim_hourly_f['TechID'].isin(PreTechIDs['Common_PreTechID'].unique())]
    sim_hourly_std_common = sim_hourly_f[sim_hourly_f['TechID'].isin(StdTechIDs['Common_StdTechID'].unique())]
    sim_hourly_msr_common = sim_hourly_f[sim_hourly_f['TechID'].isin(MsrTechIDs['Common_MsrTechID'].unique())]

    # %%
    #Pre hourly
    if False in list(PreTechIDs['PreTechID']==PreTechIDs['Common_PreTechID']):
        sim_hourly_pre = pd.DataFrame()
        for new_id in PreTechIDs['PreTechID']:
            print(f'changing to specific PreTechID {new_id}')
            sim_hourly_pre_mod = sim_hourly_pre_common.copy()
            sim_hourly_pre_mod['TechID'] = new_id
            #merge to final df
            sim_hourly_pre = pd.concat([sim_hourly_pre, sim_hourly_pre_mod])
    else:
        print('same TechID, proceeding without changing names')
        sim_hourly_pre = sim_hourly_pre_common.copy()
    # %%
    #Std hourly
    if False in list(StdTechIDs['StdTechID']==StdTechIDs['Common_StdTechID']):
        sim_hourly_std = pd.DataFrame()
        for common_id, new_id in zip(StdTechIDs['Common_StdTechID'], StdTechIDs['StdTechID']):
            print(f'common is {common_id}, changing into new id is {new_id}')
            #Isolate specific common id (old)
            sim_hourly_std_mod = sim_hourly_std_common[sim_hourly_std_common['TechID']==common_id].copy()
            #Change into final techID name (new)
            sim_hourly_std_mod['TechID'] = new_id
            #merge to final df
            sim_hourly_std = pd.concat([sim_hourly_std, sim_hourly_std_mod])
    else:
        print('same TechID, proceeding without changing names')
        sim_hourly_std = sim_hourly_std_common.copy()
    # %%
    #Msr hourly
    if False in list(MsrTechIDs['MsrTechID']==MsrTechIDs['Common_MsrTechID']):
        sim_hourly_msr = pd.DataFrame()
        for common_id, new_id in zip(MsrTechIDs['Common_MsrTechID'], MsrTechIDs['MsrTechID']):
            print(f'common is {common_id}, changing into new id is {new_id}')
            #Isolate specific common id (old)
            sim_hourly_msr_mod = sim_hourly_msr_common[sim_hourly_msr_common['TechID']==common_id].copy()
            #Change into final techID name (new)
            sim_hourly_msr_mod['TechID'] = new_id
            #merge to final df
            sim_hourly_msr = pd.concat([sim_hourly_msr, sim_hourly_msr_mod])
    else:
        print('same TechID, proceeding without changing names')
        sim_hourly_msr = sim_hourly_msr_common.copy()

    # %%
    #final merge sim_hourly
    sim_hourly_final = pd.concat([sim_hourly_pre, sim_hourly_std, sim_hourly_msr])

    # %%
    ##Final export of all processed data pre-SQL process
    #change directory to wherever desired, if needed
    current_msr_mat.to_csv(outpath/'current_msr_mat.csv', index=False)
    sim_annual_final.to_csv(outpath/'sim_annual.csv', index=False)
    sim_hourly_final.to_csv(outpath/'sim_hourly_wb.csv', index=False)

def parse_args():
    # create the top-level parser
    parser = ArgumentParser(
        description='Transform "results-summary.csv" and "instance-var.csv" '
        'into "current_msr_mat", "sim_annual", and "sim_hourly_wb"',
        epilog=None
        )

    parser.add_argument('bldgtype', metavar='bldgtype', type=str, choices=["DMo","MFm","SFm"],
                    help='E.g. "MFm"')
    parser.add_argument('measure_name', metavar='measure_name', type=str, choices=MEASURES,
                    help='E.g. "Wall Furnace"')
    parser.add_argument('msrpath', metavar='measure_path', type=Path,# nargs=+,
                    help='E.g. '+(DEERROOT/'Analysis/MFm_Furnace_Ex').resolve().as_posix())
    parser.add_argument('-o', '--outpath', type=Path,
                    help='E.g. "myresults/"')
    parser.add_argument('-d', '--hourly_column_name', type=str,
                        default=DEFAULT_HOURLY_COLUMN)
    # parse command line arguments
    return parser.parse_args()

def main():
    # Gather user options.
    args = parse_args()
    if args.bldgtype != 'MFm':
        print(f'Building type "{args.bldgtype}" not implemented.')
        return
    transform_mfm(args.bldgtype, args.measure_name, args.msrpath, args.outpath, args.hourly_column_name)

if __name__ == '__main__':
    main()
