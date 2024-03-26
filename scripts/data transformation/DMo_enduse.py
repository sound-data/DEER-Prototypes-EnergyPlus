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
##STEP 1: enduse map table extract
end_use_map = pd.read_excel('DEER_EnergyPlus_Modelkit_Measure_list.xlsx', sheet_name='enduses')
# %%
#DMo only script
####Define path
os.chdir(os.path.dirname(__file__)) #resets to current script directory
print(os.path.abspath(os.curdir))
os.chdir("../..") #go up two directory
print(os.path.abspath(os.curdir))

path = 'Analysis/DMo_Furnace'

#%%

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
# %%
os.chdir(os.path.dirname(__file__)) #resets to current script directory
print(os.path.abspath(os.curdir))
annual_map = pd.read_excel('annual8760map.xlsx')
# %%
os.chdir("../..") #go up two directory
print(os.path.abspath(os.curdir))
hrly_path = path + '/runs' 
# %%
#extract data per bldgtype-bldghvac-bldgvint group
hourly_df = pd.DataFrame(index=range(0,8760))
#extract num_runs / split_meta_cols_eu
df_raw = pd.read_csv(path+'/'+'/results-summary.csv', usecols=['File Name'])
num_runs = len(df_raw['File Name'].dropna().unique()) - 1
annual_df = pd.read_csv(path+'/'+'/results-summary.csv', nrows=num_runs, skiprows=num_runs+2)
split_meta_cols_eu = annual_df['File Name'].str.split('/', expand=True)
# %%
#filter eu map via "Measure Group Name" in current dataset
eu_map_filtered = end_use_map[end_use_map['Measure Group Name'].isin(list(split_meta_cols_eu[1]))]
#extract the last 24 fields (they are the end-use field names)
eu_fields = list(eu_map_filtered.columns)[-24:]
#%%
raw_eu_list = list(eu_map_filtered[eu_fields].reset_index().transpose()[0])
eu_field_list = [i for i in raw_eu_list if type(i)==str]


#%%
#filter master table
df_measure = df_master[df_master['Measure (general name)'] == measure_name]

#%%
#test for loop for end-use loadshapes
for i in range(0,num_runs):
    print(f"merging record {i}")
    
    #loop path of each file, read corresponding file
    full_path = hrly_path + "/" + split_meta_cols_eu.iloc[i][0] + "/" + split_meta_cols_eu.iloc[i][1] + "/" + split_meta_cols_eu.iloc[i][2] + "/instance-var.csv"
    df = pd.read_csv(full_path, low_memory=False)

    extracted_df_eu = df[eu_field_list].copy()
    extracted_df_eu['end_use_sum'] = extracted_df_eu.sum(axis=1)

    extracted_df = pd.DataFrame(extracted_df_eu.iloc[:,-1])

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
    hrly_wide['BldgType'] = col_names[1]
    hrly_wide['TechID'] = col_names[2]
    hrly_wide['file'] = col_names[3]
    
    #append to master df
    #converted_df = converted_df.append(hrly_wide) #deprecated method
    converted_df = pd.concat([converted_df, hrly_wide])
    print(f"col {i} transformed.")
# %%
#rearrange columns
sim_hourly_eu_proto = converted_df[['TechID','file','BldgLoc','BldgType','ID','daynum',1,          2,          3,          4,          5,
                6,          7,          8,          9,         10,         11,
            12,         13,         14,         15,         16,         17,
            18,         19,         20,         21,         22,         23,
            24]].copy()
#hourly data conversion
#convert unit (J) to (kWh) for hourly

sim_hourly_eu_proto['hr01'] = sim_hourly_eu_proto[1]/3600000
sim_hourly_eu_proto['hr02'] = sim_hourly_eu_proto[2]/3600000
sim_hourly_eu_proto['hr03'] = sim_hourly_eu_proto[3]/3600000
sim_hourly_eu_proto['hr04'] = sim_hourly_eu_proto[4]/3600000
sim_hourly_eu_proto['hr05'] = sim_hourly_eu_proto[5]/3600000
sim_hourly_eu_proto['hr06'] = sim_hourly_eu_proto[6]/3600000
sim_hourly_eu_proto['hr07'] = sim_hourly_eu_proto[7]/3600000
sim_hourly_eu_proto['hr08'] = sim_hourly_eu_proto[8]/3600000
sim_hourly_eu_proto['hr09'] = sim_hourly_eu_proto[9]/3600000
sim_hourly_eu_proto['hr10'] = sim_hourly_eu_proto[10]/3600000
sim_hourly_eu_proto['hr11'] = sim_hourly_eu_proto[11]/3600000
sim_hourly_eu_proto['hr12'] = sim_hourly_eu_proto[12]/3600000
sim_hourly_eu_proto['hr13'] = sim_hourly_eu_proto[13]/3600000
sim_hourly_eu_proto['hr14'] = sim_hourly_eu_proto[14]/3600000
sim_hourly_eu_proto['hr15'] = sim_hourly_eu_proto[15]/3600000
sim_hourly_eu_proto['hr16'] = sim_hourly_eu_proto[16]/3600000
sim_hourly_eu_proto['hr17'] = sim_hourly_eu_proto[17]/3600000
sim_hourly_eu_proto['hr18'] = sim_hourly_eu_proto[18]/3600000
sim_hourly_eu_proto['hr19'] = sim_hourly_eu_proto[19]/3600000
sim_hourly_eu_proto['hr20'] = sim_hourly_eu_proto[20]/3600000
sim_hourly_eu_proto['hr21'] = sim_hourly_eu_proto[21]/3600000
sim_hourly_eu_proto['hr22'] = sim_hourly_eu_proto[22]/3600000
sim_hourly_eu_proto['hr23'] = sim_hourly_eu_proto[23]/3600000
sim_hourly_eu_proto['hr24'] = sim_hourly_eu_proto[24]/3600000

#rearrange columns
sim_hourly_eu_v1 = sim_hourly_eu_proto[['TechID','file','BldgLoc','BldgType','ID','daynum','hr01','hr02','hr03','hr04','hr05','hr06',
        'hr07',     'hr08',     'hr09',     'hr10',     'hr11',     'hr12',
        'hr13',     'hr14',     'hr15',     'hr16',     'hr17',     'hr18',
        'hr19',     'hr20',     'hr21',     'hr22',     'hr23',     'hr24']].copy()
# %%
##Hourly Data final field fixes
def vintage_str(name):
    if 'Ex' in name:
        return 'Ex'
    elif 'New' in name:
        return 'New'

def hvac_str(name):
    if 'rDXGF' in name:
        return 'rDXGF'
    elif 'rDXHP' in name:
        return 'rDXHP'

def bldgtype_str(name):
    if 'DMo' in name:
        return 'DMo'
    elif 'MFm' in name:
        return 'MFm'
    elif 'SFm' in name:
        return 'SFm'

#update field names based on what it contains
sim_hourly_eu_v1['BldgVint'] = sim_hourly_eu_v1['BldgType'].apply(vintage_str)
sim_hourly_eu_v1['BldgHVAC'] = sim_hourly_eu_v1['BldgType'].apply(hvac_str)
sim_hourly_eu_v1['BldgType'] = sim_hourly_eu_v1['BldgType'].apply(bldgtype_str)
sim_hourly_eu_v1['SizingID'] = 'None'
sim_hourly_eu_v1['tstat'] = 0

#enduse index note, 6 is HVAC enduses, may need to generalize
sim_hourly_eu_v1['enduse'] = 6 
sim_hourly_eu_v1['lastmod']=dt.datetime.now()

#rearrange columns
sim_hourly_f = sim_hourly_eu_v1[['TechID', 'SizingID', 'BldgType', 'BldgVint', 'BldgLoc','BldgHVAC','tstat', 'enduse', 'daynum', 
                                 'hr01', 'hr02', 'hr03', 'hr04', 'hr05', 'hr06', 'hr07', 'hr08', 'hr09', 'hr10', 'hr11',
                                'hr12', 'hr13', 'hr14', 'hr15', 'hr16', 'hr17', 'hr18', 'hr19', 'hr20',
                                'hr21', 'hr22', 'hr23', 'hr24', 'lastmod']]
# %%
#Final Clean up

#TechID identification from Master table
#if looping over all HVAC types, ignore BldgHVAC filter
PreTechIDs = df_measure[['PreTechID','Common_PreTechID']].drop_duplicates()
StdTechIDs = df_measure[['StdTechID','Common_StdTechID']].drop_duplicates()
MeasTechIDs = df_measure[['MeasTechID','Common_MeasTechID']].drop_duplicates()
# %%

#Hourly Clean up
###hourly data, separate into pre std msr, change into specific TechID
sim_hourly_pre_common = sim_hourly_f[sim_hourly_f['TechID'].isin(PreTechIDs['Common_PreTechID'].unique())]
sim_hourly_std_common = sim_hourly_f[sim_hourly_f['TechID'].isin(StdTechIDs['Common_StdTechID'].unique())]
sim_hourly_msr_common = sim_hourly_f[sim_hourly_f['TechID'].isin(MeasTechIDs['Common_MeasTechID'].unique())]

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
os.chdir(os.path.dirname(__file__)) #resets to current script directory
print(os.path.abspath(os.curdir))

sim_hourly_final.to_csv('sim_hourly_eu.csv', index=False)
# %%
