"""
Apply the SFm&1 / SFm&2 NumStor weighting to result2.py's simdata.csv
(the official DEER post-processing SFm step Pete described).
  weighted = story1*(2-numstor) + story2*(numstor-1)  per (TechID, CZ)
applied to every numeric column, including the DEER peak
(Electricity:Facility [J](Hourly)). DMo/MFm need no weighting.

Usage: python weight_sfm_simdata.py <simdata.csv> <out.csv> <vintage:1975|1985>
"""
import csv, sys
SIMD, OUT, VINT = sys.argv[1], sys.argv[2], sys.argv[3]
NUMSTOR = {
 "1975": {1:1.48,2:1.48,3:1.48,4:1.48,5:1.48,6:1.55,7:1.55,8:1.55,9:1.33},
 "1985": {10:1.42,11:1.23,12:1.23,13:1.23,14:1.12,15:1.12,16:1.31},
}[VINT]
rows = list(csv.reader(open(SIMD)))
h = rows[0]
ti = h.index("TechID"); ci = h.index("BldgLoc"); si = h.index("Story")
numstart = h.index("Net Site EUI")          # first numeric column
data = {}
for r in rows[1:]:
    if not any(r): continue
    data.setdefault((r[ti], r[ci]), {})[r[si]] = r
out = [h]; missing = 0
for (techid, cz), st in sorted(data.items()):
    s1, s2 = st.get("1"), st.get("2")
    if not s1 or not s2: missing += 1; continue
    ns = NUMSTOR[int(cz[2:])]; w1, w2 = 2 - ns, ns - 1
    row = list(s1); row[si] = "weighted"
    for i in range(numstart, len(h)):
        try: row[i] = round(float(s1[i]) * w1 + float(s2[i]) * w2, 4)
        except (ValueError, IndexError): pass
    out.append(row)
with open(OUT, "w", newline="") as f: csv.writer(f).writerows(out)
print(f"weighted rows: {len(out)-1}  (unpaired skipped: {missing})")
# quick sanity: DMo CZ06 rDXGF LSC measure-ish cooling + peak
J_KWH = 2.77778e-7
pk = h.index("Electricity:Facility [J](Hourly)")
cl = h.index("Cooling")
for r in out[1:]:
    if r[ci] == "CZ06" and "rDXGF" in r[h.index("BldgHVAC")] and "LSC" in r[ti] and "Measure" not in r[ti]:
        print(f"  weighted CZ06 rDXGF {r[ti].split('BA-')[-1]:22} cool={r[cl]}  DEERpeak={round(float(r[pk])*J_KWH,4)} kW")
        break
