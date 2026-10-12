"""
Generate base/measure 8760 hourly kW FROM Robert's corrected pairing
(29 pairs x 16 CZ x 3 buildings = 1392, 464/building), mirroring the UEC.
Source = per-run 8760_kW extracts (absolute kW). NC shares NR runs, R32/R454b
share the same rDXHP run, SFm = two stories weighted by numstor. Checks
base >= measure hour by hour. Outputs per-building base + measure files + audit.
"""
import csv, os, re, glob, sys, openpyxl

BASE=sys.argv[1]; PAIRS=sys.argv[2]; OUT=sys.argv[3]
NUMSTOR={1:1.48,2:1.48,3:1.48,4:1.48,5:1.48,6:1.55,7:1.55,8:1.55,9:1.33,10:1.42,11:1.23,12:1.23,13:1.23,14:1.12,15:1.12,16:1.31}
STUDIES=["SWSV014-02 LRM AC HP _Dmo_Ex","SWSV014-02 LRM AC HP_MFm_Ex","SWSV014-02 LRM AC HP_SFm_1975","SWSV014-02 LRM AC HP_SFm_1985"]
def pcase(c):
    h="rDXHP" if "rDXHP" in c else "rDXGF"; t="measure" if "Measure" in c else "base"
    p="AOE" if "AOE" in c else ("NR" if "NR" in c else None); m=re.search(r"\+(\d+\.?\d*)% RCA",c); return h,p,t,(float(m.group(1)) if m else 0.0)
def ptid(t):
    h="rDXHP" if "rDXHP" in t else "rDXGF"; ty="measure" if "LRM-LSC" in t else "base"
    tl=t.rstrip(); p="AOE" if tl.endswith("AOE") else ("NC" if tl.endswith("NC") else "NR"); m=re.search(r"NoLRM-(\d+\.?\d*)%\s*UC",t); return h,p,ty,(float(m.group(1)) if m else 0.0)
def K(b,cz,s,h,p,t,u): return (b,cz,s,h,p,t,u if t=="base" else None)

series={}
for folder in STUDIES:
    for fp in glob.glob(os.path.join(BASE,folder,"8760_kW","*.csv")):
        name=os.path.basename(fp)[:-4]; parts=name.split("__"); cz=int(parts[0][2:]); cp=parts[1].split("&"); h,p,t,u=pcase(parts[2])
        if not p: continue
        vals=[float(r[1]) for r in list(csv.reader(open(fp)))[1:] if len(r)>1 and r[1] not in ("","kW")]
        if len(vals)>=8760: series[K(cp[0],cz,cp[1],h,p,t,u)]=vals[-8760:]
def get(bld,cz,h,p,t,u):
    rp="NR" if p=="NC" else p
    if bld=="SFm":
        a=series.get(K("SFm",cz,"1",h,rp,t,u)); b=series.get(K("SFm",cz,"2",h,rp,t,u))
        if not a or not b: return None
        ns=NUMSTOR[cz]; w1,w2=2-ns,ns-1; return [a[i]*w1+b[i]*w2 for i in range(8760)]
    return series.get(K(bld,cz,"0",h,rp,t,u))

ws=openpyxl.load_workbook(PAIRS,data_only=True).active
pairs=[(r[0],r[1]) for r in ws.iter_rows(values_only=True) if r[0] and "TechID" not in str(r[0])]
HDR=["TechID","System Type","Building Type","Building Location"]+["h%d"%i for i in range(1,8761)]
for b in ["DMo","MFm","SFm"]: os.makedirs(os.path.join(OUT,b),exist_ok=True)
audit=[["Building Type","Building Location","Base TechID","Measure TechID","min hourly (base-meas) kW","base>=measure all hours"]]
tot=0; miss=0; viol=0
for bld in ["DMo","MFm","SFm"]:
    bo=[HDR[:]]; mo=[HDR[:]]
    for bt,mt in pairs:
        hb,pb,_,ub=ptid(bt); hm,pm,_,um=ptid(mt)
        for cz in range(1,17):
            tot+=1; czs="CZ%02d"%cz
            sb=get(bld,cz,hb,pb,"base",ub); sm=get(bld,cz,hm,pm,"measure",None)
            if sb is None or sm is None: miss+=1; continue
            bo.append([bt,hb,bld,czs]+["%.4f"%v for v in sb])
            mo.append([mt,hm,bld,czs]+["%.4f"%v for v in sm])
            margin=min(sb[i]-sm[i] for i in range(8760)); ok=margin>=-1e-6
            audit.append([bld,czs,bt,mt,round(margin,5),"Y" if ok else "NO"]); viol+=(not ok)
    with open(os.path.join(OUT,bld,f"8760kW_Base_{bld}.csv"),"w",newline="") as f: csv.writer(f).writerows(bo)
    with open(os.path.join(OUT,bld,f"8760kW_Meas_{bld}.csv"),"w",newline="") as f: csv.writer(f).writerows(mo)
    print(f"  {bld}: {len(bo)-1} rows per file")
with open(os.path.join(OUT,"audit_8760_1392.csv"),"w",newline="") as f: csv.writer(f).writerows(audit)
print(f"\ntotal permutations: {tot}  (missing source: {miss})")
print(f"pairs with any hour base<measure: {viol}")
