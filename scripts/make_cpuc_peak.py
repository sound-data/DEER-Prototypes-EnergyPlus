"""
CPUC peak-demand (kW) per run, replicating the DEER process_deer_peak method.

For each run's instance-out.sql under <study>/runs/, take the CZ-specific CPUC
peak window (3 days starting at peakspec[cz] day-of-year, hours 15-19 =
4-9pm), pull Electricity:Facility over those 15 hours from the annual run
period, average it, and convert J/hr -> kW.

Usage:  python make_cpuc_peak.py "<study folder>"
Writes <study>/cpuc_peak_demand.csv (one row per run).
"""
import sqlite3, sys, os, glob, datetime, csv

PEAKSPEC = {"CZ01":238,"CZ02":238,"CZ03":238,"CZ04":238,"CZ05":259,"CZ06":245,
            "CZ07":245,"CZ08":245,"CZ09":244,"CZ10":180,"CZ11":180,"CZ12":180,
            "CZ13":180,"CZ14":180,"CZ15":180,"CZ16":224}
J_TO_KW = 2.77778e-7

def peak_timeindexes(con, cz):
    start = datetime.datetime.strptime("2017-%d" % PEAKSPEC[cz], "%Y-%j").date()
    days = [start + datetime.timedelta(days=x) for x in range(3)]
    q = ("SELECT t.TimeIndex FROM Time t "
         "JOIN EnvironmentPeriods e ON t.EnvironmentPeriodIndex=e.EnvironmentPeriodIndex "
         "WHERE e.EnvironmentType=3 AND ("
         "(t.Month=? AND t.Day=? AND t.Hour BETWEEN 15 AND 19) OR "
         "(t.Month=? AND t.Day=? AND t.Hour BETWEEN 15 AND 19) OR "
         "(t.Month=? AND t.Day=? AND t.Hour BETWEEN 15 AND 19))")
    params = []
    for d in days:
        params += [d.month, d.day]
    return [r[0] for r in con.execute(q, params)]

def main(study):
    runs_dir = os.path.join(study, "runs")
    sqls = glob.glob(os.path.join(runs_dir, "**", "instance-out.sql"), recursive=True)
    out = os.path.join(study, "cpuc_peak_demand.csv")
    rows, bad = [], 0
    for sp in sqls:
        rel = os.path.relpath(sp, runs_dir).replace("\\", "/").split("/")
        cz, cohort, case = rel[0], rel[1], rel[2]
        con = sqlite3.connect(sp)
        ti = peak_timeindexes(con, cz)
        seq = ",".join("?" * len(ti)) if ti else ""
        vals = []
        if ti:
            q = ("SELECT rd.Value FROM ReportData rd "
                 "JOIN ReportDataDictionary d ON rd.ReportDataDictionaryIndex=d.ReportDataDictionaryIndex "
                 "WHERE d.Name='Electricity:Facility' AND d.ReportingFrequency='Hourly' "
                 "AND rd.TimeIndex IN (%s)" % seq)
            vals = [r[0] for r in con.execute(q, ti)]
        con.close()
        if not vals:
            bad += 1
            rows.append([cz, cohort, case, len(ti), ""]); continue
        peak_kw = (sum(vals) / len(vals)) * J_TO_KW
        rows.append([cz, cohort, case, len(vals), round(peak_kw, 4)])
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Climate Zone", "Cohort", "Case", "PeakHoursFound", "Peak Demand (kW)"])
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {out}  ({bad} with no data)")

if __name__ == "__main__":
    main(sys.argv[1])
