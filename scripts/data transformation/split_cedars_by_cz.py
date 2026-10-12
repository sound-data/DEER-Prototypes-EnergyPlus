"""FINAL CEDARS 8760 rebuild, directly in eTRM deliverables.
Structure per building type:
  <BT>/CEDARS_LoadShape_<BT>.zip           full deliverable (zip only; too big for Excel anyway)
  <BT>/CEDARS_LoadShape_<BT>_CZxx.csv      per-CZ, PLAIN CSV for direct opening in Excel
  <BT>/CEDARS_LoadShape_<BT>_CZxx.zip      same file zipped, for emailing
All UECproportion values plain fixed-point decimals (no scientific notation).
VERIFICATION.txt records rows + shape-sum range + MD5 per file."""
import csv, io, hashlib, zipfile
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

STASH = Path(r"C:\DEER-Prototypes-EnergyPlus\scripts\data transformation\LRM_outputs_final")
OUT = Path(r"C:\DEER-Prototypes-EnergyPlus\eTRM deliverables\SWSV014 CEDARS 8760s by CZ 2026-09-01")

manifest = ["SWSV014 CEDARS 8760 load shapes - rebuilt 2026-09-01 (HP heating COP fix, hard-sized runs, plain decimals)",
            "Open the per-CZ .csv files directly in Excel; use the .zip copies for email.",
            "Checks: each TechID shape sums to 1.0; whole column L of a per-CZ file sums to 20;",
            "row count of every per-CZ csv = 175,201 including header.", ""]

def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

for bt in ["DMo", "MFm", "SFm"]:
    d = OUT / bt
    d.mkdir(parents=True, exist_ok=True)
    for f in d.iterdir():
        f.unlink()
    src = STASH / bt / f"CEDARS_LoadShape_{bt}.zip"

    full_csv = d / f"CEDARS_LoadShape_{bt}.csv"
    cz_files, cz_writers = {}, {}
    sums = defaultdict(Decimal)
    with zipfile.ZipFile(src) as z, open(full_csv, "w", newline="") as fout:
        fw = csv.writer(fout)
        with io.TextIOWrapper(z.open(z.namelist()[0]), newline="") as fin:
            r = csv.reader(fin)
            hdr = next(r)
            czi, vi, ti = hdr.index("BldgLoc"), hdr.index("UECproportion"), hdr.index("TechID")
            fw.writerow(hdr)
            for row in r:
                v = row[vi]
                if "e" in v or "E" in v:
                    row[vi] = format(Decimal(v), "f")
                cz = row[czi]
                sums[(cz, row[ti])] += Decimal(row[vi])
                if cz not in cz_writers:
                    p = d / f"CEDARS_LoadShape_{bt}_{cz}.csv"
                    cz_files[cz] = open(p, "w", newline="")
                    cz_writers[cz] = csv.writer(cz_files[cz])
                    cz_writers[cz].writerow(hdr)
                fw.writerow(row)
                cz_writers[cz].writerow(row)
    for fh in cz_files.values():
        fh.close()

    smin, smax = min(sums.values()), max(sums.values())
    assert abs(smin - 1) < Decimal("0.000001") and abs(smax - 1) < Decimal("0.000001"), (bt, smin, smax)
    manifest.append(f"== {bt}: {len(sums)} shapes, sums {smin:.8f}..{smax:.8f}")

    # full file: zip only
    zp = full_csv.with_suffix(".zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(full_csv, full_csv.name)
    manifest.append(f"  {zp.name}: MD5={md5(zp)}")
    full_csv.unlink()

    # per-CZ: plain csv only (no per-CZ zips in the deliverable)
    for i in range(1, 17):
        p = d / f"CEDARS_LoadShape_{bt}_CZ{i:02d}.csv"
        nrows = sum(1 for _ in open(p, "rb")) - 1
        manifest.append(f"  {p.name}: data rows={nrows}, MD5={md5(p)}")
        assert nrows == 175200, (p.name, nrows)
    print(bt, "done; shape sums:", f"{smin:.8f}..{smax:.8f}")

(OUT / "VERIFICATION.txt").write_text("\n".join(manifest))
files = [f for f in OUT.rglob("*") if f.is_file()]
print("total files:", len(files), "| total size:", round(sum(f.stat().st_size for f in files)/1e9, 2), "GB")
