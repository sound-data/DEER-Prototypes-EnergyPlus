"""Generate (or check) the SWHC059 Modelkit cases files from SWHC059_Cases_COP_inputs.

The sheet 'SWSV059 Cases COP Inputs' in SWHC059_Cases_COP_inputs_<date>.xlsx is the
source of truth for the cooling COP, the heating COP or furnace efficiency, and the
base (NoSFC) and measure (SFC) TechIDs of every HVAC type. This script lays those
values into the per-cohort cases CSVs under each vintage folder of the measure, so
every simulation input traces back to one cell in that workbook.

What the workbook does NOT decide is the folder layout, which is the repo's:
    DMo        one cohort per HVAC type: rDXGF, rDXHP, rNCGF
    MFm        rDXHW rides in the rDXGF cohort; rDXWP and rDXEF ride in the rDXHP cohort
    SFm        the same three cohorts, repeated for 1-story (SFm&1) and 2-story (SFm&2)
               and for both vintage folders (1975, 1985)

Offering C (SFC with a smart communicating thermostat) carries the same COPs and
TechIDs as offering A in the workbook, so only offering A rows feed the cases files;
the script warns if the two offerings ever diverge.

Usage:
    python build_cases_from_cop_inputs.py              # write the cases files
    python build_cases_from_cop_inputs.py --check      # compare with what is on disk, write nothing
    python build_cases_from_cop_inputs.py --workbook "path/to/SWHC059_Cases_COP_inputs_YYYYMMDD.xlsx"
"""
import argparse
import csv
import glob
import os
import sys

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
MEASURE_DIR = os.path.join(REPO, "residential measures", "SWHC059 SFC")
COP_SHEET = "SWSV059 Cases COP Inputs"
CASES_HEADER = ["skip", "case_name", ":vfd_curve_name", ":supplyfan_total_eff", ":motor_eff",
                ":cooling_coil_cop", ":cooling_coil_cop2", ":coil_type", ":hvac_type",
                ":heating_coil_cop", ":burner_eff"]

# Constants shared by every SWHC059 case (fan and motor efficiency, unitary system).
SUPPLYFAN_TOTAL_EFF = "0.12"
MOTOR_EFF = "0.24"
HVAC_TYPE = "unitary_system"

# Where the workbook's "Heat ... COP or Efficiency" lands: gas furnace and hydronic
# systems take a burner efficiency, heat pumps and electric furnaces a heating COP.
BURNER_EFF_HVACS = {"rDXGF", "rNCGF", "rDXHW"}

# vintage folder -> (BldgType, [story flags])
VINTAGES = {
    "SWHC059 SFC AC HP _DMo_Ex": ("DMo", ["0"]),
    "SWHC059 SFC AC HP_MFm_Ex": ("MFm", ["0"]),
    "SWHC059 SFC AC HP_SFm_1975": ("SFm", ["1", "2"]),
    "SWHC059 SFC AC HP_SFm_1985": ("SFm", ["1", "2"]),
}
# BldgType -> {cohort HVAC: [HVAC rows in that cohort's cases file]}
COHORT_HVACS = {
    "DMo": {"rDXGF": ["rDXGF"], "rDXHP": ["rDXHP"], "rNCGF": ["rNCGF"]},
    "MFm": {"rDXGF": ["rDXGF", "rDXHW"], "rDXHP": ["rDXHP", "rDXWP", "rDXEF"], "rNCGF": ["rNCGF"]},
    "SFm": {"rDXGF": ["rDXGF"], "rDXHP": ["rDXHP"], "rNCGF": ["rNCGF"]},
}
COHORT_SUFFIX = {"rDXGF": "dxAC_equip", "rDXHP": "dxHP_equip", "rNCGF": "SpaceHtg_eq"}

NUMERIC = ("cool_base", "cool_meas", "heat_base", "heat_meas")


def default_workbook():
    hits = sorted(glob.glob(os.path.join(HERE, "SWHC059_Cases_COP_inputs_*.xlsx")))
    hits = [h for h in hits if not os.path.basename(h).startswith("~")]
    if not hits:
        raise SystemExit(f"no SWHC059_Cases_COP_inputs_*.xlsx next to this script in {HERE}")
    return hits[-1]       # the latest date stamp


def fmt(value):
    """Workbook floats as the cases files carry them: at most nine decimals, no
    trailing noise (1.7117499999999999 -> 1.71175, 1.0 -> 1), blank for None."""
    if value is None or value == "":
        return ""
    x = round(float(value), 9)
    return str(int(x)) if x == int(x) else repr(x)


def read_cop_inputs(path):
    """{hvac: {offering: {cool_base, cool_meas, heat_base, heat_meas, meas_id, pre_id, desc}}}"""
    ws = openpyxl.load_workbook(path, data_only=True, read_only=True)[COP_SHEET]
    rows = list(ws.iter_rows(values_only=True))
    hdr_i = next(i for i, r in enumerate(rows) if r and r[0] == "Building HVAC")
    hdr = {str(v).strip(): j for j, v in enumerate(rows[hdr_i]) if v is not None}

    def col(name_start):
        hits = [j for h, j in hdr.items() if h.startswith(name_start)]
        if len(hits) != 1:
            raise SystemExit(f"column starting {name_start!r} not found once in {COP_SHEET!r}: {hits}")
        return hits[0]

    c = {
        "hvac": col("Building HVAC"), "offering": col("Statewide Measure Offering ID"),
        "desc": col("Measure Offering Description"),
        "cool_base": col("Cool Base COP"), "cool_meas": col("Cool Measure COP"),
        "heat_base": col("Heat Base COP"), "heat_meas": col("Heat Measure COP"),
        "meas_id": col("techId__measTechID"), "pre_id": col("techId__preTechID"),
    }
    out = {}
    for r in rows[hdr_i + 1:]:
        if not r or r[c["hvac"]] is None:
            break
        rec = {k: r[j] for k, j in c.items()}
        out.setdefault(str(rec["hvac"]).strip(), {})[str(rec["offering"]).strip()] = rec

    # Offering A feeds the cases files; make sure nothing else disagrees with it.
    for hvac, offs in out.items():
        a = offs.get("A")
        if a is None:
            raise SystemExit(f"{hvac}: no offering A row in {COP_SHEET!r}")
        for oid, rec in offs.items():
            for k in NUMERIC + ("meas_id", "pre_id"):
                same = fmt(rec[k]) == fmt(a[k]) if k in NUMERIC else rec[k] == a[k]
                if not same:
                    print(f"WARNING: {hvac} offering {oid} {k} differs from offering A "
                          f"({rec[k]!r} vs {a[k]!r}); cases files follow offering A", flush=True)
    return out


def case_rows(hvac, rec):
    """The NoSFC (base) row then the SFC (measure) row for one HVAC type."""
    rows = []
    for tech_id, cool, heat in ((rec["pre_id"], rec["cool_base"], rec["heat_base"]),
                                (rec["meas_id"], rec["cool_meas"], rec["heat_meas"])):
        heating_cop, burner_eff = ("", fmt(heat)) if hvac in BURNER_EFF_HVACS else (fmt(heat), "")
        rows.append(["", str(tech_id).strip(), "", SUPPLYFAN_TOTAL_EFF, MOTOR_EFF, fmt(cool), "", "",
                     HVAC_TYPE, heating_cop, burner_eff])
    return rows


def expected_files(cop):
    """{vintage folder: {cases file name: [rows]}}"""
    out = {}
    for folder, (bt, stories) in VINTAGES.items():
        files = {}
        for story in stories:
            for cohort_hvac, hvacs in COHORT_HVACS[bt].items():
                name = f"{bt}&{story}&{cohort_hvac}&Ex&{COHORT_SUFFIX[cohort_hvac]}.csv"
                rows = []
                for hvac in hvacs:
                    if hvac not in cop:
                        raise SystemExit(f"{hvac} is not in {COP_SHEET!r}")
                    rows.extend(case_rows(hvac, cop[hvac]["A"]))
                files[name] = rows
        out[folder] = files
    return out


def read_cases(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = [r for r in csv.reader(f) if any(c.strip() for c in r)]
    return rows[0], rows[1:]


def check(expected):
    problems = 0
    for folder, files in expected.items():
        cdir = os.path.join(MEASURE_DIR, folder, "cases")
        on_disk = {os.path.basename(p) for p in glob.glob(os.path.join(cdir, "*.csv"))}
        for extra in sorted(on_disk - set(files)):
            print(f"EXTRA    {folder}/cases/{extra}  (not generated from the workbook)")
            problems += 1
        for name, rows in files.items():
            path = os.path.join(cdir, name)
            if not os.path.isfile(path):
                print(f"MISSING  {folder}/cases/{name}")
                problems += 1
                continue
            hdr, got = read_cases(path)
            if hdr != CASES_HEADER:
                print(f"HEADER   {folder}/cases/{name}: {hdr}")
                problems += 1
            if got != rows:
                problems += 1
                print(f"DIFFERS  {folder}/cases/{name}")
                for i in range(max(len(got), len(rows))):
                    g = got[i] if i < len(got) else None
                    e = rows[i] if i < len(rows) else None
                    if g != e:
                        print(f"           on disk : {g}")
                        print(f"           workbook: {e}")
    print("cases files match the COP inputs workbook" if not problems
          else f"{problems} difference(s) between the cases files and the COP inputs workbook")
    return problems


def write(expected):
    n = 0
    for folder, files in expected.items():
        cdir = os.path.join(MEASURE_DIR, folder, "cases")
        os.makedirs(cdir, exist_ok=True)
        for stale in glob.glob(os.path.join(cdir, "*.csv")):
            if os.path.basename(stale) not in files:
                os.remove(stale)
                print(f"removed stale {folder}/cases/{os.path.basename(stale)}")
        for name, rows in files.items():
            with open(os.path.join(cdir, name), "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f, lineterminator="\n")
                w.writerow(CASES_HEADER)
                w.writerows(rows)
            n += 1
    print(f"wrote {n} cases files under {MEASURE_DIR}")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--workbook", default=None,
                    help="COP inputs workbook (default: latest next to this script)")
    ap.add_argument("--check", action="store_true",
                    help="compare with the files on disk; write nothing")
    args = ap.parse_args(argv[1:])
    wb = args.workbook or default_workbook()
    print(f"COP inputs: {wb}")
    expected = expected_files(read_cop_inputs(wb))
    if args.check:
        return 1 if check(expected) else 0
    write(expected)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
