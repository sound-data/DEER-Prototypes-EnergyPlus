"""
Independent verification of the regenerated 1392 UEC deliverable.
Re-derives values straight from the results summaries and Robert's pairing file,
then compares to the written per-building files. Checks: counts, pairing,
base>=measure, populated, and a value-traces-to-run audit. Writes audit_1392.csv.
"""
import csv, os, re, sys, openpyxl

BASE=sys.argv[1]; PAIRS=sys.argv[2]; OUT=sys.argv[3]
ECOLS=["Heating Elec (kWh)","Cooling Elec (kWh)","Fans (kWh)"]
NUMSTOR={1:1.48,2:1.48,3:1.48,4:1.48,5:1.48,6:1.55,7:1.55,8:1.55,9:1.33,10:1.42,11:1.23,12:1.23,13:1.23,14:1.12,15:1.12,16:1.31}
STUDIES={"Dmo":("SWSV014-02 LRM AC HP _Dmo_Ex","results-summary-Dmo.csv"),"Mfm":("SWSV014-02 LRM AC HP_MFm_Ex","results-summary-Mfm.csv"),
         "S75":("SWSV014-02 LRM AC HP_SFm_1975","results-summary-Sfm-1975.csv"),"S85":("SWSV014-02 LRM AC HP_SFm_1985","results-summary-Sfm-1985.csv")}
def pcase(c):
    h="rDXHP" if "rDXHP" in c else "rDXGF"; t="measure" if "Measure" in c else "base"
    p="AOE" if "AOE" in c else ("NR" if "NR" in c else None); m=re.search(r"\+(\d+\.?\d*)% RCA",c); return h,p,t,(float(m.group(1)) if m else 0.0)
def ptid(t):
    h="rDXHP" if "rDXHP" in t else "rDXGF"; ty="measure" if "LRM-LSC" in t else "base"
    tl=t.rstrip(); p="AOE" if tl.endswith("AOE") else ("NC" if tl.endswith("NC") else "NR"); m=re.search(r"NoLRM-(\d+\.?\d*)%\s*UC",t); return h,p,ty,(float(m.group(1)) if m else 0.0)
def K(b,cz,s,h,p,t,u): return (b,cz,s,h,p,t,u if t=="base" else None)
look={}
for folder,summ in STUDIES.values():
    rows=list(csv.reader(open(os.path.join(BASE,folder,summ)))); hi=next(i for i,r in enumerate(rows) if r and r[0]=="File Name" and "Cooling Elec (kWh)" in r)
    idx={c:rows[hi].index(c) for c in ECOLS}
    for r in rows[hi+1:]:
        if not r or "/" not in r[0]: continue
        p=r[0].split("/"); cz=int(p[0][2:]); cp=p[1].split("&"); h,pr,t,u=pcase(p[2])
        if not pr: continue
        try: look[K(cp[0],cz,cp[1],h,pr,t,u)]=({c:float(r[idx[c]]) for c in ECOLS}, p[2])
        except: pass
def exp(bld,cz,h,p,t,u):
    rp="NR" if p=="NC" else p
    if bld=="SFm":
        a=look.get(K("SFm",cz,"1",h,rp,t,u)); b=look.get(K("SFm",cz,"2",h,rp,t,u))
        if not a or not b: return None,None
        ns=NUMSTOR[cz]; w1,w2=2-ns,ns-1; return {c:round(a[0][c]*w1+b[0][c]*w2,4) for c in ECOLS}, "WTD: "+a[1]+" | "+b[1]
    r=look.get(K(bld,cz,"0",h,rp,t,u)); return (None,None) if not r else ({c:round(r[0][c],4) for c in ECOLS}, r[1])

ws=openpyxl.load_workbook(PAIRS,data_only=True).active
robert_pairs=set((r[0],r[1]) for r in ws.iter_rows(values_only=True) if r[0] and "TechID" not in str(r[0]))

audit=[["Bldg","CZ","Kind","TechID","MappedRun","srcCool","fileCool","MATCH"]]
tot=0; mismatch=0; pair_bad=0; basebad=0; blank=0; runtype_bad=0
for bld in ["DMo","MFm","SFm"]:
    B=list(csv.reader(open(os.path.join(OUT,bld,f"UEC_kWhBase_{bld}.csv"))))[1:]
    M=list(csv.reader(open(os.path.join(OUT,bld,f"UEC_kWhMeas_{bld}.csv"))))[1:]
    KW=list(csv.reader(open(os.path.join(OUT,bld,f"UEC_kWBaseMeas_{bld}.csv"))))[1:]
    for rb,rm,rk in zip(B,M,KW):
        tot+=1
        if (rb[0],rm[0]) not in robert_pairs: pair_bad+=1
        if any(x=="" for x in rb[4:7]+rm[4:7]+rk[4:6]): blank+=1
        # base>=measure kWh
        if sum(float(x) for x in rb[4:7]) < sum(float(x) for x in rm[4:7])-1e-6: basebad+=1
        for kind,row in [("base",rb),("meas",rm)]:
            h,p,t,u=ptid(row[0]); ev,run=exp(row[0].split("BA-")[-1] and row[0],int(row[3][2:]) if False else int(row[3][2:]),) if False else (None,None)
            cz=int(row[3][2:]); ev,run=exp(bld,cz,h,p,("base" if kind=="base" else "measure"),u)
            fc=float(row[5])
            if ev is None: audit.append([bld,cz,kind,row[0],"NO RUN","",fc,"MISSING"]); mismatch+=1; continue
            if kind=="base" and "Base" not in run and "WTD" not in run: runtype_bad+=1
            if kind=="meas" and "Measure" not in run and "WTD" not in run: runtype_bad+=1
            ok=abs(ev["Cooling Elec (kWh)"]-fc)<0.01
            audit.append([bld,cz,kind,row[0],run,ev["Cooling Elec (kWh)"],fc,"Y" if ok else "DIFF"]); mismatch+=(not ok)
with open(os.path.join(OUT,"audit_1392.csv"),"w",newline="") as f: csv.writer(f).writerows(audit)
print(f"permutations checked: {tot}  (expected 1392)")
print(f"rows whose (base,measure) is NOT a Robert pair: {pair_bad}")
print(f"rows with blank cells:                          {blank}")
print(f"rows base<measure (kWh):                        {basebad}")
print(f"audit value mismatches (file vs results summary): {mismatch}")
print(f"base->non-Base run or measure->non-Measure run:   {runtype_bad}")
print("wrote audit_1392.csv")
