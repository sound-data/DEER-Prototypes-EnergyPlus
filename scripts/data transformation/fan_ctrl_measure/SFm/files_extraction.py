#%%
#import necessary libraries
import pandas as pd
import numpy as np
import datetime as dt
import os
import re
# %%

#define path
#8/24/2022 this should be path of the AC baseline run, containing fan PLR hourly outputs
#path = "//hou7002/Projects/CPUC_DEER/EnergyPlus Transition/Task 2/Modelkit Results for QC/Fan Controller Measure/SFm-DXGF"

#9/1/2022 actual SEER rated baseline output path, SFm
#path = "High SEER baseline"

#go up 3 directories, back into Analysis folder
path = "../../../../Analysis"

# %%
#grab path
file_list = os.listdir(path)
#list comprehension to extract only folder names
vint_folder_list = [i for i in file_list if 'SFm_SEER Rated AC_HP_1' in i]

#split to 2 sets of folder, one for CZ1-9, the other CZ10-16. Each ocntains 1 and 2 story.


# %%
#goal: extract each instance-var.csv and put together in the same workbook

#1-story
writer = pd.ExcelWriter('combined_1_story_8760s.xlsx', engine='xlsxwriter')
for vint_folder in vint_folder_list:
    full_path = path + "/" + vint_folder + "/" + "runs"
    cz_folders = [cz for cz in os.listdir(full_path) if 'CZ' in cz]
    for cz in cz_folders:
        print(f"merging {cz} data @ {vint_folder}")
        subpath = full_path + f"/{cz}/SFm&1&rDXGF&Ex&dxAC_equip/dxAC-Res-SEER-13.0/instance-var.csv"
        df = pd.read_csv(subpath, low_memory=False)
        df.to_excel(writer, sheet_name = cz)
writer.save()
writer.close()
#%%
#2-story
writer = pd.ExcelWriter('combined_2_story_8760s.xlsx', engine='xlsxwriter')
for vint_folder in vint_folder_list:
    full_path = path + "/" + vint_folder + "/" + "runs"
    cz_folders = [cz for cz in os.listdir(full_path) if 'CZ' in cz]
    for cz in cz_folders:
        print(f"merging {cz} data @ {vint_folder}")
        subpath = full_path + f"/{cz}/SFm&2&rDXGF&Ex&dxAC_equip/dxAC-Res-SEER-13.0/instance-var.csv"
        df = pd.read_csv(subpath, low_memory=False)
        df.to_excel(writer, sheet_name = cz)
writer.save()
writer.close()

#%%
#html table extraction

#1-story
write1 = pd.ExcelWriter('end_uses_combined_1s.xlsx', engine='xlsxwriter')
write2 = pd.ExcelWriter('fan_table_combined_1s.xlsx', engine='xlsxwriter')
write3 = pd.ExcelWriter('fan_split1_combined_1s.xlsx', engine='xlsxwriter')
write4 = pd.ExcelWriter('fan_split2_combined_1s.xlsx', engine='xlsxwriter')
write5 = pd.ExcelWriter('airloophvac_1s.xlsx', engine='xlsxwriter')
for vint_folder in vint_folder_list:
    full_path = path + "/" + vint_folder + "/" + "runs"
    cz_folders = [cz for cz in os.listdir(full_path) if 'CZ' in cz]
    for cz in cz_folders:
        print(f"getting {cz} html outputs...")
        subpath = full_path + f"/{cz}/SFm&1&rDXGF&Ex&dxAC_equip/dxAC-Res-SEER-13.0/instance-tbl.htm"
        raw_dfs = pd.read_html(subpath)
        #extract certain tables, raw_dfs is a giant list of tables
        end_uses = raw_dfs[3]
        fan_table = raw_dfs[125]
        fan_split_1 = raw_dfs[193]
        fan_split_2 = raw_dfs[194]
        airloophvac = raw_dfs[24]
        #pass to writer
        end_uses.to_excel(write1, index=False, sheet_name = cz)
        fan_table.to_excel(write2, index=False, sheet_name = cz)
        fan_split_1.to_excel(write3, index=False, sheet_name = cz)
        fan_split_2.to_excel(write4, index=False, sheet_name = cz)
        airloophvac.to_excel(write5, index=False, sheet_name = cz)

write1.save()
write2.save()
write3.save()
write4.save()
write5.save()
write1.close()
write2.close()
write3.close()
write4.close()
write5.close()

#%%
#html table extraction

#2-story
write1 = pd.ExcelWriter('end_uses_combined_2s.xlsx', engine='xlsxwriter')
write2 = pd.ExcelWriter('fan_table_combined_2s.xlsx', engine='xlsxwriter')
write3 = pd.ExcelWriter('fan_split1_combined_2s.xlsx', engine='xlsxwriter')
write4 = pd.ExcelWriter('fan_split2_combined_2s.xlsx', engine='xlsxwriter')
write5 = pd.ExcelWriter('airloophvac_2s.xlsx', engine='xlsxwriter')
for vint_folder in vint_folder_list:
    full_path = path + "/" + vint_folder + "/" + "runs"
    cz_folders = [cz for cz in os.listdir(full_path) if 'CZ' in cz]
    for cz in cz_folders:
        print(f"getting {cz} html outputs...")
        subpath = full_path + f"/{cz}/SFm&2&rDXGF&Ex&dxAC_equip/dxAC-Res-SEER-13.0/instance-tbl.htm"
        raw_dfs = pd.read_html(subpath)
        #extract certain tables, raw_dfs is a giant list of tables
        end_uses = raw_dfs[3]
        fan_table = raw_dfs[125]
        fan_split_1 = raw_dfs[193]
        fan_split_2 = raw_dfs[194]
        airloophvac = raw_dfs[24]
        #pass to writer
        end_uses.to_excel(write1, index=False, sheet_name = cz)
        fan_table.to_excel(write2, index=False, sheet_name = cz)
        fan_split_1.to_excel(write3, index=False, sheet_name = cz)
        fan_split_2.to_excel(write4, index=False, sheet_name = cz)
        airloophvac.to_excel(write5, index=False, sheet_name = cz)

write1.save()
write2.save()
write3.save()
write4.save()
write5.save()
write1.close()
write2.close()
write3.close()
write4.close()
write5.close()

# %%
