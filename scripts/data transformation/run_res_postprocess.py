"""SWHC059 results chain: simdata + DEER peak, per vintage.

This is the chain that does NOT use the measure list. result2.py is a
sector-agnostic scraper: point it at a vintage folder, it walks runs/, reads
each instance-out.sql, and writes simdata.csv. The measure list belongs to the
other chain (run_res_by_bldgtype.py, which builds the CEDARS load shapes).

Per vintage:
    simdata.csv           result2.py
    simdata_norm.csv      normalize_simdata.py   (per-ft2, peak converted to kW)
    simdata_weighted.csv  weight_sfm_simdata.py  (SFm only: 1-story/2-story NumStor blend)
    simdata_weighted_norm.csv                    (SFm only)

result2.py writes simdata.csv into the *current directory*, so each vintage is
run with cwd set to its own folder. That also keeps the File Name column
relative to the vintage, matching the LRM deliverable.

Usage:
    python run_res_postprocess.py             # all vintages
    python run_res_postprocess.py DMo_Ex      # a subset, by key below
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SCRIPTS = os.path.join(REPO, "scripts")
MEASURE_DIR = os.path.join(REPO, "residential measures", "SWHC059 SFC")

# key -> (vintage folder name, SFm weighting vintage or None)
VINTAGES = {
    "DMo_Ex":   ("SWHC059 SFC AC HP _DMo_Ex",   None),
    "MFm_Ex":   ("SWHC059 SFC AC HP_MFm_Ex",    None),
    "SFm_1975": ("SWHC059 SFC AC HP_SFm_1975",  "1975"),
    "SFm_1985": ("SWHC059 SFC AC HP_SFm_1985",  "1985"),
}


def run(cmd, cwd, label):
    t0 = time.time()
    r = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True)
    ok = r.returncode == 0
    print(f"     {label}: {'OK' if ok else f'FAIL rc={r.returncode}'} ({time.time()-t0:.0f}s)", flush=True)
    if not ok:
        tail = [ln for ln in r.stdout.splitlines() if ln.strip()][-6:]
        for ln in tail:
            print(f"        {ln}", flush=True)
    return ok


def check_peak(simdata):
    """The DEER peak column disappears silently when anything upstream is off,
    so assert it is present and populated rather than trusting a zero exit."""
    import csv
    peak = "Electricity:Facility [J](Hourly)"
    with open(simdata, newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return "simdata.csv is empty"
    if peak not in rows[0]:
        return f"missing the {peak!r} column"
    blank = sum(1 for r in rows if not (r[peak] or "").strip())
    if blank:
        return f"{blank}/{len(rows)} rows have no DEER peak"
    return None


def main(argv):
    wanted = argv[1:] or list(VINTAGES)
    unknown = [v for v in wanted if v not in VINTAGES]
    if unknown:
        raise SystemExit(f"unknown vintage(s) {unknown}; choose from {list(VINTAGES)}")

    failures = []
    for key in wanted:
        folder, sfm_vint = VINTAGES[key]
        vdir = os.path.join(MEASURE_DIR, folder)
        print(f"== {key}  ({folder})", flush=True)
        if not os.path.isdir(os.path.join(vdir, "runs")):
            print("     no runs/ directory, skipping", flush=True)
            failures.append(key)
            continue

        # -P selects serial mode (argparse store_false), which avoids the
        # documented chunked-CSV column-misalignment risk in parallel mode.
        if not run([sys.executable, os.path.join(SCRIPTS, "result2.py"),
                    ".", "-q", "query.txt", "-P"], vdir, "result2 -> simdata.csv"):
            failures.append(key)
            continue

        problem = check_peak(os.path.join(vdir, "simdata.csv"))
        if problem:
            print(f"     DEER PEAK PROBLEM: {problem}", flush=True)
            failures.append(key)
            continue
        print("     DEER peak column present and fully populated", flush=True)

        run([sys.executable, os.path.join(SCRIPTS, "normalize_simdata.py"),
             "simdata.csv", "simdata_norm.csv"], vdir, "normalize -> simdata_norm.csv")

        if sfm_vint:
            if run([sys.executable, os.path.join(SCRIPTS, "weight_sfm_simdata.py"),
                    "simdata.csv", "simdata_weighted.csv", sfm_vint],
                   vdir, f"NumStor weighting ({sfm_vint}) -> simdata_weighted.csv"):
                run([sys.executable, os.path.join(SCRIPTS, "normalize_simdata.py"),
                     "simdata_weighted.csv", "simdata_weighted_norm.csv"],
                    vdir, "normalize -> simdata_weighted_norm.csv")

    print(f"\ndone. failures: {failures if failures else 'none'}", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
