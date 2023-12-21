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
#Shows list of measure names (with workpaper ID) 
print(measures)
#%%
#Define measure name here (name of the measure folder itself)
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
                                    'SUn'],
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
    'BldgVint': ['Ex','New']+['2015',
                                '2023',
                                '2003',
                                '1975',
                                '2007',
                                '2011',
                                '2020',
                                '2017',
                                '1996',
                                '1985'],
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

#annual parsing function for Com
def annual_raw_parsing_com(df, bldgvint, cohort_dict):
    #create separated meta data cols
    df['BldgLoc'] = split_meta_cols_all[0]

    df['BldgType'] = split_meta_cols_all[1]
    #df['BldgHVAC'] = m_df['BldgHVAC'] #using mapping workbook for now  
    #not robust. best way is to have cohort file name have this info

    df['BldgHVAC'] = cohort_dict['BldgHVAC'] #this should be cohort folder names
    #but using mapping workbook field as proxy
    df['BldgVint'] = bldgvint #in the loop, bldgvint 

    df['Story'] = 0 #no need for stories indication for com

    df['TechGroup_TechType'] = cohort_dict['Measure']

    df['TechID'] = split_meta_cols_all[2]
    df['file'] = split_meta_cols_all[3]
    
    #COM modelkit output is kBtu for the time being. change this after fix

    # annual_df_v1 = df[['TechID', 'file', 'BldgLoc', 'BldgType','BldgHVAC','BldgVint','Story', 'TechGroup_TechType','Total (kWh)', 'Heating (kWh)', 'Cooling (kWh)',
    #    'Interior Lighting (kWh)', 'Exterior Lighting (kWh)',
    #    'Interior Equipment (kWh)', 'Exterior Equipment (kWh)', 'Fans (kWh)',
    #    'Pumps (kWh)', 'Heat Rejection (kWh)', 'Humidification (kWh)',
    #    'Heat Recovery (kWh)', 'Water Systems (kWh)', 'Refrigeration (kWh)',
    #    'Generators (kWh)', 'Heating Elec (kWh)', 'Cooling Elec (kWh)',
    #    'Heating NG (kWh)', 'Cooling NG (kWh)', 'Interior Equipment Elec (kWh)',
    #    'Interior Equipment NG (kWh)']]
    
    annual_df_v1 = df[['TechID', 'file', 'BldgLoc', 'BldgType','BldgHVAC','BldgVint','Story', 'TechGroup_TechType','Total (kBtu)', 'Heating (kBtu)', 'Cooling (kBtu)',
       'Interior Lighting (kBtu)', 'Exterior Lighting (kBtu)',
       'Interior Equipment (kBtu)', 'Exterior Equipment (kBtu)', 'Fans (kBtu)',
       'Pumps (kBtu)', 'Heat Rejection (kBtu)', 'Humidification (kBtu)',
       'Heat Recovery (kBtu)', 'Water Systems (kBtu)', 'Refrigeration (kBtu)',
       'Generators (kBtu)', 'Heating Elec (kBtu)', 'Cooling Elec (kBtu)',
       'Heating NG (kBtu)', 'Cooling NG (kBtu)', 'Interior Equipment Elec (kBtu)',
       'Interior Equipment NG (kBtu)']]
    
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
                            df_in['Pumps (kWh)'])

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
    df_in['kwh_refg'] = 0 
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

#test case for for-loop

df_annual_raw = pd.DataFrame()
split_meta_cols_all = pd.DataFrame()
folder_list = list_folders_in_path(filepath)
for folder in folder_list:
    bldgvint = folder[-4:]
    print(f"looking at vintage {bldgvint} folder..")
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


#%%
#after looping to read the raw results-summary.csv

df_parsed_test = annual_raw_parsing_com(df_annual_raw, 1975, cohort_dict)

#parse this as a whole? BldgHVAC needs record/filepath specific reference. this is a placeholder for now.


#%%
cohort_cases = list(df_measure['Measure Group Name'])
for case in cohort_cases:
    print(case)
    cohort_dict = parse_measure_name(case)
    print(cohort_dict)



# %%
# %%

#test case for single folder
filepath_single = filepath + "/SWXX111-00 Example_SEER_AC_1975"
bldgvint_single = '1975'

df_raw = pd.read_csv(filepath_single+'/results-summary.csv', usecols=['File Name'])
num_runs = len(df_raw['File Name'].dropna().unique()) - 1
#Read annual data
annual_df = pd.read_csv(filepath_single+'/results-summary.csv', nrows=num_runs, skiprows=num_runs+2)
split_meta_cols_eu = annual_df['File Name'].str.split('/', expand=True)
# %%
#if looping over multiple folders/cohort cases, use a list
#(supposed to be the actual cohort with &s for Res case)
#for Com's case, it's the building type

#Res version
#cohort_cases = list(split_meta_cols_eu[1].unique())

#Com version for now
#12/21/2023 use "measure group name" column as proxy for Com for now, but cohort (files in each measure subfolder) should be named accordingly?
cohort_cases = list(df_measure['Measure Group Name'])
# %%
for case in cohort_cases:
    print(case)
    cohort_dict = parse_measure_name(case)
    print(cohort_dict)



#%%
sim_annual_proto = pd.DataFrame()
for case in cohort_cases:
    print(f'processing all annual data that are grouped in {case}')
    cohort_dict = parse_measure_name(case)
    sim_annual_i = annual_raw_parsing_com(annual_df[annual_df['File Name'].str.contains(case)].copy(), cohort_dict)
    sim_annual_proto = pd.concat([sim_annual_proto, sim_annual_i])
    print('ok.')
sim_annual_proto = end_use_rearrange(sim_annual_proto)

sim_annual_v1 = sim_annual_proto[['TechID', 'BldgLoc', 'BldgType', 'BldgHVAC', 'BldgVint', 'kwh_tot', 'kwh_ltg', 'kwh_task',
    'kwh_equip', 'kwh_htg', 'kwh_clg', 'kwh_twr', 'kwh_aux', 'kwh_vent',
    'kwh_venthtg', 'kwh_ventclg',
    'kwh_refg', 'kwh_hpsup', 'kwh_shw', 'kwh_ext', 'thm_tot', 'thm_equip',
    'thm_htg', 'thm_shw', 'deskw_ltg', 'deskw_equ']].drop_duplicates().copy()
# %%
