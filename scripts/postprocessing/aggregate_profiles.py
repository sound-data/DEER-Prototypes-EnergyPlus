"""Memory-safe replacement for the rakefile's aggregate_profiles.
Replicates its output: column 1 = Date/Time, one column per run
(header = run csv path relative to runs/), values from the first header
matching the requested series; trailing 8760 hourly rows only.

Usage: python aggregate_profiles.py <study_dir>
Writes results-profile-elec.csv and results-profile-gas.csv into study_dir.
"""
import csv, sys
from pathlib import Path

study = Path(sys.argv[1])
runs = study / "runs"
SERIES = {"results-profile-elec.csv": "Electricity:Facility",
          "results-profile-gas.csv": "Gas:Facility"}

paths = sorted(runs.rglob("instance-var.csv"))
print(f"{len(paths)} hourly files")

for outname, match in SERIES.items():
    date_col = None
    cols = []   # (header, list-of-values)
    for p in paths:
        with open(p, newline="") as f:
            reader = csv.reader(f)
            headers = next(reader)
            rows = list(reader)
        rows = rows[-8760:]
        if date_col is None:
            di = headers.index("Date/Time")
            date_col = ["Date/Time"] + [r[di] for r in rows]
        ci = next(i for i, h in enumerate(headers) if match in h)
        short = p.relative_to(runs).as_posix()
        cols.append([short] + [r[ci] for r in rows])
    with open(study / outname, "w", newline="") as f:
        w = csv.writer(f)
        for row in zip(date_col, *cols):
            w.writerow(row)
    print(f"wrote {outname}: {len(cols)} runs x 8760 h")
