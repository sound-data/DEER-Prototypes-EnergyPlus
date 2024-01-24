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

engine = sqlalchemy.create_engine("postgresql://sptviewer:deereddev@cpucexante.cwuiixjcexyp.us-east-1.rds.amazonaws.com:5432/DEER")


#%%
db_params = {
    'host': 'cpucexante.cwuiixjcexyp.us-east-1.rds.amazonaws.com',
    'database': 'DEER',
    'user': 'sptviewer',
    'password': 'deereddev',
    'port': '5432'
}

conn = psycopg2.connect(**db_params)

#12/22/2023 connection error?
# %%
query = ('''
SELECT *
FROM applic.BldgWts;
''')

df = pd.read_sql_table(query, engine.connect())
# %%
