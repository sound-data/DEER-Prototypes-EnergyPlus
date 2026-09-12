"""Assemble the 17-building-type '-all' files the Energy Savings workbook
script expects:
  Summary-Report-all.csv      (metadata row + header; Ex + Htl + MFmCmn=OfS copy)
  Deer_Peak_-_Electric-all.csv (Ex + Htl + MFmCmn=OfS copy)
MFmCmn is a direct relabeled copy of OfS per the established convention."""
import pandas as pd
from pathlib import Path

PP = Path(r"C:\dev\SWHC062-03\postprocess")

# --- Summary-Report-all ---
# process_summary_data_multi_measure.py now covers both studies in one file
s = pd.read_csv(Path(r"C:\dev\SWHC062-03\commercial measures\SWHC062-03 Occupancy Fan Controller\Summary-Report.csv"))
mf = s[s.BldgType == "OfS"].copy()
mf["BldgType"] = "MFmCmn"
s = pd.concat([s, mf], ignore_index=True)
print("Summary-all:", len(s), "rows | types:", s.BldgType.nunique())
out = PP / "Summary-Report-all.csv"
with open(out, "w", newline="") as f:
    f.write(",,,,,,,,,therm/Kwh conversion factor,0.03412,,,,W/tons conversion factor\n")
    s.to_csv(f, index=False)

# --- Deer_Peak_-_Electric-all ---
p = pd.read_csv(PP / "Deer Peak - Electric.csv")
mfp = p[p["Building Type"] == "OfS"].copy()
mfp["Building Type"] = "MFmCmn"
p = pd.concat([p, mfp], ignore_index=True)
print("Peak-all:", len(p), "rows | types:", p["Building Type"].nunique())
p.to_csv(PP / "Deer_Peak_-_Electric-all.csv", index=False)
print("done")
