"""
Independent check that the revised TechIDs are correctly applied:
 1) every (base,measure) pair in the output exists in Robert's revised file
 2) the savings on each row match the UC level NAMED in that row's measure TechID
    (measure cool == base cool / (1+coolfrac[uc]); HP heat likewise)
 3) base TechIDs are the single no-UC form; measure carry Correct-X%UC
Re-derives from scratch and compares to the written files.
"""
import csv, os, re, sys, openpyxl
OUT=sys.argv[1]; PAIRS=sys.argv[2]
COOLFRAC={0.0:0.0945,7.5:0.2283,15.0:0.3621,22.5:0.4959,30.0:0.6297,40.0:0.8081}
HEATFRAC={0.0:0.0394,7.5:0.0951,15.0:0.1508,22.5:0.2066,30.0:0.2623,40.0:0.3366}
ws=openpyxl.load_workbook(PAIRS,data_only=True).active
robert=set((r[0],r[1]) for r in ws.iter_rows(values_only=True) if r[0] and "TechID" not in str(r[0]))
print(f"Robert's file: {len(robert)} distinct pairs, "
      f"{len(set(b for b,_ in robert))} distinct base IDs, {len(set(m for _,m in robert))} distinct measure IDs")
def uc(mt):
    m=re.search(r"Correct-(\d+\.?\d*)%\s*UC",mt); return float(m.group(1)) if m else None
tot=pair_bad=uc_bad=cool_bad=heat_bad=struct_bad=0
for bld in ["DMo","MFm","SFm"]:
    B=list(csv.reader(open(os.path.join(OUT,bld,f"UEC_COP_kWhBase_{bld}.csv"))))[1:]
    M=list(csv.reader(open(os.path.join(OUT,bld,f"UEC_COP_kWhMeas_{bld}.csv"))))[1:]
    for rb,rm in zip(B,M):
        tot+=1
        bt,mt=rb[0],rb[1]; hvac=rb[2]   # col0=Base TechID, col1=Measure TechID
        # 1) pairing exists in Robert's file
        if (bt,mt) not in robert: pair_bad+=1
        # 3) structure: base no-UC, measure has Correct-X%UC
        if re.search(r"%UC",bt) or "Correct" not in mt: struct_bad+=1
        u=uc(mt)
        if u is None or u not in COOLFRAC: uc_bad+=1; continue
        # 2) savings match the named UC level
        bh,bc=float(rb[5]),float(rb[6]); mh,mc=float(rm[5]),float(rm[6])
        if abs(mc - bc/(1+COOLFRAC[u]))>0.05: cool_bad+=1
        exp_mh = bh/(1+HEATFRAC[u]) if hvac=="rDXHP" else bh
        if abs(mh-exp_mh)>0.05: heat_bad+=1
print(f"\nrows checked: {tot}")
print(f"  pairs NOT in Robert's file:                 {pair_bad}")
print(f"  base has UC / measure missing 'Correct':    {struct_bad}")
print(f"  measure UC unparseable:                     {uc_bad}")
print(f"  cooling savings != named UC fraction:       {cool_bad}")
print(f"  heating savings != named UC fraction:       {heat_bad}")
print("ALL CLEAN" if (pair_bad+struct_bad+uc_bad+cool_bad+heat_bad)==0 else "*** ISSUES ABOVE ***")
