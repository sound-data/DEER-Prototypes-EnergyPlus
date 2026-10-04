"""
make_measure_off_hour2.py

Builds "Measure Off-hour2.csv" in the same format as "Measure_Off-hour.csv",
using per-building-type/run-type CSV files extracted from hourly_results.zip.

Inputs (expected in the same directory as this script, or adjust paths below):
    Measure_Off-hour.csv        - the original file; used only to read off the
                                   exact Building Type / Run Type / System Type /
                                   Climate Zone ordering conventions and header.
    hourly_results/             - unzipped contents of hourly_results.zip, i.e.
                                   files named like "Asm-M1.csv", "ECC-M3.csv", etc.
                                   (the "*-columns.txt" files are ignored).

Notes on data coverage:
    - hourly_results.zip contains 16 of the 17 building types found in
      Measure_Off-hour.csv. It is missing "MFmCmn" entirely.
    - Per instruction, MFmCmn rows are synthesized as a direct copy of the
      "OfS" (Office, Small) building type's values, relabeled as MFmCmn.
      This is a placeholder / stand-in, not real MFmCmn simulation data.

Output:
    "Measure Off-hour2.csv" - same 14-column layout as the original
    (10 real data columns + 4 trailing blank columns), CRLF line endings,
    sorted Building Type -> Run Type -> System Type -> Climate Zone to match
    the original file's row order.
"""

import glob
import re

import pandas as pd

ORIGINAL_CSV = "Measure_Off-hour.csv"
HOURLY_RESULTS_DIR = "hourly_results"
OUTPUT_CSV = "Measure Off-hour2.csv"

SYS_ORDER = ["cDXGF", "cDXHP", "cPTAC", "cPVVG"]
CZ_ORDER = [f"CZ{n:02d}" for n in range(1, 17)]
RUN_ORDER = ["M1", "M2", "M3", "M4", "M5"]

PLACEHOLDER_BLDG_TYPE = "MFmCmn"
PLACEHOLDER_SOURCE_BLDG_TYPE = "OfS"


def load_original_ordering(path):
    """Read the original file just to recover the exact Building Type order
    (including MFmCmn, which won't appear in the zip data) and the header line."""
    df = pd.read_csv(path)
    bt_order = df["Building Type"].drop_duplicates().tolist()
    with open(path, "rb") as f:
        header_line = f.readline().decode()
    return bt_order, header_line


def load_hourly_results(results_dir):
    """Concatenate every '<BldgType>-<RunType>.csv' file in the hourly_results
    folder into one dataframe, adding a 'Run Type' column parsed from the filename."""
    files = sorted(glob.glob(f"{results_dir}/*.csv"))
    files = [f for f in files if "columns" not in f]

    dfs = []
    for f in files:
        m = re.search(r"([A-Za-z0-9]+)-M(\d)\.csv$", f)
        run_type = f"M{m.group(2)}"
        df = pd.read_csv(f)
        df.insert(1, "Run Type", run_type)
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


def add_placeholder_building_type(combined, new_type, source_type):
    """Duplicate all rows for `source_type` and relabel them as `new_type`.
    Used here to synthesize MFmCmn from OfS, since the zip has no MFmCmn data."""
    source_rows = combined[combined["Building Type"] == source_type].copy()
    source_rows["Building Type"] = new_type
    return pd.concat([combined, source_rows], ignore_index=True)


def sort_like_original(combined, bt_order):
    combined["Building Type"] = pd.Categorical(combined["Building Type"], categories=bt_order, ordered=True)
    combined["Run Type"] = pd.Categorical(combined["Run Type"], categories=RUN_ORDER, ordered=True)
    combined["System Type"] = pd.Categorical(combined["System Type"], categories=SYS_ORDER, ordered=True)
    combined["Climate Zone"] = pd.Categorical(combined["Climate Zone"], categories=CZ_ORDER, ordered=True)
    combined = combined.sort_values(
        ["Building Type", "Run Type", "System Type", "Climate Zone"]
    ).reset_index(drop=True)
    for c in ["Building Type", "Run Type", "System Type", "Climate Zone"]:
        combined[c] = combined[c].astype(str)
    return combined


def write_output(combined, header_line, out_path):
    """Write with the same column layout as the original: 10 real data columns
    followed by 4 blank trailing columns, CRLF line endings."""
    with open(out_path, "w", newline="") as f:
        f.write(header_line)
        for _, row in combined.iterrows():
            vals = [
                row["Building Type"], row["Run Type"], row["Climate Zone"], row["System Type"],
                row["Heating Gas Energy"], row["Heating Electricity Energy"], row["Cooling Energy"],
                row["Heating Gas Total Energy"], row["Heating Electricity Total Energy"],
                row["Cooling Total Energy"],
            ]
            f.write(",".join(str(v) for v in vals) + ",,,,\r\n")


def main():
    bt_order, header_line = load_original_ordering(ORIGINAL_CSV)
    combined = load_hourly_results(HOURLY_RESULTS_DIR)
    combined = add_placeholder_building_type(
        combined, PLACEHOLDER_BLDG_TYPE, PLACEHOLDER_SOURCE_BLDG_TYPE
    )
    combined = sort_like_original(combined, bt_order)
    write_output(combined, header_line, OUTPUT_CSV)
    print(f"Wrote {len(combined)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
