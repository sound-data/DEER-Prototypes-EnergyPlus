"""Run the SWHC059 residential transformation once per building type.

Mirrors run_com_by_bldgtype.py (SWHC062 / OFC), adapted for residential:
the commercial side has one script (Com_SWHC062.py) driven across many building
types, whereas residential has one script per building type. So instead of
looping workbooks and re-running a single script, this pairs each per-building-type
workbook in DEER_EnergyPlus_Modelkit_Measure_list_working_dir with the matching
*_SWHC059.py script.

Each pass sets RES_WORKBOOK (and the run paths) in the environment and stashes
that pass's outputs under outputs_by_bldgtype/<BldgType>/, because all three
scripts write current_msr_mat.csv to the same filename and would otherwise
overwrite each other.

The shared DEER_EnergyPlus_Modelkit_Measure_list_working.xlsx is never touched.

Usage:
    python run_res_by_bldgtype.py            # all building types
    python run_res_by_bldgtype.py DMo SFm    # a subset
"""
import os
import shutil
import subprocess
import sys
import time

os.chdir(os.path.dirname(os.path.abspath(__file__)))

WB_DIR = "DEER_EnergyPlus_Modelkit_Measure_list_working_dir"
OUT = "outputs_by_bldgtype"
MEASURE = "Smart Fan Controller, Residential"
MEASURE_DIR = "residential measures/SWHC059 SFC"

# bldgtype -> (script, extra environment, output files to stash)
JOBS = {
    "DMo": (
        "DMo_SWHC059.py",
        {"RES_PATH": f"{MEASURE_DIR}/SWHC059 SFC AC HP _DMo_Ex"},
        ["current_msr_mat.csv", "sim_annual.csv", "sim_hourly_wb.csv",
         "CEDARS_LoadShape_DMo.zip", "CEDARS_ls_annual_loads_DMo.csv"],
        ["CEDARS_long_ls_DMo.csv"],
    ),
    "MFm": (
        "MFm_SWHC059.py",
        {"RES_PATH": f"{MEASURE_DIR}/SWHC059 SFC AC HP_MFm_Ex"},
        ["current_msr_mat.csv", "sim_annual.csv", "sim_hourly_wb.csv",
         "CEDARS_LoadShape_MFm.zip", "CEDARS_ls_annual_loads_MFm.csv"],
        ["CEDARS_long_ls_MFm.csv"],
    ),
    "SFm": (
        "SFm_SWHC059.py",
        {"RES_1975": f"{MEASURE_DIR}/SWHC059 SFC AC HP_SFm_1975",
         "RES_1985": f"{MEASURE_DIR}/SWHC059 SFC AC HP_SFm_1985",
         "RES_MODE_NEW_VINTAGE": "0"},
        # SFm names its annual/hourly outputs differently from DMo/MFm
        ["current_msr_mat.csv", "sfm_annual.csv", "sfm_hourly_wb.csv",
         "CEDARS_LoadShape_SFm.zip", "CEDARS_ls_annual_loads_SFm.csv"],
        ["CEDARS_long_ls_SFm.csv"],
    ),
}


def restore_if_tracked(path):
    """Put back a git-tracked file we just stashed into outputs_by_bldgtype/.

    sim_annual.csv, sim_hourly_wb.csv and current_msr_mat.csv are committed
    artifacts from earlier measures. A pass legitimately overwrites them, and
    stashing the result is what we want per building type, but leaving the repo
    with three deleted files afterwards is just noise. Restore the committed
    copy; the SWHC059 output lives in outputs_by_bldgtype/<BldgType>/ either way.
    """
    try:
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", path],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        if tracked:
            subprocess.run(["git", "checkout", "--", path],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except (OSError, subprocess.SubprocessError):
        pass   # no git available: leave the working tree as-is


def workbook_for(bldgtype):
    """The per-building-type workbook, matched on a trailing '_<BldgType>.xlsx' or ' <BldgType>.xlsx'."""
    matches = [f for f in sorted(os.listdir(WB_DIR))
               if f.endswith((f"_{bldgtype}.xlsx", f" {bldgtype}.xlsx")) and not f.startswith("~")]
    if len(matches) != 1:
        raise SystemExit(
            f"expected exactly one workbook ending in '_{bldgtype}.xlsx' in {WB_DIR}, found {matches}")
    return os.path.abspath(os.path.join(WB_DIR, matches[0]))


def main(argv):
    wanted = argv[1:] or list(JOBS)
    unknown = [b for b in wanted if b not in JOBS]
    if unknown:
        raise SystemExit(f"unknown building type(s) {unknown}; choose from {list(JOBS)}")

    print(f"{len(wanted)} building type(s) to process: {', '.join(wanted)}", flush=True)
    failures = []
    for bt in wanted:
        script, extra_env, outputs, discard = JOBS[bt]
        dest = os.path.join(OUT, bt)
        os.makedirs(dest, exist_ok=True)
        env = dict(os.environ, RES_WORKBOOK=workbook_for(bt), RES_MEASURE=MEASURE, **extra_env)

        # Fingerprint the output names before the run. Several of these (sim_annual.csv,
        # sim_hourly_wb.csv, current_msr_mat.csv) are checked-in artifacts from earlier
        # work, and stashing one this pass did not write would silently delete it.
        before = {f: os.path.getmtime(f) for f in outputs if os.path.exists(f)}

        t0 = time.time()
        with open(os.path.join(dest, "res_run.log"), "w") as log:
            r = subprocess.run([sys.executable, script], stdout=log,
                               stderr=subprocess.STDOUT, env=env)

        moved, untouched = [], []
        for f in outputs:
            if not os.path.exists(f):
                continue
            if f in before and os.path.getmtime(f) == before[f]:
                untouched.append(f)   # pre-existing and not rewritten: leave it alone
                continue
            shutil.move(f, os.path.join(dest, f))
            moved.append(f)
            restore_if_tracked(f)
        # Uncompressed duplicates of the zipped load shape; hundreds of MB each.
        for f in discard:
            if os.path.exists(f):
                os.remove(f)

        status = "OK" if r.returncode == 0 else f"FAIL rc={r.returncode}"
        if r.returncode != 0:
            failures.append(bt)
        print(f"{bt}: {status}, {len(moved)}/{len(outputs)} outputs, {time.time()-t0:.0f}s",
              flush=True)
        if untouched:
            print(f"   left in place (pre-existing, not rewritten): {sorted(untouched)}", flush=True)
        absent = sorted(set(outputs) - set(moved) - set(untouched))
        if absent:
            print(f"   not produced: {absent}", flush=True)

    print(f"done. failures: {failures if failures else 'none'}", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
