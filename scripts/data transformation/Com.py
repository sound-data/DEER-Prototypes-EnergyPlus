#%%
##STEP 0: Setup (import all necessary libraries)
import pandas as pd
import numpy as np
import os
import sys
import datetime as dt
os.chdir(os.path.dirname(__file__)) #resets to current script directory

import helper_functions
from importlib import reload
reload(helper_functions)
# %%
#Read master workbook for measure / tech list (note example commented line for specific measures)
df_master = pd.read_excel('DEER_EnergyPlus_Modelkit_Measure_list_working.xlsx', sheet_name='Measure_list', skiprows=4)
#df_master = pd.read_excel('DEER_EnergyPlus_Modelkit_Measure_list_working_fanbelts.xlsx', sheet_name='Measure_list', skiprows=4)
#df_master = pd.read_excel('DEER_EnergyPlus_Modelkit_Measure_list_AshControl.xlsx', sheet_name='Measure_list', skiprows=4)
measure_group_names = list(df_master['Measure Group Name'].unique())

# %%
#generate unique list of measure names for Com

df_com = df_master[df_master['Sector']=='Com']

measures = list(df_com['Modelkit Folder Primary Name'].unique())
# %%
#Shows list of commercial measure names (with workpaper ID) 
print(measures)
#%%
#Define measure name here (name of the measure folder itself) 
##NOTE: The example folder used here, 'SWXX111-00 Example_SEER_AC' is only used to illustrate an example workflow thru post-procesing
#measure_name = 'SWXX111-00 Example_SEER_AC'
measure_name = 'SWCR001-06 ASH_Controls'
#measure_name = 'SWCR001-05 ASH_Controls'
#filter to specific measure mapping records from mapping workbook
df_measure = df_com[df_com['Modelkit Folder Primary Name']== measure_name]
# %%
#### Define path

os.chdir(os.path.dirname(__file__)) #resets to current script directory
print(os.path.abspath(os.curdir))
os.chdir("../..") #go up two directory
print(os.path.abspath(os.curdir))

#12/20/2023 After finishing Com, try to condense Res script so one script takes care of one measure folder?
#to do: use for loop to loop over each folder, using if-else to process different building types for Res
#filepath = f'commercial measures/{measure_name}'
filepath = f'commercial measures/SWCR001-06 ASH_Controls' #only changed this for testing


# %%
#function to list all sub-directories in a directory
def list_folders_in_path(path):
    folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
    return folders


def locate_file(directory, target_file):
    for root, dirs, files in os.walk(directory):
        if target_file in files:
            print(f'found {target_file} in path:"{directory}"')
            return os.path.join(root, target_file)
    return None



#%%
#other helper functions
#set up helper functions for data transform
techgroup_techtypes = [i.split('&', 4)[-1] for i in measure_group_names]
tech_uniques = list(np.unique((np.array(techgroup_techtypes))))

#Added Com options for data parser
expected_att = {
    'BldgType': ['MFm','SFm','DMo']+['Asm',
                                    'ECC',
                                    'EPr',
                                    'ERC',
                                    'ESe',
                                    'EUn',
                                    'Fin',
                                    'Gro',
                                    'Hsp',
                                    'Htl',
                                    'Lib',
                                    'MBT',
                                    'MLI',
                                    'Mtl',
                                    'Nrs',
                                    'OfL',
                                    'OfS',
                                    'Rel',
                                    'RFF',
                                    'RSD',
                                    'Rt3',
                                    'RtL',
                                    'RtS',
                                    'SCn',
                                    'SUn',
                                    'WRf'],
    'Story': ['0','1','2'], # NA for Not Applicable
    'BldgHVAC': ['rDXGF','rDXHP','rNCEH','rNCGF'] + ['cWLHP',
                                                    'cSVVG',
                                                    'cNCGF',
                                                    'cNCEH',
                                                    'cDDCT',
                                                    'cDXHP',
                                                    'cPTHP',
                                                    'cPTAC',
                                                    'cEVAP',
                                                    'cDXEH',
                                                    'cUnc',
                                                    'cVRF',
                                                    'cPVVE',
                                                    'cFPFC',
                                                    'cDXGF',
                                                    'cPVVG',
                                                    'cWtd',
                                                    'cSVVE',
                                                    'cHPVRF',
                                                    'cHRVRF',
                                                    'cAVVG',
                                                    'cWVVG',
                                                    'cDXOH'],
    'BldgVint': ['Ex','New'],
    'Measure': tech_uniques
}

#%%
# function to parse meta data from & delimited case file names (Measure Group Name from master spreadsheet)
def parse_measure_name(measure_name):
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
def long2wide_pivot(df, name):
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

#annual parsing function for Com
def annual_raw_parsing_com(df, cohort_dict, case):
    #create separated meta data cols
    df['BldgLoc'] = split_meta_cols_all[split_meta_cols_all[1]==case][0]

    df['BldgType'] = cohort_dict['BldgType']
    df['BldgHVAC'] = cohort_dict['BldgHVAC']
    df['BldgVint'] = cohort_dict['BldgVint']

    df['Story'] = 0 #no need for stories indication for com

    df['TechGroup_TechType'] = cohort_dict['Measure']

    df['TechID'] = split_meta_cols_all[split_meta_cols_all[1]==case][2]
    df['file'] = split_meta_cols_all[split_meta_cols_all[1]==case][3]
    
    #COM modelkit output is kBtu for the time being. change this after fix

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
#to be edited for Com
def end_use_rearrange(df_in):
    df_in['kwh_tot'] = (df_in['Heating Elec (kWh)'] + \
                            df_in['Cooling Elec (kWh)'] +\
                            df_in['Interior Equipment Elec (kWh)'] +\
                            df_in['Interior Lighting (kWh)'] +\
                            df_in['Exterior Lighting (kWh)'] +\
                            df_in['Fans (kWh)']+\
                            df_in['Pumps (kWh)']+\
                            df_in['Refrigeration (kWh)'])

    df_in['kwh_ltg'] = (df_in['Interior Lighting (kWh)'] +\
                                    df_in['Exterior Lighting (kWh)'])

    df_in['kwh_task'] = 0 # placeholder (task lighting load?)

    df_in['kwh_equip'] = df_in['Interior Equipment Elec (kWh)'] +\
                                    df_in['Exterior Equipment (kWh)']

    df_in['kwh_htg'] = df_in['Heating Elec (kWh)']
    df_in['kwh_clg'] = df_in['Cooling Elec (kWh)']
    df_in['kwh_twr'] = 0 #place holder (tower kwh load?)
    df_in['kwh_aux'] = 0 #place holder (aux equipment kwh load?)

    df_in['kwh_vent'] = df_in['Fans (kWh)'] #use fan kWh as vent load for now

    df_in['kwh_venthtg'] =0 #placeholders fields for now
    df_in['kwh_ventclg'] =0
    df_in['kwh_refg'] = df_in['Refrigeration (kWh)']
    df_in['kwh_hpsup'] = 0
    df_in['kwh_shw'] = 0
    df_in['kwh_ext'] = 0

    df_in['thm_tot'] = (df_in['Heating NG (kWh)'] +\
                                df_in['Cooling NG (kWh)'] +\
                                df_in['Interior Equipment NG (kWh)'] +\
                                df_in['Water Systems (kWh)'])/29.3

    df_in['thm_equip'] = df_in['Interior Equipment NG (kWh)']/29.3

    df_in['thm_htg'] = df_in['Heating NG (kWh)']/29.3

    df_in['thm_shw'] = df_in['Water Systems (kWh)']/29.3

    df_in['deskw_ltg'] = 1 #placeholders fields for now
    df_in['deskw_equ'] = 1

    return df_in





#%%
##STEP 1: Annual data extraction / transformation
#creates unparsed table over all runs

df_annual_raw = pd.DataFrame()
split_meta_cols_all = pd.DataFrame()
folder_list = list_folders_in_path(filepath)
for folder in folder_list:
    print(f"looking at folder {folder}..")
    if locate_file(filepath+"/"+folder, 'results-summary.csv') != None:
        #locate_file(filepath+"/"+folder, 'results-summary.csv')
        print(f"'{filepath}/{folder}/results-summary.csv' will be processed.")
        #insert subsequent processing here
        df_raw = pd.read_csv(filepath+"/"+folder+'/results-summary.csv', usecols=['File Name'])
        num_runs = len(df_raw['File Name'].dropna().unique()) - 1 
        annual_df = pd.read_csv(filepath+"/"+folder+'/results-summary.csv', nrows=num_runs, skiprows=num_runs+2)
        split_meta_cols_eu = annual_df['File Name'].str.split('/', expand=True)

        #concat each dataset
        df_annual_raw = pd.concat([df_annual_raw, annual_df])
        split_meta_cols_all = pd.concat([split_meta_cols_all, split_meta_cols_eu])

        print("processed.")
    else:
        print(f"no data found.")


# %%
#if looping over multiple folders/cohort cases, use a list
#Com version

cohort_cases = list(split_meta_cols_all[1].unique())
#combine data
sim_annual_proto = pd.DataFrame()
for case in cohort_cases:
    print(f'processing all annual data that are grouped in {case}')
    cohort_dict = parse_measure_name(case)
    sim_annual_filtered = df_annual_raw[df_annual_raw['File Name'].str.contains(case)].copy()
    sim_annual_i = annual_raw_parsing_com(sim_annual_filtered, cohort_dict, case)
    sim_annual_proto = pd.concat([sim_annual_proto, sim_annual_i])
    print('ok.')
sim_annual_proto = end_use_rearrange(sim_annual_proto)
sim_annual_v1 = sim_annual_proto[['TechID', 'BldgLoc', 'BldgType', 'BldgHVAC', 'BldgVint', 'kwh_tot', 'kwh_ltg', 'kwh_task',
    'kwh_equip', 'kwh_htg', 'kwh_clg', 'kwh_twr', 'kwh_aux', 'kwh_vent',
    'kwh_venthtg', 'kwh_ventclg',
    'kwh_refg', 'kwh_hpsup', 'kwh_shw', 'kwh_ext', 'thm_tot', 'thm_equip',
    'thm_htg', 'thm_shw', 'deskw_ltg', 'deskw_equ']].drop_duplicates().copy()


#========================


#%%

#hourly
##STEP 2: Hourly data extraction / transformation
#Read 8760 map
os.chdir(os.path.dirname(__file__)) #resets to current script directory
print(os.path.abspath(os.curdir))
annual_map = pd.read_excel('annual8760map.xlsx')



# %%
os.chdir("../..") #go up two directory
print(os.path.abspath(os.curdir))

#%%
#lookup each folder, see if there is hourly output inside
#if so, extract hourly data per bldgtype-bldghvac-bldgvint group
#put together into one table

#4/23/26 fix attempt#1 - avoid multiple dataframe creations
index = pd.RangeIndex(8760)
hourly_data = {}

for folder in folder_list:
    print(f"looking at folder {folder}..")
    if 'runs' in list_folders_in_path(f'{filepath}/{folder}'):
        #locate_file(filepath+"/"+folder, 'results-summary.csv')
        print(f"'{filepath}/{folder}/runs' will be processed.")

        subpath = filepath + "/" + folder
        hrly_subpath = filepath + "/" + folder + "/runs"
        print(hrly_subpath)

        df_raw = pd.read_csv(subpath+'/'+'/results-summary.csv', usecols=['File Name'])
        num_runs = len(df_raw['File Name'].dropna().unique()) - 1
        annual_df = pd.read_csv(subpath+'/'+'/results-summary.csv', nrows=num_runs, skiprows=num_runs+2)
        split_meta_cols_eu = annual_df['File Name'].str.split('/', expand=True)

        for i in range(0,num_runs):
            print(f"processing record {i}")
            #loop path of each file, read corresponding file
            base_path = (
                f"{hrly_subpath}/"
                f"{split_meta_cols_eu.iloc[i][0]}/"
                f"{split_meta_cols_eu.iloc[i][1]}/"
                f"{split_meta_cols_eu.iloc[i][2]}"
                        )
            csv_path = f"{base_path}/instance-var.csv"
            idf_path = f"{base_path}/instance.idf"

            #3/3/2026 update, extract RunPeriod Start Day from IDF file for a particular simulation
            runperiod_start_day = helper_functions.get_runperiod_start_day(idf_path)

            #remove trailing spaces for col name if it happens
            df = pd.read_csv(csv_path, low_memory=False)
            df.columns = df.columns.str.strip()

            #extract values only
            values = df["Electricity:Facility [J](Hourly)"].to_numpy(copy=False)

            #8760 values check
            if len(values) != 8760:
                diff = len(values) - 8760
                print(f'extra records: {len(values)}, snipping away {diff} records and changing to 8760')
                values = values[diff:]

            #construct combined string as column header
            col_name = (
                        f"{split_meta_cols_eu.iloc[i][0]}/"
                        f"{split_meta_cols_eu.iloc[i][1]}/"
                        f"{split_meta_cols_eu.iloc[i][2]}/"
                        f"instance-var.csv/{runperiod_start_day}"
                        )
            
            #add in corresponding value from values
            hourly_data[col_name] = values

        print(f"hourly data for '{subpath}' processed.")
    else:
        print(f"no data found.")

# Create DataFrame once
hourly_df = pd.DataFrame(hourly_data, index=index)

# %%
fyr_hrly = hourly_df
#rearrange 1-column 8760 format to 365x24 wide format for all runs in hourly_df

#4/23/26 memory saver update - list of row dicts
converted_records = []

for i, col_name in enumerate(fyr_hrly.columns):
    
    #isolate single column values only
    values = fyr_hrly.iloc[:,i].to_numpy(copy=False)

    #check for data length
    if len(values) != 8760:
        raise ValueError(f"{col_name} has {len(values)} hours, expected 8760")
    
    #reshape to 365x24 via numpy
    wide_values = values.reshape(365, 24)

    #parse separate metadata columns
    col_parts = col_name.split('/')
    bldg_loc = col_parts[0]
    bldg_type = col_parts[1][:3]
    tech_id   = col_parts[2]
    file_name = col_parts[3]
    id = col_name
    
    #build row records
    for day_idx in range(365):
        row = {
            "daynum": day_idx + 1,
            "BldgLoc": bldg_loc,
            "BldgType": bldg_type,
            "TechID": tech_id,
            "file": file_name,
            "ID": id
        }

        #add 24 hourly cols
        for hour in range(24):
            row[hour + 1] = wide_values[day_idx, hour]
        
        converted_records.append(row)
    print(f"col {i} transformed.")

# create DataFrame once
converted_df = pd.DataFrame.from_records(converted_records)


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

#%%
#3/3/2026 update: move normalizing unit conversion to here for better organization
##STEP 3: Normalizing Units
bldgtype = 'Com'
os.chdir(os.path.dirname(__file__)) #resets to current script directory
print(os.path.abspath(os.curdir))


#Normunits.xlsx initial read error handling
try:
    df_normunits = pd.read_excel('Normunits.xlsx', sheet_name=bldgtype)
#error exception message for file doesn't exist
except FileNotFoundError:
    raise FileNotFoundError(
            "[ERROR] Cannot find workbook 'Normunits.xlsx'.\n"
            "Please make sure 'Normunits.xlsx' exists in the same directory as this script "
            "or provide the correct full path."
        )

#Normunit validation: do they exist in Normunits.xlsx, default state = missing
normunit_missing = True
#create set of available unique normunits to test if current measure's normunit is availble in Normunits.xlsx
available_normunits = set(df_normunits["Normunit"].dropna().astype(str).str.strip())

#locate current measure's normunit from the starting workbook
#pull raw values before converting to str to check for validity
raw_normunits = df_measure["Normunit"].dropna().unique()

#If normunit is completely missing, raise a flag / error
if len(raw_normunits) == 0:
    raise ValueError(
            "Normunit is missing: df_measure['Normunit'] contains only NaN/blank values.\n"
            "Please populate the 'Normunit' column in the starting measure workbook with a valid text value "
            "(e.g., 'Cap-Tons', 'Each').\n"
            "And make sure Normunits.xlsx is up-to-date."
        )
#(5/14/2026 the less critical issue but ASH Controls hits this edge case)
#Current script only designed for Normunit is 1 unique value within a batch workbook
#If there are multiple Normunits within a batch workbook, there needs to be unique identifiers at the TechID level, perhaps using MeasTechID
# what about the baseline TechID?  
# and the unit lookup portion of the script needs to be updated

if len(raw_normunits) != 1:
    raise ValueError(f"[ERROR] Expected 1 Normunit but found {raw_normunits}. Please make sure only 1 Normunit exists on starting workbook.")

raw_normunit = raw_normunits[0]

#If normunit anything other than a string/text, hard stop, provide appropriate error message 
if not isinstance(raw_normunit, str):
    raise TypeError(
            "Invalid Normunit type in df_measure['Normunit'].\n"
            f"Expected a string like 'Cap-Tons' or 'Each', but got:\n"
            f"  type = {type(raw_normunit).__name__}\n"
            f"  value = {raw_normunit!r}\n\n"
            "Please correct the starting measure workbook column 'Normunit' to contain text values.\n"
            "And make sure Normunits.xlsx is up-to-date."
        )

# Normalize whitespace
normunit = raw_normunit.strip()

# hard stop if Normunit field is empty
if normunit == "":
    raise ValueError(
        "Invalid Normunit value in df_measure['Normunit'].\n"
        "Normunit is an empty/blank string after stripping whitespace.\n"
        "Please correct the source workbook column 'Normunit'.\n"
        "And make sure Normunits.xlsx is up-to-date."
    )

if normunit in available_normunits:
    normunit_missing = False
    print(f'Current normalzing unit is {normunit}, proceeding')
else:
    normunit_missing = True
    raise ValueError(
        f"Current normalizing unit(s) for this measure (Normunit = {raw_normunit}) not found on Normunit.xlsx table,\n" 
        "please update Normunit.xlsx table appropriately and add corresponding normalizing unit and corresponding unit value(s).\n"
    )
    

#%%
################################################################################################
################################################################################################
#12/22/2025 CEDARS Hourly consumption output reformatting
# 4/23/2026 memory saver update
# use the hourly data before long2wide pivot transform

#Calendar arrays creation
N_HOURS = 8760
hours = np.arange(N_HOURS)
calendar = {
    "hr in 8760": hours + 1,
    "Hour": (hours % 24) + 1,
    "daynum": (hours // 24) + 1,
}
# pick a reference start day, add relevant fields
dt_index = pd.date_range("2018-01-01", periods=N_HOURS, freq="h")
calendar["Month"] = dt_index.month
calendar["Day"] = dt_index.day
#%%
#setup data dict
long_data = {
    "Total_Elec_Consumption": [],
    "hr in 8760": [],
    "Hour": [],
    "daynum": [],
    "Month": [],
    "Day": [],
    "BldgLoc": [],
    "BldgType": [],
    "BldgHVAC": [],
    "BldgVint": [],
    "TechGroup": [],
    "Measure Group Name": [],
    "TechID": [],
    "file": [],
    "RunPeriod Start Day": [],
}
print('reformatting hourly data for CEDARS loadshape format..')

for i, col_name in enumerate(fyr_hrly.columns):
    #isolate values
    values = fyr_hrly[col_name].to_numpy(copy=False)

    #check for data length
    if len(values) != N_HOURS:
        raise ValueError(f"{col_name} has {len(values)} rows")
    
    parts = col_name.split("/")
    cohort = parse_measure_name(parts[1])

    #hourly data value only put into dict
    long_data["Total_Elec_Consumption"].append(values)

    #add calendar fields
    for k in calendar:
        long_data[k].append(calendar[k])

    # add metadata
    long_data["BldgLoc"].append(np.repeat(parts[0], N_HOURS))
    long_data["BldgType"].append(np.repeat(cohort["BldgType"], N_HOURS))
    long_data["BldgHVAC"].append(np.repeat(cohort["BldgHVAC"], N_HOURS))
    long_data["BldgVint"].append(np.repeat(cohort["BldgVint"], N_HOURS))
    long_data["TechGroup"].append(np.repeat(cohort["Measure"], N_HOURS))
    long_data["Measure Group Name"].append(np.repeat(parts[1], N_HOURS))
    long_data["TechID"].append(np.repeat(parts[2], N_HOURS))
    long_data["file"].append(np.repeat(parts[3], N_HOURS))
    long_data["RunPeriod Start Day"].append(np.repeat(parts[4], N_HOURS))

    print(f"col {i} long format loaded.")

#build dataframe once
final_data = {k: np.concatenate(v) for k, v in long_data.items()}
converted_long_df = pd.DataFrame(final_data)


#%%
#Setup a lookup using Measure Group name, to lookup for TechGroup_ee, TechType_ee
TechGroup_lookup_map = df_measure.set_index('Measure Group Name')['TechGroup_ee'].to_dict()
TechType_lookup_map = df_measure.set_index('Measure Group Name')['TechType_ee'].to_dict()

#add corresponding TechGroup and TechType
converted_long_df['TechGroup'] = converted_long_df['Measure Group Name'].map(TechGroup_lookup_map)
converted_long_df['TechType'] = converted_long_df['Measure Group Name'].map(TechType_lookup_map)

#%%
#convert from J to kWh
converted_long_df['Total_Elec_Consumption'] = converted_long_df['Total_Elec_Consumption']/3600000

#%%
#Long format final field updates
#need to divide each 8760 by its annual and its corresponding numunit
#1. grouby to find sum of each table via unique ID
#2. merge as a new col in long df
#3, divide and clean up final columns

#convert to UEC by applying numunits
#delete UEC col
#converted_long_df['UEC'] = converted_long_df['Total_Elec_Consumption'] / converted_long_df['Numunits']

#sort
df_long = converted_long_df.sort_values(['BldgType','BldgLoc', 'TechID', 'hr in 8760'])

#%% 
#calculate annual consumption (no UEC involved)
df_long['annual_sum'] = (df_long
    .groupby(['BldgType', 'BldgVint', 'BldgHVAC', 'BldgLoc', 'TechID'])['Total_Elec_Consumption']
    .transform('sum'))

#%%
#Calculate unitzed 8760 values based on annual sum of 8760, updated to exclude numunits and UEC
df_long['UECproportion'] = df_long['Total_Elec_Consumption'] / df_long['annual_sum']
#%%
#rearrange / true-up columns
#source year mapping:
StartDayToSourceYear = {
    "Monday": 2018, #Basis year for 2024 electric ACCs
    "Tuesday": 2013, #2013 or 2019 could be used
    "Wednesday": 2020, #Basis for 2022/2021 electric ACCs
    "Thursday": 2009, #Per CEC's Nonres/MFm ACM Reference Manual
    "Friday": 2010, #2016 is Friday but a leap year, so this should be either 2010 or 2021
    "Saturday": 2011, #Next Saturday option is 2022 because it is skipped between 2016 and 2017 because 2016 is a leap year
    "Sunday": 2017 #2012 is a leap year, suggest using 2017
}

df_long['Sector'] = 'Com' #this is Com script, so Sector = Com
df_long['Type (Whole Building or End Use)'] = 'Whole Building'
df_long['Source Year'] = df_long['RunPeriod Start Day'].map(StartDayToSourceYear)

df_long.rename(columns={'hr in 8760': 'Hour of Year'}, inplace=True)

#final table fields round-up
#note: UEC and Numunits omitted from draft long table in the final table
df_long_final = df_long[['Sector', 'BldgType','BldgVint','BldgHVAC','BldgLoc',
         'Type (Whole Building or End Use)', 'Source Year', 'TechGroup', 'TechType','TechID',
         'Hour of Year','UECproportion']] 
#%%
#output annual consumption of each permutation and store for later use if needed
df_long_annual_loads = df_long[[
        'Sector', 'BldgType','BldgVint','BldgHVAC','BldgLoc','Type (Whole Building or End Use)','Source Year', 'TechGroup', 'TechType','TechID','annual_sum'
         ]].drop_duplicates().reset_index(drop=True)

#%%
#export CEDARS long 8760 csv

os.chdir(os.path.dirname(__file__)) #resets to current script directory
print(os.path.abspath(os.curdir))

#enable if html viewer is needed / csv export is needed
df_long_final.to_csv('CEDARS_long_ls_Com.csv', index=False) 
df_long_annual_loads.to_csv('CEDARS_ls_annual_loads_Com.csv', index=False)
#3/4/2026 Dan P. on CEDARS - need to provide as zip format
#%%
import zipfile 

zip_filename = 'CEDARS_LoadShape_Com.zip'
csv_filename_prefix = 'CEDARS_LoadShape_Com_'

with zipfile.ZipFile(zip_filename, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
    #Open a file inside the zip and write CSV to it
    #Loop through each building type and write a separate CSV for each, put into the same zip file
    for bldgtype in df_long_final['BldgType'].unique():
        print(f'writing {bldgtype} csv to zip...')

        csv_filename = f'{csv_filename_prefix}{bldgtype}.csv'
        with zipf.open(csv_filename, 'w') as f:
            df_long_final[df_long_final['BldgType'] == bldgtype].to_csv(f, index=False)
        print(f'{bldgtype} csv written to zip.')

print('CEDARS long 8760 csv exported.')
################################################################################################
################################################################################################
#%%
##############################################
##############################################
## Here resumes the normal post-processing of DEER outputs
# Annual Data final field fixes

#normunit = buildng area(conditioned) for default / example measure

sim_annual_v1['SizingID'] = 'None'
sim_annual_v1['tstat'] = 0
#now Norm unit is read from measure master table
#this may need to be modified if there are more than 1 Normunit(s) within the same batch
sim_annual_v1['Normunit'] = normunit

#%%
#add area based on building type
#also add normunit (also the area) for the example measure
#code may need to be tweaked if normalizing unit is different for a specific measure
#3/2/26 QC check - if Cap-Tons, this code + supporting tables does not address the case. Solaris produced some scripts to extract Cap-Ton, but did not get every building type.

unit_lookup = df_normunits[['BldgType','Normunit','Value']]

#check for missing first
if normunit_missing == True:
    # warnings.warn('Note: normunit = Each, numunit = 1 as placeholder to continue processing without the appropriate normunit.')
    # sim_annual_v1['Value'] = 1
    # sim_annual_v2 = sim_annual_v1
    raise ValueError(
        "Current normalizing unit(s) for this measure not found on Normunit.xlsx table,\n" 
        "please update Normunit.xlsx table appropriately and add corresponding normalizing unit and corresponding unit value(s).\n"
    )
#hard-code specific normunit examples, may be redundant
elif (normunit == 'Each') & (normunit_missing == False):
    unit_table = unit_lookup[unit_lookup['Normunit']=='Each'][['BldgType','Normunit','Value']]
    #sim_annual_v2 = pd.merge(sim_annual_v1, unit_table, on=['BldgType','Normunit'])
    sim_annual_v2 = pd.merge(sim_annual_v1, unit_table, on=['BldgType', 'Normunit'], how="left")
    print(f'normalizing unit is {normunit}, added based on Building Type')
elif (normunit == 'Cap-Tons') & (normunit_missing == False):
    unit_table = unit_lookup[unit_lookup['Normunit']=='Cap-Tons'][['BldgType','Normunit','Value']]
    #sim_annual_v2 = pd.merge(sim_annual_v1, unit_table, on=['BldgType','Normunit'])
    sim_annual_v2 = pd.merge(sim_annual_v1, unit_table, on=['BldgType', 'Normunit'], how="left")
    print(f'normalizing unit is {normunit}, added based on Building Type')
else:
    # Revised 2025-09-25 by Nicholas Fette to resolve KeyError: 'BldgType'
    # Both sim_annual_v1 and unit_lookup have BldgType column when normunit != Each.
    # If "join on" columns omits BldgType, then sim_annual_v2 gets two columns BldgType_x and BldgType_y.
    # sim_annual_v2 = pd.merge(sim_annual_v1, unit_lookup, on=['Normunit','BldgType'])

    #5/14/2026 improvement opportunities for handling Normunits:
    #proposed if-else branch for other generalized Normunit cases.
    #Other edge cases not covered may include but not limited to:
    #What if normalizing unit is not dependent on building type? (some constant, i.e. each, refrigeration reducedkW?)
    #What if normalizing unit is dependent on climate zone? (i.e. auto-sized capacity?)
    #possible revision/improvements: Have normunit + numunit be included in the starting measure workbook
    #possible revision/improvements: Have Measure Name/ID also be an identifier to better manage measure packages

    #work with measure developer(s) / other DEER normalizing units reference to make sure this logic cover all bases

    unit_table = unit_lookup[unit_lookup['Normunit']==normunit][['BldgType','Normunit','Value']]
    sim_annual_v2 = pd.merge(sim_annual_v1, unit_table, on=['BldgType', 'Normunit'], how="left")
    print(f'normalizing unit is {normunit}, added based on Building Type')

sim_annual_v2['numunits'] = sim_annual_v2['Value']

#%%
#do area separately after normunit merge
#5/14/2026 read from a separate Com_area sheet from Normunits.xlsx to avoid confusion
#area_lookup = df_normunits[df_normunits['Normunit']=='Area-ft2-BA'][['BldgType','total_area_m2']]

try:
    com_area_table = pd.read_excel('Normunits.xlsx', sheet_name='Com_area')[['BldgType','measarea']]
#error exception message for file doesn't exist
except FileNotFoundError:
    raise FileNotFoundError(
            "[ERROR] Cannot find workbook 'Normunits.xlsx'.\n"
            "Please make sure 'Normunits.xlsx' exists in the same directory as this script "
            "or provide the correct full path."
        )
except ValueError as e:
    msg = str(e)
    #error exception for missing worksheet name
    if "Worksheet named" in msg or "sheetname" in msg.lower() or "not found" in msg.lower():
        raise ValueError(
            "[ERROR] Worksheet 'Com_area' not found in 'Normunits.xlsx'.\n"
            "Please confirm the sheet name in Excel matches exactly (case-sensitive)."
        ) from e
#error exception for missing fields / empty sheets
except KeyError:
    raise KeyError(
            "[ERROR] Worksheet 'Com_area' have missing required columns: 'BldgType','measarea'."
            "Please make sure those two column exists."
        )
else:
    if com_area_table.empty:
        raise ValueError(
            "[ERROR] Sheet 'Com_area' in 'Normunits.xlsx' is empty (no rows). "
            "Please populate the table with 'BldgType' and 'measarea' values."
        )


#create dict area lookup from table
area_lookup = com_area_table.set_index('BldgType')['measarea'].to_dict()
#sim_annual_v3 = pd.merge(sim_annual_v2, area_lookup, on='BldgType', how='left')

#5/24/2026: measarea field is now in square-ft, which is contained in Normunits.xlsx, in the Com_area worksheet
sim_annual_v2['measarea'] = sim_annual_v2['BldgType'].map(area_lookup)
sim_annual_v3 = sim_annual_v2.copy()
print('measarea (in sqft) added.')

# %%
sim_annual_v3['lastmod']=dt.datetime.now()
sim_annual_v3 = sim_annual_v3.rename(columns={'Normunit':'normunit'})
#rearrange columns
sim_annual_f = sim_annual_v3[['TechID', 'SizingID', 'BldgType','BldgVint','BldgLoc','BldgHVAC','tstat',
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
MeasTechIDs = df_measure[['MeasTechID','Common_MeasTechID']].drop_duplicates()
# %%
#filter out each pre, std, msr using the Common TechIDs from master table
metadata_pre = metadata_cols[metadata_cols['TechID'].isin(PreTechIDs['Common_PreTechID'].unique())]
metadata_std = metadata_cols[metadata_cols['TechID'].isin(StdTechIDs['Common_StdTechID'].unique())]
metadata_msr = metadata_cols[metadata_cols['TechID'].isin(MeasTechIDs['Common_MeasTechID'].unique())]

# %%
#rename to Pre, Std or Msr 
#both Std and Pre are baseline for SEER rated AC measures
metadata_pre = metadata_pre.rename(columns={'TechID':'PreTechID'})
metadata_std = metadata_std.rename(columns={'TechID':'StdTechID'})
metadata_msr = metadata_msr.rename(columns={'TechID':'MeasTechID'})
# %%
#Changing common TechID to actual TechIDs if needed.
#In most cases this is not needed
#only needed when TechID and CommonTechID field on measure mapping workbook is not the same
#might only apply to Res SEER AC/HP and some selected measures

#create full pre_metadata sets for different names but the same TechID
# commom_preTechID = PreTechIDs['Common_PreTechID'].unique()[0]
if False in list(PreTechIDs['PreTechID']==PreTechIDs['Common_PreTechID']):
    metadata_pre_full = pd.DataFrame()
    # Solaris Technical 2024-04-17
    # Corrects an issue where more than one "Common_PreTechID" in
    # the batch of measures causes the renaming step to fail silently
    # and generate duplicate rows with mismatched data.
    for _, (common_id, new_id) in PreTechIDs[['Common_PreTechID','PreTechID']].iterrows():
        print(f'changing to specific PreTechID {new_id}')
        metadata_pre_mod = metadata_pre[metadata_pre['PreTechID']==common_id].copy()
        metadata_pre_mod['PreTechID'] = new_id
        #merge to final df
        metadata_pre_full = pd.concat([metadata_pre_full, metadata_pre_mod])
else:
    print('same TechID, proceeding without changing names')
    metadata_pre_full = metadata_pre.copy()


# %%
#create std_metadata sets, assigning appropriate final TechIDs
if (False in list(StdTechIDs['StdTechID']==StdTechIDs['Common_StdTechID'])):
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
if False in list(MeasTechIDs['MeasTechID']==MeasTechIDs['Common_MeasTechID']):
    metadata_msr_full = pd.DataFrame()
    for common_id, new_id in zip(MeasTechIDs['Common_MeasTechID'], MeasTechIDs['MeasTechID']):
        print(f'common is {common_id}, changing into new id is {new_id}')
        #Identify corresponding common TechID (the last 9 characters indicating SEER levels)
        metadata_msr_mod = metadata_msr[metadata_msr['MeasTechID']==common_id].copy()
        #Change into final TechID name
        metadata_msr_mod['MeasTechID'] = new_id
        #merge to final df
        metadata_msr_full = pd.concat([metadata_msr_full, metadata_msr_mod])
else:
    print('same TechID, proceeding without changing names')
    metadata_msr_full = metadata_msr.copy()
# %%
#create raw merged current_msr_mat
#need to delete/drop incorrect sets
if any(isinstance(i, str) for i in list(StdTechIDs['StdTechID'].unique())) == False:
    # when there is no std tech ID - only pre baseline used in merge
    df_measure_set_full = pd.merge(metadata_pre_full, metadata_msr_full, on=['BldgLoc','BldgType','BldgVint','BldgHVAC','SizingID','tstat','normunit'])
elif any(isinstance(i, str) for i in list(PreTechIDs['PreTechID'].unique())) == False:
    # when there is no pre tech ID - only std baseline used in merge
    df_measure_set_full = pd.merge(metadata_std_full, metadata_msr_full, on=['BldgLoc','BldgType','BldgVint','BldgHVAC','SizingID','tstat','normunit'])
else:
    # when both std tech and pre tech ID present - use both
    df_measure_baseline_full = pd.merge(metadata_pre_full, metadata_std_full, on=['BldgLoc','BldgType','BldgVint','BldgHVAC','SizingID','tstat','normunit'])
    df_measure_set_full = pd.merge(df_measure_baseline_full, metadata_msr_full, on=['BldgLoc','BldgType','BldgVint','BldgHVAC','SizingID','tstat','normunit'])

# %%
#Unique sets of each MeasureID with their TechID triplets
TechID_triplets = df_measure[['EnergyImpactID','MeasureID', 'PreTechID', 'StdTechID','MeasTechID']].drop_duplicates()
# %%
#to match TechID triplets, merge on these 3 fields, keeping only valid TechID Triplets
if any(isinstance(i, str) for i in list(StdTechIDs['StdTechID'].unique())) == False:
    # when there is no std tech ID - only pre baseline used in merge
    current_msr_mat_proto = pd.merge(df_measure_set_full, TechID_triplets, on=['PreTechID','MeasTechID'])
elif any(isinstance(i, str) for i in list(PreTechIDs['PreTechID'].unique())) == False:
    # when there is no pre tech ID - only std baseline used in merge
    current_msr_mat_proto = pd.merge(df_measure_set_full, TechID_triplets, on=['StdTechID','MeasTechID'])
else:
    # when both std tech and pre tech ID present - use both
    current_msr_mat_proto = pd.merge(df_measure_set_full, TechID_triplets, on=['PreTechID','StdTechID','MeasTechID'])

# %%
#add placeholders, rearrange fields
current_msr_mat_proto['PreSizingID']='None'
current_msr_mat_proto['StdSizingID']='None'
current_msr_mat_proto['MsrSizingID']='None'
current_msr_mat_proto['SizingSrc']=np.nan

#to be worked on: need to add corresponding indicator for what enduse it is for end use loadshape connections
current_msr_mat_proto['EU_HrRepVar']=np.nan

current_msr_mat = current_msr_mat_proto[['MeasureID', 'BldgType', 'BldgVint','BldgLoc','BldgHVAC','tstat','PreTechID','PreSizingID',
                             'StdTechID', 'StdSizingID','MeasTechID','MsrSizingID','SizingSrc','EU_HrRepVar','normunit']]
current_msr_mat = current_msr_mat.rename(columns={'normunit':'NormUnit'})

# %%
#check length of current_msr_mat
len(current_msr_mat)

# %%
##STEP 5: Clean Up Sequence
#Again, in most cases this is not needed
#only needed when TechID and CommonTechID field on measure mapping workbook is not the same
#might only apply to Res SEER AC/HP and some selected measures
#Creating updated Sim_annual and Sim_hourly data with distinguished TechID names if needed. 
sim_annual_pre_common = sim_annual_f[sim_annual_f['TechID'].isin(PreTechIDs['Common_PreTechID'].unique())]
sim_annual_std_common = sim_annual_f[sim_annual_f['TechID'].isin(StdTechIDs['Common_StdTechID'].unique())]
sim_annual_msr_common = sim_annual_f[sim_annual_f['TechID'].isin(MeasTechIDs['Common_MeasTechID'].unique())]
# %%
#Add a TechID col renaming the common TechID to the specific TechID using PreTechIDs, StdTechIDs, MeasTechIDs

#create full pre sim_annual sets for different names but the same TechID
# commom_preTechID = PreTechIDs['Common_PreTechID'].unique()[0]
if False in list(PreTechIDs['PreTechID']==PreTechIDs['Common_PreTechID']):
    sim_annual_pre = pd.DataFrame()
    for _, (common_id, new_id) in PreTechIDs[['Common_PreTechID','PreTechID']].iterrows():
        print(f'changing to specific PreTechID {new_id}')
        sim_annual_pre_mod = sim_annual_pre_common[sim_annual_pre_common['TechID']==common_id].copy()
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
if False in list(MeasTechIDs['MeasTechID']==MeasTechIDs['Common_MeasTechID']):
    sim_annual_msr = pd.DataFrame()
    for common_id, new_id in zip(MeasTechIDs['Common_MeasTechID'], MeasTechIDs['MeasTechID']):
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
sim_hourly_msr_common = sim_hourly_f[sim_hourly_f['TechID'].isin(MeasTechIDs['Common_MeasTechID'].unique())]

# %%
#Pre hourly
if False in list(PreTechIDs['PreTechID']==PreTechIDs['Common_PreTechID']):
    sim_hourly_pre = pd.DataFrame()
    for _, (common_id, new_id) in PreTechIDs[['Common_PreTechID','PreTechID']].iterrows():
        print(f'changing to specific PreTechID {new_id}')
        sim_hourly_pre_mod = sim_hourly_pre_common[sim_hourly_pre_common['TechID']==common_id].copy()
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
if False in list(MeasTechIDs['MeasTechID']==MeasTechIDs['Common_MeasTechID']):
    sim_hourly_msr = pd.DataFrame()
    for common_id, new_id in zip(MeasTechIDs['Common_MeasTechID'], MeasTechIDs['MeasTechID']):
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

os.chdir(os.path.dirname(__file__)) #resets to current script directory
print(os.path.abspath(os.curdir))

current_msr_mat.to_csv('current_msr_mat.csv', index=False)
sim_annual_final.to_csv('sim_annual.csv', index=False)
sim_hourly_final.to_csv('sim_hourly_wb.csv', index=False)
# %%
