"""
Reformat the COP-method UEC into Pete's approved template format:
 single 'TechID' column per file + the exact value-column headers.
  kWhBase/ThermBase  -> TechID = BASE techid (Col A)
  kWhMeas/ThermMeas  -> TechID = MEASURE techid (Col B)
  kWBaseMeas         -> TechID = MEASURE techid (unique per offer; base is shared)
Input COP cols: 0 Base TechID,1 Measure TechID,2 System Type,3 Bldg,4 Loc,5,6,7 values
"""
import csv, os, sys
SRC=sys.argv[1]; OUT=sys.argv[2]
def hdr(valcols): return ["TechID","System Type","Building Type","Building Location"]+valcols
SPECS={
 "UEC_COP_kWhBase":   ("UEC_kWhBase",   0, ["UEC_kWhBase__heat","UEC_kWhBase__cool","UEC_kWhBase__ventFan"]),
 "UEC_COP_kWhMeas":   ("UEC_kWhMeas",   1, ["UEC_kWhMeas__heat","UEC_kWhMeas__cool","UEC_kWhMeas__ventFan"]),
 "UEC_COP_ThermBase": ("UEC_ThermBase", 0, ["UEC_ThermBase__heat","UEC_ThermBase__cool","UEC_ThermBase__ventFan"]),
 "UEC_COP_ThermMeas": ("UEC_ThermMeas", 1, ["UEC_ThermMeas__heat","UEC_ThermMeas__cool","UEC_ThermMeas__ventFan"]),
}
for bld in ["DMo","MFm","SFm"]:
    od=os.path.join(OUT,bld); os.makedirs(od,exist_ok=True)
    for src,(name,tcol,vals) in SPECS.items():
        rows=list(csv.reader(open(os.path.join(SRC,bld,f"{src}_{bld}.csv"))))[1:]
        out=[hdr(vals)]+[[r[tcol],r[2],r[3],r[4],r[5],r[6],r[7]] for r in rows]
        with open(os.path.join(od,f"{name}_{bld}.csv"),"w",newline="") as f: csv.writer(f).writerows(out)
    # kWBaseMeas: TechID = measure (col1), base/meas kW (cols 5,6)
    rows=list(csv.reader(open(os.path.join(SRC,bld,f"UEC_COP_kWBaseMeas_{bld}.csv"))))[1:]
    out=[hdr(["UEC_YrkW__base","UEC_YrkW__meas"])]+[[r[1],r[2],r[3],r[4],r[5],r[6]] for r in rows]
    with open(os.path.join(od,f"UEC_kWBaseMeas_{bld}.csv"),"w",newline="") as f: csv.writer(f).writerows(out)
    print(f"  {bld}: 5 files reformatted")
print("done")
