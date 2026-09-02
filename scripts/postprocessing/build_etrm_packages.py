"""Build the three eTRM deliverable packages for a measure, per the PY2028
filing instructions and the team's standard folder format.

  1. "<MeasureID> Energy Models Inputs YYYY-MM-DD.zip"
       Repo trimmed to this measure: templates, prototypes, codes, weather,
       querylibrary, scripts, the measure folder (no runs/, no generated
       outputs, no other measures).
  2. "<MeasureID> Energy Models Outputs YYYY-MM-DD.zip"
       Every run's instance.idf, instance-out.err, instance-tbl.htm,
       instance-out.sql (the four files CPUC requests).
  3. "<MeasureID> Postprocessed Outputs YYYY-MM-DD.zip"
       Per-study results + simdata files, plus (optional) a data
       transformation stash of per-building-type 8760/CEDARS outputs.

Usage (defaults shown for SWSV014):
  python build_etrm_packages.py ^
      --measure-dir "residential measures/SWSV014 Lifecycle Refridgerant Management" ^
      --measure-id SWSV014 ^
      --stash "scripts/data transformation/LRM_outputs_final" ^
      --package inputs outputs postproc
"""
import argparse
import os
import zipfile
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

STUDY_RESULT_FILES = ["results-summary.csv", "results-profile-elec.csv", "results-profile-gas.csv",
                      "simdata.csv", "simdata.sqlite", "simdata_weighted.csv", "simdata_norm.csv"]
RUN_KEEP = {"instance.idf", "instance-out.err", "instance-tbl.htm", "instance-out.sql"}
EXCLUDE_DIR_NAMES = {".git", ".claude", "__pycache__", "eTRM deliverables"}
EXCLUDE_FILE_NAMES = {"sim_hourly_wb.csv", "sfm_hourly_wb.csv", "sim_annual.csv", "sfm_annual.csv",
                      "current_msr_mat.csv", "result2.log", "results-summary.csv",
                      "results-profile-elec.csv", "results-profile-gas.csv", "modelkit_cmd_output.txt"}


def build_inputs(measure_dir: Path, dest: Path):
    measure_rel = measure_dir.relative_to(REPO).as_posix()
    count = 0
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for root, dirs, files in os.walk(REPO):
            rootp = Path(root)
            rel_root = rootp.relative_to(REPO)
            pruned = []
            for d in dirs:
                reld = (rel_root / d).as_posix().lstrip("./")
                if d in EXCLUDE_DIR_NAMES or d.startswith(("runs", "LRM_outputs", "CEDARS_", "PGE_", "postprocess")):
                    continue
                # keep only this measure's folder among the measures dirs
                if reld.count("/") == 1 and reld.split("/")[0].endswith("measures"):
                    if not (measure_rel.startswith(reld) or reld == measure_rel):
                        continue
                pruned.append(d)
            dirs[:] = pruned
            for f in files:
                rel = (rel_root / f).as_posix()
                if (f in EXCLUDE_FILE_NAMES or f.startswith("simdata") or f.startswith("CEDARS_")
                        or f.startswith("~$") or f.endswith(".backup") or f.endswith(".zip")):
                    continue
                zf.write(rootp / f, rel)
                count += 1
    print(f"inputs: {count} files -> {dest.name} ({dest.stat().st_size/1e6:,.0f} MB)")


def build_outputs(measure_dir: Path, dest: Path):
    count = 0
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for study in sorted(d for d in measure_dir.iterdir() if d.is_dir()):
            runs = study / "runs"
            if not runs.is_dir():
                print("  (no runs folder:", study.name + ")")
                continue
            for p in sorted(runs.rglob("*")):
                if p.is_file() and p.name in RUN_KEEP:
                    zf.write(p, str(p.relative_to(measure_dir)))
                    count += 1
    print(f"outputs: {count} files -> {dest.name} ({dest.stat().st_size/1e6:,.0f} MB)")


def build_postproc(measure_dir: Path, stash: Path | None, dest: Path):
    count = 0
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for study in sorted(d for d in measure_dir.iterdir() if d.is_dir()):
            for f in STUDY_RESULT_FILES:
                p = study / f
                if p.exists():
                    zf.write(p, f"{study.name}/{f}")
                    count += 1
                else:
                    print("  missing:", study.name, f)
        if stash and stash.is_dir():
            for p in sorted(stash.rglob("*")):
                if p.is_file():
                    comp = zipfile.ZIP_STORED if p.suffix == ".zip" else zipfile.ZIP_DEFLATED
                    zf.write(p, f"data transformation/{p.relative_to(stash).as_posix()}",
                             compress_type=comp)
                    count += 1
    print(f"postproc: {count} files -> {dest.name} ({dest.stat().st_size/1e6:,.0f} MB)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--measure-dir", required=True, help="measure folder, relative to repo root")
    ap.add_argument("--measure-id", required=True, help="e.g. SWSV014 (no version suffix)")
    ap.add_argument("--stash", default=None, help="per-building-type 8760/CEDARS stash dir (postproc package)")
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--out", default=str(REPO / "eTRM deliverables"))
    ap.add_argument("--package", nargs="+", default=["inputs", "outputs", "postproc"],
                    choices=["inputs", "outputs", "postproc"])
    args = ap.parse_args()

    measure_dir = (REPO / args.measure_dir).resolve()
    assert measure_dir.is_dir(), measure_dir
    out = Path(args.out)
    out.mkdir(exist_ok=True)
    stash = (REPO / args.stash).resolve() if args.stash else None

    if "inputs" in args.package:
        build_inputs(measure_dir, out / f"{args.measure_id} Energy Models Inputs {args.date}.zip")
    if "outputs" in args.package:
        build_outputs(measure_dir, out / f"{args.measure_id} Energy Models Outputs {args.date}.zip")
    if "postproc" in args.package:
        build_postproc(measure_dir, stash, out / f"{args.measure_id} Postprocessed Outputs {args.date}.zip")


if __name__ == "__main__":
    main()
