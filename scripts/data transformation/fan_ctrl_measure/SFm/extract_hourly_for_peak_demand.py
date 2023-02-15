#%%import necessary libraries
import pandas as pd
import numpy as np
import datetime as dt
import os
# %%
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

def hvac_field(x):
    if 'HP' in x:
        return 'rDXHP'
    elif 'rDXGF' in x:
        return 'rDXGF'

def vint_filter(cz):
    if cz in ['CZ01','CZ02','CZ03','CZ04','CZ05','CZ06','CZ07','CZ08','CZ09']:
        return '1975'
    else:
        return '1985'
# %%
#9/1/2022 actual SEER rated baseline output path, SFm
#path = "High SEER baseline"

#2/14/2023 update for github repo
#go up 3 directories, back into Analysis folder
path = "../../../../Analysis"

#grab path
file_list = os.listdir(path)
#list comprehension to extract only folder names
vint_folder_list = [i for i in file_list if 'SFm_SEER Rated AC_HP_1' in i]

#split to 2 sets of folder, one for CZ1-9, the other CZ10-16. Each ocntains 1 and 2 story.

# # %%
# file_list = os.listdir(path)
# #list comprehension to extract only folder names
# vint_folder_list = [i for i in file_list if 'SFm' in i]
# %%
# %%
## Hourly data setup/transform
#Read 8760 map
annual_map = pd.read_excel('../annual8760map.xlsx')

# %%
#vintage = 1975, all runs, hourly data
full_path = path + "/" + vint_folder_list[0] 

df_raw = pd.read_csv(full_path +'/results-summary.csv', usecols=['File Name'])
num_runs = len(df_raw['File Name'].dropna().unique()) - 1

#%%
annual_df = pd.read_csv(full_path + "/results-summary.csv", nrows=num_runs, skiprows=num_runs+2)
split_meta_cols_eu = annual_df['File Name'].str.split('/', expand=True)

hourly_df_pervint = pd.DataFrame(index=range(0,8760))

cz_folders = [cz for cz in os.listdir(full_path+"/runs") if 'CZ' in cz]

for cz in cz_folders:
        print(f"parsing {cz} data...")
        sub_meta_cols = split_meta_cols_eu[split_meta_cols_eu[0]==cz].reset_index(drop=True)
        hourly_df_percz = pd.DataFrame(index=range(0,8760))
        for i in range(0,len(sub_meta_cols)):
            full_path_to_hrly = full_path +"/runs" + "/" + f"{cz}" + "/" + sub_meta_cols[1][i] + "/" + sub_meta_cols[2][i] + "/instance-var.csv"
            df = pd.read_csv(full_path_to_hrly, low_memory=False)
            
            #extract the last column (the total elec hrly profile)
            extracted_df = pd.DataFrame(df.iloc[:,-1])

            #create the column name based on the permutations
            col_name = sub_meta_cols[0][i] + "/" + sub_meta_cols[1][i] + "/" + sub_meta_cols[2][i] + "/instance-var.csv"

            #change column name
            extracted_df = extracted_df.set_axis([col_name],axis=1)
            if len(extracted_df)!=8760:
                #if multiple design day data (>2), length will not be 8808, may be 8976. if not 8976, update code
                #8/23/2022 update, need to make the final length 8808. Snip data based on difference to 8808
                record_count_diff = len(extracted_df) - 8760
                print(f'extra records: {str(len(extracted_df))}, snipping away {record_count_diff} records and changing to 8760')
                extracted_df = extracted_df.iloc[record_count_diff:].reset_index(drop=True)
            
            #left-merge onto cz df
            hourly_df_percz = hourly_df_percz.merge(extracted_df, left_index=True, right_index=True)
        
        hourly_df_pervint = hourly_df_pervint.merge(hourly_df_percz, left_index=True, right_index=True)
# %%
fyr_hrly = hourly_df_pervint

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

#rearrange columns
sim_hourly_wb_proto_1975 = converted_df[['TechID','file','BldgLoc','BldgType','ID','daynum',1,          2,          3,          4,          5,
                6,          7,          8,          9,         10,         11,
               12,         13,         14,         15,         16,         17,
               18,         19,         20,         21,         22,         23,
               24]]
# %%
#split result into 1975_1s, 1975_2s
#note - use dxgf only for fan control 
story_flags = list(sim_hourly_wb_proto_1975['BldgType'].unique())
sim_hourly_wb_1975_1s = sim_hourly_wb_proto_1975[sim_hourly_wb_proto_1975['BldgType'] == story_flags[0]]
sim_hourly_wb_1975_2s = sim_hourly_wb_proto_1975[sim_hourly_wb_proto_1975['BldgType'] == story_flags[1]]


# %%
#vintage = 1985, all runs, hourly data
full_path = path + "/" + vint_folder_list[1] 

df_raw = pd.read_csv(full_path +'/results-summary.csv', usecols=['File Name'])
num_runs = len(df_raw['File Name'].dropna().unique()) - 1
#%%
annual_df_2 = pd.read_csv(full_path + "/results-summary.csv", nrows=num_runs, skiprows=num_runs+2)
split_meta_cols_eu2 = annual_df_2['File Name'].str.split('/', expand=True)

hourly_df_pervint_2 = pd.DataFrame(index=range(0,8760))

cz_folders = [cz for cz in os.listdir(full_path+"/runs") if 'CZ' in cz]

for cz in cz_folders:
    print(f"parsing {cz} data...")
    sub_meta_cols = split_meta_cols_eu2[split_meta_cols_eu2[0]==cz].reset_index(drop=True)
    hourly_df_percz = pd.DataFrame(index=range(0,8760))
    for i in range(0,len(sub_meta_cols)):
        full_path_to_hrly = full_path +"/runs" + "/" + f"{cz}" + "/" + sub_meta_cols[1][i] + "/" + sub_meta_cols[2][i] + "/instance-var.csv"
        df = pd.read_csv(full_path_to_hrly, low_memory=False)
        
        #extract the last column (the total elec hrly profile)
        extracted_df = pd.DataFrame(df.iloc[:,-1])

        #create the column name based on the permutations
        col_name = sub_meta_cols[0][i] + "/" + sub_meta_cols[1][i] + "/" + sub_meta_cols[2][i] + "/instance-var.csv"

        #change column name
        extracted_df = extracted_df.set_axis([col_name],axis=1)
        if len(extracted_df)!=8760:
            #8/31/2022 update, need to make the final length 8760. Snip data based on difference to 8760
            record_count_diff = len(extracted_df) - 8760
            print(f'extra records: {str(len(extracted_df))}, snipping away {record_count_diff} records and changing to 8760')
            extracted_df = extracted_df.iloc[record_count_diff:].reset_index(drop=True)
        
        #left-merge onto cz df
        hourly_df_percz = hourly_df_percz.merge(extracted_df, left_index=True, right_index=True)
    
    hourly_df_pervint_2 = hourly_df_pervint_2.merge(hourly_df_percz, left_index=True, right_index=True)

# %%

fyr_hrly_2 = hourly_df_pervint_2

#rearrange 1-column 8760 format to 365x24 wide format for all runs in hourly_df
converted_df_2 = pd.DataFrame()

for i in range(0,len(fyr_hrly_2.columns)):
    
    #isolate single column
    hrly_df = pd.DataFrame(fyr_hrly_2.iloc[:,i])
    
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
    converted_df_2 = pd.concat([converted_df_2, hrly_wide])
    print(f"col {i} transformed.")

#rearrange columns
sim_hourly_wb_proto_1985 = converted_df_2[['TechID','file','BldgLoc','BldgType','ID','daynum',1,          2,          3,          4,          5,
                6,          7,          8,          9,         10,         11,
               12,         13,         14,         15,         16,         17,
               18,         19,         20,         21,         22,         23,
               24]]
# %%
#split result into 1985_1s, 1985_2s
story_flags2 = list(sim_hourly_wb_proto_1985['BldgType'].unique())
sim_hourly_wb_1985_1s = sim_hourly_wb_proto_1985[sim_hourly_wb_proto_1985['BldgType'] == story_flags2[0]]
sim_hourly_wb_1985_2s = sim_hourly_wb_proto_1985[sim_hourly_wb_proto_1985['BldgType'] == story_flags2[1]]


# %%
#reassemble into 1-story and 2-story hourly profiles

sim_hourly_wb_proto1s = pd.concat([sim_hourly_wb_1975_1s, sim_hourly_wb_1985_1s])
sim_hourly_wb_proto2s = pd.concat([sim_hourly_wb_1975_2s, sim_hourly_wb_1985_2s])
# %%
### hourly data unit conversion (both 1s, 2s)
#hourly data conversion
#convert unit (J) to (kWh) for hourly
sim_hourly_wb_proto1s['hr01'] = sim_hourly_wb_proto1s[1]/3600000
sim_hourly_wb_proto1s['hr02'] = sim_hourly_wb_proto1s[2]/3600000
sim_hourly_wb_proto1s['hr03'] = sim_hourly_wb_proto1s[3]/3600000
sim_hourly_wb_proto1s['hr04'] = sim_hourly_wb_proto1s[4]/3600000
sim_hourly_wb_proto1s['hr05'] = sim_hourly_wb_proto1s[5]/3600000
sim_hourly_wb_proto1s['hr06'] = sim_hourly_wb_proto1s[6]/3600000
sim_hourly_wb_proto1s['hr07'] = sim_hourly_wb_proto1s[7]/3600000
sim_hourly_wb_proto1s['hr08'] = sim_hourly_wb_proto1s[8]/3600000
sim_hourly_wb_proto1s['hr09'] = sim_hourly_wb_proto1s[9]/3600000
sim_hourly_wb_proto1s['hr10'] = sim_hourly_wb_proto1s[10]/3600000
sim_hourly_wb_proto1s['hr11'] = sim_hourly_wb_proto1s[11]/3600000
sim_hourly_wb_proto1s['hr12'] = sim_hourly_wb_proto1s[12]/3600000
sim_hourly_wb_proto1s['hr13'] = sim_hourly_wb_proto1s[13]/3600000
sim_hourly_wb_proto1s['hr14'] = sim_hourly_wb_proto1s[14]/3600000
sim_hourly_wb_proto1s['hr15'] = sim_hourly_wb_proto1s[15]/3600000
sim_hourly_wb_proto1s['hr16'] = sim_hourly_wb_proto1s[16]/3600000
sim_hourly_wb_proto1s['hr17'] = sim_hourly_wb_proto1s[17]/3600000
sim_hourly_wb_proto1s['hr18'] = sim_hourly_wb_proto1s[18]/3600000
sim_hourly_wb_proto1s['hr19'] = sim_hourly_wb_proto1s[19]/3600000
sim_hourly_wb_proto1s['hr20'] = sim_hourly_wb_proto1s[20]/3600000
sim_hourly_wb_proto1s['hr21'] = sim_hourly_wb_proto1s[21]/3600000
sim_hourly_wb_proto1s['hr22'] = sim_hourly_wb_proto1s[22]/3600000
sim_hourly_wb_proto1s['hr23'] = sim_hourly_wb_proto1s[23]/3600000
sim_hourly_wb_proto1s['hr24'] = sim_hourly_wb_proto1s[24]/3600000


#hourly data conversion
#convert unit (J) to (kWh) for hourly
sim_hourly_wb_proto2s['hr01'] = sim_hourly_wb_proto2s[1]/3600000
sim_hourly_wb_proto2s['hr02'] = sim_hourly_wb_proto2s[2]/3600000
sim_hourly_wb_proto2s['hr03'] = sim_hourly_wb_proto2s[3]/3600000
sim_hourly_wb_proto2s['hr04'] = sim_hourly_wb_proto2s[4]/3600000
sim_hourly_wb_proto2s['hr05'] = sim_hourly_wb_proto2s[5]/3600000
sim_hourly_wb_proto2s['hr06'] = sim_hourly_wb_proto2s[6]/3600000
sim_hourly_wb_proto2s['hr07'] = sim_hourly_wb_proto2s[7]/3600000
sim_hourly_wb_proto2s['hr08'] = sim_hourly_wb_proto2s[8]/3600000
sim_hourly_wb_proto2s['hr09'] = sim_hourly_wb_proto2s[9]/3600000
sim_hourly_wb_proto2s['hr10'] = sim_hourly_wb_proto2s[10]/3600000
sim_hourly_wb_proto2s['hr11'] = sim_hourly_wb_proto2s[11]/3600000
sim_hourly_wb_proto2s['hr12'] = sim_hourly_wb_proto2s[12]/3600000
sim_hourly_wb_proto2s['hr13'] = sim_hourly_wb_proto2s[13]/3600000
sim_hourly_wb_proto2s['hr14'] = sim_hourly_wb_proto2s[14]/3600000
sim_hourly_wb_proto2s['hr15'] = sim_hourly_wb_proto2s[15]/3600000
sim_hourly_wb_proto2s['hr16'] = sim_hourly_wb_proto2s[16]/3600000
sim_hourly_wb_proto2s['hr17'] = sim_hourly_wb_proto2s[17]/3600000
sim_hourly_wb_proto2s['hr18'] = sim_hourly_wb_proto2s[18]/3600000
sim_hourly_wb_proto2s['hr19'] = sim_hourly_wb_proto2s[19]/3600000
sim_hourly_wb_proto2s['hr20'] = sim_hourly_wb_proto2s[20]/3600000
sim_hourly_wb_proto2s['hr21'] = sim_hourly_wb_proto2s[21]/3600000
sim_hourly_wb_proto2s['hr22'] = sim_hourly_wb_proto2s[22]/3600000
sim_hourly_wb_proto2s['hr23'] = sim_hourly_wb_proto2s[23]/3600000
sim_hourly_wb_proto2s['hr24'] = sim_hourly_wb_proto2s[24]/3600000


#rearrange columns
sim_hourly_wb_1s_v1 = sim_hourly_wb_proto1s[['TechID','file','BldgLoc','BldgType','ID','daynum','hr01','hr02','hr03','hr04','hr05','hr06',
           'hr07',     'hr08',     'hr09',     'hr10',     'hr11',     'hr12',
           'hr13',     'hr14',     'hr15',     'hr16',     'hr17',     'hr18',
           'hr19',     'hr20',     'hr21',     'hr22',     'hr23',     'hr24']].copy()

#rearrange columns
sim_hourly_wb_2s_v1 = sim_hourly_wb_proto2s[['TechID','file','BldgLoc','BldgType','ID','daynum','hr01','hr02','hr03','hr04','hr05','hr06',
           'hr07',     'hr08',     'hr09',     'hr10',     'hr11',     'hr12',
           'hr13',     'hr14',     'hr15',     'hr16',     'hr17',     'hr18',
           'hr19',     'hr20',     'hr21',     'hr22',     'hr23',     'hr24']].copy()
# %%
#hourly data
#1story
#rename some fields to fit MC3 output
#add some placeholder fields to fit MC3 output
sim_hourly_wb_1s_v1['SizingID'] = 'None'
sim_hourly_wb_1s_v1['BldgType'] = 'SFm'
sim_hourly_wb_1s_v1['BldgHVAC'] = 'rDXGF'
sim_hourly_wb_1s_v1['tstat'] = 0
sim_hourly_wb_1s_v1['enduse'] = 0

#add BldgVint col based on CZ (per the new update on building vintage rules)
sim_hourly_wb_1s_v1['BldgVint'] = sim_hourly_wb_1s_v1['BldgLoc'].apply(vint_filter)

#2story
#rename some fields to fit MC3 output
#add some placeholder fields to fit MC3 output
sim_hourly_wb_2s_v1['SizingID'] = 'None'
sim_hourly_wb_2s_v1['BldgType'] = 'SFm'
sim_hourly_wb_2s_v1['BldgHVAC'] = 'rDXGF'
sim_hourly_wb_2s_v1['tstat'] = 0
sim_hourly_wb_2s_v1['enduse'] = 0

#add BldgVint col based on CZ (per the new update on building vintage rules)
sim_hourly_wb_2s_v1['BldgVint'] = sim_hourly_wb_2s_v1['BldgLoc'].apply(vint_filter)

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
# %%
#export formatted hourly output
sim_hourly_final.to_csv('sfm_hourly_wb.csv', index=False)
# %%
