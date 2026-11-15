"""Assemble the SWHC059 eTRM deliverable packages.

Mirrors what was delivered for SWSV014 (refrigerant management, residential) and
SWHC062 (occupancy fan controller, commercial):

    SWHC059 Energy Models Inputs <date>.zip        repo tree, no runs
    SWHC059 Energy Models Outputs <vintage>.zip    one per vintage (runs are ~4 GB total)
    SWHC059 Postprocessed Outputs <date>.zip       per-vintage results + simdata
    SWHC059 CEDARS 8760s by CZ <date>/             built separately by package_8760_swhc059.py

Run package_8760_swhc059.py first if you want the load shapes alongside these.

Usage:
    python build_etrm_swhc059.py                 # everything
    python build_etrm_swhc059.py inputs post     # a subset: inputs | outputs | post
"""
import os
import sys
import zipfile
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
MEASURE_REL = os.path.join("residential measures", "SWHC059 SFC")
OUT = os.path.join(REPO, "eTRM deliverables")
TODAY = f"{date.today():%Y-%m-%d}"

VINTAGES = ["SWHC059 SFC AC HP _DMo_Ex", "SWHC059 SFC AC HP_MFm_Ex",
            "SWHC059 SFC AC HP_SFm_1975", "SWHC059 SFC AC HP_SFm_1985"]

# Inputs package: the model tree, not the results.
INPUT_DIRS = ["codes", "prototypes", "templates", "weather", "querylibrary"]
INPUT_FILES = ["README.md", ".gitattributes", ".gitignore", "pull_request_template.md"]

# Per-vintage postprocessed artifacts, in the order SWSV014 delivered them.
POST_FILES = ["results-summary.csv", "results-profile-elec.csv", "results-profile-gas.csv",
              "simdata.csv", "simdata_norm.csv", "simdata_weighted.csv",
              "simdata_weighted_norm.csv"]

SKIP_DIRS = {".git", "__pycache__", "runs", "eTRM deliverables", ".vscode",
             "outputs_by_bldgtype", ".claude"}


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}"
        n /= 1024


def add_tree(zf, abs_root, arc_root, skip=SKIP_DIRS):
    count = 0
    for dirpath, dirnames, filenames in os.walk(abs_root):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            arc = os.path.join(arc_root, os.path.relpath(full, abs_root))
            zf.write(full, arc)
            count += 1
    return count


def build_inputs():
    path = os.path.join(OUT, f"SWHC059 Energy Models Inputs {TODAY}.zip")
    print(f"building {os.path.basename(path)}", flush=True)
    n = 0
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for d in INPUT_DIRS:
            src = os.path.join(REPO, d)
            if os.path.isdir(src):
                n += add_tree(zf, src, d)
        for f in INPUT_FILES:
            src = os.path.join(REPO, f)
            if os.path.isfile(src):
                zf.write(src, f)
                n += 1
        # the measure setup itself, minus runs (SKIP_DIRS) and minus the bulky
        # results that belong in the postprocessed package
        src = os.path.join(REPO, MEASURE_REL)
        for dirpath, dirnames, filenames in os.walk(src):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                if fn in POST_FILES:
                    continue
                full = os.path.join(dirpath, fn)
                zf.write(full, os.path.join(MEASURE_REL, os.path.relpath(full, src)))
                n += 1
        # the scripts that produced the results, excluding their own large outputs
        for dirpath, dirnames, filenames in os.walk(os.path.join(REPO, "scripts")):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                full = os.path.join(dirpath, fn)
                if os.path.getsize(full) > 20 * 1024 * 1024:
                    continue          # stale bulk CSVs checked in under scripts/
                zf.write(full, os.path.join("scripts", os.path.relpath(full, os.path.join(REPO, "scripts"))))
                n += 1
    print(f"   {n} files, {human(os.path.getsize(path))}", flush=True)


def build_outputs():
    for v in VINTAGES:
        runs = os.path.join(REPO, MEASURE_REL, v, "runs")
        if not os.path.isdir(runs):
            print(f"skipping outputs for {v}: no runs/", flush=True)
            continue
        tag = v.replace("SWHC059 SFC AC HP", "").strip().strip("_") or v
        path = os.path.join(OUT, f"SWHC059 Energy Models Outputs {tag} {TODAY}.zip")
        print(f"building {os.path.basename(path)} (this is the slow one)", flush=True)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
            n = add_tree(zf, runs, os.path.join(v, "runs"), skip={"__pycache__"})
        print(f"   {n} files, {human(os.path.getsize(path))}", flush=True)


def build_post():
    path = os.path.join(OUT, f"SWHC059 Postprocessed Outputs {TODAY}.zip")
    print(f"building {os.path.basename(path)}", flush=True)
    n, missing = 0, []
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for v in VINTAGES:
            vdir = os.path.join(REPO, MEASURE_REL, v)
            for fn in POST_FILES:
                full = os.path.join(vdir, fn)
                if os.path.isfile(full):
                    zf.write(full, os.path.join(v, fn))
                    n += 1
                elif not fn.startswith("simdata_weighted") or "SFm" in v:
                    # weighted variants only exist for SFm; anything else is a real gap
                    missing.append(f"{v}/{fn}")
    print(f"   {n} files, {human(os.path.getsize(path))}", flush=True)
    if missing:
        print("   MISSING (run run_res_postprocess.py first):", flush=True)
        for m in missing:
            print(f"     {m}", flush=True)


def main(argv):
    stages = argv[1:] or ["inputs", "outputs", "post"]
    unknown = [s for s in stages if s not in ("inputs", "outputs", "post")]
    if unknown:
        raise SystemExit(f"unknown stage(s) {unknown}; choose from inputs, outputs, post")
    os.makedirs(OUT, exist_ok=True)
    for s in stages:
        {"inputs": build_inputs, "outputs": build_outputs, "post": build_post}[s]()
    print(f"\ndone -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
