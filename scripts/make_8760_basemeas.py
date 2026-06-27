"""
Build base/measure 8760 hourly kW with the SAME verified pairing as the UEC,
and check base >= measure hour by hour. Source = per-run 8760_kW extracts
(absolute kW). NC shares NR runs; SFm = the two stories weighted by numstor.

Reads the base/measure TechID + bldg/CZ layout straight from the UEC templates
(row-aligned: base row i pairs with measure row i), so the 8760 mirrors the
UEC exactly. Writes nothing yet -- this proves correctness first.
"""
import csv, os, re, glob, sys

BASE = sys.argv[1]; DL = sys.argv[2]
NUMSTOR = {1:1.48,2:1.48,3:1.48,4:1.48,5:1.48,6:1.55,7:1.55,8:1.55,9:1.33,
           10:1.42,11:1.23,12:1.23,13:1.23,14:1.12,15:1.12,16:1.31}
STUDIES = ["SWSV014-02 LRM AC HP _Dmo_Ex","SWSV014-02 LRM AC HP_MFm_Ex",
           "SWSV014-02 LRM AC HP_SFm_1975","SWSV014-02 LRM AC HP_SFm_1985"]

def parse_case(c):
    hvac="rDXHP" if "rDXHP" in c else "rDXGF"; typ="measure" if "Measure" in c else "base"
    prog="AOE" if "AOE" in c else ("NR" if "NR" in c else None)
    m=re.search(r"\+(\d+\.?\d*)% RCA",c); return hvac,prog,typ,(float(m.group(1)) if m else 0.0)

def parse_tid(t):
    hvac="rDXHP" if "rDXHP" in t else "rDXGF"; typ="measure" if "LRM-LSC" in t else "base"
    prog="AOE" if "AOE" in t else ("NC" if t.rstrip().endswith("NC") else "NR")
    m=re.search(r"NoLRM-(\d+\.?\d*)% UC",t); return hvac,prog,typ,(float(m.group(1)) if m else 0.0)

def k(b,cz,s,h,p,t,u): return (b,cz,s,h,p,t,u if t=="base" else None)

# load 8760 kW arrays keyed by parsed run identity
series={}
for folder in STUDIES:
    for fp in glob.glob(os.path.join(BASE,folder,"8760_kW","*.csv")):
        name=os.path.basename(fp)[:-4]           # CZ01__DMo&0&rDXGF&Ex&..__<case>
        parts=name.split("__"); cz=int(parts[0][2:]); cp=parts[1].split("&"); case=parts[2]
        h,p,t,u=parse_case(case)
        if not p: continue
        rows=list(csv.reader(open(fp)))[1:]
        vals=[float(r[1]) for r in rows if len(r)>1 and r[1] not in ("","kW")]
        if len(vals)>=8760: series[k(cp[0],cz,cp[1],h,p,t,u)]=vals[-8760:]

def get(bld,cz,hvac,prog,typ,uc):
    rp="NR" if prog=="NC" else prog
    if bld=="SFm":
        a=series.get(k("SFm",cz,"1",hvac,rp,typ,uc)); b=series.get(k("SFm",cz,"2",hvac,rp,typ,uc))
        if not a or not b: return None
        ns=NUMSTOR[cz]; w1,w2=2-ns,ns-1
        return [a[i]*w1+b[i]*w2 for i in range(8760)]
    return series.get(k(bld,cz,"0",hvac,rp,typ,uc))

OUT=sys.argv[3]
for b in ["DMo","MFm","SFm"]: os.makedirs(os.path.join(OUT,b),exist_ok=True)
base=list(csv.reader(open(os.path.join(DL,"UEC_kWhBase.csv"))))[1:]
meas=list(csv.reader(open(os.path.join(DL,"UEC_kWhMeas.csv"))))[1:]
HDR=["TechID","System Type","Building Type","Building Location"]+["h%d"%i for i in range(1,8761)]
files={(b,t):[HDR[:]] for b in ["DMo","MFm","SFm"] for t in ["Base","Meas"]}
audit=[["Building Type","Building Location","Base TechID","Measure TechID","min hourly (base-meas) kW","base>=measure all hours"]]
pairs=0; miss=0; viol_pairs=0; viol_hours=0; worst=0.0
for rb,rm in zip(base,meas):
    if not rb or not rm: continue
    bld=rb[2]; cz=int(rb[3][2:])
    hb,pb,tb,ub=parse_tid(rb[0]); hm,pm,tm,um=parse_tid(rm[0])
    sb=get(bld,cz,hb,pb,"base",ub); sm=get(bld,cz,hm,pm,"measure",None)
    if sb is None or sm is None: miss+=1; continue
    pairs+=1
    files[(bld,"Base")].append(rb[:4]+["%.4f"%v for v in sb])
    files[(bld,"Meas")].append(rm[:4]+["%.4f"%v for v in sm])
    margin=min(sb[i]-sm[i] for i in range(8760))
    okall = margin >= -1e-6
    audit.append([bld,rb[3],rb[0],rm[0],round(margin,5),"Y" if okall else "NO"])
    if not okall:
        vh=sum(1 for i in range(8760) if sb[i]<sm[i]-1e-6)
        viol_pairs+=1; viol_hours+=vh
        worst=max(worst, max(sm[i]-sb[i] for i in range(8760) if sb[i]<sm[i]-1e-6))
for (b,t),rows in files.items():
    with open(os.path.join(OUT,b,f"8760kW_{t}_{b}.csv"),"w",newline="") as f:
        csv.writer(f).writerows(rows)
with open(os.path.join(OUT,"audit_8760_basemeas.csv"),"w",newline="") as f:
    csv.writer(f).writerows(audit)
print(f"pairs checked: {pairs}   (missing source: {miss})")
print(f"base >= measure for ALL 8760 hours: {pairs-viol_pairs}/{pairs} pairs")
print(f"pairs with any hour base<measure:   {viol_pairs}  (total such hours: {viol_hours})")
print(f"worst base-below-measure gap: {worst:.5f} kW")
print(f"wrote 6 files + audit to {OUT}")
