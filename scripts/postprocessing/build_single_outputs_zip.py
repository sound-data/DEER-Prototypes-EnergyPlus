"""Single SWHC062 Energy Models Outputs zip (SharePoint-size), per Robert's
request: instance.idf + instance-out.err + instance-tbl.htm for every run in
both studies. The instance-out.sql files (181.6 GB raw) are omitted to keep the
zip shippable; they remain available per building type in the
'Energy Models Outputs by BldgType' zips.
"""
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MEAS = REPO / "commercial measures" / "SWHC062-03 Occupancy Fan Controller"
DEST = REPO / "eTRM deliverables" / "SWHC062 Energy Models Outputs 2026-09-12.zip"
KEEP = {"instance.idf", "instance-out.err", "instance-tbl.htm"}
STUDIES = ["SWHC062-03 Occupancy Fan Controller_Ex",
           "SWHC062-03 Occupancy Fan Controller_Htl_Ex"]

NOTE = """SWHC062 Energy Models Outputs 2026-09-12
One folder per run (both studies, 10,240 runs): instance.idf (model input),
instance-out.err (EnergyPlus errors), instance-tbl.htm (tabular results).
The instance-out.sql files (SQLite hourly/tabular output, ~182 GB raw) are
omitted from this combined zip for size; they are included in the per-building-
type zips in "SWHC062 Energy Models Outputs by BldgType" for anyone who needs
the raw SQL. All runs reflect the corrected Thursday/2009-basis calendar,
CZ2025 weather, and the revised Base 3/5 measure cases; the Htl CZ06
M3-cDXGF-Measure run is the 2026-09-12 corrected re-simulation.
"""

count = 0
with zipfile.ZipFile(DEST, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    zf.writestr("README.txt", NOTE)
    for study in STUDIES:
        runs = MEAS / study / "runs"
        for p in sorted(runs.rglob("*")):
            if p.is_file() and p.name in KEEP:
                zf.write(p, f"{study}/runs/{p.relative_to(runs).as_posix()}")
                count += 1
                if count % 5000 == 0:
                    print(f"{count} files...", flush=True)
print(f"done: {count} files -> {DEST.name} ({DEST.stat().st_size/1e9:.2f} GB)", flush=True)
