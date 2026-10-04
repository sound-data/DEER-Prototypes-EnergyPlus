#QA helper: split the CEDARS load shapes into one CSV per building type PER CZ
#(small enough to open in Excel), from the real-TechID zip. The full
#CEDARS_LoadShape_Com_realTechID.zip is preserved as the deliverable.
import zipfile, pandas as pd, os
os.chdir(os.path.dirname(__file__))

SRC = 'CEDARS_LoadShape_Com_realTechID.zip'
OUT = 'CEDARS_LoadShape_byCZ_QA.zip'

zin = zipfile.ZipFile(SRC)
zout = zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED)
for name in zin.namelist():                       # one file per building type
    df = pd.read_csv(zin.open(name))
    bt = df['BldgType'].iloc[0]
    for cz, sub in df.groupby('BldgLoc'):         # split by climate zone
        zout.writestr(f'CEDARS_LoadShape_{bt}_{cz}.csv', sub.to_csv(index=False))
    print(f'{bt}: {df["BldgLoc"].nunique()} CZ files ({len(df)} rows total)')
zin.close(); zout.close()
print(f'done -> {OUT}')
