"""
Build per-building delta (savings) files = base UEC - measure UEC.

Each base TechID (NoLRM-<X>%UC-<prog>) is paired with its corrected measure
(LRM-LSC-<prog>, same HVAC and CZ); savings = base - measure for kWh/kW/therms.
base > measure (undercharged uses more), so savings should be positive; any
negative row is printed as a warning.
"""
import csv, os, sys, re

def read(path):
    rows = list(csv.reader(open(path, newline="")))
    return rows[0], [r for r in rows[1:] if any(r)]

def measure_techid(base_tid):
    # NoLRM-7.5%UC-AOE  ->  LRM-LSC-AOE
    return re.sub(r'NoLRM-[\d.]+%UC', 'LRM-LSC', base_tid)

def main(d, bldg):
    _, base = read(os.path.join(d, f"UEC_{bldg}_base.csv"))
    hdr, meas = read(os.path.join(d, f"UEC_{bldg}_measure.csv"))
    midx = {(r[10], r[4]): r for r in meas}
    out = [hdr[:11] + ["Measure TechID", "Savings kWh", "Savings kW", "Savings Therms"]]
    neg = missing = 0
    for b in base:
        mtid = measure_techid(b[10])
        m = midx.get((mtid, b[4]))
        if not m:
            print(f"  no measure match: {b[10]} CZ{b[4]}"); missing += 1; continue
        row = b[:11] + [mtid]
        for i in (11, 12, 13):
            try:
                dv = round(float(b[i]) - float(m[i]), 4)
                if dv < 0:
                    neg += 1
                    print(f"  NEGATIVE savings: {b[10]} CZ{b[4]} col{i} = {dv}")
                row.append(dv)
            except (ValueError, TypeError):
                row.append("")
        out.append(row)
    with open(os.path.join(d, f"UEC_{bldg}_delta.csv"), "w", newline="") as f:
        csv.writer(f).writerows(out)
    print(f"{bldg}: {len(out)-1} delta rows, {neg} negative, {missing} unmatched")

if __name__ == "__main__":
    d = sys.argv[1]
    for bldg in ["DMo", "MFm", "SFm"]:
        main(d, bldg)
