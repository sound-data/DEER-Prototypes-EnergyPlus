#%%
##STEP 0: Setup (import all necessary libraries)
import pandas as pd
import numpy as np
import os
import sys
import datetime as dt
os.chdir(os.path.dirname(__file__)) #resets to current script directory
# %%
#Read master workbook for measure / tech list
df_master = pd.read_excel('DEER_EnergyPlus_Modelkit_Measure_list_working.xlsx', sheet_name='Measure_list', skiprows=4)

measure_group_names = list(df_master['Measure Group Name'].unique())

# %%
#generate unique list of measure names for Com

df_com = df_master[df_master['Sector']=='Com']

measures = list(df_com['Modelkit Folder Primary Name'].unique())
# %%
#Shows list of commercial measure names (with workpaper ID) 
print(measures)
#%%
#Define measure name here (name of the measure folder itself
##NOTE: The example folder used here, 'SWXX111-00 Example_SEER_AC' is only used to illustrate an example workflow thru post-procesing
measure_name = 'SWXX111-00 Example_SEER_AC'

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
filepath = f'commercial measures/{measure_name}'

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
hourly_df = pd.DataFrame(index=range(0,8760))

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
            print(f"merging record {i}")
            
            #loop path of each file, read corresponding file
            full_path = hrly_subpath + "/" + split_meta_cols_eu.iloc[i][0] + "/" + split_meta_cols_eu.iloc[i][1] + "/" + split_meta_cols_eu.iloc[i][2] + "/instance-var.csv"
            df = pd.read_csv(full_path, low_memory=False)
            #remove traling spaces on col headers
            df.columns = df.columns.str.rstrip()
        
            #8/1/2024 update: extract the electricy column only
            #if for enduse hourly, then extract the relevant end use column
            extracted_df = pd.DataFrame(df['Electricity:Facility [J](Hourly)'])
            
            #create the column name based on the permutations
            col_name = split_meta_cols_eu.iloc[i][0] + "/" + split_meta_cols_eu.iloc[i][1] + "/" + split_meta_cols_eu.iloc[i][2] + "/instance-var.csv"
            
            #change column name
            extracted_df = extracted_df.set_axis([col_name],axis=1)
            if len(extracted_df)!=8760:
                #8/31/2022 update, need to make the final length 8808. Snip data based on difference to 8760
                record_count_diff = len(extracted_df) - 8760
                print(f'extra records: {str(len(extracted_df))}, snipping away {record_count_diff} records and changing to 8760')
                extracted_df = extracted_df.iloc[record_count_diff:].reset_index(drop=True)
            
            #left-merge onto big df
            hourly_df = hourly_df.merge(extracted_df, left_index=True, right_index=True)
        print(f"hourly data for '{subpath}' processed.")
    else:
        print(f"no data found.")




# %%
fyr_hrly = hourly_df
#rearrange 1-column 8760 format to 365x24 wide format for all runs in hourly_df
converted_df = pd.DataFrame()

for i in range(0,len(fyr_hrly.columns)):
    
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
    hrly_wide['BldgType'] = col_names[1][0:3]  #slight mod to only extract first 3 letters for bldgtype
    hrly_wide['TechID'] = col_names[2]
    hrly_wide['file'] = col_names[3]
    
    #append to master df
    #converted_df = converted_df.append(hrly_wide) #deprecated method
    converted_df = pd.concat([converted_df, hrly_wide])
    print(f"col {i} transformed.")

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
bldgtype = 'Com'
os.chdir(os.path.dirname(__file__)) #resets to current script directory
print(os.path.abspath(os.curdir))
# %%
df_normunits = pd.read_excel('Normunits.xlsx', sheet_name=bldgtype)
# %%
normunit = df_measure['Normunit'].unique()[0]
#%%
##Annual Data final field fixes

#normunit = buildng area(conditioned) for default / example measure

sim_annual_v1['SizingID'] = 'None'
sim_annual_v1['tstat'] = 0
#now Norm unit is read from measure master table
#this may need to be modified based on the measure
sim_annual_v1['Normunit'] = normunit

#%%
#add area based on building type
#also add normunit (also the area) for the example measure
#code may need to be tweaked if normalizing unit is different for a specific measure

unit_lookup = df_normunits[['BldgType', 'Normunit', 'Value']]
if normunit == 'Each':
    unit_table = unit_lookup[unit_lookup['Normunit']=='Each'][['Normunit','Value']]
    sim_annual_v2 = pd.merge(sim_annual_v1, unit_table, on='Normunit')
else:
    sim_annual_v2 = pd.merge(sim_annual_v1, unit_lookup, on='Normunit')
sim_annual_v2['numunits'] = sim_annual_v2['Value']

#%%
#do area separately after normunit merge
area_lookup = df_normunits[df_normunits['Normunit']=='Area-ft2-BA'][['BldgType','total_area_m2']]

sim_annual_v3 = pd.merge(sim_annual_v2, area_lookup, on='BldgType')
sim_annual_v3['measarea'] = sim_annual_v3['total_area_m2']

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
