"""Build the SWHC062 eTRM deliverable packages from the current runs, matching
the folder/naming conventions of the 2026-08-2x packages:

  SWHC062 Energy Models Inputs <date>.zip        repo trimmed to this measure
  SWHC062 Energy Models Outputs by BldgType <date>/
      SWHC062 Outputs <BT> <date>.zip            instance.idf/-out.err/-tbl.htm/-out.sql per run
  SWHC062 Postprocessed Outputs <date>.zip       per-study results + data transformation stash
  SWHC062 CEDARS_LoadShape_Com <date>.zip        copy of CEDARS_LoadShape_Com_realTechID.zip
  SWHC062 8760 Load Shapes by BldgType <date>/   copy of PGE_8760_zips

Usage: python "scripts/postprocessing/build_etrm_swhc062.py" [--package ...] [--date YYYY-MM-DD]
"""
import argparse
import os
import shutil
import zipfile
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MEASURE = REPO / "commercial measures" / "SWHC062-03 Occupancy Fan Controller"
DT = REPO / "scripts" / "data transformation"
OUT = REPO / "eTRM deliverables"
STUDIES = ["SWHC062-03 Occupancy Fan Controller_Ex",
           "SWHC062-03 Occupancy Fan Controller_Htl_Ex"]

RUN_KEEP = {"instance.idf", "instance-out.err", "instance-tbl.htm", "instance-out.sql"}
STUDY_RESULT_FILES = ["results-summary.csv", "results-profile-elec.csv",
                      "results-profile-gas.csv", "simdata.csv", "simdata.sqlite"]
EXCLUDE_DIR_NAMES = {".git", ".claude", ".venv", ".vscode", "__pycache__",
                     "eTRM deliverables", "hourly_results", "outputs_by_bldgtype",
                     "PGE_8760_zips", "CEDARS_LoadShape_Com"}
EXCLUDE_DIR_PREFIXES = ("runs", "instance0", "SWHC062 Review Package")
EXCLUDE_FILE_NAMES = {"sim_hourly_wb.csv", "sim_hourly_eu.csv", "sim_annual.csv",
                      "current_msr_mat.csv", "results-summary.csv",
                      "results-profile-elec.csv", "results-profile-gas.csv"}
#small stash files copied into the postproc package under "data transformation/"
STASH_SCRIPTS = ["Com.py", "run_com_by_bldgtype.py", "make_mfmcmn_dupes.py",
                 "fix_cedars_techid.py", "package_8760_for_pge.py",
                 "make_hourly_wb_by_bldgtype.py", "split_cedars_by_cz.py",
                 "helper_functions.py"]
BT_SMALL = ["sim_annual.csv", "current_msr_mat.csv", "CEDARS_ls_annual_loads_Com.csv"]


def build_inputs(dest: Path):
    measure_rel = MEASURE.relative_to(REPO).as_posix()
    count = 0
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for root, dirs, files in os.walk(REPO):
            rootp = Path(root)
            rel_root = rootp.relative_to(REPO)
            pruned = []
            for d in dirs:
                reld = (rel_root / d).as_posix().lstrip("./")
                if d in EXCLUDE_DIR_NAMES or d.startswith(EXCLUDE_DIR_PREFIXES):
                    continue
                if reld.count("/") == 1 and reld.split("/")[0].endswith("measures"):
                    if not (measure_rel.startswith(reld) or reld == measure_rel):
                        continue
                pruned.append(d)
            dirs[:] = pruned
            for f in files:
                rel = (rel_root / f).as_posix()
                if (f in EXCLUDE_FILE_NAMES or f.startswith(("simdata", "CEDARS_", "~$", "htl_run"))
                        or f.endswith((".zip", ".log", ".err", ".pyc", ".bak"))):
                    continue
                zf.write(rootp / f, rel)
                count += 1
    print(f"inputs: {count} files -> {dest.name} ({dest.stat().st_size/1e6:,.0f} MB)", flush=True)


def build_outputs_by_bt(destdir: Path, datestr: str):
    destdir.mkdir(exist_ok=True)
    #map building type (as on disk) -> (study, BT dir name)
    bt_runs = {}
    for study in STUDIES:
        runs = MEASURE / study / "runs"
        for cz in sorted(runs.iterdir()):
            if not cz.is_dir():
                continue
            for btdir in sorted(cz.iterdir()):
                if btdir.is_dir():
                    bt_runs.setdefault(btdir.name, []).append((study, cz.name, btdir))
    for bt, entries in sorted(bt_runs.items()):
        dest = destdir / f"SWHC062 Outputs {bt} {datestr}.zip"
        count = 0
        with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for study, cz, btdir in entries:
                for p in sorted(btdir.rglob("*")):
                    if p.is_file() and p.name in RUN_KEEP:
                        zf.write(p, f"{study}/runs/{cz}/{bt}/{p.relative_to(btdir).as_posix()}")
                        count += 1
        print(f"outputs {bt}: {count} files -> {dest.name} "
              f"({dest.stat().st_size/1e9:,.2f} GB)", flush=True)


def build_postproc(dest: Path):
    count = 0
    missing = []
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for study in STUDIES:
            for f in STUDY_RESULT_FILES:
                p = MEASURE / study / f
                if p.exists():
                    zf.write(p, f"{study}/{f}")
                    count += 1
                else:
                    missing.append(f"{study}/{f}")
        #data transformation stash
        for name in ["Summary-Report.csv", "Deer Peak.csv"]:
            p = MEASURE / name
            if p.exists():
                zf.write(p, f"data transformation/{name}")
                count += 1
        hr = MEASURE / "hourly_results"
        for p in sorted(hr.glob("*")):
            zf.write(p, f"data transformation/hourly_results/{p.name}")
            count += 1
        for s in STASH_SCRIPTS:
            p = DT / s
            if p.exists():
                zf.write(p, f"data transformation/{s}")
                count += 1
        for btdir in sorted((DT / "outputs_by_bldgtype").iterdir()):
            if btdir.is_dir():
                for f in BT_SMALL:
                    p = btdir / f
                    if p.exists():
                        zf.write(p, f"data transformation/outputs_by_bldgtype/{btdir.name}/{f}")
                        count += 1
    for m in missing:
        print("  missing:", m)
    print(f"postproc: {count} files -> {dest.name} ({dest.stat().st_size/1e6:,.0f} MB)", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--package", nargs="+",
                    default=["inputs", "outputs", "postproc", "cedars", "shapes"],
                    choices=["inputs", "outputs", "postproc", "cedars", "shapes"])
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    d = args.date

    if "inputs" in args.package:
        build_inputs(OUT / f"SWHC062 Energy Models Inputs {d}.zip")
    if "cedars" in args.package:
        src = DT / "CEDARS_LoadShape_Com_realTechID.zip"
        shutil.copyfile(src, OUT / f"SWHC062 CEDARS_LoadShape_Com {d}.zip")
        print(f"cedars: copied -> SWHC062 CEDARS_LoadShape_Com {d}.zip", flush=True)
    if "shapes" in args.package:
        destdir = OUT / f"SWHC062 8760 Load Shapes by BldgType {d}"
        destdir.mkdir(exist_ok=True)
        for p in sorted((DT / "PGE_8760_zips").glob("*.zip")):
            shutil.copyfile(p, destdir / p.name)
        print(f"shapes: {len(list(destdir.glob('*.zip')))} zips -> {destdir.name}/", flush=True)
    if "postproc" in args.package:
        build_postproc(OUT / f"SWHC062 Postprocessed Outputs {d}.zip")
    if "outputs" in args.package:
        build_outputs_by_bt(OUT / f"SWHC062 Energy Models Outputs by BldgType {d}", d)


if __name__ == "__main__":
    main()
