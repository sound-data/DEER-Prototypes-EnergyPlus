"""
Audit the filled UEC kWh files: for every base/measure row, show which run the
value was pulled from and whether it matches the results-summary cell. Lets a
human confirm the base/measure pairing is NOT scrambled (base TechID -> a *Base*
run, measure TechID -> a *Measure* run) and that every value traces to a real run.

Writes audit_uec_kwh.csv and prints match/mismatch counts.
"""
import csv, os, re, sys

BASE = sys.argv[1]
OUT  = sys.argv[2]
ECOLS = ["Heating Elec (kWh)","Cooling Elec (kWh)","Fans (kWh)"]
NUMSTOR = {1:1.48,2:1.48,3:1.48,4:1.48,5:1.48,6:1.55,7:1.55,8:1.55,9:1.33,
           10:1.42,11:1.23,12:1.23,13:1.23,14:1.12,15:1.12,16:1.31}
STUDIES = {"Dmo":("SWSV014-02 LRM AC HP _Dmo_Ex","results-summary-Dmo.csv"),
           "Mfm":("SWSV014-02 LRM AC HP_MFm_Ex","results-summary-Mfm.csv"),
           "S75":("SWSV014-02 LRM AC HP_SFm_1975","results-summary-Sfm-1975.csv"),
           "S85":("SWSV014-02 LRM AC HP_SFm_1985","results-summary-Sfm-1985.csv")}

def parse_case(c):
    hvac="rDXHP" if "rDXHP" in c else "rDXGF"; typ="measure" if "Measure" in c else "base"
    prog="AOE" if "AOE" in c else ("NR" if "NR" in c else None)
    m=re.search(r"\+(\d+\.?\d*)% RCA",c); return hvac,prog,typ,(float(m.group(1)) if m else 0.0)

def parse_tid(t):
    hvac="rDXHP" if "rDXHP" in t else "rDXGF"; typ="measure" if "LRM-LSC" in t else "base"
    prog="AOE" if "AOE" in t else ("NC" if t.rstrip().endswith("NC") else "NR")
    m=re.search(r"NoLRM-(\d+\.?\d*)% UC",t); return hvac,prog,typ,(float(m.group(1)) if m else 0.0)

def k(b,cz,s,h,p,t,u): return (b,cz,s,h,p,t,u if t=="base" else None)

# build lookup: key -> (values dict, run-name)
look={}
for folder,summ in STUDIES.values():
    rows=list(csv.reader(open(os.path.join(BASE,folder,summ))))
    hi=next(i for i,r in enumerate(rows) if r and r[0]=="File Name" and "Cooling Elec (kWh)" in r)
    idx={c:rows[hi].index(c) for c in ECOLS}
    for r in rows[hi+1:]:
        if not r or "/" not in r[0]: continue
        pa=r[0].split("/"); cz=int(pa[0][2:]); cp=pa[1].split("&")
        h,p,t,u=parse_case(pa[2])
        if not p: continue
        try: look[k(cp[0],cz,cp[1],h,p,t,u)]=({c:float(r[idx[c]]) for c in ECOLS}, pa[2])
        except: pass

def expect(bld,cz,h,p,t,u):
    rp="NR" if p=="NC" else p
    if bld=="SFm":
        a=look.get(k("SFm",cz,"1",h,rp,t,u)); b=look.get(k("SFm",cz,"2",h,rp,t,u))
        if not a or not b: return None,None
        ns=NUMSTOR[cz]; w1,w2=2-ns,ns-1
        v={c:round(a[0][c]*w1+b[0][c]*w2,4) for c in ECOLS}
        return v, "WEIGHTED: %s | %s"%(a[1],b[1])
    r=look.get(k(bld,cz,"0",h,rp,t,u))
    return (None,None) if not r else ({c:round(r[0][c],4) for c in ECOLS}, r[1])

audit=[["File","Bldg","CZ","TechID","MappedRun","srcHeat","srcCool","srcFan","fileHeat","fileCool","fileFan","MATCH"]]
ok=bad=0
for fn in ["UEC_kWhBase.csv","UEC_kWhMeas.csv"]:
    for r in list(csv.reader(open(os.path.join(OUT,fn))))[1:]:
        if not r or not r[0]: continue
        tid,bld,cz=r[0],r[2],int(r[3][2:]); h,p,t,u=parse_tid(tid)
        ev,run=expect(bld,cz,h,p,t,u)
        fh,fc,ff=[float(x) for x in r[4:7]]
        if ev is None:
            audit.append([fn,bld,cz,tid,"NO RUN MATCH","","","",fh,fc,ff,"MISSING"]); bad+=1; continue
        sh,sc,sf=ev["Heating Elec (kWh)"],ev["Cooling Elec (kWh)"],ev["Fans (kWh)"]
        m = abs(sh-fh)<0.01 and abs(sc-fc)<0.01 and abs(sf-ff)<0.01
        audit.append([fn,bld,cz,tid,run,sh,sc,sf,fh,fc,ff,"Y" if m else "DIFF"])
        ok+=m; bad+=(not m)
with open(os.path.join(OUT,"audit_uec_kwh.csv"),"w",newline="") as f:
    csv.writer(f).writerows(audit)
print(f"audit rows: {len(audit)-1}, MATCH: {ok}, problems: {bad}")
print("wrote", os.path.join(OUT,"audit_uec_kwh.csv"))
