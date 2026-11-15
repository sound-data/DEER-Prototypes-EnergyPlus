"""Clean finisher for the 2026-09-15 M3/M5 rerun.

STEP A  Regenerate results-summary.csv for both studies wholesale from each
        run's instance-out.sql, using the 4-table format taken from the intact
        Htl file. GATE: reproduce the intact Htl summary from SQL and require
        it to match the on-disk Htl file (<=0.02 abs) before writing anything.
STEP B  Com per building type -> mfmcmn -> realTechID -> CEDARS-by-CZ ->
        PGE 8760 -> QC (summary/hourly/peak) -> simdata (both studies).
Workbook chain + packaging run afterward (Excel COM step done in PowerShell).
Profiles (results-profile-*.csv) are modelkit artifacts read by nothing
downstream and are left as-is.
"""
import csv
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MEAS_REL = Path("commercial measures") / "SWHC062-03 Occupancy Fan Controller"
EX = REPO / MEAS_REL / "SWHC062-03 Occupancy Fan Controller_Ex"
HTL = REPO / MEAS_REL / "SWHC062-03 Occupancy Fan Controller_Htl_Ex"
PY = str(REPO / r".venv\Scripts\python.exe")
DT = REPO / "scripts" / "data transformation"


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


# query map: output-name -> Report/For/Table/Column/Row
QUERIES = {}
for line in open(EX / "query.txt"):
    line = line.strip()
    if line and "," in line:
        path, name = line.rsplit(",", 1)
        QUERIES[name.strip()] = path.strip().split("/")


def qname(header):
    if header in QUERIES:
        return QUERIES[header]
    if " (" in header:
        return QUERIES.get(header[: header.rindex(" (")])
    return None


def fetch(con, parts):
    report, forstr, table, col, row = parts
    cur = con.execute(
        "SELECT Value FROM TabularDataWithStrings WHERE ReportName=? AND "
        "ReportForString=? AND TableName=? AND ColumnName=? AND RowName=?",
        (report, forstr, table, col, row))
    vals = [r[0] for r in cur.fetchall()]
    if not vals and col == "Total Energy":
        cur = con.execute(
            "SELECT SUM(CAST(Value AS REAL)) FROM TabularDataWithStrings WHERE ReportName=? "
            "AND ReportForString=? AND TableName=? AND RowName=? AND ColumnName NOT LIKE 'Water%'",
            (report, forstr, table, row))
        v = cur.fetchone()[0]
        return float(v) if v is not None else None
    if not vals:
        return None
    try:
        return float(vals[0])
    except ValueError:
        return None


def table_headers():
    """4 (header-col-list) tuples from the intact Htl summary."""
    hdrs = []
    for line in open(HTL / "results-summary.csv", newline="").read().splitlines():
        if line.startswith("File Name,"):
            hdrs.append(next(csv.reader([line])))
    assert len(hdrs) == 4, len(hdrs)
    return hdrs


def gen_rows(study_dir, headers):
    """{filekey: {table_idx: [values]}} for every run under study_dir/runs."""
    runs = study_dir / "runs"
    sqls = sorted(runs.glob("CZ*/*/*/instance-out.sql"))
    result = {}
    for n, sqlp in enumerate(sqls):
        key = sqlp.relative_to(runs).as_posix()
        con = sqlite3.connect(str(sqlp))
        per_table = []
        for hdr in headers:
            vals = []
            for name in hdr[1:]:
                parts = qname(name)
                if parts is None:
                    con.close()
                    raise SystemExit(f"no query for column {name!r}")
                v = fetch(con, parts)
                vals.append(0.0 if v is None else v)
            per_table.append(vals)
        con.close()
        result[key] = per_table
        if (n + 1) % 1500 == 0:
            log(f"  {study_dir.name[-6:]}: {n+1}/{len(sqls)} sql read")
    return result


def write_summary(study_dir, headers, rows):
    key_re = "instance-out.sql"
    lines = []
    for t, hdr in enumerate(headers):
        lines.append(",".join(hdr))
        for key in sorted(rows):
            vals = rows[key][t]
            lines.append(",".join([key] + [f"{v:.2f}" for v in vals]))
    (study_dir / "results-summary.csv").write_text("\r\n".join(lines) + "\r\n", newline="")
    log(f"{study_dir.name[-6:]}: results-summary.csv written ({len(rows)} runs x {len(headers)} tables)")


# ---- STEP A ----
headers = table_headers()
log("validation: regenerating Htl summary from SQL to compare with on-disk file")
htl_gen = gen_rows(HTL, headers)
# parse on-disk Htl values keyed by (table, filekey)
disk = {}
t = -1
for line in open(HTL / "results-summary.csv", newline="").read().splitlines():
    if line.startswith("File Name,"):
        t += 1
        continue
    if not line.strip():
        continue
    row = next(csv.reader([line]))
    disk[(t, row[0])] = row[1:]
mism = 0
for key, per_table in htl_gen.items():
    for t, vals in enumerate(per_table):
        d = disk.get((t, key))
        if d is None:
            log(f"!! disk missing ({t},{key})"); sys.exit(1)
        for a, b in zip(vals, d):
            if abs(a - float(b)) > 0.02:
                mism += 1
                if mism <= 5:
                    log(f"  mismatch ({t},{key}): gen {a:.2f} vs disk {b}")
if mism:
    log(f"!! {mism} value mismatches vs intact Htl file; aborting (generator not trusted)")
    sys.exit(1)
log("validation PASSED: generator reproduces the intact Htl summary exactly")

# write both studies fresh from SQL (Htl included, harmless - identical result)
write_summary(HTL, headers, htl_gen)
log("regenerating _Ex summary from 9600 SQL files")
ex_gen = gen_rows(EX, headers)
write_summary(EX, headers, ex_gen)

# ---- STEP B: postprocessing chain ----
def step(name, args, cwd):
    t0 = time.time()
    r = subprocess.run([PY] + args, cwd=str(cwd), stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    log(f"[{name}] rc={r.returncode} {time.time()-t0:.0f}s | " +
        " / ".join(r.stdout.strip().splitlines()[-1:]))
    if r.returncode != 0:
        print(r.stdout[-2500:], flush=True)
        sys.exit(1)


step("com by bldgtype", ["run_com_by_bldgtype.py"], DT)
step("mfmcmn dupes", ["make_mfmcmn_dupes.py"], DT)
step("fix techid", ["fix_cedars_techid.py"], DT)
step("cedars by cz", [str(REPO / r"scripts\postprocessing\split_cedars_by_cz_swhc062.py")], REPO)
step("pge 8760", ["package_8760_for_pge.py"], DT)
SCR = REPO / MEAS_REL / "scripts"
step("summary QC", [str(SCR / "process_summary_data_multi_measure.py")], SCR)
step("hourly QC", [str(SCR / "process_hourly_data_multi_measure.py")], SCR)
step("deer peak QC", [str(SCR / "process_deer_peak_sql.py")], SCR)
for study in [HTL, EX]:
    step(f"result2 {study.name[-6:]}", [str(REPO / r"scripts\result2.py"), str(study),
                                        "-c", "--queryfile", str(study / "query.txt")], REPO)
    shutil.move(str(REPO / "simdata.csv"), str(study / "simdata.csv"))
log("REGEN+PIPELINE COMPLETE")
