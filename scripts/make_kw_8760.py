"""
Build Pete's 8760 kW files from instance-var.csv (per Peter Jacobs spec).

For each run's instance-var.csv under <study>/runs/, take the
"Electricity:Facility [J](Hourly)" column, convert J -> kW (x 2.77778e-7),
and write a CSV of Date/Time + the 8760 annual-hour kW values into
<study>/8760_kW/.  Design/sizing-period rows (which precede the run period)
are excluded by taking the last 8760 hourly rows.

Usage:  python make_kw_8760.py "<study folder>"
"""
import sys, os, glob, csv

J_TO_KW = 2.77778e-7
FIELD = "Electricity:Facility [J](Hourly)"

def run_id(var_path, runs_dir):
    rel = os.path.relpath(var_path, runs_dir).replace("\\", "/").split("/")
    return "__".join(rel[:3])  # CZ / cohort / case

def main(study):
    runs_dir = os.path.join(study, "runs")
    out_dir = os.path.join(study, "8760_kW")
    os.makedirs(out_dir, exist_ok=True)
    files = glob.glob(os.path.join(runs_dir, "**", "instance-var.csv"), recursive=True)
    print(f"{len(files)} instance-var.csv found")
    ok = skipped = 0
    for vp in files:
        with open(vp, newline="") as f:
            rows = list(csv.reader(f))
        if not rows:
            print("  SKIP empty:", run_id(vp, runs_dir)); skipped += 1; continue
        header = [h.strip() for h in rows[0]]
        try:
            ei = header.index(FIELD)
        except ValueError:
            print("  SKIP (no Electricity:Facility col):", run_id(vp, runs_dir)); skipped += 1; continue
        data = rows[1:]
        annual = data[-8760:]               # run period is the last 8760 hourly rows
        if len(annual) != 8760:
            print(f"  SKIP ({len(data)} data rows): {run_id(vp, runs_dir)}"); skipped += 1; continue
        out = os.path.join(out_dir, run_id(vp, runs_dir) + ".csv")
        with open(out, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Date/Time", "kW"])
            for r in annual:
                dt = r[0].strip()
                kw = float(r[ei]) * J_TO_KW
                w.writerow([dt, f"{kw:.6f}"])
        ok += 1
    print(f"wrote {ok} kW files to {out_dir}  (skipped {skipped})")

if __name__ == "__main__":
    main(sys.argv[1])
