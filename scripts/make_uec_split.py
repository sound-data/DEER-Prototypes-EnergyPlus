"""
Split the UEC tables into separate BASE and MEASURE files per building.
  base   = NoLRM TechIDs (undercharged baselines)
  measure = LRM-LSC TechIDs (charge corrected)
For SFm, combine the two stories first via the official numstor weighting
(weighted = 1story*(2-numstor) + 2story*(numstor-1)), then split.

Columns: 0 Sector,1 BldgType,2 BldgVint,3 BldgHVAC,4 BldgLoc(CZ),...,10 TechID,
         11 UEC kWh,12 UEC kW,13 UEC Therms
"""
import csv, os, sys

# SFm avg stories by CZ (CZ1-9 = 1975 vintage, CZ10-16 = 1985 vintage)
NUMSTOR = {1:1.48,2:1.48,3:1.48,4:1.48,5:1.48,6:1.55,7:1.55,8:1.55,9:1.33,
           10:1.42,11:1.23,12:1.23,13:1.23,14:1.12,15:1.12,16:1.31}
KWH, KW, THM = 11, 12, 13

def read_uec(path):
    rows = list(csv.reader(open(path, newline="")))
    return rows[0], [r for r in rows[1:] if any(r)]

def split_write(header, rows, base_path, meas_path):
    base = [r for r in rows if "NoLRM" in r[10]]
    meas = [r for r in rows if "LRM-LSC" in r[10]]
    for path, data in [(base_path, base), (meas_path, meas)]:
        with open(path, "w", newline="") as f:
            w = csv.writer(f); w.writerow(header); w.writerows(data)
    return len(base), len(meas)

def main(d):
    for bldg in ["DMo", "MFm"]:
        h, rows = read_uec(os.path.join(d, f"UEC_{bldg}.csv"))
        b, m = split_write(h, rows, os.path.join(d, f"UEC_{bldg}_base.csv"),
                           os.path.join(d, f"UEC_{bldg}_measure.csv"))
        print(f"{bldg}: base={b}, measure={m}")
    # SFm: weight stories then split
    h, r1 = read_uec(os.path.join(d, "UEC_SFm_1story.csv"))
    _, r2 = read_uec(os.path.join(d, "UEC_SFm_2story.csv"))
    by2 = {(r[10], r[4]): r for r in r2}
    weighted = []
    for r in r1:
        two = by2.get((r[10], r[4]))
        cz = int(r[4]); ns = NUMSTOR[cz]; w1, w2 = 2 - ns, ns - 1
        out = r[:11]
        for i in (KWH, KW, THM):
            try:
                out.append(round(float(r[i]) * w1 + float(two[i]) * w2, 4))
            except (ValueError, TypeError):
                out.append("")
        weighted.append(out)
    b, m = split_write(h, weighted, os.path.join(d, "UEC_SFm_base.csv"),
                       os.path.join(d, "UEC_SFm_measure.csv"))
    print(f"SFm (story-weighted): base={b}, measure={m}")

if __name__ == "__main__":
    main(sys.argv[1])
