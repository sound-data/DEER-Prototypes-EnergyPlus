#Remap TechID in CEDARS_LoadShape_Com.zip from the path token (M1-cPTAC-Base) to
#the real measure-workbook TechID (NE-dxAC_equip-... / NE-HV_Tech-...), like the
#residential example. Only the TechID column changes; UECproportion etc. untouched.
import zipfile, pandas as pd, os
os.chdir(os.path.dirname(__file__))

m = pd.read_excel('DEER_EnergyPlus_Modelkit_Measure_list_working_dir/DEER_EnergyPlus_Modelkit_Measure_list_working OFC Asm.xlsx',
                  sheet_name='Measure_list', skiprows=4)
d = m[m['Modelkit Folder Primary Name'] == 'SWHC062-03 Occupancy Fan Controller']
tmap = {}
for _, r in d[['Common_PreTechID', 'PreTechID']].dropna().drop_duplicates().iterrows():
    tmap[r['Common_PreTechID']] = r['PreTechID']
for _, r in d[['Common_MeasTechID', 'MeasTechID']].dropna().drop_duplicates().iterrows():
    tmap[r['Common_MeasTechID']] = r['MeasTechID']
print(f'{len(tmap)} TechID mappings loaded')

zin = zipfile.ZipFile('CEDARS_LoadShape_Com.zip')
zout = zipfile.ZipFile('CEDARS_LoadShape_Com_realTechID.zip', 'w', zipfile.ZIP_DEFLATED)
for name in zin.namelist():
    df = pd.read_csv(zin.open(name))
    unmapped = set(df['TechID'].unique()) - set(tmap)
    df['TechID'] = df['TechID'].map(tmap).fillna(df['TechID'])
    zout.writestr(name, df.to_csv(index=False))
    print(f'{name}: {len(df)} rows remapped' + (f'  WARN unmapped={unmapped}' if unmapped else ''))
zin.close(); zout.close()
print('done -> CEDARS_LoadShape_Com_realTechID.zip')
