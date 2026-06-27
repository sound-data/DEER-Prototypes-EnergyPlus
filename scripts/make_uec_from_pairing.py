"""
Generate the UEC deliverable FROM Robert's corrected pairing (29 base/measure
pairs) x 16 CZ x 3 buildings = 1392 permutations (464/building), instead of
filling Pete's old 1344-row template. Values come from the same verified run
mapping (end uses from results summary, peak kW from SQL; NC shares NR runs,
R32/R454b share the same rDXHP run, SFm story-weighted).

Outputs per building: UEC_kWhBase/Meas, UEC_ThermBase/Meas, UEC_kWBaseMeas.
"""
import csv, os, re, glob, sqlite3, datetime, sys, openpyxl

BASE=sys.argv[1]; PAIRS=sys.argv[2]; OUT=sys.argv[3]
KWH_PER_THERM=29.3001; J_KWH=2.77778e-7
PEAKSPEC={"CZ01":238,"CZ02":238,"CZ03":238,"CZ04":238,"CZ05":259,"CZ06":245,"CZ07":245,
          "CZ08":245,"CZ09":244,"CZ10":180,"CZ11":180,"CZ12":180,"CZ13":180,"CZ14":180,"CZ15":180,"CZ16":224}
NUMSTOR={1:1.48,2:1.48,3:1.48,4:1.48,5:1.48,6:1.55,7:1.55,8:1.55,9:1.33,10:1.42,11:1.23,12:1.23,13:1.23,14:1.12,15:1.12,16:1.31}
STUDIES={"Dmo":("SWSV014-02 LRM AC HP _Dmo_Ex","results-summary-Dmo.csv"),
         "Mfm":("SWSV014-02 LRM AC HP_MFm_Ex","results-summary-Mfm.csv"),
         "S75":("SWSV014-02 LRM AC HP_SFm_1975","results-summary-Sfm-1975.csv"),
         "S85":("SWSV014-02 LRM AC HP_SFm_1985","results-summary-Sfm-1985.csv")}
ECOLS=["Heating Elec (kWh)","Cooling Elec (kWh)","Fans (kWh)","Heating NG (kWh)","Cooling NG (kWh)"]

def parse_case(c):
    hvac="rDXHP" if "rDXHP" in c else "rDXGF"; typ="measure" if "Measure" in c else "base"
    prog="AOE" if "AOE" in c else ("NR" if "NR" in c else None)
    m=re.search(r"\+(\d+\.?\d*)% RCA",c); return hvac,prog,typ,(float(m.group(1)) if m else 0.0)

def parse_tid(t):
    hvac="rDXHP" if "rDXHP" in t else "rDXGF"; typ="measure" if "LRM-LSC" in t else "base"
    tl=t.rstrip(); prog="AOE" if tl.endswith("AOE") else ("NC" if tl.endswith("NC") else "NR")
    m=re.search(r"NoLRM-(\d+\.?\d*)%\s*UC",t); return hvac,prog,typ,(float(m.group(1)) if m else 0.0)

def key(b,cz,s,h,p,t,u): return (b,cz,s,h,p,t,u if t=="base" else None)

# end-use lookup
enduse={}
for folder,summ in STUDIES.values():
    rows=list(csv.reader(open(os.path.join(BASE,folder,summ))))
    hi=next(i for i,r in enumerate(rows) if r and r[0]=="File Name" and "Cooling Elec (kWh)" in r)
    idx={c:rows[hi].index(c) for c in ECOLS}
    for r in rows[hi+1:]:
        if not r or "/" not in r[0]: continue
        p=r[0].split("/"); cz=int(p[0][2:]); cp=p[1].split("&"); h,pr,t,u=parse_case(p[2])
        if not pr: continue
        try: enduse[key(cp[0],cz,cp[1],h,pr,t,u)]={c:float(r[idx[c]]) for c in ECOLS}
        except: pass

def peak_kw(con,cz):
    st=datetime.datetime.strptime("2017-%d"%PEAKSPEC[cz],"%Y-%j").date(); days=[st+datetime.timedelta(days=x) for x in range(3)]
    q=("SELECT t.TimeIndex FROM Time t JOIN EnvironmentPeriods e ON t.EnvironmentPeriodIndex=e.EnvironmentPeriodIndex "
       "WHERE e.EnvironmentType=3 AND ((t.Month=? AND t.Day=? AND t.Hour BETWEEN 16 AND 20) OR (t.Month=? AND t.Day=? AND t.Hour BETWEEN 16 AND 20) OR (t.Month=? AND t.Day=? AND t.Hour BETWEEN 16 AND 20))")
    pr=[]
    for d in days: pr+=[d.month,d.day]
    ti=[x[0] for x in con.execute(q,pr)]
    if not ti: return ""
    seq=",".join("?"*len(ti))
    v=[x[0] for x in con.execute("SELECT rd.Value FROM ReportData rd JOIN ReportDataDictionary d ON rd.ReportDataDictionaryIndex=d.ReportDataDictionaryIndex WHERE d.Name='Electricity:Facility' AND d.ReportingFrequency='Hourly' AND rd.TimeIndex IN (%s)"%seq,ti)]
    return round((sum(v)/len(v))*J_KWH,4) if v else ""

peakkw={}
for folder,summ in STUDIES.values():
    for sp in glob.glob(os.path.join(BASE,folder,"runs","**","instance-out.sql"),recursive=True):
        rel=os.path.relpath(sp,os.path.join(BASE,folder,"runs")).replace("\\","/").split("/")
        cz=int(rel[0][2:]); cp=rel[1].split("&"); h,pr,t,u=parse_case(rel[2])
        if not pr: continue
        con=sqlite3.connect(sp); kw=peak_kw(con,"CZ%02d"%cz); con.close()
        peakkw[key(cp[0],cz,cp[1],h,pr,t,u)]=kw

def get(store,bld,cz,hvac,prog,typ,uc):
    rp="NR" if prog=="NC" else prog
    if bld=="SFm":
        a=store.get(key("SFm",cz,"1",hvac,rp,typ,uc)); b=store.get(key("SFm",cz,"2",hvac,rp,typ,uc))
        if a is None or b is None: return None
        ns=NUMSTOR[cz]; w1,w2=2-ns,ns-1
        return {c:a[c]*w1+b[c]*w2 for c in a} if isinstance(a,dict) else (a*w1+b*w2)
    return store.get(key(bld,cz,"0",hvac,rp,typ,uc))

ws=openpyxl.load_workbook(PAIRS,data_only=True).active
pairs=[(r[0],r[1]) for r in ws.iter_rows(values_only=True) if r[0] and "TechID" not in str(r[0])]
print(f"pairs read: {len(pairs)}")

H_KWH=lambda s:["TechID","System Type","Building Type","Building Location",f"UEC_kWh{s}__heat",f"UEC_kWh{s}__cool",f"UEC_kWh{s}__ventFan"]
H_THM=lambda s:["TechID","System Type","Building Type","Building Location",f"UEC_Therm{s}__heat",f"UEC_Therm{s}__cool",f"UEC_Therm{s}__ventFan"]
H_KW=["TechID","System Type","Building Type","Building Location","UEC_YrkW__base","UEC_YrkW__meas"]
for b in ["DMo","MFm","SFm"]: os.makedirs(os.path.join(OUT,b),exist_ok=True)
miss=0; kwh_bad=0; kw_bad=0; total=0
for bld in ["DMo","MFm","SFm"]:
    out={ "kwhB":[H_KWH("Base")],"kwhM":[H_KWH("Meas")],"thmB":[H_THM("Base")],"thmM":[H_THM("Meas")],"kw":[H_KW] }
    for bt,mt in pairs:
        hb,pb,_,ub=parse_tid(bt); hm,pm,_,um=parse_tid(mt)
        for cz in range(1,17):
            czs="CZ%02d"%cz; total+=1
            eb=get(enduse,bld,cz,hb,pb,"base",ub); em=get(enduse,bld,cz,hm,pm,"measure",None)
            kb=get(peakkw,bld,cz,hb,pb,"base",ub); km=get(peakkw,bld,cz,hm,pm,"measure",None)
            if eb is None or em is None or kb is None or km is None: miss+=1; continue
            out["kwhB"].append([bt,hb,bld,czs,round(eb["Heating Elec (kWh)"],4),round(eb["Cooling Elec (kWh)"],4),round(eb["Fans (kWh)"],4)])
            out["kwhM"].append([mt,hm,bld,czs,round(em["Heating Elec (kWh)"],4),round(em["Cooling Elec (kWh)"],4),round(em["Fans (kWh)"],4)])
            out["thmB"].append([bt,hb,bld,czs,round(eb["Heating NG (kWh)"]/KWH_PER_THERM,4),round(eb["Cooling NG (kWh)"]/KWH_PER_THERM,4),0.0])
            out["thmM"].append([mt,hm,bld,czs,round(em["Heating NG (kWh)"]/KWH_PER_THERM,4),round(em["Cooling NG (kWh)"]/KWH_PER_THERM,4),0.0])
            out["kw"].append([bt,hb,bld,czs,kb,km])
            if not (sum(eb[c] for c in ECOLS[:3]) >= sum(em[c] for c in ECOLS[:3])-1e-6): kwh_bad+=1
            if kb!="" and km!="" and kb<km-1e-6: kw_bad+=1
    names={"kwhB":"UEC_kWhBase","kwhM":"UEC_kWhMeas","thmB":"UEC_ThermBase","thmM":"UEC_ThermMeas","kw":"UEC_kWBaseMeas"}
    for k,rows in out.items():
        with open(os.path.join(OUT,bld,f"{names[k]}_{bld}.csv"),"w",newline="") as f: csv.writer(f).writerows(rows)
    print(f"  {bld}: {len(out['kwhB'])-1} rows per file")
print(f"\ntotal permutations: {total}  (missing source: {miss})")
print(f"Base>=Measure kWh failures: {kwh_bad}   peak kW base<measure (negatives): {kw_bad}")
