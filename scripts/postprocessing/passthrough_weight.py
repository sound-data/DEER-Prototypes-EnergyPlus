"""DMo/MFm are 1-story models: weighted = the single record (weight 1.0).
Emit simdata_weighted.csv in the same shape as the SFm weighted files
(Story column set to 'weighted') so all study folders have a uniform file set."""
import csv, sys
SIMD, OUT = sys.argv[1], sys.argv[2]
rows = list(csv.reader(open(SIMD)))
h = rows[0]
si = h.index("Story")
out = [h]
for r in rows[1:]:
    if not any(r): continue
    row = list(r)
    row[si] = "weighted"
    out.append(row)
with open(OUT, "w", newline="") as f: csv.writer(f).writerows(out)
print(f"pass-through weighted rows: {len(out)-1} -> {OUT}")
