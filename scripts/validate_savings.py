"""
Validate simulated LRM savings fractions against Robert's regression fractions,
across every CZ / undercharge level / HVAC / building, separately for cooling
and (for HP) heating.

For each AOE +X% RCA base run, savings fraction = (base_enduse - measure_enduse)
/ base_enduse, where measure = the AOE corrected run for the same CZ/cohort.
"""
import csv, os, re, sys
from statistics import mean

BASE = sys.argv[1]
STUDIES = {
    "DMo":   "SWSV014-02 LRM AC HP _Dmo_Ex/results-summary-Dmo.csv",
    "MFm":   "SWSV014-02 LRM AC HP_MFm_Ex/results-summary-Mfm.csv",
    "SFm75": "SWSV014-02 LRM AC HP_SFm_1975/results-summary-Sfm-1975.csv",
    "SFm85": "SWSV014-02 LRM AC HP_SFm_1985/results-summary-Sfm-1985.csv",
}
EXP_COOL = {"+7.5%":0.2283,"+15%":0.3621,"+22.5%":0.4959,"+30%":0.6297,"+40%":0.8081}
EXP_HEAT = {"+7.5%":0.0951,"+15%":0.1508,"+22.5%":0.2066,"+30%":0.2623,"+40%":0.3366}

def load(path):
    rows = list(csv.reader(open(path)))
    hi = next(i for i,r in enumerate(rows) if r and r[0]=="File Name" and "Cooling Elec (kWh)" in r)
    h = rows[hi]; ci = h.index("Cooling Elec (kWh)"); hci = h.index("Heating Elec (kWh)")
    d = {}
    for r in rows[hi+1:]:
        if not r or r[0]=="File Name" or not r[0].strip(): continue
        try: d[r[0].strip()] = (float(r[ci]), float(r[hci]))
        except (ValueError, IndexError): pass
    return d

res = {}   # (hvac, uc, kind) -> list of sim fractions
for name, rel in STUDIES.items():
    p = os.path.join(BASE, rel)
    if not os.path.exists(p):
        print("missing:", p); continue
    d = load(p)
    runs = {}
    for fn,(c,h) in d.items():
        parts = fn.split("/")
        if len(parts) < 3: continue
        runs.setdefault((parts[0], parts[1]), {})[parts[2]] = (c, h)
    for (cz, cohort), cases in runs.items():
        hvac = "rDXHP" if "rDXHP" in cohort else "rDXGF"
        meas = next((v for k,v in cases.items() if "AOE" in k and "Measure" in k), None)
        if not meas: continue
        mc, mh = meas
        for case,(bc,bh) in cases.items():
            if "Base" not in case or "AOE" not in case: continue
            m = re.search(r"\+(\d+\.?\d*)% RCA", case)
            if not m: continue
            uc = "+"+m.group(1)+"%"
            if uc not in EXP_COOL: continue
            if bc: res.setdefault((hvac,uc,"cool"),[]).append((bc-mc)/bc)
            if hvac=="rDXHP" and bh: res.setdefault((hvac,uc,"heat"),[]).append((bh-mh)/bh)

def report(hvac, kind, exp):
    print(f"\n=== {hvac} {kind.upper()} savings fraction (sim vs expected) ===")
    print(f"{'UC':>7} {'expected':>9} {'sim avg':>9} {'min':>8} {'max':>8} {'n':>4} {'avg-exp':>9}")
    for uc in EXP_COOL:
        v = res.get((hvac,uc,kind))
        if not v: continue
        e = exp[uc]
        print(f"{uc:>7} {e:>9.4f} {mean(v):>9.4f} {min(v):>8.4f} {max(v):>8.4f} {len(v):>4} {mean(v)-e:>+9.4f}")

report("rDXGF","cool",EXP_COOL)
report("rDXHP","cool",EXP_COOL)
report("rDXHP","heat",EXP_HEAT)
