"""Repackage the SWHC059 CEDARS load shapes into the eTRM layout Robert received
for SWHC062 (the occupancy fan controller).

Per building type, a folder holding sixteen per-climate-zone CSVs plus one zip:
    <OUT>/<BldgType>/SWHC059_8760_LoadShape_<BldgType>_<CZ>.csv
    <OUT>/<BldgType>/SWHC059_8760_LoadShape_<BldgType>.zip
plus a VERIFICATION.txt recording, per building type, the shape count, the range
of per-shape sums (each must be 1.0), row counts and MD5s.

Source is whatever run_res_by_bldgtype.py stashed:
    outputs_by_bldgtype/<BldgType>/CEDARS_LoadShape_<BldgType>.zip

Note the residential split differs from commercial: single-family covers two
vintages that the CEDARS script has already folded into one output keyed by
climate zone (CZ01-CZ09 = 1975, CZ10-CZ16 = 1985), so a single-family building
type still yields sixteen per-zone files.

Usage:
    python package_8760_swhc059.py                 # all building types found
    python package_8760_swhc059.py DMo MFm         # a subset
"""
import hashlib
import io
import os
import sys
import zipfile
from datetime import date

import pandas as pd

os.chdir(os.path.dirname(os.path.abspath(__file__)))

SRC_DIR = "outputs_by_bldgtype"
PREFIX = "SWHC059_8760_LoadShape_"
REPO = os.path.abspath(os.path.join("..", ".."))
OUT = os.path.join(REPO, "eTRM deliverables",
                   f"SWHC059 CEDARS 8760s by CZ {date.today():%Y-%m-%d}")
BLDGTYPES = ["DMo", "MFm", "SFm"]

# SWHC062's VERIFICATION.txt promises "plain decimals"; pandas would otherwise
# write these small proportions in scientific notation. %.20f is the format the
# delivered SWHC062 files actually used - verified to reproduce their values
# character for character, and it round-trips back to the same float.
FLOAT_FMT = "%.20f"

# Column order Robert received for SWHC062. Checked on every build so a format
# drift shows up here rather than in his inbox.
EXPECTED_COLUMNS = ["Sector", "BldgType", "BldgVint", "BldgHVAC", "BldgLoc", "NormUnit",
                    "Type (Whole Building or End Use)", "Source Year", "TechGroup",
                    "TechType", "TechID", "Hour of Year", "UECproportion"]


def md5(path, chunk=1 << 20):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def source_zip(bt):
    p = os.path.join(SRC_DIR, bt, f"CEDARS_LoadShape_{bt}.zip")
    return p if os.path.exists(p) else None


def package(bt, report):
    src = source_zip(bt)
    if src is None:
        print(f"{bt}: no CEDARS_LoadShape_{bt}.zip in {SRC_DIR}/{bt}, skipping", flush=True)
        report.append(f"== {bt}: NOT BUILT (no source load shape)")
        return False

    with zipfile.ZipFile(src) as z:
        df = pd.read_csv(z.open(z.namelist()[0]))

    if list(df.columns) != EXPECTED_COLUMNS:
        missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
        extra = [c for c in df.columns if c not in EXPECTED_COLUMNS]
        raise SystemExit("\n".join([
            f"{bt}: load shape columns do not match the SWHC062 deliverable layout.",
            f"  missing: {missing}",
            f"  unexpected: {extra}",
            f"  got: {list(df.columns)}",
            "Rebuild the load shapes with run_res_by_bldgtype.py after updating the scripts.",
        ]))

    sums = df.groupby(["TechID", "BldgLoc"])["UECproportion"].sum()
    # plain ints: numpy scalars would print as "[np.int64(8760)]" in the note
    hours = sorted(int(h) for h in df.groupby(["TechID", "BldgLoc"])["Hour of Year"].count().unique())

    dest = os.path.join(OUT, bt)
    os.makedirs(dest, exist_ok=True)
    lines = [f"== {bt}: {len(sums)} shapes, sums {sums.min():.8f}..{sums.max():.8f}, "
             f"hours per shape {hours}"]
    if df["TechGroup"].isna().any() or df["TechType"].isna().any():
        lines.append(f"   WARNING: TechGroup/TechType nulls "
                     f"({int(df['TechGroup'].isna().sum())}/{int(df['TechType'].isna().sum())}) "
                     f"- the measure list join did not fully match")

    # per-CZ csv files, plus one zip holding the whole building type
    zippath = os.path.join(dest, f"{PREFIX}{bt}.zip")
    with zipfile.ZipFile(zippath, "w", zipfile.ZIP_DEFLATED) as zf:
        buf = io.StringIO()
        df.to_csv(buf, index=False, float_format=FLOAT_FMT)
        zf.writestr(f"{PREFIX}{bt}.csv", buf.getvalue())
    lines.append(f"  {os.path.basename(zippath)}: MD5={md5(zippath)}")

    for cz, sub in df.groupby("BldgLoc"):
        csvpath = os.path.join(dest, f"{PREFIX}{bt}_{cz}.csv")
        sub.to_csv(csvpath, index=False, float_format=FLOAT_FMT)
        lines.append(f"  {os.path.basename(csvpath)}: data rows={len(sub)}, MD5={md5(csvpath)}")

    print(f"{bt}: {df['BldgLoc'].nunique()} CZ files, {len(sums)} shapes, {len(df)} rows", flush=True)
    report.extend(lines)
    return True


def main(argv):
    wanted = argv[1:] or BLDGTYPES
    unknown = [b for b in wanted if b not in BLDGTYPES]
    if unknown:
        raise SystemExit(f"unknown building type(s) {unknown}; choose from {BLDGTYPES}")

    os.makedirs(OUT, exist_ok=True)
    report = [
        f"SWHC059 CEDARS 8760 load shapes - built {date.today():%Y-%m-%d} from the "
        f"SWHC059 SFC runs (CZ2025 weather; NormUnit column 6 = Area-ft2-BA; real measure TechIDs).",
        "Open the per-CZ .csv files directly in Excel; use the .zip copies for email.",
        "Checks: each TechID shape sums to 1.0 over 8760 hours.",
        "",
    ]
    built = [bt for bt in wanted if package(bt, report)]

    with open(os.path.join(OUT, "VERIFICATION.txt"), "w") as f:
        f.write("\n".join(report) + "\n")
    print(f"\ndone -> {OUT}")
    print(f"built: {built if built else 'nothing'}")
    return 0 if len(built) == len(wanted) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
