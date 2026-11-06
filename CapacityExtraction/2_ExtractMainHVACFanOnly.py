import os
import re
import io
import json
import pandas as pd

CSV_TARGET_FOLDER = os.environ.get(
    "EXTRACTED_RAW_DIR",
    r"C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\CapacityExtraction\Extracted_Data_Raw"
)
CSV_OUTPUT_FOLDER = os.environ.get(
    "INTERMEDIATE_DIR",
    r"C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\CapacityExtraction\Extracted_Data_Intermediate_Processed"
)
# Path to the EnergyPlus prototype root (contains per-building-type subfolders).
# Used to generate the zone map in-memory — no external JSON file required.
PXT_ROOT_PATH = os.environ.get(
    "PXT_ROOT_PATH",
    r"C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\prototypes"
)

_CAPACITY_EXTRACTION_FOLDER = os.path.dirname(CSV_TARGET_FOLDER)
SAVE_JSON_PATH = os.path.join(_CAPACITY_EXTRACTION_FOLDER, "deer_zone_types_processed.json")

BUILDING_TYPE_MAP = {
    "Asm": "Assembly", "ECC": "Education - Community College",
    "EPr": "Education - Primary School", "ERC": "Education - Relocatable Classroom",
    "ESe": "Education - Secondary School", "EUn": "Education - University",
    "Fin": "Financial buildings, incl. banks", "Gro": "Grocery",
    "Hsp": "Health/Medical - Hospital", "Htl": "Lodging - Hotel",
    "Lib": "Libraries", "MBT": "Manufacturing Biotech",
    "MLI": "Manufacturing Light Industrial", "Mtl": "Lodging - Motel",
    "Nrs": "Health/Medical - Nursing Home", "OfL": "Office - Large",
    "OfS": "Office - Small", "Rel": "Religious assembly buildings",
    "RFF": "Restaurant - Fast-Food", "RSD": "Restaurant - Sit-Down",
    "Rt3": "Retail - Multistory Large", "RtL": "Retail - Single-Story Large",
    "RtS": "Retail - Small", "SCn": "Storage - Conditioned",
    "SUn": "Storage - Unconditioned", "WRf": "Warehouse - Refrigerated"
}

# ---------------------------------------------------------------------------
# Zone-map generation (ported from 3_Intermediate_Process.py)
# Produces the same structure as deer_zone_types_processed.json in-memory.
# ---------------------------------------------------------------------------

def generate_zone_map(prototypes_path: str) -> dict:
    """
    Walk each building-type subfolder under *prototypes_path*, parse the
    ``all_zones`` and ``irregular_zones`` arrays from ``templates/root.pxt``,
    and return a raw zone map:
        { bldg_code: { zone_name: { raw_zone_type, raw_schedule_iden,
                                    raw_hvac_iden, is_irregular } } }
    """
    def _parse_zone_line(line):
        patt = r'"([^"]+)"|\'([^\']+)\'|\b(nil)\b|([A-Za-z][A-Za-z0-9_.\-]*)'
        matches = re.findall(patt, line)
        tokens = []
        for a, b, c, d in matches:
            if a:
                tokens.append(a.strip())
            elif b:
                tokens.append(b.strip())
            elif c:
                tokens.append("nil")
            elif d:
                tokens.append(d.strip())

        if len(tokens) < 2:
            return None

        units = {"ft2", "m2", "ft", "m"}
        zone_name = tokens[0]

        schedule_type = None
        for t in reversed(tokens):
            tl = t.lower()
            if tl in units or tl == "nil":
                continue
            schedule_type = t
            break

        hvac_type = None
        for t in tokens[2:]:
            tl = t.lower()
            if tl in units:
                continue
            hvac_type = t
            break

        return zone_name, tokens[1], schedule_type, hvac_type

    raw_data = {}
    for code in BUILDING_TYPE_MAP.keys():
        file_path = os.path.join(prototypes_path, code, "templates", "root.pxt")
        if not os.path.exists(file_path):
            continue
        raw_data[code] = {}
        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            with open(file_path, encoding="ISO-8859-1") as f:
                lines = f.readlines()

        for array_name, is_irr in [("all_zones", False), ("irregular_zones", True)]:
            in_block = False
            for line in lines:
                stripped = line.strip()
                if f"{array_name} = [" in stripped:
                    in_block = True
                    continue
                if in_block and stripped.startswith("]"):
                    break
                if in_block:
                    parsed = _parse_zone_line(line)
                    if parsed:
                        z_name, z_type, sched, hvac = parsed
                        raw_data[code][z_name] = {
                            "raw_zone_type": z_type,
                            "raw_schedule_iden": sched,
                            "raw_hvac_iden": hvac,
                            "is_irregular": is_irr,
                        }
    return raw_data


def create_processed_map(raw_map: dict) -> dict:
    """
    Convert the raw zone map produced by *generate_zone_map* into the
    processed map used for HVAC-label look-ups:
        { bldg_code: { zone_name: { Zone Type, Schedule Identifier,
                                    HVAC System Identifier } } }
    """
    def _normalize_zone_type(raw_type):
        if not raw_type:
            return "Unknown"
        t = raw_type
        if t == "office_large":
            t = "office"
        elif t == "mech":
            t = "mechanical room"
        return t.capitalize() if t else "Unknown"

    def _normalize_schedule_type(raw_schedule):
        if raw_schedule is None:
            return "Unknown"
        sl = str(raw_schedule).strip().lower()
        if sl == "crac":
            return "Computer room"
        if sl == "kitch":
            return "Kitchen"
        return raw_schedule

    def _hvac_category(raw_hvac_iden, is_irregular):
        if is_irregular:
            return "Customized"
        if not raw_hvac_iden:
            return "None"
        hvac = str(raw_hvac_iden).strip()
        if hvac.lower() == "nil":
            return "None"
        if re.search(r'\bALT\b|_ALT\b|\bALT_', hvac, flags=re.IGNORECASE):
            return "Alternative"
        return "Main"

    processed_map = {}
    for bldg_code, zones in (raw_map or {}).items():
        processed_map[bldg_code] = {}
        for zone_name, info in (zones or {}).items():
            is_irr = bool(info.get("is_irregular"))
            processed_map[bldg_code][zone_name] = {
                "Zone Type": _normalize_zone_type(info.get("raw_zone_type")),
                "Schedule Identifier": _normalize_schedule_type(
                    info.get("raw_schedule_iden")
                ),
                "HVAC System Identifier": _hvac_category(
                    info.get("raw_hvac_iden"), is_irr
                ),
            }

    # If only one candidate system exists (ignoring None/Customized/Alternative),
    # promote it to "Main".
    for bldg_code, zones_data in processed_map.items():
        all_cats = [v["HVAC System Identifier"] for v in zones_data.values()]
        candidates = {
            c for c in all_cats
            if c not in ("None", "Customized", "Alternative", "Main")
        }
        if "Main" not in all_cats and len(candidates) == 1:
            target = list(candidates)[0]
            for z_info in zones_data.values():
                if z_info["HVAC System Identifier"] == target:
                    z_info["HVAC System Identifier"] = "Main"

    return processed_map


def build_zone_map(pxt_root: str) -> dict:
    """
    Generate the processed zone map in-memory from prototype files.
    Optionally saves to SAVE_JSON_PATH if that env-var is set.
    Returns an empty dict (with a warning) if the prototype folder is missing.
    """
    if not os.path.exists(pxt_root):
        print(f"[Warning] Prototype folder not found: {pxt_root} — "
              "using name-based HVAC labels.")
        return {}

    raw_map = generate_zone_map(pxt_root)
    processed = create_processed_map(raw_map)
    print(f"Generated zone map in-memory "
          f"({len(processed)} building types from {pxt_root})")

    if SAVE_JSON_PATH:
        try:
            os.makedirs(os.path.dirname(SAVE_JSON_PATH), exist_ok=True)
            with open(SAVE_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(processed, f, indent=4)
            print(f"  Saved processed JSON → {SAVE_JSON_PATH}")
        except Exception as exc:
            print(f"  [Warning] Could not save JSON: {exc}")

    return processed


# ---------------------------------------------------------------------------

def _norm(s: str) -> str:
    s = str(s or "").replace("\u00A0", " ")
    return re.sub(r"\s+", " ", s).strip().upper()


def _is_sentinel(name) -> bool:
    return _norm(str(name)) in {"", "NONE", "NAN", "N/A"}


def _read_section(lines, marker):
    """
    Return DataFrame for the section starting at ### marker ###.
    Stops only at the next ### marker (not on blank lines).
    """
    in_section = False
    buf = []
    for line in lines:
        stripped = line.strip()
        if stripped == marker:
            in_section = True
            continue
        if in_section:
            if stripped.startswith("###"):
                break
            buf.append(line)
    if not buf:
        return pd.DataFrame()
    try:
        return pd.read_csv(io.StringIO("".join(buf)), skip_blank_lines=True)
    except Exception:
        return pd.DataFrame()


def _system_prefix(name: str) -> str:
    """
    Extract the shared system prefix by stripping the role suffix.
    Works for both fan names and coil names:

      Fan:
        "MZ-VAV-LEVEL1 SUPPLY FAN"                          -> "MZ-VAV-LEVEL1"
        "MZ-VAV-LEVEL1_ALT SUPPLY FAN"                      -> "MZ-VAV-LEVEL1_ALT"
        "SHOP EL1 WEST PERIM SPC (G.W1) SZ-VAV SUPPLY FAN" -> "SHOP EL1 WEST PERIM SPC (G.W1) SZ-VAV"
        "SHOP EL1 WEST PERIM SPC (G.W1) SZ-VAV RETURN FAN" -> "SHOP EL1 WEST PERIM SPC (G.W1) SZ-VAV"

      Coil:
        "MZ-VAV-LEVEL1 COOLING COIL"                            -> "MZ-VAV-LEVEL1"
        "MZ-VAV-LEVEL1_ALT COOLING COIL"                        -> "MZ-VAV-LEVEL1_ALT"
        "SHOP EL1 WEST PERIM SPC (G.W1) SZ-VAV COOLING COIL"   -> "SHOP EL1 WEST PERIM SPC (G.W1) SZ-VAV"
        "SHOP EL1 WEST PERIM SPC (G.W1) SZ-CAV COOLING COIL"   -> "SHOP EL1 WEST PERIM SPC (G.W1) SZ-CAV"
    """
    s = str(name).strip()
    # Strip fan suffix
    s2 = re.sub(r"\s+(SUPPLY|RETURN)\s+FAN\s*$", "", s, flags=re.IGNORECASE).strip()
    if s2 != s:
        return s2
    # Strip coil suffix (SZ-VAV/SZ-CAV/SZ-CRAC version keeps the SZ token)
    m = re.search(r"\s+SZ[-\s]?(VAV|CAV|CRAC)\s+COOLING\s+COIL", s, flags=re.IGNORECASE)
    if m:
        # Keep everything up to and including the SZ-* token
        return s[:m.end() - len(" COOLING COIL")].strip() \
               if False else s[:m.start()].strip() + " " + m.group(0).split()[0].strip()
    # Generic: strip trailing " COOLING COIL"
    s3 = re.sub(r"\s+COOLING\s+COIL\s*$", "", s, flags=re.IGNORECASE).strip()
    return s3


def _fan_label_prefix(system_name: str) -> str:
    """Prefix used for HVAC label lookup (same as _system_prefix for fans)."""
    return _system_prefix(system_name)


def _coil_label_prefix(coil_name: str) -> str:
    """Prefix used for HVAC label lookup (same as _system_prefix for coils)."""
    return _system_prefix(coil_name)

def _hvac_label(prefix: str, bldg_zone_map: dict) -> str:
    """
    1. ALT anywhere in prefix -> Alternative
    2. Zone map: Alt/Customized zones only, zn in fp direction
    3. Default -> Main
    """
    if re.search(r'\bALT\b|_ALT\b|\bALT_', str(prefix), flags=re.IGNORECASE):
        return "Alternative"

    if not bldg_zone_map or not prefix:
        return "Main"

    fp = _norm(prefix)
    matched = []
    for json_zone, info in bldg_zone_map.items():
        zn = _norm(json_zone)
        if not zn:
            continue
        label = str(info.get("HVAC System Identifier", "")).strip()
        if label not in ("Alternative", "Customized"):
            continue
        if zn in fp:
            matched.append(label)

    if "Customized" in matched:
        return "Customized"
    if "Alternative" in matched:
        return "Alternative"
    return "Main"


def _hvac_has_coils(hvac_name: str, df_seer2: pd.DataFrame, df_coil: pd.DataFrame) -> bool:
    """
    Return True if the HVAC has at least one real (non-sentinel) coil row
    in either coil DataFrame.
    """
    for df in (df_seer2, df_coil):
        if df is None or df.empty:
            continue
        if "HVAC name" not in df.columns or "Coil name" not in df.columns:
            continue
        subset = df[df["HVAC name"] == hvac_name]
        if subset.empty:
            continue
        if subset["Coil name"].apply(lambda v: not _is_sentinel(v)).any():
            return True
    return False


def build_fan_overview(df_fan: pd.DataFrame, bldg_zone_map: dict,
                       df_seer2: pd.DataFrame = None,
                       df_coil: pd.DataFrame = None) -> pd.DataFrame:
    if df_fan is None or df_fan.empty:
        return pd.DataFrame()

    df = df_fan.copy()
    sys_col = next((c for c in ["System name", "System Name"] if c in df.columns), None)
    if not sys_col:
        return df

    df["HVAC System Identifier"] = df[sys_col].apply(
        lambda n: _hvac_label(_fan_label_prefix(str(n)), bldg_zone_map)
    )

    # Override to N/A for any HVAC that has no real coils — fan-only systems
    # (e.g. unit heater fans) are not Main/Alternative/Customized cooling systems
    if "HVAC name" in df.columns:
        no_coil_mask = df["HVAC name"].apply(
            lambda h: not _hvac_has_coils(h, df_seer2, df_coil)
        )
        df.loc[no_coil_mask, "HVAC System Identifier"] = "N/A"

    out_cols = [c for c in [
        "Climate Zone", "Vintage", "HVAC name",
        "System name", "HVAC System Identifier",
        "Rated Electricity Rate [W]",
    ] if c in df.columns]
    return df[out_cols].reset_index(drop=True)


KEY_COLS = ["Climate Zone", "Vintage", "HVAC name", "Coil name"]
CAP_COL  = "Standard Rated Net Cooling Capacity [W]"
LOAD_COL = "Design Coil Load [W]"


def _prep_side(df, value_col):
    if df is None or df.empty:
        return pd.DataFrame(columns=KEY_COLS + ["_coil_key", value_col]), set()

    df = df.copy()
    for c in KEY_COLS:
        if c not in df.columns:
            df[c] = "N/A"

    sentinel_mask = df["Coil name"].apply(_is_sentinel)
    sent_keys = set(
        tuple(r) for r in
        df[sentinel_mask][["Climate Zone", "Vintage", "HVAC name"]]
        .drop_duplicates().values
    )

    df = df[~sentinel_mask].copy()
    if df.empty:
        return pd.DataFrame(columns=KEY_COLS + ["_coil_key", value_col]), sent_keys

    df["_coil_key"] = df["Coil name"].apply(_norm)
    return df[KEY_COLS + ["_coil_key", value_col]], sent_keys


def build_cooling_summary(df_seer2: pd.DataFrame,
                          df_coil: pd.DataFrame,
                          bldg_zone_map: dict) -> pd.DataFrame:
    left,  sent_left  = _prep_side(df_seer2, CAP_COL)
    right, sent_right = _prep_side(df_coil,  LOAD_COL)
    sentinel_czs = sent_left & sent_right

    merge_keys = ["Climate Zone", "Vintage", "HVAC name", "_coil_key"]

    if left.empty and right.empty:
        merged = pd.DataFrame()
    elif left.empty:
        merged = right.copy()
        merged[CAP_COL] = "N/A"
    elif right.empty:
        merged = left.copy()
        merged[LOAD_COL] = "N/A"
    else:
        merged = pd.merge(
            left.rename(columns={"Coil name": "Coil name_L"}),
            right.rename(columns={"Coil name": "Coil name_R"}),
            on=merge_keys, how="outer"
        )
        merged["Coil name"] = merged["Coil name_L"].combine_first(merged["Coil name_R"])
        merged = merged.drop(columns=["Coil name_L", "Coil name_R"], errors="ignore")

    for col in [CAP_COL, LOAD_COL]:
        if not merged.empty:
            if col not in merged.columns:
                merged[col] = "N/A"
            merged[col] = merged[col].fillna("N/A")

    if not merged.empty:
        merged = merged.drop(columns=["_coil_key"], errors="ignore")
        merged["Coil name"] = merged["Coil name"].apply(
            lambda n: "N/A" if _is_sentinel(n) else str(n).strip()
        )

    if sentinel_czs:
        sent_rows = pd.DataFrame([
            {"Climate Zone": cz, "Vintage": vint, "HVAC name": hvac,
             "Coil name": "N/A", CAP_COL: "N/A", LOAD_COL: "N/A"}
            for (cz, vint, hvac) in sorted(sentinel_czs)
        ])
        merged = pd.concat([merged, sent_rows], ignore_index=True) \
                 if not merged.empty else sent_rows

    if merged.empty:
        return pd.DataFrame()

    # Sort: real rows first within each CZ, sentinel last
    merged["_sort_sentinel"] = (merged["Coil name"] == "N/A").astype(int)
    merged = merged.sort_values(
        by=["Climate Zone", "_sort_sentinel"], kind="mergesort"
    ).drop(columns=["_sort_sentinel"])

    merged["HVAC System Identifier"] = merged["Coil name"].apply(
        lambda n: "N/A" if n == "N/A"
        else _hvac_label(_coil_label_prefix(str(n)), bldg_zone_map)
    )

    out_cols = ["Climate Zone", "Vintage", "HVAC name",
                "Coil name", "HVAC System Identifier", CAP_COL, LOAD_COL]
    for c in out_cols:
        if c not in merged.columns:
            merged[c] = "N/A"

    return merged[out_cols].reset_index(drop=True)


FAN_RATE_COL = "Rated Electricity Rate [W]"


def build_capacity_summary(df_coil_summary: pd.DataFrame,
                           df_fan_overview: pd.DataFrame) -> pd.DataFrame:
    """
    Start from COOLING COILS SUMMARY and append fan Rated Electricity Rate [W]
    by matching on the shared system prefix:

      coil prefix  = _system_prefix(coil_name)
      fan  prefix  = _system_prefix(system_name)

    For each (Climate Zone, coil_prefix) key, sum all matching fan rates
    (handles MZ systems that may have multiple fans per coil).
    Unmatched coils and N/A sentinel rows get "N/A".
    """
    if df_coil_summary is None or df_coil_summary.empty:
        return pd.DataFrame()

    df = df_coil_summary.copy()
    df[FAN_RATE_COL] = "N/A"

    if df_fan_overview is None or df_fan_overview.empty:
        return df

    fan_col = next((c for c in ["System name", "System Name"]
                    if c in df_fan_overview.columns), None)
    if not fan_col or FAN_RATE_COL not in df_fan_overview.columns:
        return df

    # Build fan lookup: (Climate Zone, normalised prefix) -> sum of rates
    fan_df = df_fan_overview.copy()
    fan_df["_prefix"] = fan_df[fan_col].apply(
        lambda n: _norm(_system_prefix(str(n)))
    )
    fan_df["_rate"] = pd.to_numeric(fan_df[FAN_RATE_COL], errors="coerce")

    # Group by (Climate Zone, prefix) and sum — handles multiple fans per system
    fan_lookup = (
        fan_df.dropna(subset=["_rate"])
        .groupby(["Climate Zone", "_prefix"])["_rate"]
        .sum()
        .reset_index()
    )
    fan_lookup = {
        (row["Climate Zone"], row["_prefix"]): row["_rate"]
        for _, row in fan_lookup.iterrows()
    }

    fan_cz_total = (
        fan_df.dropna(subset=["_rate"])
        .groupby(["Climate Zone", "HVAC name"])["_rate"]
        .sum()
        .reset_index()
    )
    fan_cz_lookup = {
        (row["Climate Zone"], row["HVAC name"]): row["_rate"]
        for _, row in fan_cz_total.iterrows()
    }

    def _match_fan(row):
        """For real coil rows — match by prefix."""
        coil_name = str(row["Coil name"])
        cz        = str(row["Climate Zone"])
        if coil_name == "N/A":
            return "N/A"
        prefix = _norm(_system_prefix(coil_name))
        rate = fan_lookup.get((cz, prefix))
        return round(rate, 2) if rate is not None else "N/A"

    # For real coil rows apply prefix matching as before
    df[FAN_RATE_COL] = df.apply(_match_fan, axis=1)

    # For N/A sentinel rows (no coils): expand one row per fan, keep separate
    sentinel_mask = df["Coil name"] == "N/A"
    real_rows     = df[~sentinel_mask].copy()

    # Build per-fan rows from fan_df for each sentinel CZ
    sentinel_czs = df[sentinel_mask][["Climate Zone", "Vintage", "HVAC name"]].drop_duplicates()
    fan_expansion_rows = []
    for _, sent_row in sentinel_czs.iterrows():
        cz   = sent_row["Climate Zone"]
        vint = sent_row["Vintage"]
        hvac = sent_row["HVAC name"]
        # Get all fans for this CZ/HVAC
        cz_fans = fan_df[
            (fan_df["Climate Zone"] == cz) &
            (fan_df["HVAC name"]    == hvac)
        ]
        if cz_fans.empty:
            # No fans either — keep the original N/A row as-is
            fan_expansion_rows.append({
                "Climate Zone": cz, "Vintage": vint, "HVAC name": hvac,
                "Coil name": "N/A", "HVAC System Identifier": "N/A",
                CAP_COL: "N/A", LOAD_COL: "N/A", FAN_RATE_COL: "N/A",
            })
        else:
            for _, fan_row in cz_fans.iterrows():
                rate = fan_row["_rate"]
                fan_expansion_rows.append({
                    "Climate Zone": cz, "Vintage": vint, "HVAC name": hvac,
                    "Coil name": str(fan_row.get(fan_col, "N/A")),
                    "HVAC System Identifier": str(fan_row.get("HVAC System Identifier", "N/A")),
                    CAP_COL: "N/A", LOAD_COL: "N/A",
                    FAN_RATE_COL: round(rate, 2) if pd.notna(rate) else "N/A",
                })

    if fan_expansion_rows:
        df_expanded = pd.DataFrame(fan_expansion_rows)
        df = pd.concat([real_rows, df_expanded], ignore_index=True)
    else:
        df = real_rows

    out_cols = [
        "Climate Zone", "Vintage", "HVAC name",
        "Coil name", "HVAC System Identifier",
        CAP_COL, LOAD_COL, FAN_RATE_COL,
    ]
    for c in out_cols:
        if c not in df.columns:
            df[c] = "N/A"

    return df[out_cols].reset_index(drop=True)


GENERATED_MARKERS = {
    "### FAN OVERVIEW ###",
    "### COOLING COILS SUMMARY ###",
    "### CAPACITY SUMMARY ###",
    "### MAIN CAPACITY SUMMARY ###",   # add this
}


def process_file(file_path: str, output_folder: str, bldg_zone_map: dict):
    with open(file_path, encoding="utf-8-sig", errors="ignore") as f:
        lines = f.readlines()

    df_fan   = _read_section(lines, "### FAN ###")
    df_seer2 = _read_section(lines, "### DX COOLING COILS [SEER2] ###")
    df_coil  = _read_section(lines, "### COOLING COILS ###")

    df_fan_overview    = build_fan_overview(df_fan, bldg_zone_map, df_seer2, df_coil)
    df_cooling_summary = build_cooling_summary(df_seer2, df_coil, bldg_zone_map)
    df_capacity_summary = build_capacity_summary(df_cooling_summary, df_fan_overview)

    # Strip any pre-existing generated blocks (idempotent re-run)
    new_lines = []
    skip = False
    for line in lines:
        stripped = line.strip()
        if stripped in GENERATED_MARKERS:
            skip = True
        if skip and stripped.startswith("###") and stripped not in GENERATED_MARKERS:
            skip = False
        if not skip:
            new_lines.append(line)

    if new_lines and new_lines[-1].strip():
        new_lines.append("\n")

    # Append FAN OVERVIEW
    new_lines.append("\n### FAN OVERVIEW ###\n")
    new_lines.append(df_fan_overview.to_csv(index=False, lineterminator="\n")
                     if not df_fan_overview.empty else "No data\n")

    # Append COOLING COILS SUMMARY
    new_lines.append("\n### COOLING COILS SUMMARY ###\n")
    new_lines.append(df_cooling_summary.to_csv(index=False, lineterminator="\n")
                     if not df_cooling_summary.empty else "No data\n")

    # Append CAPACITY SUMMARY
    new_lines.append("\n### CAPACITY SUMMARY ###\n")
    new_lines.append(df_capacity_summary.to_csv(index=False, lineterminator="\n")
                     if not df_capacity_summary.empty else "No data\n")

    # Append MAIN CAPACITY SUMMARY — filter to Main rows only
    new_lines.append("\n### MAIN CAPACITY SUMMARY ###\n")
    if not df_capacity_summary.empty and "HVAC System Identifier" in df_capacity_summary.columns:
        df_main = df_capacity_summary[
            df_capacity_summary["HVAC System Identifier"].str.strip().str.upper() == "MAIN"
        ].reset_index(drop=True)
        new_lines.append(df_main.to_csv(index=False, lineterminator="\n")
                         if not df_main.empty else "No data\n")
    else:
        new_lines.append("No data\n")

    out_path = os.path.join(output_folder, os.path.basename(file_path))
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        f.writelines(new_lines)

    print(f"  [OK] {os.path.basename(file_path)} "
          f"— {len(df_fan_overview)} fan, "
          f"{len(df_cooling_summary)} coil, "
          f"{len(df_capacity_summary)} capacity, "
          f"{len(df_main) if not df_capacity_summary.empty else 0} main rows")


if __name__ == "__main__":
    os.makedirs(CSV_OUTPUT_FOLDER, exist_ok=True)

    # Generate the processed zone map in-memory from prototype files.
    # No external JSON file is read; the map is built fresh every run.
    zone_map = build_zone_map(PXT_ROOT_PATH)

    if not os.path.exists(CSV_TARGET_FOLDER):
        print(f"[Error] Input folder not found: {CSV_TARGET_FOLDER}")
        exit(1)

    files = [f for f in os.listdir(CSV_TARGET_FOLDER) if f.lower().endswith(".csv")]
    print(f"Processing {len(files)} files from {CSV_TARGET_FOLDER}")

    for filename in sorted(files):
        file_path = os.path.join(CSV_TARGET_FOLDER, filename)
        bldg_code = filename[:3]
        bldg_zone_map = zone_map.get(bldg_code, {})
        if not bldg_zone_map:
            print(f"  [Note] No zone map for '{bldg_code}' — using name-based HVAC labels")
        process_file(file_path, CSV_OUTPUT_FOLDER, bldg_zone_map)

    print("\nDone.")