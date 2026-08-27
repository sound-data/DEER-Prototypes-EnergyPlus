"""
NEW COP method (no re-sim -- exact 1/COP scaling, proven cooling_elec*COP=const).
  new BASE   = the old MEASURE run (corrected unit, COP 3.23/3.58) -- end uses as-is
  new MEASURE = COP-improved: cooling / (1+coolfrac), HP heating / (1+heatfrac),
               fan unchanged, gas therms unchanged.
Row structure = Robert's corrected 29-pair file x 16 CZ x 3 buildings (1392).
The base TechID's UC level sets the fraction. SFm story-weighted; NC shares NR.
"""
import csv, os, re, sys, openpyxl

BASE=sys.argv[1]; PAIRS=sys.argv[2]; OUT=sys.argv[3]
KWH_PER_THERM=29.3001
COOLFRAC={0.0:0.0945,7.5:0.2283,15.0:0.3621,22.5:0.4959,30.0:0.6297,40.0:0.8081}
HEATFRAC={0.0:0.0394,7.5:0.0951,15.0:0.1508,22.5:0.2066,30.0:0.2623,40.0:0.3366}
NUMSTOR={1:1.48,2:1.48,3:1.48,4:1.48,5:1.48,6:1.55,7:1.55,8:1.55,9:1.33,10:1.42,11:1.23,12:1.23,13:1.23,14:1.12,15:1.12,16:1.31}
STUDIES={"Dmo":("SWSV014-02 LRM AC HP _Dmo_Ex","results-summary-Dmo.csv"),"Mfm":("SWSV014-02 LRM AC HP_MFm_Ex","results-summary-Mfm.csv"),
         "S75":("SWSV014-02 LRM AC HP_SFm_1975","results-summary-Sfm-1975.csv"),"S85":("SWSV014-02 LRM AC HP_SFm_1985","results-summary-Sfm-1985.csv")}
EC=["Heating Elec (kWh)","Cooling Elec (kWh)","Fans (kWh)","Heating NG (kWh)","Cooling NG (kWh)"]
def pcase(c):
    h="rDXHP" if "rDXHP" in c else "rDXGF"; t="measure" if "Measure" in c else "base"
    p="AOE" if "AOE" in c else ("NR" if "NR" in c else None); return h,p,t
def ptid(t):
    h="rDXHP" if "rDXHP" in t else "rDXGF"; tl=t.rstrip()
    p="AOE" if tl.endswith("AOE") else ("NC" if tl.endswith("NC") else "NR")
    m=re.search(r"NoLRM-(\d+\.?\d*)%\s*UC",t); return h,p,(float(m.group(1)) if m else 0.0)
def K(b,cz,s,h,p): return (b,cz,s,h,p)   # MEASURE run only
# load old MEASURE-run end uses
meas={}
for folder,summ in STUDIES.values():
    rows=list(csv.reader(open(os.path.join(BASE,folder,summ))))
    hi=next(i for i,r in enumerate(rows) if r and r[0]=="File Name" and "Cooling Elec (kWh)" in r)
    idx={c:rows[hi].index(c) for c in EC}
    for r in rows[hi+1:]:
        if not r or "/" not in r[0]: continue
        pa=r[0].split("/"); cz=int(pa[0][2:]); cp=pa[1].split("&"); h,p,t=pcase(pa[2])
        if t!="measure" or not p: continue
        try: meas[K(cp[0],cz,cp[1],h,p)]={c:float(r[idx[c]]) for c in EC}
        except: pass
def base_enduse(bld,cz,hvac,prog):
    rp="NR" if prog=="NC" else prog
    if bld=="SFm":
        a=meas.get(K("SFm",cz,"1",hvac,rp)); b=meas.get(K("SFm",cz,"2",hvac,rp))
        if not a or not b: return None
        ns=NUMSTOR[cz]; w1,w2=2-ns,ns-1; return {c:a[c]*w1+b[c]*w2 for c in EC}
    return meas.get(K(bld,cz,"0",hvac,rp))

ws=openpyxl.load_workbook(PAIRS,data_only=True).active
pairs=[(r[0],r[1]) for r in ws.iter_rows(values_only=True) if r[0] and "TechID" not in str(r[0])]
for b in ["DMo","MFm","SFm"]: os.makedirs(os.path.join(OUT,b),exist_ok=True)
HB=["Base TechID","Measure TechID","System Type","Building Type","Building Location","heat","cool","ventFan"]
tot=0; bad=0; miss=0
for bld in ["DMo","MFm","SFm"]:
    base_rows=[HB[:]]; meas_rows=[HB[:]]; chk=[]
    for bt,mt in pairs:
        h,prog,uc=ptid(bt); cf=COOLFRAC[uc]; hf=HEATFRAC[uc]
        for cz in range(1,17):
            tot+=1; e=base_enduse(bld,cz,h,prog)
            if e is None: miss+=1; continue
            bh,bc,bf=e["Heating Elec (kWh)"],e["Cooling Elec (kWh)"],e["Fans (kWh)"]
            mh=bh/(1+hf) if h=="rDXHP" else bh   # HP heating scales; furnace elec heat ~0
            mc=bc/(1+cf)
            czs="CZ%02d"%cz
            base_rows.append([bt,mt,h,bld,czs,round(bh,2),round(bc,2),round(bf,2)])
            meas_rows.append([bt,mt,h,bld,czs,round(mh,2),round(mc,2),round(bf,2)])
            # base total >= measure total?
            if (bh+bc+bf) < (mh+mc+bf)-1e-6: bad+=1
    with open(os.path.join(OUT,bld,f"UEC_COP_Base_{bld}.csv"),"w",newline="") as f: csv.writer(f).writerows(base_rows)
    with open(os.path.join(OUT,bld,f"UEC_COP_Meas_{bld}.csv"),"w",newline="") as f: csv.writer(f).writerows(meas_rows)
    print(f"  {bld}: {len(base_rows)-1} rows")
print(f"\ntotal: {tot}  missing: {miss}  base<measure failures: {bad}")
# sample: DMo CZ06 rDXGF, show old(40% derate) savings vs new(COP) savings
print("\n=== DMo CZ06 rDXGF cooling: NEW method savings by UC level (realistic) ===")
e=base_enduse("DMo",6,"rDXGF","AOE")
for uc in [7.5,15,22.5,30,40]:
    cf=COOLFRAC[uc]; bc=e["Cooling Elec (kWh)"]; mc=bc/(1+cf)
    print(f"  {uc:>5}% UC: base(cool)={bc:.0f}  measure(cool)={mc:.0f}  savings={bc-mc:.0f} kWh  ({cf/(1+cf)*100:.0f}% of cooling)")
