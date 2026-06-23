"""
Full COP-method UEC: kWh end-use + therms + peak kW, base/measure, with TechIDs.
NEW base = corrected unit (old measure run, COP 3.23/3.58). NEW measure = COP
improved -> cooling/(1+coolfrac), HP heating/(1+heatfrac), fan & gas unchanged.
Peak kW: extract the cooling-at-peak component from the existing multi-COP runs
(facility = cool_const/COP + noncool) and scale -- no re-sim.
"""
import csv, os, re, sys, openpyxl

BASE=sys.argv[1]; PAIRS=sys.argv[2]; OLDKW=sys.argv[3]; OUT=sys.argv[4]
KWH_PER_THERM=29.3001
COOLFRAC={0.0:0.0945,7.5:0.2283,15.0:0.3621,22.5:0.4959,30.0:0.6297,40.0:0.8081}
HEATFRAC={0.0:0.0394,7.5:0.0951,15.0:0.1508,22.5:0.2066,30.0:0.2623,40.0:0.3366}
COP_BASE={"AOE":3.23,"NR":3.58,"NC":3.58}; COP_40=0.62   # derated 40% cooling COP (for cool_const extraction)
NUMSTOR={1:1.48,2:1.48,3:1.48,4:1.48,5:1.48,6:1.55,7:1.55,8:1.55,9:1.33,10:1.42,11:1.23,12:1.23,13:1.23,14:1.12,15:1.12,16:1.31}
STUDIES={"Dmo":("SWSV014-02 LRM AC HP _Dmo_Ex","results-summary-Dmo.csv"),"Mfm":("SWSV014-02 LRM AC HP_MFm_Ex","results-summary-Mfm.csv"),
         "S75":("SWSV014-02 LRM AC HP_SFm_1975","results-summary-Sfm-1975.csv"),"S85":("SWSV014-02 LRM AC HP_SFm_1985","results-summary-Sfm-1985.csv")}
EC=["Heating Elec (kWh)","Cooling Elec (kWh)","Fans (kWh)","Heating NG (kWh)","Cooling NG (kWh)"]
def pcase(c):
    h="rDXHP" if "rDXHP" in c else "rDXGF"; t="measure" if "Measure" in c else "base"
    p="AOE" if "AOE" in c else ("NR" if "NR" in c else None); return h,p,t
def ptid(bt,mt=""):
    h="rDXHP" if "rDXHP" in bt else "rDXGF"; tl=bt.rstrip()
    p="AOE" if tl.endswith("AOE") else ("NC" if tl.endswith("NC") else "NR")
    # UC level lives on the MEASURE TechID now (LRM-LSC-Correct-X%UC); fall back to base
    m=re.search(r"Correct-(\d+\.?\d*)%\s*UC",mt) or re.search(r"NoLRM-(\d+\.?\d*)%\s*UC",bt)
    return h,p,(float(m.group(1)) if m else 0.0)
def Km(b,cz,s,h,p): return (b,cz,s,h,p)
# old MEASURE end uses
meas={}
for folder,summ in STUDIES.values():
    rows=list(csv.reader(open(os.path.join(BASE,folder,summ))))
    hi=next(i for i,r in enumerate(rows) if r and r[0]=="File Name" and "Cooling Elec (kWh)" in r)
    idx={c:rows[hi].index(c) for c in EC}
    for r in rows[hi+1:]:
        if not r or "/" not in r[0]: continue
        pa=r[0].split("/"); cz=int(pa[0][2:]); cp=pa[1].split("&"); h,p,t=pcase(pa[2])
        if t!="measure" or not p: continue
        try: meas[Km(cp[0],cz,cp[1],h,p)]={c:float(r[idx[c]]) for c in EC}
        except: pass
def base_eu(bld,cz,hvac,prog):
    rp="NR" if prog=="NC" else prog
    if bld=="SFm":
        a=meas.get(Km("SFm",cz,"1",hvac,rp)); b=meas.get(Km("SFm",cz,"2",hvac,rp))
        if not a or not b: return None
        ns=NUMSTOR[cz]; w1,w2=2-ns,ns-1; return {c:a[c]*w1+b[c]*w2 for c in EC}
    return meas.get(Km(bld,cz,"0",hvac,rp))
# cool_const per (bldg,cz,hvac) from old kWBaseMeas: 40% base peak (COP .62) + measure peak (3.23)
cool_const={}; meas_peak={}
for bld in ["DMo","MFm","SFm"]:
    rows=list(csv.reader(open(os.path.join(OLDKW,bld,f"UEC_kWBaseMeas_{bld}.csv"))))[1:]
    for r in rows:
        h="rDXHP" if "rDXHP" in r[1] else "rDXGF"; cz=int(r[3][2:])
        if "40%UC-AOE" in r[0] and r[4] and r[5]:
            bp=float(r[4]); mp=float(r[5])  # base(0.62), measure(3.23)
            cc=(bp-mp)/(1/COP_40 - 1/3.23)
            cool_const[(bld,cz,h)]=cc; meas_peak[(bld,cz,h)]=mp
ws=openpyxl.load_workbook(PAIRS,data_only=True).active
pairs=[(r[0],r[1]) for r in ws.iter_rows(values_only=True) if r[0] and "TechID" not in str(r[0])]
for b in ["DMo","MFm","SFm"]: os.makedirs(os.path.join(OUT,b),exist_ok=True)
HK=["Base TechID","Measure TechID","System Type","Building Type","Building Location","heat","cool","ventFan"]
HKW=["Base TechID","Measure TechID","System Type","Building Type","Building Location","kW_base","kW_meas"]
tot=0; miss=0; bad=0; kwbad=0
for bld in ["DMo","MFm","SFm"]:
    kb=[HK[:]]; km=[HK[:]]; tb=[HK[:]]; tm=[HK[:]]; kw=[HKW[:]]
    for bt,mt in pairs:
        h,prog,uc=ptid(bt,mt); cf=COOLFRAC[uc]; hf=HEATFRAC[uc]
        for cz in range(1,17):
            tot+=1; e=base_eu(bld,cz,h,prog)
            if e is None: miss+=1; continue
            bh,bc,bf=e["Heating Elec (kWh)"],e["Cooling Elec (kWh)"],e["Fans (kWh)"]
            tbh,tbc=e["Heating NG (kWh)"]/KWH_PER_THERM,e["Cooling NG (kWh)"]/KWH_PER_THERM
            mh=bh/(1+hf) if h=="rDXHP" else bh; mc=bc/(1+cf)
            czs="CZ%02d"%cz
            kb.append([bt,mt,h,bld,czs,round(bh,2),round(bc,2),round(bf,2)])
            km.append([bt,mt,h,bld,czs,round(mh,2),round(mc,2),round(bf,2)])
            tb.append([bt,mt,h,bld,czs,round(tbh,3),round(tbc,3),0.0])
            tm.append([bt,mt,h,bld,czs,round(tbh,3),round(tbc,3),0.0])   # gas unchanged -> base=meas
            if (bh+bc+bf)<(mh+mc+bf)-1e-6: bad+=1
            # peak
            cc=cool_const.get((bld,cz,h)); mp=meas_peak.get((bld,cz,h))
            if cc is not None:
                cool_at_pk=cc/3.23
                base_pk=mp; meas_pk=mp - cool_at_pk*cf/(1+cf)
                kw.append([bt,mt,h,bld,czs,round(base_pk,4),round(meas_pk,4)])
                if meas_pk>base_pk+1e-6: kwbad+=1
            else: kw.append([bt,mt,h,bld,czs,"",""])
    for name,rows in [("UEC_COP_kWhBase",kb),("UEC_COP_kWhMeas",km),("UEC_COP_ThermBase",tb),("UEC_COP_ThermMeas",tm),("UEC_COP_kWBaseMeas",kw)]:
        with open(os.path.join(OUT,bld,f"{name}_{bld}.csv"),"w",newline="") as f: csv.writer(f).writerows(rows)
    print(f"  {bld}: {len(kb)-1} rows")
print(f"\ntotal {tot}  missing {miss}  base<meas kWh fails {bad}  measure>base kW fails {kwbad}")
