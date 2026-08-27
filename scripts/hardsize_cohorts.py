"""
Repoint SFm 2-story cohorts to the new "| 2 Story" codes tables.

For every residential cohorts.csv whose sibling climates.csv uses
deer-sfm-1975-1985.csv, rewrite ONLY the 5 capacity lookups
(coolCap, coolShr, heatCap, heatPumpHeatCap, airflow) on SFm&2 rows so the
table name becomes "... Climate Zone #{climate_zone} | 2 Story". SFm&1 rows
and all non-capacity lookups are left untouched.
"""
import os, sys

KEYS = ("coolCap", "coolShr", "heatCap", "heatPumpHeatCap", "airflow")
OLD = 'Climate Zone #{{climate_zone}}"", ""{k}'
NEW = 'Climate Zone #{{climate_zone}} | 2 Story"", ""{k}'
CODES_MARKER = "deer-sfm-1975-1985.csv"
DRY = "--dry" in sys.argv

root = "residential measures"
total_files, total_rows = 0, 0
for dirpath, _, files in os.walk(root):
    if "cohorts.csv" not in files:
        continue
    climates = os.path.join(dirpath, "climates.csv")
    if not os.path.exists(climates):
        continue
    with open(climates, encoding="utf-8-sig", errors="replace") as f:
        if CODES_MARKER not in f.read():
            continue  # not an SFm deer-sfm study -> skip (excludes SFm_New, T24-only)
    path = os.path.join(dirpath, "cohorts.csv")
    with open(path, encoding="utf-8-sig", newline="") as f:
        raw = f.read()
    nl = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.split(nl)
    file_rows = 0
    for i, line in enumerate(lines):
        if "SFm&2" not in line:
            continue
        new_line = line
        for k in KEYS:
            new_line = new_line.replace(OLD.format(k=k), NEW.format(k=k))
        if new_line != line:
            lines[i] = new_line
            file_rows += 1
    if file_rows:
        total_files += 1
        total_rows += file_rows
        print(f"{'(dry) ' if DRY else ''}{path}: {file_rows} SFm&2 row(s) repointed")
        if not DRY:
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                f.write(nl.join(lines))

print(f"\n{'DRY RUN ' if DRY else ''}TOTAL: {total_rows} rows across {total_files} files")
