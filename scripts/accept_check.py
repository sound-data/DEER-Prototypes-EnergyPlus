"""
Test the revised UEC files against Robert's acceptance criteria:
  1) Base > Measure for every row (electric kWh total and peak kW)
  2) Every row populated (no blanks)
Plus: base/measure rows are aligned (same bldg/CZ/system) and the base->measure
TechID pairing on each row matches Pete's 'Base Measure Tech ID pairs.xlsx'.
"""
import csv, os, sys, openpyxl

OUT = sys.argv[1]; DL = sys.argv[2]
def rd(f): return list(csv.reader(open(os.path.join(OUT, f))))

b = rd("UEC_kWhBase.csv");  m = rd("UEC_kWhMeas.csv")
tb = rd("UEC_ThermBase.csv"); tm = rd("UEC_ThermMeas.csv"); kw = rd("UEC_kWBaseMeas.csv")

# Pete's pairing map (base TechID -> measure TechID)
ws = openpyxl.load_workbook(os.path.join(DL, "Base Measure Tech ID pairs.xlsx"), data_only=True)["Sheet1"]
pairs = set((r[0], r[1]) for r in ws.iter_rows(values_only=True) if r[0] and r[0] != "TechID - Base")

n = len(b) - 1
align = pairok = 0
kwh_bad = []; kw_bad = []; therm_lt = 0; blanks = 0
for i in range(1, len(b)):
    rb, rm, rkw = b[i], m[i], kw[i]
    # alignment: same system/bldg/CZ
    if rb[1:4] == rm[1:4] == rkw[1:4]: align += 1
    # pairing matches Pete's file
    if (rb[0], rm[0]) in pairs: pairok += 1
    # populated
    for r, ncol in ((rb,7),(rm,7),(tb[i],7),(tm[i],7),(rkw,6)):
        if any(c == "" for c in r[:ncol]): blanks += 1; break
    # Base > Measure: kWh total
    bt = sum(float(x) for x in rb[4:7]); mt = sum(float(x) for x in rm[4:7])
    if not (bt > mt): kwh_bad.append((i, rb[2], rb[3], rb[0], round(bt,1), round(mt,1)))
    # Base > Measure: peak kW (cols 4=base,5=meas)
    if rkw[4] != "" and rkw[5] != "":
        if not (float(rkw[4]) > float(rkw[5])): kw_bad.append((i, rkw[2], rkw[3], rkw[0], rkw[4], rkw[5]))
    # therms base vs measure (expect equal -> no gas savings)
    if sum(float(x) for x in tb[i][4:7]) < sum(float(x) for x in tm[i][4:7]) - 1e-6: therm_lt += 1

print(f"rows: {n}")
print(f"base/measure row-aligned (same bldg/CZ/system): {align}/{n}")
print(f"row pairing matches Pete's pairing file:         {pairok}/{n}")
print(f"rows with any blank cell:                        {blanks}")
print(f"--- Robert criterion 1: Base > Measure ---")
print(f"  kWh total  base>measure FAILURES: {len(kwh_bad)}")
for x in kwh_bad[:10]: print("    ", x)
print(f"  peak kW    base>measure FAILURES: {len(kw_bad)}")
for x in kw_bad[:10]: print("    ", x)
print(f"  therms rows where base<measure (should be 0; gas equal): {therm_lt}")
