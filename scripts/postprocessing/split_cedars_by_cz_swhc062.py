"""SWHC062 CEDARS 8760 deliverable build, mirroring the SWSV014 2026-09-08 set.
Structure per building type (17 incl. MFmCmn):
  <BT>/SWHC062_8760_LoadShape_<BT>.zip       full deliverable (zip of one combined csv)
  <BT>/SWHC062_8760_LoadShape_<BT>_CZxx.csv  per-CZ, PLAIN CSV for direct opening in Excel
Top level: VERIFICATION.txt (rows + shape-sum range + MD5 per file).
All UECproportion values plain fixed-point decimals (no scientific notation).
NormUnit is already column 6 ('Cap-Tons') in the source (Com_SWHC062.py output).
Source: scripts/data transformation/CEDARS_LoadShape_Com_realTechID.zip (real TechIDs).
"""
import csv, io, hashlib, zipfile
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from datetime import date

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "scripts" / "data transformation" / "CEDARS_LoadShape_Com_realTechID.zip"
DATESTR = date.today().isoformat()
OUT = REPO / "eTRM deliverables" / f"SWHC062 CEDARS 8760s by CZ {DATESTR}"

SHAPES_PER_CZ = 40   # 5 measures x 4 HVAC x Base/Measure
TECHGROUP, TECHTYPE = "HV_Tech", "TStat"  # measure-level, per the OFC workbook
ROWS_PER_CZ = SHAPES_PER_CZ * 8760

manifest = [f"SWHC062 CEDARS 8760 load shapes - built {DATESTR} from the 2026-08-2x runs "
            "(Thursday/2009-basis calendar, CZ2025 weather, revised M3/M5 measure cases; "
            "real measure TechIDs; NormUnit column 6 = Cap-Tons; plain decimals)",
            "Open the per-CZ .csv files directly in Excel; use the .zip copies for email.",
            "Checks: each TechID shape sums to 1.0; whole UECproportion column of a per-CZ "
            f"file sums to {SHAPES_PER_CZ};",
            f"row count of every per-CZ csv = {ROWS_PER_CZ + 1:,} including header.", ""]


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


zsrc = zipfile.ZipFile(SRC)
bts = sorted(n.replace("CEDARS_LoadShape_Com_", "").replace(".csv", "") for n in zsrc.namelist())
print(len(bts), "building types:", bts, flush=True)

for bt in bts:
    d = OUT / bt
    d.mkdir(parents=True, exist_ok=True)
    for f in d.iterdir():
        f.unlink()

    full_csv = d / f"SWHC062_8760_LoadShape_{bt}.csv"
    cz_files, cz_writers = {}, {}
    sums = defaultdict(Decimal)
    with open(full_csv, "w", newline="") as fout:
        fw = csv.writer(fout)
        with io.TextIOWrapper(zsrc.open(f"CEDARS_LoadShape_Com_{bt}.csv"), newline="") as fin:
            r = csv.reader(fin)
            hdr = next(r)
            assert hdr[5] == "NormUnit", hdr  # column 6 per CEDARS template
            czi, vi, ti = hdr.index("BldgLoc"), hdr.index("UECproportion"), hdr.index("TechID")
            tgi, tti = hdr.index("TechGroup"), hdr.index("TechType")
            fw.writerow(hdr)
            for row in r:
                # source zip has TechGroup/TechType null for all but Asm (lookup
                # keyed on BldgType); fill the measure-level values per the workbook
                if not row[tgi]:
                    row[tgi] = TECHGROUP
                if not row[tti]:
                    row[tti] = TECHTYPE
                v = row[vi]
                if "e" in v or "E" in v:
                    row[vi] = format(Decimal(v), "f")
                cz = row[czi]
                sums[(cz, row[ti])] += Decimal(row[vi])
                if cz not in cz_writers:
                    p = d / f"SWHC062_8760_LoadShape_{bt}_{cz}.csv"
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

    zp = full_csv.with_suffix(".zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(full_csv, full_csv.name)
    manifest.append(f"  {zp.name}: MD5={md5(zp)}")
    full_csv.unlink()

    for i in range(1, 17):
        p = d / f"SWHC062_8760_LoadShape_{bt}_CZ{i:02d}.csv"
        nrows = sum(1 for _ in open(p, "rb")) - 1
        manifest.append(f"  {p.name}: data rows={nrows}, MD5={md5(p)}")
        assert nrows == ROWS_PER_CZ, (p.name, nrows)
    print(bt, "done; shape sums:", f"{smin:.8f}..{smax:.8f}", flush=True)

(OUT / "VERIFICATION.txt").write_text("\n".join(manifest))

# whole-set zip beside the folder, like the SWSV014 deliverable
setzip = OUT.parent / f"{OUT.name}.zip"
with zipfile.ZipFile(setzip, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    for f in sorted(OUT.rglob("*")):
        if f.is_file():
            comp = zipfile.ZIP_STORED if f.suffix == ".zip" else zipfile.ZIP_DEFLATED
            zf.write(f, f.relative_to(OUT.parent).as_posix(), compress_type=comp)
print("set zip:", setzip.name, flush=True)

files = [f for f in OUT.rglob("*") if f.is_file()]
print("total files:", len(files), "| total size:", round(sum(f.stat().st_size for f in files) / 1e9, 2), "GB", flush=True)
