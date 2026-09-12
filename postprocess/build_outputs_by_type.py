"""Split the SWHC062 Energy Models Outputs into one zip per building type
(the 79 GB single zip is impractical to upload). Each zip carries the four
CPUC-requested files per run for that building type across all CZs."""
import zipfile
from pathlib import Path

MEASURE = Path(r"C:\dev\SWHC062-03\commercial measures\SWHC062-03 Occupancy Fan Controller")
STUDIES = ["SWHC062-03 Occupancy Fan Controller_Ex", "SWHC062-03 Occupancy Fan Controller_Htl_Ex"]
OUT = Path(r"C:\dev\SWHC062-03\eTRM deliverables\SWHC062 Energy Models Outputs by BldgType 2026-08-21")
OUT.mkdir(exist_ok=True)
KEEP = {"instance.idf", "instance-out.err", "instance-tbl.htm", "instance-out.sql"}

# discover building types
types = sorted({d.name for s in STUDIES for cz in (MEASURE / s / "runs").glob("CZ*")
                for d in cz.iterdir() if d.is_dir()})
print("building types:", types)

for bt in types:
    dest = OUT / f"SWHC062 Outputs {bt} 2026-08-21.zip"
    count = 0
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for s in STUDIES:
            runs = MEASURE / s / "runs"
            for p in sorted(runs.glob(f"CZ*/{bt}/*/*")):
                if p.is_file() and p.name in KEEP:
                    zf.write(p, f"{s}/{p.relative_to(MEASURE / s)}")
                    count += 1
    print(f"{bt}: {count} files -> {dest.name} ({dest.stat().st_size/1e9:.1f} GB)", flush=True)
print("done")
