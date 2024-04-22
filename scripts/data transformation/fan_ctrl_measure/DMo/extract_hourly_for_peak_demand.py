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

# %%
#9/1/2022 actual SEER rated baseline output path, DMo

path = "../../../../Analysis/DMo_SEER Rated AC_HP"


# %%
## Hourly data setup/transform
#Read 8760 map
annual_map = pd.read_excel('../annual8760map.xlsx')
# %%
df_raw = pd.read_csv(path +'/results-summary.csv', usecols=['File Name'])
num_runs = len(df_raw['File Name'].dropna().unique()) - 1

#%%
annual_df = pd.read_csv(path + "/results-summary.csv", nrows=num_runs, skiprows=num_runs+2)
split_meta_cols_eu = annual_df['File Name'].str.split('/', expand=True)

#%%
hrly_path = path + "/runs"

hourly_df = pd.DataFrame(index=range(0,8808))
for i in range(0,num_runs):
    print(f"merging record {i}")
    
    #loop path of each file, read corresponding file
    full_path = hrly_path + "/" + split_meta_cols_eu.iloc[i][0] + "/" + split_meta_cols_eu.iloc[i][1] + "/" + split_meta_cols_eu.iloc[i][2] + "/instance-var.csv"
    df = pd.read_csv(full_path, low_memory=False)
    
    #extract the last column (the total elec hrly profile)
    extracted_df = pd.DataFrame(df.iloc[:,-1])
    
    #create the column name based on the permutations
    col_name = split_meta_cols_eu.iloc[i][0] + "/" + split_meta_cols_eu.iloc[i][1] + "/" + split_meta_cols_eu.iloc[i][2] + "/instance-var.csv"
    
    #change column name
    extracted_df = extracted_df.set_axis([col_name],axis=1)
    if len(extracted_df)!=8760:
        record_count_diff = len(extracted_df) - 8760
        print(f'extra records: {str(len(extracted_df))}, snipping away {record_count_diff} records and changing to 8760')
        extracted_df = extracted_df.iloc[record_count_diff:].reset_index(drop=True)
    
    #left-merge onto big df
    
    hourly_df = hourly_df.merge(extracted_df, left_index=True, right_index=True)


#%%
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
sim_hourly_wb_proto = converted_df[['TechID','file','BldgLoc','BldgType','ID','daynum',1,          2,          3,          4,          5,
                6,          7,          8,          9,         10,         11,
               12,         13,         14,         15,         16,         17,
               18,         19,         20,         21,         22,         23,
               24]]

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
##Hourly Data
#rename some fields to fit MC3 output
#add some placeholder fields to fit MC3 output
sim_hourly_wb_v1['SizingID'] = 'None'
sim_hourly_wb_v1['BldgType'] = 'DMo'
sim_hourly_wb_v1['BldgHVAC'] = 'rDXGF'

sim_hourly_wb_v1['tstat'] = 0
sim_hourly_wb_v1['enduse'] = 0

#add BldgVint col based on CZ (per the new update on building vintage rules)
sim_hourly_wb_v1['BldgVint'] = 'Ex'

#finalize hourly 
sim_hourly_final = sim_hourly_wb_v1
sim_hourly_final['lastmod']=dt.datetime.now()

#rearrange columns
sim_hourly_f = sim_hourly_final[['TechID', 'SizingID', 'BldgType', 'BldgVint', 'BldgLoc','BldgHVAC','tstat', 'enduse', 'daynum', 
                                 'hr01', 'hr02', 'hr03', 'hr04', 'hr05', 'hr06', 'hr07', 'hr08', 'hr09', 'hr10', 'hr11',
                                'hr12', 'hr13', 'hr14', 'hr15', 'hr16', 'hr17', 'hr18', 'hr19', 'hr20',
                                'hr21', 'hr22', 'hr23', 'hr24', 'lastmod']]
# %%
sim_hourly_filtered = sim_hourly_f[sim_hourly_f['TechID'].isin(['dxAC-Res-SEER-13.0'])]
# %%
sim_hourly_filtered.to_csv('sim_hourly_wb.csv', index=False)
# %%
