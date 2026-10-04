#Duplicate the OfS (small office) Com.py outputs as MFmCmn (multi-family common),
#per the SWHC062 ReadMe: MFmCmn load shapes and UEC results are copies of OfS with
#the BldgType relabeled. Handles any casing of the source token ('OfS'/'Ofs').
#Also assembles the combined CEDARS_LoadShape_Com.zip (all building types + MFmCmn)
#at the data-transformation root for the downstream fix_cedars_techid /
#package_8760_for_pge chain.
import os, io, zipfile, glob
import pandas as pd

os.chdir(os.path.dirname(os.path.abspath(__file__)))

OUT = "outputs_by_bldgtype"
SRC = os.path.join(OUT, "OfS")
DST = os.path.join(OUT, "MFmCmn")
os.makedirs(DST, exist_ok=True)


def relabel(df):
    n = 0
    if "BldgType" in df.columns:
        mask = df["BldgType"].astype(str).str.lower() == "ofs"
        df.loc[mask, "BldgType"] = "MFmCmn"
        n = int(mask.sum())
    return df, n


CSVS = ["current_msr_mat.csv", "sim_annual.csv", "sim_hourly_wb.csv",
        "CEDARS_ls_annual_loads_Com.csv"]
for name in CSVS:
    src = os.path.join(SRC, name)
    if not os.path.exists(src):
        print(f"skip {name} (not found in {SRC})")
        continue
    df = pd.read_csv(src, low_memory=False)
    df, n = relabel(df)
    df.to_csv(os.path.join(DST, name), index=False)
    print(f"{name}: {n} BldgType values relabeled OfS -> MFmCmn")

#CEDARS zip: rename the inner per-type CSV and relabel its BldgType column
src_zip = os.path.join(SRC, "CEDARS_LoadShape_Com.zip")
dst_zip = os.path.join(DST, "CEDARS_LoadShape_Com.zip")
with zipfile.ZipFile(src_zip) as zin, \
     zipfile.ZipFile(dst_zip, "w", zipfile.ZIP_DEFLATED) as zout:
    for name in zin.namelist():
        df = pd.read_csv(zin.open(name))
        df, n = relabel(df)
        newname = name.replace("_OfS", "_MFmCmn").replace("_Ofs", "_MFmCmn")
        zout.writestr(newname, df.to_csv(index=False))
        print(f"zip: {name} -> {newname}, {n} values relabeled")

#Combined zip for the downstream chain: every building type's CSVs in one archive
combined = "CEDARS_LoadShape_Com.zip"
with zipfile.ZipFile(combined, "w", zipfile.ZIP_DEFLATED) as zout:
    for z in sorted(glob.glob(os.path.join(OUT, "*", "CEDARS_LoadShape_Com.zip"))):
        with zipfile.ZipFile(z) as zin:
            for name in zin.namelist():
                zout.writestr(name, zin.read(name))
    print(f"combined -> {combined}: {len(zout.namelist())} building-type CSVs")
