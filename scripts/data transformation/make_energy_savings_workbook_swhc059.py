"""Build SWHC059_Energy_Savings_Calculations_<date>.xlsx in the eTRM layout.

Follows the SWSV014 (refrigerant management, residential) workbook Robert
received, with the same fourteen sheets and the same formula structure:

    Readme
    Measure_Offerings
    All_UEC                      per-SF unit energy consumption, by TechID x CZ
    UECBase / UECMeas            one row per offering x BldgHVAC x BldgType x CZ
    Savings = UECBase - UECMeas
    UECBase_cool / UECMeas_cool  eTRM upload format
    UECBase_heat / UECMeas_heat  eTRM upload format
    simdata_weighted SFm 1975-1985 / MFm / DMo
    NumStor

Two deliberate differences from the SWSV014 workbook:

 1. Self-contained. The SWSV014 file's UEC sheets point at an external workbook
    ([1]All_UEC), so the values do not resolve on their own. Here All_UEC carries
    its own lookup key and floor-area columns and every formula is local.
 2. No refrigerant column. SWSV014 permuted on refrigerant; SWHC059 does not.

Everything numeric is a live Excel formula chained back to the simdata sheets,
so Robert can trace any value to the simulation row it came from.

Usage:
    python make_energy_savings_workbook_swhc059.py
"""
import glob
import os
from datetime import date

import openpyxl
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
MEASURE_DIR = os.path.join(REPO, "residential measures", "SWHC059 SFC")
OUT_DIR = os.path.join(REPO, "eTRM deliverables")
OUT = os.path.join(OUT_DIR, f"SWHC059_Energy_Savings_Calculations_{date.today():%Y%m%d}.xlsx")

# simdata sheet name -> source csv(s). SFm uses the story-weighted variant.
SIMDATA_SHEETS = {
    "simdata_weighted SFm 1975-1985": [
        os.path.join(MEASURE_DIR, "SWHC059 SFC AC HP_SFm_1975", "simdata_weighted.csv"),
        os.path.join(MEASURE_DIR, "SWHC059 SFC AC HP_SFm_1985", "simdata_weighted.csv"),
    ],
    "simdata_weighted MFm": [os.path.join(MEASURE_DIR, "SWHC059 SFC AC HP_MFm_Ex", "simdata.csv")],
    "simdata_weighted DMo": [os.path.join(MEASURE_DIR, "SWHC059 SFC AC HP _DMo_Ex", "simdata.csv")],
}

# Offerings, descriptions and base/measure TechIDs come straight from the COP inputs
# workbook (sheet 'SWSV059 Cases COP Inputs'), the same source
# build_cases_from_cop_inputs.py writes the Modelkit cases files from. Offering C
# (controller paired with a smart communicating thermostat) carries the same COP
# inputs and TechIDs as A there, so its rows resolve to A's simulations.
COP_WORKBOOK = sorted(f for f in glob.glob(os.path.join(HERE, "SWHC059_Cases_COP_inputs_*.xlsx"))
                      if not os.path.basename(f).startswith("~"))
if not COP_WORKBOOK:
    raise SystemExit(f"no SWHC059_Cases_COP_inputs_*.xlsx next to this script in {HERE}")
COP_WORKBOOK = COP_WORKBOOK[-1]          # latest date stamp
COP_SHEET = "SWSV059 Cases COP Inputs"
# installation descriptor per offering, as the eTRM sheets label it
INSTALL = {"A": "SFC AOE", "C": "SFC with SCT AOE"}


def load_offerings(path=COP_WORKBOOK):
    """[{offering, hvac, desc, meas, pre}] in workbook order, from the COP inputs sheet."""
    ws = openpyxl.load_workbook(path, data_only=True, read_only=True)[COP_SHEET]
    rows = list(ws.iter_rows(values_only=True))
    hdr_i = next(i for i, r in enumerate(rows) if r and r[0] == "Building HVAC")
    hdr = {str(v).strip(): j for j, v in enumerate(rows[hdr_i]) if v is not None}

    def col(start):
        hits = [j for h, j in hdr.items() if h.startswith(start)]
        if len(hits) != 1:
            raise SystemExit(f"column starting {start!r} not found once in {COP_SHEET!r}")
        return hits[0]

    c_hvac, c_off, c_desc = col("Building HVAC"), col("Statewide Measure Offering ID"), \
        col("Measure Offering Description")
    c_meas, c_pre = col("techId__measTechID"), col("techId__preTechID")
    out = []
    for r in rows[hdr_i + 1:]:
        if not r or r[c_hvac] is None:
            break
        out.append(dict(offering=str(r[c_off]).strip(), hvac=str(r[c_hvac]).strip(),
                        desc=str(r[c_desc]).strip(), meas=str(r[c_meas]).strip(),
                        pre=str(r[c_pre]).strip()))
    return out


OFFER_ROWS = load_offerings()
OFFERING_IDS = list(dict.fromkeys(r["offering"] for r in OFFER_ROWS))
TECHIDS = {(r["offering"], r["hvac"]): r for r in OFFER_ROWS}
# which HVAC types each building type actually simulates
BLDG_HVAC = {
    "DMo": ["rDXGF", "rDXHP", "rNCGF"],
    "MFm": ["rDXGF", "rDXHP", "rNCGF", "rDXHW", "rDXWP", "rDXEF"],
    "SFm": ["rDXGF", "rDXHP", "rNCGF"],
}
CZS = [f"CZ{i:02d}" for i in range(1, 17)]
M2_PER_FT2 = 0.0929
BLDGTYPE_SHEET = {"SFm": "simdata_weighted SFm 1975-1985",
                  "MFm": "simdata_weighted MFm", "DMo": "simdata_weighted DMo"}

HDR_FONT = Font(bold=True, color="FFFFFFFF")
HDR_FILL = PatternFill("solid", fgColor="FF997950")
BOLD = Font(bold=True)
thin = Side(style="thin")
HDR_BORDER = Border(top=thin, bottom=thin)
FILL_BASE = PatternFill("solid", fgColor="FFDDEBF7")
FILL_MEAS = PatternFill("solid", fgColor="FFE2EFDA")
FILL_SAVE = PatternFill("solid", fgColor="FFFFF2CC")
NOTE_FILL = PatternFill("solid", fgColor="FFFFFFCC")


def write_header(ws, headers, fills=None):
    for i, h in enumerate(headers, start=1):
        c = ws.cell(row=1, column=i, value=h)
        c.font = HDR_FONT
        c.fill = (fills or {}).get(i, HDR_FILL)
        c.border = HDR_BORDER
        c.alignment = Alignment(wrap_text=True, vertical="bottom")
    ws.freeze_panes = "A2"


def autosize(ws, maxw=42):
    for col in ws.columns:
        letter = get_column_letter(col[0].column)
        width = max((len(str(c.value)) for c in col[:60] if c.value is not None), default=10)
        ws.column_dimensions[letter].width = min(max(width + 2, 10), maxw)


def add_simdata_sheets(wb):
    """Raw simulation data, one sheet per building type. Column order is
    result2.py's, which the All_UEC formulas below index by letter."""
    counts = {}
    for sheet, paths in SIMDATA_SHEETS.items():
        df = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
        ws = wb.create_sheet(sheet)
        write_header(ws, list(df.columns))
        for row in df.itertuples(index=False):
            ws.append(list(row))
        autosize(ws, maxw=28)
        counts[sheet] = len(df)
    return counts


def add_all_uec(wb, counts):
    """Per-square-foot UEC, as live formulas into the simdata sheets.

    Column letters on the simdata sheets: I TechID, B BldgLoc, C BldgType,
    E BldgHVAC, F BldgVint, W Fans, AE Heating Elec, AF Cooling Elec,
    AG Heating NG, AM Conditioned Area (m2), AN DEER peak (J, hourly average).
    """
    ws = wb.create_sheet("All_UEC")
    headers = ["TechID", "BldgLoc", "BldgType", "BldgHVAC", "VintYear",
               "Cooling Elec (kWh/SF)", "Heating Elec (kWh/SF)", "Fans (kWh/SF)",
               "Heating NG (therm/SF)", "Cooling NG (Therm/SF)", "DEER Peak kW/SF",
               "Run", "", "Key", "Floor Area (SF)"]
    write_header(ws, headers)
    r = 2
    for sheet in SIMDATA_SHEETS:
        q = f"'{sheet}'"
        for s in range(2, counts[sheet] + 2):
            area = f"({q}!$AM{s}/{M2_PER_FT2})"          # m2 -> ft2
            ws.cell(row=r, column=1, value=f"={q}!I{s}")
            ws.cell(row=r, column=2, value=f"={q}!B{s}")
            ws.cell(row=r, column=3, value=f"={q}!C{s}")
            ws.cell(row=r, column=4, value=f"={q}!E{s}")
            ws.cell(row=r, column=5, value=f"={q}!F{s}")
            ws.cell(row=r, column=6, value=f"={q}!AF{s}/{area}")
            ws.cell(row=r, column=7, value=f"={q}!AE{s}/{area}")
            ws.cell(row=r, column=8, value=f"={q}!W{s}/{area}")
            # kWh -> therm: x 3412 Btu/kWh / 100,000 Btu/therm
            ws.cell(row=r, column=9, value=f"={q}!AG{s}*3412/100000/{area}")
            ws.cell(row=r, column=10, value=0)            # no gas cooling in these prototypes
            # DEER peak: J/h -> kW is x 2.77778e-7
            ws.cell(row=r, column=11, value=f"={q}!AN{s}*0.000000277778/{area}")
            ws.cell(row=r, column=12, value=f"={q}!A{s}")
            # TechID|BldgType|BldgLoc. BldgType is essential: DEER TechIDs describe the
            # equipment, not the building, so the same TechID appears under SFm, MFm and
            # DMo. Keying on TechID|BldgLoc alone collides and MATCH silently returns
            # whichever building type happens to sit first in the sheet.
            ws.cell(row=r, column=14, value=f'=A{r}&"|"&C{r}&"|"&B{r}')
            ws.cell(row=r, column=15, value=f"={q}!$AM{s}/{M2_PER_FT2}")
            r += 1
    autosize(ws)
    return r - 2


def permutations():
    """One row per offering x building type x HVAC x climate zone."""
    for oid in OFFERING_IDS:
        for bt in ("SFm", "MFm", "DMo"):
            for hv in BLDG_HVAC[bt]:
                if (oid, hv) not in TECHIDS:
                    raise SystemExit(f"offering {oid} has no {hv} row in {COP_SHEET!r} of {COP_WORKBOOK}")
                row = TECHIDS[(oid, hv)]
                for cz in CZS:
                    yield dict(key=f"{oid}-{hv}-{bt}-{cz}", offering=oid,
                               instal=INSTALL.get(oid, oid), desc=row["desc"], bt=bt, hv=hv,
                               cz=cz, meas=row["meas"], pre=row["pre"])


def lookup(col_letter, techid_cell, bldgtype_cell, cz_cell):
    """INDEX/MATCH into All_UEC on the TechID|BldgType|BldgLoc key."""
    return (f'=IFERROR(INDEX(All_UEC!${col_letter}:${col_letter},'
            f'MATCH(${techid_cell}&"|"&${bldgtype_cell}&"|"&${cz_cell},All_UEC!$N:$N,0)),"")')


def add_uec_sheet(wb, name, techid_col, fill):
    """UECBase / UECMeas: the permutation grid with per-SF values pulled from All_UEC."""
    ws = wb.create_sheet(name)
    label = "TechID (Base)" if techid_col == "pre" else "TechID (Measure)"
    headers = ["Key", "Offering ID", label, "BldgLoc", "BldgType", "BldgHVAC", "VintYear",
               "Cooling Elec (kWh/SF)", "Heating Elec (kWh/SF)", "Fans (kWh/SF)",
               "Heating NG (therm/SF)", "Cooling NG (Therm/SF)", "DEER Peak kW/SF"]
    write_header(ws, headers, fills={i: fill for i in range(8, 14)})
    for r, p in enumerate(permutations(), start=2):
        ws.cell(row=r, column=1, value=p["key"])
        ws.cell(row=r, column=2, value=p["offering"])
        ws.cell(row=r, column=3, value=p[techid_col])
        ws.cell(row=r, column=4, value=p["cz"])
        ws.cell(row=r, column=5, value=p["bt"])
        ws.cell(row=r, column=6, value=p["hv"])
        ws.cell(row=r, column=7, value="Ex")
        for i, col in enumerate("FGHIJK"):
            ws.cell(row=r, column=8 + i, value=lookup(col, f"C{r}", f"E{r}", f"D{r}"))
    autosize(ws)
    return ws.max_row


def add_savings(wb, nrows):
    ws = wb.create_sheet("Savings = UECBase - UECMeas")
    metrics = ["Cooling Elec (kWh/SF)", "Heating Elec (kWh/SF)", "Fans (kWh/SF)",
               "Heating NG (therm/SF)", "Cooling NG (Therm/SF)", "DEER Peak kW/SF"]
    headers = (["Key", "Offering ID", "TechID (Measure)", "BldgLoc", "BldgType", "BldgHVAC"]
               + [f"Base {m}" for m in metrics] + [f"Meas {m}" for m in metrics]
               + [f"Savings {m}" for m in metrics]
               + [f"Pct Savings {m.split(' (')[0]}" for m in metrics])
    fills = {}
    for i in range(7, 13):
        fills[i] = FILL_BASE
    for i in range(13, 19):
        fills[i] = FILL_MEAS
    for i in range(19, 31):
        fills[i] = FILL_SAVE
    write_header(ws, headers, fills)
    for r in range(2, nrows + 1):
        ws.cell(row=r, column=1, value=f"=UECBase!A{r}")
        ws.cell(row=r, column=2, value=f"=UECBase!B{r}")
        ws.cell(row=r, column=3, value=f"=UECMeas!C{r}")
        ws.cell(row=r, column=4, value=f"=UECBase!D{r}")
        ws.cell(row=r, column=5, value=f"=UECBase!E{r}")
        ws.cell(row=r, column=6, value=f"=UECBase!F{r}")
        for i in range(6):                                  # base H..M  <- UECBase H..M
            ws.cell(row=r, column=7 + i, value=f"=UECBase!{get_column_letter(8+i)}{r}")
            ws.cell(row=r, column=13 + i, value=f"=UECMeas!{get_column_letter(8+i)}{r}")
            b, m = get_column_letter(7 + i), get_column_letter(13 + i)
            ws.cell(row=r, column=19 + i, value=f"={b}{r}-{m}{r}")
            s = get_column_letter(19 + i)
            ws.cell(row=r, column=25 + i,
                    value=f'=IF(AND(ISNUMBER({b}{r}),{b}{r}<>0),{s}{r}/{b}{r},"")')
        for i in range(6):
            ws.cell(row=r, column=25 + i).number_format = "0.0%"
    autosize(ws)


def add_etrm_sheet(wb, name, techid_col, enduse):
    """eTRM upload format: whole-building annual values, per-SF x floor area.

    cool sheets carry kW / kWh / therm for the cooling end use; heat sheets
    carry heating. kW is zero on the heating sheets, matching SWSV014.
    """
    ws = wb.create_sheet(name)
    stub = name.split("__")[0]
    headers = ["SWHC059__BldgHVAC", "SWHC059__instal", "SWHC059__BldgType", "SWHC059__BldgLoc",
               f"{name}__measTechID", f"{name}__YrkW", f"{name}__YrkWh", f"{name}__YrTherm"]
    write_header(ws, headers)
    area = 'INDEX(All_UEC!$O:$O,MATCH($E{r}&"|"&$C{r}&"|"&$D{r},All_UEC!$N:$N,0))'
    for r, p in enumerate(permutations(), start=2):
        ws.cell(row=r, column=1, value=p["hv"])
        ws.cell(row=r, column=2, value=p["instal"])
        ws.cell(row=r, column=3, value=p["bt"])
        ws.cell(row=r, column=4, value=p["cz"])
        ws.cell(row=r, column=5, value=p[techid_col])
        a = area.format(r=r)

        def whole(col):
            return (f'=IFERROR(INDEX(All_UEC!${col}:${col},'
                    f'MATCH($E{r}&"|"&$C{r}&"|"&$D{r},All_UEC!$N:$N,0))*{a},"")')

        if enduse == "cool":
            ws.cell(row=r, column=6, value=whole("K"))     # DEER peak kW
            ws.cell(row=r, column=7, value=whole("F"))     # cooling kWh
            ws.cell(row=r, column=8, value=whole("J"))     # cooling therms (zero)
        else:
            ws.cell(row=r, column=6, value=0)
            ws.cell(row=r, column=7, value=whole("G"))     # heating elec kWh
            ws.cell(row=r, column=8, value=whole("I"))     # heating therms
    autosize(ws)


def add_measure_offerings(wb):
    ws = wb.create_sheet("Measure_Offerings")
    write_header(ws, ["Statewide Measure Offering ID", "BldgHVAC", "Installation",
                      "Measure Offering Description", "techId__measTechID",
                      "techId__preTechID", "techId__stdTechID"])
    for row in OFFER_ROWS:
        ws.append([row["offering"], row["hvac"], INSTALL.get(row["offering"], row["offering"]),
                   row["desc"], row["meas"], row["pre"], None])
    autosize(ws)


def add_numstor(wb):
    ws = wb.create_sheet("NumStor")
    src = pd.read_excel(os.path.join(HERE, "NumStor2.xlsx"), sheet_name="NumStor")
    write_header(ws, list(src.columns))
    for row in src.itertuples(index=False):
        ws.append(list(row))
    autosize(ws)
    return len(src)


def add_readme(wb, stats):
    ws = wb.create_sheet("Readme", 0)
    ws["A1"] = "SWHC059 Energy Savings Calculations"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = "Date:"
    ws["B2"] = f"{date.today():%Y%m%d}"
    ws["A2"].font = BOLD
    lines = [
        ("Readme", "This sheet."),
        ("Measure_Offerings", "Offering IDs, installation descriptors and the base and measure "
                              "TechIDs, from SWHC059_Cases_COP_inputs."),
        ("All_UEC", "Converts the simdata sheets to Unit Energy Consumption per square foot of "
                    "conditioned floor area. Column N is the TechID|BldgLoc lookup key and column "
                    "O the floor area in SF; the UEC sheets index into both."),
        ("UECBase", "Base-case UEC per SF, one row per offering, HVAC type, building type and "
                    "climate zone."),
        ("UECMeas", "Measure-case UEC per SF, same permutations."),
        ("Savings = UECBase - UECMeas", "Base, measure, absolute savings and percent savings."),
        ("UECBase_cool", "Base cooling values, whole building, formatted for eTRM upload as csv."),
        ("UECMeas_cool", "Measure cooling values, whole building, formatted for eTRM upload."),
        ("UECBase_heat", "Base heating values, whole building, formatted for eTRM upload."),
        ("UECMeas_heat", "Measure heating values, whole building, formatted for eTRM upload."),
        ("simdata_weighted SFm 1975-1985",
         "result2.py simdata for SFm, with the 1-story and 2-story models blended by the NumStor "
         "weighting: weighted = story1 x (2 - numstor) + story2 x (numstor - 1)."),
        ("simdata_weighted MFm", "result2.py simdata for MFm. No story weighting applies."),
        ("simdata_weighted DMo", "result2.py simdata for DMo. No story weighting applies."),
        ("NumStor", "Story counts and weights by building type, vintage and climate zone."),
    ]
    r = 4
    for name, desc in lines:
        ws.cell(row=r, column=2, value=name).font = BOLD
        ws.cell(row=r, column=3, value=desc).alignment = Alignment(wrap_text=True, vertical="top")
        r += 1
    r += 1
    ws.cell(row=r, column=2, value="Notes").font = BOLD
    r += 1
    notes = [
        "Every numeric cell is a live formula chained back to the simdata sheets, so any value "
        "can be traced to the simulation run it came from.",
        "Unit conversions: floor area m2 to SF divides by 0.0929; gas kWh to therms multiplies by "
        "3412 and divides by 100,000; the DEER peak converts from J per hour to kW by 2.77778e-7.",
        "DEER peak days are the CZ2025 assessment values, matching the CZ2025 weather the models "
        "were run on.",
        f"Offerings, descriptions and TechIDs are read from {os.path.basename(COP_WORKBOOK)} "
        f"(sheet '{COP_SHEET}'), the same workbook the Modelkit cases files are generated from. "
        "Offering C (controller with a smart communicating thermostat) carries the same COP inputs "
        "and TechIDs as offering A there, so its rows resolve to offering A's simulations. "
        "CONFIRM this is intended before upload.",
        "Cooling NG is zero throughout: none of these prototypes have gas cooling.",
        "The no-cooling gas furnace cohort (rNCGF) logged EnergyPlus warmup convergence errors in "
        "every vintage, worst on MFm. Those runs completed but their zone temperatures did not "
        "fully settle, so treat rNCGF rows with more caution than the rest.",
    ]
    for n in notes:
        c = ws.cell(row=r, column=3, value=n)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        c.fill = NOTE_FILL
        r += 1
    r += 1
    ws.cell(row=r, column=2, value="Row counts").font = BOLD
    r += 1
    for k, v in stats.items():
        ws.cell(row=r, column=3, value=f"{k}: {v}")
        r += 1
    ws.column_dimensions["B"].width = 32
    ws.column_dimensions["C"].width = 110


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    wb = Workbook()
    wb.remove(wb.active)

    add_measure_offerings(wb)
    counts = add_simdata_sheets(wb)
    n_uec = add_all_uec(wb, counts)
    nrows = add_uec_sheet(wb, "UECBase", "pre", FILL_BASE)
    add_uec_sheet(wb, "UECMeas", "meas", FILL_MEAS)
    add_savings(wb, nrows)
    add_etrm_sheet(wb, "UECBase_cool", "pre", "cool")
    add_etrm_sheet(wb, "UECMeas_cool", "meas", "cool")
    add_etrm_sheet(wb, "UECBase_heat", "pre", "heat")
    add_etrm_sheet(wb, "UECMeas_heat", "meas", "heat")
    n_numstor = add_numstor(wb)

    stats = {"All_UEC rows": n_uec, "permutation rows per UEC sheet": nrows - 1,
             "NumStor rows": n_numstor}
    stats.update({s: f"{c} rows" for s, c in counts.items()})
    add_readme(wb, stats)

    # Readme first, then the order SWSV014 used
    order = ["Readme", "Measure_Offerings", "All_UEC", "UECBase", "UECMeas",
             "Savings = UECBase - UECMeas", "UECBase_cool", "UECMeas_cool",
             "UECBase_heat", "UECMeas_heat", "simdata_weighted SFm 1975-1985",
             "simdata_weighted MFm", "simdata_weighted DMo", "NumStor"]
    wb._sheets = [wb[s] for s in order]
    wb.save(OUT)
    print(f"wrote {OUT}")
    for k, v in stats.items():
        print(f"   {k}: {v}")


if __name__ == "__main__":
    main()
