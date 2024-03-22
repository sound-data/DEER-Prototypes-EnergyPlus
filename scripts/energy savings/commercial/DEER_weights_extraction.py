#%%
import pandas as pd
import numpy as np
import os
import sys
import datetime as dt

os.chdir(os.path.dirname(__file__)) #resets to current script directory

import sqlalchemy
import psycopg2
#%%
from sqlalchemy import create_engine, text
# %%
#read from DEER database
#sqlalchemy way
engine = sqlalchemy.create_engine("postgresql://sptviewer:deereddev@cpucexante.cwuiixjcexyp.us-east-1.rds.amazonaws.com:5432/DEER")

#%%
#psycopg2 way
db_params = {
    'host': 'cpucexante.cwuiixjcexyp.us-east-1.rds.amazonaws.com',
    'database': 'DEER',
    'user': 'sptviewer',
    'password': 'deereddev',
    'port': '5432'
}
conn = psycopg2.connect(**db_params)

# %%
#Read BldgWts table as df
query = '''SELECT * FROM applic."BldgWts"'''
df = pd.read_sql_query(query, engine)
# %%
##Extracting wts_com_bldg
#filter for BldgType=Com weights
flag_weightID = df['weightID']=='Com'
flag_Sector = (df['Sector']=='Com')|(df['Sector']=='Ind')

df_bldgtype_com_wts = df[flag_weightID & flag_Sector]
# %%
#condense table
wts_com_bldg = df_bldgtype_com_wts[['BldgType', 'BldgVint','BldgLoc','weight']]
wts_com_bldg = wts_com_bldg.assign(PA='Any')
# %%
#rearrange/rename table
wts_com_bldg.rename(columns={'weight':'sum_bldg'}, inplace=True)
wts_com_bldg_final = wts_com_bldg[['PA','BldgType', 'BldgVint','BldgLoc','sum_bldg']]
wts_com_bldg_final_sorted = wts_com_bldg_final.sort_values(by=['BldgType', 'BldgVint','BldgLoc'])

#%%
#export wts_com_bldg
#os.chdir(os.path.dirname(__file__)) #resets to current script directory
wts_com_bldg_final_sorted.to_csv('wts_com_bldg.csv',index=False)

# %%
#===========================================
##Extracting wts_com_vint
flag_weightID_vint = (df['weightID']=='Old')|(df['weightID']=='Ex')|(df['weightID']=='Rec')|(df['weightID']=='New')
flag_Sector = (df['Sector']=='Com')|(df['Sector']=='Ind')
flag_Version = (df['Version']=='DEER2019')|(df['Version']=='DEER2023')

df_bldgvint_com_wts = df[flag_weightID_vint & flag_Sector & flag_Version]
# %%
# condense table
wts_com_vintage = df_bldgvint_com_wts[['Version','BldgType', 'BldgLoc','BldgVint','weight', 'weightID']]
wts_com_vintage = wts_com_vintage.assign(PA='Any')
# %%
#rearrange/rename table
wts_com_vintage.rename(columns={'Version':'ver', 
                                'weight':'wt_vint', 
                                'BldgType':'bldgtype', 
                                'BldgLoc':'bldgloc', 
                                'BldgVint':'bldgvint', 
                                'weightID':'era', 
                                'PA':'pa'}, inplace=True)
wts_com_vintage_final = wts_com_vintage[['ver','pa','bldgtype','bldgloc','bldgvint','wt_vint','era']]
wts_com_vintage_final_sorted = wts_com_vintage_final.sort_values(by=['bldgtype','bldgloc','bldgvint'])
# %%
#export wts_com_vint
#os.chdir(os.path.dirname(__file__)) #resets to current script directory
wts_com_vintage_final_sorted.to_csv('wts_com_vintage.csv', index=False)
# %%
