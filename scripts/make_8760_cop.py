"""
COP-method 8760: base = old measure run hourly; measure = base minus the hourly
cooling (and HP heating) reduction. The hourly cooling/heating component is
extracted from the existing multi-COP runs by least squares:
  facility_hr = cool_const_hr/cool_COP (+ heat_const_hr/heat_COP for HP) + rest_hr
then measure_hr = base_hr - cool@base_hr*cf/(1+cf) - heat@base_hr*hf/(1+hf).
No re-sim. Outputs base/measure 8760 per building + audit.
"""
import csv, os, re, glob, sys
import numpy as np

BASE=sys.argv[1]; PAIRS=sys.argv[2]; OUT=sys.argv[3]
import openpyxl
COOLFRAC={0.0:0.0945,7.5:0.2283,15.0:0.3621,22.5:0.4959,30.0:0.6297,40.0:0.8081}
HEATFRAC={0.0:0.0394,7.5:0.0951,15.0:0.1508,22.5:0.2066,30.0:0.2623,40.0:0.3366}
# AOE base/measure cooling & heating COPs by UC label
COOLCOP={"meas":3.23,0.0:2.925,7.5:2.493,15.0:2.060,22.5:1.628,30.0:1.196,40.0:0.620}
HEATCOP={"meas":2.05,0.0:1.969,7.5:1.855,15.0:1.741,22.5:1.627,30.0:1.512,40.0:1.360}
NUMSTOR={1:1.48,2:1.48,3:1.48,4:1.48,5:1.48,6:1.55,7:1.55,8:1.55,9:1.33,10:1.42,11:1.23,12:1.23,13:1.23,14:1.12,15:1.12,16:1.31}
STUDIES=["SWSV014-02 LRM AC HP _Dmo_Ex","SWSV014-02 LRM AC HP_MFm_Ex","SWSV014-02 LRM AC HP_SFm_1975","SWSV014-02 LRM AC HP_SFm_1985"]
def ptid(bt,mt=""):
    h="rDXHP" if "rDXHP" in bt else "rDXGF"; tl=bt.rstrip()
    p="AOE" if tl.endswith("AOE") else ("NC" if tl.endswith("NC") else "NR")
    m=re.search(r"Correct-(\d+\.?\d*)%\s*UC",mt) or re.search(r"NoLRM-(\d+\.?\d*)%\s*UC",bt)
    return h,p,(float(m.group(1)) if m else 0.0)
def uclabel(case):
    m=re.search(r"\+(\d+\.?\d*)% RCA",case);
    return float(m.group(1)) if m else (0.0 if "LSC" in case else "meas")
# load 8760 series keyed (bldg,cz,story,hvac,prog,kind) kind=uc-label or 'meas'
series={}
for folder in STUDIES:
    for fp in glob.glob(os.path.join(BASE,folder,"8760_kW","*.csv")):
        name=os.path.basename(fp)[:-4]; parts=name.split("__"); cz=int(parts[0][2:]); cp=parts[1].split("&"); case=parts[2]
        hv="rDXHP" if "rDXHP" in case else "rDXGF"; prog="AOE" if "AOE" in case else ("NR" if "NR" in case else None)
        if not prog: continue
        kind="meas" if "Measure" in case else uclabel(case)
        v=[float(r[1]) for r in list(csv.reader(open(fp)))[1:] if len(r)>1 and r[1] not in ("","kW")]
        if len(v)>=8760: series[(cp[0],cz,cp[1],hv,prog,kind)]=np.array(v[-8760:])
def get(bld,cz,hvac,prog,kind):
    rp="NR" if prog=="NC" else prog
    if bld=="SFm":
        a=series.get(("SFm",cz,"1",hvac,rp,kind)); b=series.get(("SFm",cz,"2",hvac,rp,kind))
        if a is None or b is None: return None
        ns=NUMSTOR[cz]; return a*(2-ns)+b*(ns-1)
    return series.get((bld,cz,"0",hvac,rp,kind))
def components(bld,cz,hvac):
    # extract cool@base (and heat@base) hourly from AOE multi-COP runs
    ucs=[0.0,7.5,15.0,22.5,30.0,40.0]
    runs=[("meas",get(bld,cz,hvac,"AOE","meas"))]+[(u,get(bld,cz,hvac,"AOE",u)) for u in ucs]
    runs=[(k,v) for k,v in runs if v is not None]
    if len(runs)<3: return None
    Y=np.array([v for _,v in runs])            # (n,8760)
    if hvac=="rDXHP":
        X=np.array([[1/COOLCOP[k],1/HEATCOP[k],1.0] for k,_ in runs])
        coef,_,_,_=np.linalg.lstsq(X,Y,rcond=None)      # (3,8760)
        cool_at=coef[0]/3.23; heat_at=coef[1]/2.05
    else:
        X=np.array([[1/COOLCOP[k],1.0] for k,_ in runs])
        coef,_,_,_=np.linalg.lstsq(X,Y,rcond=None)
        cool_at=coef[0]/3.23; heat_at=np.zeros(8760)
    return cool_at,heat_at
ws=openpyxl.load_workbook(PAIRS,data_only=True).active
pairs=[(r[0],r[1]) for r in ws.iter_rows(values_only=True) if r[0] and "TechID" not in str(r[0])]
HDR=["Base TechID","Measure TechID","System Type","Building Type","Building Location"]+["h%d"%i for i in range(1,8761)]
for b in ["DMo","MFm","SFm"]: os.makedirs(os.path.join(OUT,b),exist_ok=True)
audit=[["Bldg","CZ","Base TechID","Measure TechID","min(base-meas) kW","base>=meas all hrs"]]
comp_cache={}; tot=0; miss=0; viol=0
for bld in ["DMo","MFm","SFm"]:
    bo=[HDR[:]]; mo=[HDR[:]]
    for bt,mt in pairs:
        h,prog,uc=ptid(bt,mt); cf=COOLFRAC[uc]; hf=HEATFRAC[uc]
        for cz in range(1,17):
            tot+=1
            base=get(bld,cz,h,prog,"meas")     # base = corrected unit = old measure run
            ck=comp_cache.get((bld,cz,h))
            if ck is None and (bld,cz,h) not in comp_cache: ck=components(bld,cz,h); comp_cache[(bld,cz,h)]=ck
            if base is None or ck is None: miss+=1; continue
            cool_at,heat_at=ck
            # NR/NC base uses NR cooling base scale (COP 3.58); reuse load via 3.23/3.58 ratio
            scale = 1.0 if prog=="AOE" else (3.23/3.58)
            measure=base - (cool_at*scale)*cf/(1+cf) - (heat_at*scale)*hf/(1+hf)
            czs="CZ%02d"%cz
            bo.append([bt,mt,h,bld,czs]+["%.4f"%x for x in base])
            mo.append([bt,mt,h,bld,czs]+["%.4f"%x for x in measure])
            mn=float((base-measure).min()); audit.append([bld,czs,bt,mt,round(mn,5),"Y" if mn>=-1e-6 else "NO"]); viol+=(mn<-1e-6)
    with open(os.path.join(OUT,bld,f"8760kW_COP_Base_{bld}.csv"),"w",newline="") as f: csv.writer(f).writerows(bo)
    with open(os.path.join(OUT,bld,f"8760kW_COP_Meas_{bld}.csv"),"w",newline="") as f: csv.writer(f).writerows(mo)
    print(f"  {bld}: {len(bo)-1} rows")
with open(os.path.join(OUT,"audit_8760_cop.csv"),"w",newline="") as f: csv.writer(f).writerows(audit)
print(f"\ntotal {tot}  missing {miss}  base<measure-any-hour pairs {viol}")
