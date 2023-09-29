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
df_master = pd.read_excel('DEER_EnergyPlus_Modelkit_Measure_list.xlsx', sheet_name='Measure_list', skiprows=4)

measure_group_names = list(df_master['Measure Group Name'].unique())

# %%
#generate unique list of measure names
measures = list(df_master['Measure (general name)'].unique())
# %%
#Shows list of measure names 
print(measures)
#%%
#Define measure name here
measure_name = 'Wall Furnace'

# %%
#SFm only script
####Define path
os.chdir(os.path.dirname(__file__)) #resets to current script directory
print(os.path.abspath(os.curdir))
os.chdir("../..") #go up two directory
print(os.path.abspath(os.curdir))

#input the two subdirectory of SFm, one being 1975, the other 1985. If New vintage, input path at path_new and leave other blank.
path_1975 = 'Analysis/SFm_Furnace_1975'
path_1985 = 'Analysis/SFm_Furnace_1985'
path_new = ''

paths = [path_1975, path_1985]

if path_new != '' :
    paths = [path_new]
# %%
#extract only the 5th portion of the measure group name for expected_att
#split argument 4 means only split 4 times maximum
techgroup_techtypes = [i.split('&', 4)[-1] for i in measure_group_names]
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

#function to uses the “File Name” column from the results-summary csv to identify directory structure (an organized table) of a batch run 
# and uses the structure to construct a semi-organized annual outputs table.
def annual_raw_parsing(df, cohort_dict):
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
def end_use_rearrange(df):
        #end use rearrangement
    df['kwh_tot'] = (df['Heating Elec (kWh)'] + \
                                df['Cooling Elec (kWh)'] +\
                                df['Interior Equipment Elec (kWh)'] +\
                                df['Interior Lighting (kWh)'] +\
                                df['Exterior Lighting (kWh)'] +\
                                df['Fans (kWh)']+\
                                df['Pumps (kWh)'])

    df['kwh_ltg'] = (df['Interior Lighting (kWh)'] +\
                                    df['Exterior Lighting (kWh)'])

    df['kwh_task'] = 0 # placeholder (task lighting load?)

    df['kwh_equip'] = df['Interior Equipment Elec (kWh)'] +\
                                    df['Exterior Equipment (kWh)']

    df['kwh_htg'] = df['Heating Elec (kWh)']

    df['kwh_clg'] = df['Cooling Elec (kWh)']

    df['kwh_twr'] = 0 #place holder (tower kwh load?)
    df['kwh_aux'] = 0 #place holder (aux equipment kwh load?)
    df['kwh_vent'] = df['Fans (kWh)'] #use fan kWh as vent load for now

    df['kwh_venthtga'] =0 #placeholders fields..
    df['kwh_ventclga'] =0

    df['kwh_venthtgb'] =0
    df['kwh_ventclgb'] =0

    df['kwh_refg'] = 0 
    df['kwh_hpsup'] = 0
    df['kwh_shw'] = 0
    df['kwh_ext'] = 0

    df['thm_tot'] = (df['Heating NG (kWh)'] +\
                                df['Cooling NG (kWh)'] +\
                                df['Interior Equipment NG (kWh)'] +\
                                df['Water Systems (kWh)'])/29.3

    df['thm_equip'] = df['Interior Equipment NG (kWh)']/29.3

    df['thm_htg'] = df['Heating NG (kWh)']/29.3

    df['thm_shw'] = df['Water Systems (kWh)']/29.3

    df['deskw_ltg'] = 1 #placeholders fields for now
    df['deskw_equ'] = 1

    annual_df_final = df[['TechID', 'BldgLoc', 'BldgType','BldgHVAC', 'BldgVint', 'kwh_tot', 'kwh_ltg', 'kwh_task',
       'kwh_equip', 'kwh_htg', 'kwh_clg', 'kwh_twr', 'kwh_aux', 'kwh_vent',
       'kwh_venthtga', 'kwh_ventclga', 'kwh_venthtgb', 'kwh_ventclgb',
       'kwh_refg', 'kwh_hpsup', 'kwh_shw', 'kwh_ext', 'thm_tot', 'thm_equip',
       'thm_htg', 'thm_shw']]
    
    return annual_df_final

# %%
#create measure specific Master table based on Measure selected
df_measure = df_master[df_master['Measure (general name)'] == measure_name]
case_cohort_list = df_measure['Measure Group Name'].unique()

# %%
##STEP 1: Annual data extraction / transformation
sim_annual_raw = pd.DataFrame()
for path in paths:
    print(f'processing data in {path}')
    df_raw = pd.read_csv(path+'/'+'/results-summary.csv', usecols=['File Name'])
    num_runs = len(df_raw['File Name'].dropna().unique()) - 1
    #Read annual data
    annual_df = pd.read_csv(path+'/'+'/results-summary.csv', nrows=num_runs, skiprows=num_runs+2)
    split_meta_cols_eu = annual_df['File Name'].str.split('/', expand=True)

    #looping over multiple folders/cohort cases, use a list
    cohort_cases = list(split_meta_cols_eu[1].unique())
    sim_annual_proto = pd.DataFrame()
    for case in cohort_cases:
        print(f'processing all annual data that are grouped in {case}')
        cohort_dict = parse_measure_name(case)
        sim_annual_i = annual_raw_parsing(annual_df[annual_df['File Name'].str.contains(case)].copy(), cohort_dict)
        sim_annual_proto = pd.concat([sim_annual_proto, sim_annual_i])
        print('ok.')
    sim_annual_raw = pd.concat([sim_annual_raw, sim_annual_proto])

#%%

#seperate into 1-story and 2-story, SFm, New vintage, (no need to separate DXGF and NCGF if combined)

sim_annual_1s = sim_annual_raw[sim_annual_raw['Story']=='1'].copy()
sim_annual_2s = sim_annual_raw[sim_annual_raw['Story']=='2'].copy()
# %%
#apply enduse rearrangement
sim_annual_1s_v1 = end_use_rearrange(sim_annual_1s)
sim_annual_2s_v1 = end_use_rearrange(sim_annual_2s)


# %%
##STEP 2: Hourly data extraction / transformation
#Read 8760 map
os.chdir(os.path.dirname(__file__)) #resets to current script directory
print(os.path.abspath(os.curdir))
annual_map = pd.read_excel('annual8760map.xlsx')
hrly_paths = paths


#%%
os.chdir("../..") #go up two directories
print(os.path.abspath(os.curdir))

sim_hourly_raw = pd.DataFrame()

for path in paths:
    print(f'processing data in {path}')
    hrly_path = path + '/runs' 

    #extract data per bldgtype-bldghvac-bldgvint group
    hourly_df = pd.DataFrame(index=range(0,8760))
    #extract num_runs / split_meta_cols_eu
    df_raw = pd.read_csv(path+'/'+'/results-summary.csv', usecols=['File Name'])
    num_runs = len(df_raw['File Name'].dropna().unique()) - 1
    annual_df = pd.read_csv(path+'/'+'/results-summary.csv', nrows=num_runs, skiprows=num_runs+2)
    split_meta_cols_eu = annual_df['File Name'].str.split('/', expand=True)
    for i in range(0,num_runs):
        print(f"merging record {i}")
        
        #loop path of each file, read corresponding file
        full_path = hrly_path + "/" + split_meta_cols_eu.iloc[i][0] + "/" + split_meta_cols_eu.iloc[i][1] + "/" + split_meta_cols_eu.iloc[i][2] + "/instance-var.csv"
        df = pd.read_csv(full_path, low_memory=False)
        
        #extract the last column (the total elec hrly profile)
        #if for enduse hourly, then extract the relevant end use column
        extracted_df = pd.DataFrame(df.iloc[:,-1])
        
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
        hrly_wide['BldgType'] = col_names[1]
        hrly_wide['TechID'] = col_names[2]
        hrly_wide['file'] = col_names[3]
        
        #append to master df
        #converted_df = converted_df.append(hrly_wide) #deprecated method
        converted_df = pd.concat([converted_df, hrly_wide])
        print(f"col {i} transformed.")

    sim_hourly_raw = pd.concat([sim_hourly_raw, converted_df])


# %%
#rearrange columns
sim_hourly_wb_proto = sim_hourly_raw[['TechID','file','BldgLoc','BldgType','ID','daynum',1,          2,          3,          4,          5,
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
           'hr19',     'hr20',     'hr21',     'hr22',     'hr23',     'hr24']]
# %%
#separate into 1s and 2s for hourly
sim_hourly_wb_1s_v1 = sim_hourly_wb_v1[sim_hourly_wb_v1['BldgType'].str.contains('&1&')].copy()
sim_hourly_wb_2s_v1 = sim_hourly_wb_v1[sim_hourly_wb_v1['BldgType'].str.contains('&2&')].copy()
# %%
##STEP 3: 1-S, 2-S combination, and Normalizing Units
# annual data
rename_1s_fields = {'kwh_tot':'kwh_tot1', 
                    'kwh_ltg':'kwh_ltg1',
                    'kwh_task':'kwh_task1', 
                    'kwh_equip':'kwh_equip1',
                    'kwh_htg':'kwh_htg1',
                    'kwh_clg':'kwh_clg1',                    
                    'kwh_twr':'kwh_twr1',
                    'kwh_aux':'kwh_aux1', 
                    'kwh_vent':'kwh_vent1',
                    'kwh_venthtga':'kwh_venthtg1a', 
                    'kwh_ventclga':'kwh_ventclg1a', 
                    'kwh_venthtgb':'kwh_venthtg1b', 
                    'kwh_ventclgb':'kwh_ventclg1b',
                    'kwh_refg':'kwh_refg1', 
                    'kwh_hpsup':'kwh_hpsup1',
                    'kwh_shw':'kwh_shw1', 
                    'kwh_ext':'kwh_ext1', 
                    'thm_tot':'thm_tot1',
                    'thm_htg':'thm_htg1',
                    'thm_equip':'thm_equip1',
                    'thm_shw':'thm_shw1'}

rename_2s_fields = {'kwh_tot':'kwh_tot2', 
                    'kwh_ltg':'kwh_ltg2',
                    'kwh_task':'kwh_task2', 
                    'kwh_equip':'kwh_equip2',
                    'kwh_htg':'kwh_htg2',
                    'kwh_clg':'kwh_clg2',                    
                    'kwh_twr':'kwh_twr2',
                    'kwh_aux':'kwh_aux2', 
                    'kwh_vent':'kwh_vent2',
                    'kwh_venthtga':'kwh_venthtg2a', 
                    'kwh_ventclga':'kwh_ventclg2a', 
                    'kwh_venthtgb':'kwh_venthtg2b', 
                    'kwh_ventclgb':'kwh_ventclg2b',
                    'kwh_refg':'kwh_refg2', 
                    'kwh_hpsup':'kwh_hpsup2',
                    'kwh_shw':'kwh_shw2', 
                    'kwh_ext':'kwh_ext2', 
                    'thm_tot':'thm_tot2',
                    'thm_htg':'thm_htg2',
                    'thm_equip':'thm_equip2',
                    'thm_shw':'thm_shw2'}

#rename columns
sim_annual_1s = sim_annual_1s_v1.rename(columns=rename_1s_fields)
sim_annual_2s = sim_annual_2s_v1.rename(columns=rename_2s_fields)

# %%
####Finalize Norm units
#Read from normunit table
bldgtype = 'SFm'
os.chdir(os.path.dirname(__file__)) #resets to current script directory
print(os.path.abspath(os.curdir))
df_normunits = pd.read_excel('Normunits.xlsx', sheet_name=bldgtype)
numunits_vals = df_normunits[df_normunits['Normunit'] == df_measure['Normunit'].unique()[0]][['CZ','Value', 'Msr','BldgVint']]

#%%

#create numunits object based on what normunit it uses. 
#numunits can be a single value, or a dictionary
if len(numunits_vals) == 1:
    numunits = numunits_vals[0]
elif df_measure['Normunit'].unique()[0] == 'Area-ft2-BA':
    cz = list(numunits_vals['CZ'])
    nvals = list(numunits_vals['Value'])
    #create dictionary of {cz:values}
    numunits = {cz[i]:nvals[i] for i in range(len(cz))}
elif (measure_name == 'Wall Insulation') or (measure_name == 'Ceiling Insulation'):
    #filter to the corresponding measure
    numunits_vals = numunits_vals[numunits_vals['Msr'] == measure_name]
    #create aligned lists for numunit dictionary
    cz = list(numunits_vals['CZ'])
    nvals = list(numunits_vals['Value'])
    #create dictionary of {cz:values}
    numunits = {cz[i]:nvals[i] for i in range(len(cz))}

elif measure_name == 'PTAC / PTHP':
    #create aligned lists for numunit dictionary
    cz = list(numunits_vals['CZ'])
    vint = list(numunits_vals['BldgVint'])
    nvals = list(numunits_vals['Value'])
    #create dictionary of {(cz,vintage):numunits}
    numunits = {(cz[i],vint[i]):nvals[i] for i in range(len(cz))}
else:
    pass

# %%
#note HVAC type of this dataset
print(sim_annual_1s['BldgHVAC'].unique())

#note HVAC type and its corresponding normalizing unit
#num unit will be per dwelling, so use normunit / num of dwellings (2 for SFM & DMo, 24 for MFm)
sim_annual_1s.reset_index(inplace=True)
sim_annual_1s['SizingID'] = 'None'
sim_annual_1s['tstat'] = 0
sim_annual_1s['normunit'] = df_measure['Normunit'].unique()[0]

#apply numunits appropriately
if (measure_name == 'Wall Insulation') or (measure_name == 'Ceiling Insulation'):
    sim_annual_1s['numunits'] = (sim_annual_1s['BldgLoc'].map(numunits))/2
elif df_measure['Normunit'].unique()[0] == 'Area-ft2-BA':
    sim_annual_1s['numunits'] = (sim_annual_1s['BldgLoc'].map(numunits))/2
elif measure_name == 'PTAC / PTHP':
    sim_annual_1s['numunits'] = (pd.Series(list(zip(sim_annual_1s['BldgLoc'],sim_annual_1s['BldgVint']))).map(numunits))/2
else:
    sim_annual_1s['numunits'] = numunits/2

#%%
sim_annual_2s.reset_index(inplace=True)
sim_annual_2s['SizingID'] = 'None'
sim_annual_2s['tstat'] = 0
sim_annual_2s['normunit'] = df_measure['Normunit'].unique()[0]

#apply numunits appropriately
if (measure_name == 'Wall Insulation') or (measure_name == 'Ceiling Insulation'):
    sim_annual_2s['numunits'] = (sim_annual_2s['BldgLoc'].map(numunits))/2
elif df_measure['Normunit'].unique()[0] == 'Area-ft2-BA':
    sim_annual_2s['numunits'] = (sim_annual_2s['BldgLoc'].map(numunits))/2
elif measure_name == 'PTAC / PTHP':
    sim_annual_2s['numunits'] = (pd.Series(list(zip(sim_annual_2s['BldgLoc'],sim_annual_2s['BldgVint']))).map(numunits))/2
else:
    sim_annual_2s['numunits'] = numunits/2

#%%

#merge 1-s and 2-s results back together side by side
sim_annual_final = pd.merge(sim_annual_1s, sim_annual_2s, on=['TechID', 'SizingID', 'BldgType', 'BldgLoc','BldgHVAC','BldgVint','tstat','normunit','numunits'])
sim_annual_final['lastmod']=dt.datetime.now()

#%%
#rearrange columns
sim_annual_f = sim_annual_final[['TechID', 'SizingID', 'BldgType','BldgVint','BldgLoc','BldgHVAC','tstat',
       'normunit', 'numunits', 'kwh_tot1', 'kwh_ltg1', 'kwh_task1',
       'kwh_equip1', 'kwh_htg1', 'kwh_clg1', 'kwh_twr1', 'kwh_aux1',
       'kwh_vent1', 'kwh_venthtg1a', 'kwh_ventclg1a', 'kwh_venthtg1b',
       'kwh_ventclg1b', 'kwh_refg1', 'kwh_hpsup1', 'kwh_shw1', 'kwh_ext1',
       'thm_tot1', 'thm_equip1', 'thm_htg1', 'thm_shw1','kwh_tot2', 'kwh_ltg2',
       'kwh_task2', 'kwh_equip2', 'kwh_htg2', 'kwh_clg2', 'kwh_twr2',
       'kwh_aux2', 'kwh_vent2', 'kwh_venthtg2a', 'kwh_ventclg2a',
       'kwh_venthtg2b', 'kwh_ventclg2b', 'kwh_refg2', 'kwh_hpsup2', 'kwh_shw2',
       'kwh_ext2', 'thm_tot2', 'thm_equip2', 'thm_htg2', 'thm_shw2', 'lastmod']]
# %%
###Finalize Hourly data

#hourly data
#1story
#rename some fields to fit MC3 output
#add some placeholder fields to fit MC3 output
df_tmp = parse_measure_name2(sim_hourly_wb_1s_v1['ID'],verify=True)
sim_hourly_wb_1s_v1['BldgVint'] = df_tmp['BldgVint']
sim_hourly_wb_1s_v1['BldgHVAC'] = df_tmp['BldgHVAC']
sim_hourly_wb_1s_v1['BldgType'] = df_tmp['BldgType']
del df_tmp
sim_hourly_wb_1s_v1['SizingID'] = 'None'
sim_hourly_wb_1s_v1['tstat'] = 0
sim_hourly_wb_1s_v1['enduse'] = 0

#2story
#rename some fields to fit MC3 output
#add some placeholder fields to fit MC3 output
df_tmp = parse_measure_name2(sim_hourly_wb_2s_v1['ID'],verify=True)
sim_hourly_wb_2s_v1['BldgVint'] = df_tmp['BldgVint']
sim_hourly_wb_2s_v1['BldgHVAC'] = df_tmp['BldgHVAC']
sim_hourly_wb_2s_v1['BldgType'] = df_tmp['BldgType']
del df_tmp
sim_hourly_wb_2s_v1['SizingID'] = 'None'
sim_hourly_wb_2s_v1['tstat'] = 0
sim_hourly_wb_2s_v1['enduse'] = 0
# %%
rename_1s_hrly = {'hr01':'hr01a', 
                  'hr02':'hr02a',
                  'hr03':'hr03a', 
                  'hr04':'hr04a',
                  'hr05':'hr05a', 
                  'hr06':'hr06a', 
                  'hr07':'hr07a', 
                  'hr08':'hr08a', 
                  'hr09':'hr09a', 
                  'hr10':'hr10a', 
                  'hr11':'hr11a',
                  'hr12':'hr12a', 
                  'hr13':'hr13a', 
                  'hr14':'hr14a', 
                  'hr15':'hr15a', 
                  'hr16':'hr16a', 
                  'hr17':'hr17a', 
                  'hr18':'hr18a', 
                  'hr19':'hr19a', 
                  'hr20':'hr20a',
                  'hr21':'hr21a', 
                  'hr22':'hr22a', 
                  'hr23':'hr23a', 
                  'hr24':'hr24a'}
rename_2s_hrly = {'hr01':'hr01b', 
                  'hr02':'hr02b',
                  'hr03':'hr03b', 
                  'hr04':'hr04b',
                  'hr05':'hr05b', 
                  'hr06':'hr06b', 
                  'hr07':'hr07b', 
                  'hr08':'hr08b', 
                  'hr09':'hr09b', 
                  'hr10':'hr10b', 
                  'hr11':'hr11b',
                  'hr12':'hr12b', 
                  'hr13':'hr13b', 
                  'hr14':'hr14b', 
                  'hr15':'hr15b', 
                  'hr16':'hr16b', 
                  'hr17':'hr17b', 
                  'hr18':'hr18b', 
                  'hr19':'hr19b', 
                  'hr20':'hr20b',
                  'hr21':'hr21b', 
                  'hr22':'hr22b', 
                  'hr23':'hr23b', 
                  'hr24':'hr24b'}

#rename hourly columns
sim_hourly_1s = sim_hourly_wb_1s_v1.rename(columns=rename_1s_hrly)
sim_hourly_2s = sim_hourly_wb_2s_v1.rename(columns=rename_2s_hrly)

#rearrange cols
sim_hourly_1s_re = sim_hourly_1s[['TechID','SizingID','BldgType','BldgVint','BldgLoc','BldgHVAC','tstat','enduse','daynum','hr01a',
       'hr02a', 'hr03a', 'hr04a', 'hr05a', 'hr06a', 'hr07a', 'hr08a', 'hr09a',
       'hr10a', 'hr11a', 'hr12a', 'hr13a', 'hr14a', 'hr15a', 'hr16a', 'hr17a',
       'hr18a', 'hr19a', 'hr20a', 'hr21a', 'hr22a', 'hr23a', 'hr24a']]

sim_hourly_2s_re = sim_hourly_2s[['TechID','SizingID','BldgType','BldgVint','BldgLoc','BldgHVAC','tstat','enduse','daynum','hr01b',
       'hr02b', 'hr03b', 'hr04b', 'hr05b', 'hr06b', 'hr07b', 'hr08b', 'hr09b',
       'hr10b', 'hr11b', 'hr12b', 'hr13b', 'hr14b', 'hr15b', 'hr16b', 'hr17b',
       'hr18b', 'hr19b', 'hr20b', 'hr21b', 'hr22b', 'hr23b', 'hr24b']]

#merge columns of 1s and 2s
sim_hourly_final = pd.merge(sim_hourly_1s_re, sim_hourly_2s_re, on=['TechID', 'SizingID','BldgType','BldgVint','BldgLoc','BldgHVAC','tstat','enduse','daynum'])
sim_hourly_final['lastmod']=dt.datetime.now()

#%%
#Create CZ:VintYear dictionary based on prototype definitions
cz_list1 = ['CZ01','CZ02','CZ03','CZ04','CZ05','CZ06','CZ07','CZ08','CZ09']
cz_list2 = ['CZ10','CZ11','CZ12','CZ13','CZ14','CZ15','CZ16']

cz_vint_dict1 = {i:'1975' for i in cz_list1}
cz_vint_dict2 = {i:'1985' for i in cz_list2}

cz_vint_dict = cz_vint_dict1 | cz_vint_dict2

#%%
##BldgVint label correction for NumStor weights
sim_annual_f['BldgVint'] = sim_annual_f['BldgLoc'].map(cz_vint_dict)
sim_hourly_final['BldgVint'] = sim_hourly_final['BldgLoc'].map(cz_vint_dict)

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
#might only apply to SEER AC/HP

#create full pre_metadata sets for different names but the same TechID
# commom_preTechID = PreTechIDs['Common_PreTechID'].unique()[0]
if False in list(PreTechIDs['PreTechID']==PreTechIDs['Common_PreTechID']):
    metadata_pre_full = pd.DataFrame()
    for _, (common_id, new_id) in PreTechIDs[['Common_PreTechID', 'PreTechID']].iterrows():
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
if np.NaN in list(StdTechIDs['StdTechID'].unique()):
    df_measure_set_full = pd.merge(metadata_pre_full, metadata_msr_full, on=['BldgLoc','BldgType','BldgVint','BldgHVAC','SizingID','tstat','normunit'])
elif np.NaN in list(PreTechIDs['PreTechID'].unique()):
    df_measure_set_full = pd.merge(metadata_std_full, metadata_msr_full, on=['BldgLoc','BldgType','BldgVint','BldgHVAC','SizingID','tstat','normunit'])
else:
    df_measure_baseline_full = pd.merge(metadata_pre_full, metadata_std_full, on=['BldgLoc','BldgType','BldgVint','BldgHVAC','SizingID','tstat','normunit'])
    df_measure_set_full = pd.merge(df_measure_baseline_full, metadata_msr_full, on=['BldgLoc','BldgType','BldgVint','BldgHVAC','SizingID','tstat','normunit'])
# %%
#Unique sets of each MeasureID with their TechID triplets
TechID_triplets = df_measure[['EnergyImpactID','MeasureID', 'PreTechID', 'StdTechID','MeasTechID']].drop_duplicates()
# %%
#to match TechID triplets, merge on these 3 fields, keeping only valid TechID Triplets
if np.NaN in list(StdTechIDs['StdTechID'].unique()):
    current_msr_mat_proto = pd.merge(df_measure_set_full, TechID_triplets, on=['PreTechID','MeasTechID'])
elif np.NaN in list(PreTechIDs['PreTechID'].unique()):
    current_msr_mat_proto = pd.merge(df_measure_set_full, TechID_triplets, on=['StdTechID','MeasTechID'])
else:
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

#%%
#check length of current_msr_mat
len(current_msr_mat)

# %%
##STEP 5: Clean Up Sequence
# Creating updated Sim_annual and Sim_hourly data with distinguished TechID names
sim_annual_pre_common = sim_annual_f[sim_annual_f['TechID'].isin(PreTechIDs['Common_PreTechID'].unique())]
sim_annual_std_common = sim_annual_f[sim_annual_f['TechID'].isin(StdTechIDs['Common_StdTechID'].unique())]
sim_annual_msr_common = sim_annual_f[sim_annual_f['TechID'].isin(MeasTechIDs['Common_MeasTechID'].unique())]
# %%
#Add a TechID col renaming the common TechID to the specific TechID using PreTechIDs, StdTechIDs, MeasTechIDs

#create full pre sim_annual sets for different names but the same TechID
# commom_preTechID = PreTechIDs['Common_PreTechID'].unique()[0]
if False in list(PreTechIDs['PreTechID']==PreTechIDs['Common_PreTechID']):
    sim_annual_pre = pd.DataFrame()
    for _, (common_id, new_id) in PreTechIDs[['Common_PreTechID', 'PreTechID']].iterrows():
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
sim_hourly_pre_common = sim_hourly_final[sim_hourly_final['TechID'].isin(PreTechIDs['Common_PreTechID'].unique())]
sim_hourly_std_common = sim_hourly_final[sim_hourly_final['TechID'].isin(StdTechIDs['Common_StdTechID'].unique())]
sim_hourly_msr_common = sim_hourly_final[sim_hourly_final['TechID'].isin(MeasTechIDs['Common_MeasTechID'].unique())]

# %%
#Pre hourly
if False in list(PreTechIDs['PreTechID']==PreTechIDs['Common_PreTechID']):
    sim_hourly_pre = pd.DataFrame()
    for _, (common_id, new_id) in PreTechIDs[['Common_PreTechID', 'PreTechID']].iterrows():
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
current_msr_mat.to_csv('current_msr_mat.csv', index=False)
sim_annual_final.to_csv('sfm_annual.csv', index=False)
sim_hourly_final.to_csv('sfm_hourly_wb.csv', index=False)

# %%
