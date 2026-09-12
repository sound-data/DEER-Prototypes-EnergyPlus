#Produce the sim_hourly_wb 24x365 format (actual demand kWh), split into one CSV
#per building type, Ex + Htl_Ex combined, read straight from each run's eplusmtr.csv.
import pandas as pd, numpy as np, glob, os, zipfile, datetime as dt
from collections import defaultdict

os.chdir(os.path.dirname(__file__))

BLDGTYPE_CASE_FIX = {'Epr': 'EPr', 'Ese': 'ESe', 'Eun': 'EUn'}
def norm(bt): return BLDGTYPE_CASE_FIX.get(bt, bt)

#path token (Common_*TechID) -> real TechID, from the measure workbook
m = pd.read_excel('DEER_EnergyPlus_Modelkit_Measure_list_working_dir/DEER_EnergyPlus_Modelkit_Measure_list_working OFC Asm.xlsx', sheet_name='Measure_list', skiprows=4)
d = m[m['Modelkit Folder Primary Name'] == 'SWHC062-03 Occupancy Fan Controller']
techid_map = {}
for _, r in d[['Common_PreTechID', 'PreTechID']].dropna().drop_duplicates().iterrows():
    techid_map[r['Common_PreTechID']] = r['PreTechID']
for _, r in d[['Common_MeasTechID', 'MeasTechID']].dropna().drop_duplicates().iterrows():
    techid_map[r['Common_MeasTechID']] = r['MeasTechID']

measure_dir = r'../../commercial measures/SWHC062-03 Occupancy Fan Controller'
studies = ['SWHC062-03 Occupancy Fan Controller_Ex',
           'SWHC062-03 Occupancy Fan Controller_Htl_Ex']
ELEC = 'Electricity:Facility [J](Hourly)'
HRS = [f'hr{h:02d}' for h in range(1, 25)]

#collect run dirs (CZ/Bldg/Tech) grouped by building type, across both studies
runs_by_bt = defaultdict(list)
for study in studies:
    rd = os.path.join(measure_dir, study, 'runs')
    if not os.path.isdir(rd):
        continue
    for base in glob.glob(rd + '/*/*/*'):
        if not os.path.isdir(base):
            continue
        cz, bt, tech = os.path.relpath(base, rd).replace(os.sep, '/').split('/')[:3]
        runs_by_bt[norm(bt)].append((cz, tech, base))

now = dt.datetime.now()
cols = ['TechID', 'SizingID', 'BldgType', 'BldgVint', 'BldgLoc', 'BldgHVAC',
        'tstat', 'enduse', 'daynum'] + HRS + ['lastmod']

with zipfile.ZipFile('CEDARS_hourly_wb_by_bldgtype.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    for bt in sorted(runs_by_bt):
        records = []
        for cz, tech, base in runs_by_bt[bt]:
            mtr = glob.glob(base + '/**/eplusmtr.csv', recursive=True)
            if not mtr:
                print(f'  no eplusmtr for {cz}/{bt}/{tech}')
                continue
            df = pd.read_csv(max(mtr, key=os.path.getmtime), low_memory=False)
            df.columns = df.columns.str.strip()
            v = df[ELEC].to_numpy(dtype=float)
            if len(v) > 8760:
                v = v[len(v) - 8760:]
            wide = (v / 3.6e6).reshape(365, 24)   # J -> kWh, 365 x 24
            hvac = tech.split('-')[1]
            real_techid = techid_map.get(tech, tech)
            for day in range(365):
                row = {'TechID': real_techid, 'SizingID': 'None', 'BldgType': bt,
                       'BldgVint': 'Ex', 'BldgLoc': cz, 'BldgHVAC': hvac,
                       'tstat': 0, 'enduse': 0, 'daynum': day + 1, 'lastmod': now}
                for h in range(24):
                    row[HRS[h]] = wide[day, h]
                records.append(row)
        out = pd.DataFrame.from_records(records)[cols]
        zf.writestr(f'CEDARS_hourly_wb_{bt}.csv', out.to_csv(index=False))
        print(f'{bt}: {len(runs_by_bt[bt])} runs -> {len(out)} rows')

print('done -> CEDARS_hourly_wb_by_bldgtype.zip')
