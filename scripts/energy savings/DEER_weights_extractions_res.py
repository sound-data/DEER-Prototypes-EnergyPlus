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

#====================================
# %%
##Extracting wts_res_bldg
#filter for BldgType=Res weights
flag_weightID = df['weightID']=='Res'
flag_Sector = df['Sector']=='Res'
flag_Version = df['Version']=='DEER2024'

df_bldgtype_res_wts = df[flag_weightID & flag_Sector & flag_Version]
# %%
#condense table
wts_res_bldg = df_bldgtype_res_wts[['BldgType', 'BldgVint','BldgLoc','weight']].copy()
wts_res_bldg.rename(columns={'weight':'sum_bldg', 
                             'BldgVint':'era', 
                             'BldgType':'bldgtype', 
                             'BldgLoc':'bldgloc'},
                             inplace=True)
#%%
#export wts_res_bldg
os.chdir(os.path.dirname(__file__)) #resets to current script directory
wts_res_bldg.to_csv('wts_res_bldg.csv', index=False)

#%%
##Extracting wts_res_hvac