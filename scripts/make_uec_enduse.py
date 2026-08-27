"""
Fill the revised UEC templates (base/measure, by end use) from the run results.

End-use kWh/therms come from each study's results-summary end-use block
(Heating Elec / Cooling Elec / Fans / Heating NG / Cooling NG). Peak kW comes
from each run's SQL over the CPUC peak window (not in the summary).

TechID -> run mapping (semantic, NC shares the NR runs):
  AOE base 0%      -> "LRM AOE LSC ... Base"
  AOE base X%      -> "LRM AOE +X% RCA LSC ... Base"
  AOE measure      -> "LRM AOE ... Measure"
  NR/NC base       -> "LRM NR LSC ... Base"
  NR/NC measure    -> "LRM NR ... Measure"
SFm: 1-story and 2-story weighted via numstor (CZ1-9=1975, CZ10-16=1985).
"""
import csv, os, re, glob, sqlite3, datetime, sys

BASE = sys.argv[1]    # measure root
DL   = sys.argv[2]    # downloads (templates in/out)
OUT  = sys.argv[3]    # output folder

KWH_PER_THERM = 29.3001
J_KWH = 2.77778e-7
PEAKSPEC = {"CZ01":238,"CZ02":238,"CZ03":238,"CZ04":238,"CZ05":259,"CZ06":245,
            "CZ07":245,"CZ08":245,"CZ09":244,"CZ10":180,"CZ11":180,"CZ12":180,
            "CZ13":180,"CZ14":180,"CZ15":180,"CZ16":224}
NUMSTOR = {1:1.48,2:1.48,3:1.48,4:1.48,5:1.48,6:1.55,7:1.55,8:1.55,9:1.33,
           10:1.42,11:1.23,12:1.23,13:1.23,14:1.12,15:1.12,16:1.31}
STUDIES = {  # folder, summary, story-split?
    "Dmo": ("SWSV014-02 LRM AC HP _Dmo_Ex", "results-summary-Dmo.csv"),
    "Mfm": ("SWSV014-02 LRM AC HP_MFm_Ex", "results-summary-Mfm.csv"),
    "S75": ("SWSV014-02 LRM AC HP_SFm_1975", "results-summary-Sfm-1975.csv"),
    "S85": ("SWSV014-02 LRM AC HP_SFm_1985", "results-summary-Sfm-1985.csv"),
}
ECOLS = ["Heating Elec (kWh)","Cooling Elec (kWh)","Fans (kWh)","Heating NG (kWh)","Cooling NG (kWh)"]

def parse_case(case):
    hvac = "rDXHP" if "rDXHP" in case else "rDXGF"
    typ  = "measure" if "Measure" in case else "base"
    prog = "AOE" if "AOE" in case else ("NR" if "NR" in case else None)
    m = re.search(r"\+(\d+\.?\d*)% RCA", case)
    uc = float(m.group(1)) if m else 0.0
    return hvac, prog, typ, uc

def parse_techid(tid):
    hvac = "rDXHP" if "rDXHP" in tid else "rDXGF"
    typ  = "measure" if "LRM-LSC" in tid else "base"
    prog = "AOE" if "AOE" in tid else ("NC" if tid.rstrip().endswith("NC") else "NR")
    m = re.search(r"NoLRM-(\d+\.?\d*)% UC", tid)
    uc = float(m.group(1)) if m else 0.0
    return hvac, prog, typ, uc

def key(building, cz, story, hvac, prog, typ, uc):
    return (building, cz, story, hvac, prog, typ, uc if typ == "base" else None)

# ---- load end-use lookup from results summaries ----
enduse = {}
for tag, (folder, summ) in STUDIES.items():
    rows = list(csv.reader(open(os.path.join(BASE, folder, summ))))
    hi = next(i for i,r in enumerate(rows) if r and r[0]=="File Name" and "Cooling Elec (kWh)" in r)
    idx = {c: rows[hi].index(c) for c in ECOLS}
    for r in rows[hi+1:]:
        if not r or r[0]=="File Name" or "/" not in r[0]: continue
        p = r[0].split("/"); cz = int(p[0][2:]); cp = p[1].split("&")
        bld, story = cp[0], cp[1]
        hvac, prog, typ, uc = parse_case(p[2])
        if not prog: continue
        try: enduse[key(bld,cz,story,hvac,prog,typ,uc)] = {c: float(r[idx[c]]) for c in ECOLS}
        except (ValueError, IndexError): pass

# ---- peak kW from SQL ----
def peak_kw(con, cz):
    start = datetime.datetime.strptime("2017-%d" % PEAKSPEC[cz], "%Y-%j").date()
    days = [start + datetime.timedelta(days=x) for x in range(3)]
    q = ("SELECT t.TimeIndex FROM Time t JOIN EnvironmentPeriods e ON t.EnvironmentPeriodIndex=e.EnvironmentPeriodIndex "
         "WHERE e.EnvironmentType=3 AND ((t.Month=? AND t.Day=? AND t.Hour BETWEEN 16 AND 20) OR "
         "(t.Month=? AND t.Day=? AND t.Hour BETWEEN 16 AND 20) OR (t.Month=? AND t.Day=? AND t.Hour BETWEEN 16 AND 20))")
    pr = []
    for d in days: pr += [d.month, d.day]
    ti = [x[0] for x in con.execute(q, pr)]
    if not ti: return ""
    seq = ",".join("?"*len(ti))
    v = [x[0] for x in con.execute(
        "SELECT rd.Value FROM ReportData rd JOIN ReportDataDictionary d ON rd.ReportDataDictionaryIndex=d.ReportDataDictionaryIndex "
        "WHERE d.Name='Electricity:Facility' AND d.ReportingFrequency='Hourly' AND rd.TimeIndex IN (%s)" % seq, ti)]
    return round((sum(v)/len(v))*J_KWH, 4) if v else ""

peakkw = {}
for tag, (folder, summ) in STUDIES.items():
    runs = os.path.join(BASE, folder, "runs")
    for sp in glob.glob(os.path.join(runs, "**", "instance-out.sql"), recursive=True):
        rel = os.path.relpath(sp, runs).replace("\\","/").split("/")
        cz = int(rel[0][2:]); cp = rel[1].split("&")
        hvac, prog, typ, uc = parse_case(rel[2])
        if not prog: continue
        con = sqlite3.connect(sp); kw = peak_kw(con, "CZ%02d"%cz); con.close()
        peakkw[key(cp[0], cz, cp[1], hvac, prog, typ, uc)] = kw

# ---- weighted getters (SFm blends stories) ----
def lookup(store, bld, cz, hvac, prog, typ, uc, blank):
    rp = "NR" if prog == "NC" else prog
    if bld == "SFm":
        a = store.get(key("SFm",cz,"1",hvac,rp,typ,uc)); b = store.get(key("SFm",cz,"2",hvac,rp,typ,uc))
        if a is None or b is None: return None
        ns = NUMSTOR[cz]; w1, w2 = 2-ns, ns-1
        if isinstance(a, dict): return {k: a[k]*w1 + b[k]*w2 for k in a}
        if a == "" or b == "": return blank
        return round(a*w1 + b*w2, 4)
    return store.get(key(bld,cz,"0",hvac,rp,typ,uc), blank if bld!="SFm" else None)

def fill(infile, cols, mode):
    rows = list(csv.reader(open(os.path.join(DL, infile))))
    hdr = rows[0]; out = [hdr]; miss = 0
    for r in rows[1:]:
        if not r or not r[0]: continue
        tid, bld, cz = r[0], r[2], int(r[3][2:])
        hvac, prog, typ, uc = parse_techid(tid)
        r = r[:4] + [""]*(len(hdr)-4)
        if mode == "kwh":
            e = lookup(enduse, bld, cz, hvac, prog, typ, uc, None)
            if e: r[4],r[5],r[6] = round(e["Heating Elec (kWh)"],4),round(e["Cooling Elec (kWh)"],4),round(e["Fans (kWh)"],4)
            else: miss += 1
        elif mode == "therm":
            e = lookup(enduse, bld, cz, hvac, prog, typ, uc, None)
            if e: r[4],r[5],r[6] = round(e["Heating NG (kWh)"]/KWH_PER_THERM,4),round(e["Cooling NG (kWh)"]/KWH_PER_THERM,4),0.0
            else: miss += 1
        elif mode == "kw":   # base TechID row -> base kW + paired measure kW
            r[4] = lookup(peakkw, bld, cz, hvac, prog, "base", uc, "")
            r[5] = lookup(peakkw, bld, cz, hvac, prog, "measure", None, "")
            if r[4]=="" or r[5]=="": miss += 1
        out.append(r)
    with open(os.path.join(OUT, infile), "w", newline="") as f:
        csv.writer(f).writerows(out)
    print(f"{infile}: {len(out)-1} rows, {miss} missing")

fill("UEC_kWhBase.csv",  3, "kwh")
fill("UEC_kWhMeas.csv",  3, "kwh")
fill("UEC_ThermBase.csv",3, "therm")
fill("UEC_ThermMeas.csv",3, "therm")
fill("UEC_kWBaseMeas.csv",2,"kw")
