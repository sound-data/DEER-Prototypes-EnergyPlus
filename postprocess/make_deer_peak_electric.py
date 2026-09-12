"""Build "Deer Peak - Electric.csv" for the OFC runs, matching the format of
Robert's "Deer Peak - Electric-all.csv":
  Building Type, Measure, System Type, Run Type, Climate Zone,
  Average Temperature, Average Electric Energy
Average = mean over the DEER peak period (CZ2025 peak days, 4-9 PM prevailing,
same convention as scripts/result2.py: get_deer_peak_multipliers).
Electric energy stays in J/hour (as in the reference file); temperature in C.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, r"C:\DEER-Prototypes-EnergyPlus\scripts")
from result2 import get_deer_peak_multipliers  # noqa: E402

MEASURE = Path(r"C:\dev\SWHC062-03\commercial measures\SWHC062-03 Occupancy Fan Controller")
RUNS_DIRS = [MEASURE / "SWHC062-03 Occupancy Fan Controller_Ex" / "runs",
             MEASURE / "SWHC062-03 Occupancy Fan Controller_Htl_Ex" / "runs"]
OUT = Path(r"C:\dev\SWHC062-03\postprocess\Deer Peak - Electric.csv")
ELEC = "Electricity:Facility [J](Hourly)"
TEMP = "Environment:Site Outdoor Air Drybulb Temperature [C](Hourly)"

rows = []
var_files = sorted(p for runs in RUNS_DIRS for p in runs.glob("CZ*/*/*/instance-var.csv"))
print(f"{len(var_files)} hourly files")
for i, vf in enumerate(var_files):
    cz = vf.parts[-4]
    bt = vf.parts[-3]
    measure, system, runtype = vf.parts[-2].split("-")
    hdr = pd.read_csv(vf, nrows=0).columns
    temp_col = next(c for c in hdr if "Drybulb" in c)
    elec_col = next((c for c in hdr if "Electricity:Facility" in c), None)
    if elec_col is not None:
        df = pd.read_csv(vf, usecols=[elec_col, temp_col]).rename(
            columns={elec_col: ELEC, temp_col: TEMP})
    else:
        # some building types (e.g. Eun) only report the whole-building meter
        # in the EnergyPlus working folder's eplusmtr.csv
        mtr = next(vf.parent.glob("instance0*/eplusmtr.csv"))
        mdf = pd.read_csv(mtr)
        mcol = next(c for c in mdf.columns if "Electricity:Facility" in c)
        tdf = pd.read_csv(vf, usecols=[temp_col])
        df = pd.DataFrame({ELEC: mdf[mcol].to_numpy()[-8760:],
                           TEMP: tdf[temp_col].to_numpy()[-8760:]})
    if len(df) != 8760:
        df = df.tail(8760)
    mult = get_deer_peak_multipliers(cz)
    rows.append({
        "Building Type": bt, "Measure": measure, "System Type": system,
        "Run Type": runtype, "Climate Zone": cz,
        "Average Temperature": float(np.dot(df[TEMP].to_numpy(), mult)),
        "Average Electric Energy": float(np.dot(df[ELEC].to_numpy(), mult)),
    })
    if (i + 1) % 1000 == 0:
        print(f"{i+1}/{len(var_files)}", flush=True)

out = pd.DataFrame(rows)
bt_order = sorted(out["Building Type"].unique())
out["Building Type"] = pd.Categorical(out["Building Type"], bt_order, ordered=True)
out = out.sort_values(["Building Type", "Measure", "System Type", "Run Type", "Climate Zone"])
out.to_csv(OUT, index=False)
print(f"wrote {len(out)} rows -> {OUT}")
