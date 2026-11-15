"""Build the three 2026-09-15 deliverables Robert asked for, plus move
superseded dated packages to old/.

  SWHC062 Energy Models Inputs 2026-09-15.zip        (repo trimmed to measure)
  SWHC062 Energy Models Outputs 2026-09-15.zip       (idf+err+tbl per run, no sql)
  SWHC062 Postprocessed Outputs 2026-09-15.zip       (study results + data
      transformation stash + Energy Savings Calculations/ with the updated
      workbook and -all files)
"""
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PY = str(REPO / r".venv\Scripts\python.exe")
MEAS = REPO / "commercial measures" / "SWHC062-03 Occupancy Fan Controller"
DT = REPO / "scripts" / "data transformation"
PP = REPO / "postprocess"
ETRM = REPO / "eTRM deliverables"
OLD = ETRM / "old"
D = "2026-09-15"
STUDIES = ["SWHC062-03 Occupancy Fan Controller_Htl_Ex",
           "SWHC062-03 Occupancy Fan Controller_Ex"]
WB = "SWHC062_Energy_Savings_Calculations_20260915_updated.xlsx"


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


ETRM.mkdir(exist_ok=True)
OLD.mkdir(exist_ok=True)

# regenerate simdata.sqlite for both studies (pipeline wrote only csv)
for study in STUDIES:
    sdir = MEAS / study
    r = subprocess.run([PY, str(REPO / r"scripts\result2.py"), str(sdir), "-w",
                        "--queryfile", str(sdir / "query.txt")],
                       cwd=str(REPO), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(r.stdout[-1500:]); sys.exit(1)
    shutil.move(str(REPO / "simdata.sqlite"), str(sdir / "simdata.sqlite"))
    log(f"{study[-6:]}: simdata.sqlite regenerated")

# ---- 1. Inputs ----
r = subprocess.run([PY, str(REPO / r"scripts\postprocessing\build_etrm_swhc062.py"),
                    "--package", "inputs", "--date", D],
                   cwd=str(REPO), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                   text=True, encoding="utf-8", errors="replace")
log(r.stdout.strip().splitlines()[-1])
if r.returncode != 0:
    sys.exit(1)

# ---- 2. Outputs (single combined, no sql) ----
KEEP = {"instance.idf", "instance-out.err", "instance-tbl.htm"}
dest = ETRM / f"SWHC062 Energy Models Outputs {D}.zip"
note = ("SWHC062 Energy Models Outputs " + D + "\nOne folder per run (both studies, "
        "10,240 runs): instance.idf, instance-out.err, instance-tbl.htm.\n"
        "instance-out.sql omitted for size; per-building-type sql zips available on "
        "request. Reflects the 2026-09-15 M3/M5 measure-case update (base 3/5).\n")
count = 0
with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    zf.writestr("README.txt", note)
    for study in STUDIES:
        runs = MEAS / study / "runs"
        for p in sorted(runs.rglob("*")):
            if p.is_file() and p.name in KEEP:
                zf.write(p, f"{study}/runs/{p.relative_to(runs).as_posix()}")
                count += 1
log(f"outputs: {count} files -> {dest.name} ({dest.stat().st_size/1e9:.2f} GB)")

# ---- 3. Postprocessed (+ savings) ----
STUDY_FILES = ["results-summary.csv", "results-profile-elec.csv",
               "results-profile-gas.csv", "simdata.csv", "simdata.sqlite"]
STASH = ["Com.py", "Com_SWHC062.py", "run_com_by_bldgtype.py", "make_mfmcmn_dupes.py",
         "fix_cedars_techid.py", "package_8760_for_pge.py", "helper_functions.py"]
BT_SMALL = ["sim_annual.csv", "current_msr_mat.csv", "CEDARS_ls_annual_loads_Com.csv"]
SAVINGS = [WB, "Summary-Report-all.csv", "Deer_Peak_-_Electric-all.csv", "Measure Off-hour2.csv"]
dest = ETRM / f"SWHC062 Postprocessed Outputs {D}.zip"
count = 0
with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    for study in STUDIES:
        for f in STUDY_FILES:
            p = MEAS / study / f
            if p.exists():
                zf.write(p, f"{study}/{f}"); count += 1
    for name in ["Summary-Report.csv", "Deer Peak.csv"]:
        p = MEAS / name
        if p.exists():
            zf.write(p, f"data transformation/{name}"); count += 1
    for p in sorted((MEAS / "hourly_results").glob("*")):
        zf.write(p, f"data transformation/hourly_results/{p.name}"); count += 1
    for s in STASH:
        p = DT / s
        if p.exists():
            zf.write(p, f"data transformation/{s}"); count += 1
    for btdir in sorted((DT / "outputs_by_bldgtype").iterdir()):
        if btdir.is_dir():
            for f in BT_SMALL:
                p = btdir / f
                if p.exists():
                    zf.write(p, f"data transformation/outputs_by_bldgtype/{btdir.name}/{f}"); count += 1
    for f in SAVINGS:
        p = PP / f
        if p.exists():
            zf.write(p, f"Energy Savings Calculations/{f}"); count += 1
        else:
            log(f"  !! savings file missing: {f}")
log(f"postproc: {count} files -> {dest.name} ({dest.stat().st_size/1e6:.0f} MB)")

# ---- move superseded ----
for name in [p.name for p in ETRM.iterdir()
             if p.name != "old" and ("2026-09-11" in p.name or "2026-09-12" in p.name
                                     or "2026-09-13" in p.name or "2026-08" in p.name)]:
    src = ETRM / name
    if src.exists():
        shutil.move(str(src), str(OLD / name))
        log(f"moved to old/: {name}")
log("FINAL PACKAGES 2026-09-15 COMPLETE")
