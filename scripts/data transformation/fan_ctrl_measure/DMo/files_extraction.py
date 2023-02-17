#%%
#import necessary libraries
import pandas as pd
import numpy as np
import datetime as dt
import os
import re
# %%

#define path
#9/8/2022 actual SEER rated baseline output path, DMo
#path = "DMo-Fan Controller"

#2/15/2023
#go up 3 directories, back into Analysis folder
path = "../../../../Analysis/DMo_SEER Rated AC_HP"
# %%
cz_folders = [cz for cz in os.listdir(path+"/runs") if 'CZ' in cz]
# %%
#goal: extract each instance-var.csv and put together in the same workbook

writer = pd.ExcelWriter('combined_DMo_8760s.xlsx', engine='xlsxwriter')

for cz in cz_folders:
    print(f"merging {cz} data")
    subpath = path +"/runs"+ f"/{cz}/DMo&0&rDXGF&Ex&dxAC_equip/dxAC-Res-SEER-13.0/instance-var.csv"
    df = pd.read_csv(subpath, low_memory=False)
    df.to_excel(writer, sheet_name = cz)
writer.save()
writer.close()


#%%
#html table extraction


write1 = pd.ExcelWriter('end_uses_combined_DMo.xlsx', engine='xlsxwriter')
write2 = pd.ExcelWriter('fan_table_combined_DMo.xlsx', engine='xlsxwriter')
write3 = pd.ExcelWriter('airloophvac_combined_DMo.xlsx', engine='xlsxwriter')

for cz in cz_folders:
    print(f"getting {cz} html outputs...")
    subpath = path +"/runs" + f"/{cz}/DMo&0&rDXGF&Ex&dxAC_equip/dxAC-Res-SEER-13.0/instance-tbl.htm"
    raw_dfs = pd.read_html(subpath)
    #extract certain tables, raw_dfs is a giant list of tables
    end_uses = raw_dfs[3]
    fan_table = raw_dfs[112]
    airloophvac = raw_dfs[24]

    #pass to writer
    end_uses.to_excel(write1, index=False, sheet_name = cz)
    fan_table.to_excel(write2, index=False, sheet_name = cz)
    airloophvac.to_excel(write3, index=False, sheet_name = cz)


write1.save()
write2.save()
write3.save()
write1.close()
write2.close()
write3.close()
# %%
