"""
Build 8760-hour normalized load shapes from Electricity:Facility [J](Hourly).

For each run's instance-out.sql under <study>/runs/, take the ANNUAL run-period
(EnvironmentType=3) hourly Electricity:Facility series (8760 values, design days
excluded), sum them, divide each hour by the sum, and write an 8760-row load
shape CSV per run into <study>/load_shapes/.

Usage:  python make_load_shapes.py "<study folder>"
"""
import sqlite3, sys, os, glob

QUERY = """
SELECT rd.Value
FROM ReportData rd
JOIN ReportDataDictionary d ON rd.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex
JOIN Time t ON rd.TimeIndex = t.TimeIndex
JOIN EnvironmentPeriods e ON t.EnvironmentPeriodIndex = e.EnvironmentPeriodIndex
WHERE d.Name = 'Electricity:Facility'
  AND d.ReportingFrequency = 'Hourly'
  AND e.EnvironmentType = 3
ORDER BY rd.TimeIndex
"""

def run_id(sql_path, runs_dir):
    rel = os.path.relpath(sql_path, runs_dir).replace("\\", "/").split("/")
    # rel = [CZ, cohort, case, instanceXXXX, instance-out.sql]
    return "__".join(rel[:3])

def main(study):
    runs_dir = os.path.join(study, "runs")
    out_dir = os.path.join(study, "load_shapes")
    os.makedirs(out_dir, exist_ok=True)
    sqls = glob.glob(os.path.join(runs_dir, "**", "instance-out.sql"), recursive=True)
    print(f"{len(sqls)} run SQLs found")
    ok = skipped = 0
    for sp in sqls:
        try:
            con = sqlite3.connect(sp)
            vals = [r[0] for r in con.execute(QUERY)]
            con.close()
        except Exception as ex:
            print("  ERROR reading", sp, ex); skipped += 1; continue
        if len(vals) != 8760:
            print(f"  SKIP ({len(vals)} hrs, expected 8760): {run_id(sp, runs_dir)}")
            skipped += 1; continue
        total = sum(vals)
        if total == 0:
            print(f"  SKIP (zero total): {run_id(sp, runs_dir)}"); skipped += 1; continue
        name = run_id(sp, runs_dir) + ".csv"
        with open(os.path.join(out_dir, name), "w", newline="") as f:
            f.write("Hour,LoadShape\n")
            for i, v in enumerate(vals, 1):
                f.write(f"{i},{v/total:.10g}\n")
        ok += 1
    print(f"wrote {ok} load-shape files to {out_dir}  (skipped {skipped})")

if __name__ == "__main__":
    main(sys.argv[1])
