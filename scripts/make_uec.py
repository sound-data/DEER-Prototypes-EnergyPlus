"""
Build base & measure UEC tables (kWh, peak kW, therms) per TechID, from the runs.

For every run: annual Electricity:Facility -> UEC kWh, annual NaturalGas:Facility
-> UEC therms, and the CPUC peak window avg -> UEC kW (peak). Then map each
template row (TechID + CZ -> source run in col M) to that run's UEC, so the
output has one row per TechID with its base/measure UEC.

Usage:
  python make_uec.py "<template.xlsx>" "<runs dir;dir2...>" "<out.csv>" [SUB]
  SUB optional, e.g. "SFm&0=SFm&1"
"""
import sqlite3, sys, os, glob, datetime, csv, re, openpyxl

PEAKSPEC = {"CZ01":238,"CZ02":238,"CZ03":238,"CZ04":238,"CZ05":259,"CZ06":245,
            "CZ07":245,"CZ08":245,"CZ09":244,"CZ10":180,"CZ11":180,"CZ12":180,
            "CZ13":180,"CZ14":180,"CZ15":180,"CZ16":224}
J_KWH = 2.77778e-7
J_THERM = 1.0 / 105505585.257   # 1 therm = 1.05506e8 J

def annual_sum(con, name):
    q = ("SELECT SUM(rd.Value) FROM ReportData rd "
         "JOIN ReportDataDictionary d ON rd.ReportDataDictionaryIndex=d.ReportDataDictionaryIndex "
         "JOIN Time t ON rd.TimeIndex=t.TimeIndex "
         "JOIN EnvironmentPeriods e ON t.EnvironmentPeriodIndex=e.EnvironmentPeriodIndex "
         "WHERE d.Name=? AND d.ReportingFrequency='Hourly' AND e.EnvironmentType=3")
    r = con.execute(q, (name,)).fetchone()
    return r[0] if r and r[0] is not None else 0.0

def peak_kw(con, cz):
    start = datetime.datetime.strptime("2017-%d" % PEAKSPEC[cz], "%Y-%j").date()
    days = [start + datetime.timedelta(days=x) for x in range(3)]
    tq = ("SELECT t.TimeIndex FROM Time t "
          "JOIN EnvironmentPeriods e ON t.EnvironmentPeriodIndex=e.EnvironmentPeriodIndex "
          "WHERE e.EnvironmentType=3 AND ("
          "(t.Month=? AND t.Day=? AND t.Hour BETWEEN 15 AND 19) OR "
          "(t.Month=? AND t.Day=? AND t.Hour BETWEEN 15 AND 19) OR "
          "(t.Month=? AND t.Day=? AND t.Hour BETWEEN 15 AND 19))")
    params = []
    for d in days:
        params += [d.month, d.day]
    ti = [r[0] for r in con.execute(tq, params)]
    if not ti:
        return ""
    seq = ",".join("?" * len(ti))
    vq = ("SELECT rd.Value FROM ReportData rd "
          "JOIN ReportDataDictionary d ON rd.ReportDataDictionaryIndex=d.ReportDataDictionaryIndex "
          "WHERE d.Name='Electricity:Facility' AND d.ReportingFrequency='Hourly' "
          "AND rd.TimeIndex IN (%s)" % seq)
    v = [r[0] for r in con.execute(vq, ti)]
    return round((sum(v) / len(v)) * J_KWH, 4) if v else ""

def build_lookup(run_dirs):
    look = {}
    for runs in run_dirs:
        for sp in glob.glob(os.path.join(runs, "**", "instance-out.sql"), recursive=True):
            rel = os.path.relpath(sp, runs).replace("\\", "/").split("/")
            cz, cohort, case = rel[0], rel[1], rel[2]
            con = sqlite3.connect(sp)
            kwh = round(annual_sum(con, "Electricity:Facility") * J_KWH, 2)
            thm = round(annual_sum(con, "NaturalGas:Facility") * J_THERM, 4)
            kw = peak_kw(con, cz)
            con.close()
            look["%s__%s__%s.csv" % (cz, cohort, case)] = (kwh, kw, thm)
    return look

def main(template_xlsx, run_dirs, out_csv, sub=None):
    dirs = [d for d in run_dirs.split(";") if d]
    sub_old = sub_new = None
    if sub and "=" in sub:
        sub_old, sub_new = sub.split("=", 1)
    look = build_lookup(dirs)
    wb = openpyxl.load_workbook(template_xlsx, data_only=True)
    ws = wb["8760 post processing"] if "8760 post processing" in wb.sheetnames else wb.active
    rows = list(ws.iter_rows(values_only=True))
    meta_hdr = ["" if c is None else str(c) for c in rows[0]][:11]   # A-K
    out = [meta_hdr + ["UEC kWh", "UEC kW (peak)", "UEC Therms"]]
    miss = 0
    for r in rows[1:]:
        if r is None or all(c is None for c in r):
            continue
        vals = ["" if c is None else str(c) for c in r]
        while len(vals) < 13:
            vals.append("")
        src = vals[12].strip()
        if not src:
            continue
        if sub_old:
            src = src.replace(sub_old, sub_new)
        m = re.match(r'CZ0*(\d+)__', src)
        cz = int(m.group(1)) if m else None
        meta = vals[:11]
        if cz is not None:
            meta = meta[:4] + [str(cz)] + meta[5:]   # correct BldgLoc from source CZ
        uec = look.get(src)
        if uec is None:
            print("  MISSING run for:", src); miss += 1
            out.append(meta + ["", "", ""]); continue
        out.append(meta + [uec[0], uec[1], uec[2]])
    with open(out_csv, "w", newline="") as f:
        csv.writer(f).writerows(out)
    print(f"wrote {len(out)-1} UEC rows to {out_csv}  ({miss} missing)")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3],
         sys.argv[4] if len(sys.argv) > 4 else None)
