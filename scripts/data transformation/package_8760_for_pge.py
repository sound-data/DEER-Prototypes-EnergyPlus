#Repackage the normalized 8760 load shapes into one ZIP per building type,
#each containing 16 per-CZ CSV files, named per Peter's spec:
#   ZIP:  SWHC062_8760_Load_Shapes_<BldgType>.zip
#   file: SWHC062_8760_Load_Shapes_<BldgType>_<CZ>.csv
#Also builds SWHC062_8760_Load_Shapes_MFmCmn.zip from OfS (BldgType col -> MFmCmn).
#Fills TechGroup/TechType (measure-level from the workbook), which were null for
#every building type except Asm because the source lookup keyed on BldgType.
import zipfile, pandas as pd, os
os.chdir(os.path.dirname(__file__))

SRC = 'CEDARS_LoadShape_Com_realTechID.zip'
PREFIX = 'SWHC062_8760_Load_Shapes_'
OUTDIR = 'PGE_8760_zips'
os.makedirs(OUTDIR, exist_ok=True)

#measure-level TechGroup / TechType from the measure workbook
m = pd.read_excel('DEER_EnergyPlus_Modelkit_Measure_list_working_dir/DEER_EnergyPlus_Modelkit_Measure_list_working OFC Asm.xlsx',
                  sheet_name='Measure_list', skiprows=4)
d = m[m['Modelkit Folder Primary Name'] == 'SWHC062-03 Occupancy Fan Controller']
TECHGROUP = d['TechGroup_ee'].dropna().unique()[0]   # HV_Tech
TECHTYPE = d['TechType_ee'].dropna().unique()[0]      # TStat
print(f'filling TechGroup={TECHGROUP!r}, TechType={TECHTYPE!r} for all rows')

zin = zipfile.ZipFile(SRC)
name_by_bt = {n.replace('CEDARS_LoadShape_Com_', '').replace('.csv', ''): n
              for n in zin.namelist()}

def make_zip(out_bt, source_bt=None, relabel_to=None):
    df = pd.read_csv(zin.open(name_by_bt[source_bt or out_bt]))
    df['TechGroup'] = TECHGROUP
    df['TechType'] = TECHTYPE
    if relabel_to:
        df['BldgType'] = relabel_to            # column 2 -> new building type
    zippath = os.path.join(OUTDIR, f'{PREFIX}{out_bt}.zip')
    with zipfile.ZipFile(zippath, 'w', zipfile.ZIP_DEFLATED) as zf:
        for cz, sub in df.groupby('BldgLoc'):
            zf.writestr(f'{PREFIX}{out_bt}_{cz}.csv', sub.to_csv(index=False))
    print(f'{os.path.basename(zippath)}: {df["BldgLoc"].nunique()} CZ files, {len(df)} rows')

bldg_types = ['Asm', 'EPr', 'ESe', 'ECC', 'ERC', 'EUn', 'Gro', 'Htl', 'MBT',
              'MLI', 'OfS', 'RFF', 'Rt3', 'RtL', 'RtS', 'SCn']
for bt in bldg_types:
    make_zip(bt)
make_zip('MFmCmn', source_bt='OfS', relabel_to='MFmCmn')   # MFmCmn from OfS

zin.close()
print(f'\ndone -> {len(bldg_types)+1} zips in {OUTDIR}/')
