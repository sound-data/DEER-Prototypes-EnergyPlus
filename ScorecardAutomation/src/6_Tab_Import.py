import os
import xlwings as xw
import re

def _require_env(key: str) -> str:
    v = os.environ.get(key)
    if not v or not str(v).strip():
        raise EnvironmentError(
            f"Missing required environment variable '{key}'. "
            f"Run this script via Run3_Scorecard_Generation.py."
        )
    return str(v)


# Template file (input)
template_path = _require_env("SCORECARD_TEMPLATE_PATH")

# Scorecard root folder (outputs)
root_dir = _require_env("SCORECARD_PATH")
raw_files_folder = os.path.join(root_dir, "Tab_from_Raw")
output_dir = os.path.join(root_dir, "Scorecard_by_Prototype")

building_type_map = {
    "Asm": "Assembly", "ECC": "Education - Community College", "EPr": "Education - Primary School",
    "ERC": "Education - Relocatable Classroom", "ESe": "Education - Secondary School",
    "EUn": "Education - University", "Fin": "Financial buildings, incl. banks",
    "Gro": "Grocery", "Hsp": "Health/Medical - Hospital", "Htl": "Lodging - Hotel",
    "Lib": "Libraries", "MBT": "Manufacturing Biotech", "MLI": "Manufacturing Light Industrial",
    "Mtl": "Lodging - Motel", "Nrs": "Health-Medical - Nursing Home", "OfL": "Office - Large",
    "OfS": "Office - Small", "Rel": "Religious assembly buildings", "RFF": "Restaurant - Fast-Food",
    "RSD": "Restaurant - Sit-Down", "Rt3": "Retail - Multistory Large", "RtL": "Retail - Single-Story Large",
    "RtS": "Retail - Small", "SCn": "Storage - Conditioned", "SUn": "Storage - Unconditioned",
    "WRf": "Warehouse - Refrigerated"
}


SCHEDULES_SHEET = "Schedules"
OUT_SHEET = "Schedule_Figures"

ENERGY_SHEET_PREFIX = "Energy Usage"
ENERGY_OUT_SHEET = "Energy Usage_Figures"

HEADER_ROW = 3
DATA_START_ROW = 4

COL_SCHEDULE = 1     # A
COL_SPACE = 2        # B
COL_TYPE = 3         # C

COL_HOUR_START = 5   # E
COL_HOUR_END = 28    # AB


def delete_zero_rows_in_schedules(
    sh: xw.Sheet,
    start_row: int = DATA_START_ROW,
    key_col: int = COL_SCHEDULE,
    scan_limit: int = 5000,
):
    """Deletes rows in 'Schedules' where column A is 0 / 0.0 / '0' / '0.0'."""
    last_row = sh.used_range.last_cell.row
    last_row = min(last_row, start_row + scan_limit)

    vals = sh.range((start_row, key_col), (last_row, key_col)).value
    if not vals:
        return 0

    def is_zero(v):
        return v in (0, 0.0, "0", "0.0")

    rows_to_delete = [r for r, v in enumerate(vals, start=start_row) if is_zero(v)]

    for r in reversed(rows_to_delete):
        sh.api.Rows(r).Delete()

    return len(rows_to_delete)

def clean_special_days_in_notes(
    sh: xw.Sheet,
    end_scan_rows: int = 200,
    name_col: int = 1,          # "Name" column
    n_cols: int = 4,            # Name, Start Date, Duration, Special Day Type
):
    """
    Notes tab:
    Find the 'Special Days' table and delete any data rows where:
      - Name is blank/None, OR
      - Name is 0 / '0' / 0.0 / '0.0', OR
      - All 4 columns are blank/None/0-ish
    """
    title_row = find_row_with_text(
        sh,
        "Special Days",
        search_cols=(1, 2, 3, 4, 5, 6, 7, 8),
        start_row=1,
        scan_limit=5000,
    )
    if not title_row:
        return 0

    header_row = title_row + 1
    data_start = title_row + 2

    used_last = sh.used_range.last_cell.row
    data_end = min(used_last, data_start + end_scan_rows)

    if data_end < data_start:
        return 0

    block = sh.range((data_start, name_col), (data_end, name_col + n_cols - 1)).value
    if not block:
        return 0
    if not isinstance(block, list) or (block and not isinstance(block[0], list)):
        block = [block]

    def is_zeroish(v):
        return v in (0, 0.0, "0", "0.0")

    def is_blankish(v):
        return v is None or (isinstance(v, str) and v.strip() == "")

    rows_to_delete = []
    for i, rowvals in enumerate(block):
        # rowvals: [Name, Start Date, Duration, Special Day Type]
        name_v = rowvals[0] if len(rowvals) > 0 else None

        # delete if Name blank/zero
        delete_row = is_blankish(name_v) or is_zeroish(name_v)

        # OR delete if entire row is blank/zero-ish
        if not delete_row:
            all_empty = True
            for v in rowvals[:n_cols]:
                if not (is_blankish(v) or is_zeroish(v)):
                    all_empty = False
                    break
            delete_row = all_empty

        if delete_row:
            rows_to_delete.append(data_start + i)

    for r in reversed(rows_to_delete):
        sh.api.Rows(r).Delete()

    return len(rows_to_delete)

def delete_rows_after_first_zero_in_colA(
    sh: xw.Sheet,
    start_row: int,
    end_row: int | None = None,
    key_col: int = 1,
    scan_limit: int = 50000
) -> int:
    """Find FIRST row where Column A is 0, delete from that row down to end_row/last used row."""
    used_last = sh.used_range.last_cell.row
    scan_end = used_last if end_row is None else min(used_last, end_row)
    scan_end = min(scan_end, start_row + scan_limit)
    if scan_end < start_row:
        return 0

    vals = sh.range((start_row, key_col), (scan_end, key_col)).value
    if not vals:
        return 0

    def is_zero(v):
        return v in (0, 0.0, "0", "0.0")

    first_zero_row = None
    for i, v in enumerate(vals):
        if is_zero(v):
            first_zero_row = start_row + i
            break

    if first_zero_row is None:
        return 0

    del_end = used_last if end_row is None else min(used_last, end_row)
    if first_zero_row > del_end:
        return 0

    n_deleted = del_end - first_zero_row + 1
    sh.api.Rows(f"{first_zero_row}:{del_end}").Delete()
    return n_deleted


def delete_blank_rows_to_fixed_end(
    sh: xw.Sheet,
    start_row: int,
    end_row: int,
    key_col: int = 1
) -> int:
    """Delete from FIRST blank in Column A down to end_row (inclusive)."""
    vals = sh.range((start_row, key_col), (end_row, key_col)).value
    if not vals:
        return 0

    def is_blank(v):
        return v is None or (isinstance(v, str) and v.strip() == "")

    first_blank = None
    for i, v in enumerate(vals):
        if is_blank(v):
            first_blank = start_row + i
            break

    if first_blank is None:
        return 0

    n = end_row - first_blank + 1
    sh.api.Rows(f"{first_blank}:{end_row}").Delete()
    return n


def apply_all_borders(sh: xw.Sheet, top_row: int, bottom_row: int, left_col: int, right_col: int):
    """Apply full grid borders (outside + inside) to a rectangular range."""
    rng = sh.range((top_row, left_col), (bottom_row, right_col)).api

    xlEdgeLeft = 7
    xlEdgeTop = 8
    xlEdgeBottom = 9
    xlEdgeRight = 10
    xlInsideVertical = 11
    xlInsideHorizontal = 12

    xlContinuous = 1
    xlThin = 2

    for b in (xlEdgeLeft, xlEdgeTop, xlEdgeBottom, xlEdgeRight, xlInsideVertical, xlInsideHorizontal):
        try:
            brd = rng.Borders(b)
            brd.LineStyle = xlContinuous
            brd.Weight = xlThin
        except Exception:
            pass


def find_last_data_row_in_colA(sh: xw.Sheet, start_row: int, stop_row: int | None = None, key_col: int = 1) -> int:
    """Find last row with non-blank value in Column A between start_row and stop_row."""
    used_last = sh.used_range.last_cell.row
    end = used_last if stop_row is None else min(used_last, stop_row)
    if end < start_row:
        return start_row

    vals = sh.range((start_row, key_col), (end, key_col)).value
    if not vals:
        return start_row

    def is_blank(v):
        return v is None or (isinstance(v, str) and v.strip() == "")

    last = start_row - 1
    for i, v in enumerate(vals):
        if not is_blank(v):
            last = start_row + i

    return max(last, start_row)


def apply_thermostat_table_borders(sh: xw.Sheet):
    """Thermostat table borders: A2:S(last data row)."""
    last_data_row = find_last_data_row_in_colA(sh, start_row=3, stop_row=None, key_col=1)
    apply_all_borders(sh, top_row=2, bottom_row=last_data_row, left_col=1, right_col=19)


def delete_rows_where_colA_equals(
    sh: xw.Sheet,
    start_row: int = 3,
    key_col: int = 1,
    target_text: str = "Unknown",
    scan_limit: int = 5000
) -> int:
    """Delete any rows where Column A equals target_text (case-insensitive)."""
    used_last = sh.used_range.last_cell.row
    end = min(used_last, start_row + scan_limit)
    if end < start_row:
        return 0

    vals = sh.range((start_row, key_col), (end, key_col)).value
    if not vals:
        return 0

    tgt = target_text.strip().lower()

    def is_match(v):
        if v is None:
            return False
        return str(v).strip().lower() == tgt

    rows_to_delete = [r for r, v in enumerate(vals, start=start_row) if is_match(v)]
    for r in reversed(rows_to_delete):
        sh.api.Rows(r).Delete()

    return len(rows_to_delete)


def delete_blank_rows_in_colA_to_row(
    sh: xw.Sheet,
    start_row: int,
    end_row: int,
    key_col: int = 1
) -> int:
    """Equipment: delete rows from FIRST blank in Col A within start_row..end_row down to end_row."""
    vals = sh.range((start_row, key_col), (end_row, key_col)).value
    if not vals:
        return 0

    def is_blank(v):
        return v is None or (isinstance(v, str) and v.strip() == "")

    first_blank = None
    for i, v in enumerate(vals):
        if is_blank(v):
            first_blank = start_row + i
            break

    if first_blank is None:
        return 0

    n = end_row - first_blank + 1
    sh.api.Rows(f"{first_blank}:{end_row}").Delete()
    return n


def find_row_with_text(
    sh: xw.Sheet,
    text: str,
    search_cols=(1, 2, 3, 4, 5, 6, 7, 8),
    start_row: int = 1,
    scan_limit: int = 5000
) -> int | None:
    """Return first row index where any cell in search_cols contains `text` (case-insensitive)."""
    used_last = sh.used_range.last_cell.row
    end = min(used_last, start_row + scan_limit)
    t = text.lower()

    for r in range(start_row, end + 1):
        for c in search_cols:
            v = sh.range((r, c)).value
            if v is None:
                continue
            if t in str(v).lower():
                return r
    return None


def delete_rows_from_first_dash_or_zero_in_peak_hot_water(
    sh: xw.Sheet,
    end_row: int = 60,
    space_col: int = 1,  # Column A = "Space"
    scan_limit: int = 5000,
) -> int:
    """
    Water Heater sheet:
    In 'Peak Hot Water Consumption' table, delete from the FIRST row where
    Column A (Space) is '-' OR 0 (or '0') OR blank, down to end_row (inclusive).
    """
    title_row = find_row_with_text(
        sh,
        "Peak Hot Water Consumption",
        search_cols=(1, 2, 3, 4, 5, 6, 7, 8),
        start_row=1,
        scan_limit=scan_limit,
    )
    if not title_row:
        return 0

    data_start = title_row + 2  # title row, header row, then data
    if end_row < data_start:
        return 0

    def is_cutoff(v):
        if v is None:
            return True
        if isinstance(v, str):
            s = v.strip()
            return (s == "" or s == "-" or s == "0" or s == "0.0")
        return v in (0, 0.0)

    first_cut_row = None
    for r in range(data_start, end_row + 1):
        v = sh.range((r, space_col)).value
        if is_cutoff(v):
            first_cut_row = r
            break

    if not first_cut_row:
        return 0

    n = end_row - first_cut_row + 1
    sh.api.Rows(f"{first_cut_row}:{end_row}").Delete()
    return n


def delete_rows_from_first_zero_in_colA_to_row(
    sh: xw.Sheet,
    start_row: int,
    end_row: int,
    key_col: int = 1,
    scan_limit: int = 5000
) -> int:
    """
    Ventilation sheet (Outdoor Airflow Rate table):
    Delete rows from the FIRST row where Column A is 0 / 0.0 / '0' / '0.0'
    within start_row..end_row, down to end_row (inclusive).
    """
    used_last = sh.used_range.last_cell.row
    end_row = min(end_row, used_last)
    end_row = min(end_row, start_row + scan_limit)
    if end_row < start_row:
        return 0

    vals = sh.range((start_row, key_col), (end_row, key_col)).value
    if not vals:
        return 0

    def is_zero(v):
        return v in (0, 0.0, "0", "0.0")

    first_zero = None
    for i, v in enumerate(vals):
        if is_zero(v):
            first_zero = start_row + i
            break

    if first_zero is None:
        return 0

    n = end_row - first_zero + 1
    sh.api.Rows(f"{first_zero}:{end_row}").Delete()
    return n


def build_schedule_figures_from_schedules(
    wb: xw.Book,
    schedules_sheet=SCHEDULES_SHEET,
    out_sheet=OUT_SHEET,
    charts_per_row=1,
    chart_w=950,
    chart_h=420,
    gap_x=20,
    gap_y=30,
):
    """Build charts whose SERIES VALUES reference the Schedules sheet directly."""
    sheet_names = [s.name for s in wb.sheets]
    if schedules_sheet not in sheet_names:
        # print(f"  ! No '{schedules_sheet}' sheet found. Skip Schedule figures.")
        return

    sh_src = wb.sheets[schedules_sheet]

    # Create/clear output sheet (PLACE AFTER Schedules)
    if out_sheet in sheet_names:
        sh_out = wb.sheets[out_sheet]
        sh_out.clear()
    else:
        sh_out = wb.sheets.add(out_sheet, after=wb.sheets[schedules_sheet])

    sh_out.range("A1").value = ["Schedule Figures (linked to Schedules tab)"]

    # Remove existing charts
    for ch in list(sh_out.charts):
        try:
            ch.delete()
        except Exception:
            pass

    last_row = sh_src.used_range.last_cell.row
    if last_row < DATA_START_ROW:
        # print("  ! Schedules sheet has no data rows. Skip.")
        return

    key_vals = sh_src.range((DATA_START_ROW, COL_SCHEDULE), (last_row, COL_TYPE)).value
    if not key_vals:
        # print("  ! No key values read. Skip.")
        return

    group_rows = {}
    for r, rowvals in enumerate(key_vals, start=DATA_START_ROW):
        sched = "" if rowvals[0] is None else str(rowvals[0]).strip()
        space = "" if rowvals[1] is None else str(rowvals[1]).strip()
        typ = "" if rowvals[2] is None else str(rowvals[2]).strip()
        if not sched or not space or not typ:
            continue
        group_rows.setdefault((sched, space), []).append(r)

    if not group_rows:
        # print("  ! No valid groups found. Skip.")
        return

    x_rng = sh_src.range((HEADER_ROW, COL_HOUR_START), (HEADER_ROW, COL_HOUR_END))

    BLACK = 0
    xlCategory = 1
    xlValue = 2
    xlLegendPositionRight = 2

    chart_index = 0
    for (sched, space), rows in group_rows.items():
        row_i = chart_index // charts_per_row
        col_i = chart_index % charts_per_row

        left = sh_out.range("A3").left + col_i * (chart_w + gap_x)
        top = sh_out.range("A3").top + row_i * (chart_h + gap_y)

        chart = sh_out.charts.add(left=left, top=top, width=chart_w, height=chart_h)
        chart.chart_type = "line"
        ch = chart.api[1]

        try:
            while ch.SeriesCollection().Count > 0:
                ch.SeriesCollection(1).Delete()
        except Exception:
            pass

        series_added = 0
        for r in rows:
            type_cell = sh_src.range((r, COL_TYPE))
            y_rng = sh_src.range((r, COL_HOUR_START), (r, COL_HOUR_END))
            y_vals = y_rng.value
            if not y_vals or all(v in (None, 0, 0.0, "") for v in y_vals):
                continue

            s = ch.SeriesCollection().NewSeries()
            s.Name = type_cell.api
            s.XValues = x_rng.api
            s.Values = y_rng.api
            series_added += 1

        if series_added == 0:
            try:
                chart.delete()
            except Exception:
                pass
            continue

        ch.HasTitle = True
        ch.ChartTitle.Text = f"{sched} | {space}"

        try:
            ch.HasLegend = True
            ch.Legend.Position = xlLegendPositionRight
            ch.Legend.Font.Color = BLACK
        except Exception:
            pass

        try:
            ax_x = ch.Axes(xlCategory)
            ax_y = ch.Axes(xlValue)
            ax_x.TickLabels.Font.Color = BLACK
            ax_y.TickLabels.Font.Color = BLACK
            ax_x.HasTitle = True
            ax_x.AxisTitle.Text = "Hour"
            ax_x.AxisTitle.Font.Color = BLACK
            ax_y.HasTitle = True
            ax_y.AxisTitle.Text = "Value"
            ax_y.AxisTitle.Font.Color = BLACK
        except Exception:
            pass

        chart_index += 1

    # print(f"  -> Schedule figures generated on '{out_sheet}' (linked to '{schedules_sheet}').")


def _safe_str(v):
    return "" if v is None else str(v).strip()

def _cz_sort_key(cz: str):
    # "CZ01" -> 1, "CZ16" -> 16 (fallback: keep as string)
    s = _safe_str(cz).upper()
    m = re.search(r"(\d+)", s)
    return int(m.group(1)) if m else 9999


def find_energy_consumption_sheet(wb: xw.Book) -> str | None:
    for s in wb.sheets:
        name = s.name.strip()
        if name.lower().startswith(ENERGY_SHEET_PREFIX.lower()):
            return name
    # fallback: contains text
    for s in wb.sheets:
        if ENERGY_SHEET_PREFIX.lower() in s.name.lower():
            return s.name
    return None


def build_energy_usage_figures(
    wb: xw.Book,
    out_sheet: str = ENERGY_OUT_SHEET,
    charts_per_row: int = 2,
    chart_w: int = 950,
    chart_h: int = 420,
    gap_x: int = 20,
    gap_y: int = 30,
):
    """
    Build Energy usage charts from the 'Energy Consumption - ...' sheet:
      - X axis: Climate Zone
      - Series: Vintage
      - Chart per HVAC Type and per metric (Electric / Gas)
    """
    import re  # ensure available

    src_name = find_energy_consumption_sheet(wb)
    if not src_name:
        return

    sh_src = wb.sheets[src_name]
    sheet_names = [s.name for s in wb.sheets]

    # Create/clear output sheet (place AFTER source)
    if out_sheet in sheet_names:
        sh_out = wb.sheets[out_sheet]
        sh_out.clear()
    else:
        sh_out = wb.sheets.add(out_sheet, after=sh_src)

    # detect header row by finding "Climate Zone" text in columns A:H
    header_row = find_row_with_text(
        sh_src,
        "Climate Zone",
        search_cols=(1, 2, 3, 4, 5, 6, 7, 8),
        start_row=1,
        scan_limit=200,
    )
    if not header_row:
        return
    data_start = header_row + 1

    # Read headers A:H
    headers = sh_src.range((header_row, 1), (header_row, 8)).value
    headers = [ _safe_str(h) for h in headers ]

    def find_col_contains(token: str) -> int | None:
        t = token.lower()
        for i, h in enumerate(headers, start=1):
            if t in h.lower():
                return i
        return None

    col_cz = find_col_contains("climate zone") or 1
    col_hvac = find_col_contains("hvac type") or 2
    col_vintage = find_col_contains("vintage") or 3
    col_elec = find_col_contains("annual electricity intensity")
    col_gas = find_col_contains("annual gas intensity")

    if not col_elec or not col_gas:
        return

    used_last = sh_src.used_range.last_cell.row
    end_row = min(used_last, data_start + 2000)

    data = sh_src.range((data_start, 1), (end_row, 8)).value
    if not data:
        return
    if not isinstance(data[0], list):
        data = [data]

    rows = []
    for r in data:
        cz = _safe_str(r[col_cz - 1])
        if cz == "":
            break
        hvac = _safe_str(r[col_hvac - 1])
        vintage = _safe_str(r[col_vintage - 1])
        elec = r[col_elec - 1]
        gas = r[col_gas - 1]
        if not hvac or not vintage:
            continue
        rows.append((cz, hvac, vintage, elec, gas))

    if not rows:
        return

    hvac_types = sorted({hvac for (_, hvac, _, _, _) in rows})
    vintages = sorted({v for (_, _, v, _, _) in rows})

    # Build lookup: (hvac, vintage, cz) -> (elec, gas)
    lut = {}
    cz_set = set()
    for cz, hvac, vintage, elec, gas in rows:
        cz_set.add(cz)
        lut[(hvac, vintage, cz)] = (elec, gas)

    climate_zones = sorted(list(cz_set), key=_cz_sort_key)

    sh_out.range("A1").value = [f"Energy Figures (from '{src_name}' Tab)"]

    # clean
    for ch in list(sh_out.charts):
        try:
            ch.delete()
        except Exception:
            pass

    # Layout anchors
    cur_top = sh_out.range("A3").top
    left_anchor = sh_out.range("A3").left

    BLACK = 0
    xlCategory = 1
    xlValue = 2
    xlLegendPositionRight = 2

    def make_one_metric_chart(metric_name: str, metric_idx: int, hvac: str, start_cell_row: int, col_offset: int = 0):
        """
        metric_idx: 0 -> elec, 1 -> gas (from lut tuple)
        Writes helper table then charts it.
        Returns (table_height_rows, chart_obj or None)

        col_offset:
        0 = left chart/table
        1 = right chart/table
        """

        # add helper table
        top_row = start_cell_row
        n_vtg = len(vintages)
        block_w = 1 + n_vtg          # Climate Zone + vintages columns
        gap_cols = 2                 # blank columns between left/right helper tables
        col_start = 1 + col_offset * (block_w + gap_cols)   # left starts at A, right starts after block + gap

        # Title + header
        sh_out.range((top_row, col_start)).value = [f"{hvac} | {metric_name}"]
        sh_out.range((top_row + 1, col_start)).value = ["Climate Zone"] + vintages

        # Fill rows
        table_rows = len(climate_zones)
        if table_rows == 0:
            return 0, None

        # Write climate zones
        sh_out.range(
            (top_row + 2, col_start),
            (top_row + 1 + table_rows, col_start)
        ).value = [[cz] for cz in climate_zones]

        # Write metric values for each vintage (to the right of Climate Zone col)
        for j, vtg in enumerate(vintages, start=1):  # 1..n_vtg
            vals = []
            for cz in climate_zones:
                v = lut.get((hvac, vtg, cz))
                vals.append([None if v is None else v[metric_idx]])
            sh_out.range(
                (top_row + 2, col_start + j),
                (top_row + 1 + table_rows, col_start + j)
            ).value = vals

        # hide helper table (font color = white)
        WHITE = 16777215  # Excel RGB white
        table_top = top_row
        table_bottom = top_row + 1 + table_rows  # include header + data
        table_left = col_start
        table_right = col_start + block_w - 1
        try:
            sh_out.range((table_top, table_left), (table_bottom, table_right)).api.Font.Color = WHITE
        except Exception:
            pass

        # make chart
        chart_left = left_anchor + col_offset * (chart_w + gap_x)
        chart_top = sh_out.range((top_row, 1)).top + 5

        chart = sh_out.charts.add(left=chart_left, top=chart_top, width=chart_w, height=chart_h)
        ch = chart.api[1]

        # Column chart
        xlColumnClustered = 51
        ch.ChartType = xlColumnClustered

        try:
            ch.ChartGroups(1).GapWidth = 150
        except Exception:
            pass

        # Clear series
        try:
            while ch.SeriesCollection().Count > 0:
                ch.SeriesCollection(1).Delete()
        except Exception:
            pass

        # X range from helper table climate zone col
        x_rng = sh_out.range(
            (top_row + 2, col_start),
            (top_row + 1 + table_rows, col_start)
        )

        series_added = 0
        for j, vtg in enumerate(vintages, start=1):
            y_rng = sh_out.range(
                (top_row + 2, col_start + j),
                (top_row + 1 + table_rows, col_start + j)
            )

            y_vals = y_rng.value
            flat = [vv[0] if isinstance(vv, list) else vv for vv in (y_vals or [])]
            if not flat or all(vv in (None, "", 0, 0.0) for vv in flat):
                continue

            s = ch.SeriesCollection().NewSeries()
            s.Name = vtg
            s.XValues = x_rng.api
            s.Values = y_rng.api
            series_added += 1

        if series_added == 0:
            try:
                chart.delete()
            except Exception:
                pass
            return (2 + table_rows + 1), None

        ch.HasTitle = True
        ch.ChartTitle.Text = f"{hvac} | {metric_name}"

        try:
            ch.HasLegend = True
            ch.Legend.Position = xlLegendPositionRight
            ch.Legend.Font.Color = BLACK
        except Exception:
            pass

        try:
            ax_x = ch.Axes(xlCategory)
            ax_y = ch.Axes(xlValue)
            ax_x.TickLabels.Font.Color = BLACK
            ax_y.TickLabels.Font.Color = BLACK
            ax_x.HasTitle = True
            ax_x.AxisTitle.Text = "Climate Zone"
            ax_x.AxisTitle.Font.Color = BLACK
            ax_y.HasTitle = True
            ax_y.AxisTitle.Text = metric_name
            ax_y.AxisTitle.Font.Color = BLACK
        except Exception:
            pass

        return (2 + table_rows + 2), chart


    # build charts for each HVAC and energy type
    cur_row = 3
    ROW_GAP = 10  # rows between chart blocks (depends on chart height + table height)

    for hvac in hvac_types:
        # left: Electricity
        h1, _ = make_one_metric_chart(
            "Annual Electricity Intensity (kBtu/ft²)",
            metric_idx=0,
            hvac=hvac,
            start_cell_row=cur_row,
            col_offset=0,
        )

        # right: Gas
        h2, _ = make_one_metric_chart(
            "Annual Gas Intensity (kBtu/ft²)",
            metric_idx=1,
            hvac=hvac,
            start_cell_row=cur_row,
            col_offset=1,
        )

        # move down for next HVAC
        cur_row += max(h1, h2, 2) + ROW_GAP

def activate_prototype_sheet(wb: xw.Book, sheet_name: str = "Prototype"):
    """
    Make sure when user opens the saved workbook, it lands on the Prototype tab.
    - Activates the Prototype sheet
    - Sets it as the first sheet (optional but helps)
    - Sets saved active sheet + top-left cell
    """
    names = [s.name for s in wb.sheets]
    if sheet_name not in names:
        return

    sh = wb.sheets[sheet_name]
    sh.activate()
    try:
        wb.app.api.ActiveWindow.ScrollRow = 1
        wb.app.api.ActiveWindow.ScrollColumn = 1
    except Exception:
        pass

    try:
        sh.api.Move(Before=wb.sheets[0].api)
    except Exception:
        pass


def main():
    os.makedirs(output_dir, exist_ok=True)
    raw_files = [f for f in os.listdir(raw_files_folder) if f.lower().endswith(".xlsx")]

    app = xw.App(visible=False)
    app.display_alerts = False
    app.screen_updating = False

    try:
        for raw_file in raw_files:
            prefix = raw_file.split("_")[0]
            if prefix not in building_type_map:
                continue

            clean_name = (
                building_type_map[prefix]
                .replace(" ", "")
                .replace("-", "")
                .replace("/", "")
                .replace(".", "")
                .replace(",", "")
            )

            new_file_path = os.path.join(output_dir, f"DEER_{clean_name}_ScoreCard.xlsx")
            raw_file_path = os.path.join(raw_files_folder, raw_file)

            print(f"Updating: {clean_name}...")

            wb_template = app.books.open(template_path)
            wb_raw = app.books.open(raw_file_path)

            # Copy each raw sheet into the template
            template_sheet_names = [s.name for s in wb_template.sheets]
            for source_sheet in wb_raw.sheets:
                sheet_name = source_sheet.name
                if sheet_name in template_sheet_names:
                    target_sheet = wb_template.sheets[sheet_name]
                    target_sheet.clear()
                    source_sheet.used_range.copy(target_sheet.range("A1"))

                    # Hide Raw tabs
                    if sheet_name.startswith("Raw_"):
                        target_sheet.api.Visible = 0
                else:
                    # print(f"  ! Warning: Sheet '{sheet_name}' not found in template.")
                    pass

            # HVAC System
            if "HVAC System" in [s.name for s in wb_template.sheets]:
                sh = wb_template.sheets["HVAC System"]
                n = delete_rows_after_first_zero_in_colA(sh, start_row=3, end_row=None)
                # print(f"  -> Deleted {n} trailing rows in 'HVAC System' after first 0 in col A.")

            # Notes: Special Days cleanup
            if "Notes" in [s.name for s in wb_template.sheets]:
                sh_notes = wb_template.sheets["Notes"]
                n_sd = clean_special_days_in_notes(sh_notes)
                # print(f"  -> Deleted {n_sd} blank/zero rows in 'Notes' Special Days table.")

            # Interior Lights
            if "Interior Lights" in [s.name for s in wb_template.sheets]:
                sh = wb_template.sheets["Interior Lights"]
                n = delete_rows_after_first_zero_in_colA(sh, start_row=3, end_row=None)
                # print(f"  -> Deleted {n} trailing rows in 'Interior Lights' after first 0 in col A.")

            # Thermostat
            if "Thermostat" in [s.name for s in wb_template.sheets]:
                sh = wb_template.sheets["Thermostat"]

                # Clean table rows
                n0 = delete_rows_after_first_zero_in_colA(sh, start_row=3, end_row=None)
                if n0:
                    # print(f"  -> Deleted {n0} trailing rows in 'Thermostat' after first 0 in col A.")
                    pass

                n_unknown = delete_rows_where_colA_equals(sh, start_row=3, key_col=1, target_text="Unknown")
                # print(f"  -> Deleted {n_unknown} 'Unknown' rows in 'Thermostat'.")

                # Apply formatting after cleanup
                apply_thermostat_table_borders(sh)
                # print("  -> Applied full borders to Thermostat table (A2:S...).")

            # Zones
            if "Zones" in [s.name for s in wb_template.sheets]:
                sh = wb_template.sheets["Zones"]
                n = delete_blank_rows_to_fixed_end(sh, start_row=3, end_row=69, key_col=1)
                # print(f"  -> Deleted {n} blank trailing rows in 'Zones' (rows 3–69), kept row 70.")

            # Ventilation
            if "Ventilation" in [s.name for s in wb_template.sheets]:
                sh_v = wb_template.sheets["Ventilation"]
                n = delete_rows_from_first_zero_in_colA_to_row(sh_v, start_row=3, end_row=14, key_col=1)
                # print(f"  -> Deleted {n} rows in 'Ventilation' Outdoor Airflow Rate (from first 0 to row 14).")

            # Equipment
            if "Equipment" in [s.name for s in wb_template.sheets]:
                sh = wb_template.sheets["Equipment"]
                n = delete_blank_rows_in_colA_to_row(sh, start_row=3, end_row=15, key_col=1)
                # print(f"  -> Deleted {n} blank trailing rows in 'Equipment' (from first blank to row 15).")

            # Water Heater
            if "Water Heater" in [s.name for s in wb_template.sheets]:
                sh_wh = wb_template.sheets["Water Heater"]
                n = delete_rows_from_first_dash_or_zero_in_peak_hot_water(sh_wh, end_row=60, space_col=1)
                # print(f"  -> Deleted {n} rows in 'Water Heater' (from first '-' / 0 / blank Space to row 60).")

            # Schedules: delete rows with 0 in column A
            if SCHEDULES_SHEET in [s.name for s in wb_template.sheets]:
                sh_sched = wb_template.sheets[SCHEDULES_SHEET]
                n_del = delete_zero_rows_in_schedules(sh_sched)
                # print(f"  -> Deleted {n_del} zero rows in '{SCHEDULES_SHEET}'.")

            # Enable schedule figures generations by linking charts to the Schedules tab
            build_schedule_figures_from_schedules(wb_template)

            # Energy usage figures from Energy Consumption sheet
            build_energy_usage_figures(wb_template)

            # Switch to Prototype tab
            activate_prototype_sheet(wb_template, sheet_name="Prototype")

            wb_template.save(new_file_path)
            wb_raw.close()
            wb_template.close()
            # print("  -> Successfully updated and saved.")

    finally:
        app.quit()
        print("\nScorecards generation completed.")


if __name__ == "__main__":
    main()