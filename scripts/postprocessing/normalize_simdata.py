"""
Floor-area normalization of result2.py simdata (the method Robert confirmed):
divide every whole-model energy/peak value by the model's Net Conditioned
Building Area -> per-sqft UEC. Because numerator and denominator both cover
ALL buildings in the model (EL groups), the multi-building count cancels and
the factor-of-2 goes away.

  energy end-uses:  kWh / ft2
  DEER peak:        Electricity:Facility [J](Hourly) * 2.77778e-7 (J->kWh, =kW hourly) / ft2

Usage: python normalize_simdata.py <simdata.csv|simdata_weighted.csv> <out.csv>
"""
import csv, sys
SIMD, OUT = sys.argv[1], sys.argv[2]
M2_FT2 = 10.7639
J_KW = 2.77778e-7
ENERGY_COLS = ["Total","Heating","Cooling","Interior Lighting","Exterior Lighting",
    "Interior Equipment","Exterior Equipment","Fans","Pumps","Heat Rejection",
    "Water Systems","Refrigeration","Heating Elec","Cooling Elec","Heating NG",
    "Cooling NG","Interior Equipment Elec","Interior Equipment NG"]
PEAK_COL = "Electricity:Facility [J](Hourly)"
rows = list(csv.reader(open(SIMD))); h = rows[0]
ai = h.index("Conditioned Area")
ei = {c: h.index(c) for c in ENERGY_COLS if c in h}
pi = h.index(PEAK_COL) if PEAK_COL in h else None
out = [h + ["Area ft2", "DEER Peak kW/ft2"]]
for r in rows[1:]:
    if not any(r) or not r[ai]: continue
    area_ft2 = float(r[ai]) * M2_FT2
    row = list(r)
    for c, i in ei.items():
        try: row[i] = round(float(r[i]) / area_ft2, 8)
        except ValueError: pass
    peak_kw_ft2 = ""
    if pi is not None and r[pi]:
        peak_kw_ft2 = round(float(r[pi]) * J_KW / area_ft2, 8)
        row[pi] = round(float(r[pi]) * J_KW / area_ft2, 8)   # normalized peak in place too
    out.append(row + [round(area_ft2, 1), peak_kw_ft2])
with open(OUT, "w", newline="") as f: csv.writer(f).writerows(out)
print(f"normalized {len(out)-1} rows -> {OUT}")
