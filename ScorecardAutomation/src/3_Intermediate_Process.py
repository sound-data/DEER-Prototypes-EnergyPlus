import os
import re
import json
import pandas as pd
import io

# PXT_ROOT_PATH = os.environ.get(
#     "PXT_ROOT_PATH",
#     r"C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\prototypes"
# )
# SCORECARD_FOLDER = os.environ.get(
#     "SCORECARD_FOLDER",
#     r"C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\ScorecardAutomation"
# )

# BASE_EP_FILES = os.environ.get("EP_FILES_ROOT", os.path.join(SCORECARD_FOLDER, "EP_Files"))
# CSV_TARGET_FOLDER = os.environ.get("EXTRACTED_RAW_DIR", os.path.join(BASE_EP_FILES, "Extracted_Data_Raw"))
# CSV_OUTPUT_FOLDER = os.environ.get("INTERMEDIATE_DIR", os.path.join(BASE_EP_FILES, "Extracted_Data_Intermediate_Processed"))

def _require_env(key: str) -> str:
    v = os.environ.get(key)
    if not v or not str(v).strip():
        raise EnvironmentError(
            f"Missing required environment variable '{key}'. "
            "Run this script via Run2_Data_Extraction_Processing.py."
        )
    return str(v)

PXT_ROOT_PATH = _require_env("PXT_ROOT_PATH")
SCORECARD_FOLDER = _require_env("SCORECARD_FOLDER")

BASE_EP_FILES = _require_env("EP_FILES_ROOT")
CSV_TARGET_FOLDER = _require_env("EXTRACTED_RAW_DIR")
CSV_OUTPUT_FOLDER = _require_env("INTERMEDIATE_DIR")

RAW_JSON_PATH = os.path.join(SCORECARD_FOLDER, "deer_zone_types_raw.json")
PROCESSED_JSON_PATH = os.path.join(SCORECARD_FOLDER, "deer_zone_types_processed.json")


# Function to Extract Raw Map
def generate_zone_map(prototypes_path):
    building_type_map = {
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

    def _parse_zone_line(line):
        """
        For each row like:
        ["Zone Name", "internal_space_type", 123.4['ft2'], "MAIN-ALT", ..., "Retail"]
        ["Zone Name", "kitchen", 123.4['ft2'], "Sys13", "CAV", kitch]

        We want:
        zone_name  = first field
        zone_type  = LAST field (Retail / School / Plenum / kitch / crac)
        hvac_type  = first non-unit token after the area+unit (MAIN-ALT / Sys13 / nil)
        """
        # Capture:
        #  - "double quoted"
        #  - 'single quoted'
        #  - nil
        #  - bare identifiers (Sys13, Sys11-G.C5, CAV, kitch, crac, MAIN-ALT, etc.)
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
        zone_type = tokens[1]

        # Zone Type = last meaningful token (skip units / nil if they ever appear at end)
        schedule_type = None
        for t in reversed(tokens):
            tl = t.lower()
            if tl in units:
                continue
            if tl == "nil":
                continue
            schedule_type = t
            break

        # HVAC identifier = first meaningful token after index 2 onward (skip units)
        hvac_type = None
        for t in tokens[2:]:
            tl = t.lower()
            if tl in units:
                continue
            # allow nil -> treat as None later in _hvac_category
            hvac_type = t
            break

        return zone_name, zone_type, schedule_type, hvac_type

    raw_data = {}

    for code in building_type_map.keys():
        file_path = os.path.join(prototypes_path, code, "templates", "root.pxt")
        if not os.path.exists(file_path):
            continue

        raw_data[code] = {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='ISO-8859-1') as f:
                lines = f.readlines()

        in_all = False
        for line in lines:
            stripped = line.strip()
            if "all_zones = [" in stripped:
                in_all = True
                continue
            if in_all and stripped.startswith("]"):
                in_all = False
                break
            if in_all:
                parsed = _parse_zone_line(line)
                if parsed:
                    zone_name, zone_type, schedule_type, hvac_type = parsed
                    raw_data[code][zone_name] = {
                        "raw_zone_type": zone_type,
                        "raw_schedule_iden": schedule_type,
                        "raw_hvac_iden": hvac_type,
                        "is_irregular": False
                    }

        in_irr = False
        for line in lines:
            stripped = line.strip()
            if "irregular_zones = [" in stripped:
                in_irr = True
                continue
            if in_irr and stripped.startswith("]"):
                in_irr = False
                break
            if in_irr:
                parsed = _parse_zone_line(line)
                if parsed:
                    zone_name, zone_type, schedule_type, hvac_type = parsed
                    raw_data[code][zone_name] = {
                        "raw_zone_type": zone_type,
                        "raw_schedule_iden": schedule_type,
                        "raw_hvac_iden": hvac_type,
                        "is_irregular": True
                    }

    return raw_data


# Function to Create Processed Map
def create_processed_map(raw_map):
    def _normalize_zone_type(raw_type):
        if not raw_type:
            return "Unknown"
        new_type = raw_type
        if raw_type == "office_large":
            new_type = "office"
        elif raw_type == "mech":
            new_type = "mechanical room"
        return new_type.capitalize() if new_type else "Unknown"
    
    def _normalize_schedule_type(raw_schedule):
        if raw_schedule is None:
            return "Unknown"
        if str(raw_schedule).strip().lower() == "crac":
            return "Computer room"
        elif str(raw_schedule).strip().lower() == "kitch":
            return "Kitchen"
        return raw_schedule
    
    def _hvac_category(raw_hvac_iden, raw_type, is_irregular):
        # 1. Custom/Irregular check
        if is_irregular:
            return "Customized"
        
        # 2. Convert to string safely
        if not raw_hvac_iden:
            return "None"
            
        hvac = str(raw_hvac_iden).strip()
        
        # 3. Check for "nil" explicitly (case-insensitive)
        if hvac.lower() == "nil":
            return "None"
            
        # 4. Check for Alternative systems
        if re.search(r'\bALT\b|_ALT\b|\bALT_', hvac, flags=re.IGNORECASE):
            return "Alternative"
            
        # 6. Put everything else as Main
        return "Main"

    processed_map = {}
    
    # Initial processing
    for bldg_code, zones in (raw_map or {}).items():
        processed_map[bldg_code] = {}
        for zone_name, info in (zones or {}).items():
            raw_type = info.get("raw_zone_type")
            raw_schedule = info.get("raw_schedule_iden")
            raw_hvac = info.get("raw_hvac_iden")
            is_irregular = bool(info.get("is_irregular"))

            processed_map[bldg_code][zone_name] = {
                "Zone Type": _normalize_zone_type(raw_type),
                "Schedule Identifier": _normalize_schedule_type(raw_schedule),
                "HVAC System Identifier": _hvac_category(raw_hvac, raw_type, is_irregular)
            }

    # Assign "Main" if only one candidate exists
    for bldg_code, zones_data in processed_map.items():
        all_cats = [v["HVAC System Identifier"] for v in zones_data.values()]
        candidates = set(c for c in all_cats if c not in ["None", "Customized", "Alternative", "Main"])
        
        if "Main" not in all_cats and len(candidates) == 1:
            target_system = list(candidates)[0]
            for z_name, z_info in zones_data.items():
                if z_info["HVAC System Identifier"] == target_system:
                    z_info["HVAC System Identifier"] = "Main"

    return processed_map


# Helper to find zone info

def attach_fan_hvac_identifier(df_fan: pd.DataFrame, df_zone_summary: pd.DataFrame) -> pd.DataFrame:
    """
    Add/overwrite 'HVAC System Identifier' in FAN table using:
      1) If System name contains ALT -> Alternative
      2) Else match zone name (with HVAC System Identifier Alternative/Customized) to fan System name prefix:
         - prefix = system name before 'SUPPLY FAN' or 'RETURN FAN'
         - if any match is Customized -> Customized; else Alternative
      3) Else -> Main
    """
    import re

    if df_fan is None or df_fan.empty:
        return df_fan

    df = df_fan.copy()

    # Accept either "System name" (preferred) or "System Name"
    sys_col = "System name" if "System name" in df.columns else ("System Name" if "System Name" in df.columns else None)
    if not sys_col:
        return df

    def norm(s: str) -> str:
        s = str(s or "").replace("\u00A0", " ")
        s = re.sub(r"\s+", " ", s).strip().upper()
        return s

    def fan_prefix(system_name: str) -> str:
        s = norm(system_name)
        s = re.sub(r"\s+(SUPPLY|RETURN)\s+FAN\s*$", "", s, flags=re.IGNORECASE)
        return s

    # If no zone summary / no HVAC id column, apply ALT-only and default Main
    if df_zone_summary is None or df_zone_summary.empty or "Zone Name" not in df_zone_summary.columns or "HVAC System Identifier" not in df_zone_summary.columns:
        df["HVAC System Identifier"] = df[sys_col].apply(
            lambda s: "Alternative" if re.search(r"\bALT\b", str(s), flags=re.IGNORECASE) else "Main"
        )
        return df

    # Determine default label: "Main" only if at least one zone contains it, else "N/A"
    all_hvac_ids = df_zone_summary["HVAC System Identifier"].astype(str).str.strip().tolist()
    default_label = "Main" if "Main" in all_hvac_ids else "N/A"

    zs = df_zone_summary[["Zone Name", "HVAC System Identifier"]].copy()
    zs["ZoneNameN"] = zs["Zone Name"].apply(norm)
    zs["HVACID"] = zs["HVAC System Identifier"].astype(str).str.strip()
    zs = zs[zs["HVACID"].isin(["Alternative", "Customized"])].copy()

    def assign_id(system_name: str) -> str:
        s_raw = str(system_name or "")
        if re.search(r"\bALT\b", s_raw, flags=re.IGNORECASE):
            return "Alternative"

        fp = fan_prefix(s_raw)

        matched = []
        for _, r in zs.iterrows():
            zn = r["ZoneNameN"]
            if zn and zn in fp:
                matched.append(r["HVACID"])

        if "Customized" in matched:
            return "Customized"
        if "Alternative" in matched:
            return "Alternative"
        return default_label

    df["HVAC System Identifier"] = df[sys_col].apply(assign_id)
    return df

def find_zone_info(csv_zone_name, building_map):
    if not building_map:
        return "Unknown", "Unknown", "Unknown"
    if csv_zone_name in building_map:
        info = building_map[csv_zone_name] or {}
        return (
            info.get("Zone Type", "Unknown"),
            info.get("HVAC System Identifier", "Unknown"),
            info.get("Schedule Identifier", "Unknown"),
        )
    csv_lower = str(csv_zone_name).lower()
    for json_zone_name, info in building_map.items():
        if str(json_zone_name).lower() in csv_lower:
            info = info or {}
            return (
                info.get("Zone Type", "Unknown"),
                info.get("HVAC System Identifier", "Unknown"),
                info.get("Schedule Identifier", "Unknown"),
            )
    return "Unknown", "Unknown", "Unknown"


# Summary Table Generators
def generate_summary_tables(df_zone_summary, vintage_label, df_gas_equip=None):
    """
    Generate:
      - ### INTERIOR LIGHTS ###
      - ### EQUIPMENT ###
      - ### OUTDOOR AIRFLOW RATE ###
      - ### GAS EQUIPMENT SUMMARY ###

    IMPORTANT UPDATE (2026-02-19):
      For INTERIOR LIGHTS / EQUIPMENT / OUTDOOR AIRFLOW RATE, the "Floor Area (ft2)"
      is calculated as: Zone Area * Zone Multiplier (from ### ZONE SUMMARY ###).
      All area-weighted averages use this multiplied floor area as the weighting basis.
    """
    col_type = "Zone Type"
    col_area = next((c for c in df_zone_summary.columns if "Area (Excluding Plenums and CrawlSpace)" in c), None)

    # Detect multipliers column (varies by extractor naming)
    col_mult = next((c for c in df_zone_summary.columns if re.search(r"\bmultiplier(s)?\b", str(c), flags=re.IGNORECASE)), None)

    # Detect columns with explicit units if possible
    col_light = next((c for c in df_zone_summary.columns if "Lighting" in c and "Btu/h-ft2" in c), None)
    col_plug = next((c for c in df_zone_summary.columns if "Plug" in c and "Btu/h-ft2" in c), None)
    col_people_dens = next((c for c in df_zone_summary.columns if "People (Persons/1000 ft2)" in c), None)
    col_oa_person = next((c for c in df_zone_summary.columns if "Outdoor Air Flow per Person (cfm/person)" in c), None)
    col_oa_area = next((c for c in df_zone_summary.columns if "Outdoor Air Flow per Zone Floor Area (cfm/ft2)" in c), None)
    if not col_light:
        col_light = next((c for c in df_zone_summary.columns if "Lighting" in c), None)
    if not col_plug:
        col_plug = next((c for c in df_zone_summary.columns if "Plug" in c), None)
    if not all([col_area, col_type]):
        return "", "", "", ""

    # Determine Conversion Factors (Btu/h to Watts)
    # 1 Btu/h = 0.29307107 Watts
    btuh_to_watts = 0.29307107
    light_conversion_factor = btuh_to_watts if (col_light and "Btu/h" in col_light) else 1.0
    plug_conversion_factor = btuh_to_watts if (col_plug and "Btu/h" in col_plug) else 1.0

    df = df_zone_summary.copy()

    # Build numeric columns list
    numeric_cols = [col_area]
    if col_mult:
        numeric_cols.append(col_mult)
    if col_light:
        numeric_cols.append(col_light)
    if col_plug:
        numeric_cols.append(col_plug)
    if col_people_dens:
        numeric_cols.append(col_people_dens)
    if col_oa_person:
        numeric_cols.append(col_oa_person)
    if col_oa_area:
        numeric_cols.append(col_oa_area)

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Default multiplier = 1 if missing / zeros
    if col_mult:
        df[col_mult] = df[col_mult].replace(0, 1).fillna(1)
    else:
        df["_Multiplier_"] = 1.0
        col_mult = "_Multiplier_"

    # Effective floor area = zone area * multiplier
    df["_FloorAreaEff_"] = (df[col_area] * df[col_mult]).fillna(0)

    # Filter out zero effective area
    df = df[df["_FloorAreaEff_"] > 0].copy()
    if df.empty:
        return "", "", "", ""

    grouped = df.groupby(col_type)
    results = []
    for name, group in grouped:
        total_area_eff = group["_FloorAreaEff_"].sum()

        # Weighted averages using effective area
        raw_lpd = (group[col_light] * group["_FloorAreaEff_"]).sum() / total_area_eff if col_light else 0
        raw_plug = (group[col_plug] * group["_FloorAreaEff_"]).sum() / total_area_eff if col_plug else 0

        avg_lpd = raw_lpd * light_conversion_factor
        avg_plug = raw_plug * plug_conversion_factor

        # OA per person: weight by total people count (people density * effective area)
        avg_oa_person = 0
        if col_oa_person and col_people_dens:
            # persons = (persons/1000ft2) * floor_area(ft2) / 1000
            people_cnt = (group[col_people_dens] * group["_FloorAreaEff_"] / 1000.0).sum()
            if people_cnt > 0:
                avg_oa_person = ((group[col_oa_person] * (group[col_people_dens] * group["_FloorAreaEff_"] / 1000.0)).sum() / people_cnt)

        # OA per area: already cfm/ft2, weight by effective area
        avg_oa_area = (group[col_oa_area] * group["_FloorAreaEff_"]).sum() / total_area_eff if col_oa_area else 0

        results.append({
            "Zone Type": name,
            "Floor Area": total_area_eff,
            "LPD": avg_lpd,
            "Plug": avg_plug,
            "OA_Person": avg_oa_person,
            "OA_Area": avg_oa_area
        })

    summary_df = pd.DataFrame(results)

    # Output tables with correct units (W/ft2)
    lights_df = summary_df.copy()
    lights_df["Vintage"] = vintage_label
    lights_df = lights_df[["Vintage", "Zone Type", "Floor Area", "LPD"]]
    lights_df.columns = ["Vintage", "Zone Type", "Floor Area (ft2)", "Lighting Power Density(W/ft2)"]

    equip_df = summary_df.copy()
    equip_df = equip_df[["Zone Type", "Floor Area", "Plug"]]
    equip_df.columns = ["Zone Type", "Floor Area (ft2)", "Plug Load Intensity (W/ft2)"]

    oa_df = summary_df.copy()
    oa_df = oa_df[["Zone Type", "Floor Area", "OA_Person", "OA_Area"]]
    oa_df.columns = ["Zone Type", "Floor Area (ft2)", "cfm/person", "cfm/ft2"]

    # Currently keeping as Btu/h-ft2, but use effective area (area * multiplier) for aggregation.
    gas_csv = ""

    def _gas_not_found_table():
        df_nf = pd.DataFrame([{
            "Zone Name": "No GasEquipment found.",
            "Gas Loads (Btu/h-ft2)": ""
        }])
        return "### GAS EQUIPMENT SUMMARY ###\n" + df_nf.to_csv(index=False, lineterminator="\n")

    if df_gas_equip is None or df_gas_equip.empty:
        gas_csv = _gas_not_found_table()
    else:
        if "Zone Name" not in df_gas_equip.columns:
            gas_csv = _gas_not_found_table()
        else:
            if df_gas_equip["Zone Name"].astype(str).str.contains(r"No\s*GasEquipment\s*found", case=False, na=False).any():
                gas_csv = _gas_not_found_table()
            else:
                col_gas_load = next((c for c in df_gas_equip.columns if "Gas Loads" in c), None)
                if not col_gas_load:
                    gas_csv = _gas_not_found_table()
                else:
                    gas_temp = df_gas_equip.copy()

                    # Pull Zone Name, Zone Type, Area, Multiplier from Zone Summary and compute effective area
                    zone_temp = df_zone_summary[['Zone Name', col_type, col_area]].copy()
                    if col_mult in df_zone_summary.columns:
                        zone_temp[col_mult] = pd.to_numeric(df_zone_summary[col_mult], errors="coerce").replace(0, 1).fillna(1)
                    else:
                        zone_temp[col_mult] = 1.0
                    zone_temp["_FloorAreaEff_"] = pd.to_numeric(zone_temp[col_area], errors="coerce").fillna(0) * pd.to_numeric(zone_temp[col_mult], errors="coerce").fillna(1)

                    gas_temp['merge_key'] = gas_temp['Zone Name'].astype(str).str.strip().str.lower()
                    zone_temp['merge_key'] = zone_temp['Zone Name'].astype(str).str.strip().str.lower()

                    merged_gas = pd.merge(gas_temp, zone_temp[['merge_key', col_type, "_FloorAreaEff_"]], on='merge_key', how='inner')

                    if merged_gas.empty:
                        gas_csv = _gas_not_found_table()
                    else:
                        merged_gas[col_gas_load] = pd.to_numeric(merged_gas[col_gas_load], errors='coerce').fillna(0)
                        merged_gas["_FloorAreaEff_"] = pd.to_numeric(merged_gas["_FloorAreaEff_"], errors="coerce").fillna(0)

                        if col_type in merged_gas.columns:
                            g_grouped = merged_gas.groupby(col_type)
                            g_results = []
                            for name, group in g_grouped:
                                total_area_g = group["_FloorAreaEff_"].sum()
                                avg_gas = ((group[col_gas_load] * group["_FloorAreaEff_"]).sum() / total_area_g) if total_area_g > 0 else 0
                                g_results.append({"Zone Type": name, "Floor Area": total_area_g, "Gas Load": avg_gas})

                            if g_results:
                                gas_summary_df = pd.DataFrame(g_results)
                                gas_final = gas_summary_df[["Zone Type", "Floor Area", "Gas Load"]].copy()
                                gas_final.columns = ["Zone Type", "Floor area (ft2)", "Gas Loads (Btu/h-ft2)"]
                                gas_csv = "### GAS EQUIPMENT SUMMARY ###\n" + gas_final.to_csv(index=False, lineterminator="\n")
                            else:
                                gas_csv = _gas_not_found_table()
                        else:
                            gas_csv = _gas_not_found_table()

    lights_csv = "### INTERIOR LIGHTS ###\n" + lights_df.to_csv(index=False, lineterminator='\n')
    equip_csv = "### EQUIPMENT ###\n" + equip_df.to_csv(index=False, lineterminator='\n')
    oa_csv = "### OUTDOOR AIRFLOW RATE ###\n" + oa_df.to_csv(index=False, lineterminator='\n')

    return lights_csv, equip_csv, oa_csv, gas_csv


def generate_thermostat_summary_by_schedule_identifier(df_tstat):
    """
    Aggregate thermostat setpoints by Schedule Identifier (and Climate Zone if present),
    converting C -> F.
    """
    if df_tstat.empty or "Schedule Identifier" not in df_tstat.columns:
        return ""

    numeric_cols_c = ["Heating Setpoint (C)", "Heating Setback (C)", "Cooling Setpoint (C)", "Cooling Setback (C)"]
    present_c = [c for c in numeric_cols_c if c in df_tstat.columns]
    if not present_c:
        return ""

    df = df_tstat.copy()

    # Clean - numeric - convert to F
    for c in present_c:
        df[c] = df[c].astype(str).str.replace(r"[^0-9.\-]+", "", regex=True)
        df[c] = pd.to_numeric(df[c], errors="coerce")
        df[c] = df[c] * 9/5 + 32

    # Rename to (F)
    rename_map = {c: c.replace("(C)", "(F)") for c in present_c}
    df = df.rename(columns=rename_map)
    numeric_cols_f = list(rename_map.values())

    group_keys = ["Schedule Identifier"]
    if "Climate Zone" in df.columns:
        group_keys = ["Climate Zone", "Schedule Identifier"]

    grouped = df.groupby(group_keys)[numeric_cols_f].mean().round(1).reset_index()

    if "Vintage" in df.columns:
        grouped.insert(0, "Vintage", df["Vintage"].iloc[0])

    return "### THERMOSTAT SETPOINTS ###\n" + grouped.to_csv(
        index=False, lineterminator="\n"
    )

def generate_aggregated_schedules(df):
    """
    Aggregates schedules by Schedule Identifier.

    Step A) Filter out DesignDay rows
    Step B) Clean Schedule Name: keep only content after ')' (if any)
    Step C) Aggregate by (Schedule Identifier, cleaned Schedule Name, Type):
            - If multiple zones exist for the same group, check consistency.
    Step D) (DISABLED per request): Do NOT collapse seasonal slices, even if identical.
            Keep the original '(Through m/d)' rows as-is.
    Step E) Normalize "AllOtherDays" vs "AllOtherdays" -> "AllOtherDays" (case-insensitive).
    """
    if df.empty:
        return pd.DataFrame()

    required_cols = ['Schedule Identifier', 'Schedule Name', 'Type', 'Zone Name']
    if not all(col in df.columns for col in required_cols):
        return pd.DataFrame()

    df = df.copy()

    # Filter out DesignDay rows
    df = df[~df['Type'].astype(str).str.contains("DesignDay", case=False, na=False)].copy()
    if df.empty:
        return pd.DataFrame()

    # Clean schedule name: keep only text after ')'
    def keep_after_paren(s):
        if pd.isna(s):
            return s
        s = str(s)
        if ')' in s:
            return s.split(')', 1)[1].strip()
        return s.strip()

    df['Schedule Name'] = df['Schedule Name'].apply(keep_after_paren)

    def canonical_schedule_name(s: str) -> str:
        if pd.isna(s):
            return s
        s = str(s).strip()

        # normalize whitespace
        s = re.sub(r"\s+", " ", s)

        # remove trailing numeric suffixes like "Elec Equip Sch 2" -> "Elec Equip Sch"
        s = re.sub(r"\s+\d+\s*$", "", s)

        canonical = [
            "Cooling Setpoint Schedule",
            "Heating Setpoint Schedule",
            "Infiltration Schedule",
            "Lighting Schedule",
            "OA Schedule",
            "Occupant Sch",
            "DHW Sch",
            "Elec Equip Sch",
        ]

        sl = s.lower()
        for lab in canonical:
            if lab.lower() in sl:
                return lab
        return s

    df["Schedule Name"] = df["Schedule Name"].apply(canonical_schedule_name)

    hourly_cols = [str(i) for i in range(1, 25)]

    # Helper functions for Type normalization and Through date parsing
    def _strip_through(type_str: str) -> str:
        s = str(type_str)
        s = re.sub(r"\s*\(Through\s*\d{1,2}/\d{1,2}\)\s*$", "", s, flags=re.IGNORECASE).strip()
        return s

    def _parse_through_mmdd(type_str: str):
        m = re.search(r"\(Through\s*(\d{1,2})/(\d{1,2})\)", str(type_str), flags=re.IGNORECASE)
        if not m:
            return None
        return int(m.group(1)), int(m.group(2))

    def _canonical_base_type(base: str) -> str:
        b = str(base).strip()
        bl = b.lower()
        if bl == "allotherdays":
            return "AllOtherDays"
        return b

    def _normalize_type_label(type_str: str) -> str:
        s = str(type_str).strip()
        base = _strip_through(s)
        base_can = _canonical_base_type(base)
        m = re.search(r"(\(Through\s*\d{1,2}/\d{1,2}\))\s*$", s, flags=re.IGNORECASE)
        if m:
            return f"{base_can} {m.group(1)}"
        return base_can

    # Aggregate by (Schedule Identifier, Schedule Name, Type)
    results = []
    grouped = df.groupby(['Schedule Identifier', 'Schedule Name', 'Type'], dropna=False)

    for (sched_id, sched_name, day_type), group in grouped:
        valid_cols = [c for c in hourly_cols if c in group.columns]
        if not valid_cols:
            continue

        subset = group[valid_cols]
        is_consistent = subset.drop_duplicates().shape[0] == 1

        row = {
            "Schedule Identifier": sched_id,
            "Schedule Name": sched_name,
            "Type": _normalize_type_label(day_type),  # Step E normalization here
        }

        if is_consistent:
            first_row = subset.iloc[0]
            for c in valid_cols:
                row[c] = first_row[c]
        else:
            for c in valid_cols:
                row[c] = subset[c].iloc[0] if subset[c].nunique(dropna=False) == 1 else "Inconsistent"

        results.append(row)

    out_df = pd.DataFrame(results)
    if out_df.empty:
        return out_df

    # Sorting (keeps Through slices in chronological order)
    out_df["_type_base"] = out_df["Type"].apply(_strip_through).apply(_canonical_base_type).str.lower()
    md = out_df["Type"].apply(_parse_through_mmdd)
    out_df["_through_m"] = md.apply(lambda x: x[0] if x else 99)
    out_df["_through_d"] = md.apply(lambda x: x[1] if x else 99)

    out_df = out_df.sort_values(
        by=["Schedule Identifier", "Schedule Name", "_type_base", "_through_m", "_through_d", "Type"],
        kind="mergesort"
    ).drop(columns=["_type_base", "_through_m", "_through_d"], errors="ignore")

    out_df = out_df.drop(columns=[c for c in out_df.columns if c.startswith("_")], errors="ignore")
    return out_df


# Helper to find IDF file
def find_idf_file(search_root, target_filename_no_ext):
    target_file = target_filename_no_ext + ".idf"
    for root, dirs, files in os.walk(search_root):
        if target_file in files:
            return os.path.join(root, target_file)
    return None

def extract_hvac_system_code(filename):
    parts = os.path.basename(filename).split('_')
    if len(parts) >= 3:
        return parts[2]
    return "Unknown"

# Summary Table Extractor
def extract_hvac_and_fan_info(idf_path, vintage_label, bldg_zone_map, system_code_from_filename):
    if not idf_path or not os.path.exists(idf_path):
        # print(f"  [Info Warning] IDF not found at: {idf_path}")
        return pd.DataFrame(), pd.DataFrame()

    try:
        with open(idf_path, 'r', encoding='utf-8') as f: content = f.read()
    except:
        with open(idf_path, 'r', encoding='ISO-8859-1') as f: content = f.read()

    custom_zones = set()
    if bldg_zone_map:
        for z_name, info in bldg_zone_map.items():
            if info.get("HVAC System Identifier") == "Customized":
                z_type = info.get("Zone Type", "").lower()
                if z_type and z_type != "unknown": custom_zones.add(z_type)

    default_map = {
        "cAVVG": {"cool": "chiller_cop", "heat": "boiler_eff"},
        "cDXGF": {"cool": "cool_coil_cop", "heat": "heat_coil_eff"},
        "cPVVG": {"cool": "cool_coil_cop", "heat": "heat_coil_eff"},
        "cDXHP": {"cool": "cool_coil_cop", "heat": "heat_coil_cop"},
        "cDXOH": {"cool": "cool_coil_cop", "heat": "None"},
    }
    defaults = default_map.get(system_code_from_filename, {"cool": "cool_coil_cop", "heat": "heat_coil_eff"})

    base_patt = r'![^=\n]*'
    patterns = {
        'sys_name': re.compile(base_patt + r'\bsys_name\s*=\s*"?([^"\r\n\(\)]+)"?'),
        'hvac_type': re.compile(base_patt + r'\bhvac_type\s*=\s*"?([^"\r\n\(\)]+)"?'),
        'cool_type': re.compile(base_patt + r'\bcool_coil_type\s*=\s*"?([^"\r\n\(\)]+)"?'), # Coil Type
        'heat_type': re.compile(base_patt + r'\bheat_coil_type\s*=\s*"?([^"\r\n\(\)]+)"?'), # Coil Type
        'cool_coil_cop': re.compile(base_patt + r'\bcool_coil_cop\s*=\s*([0-9.]+)'),
        'chiller_cop': re.compile(base_patt + r'\bchiller_cop\s*=\s*([0-9.]+)'),
        'heat_coil_eff': re.compile(base_patt + r'\bheat_coil_eff\s*=\s*([0-9.]+)'),
        'boiler_eff': re.compile(base_patt + r'\bboiler_eff\s*=\s*([0-9.]+)'),
        'heat_coil_cop': re.compile(base_patt + r'\bheat_coil_cop\s*=\s*([0-9.]+)'),
        'fan_rise': re.compile(base_patt + r'\bfan_rise\s*=\s*([0-9.]+)'),
        'fan_eff': re.compile(base_patt + r'\bfan_eff\s*=\s*([0-9.]+)'),
        'fan_motor_eff': re.compile(base_patt + r'\bfan_motor_eff\s*=\s*([0-9.]+)'),
        'fan_power': re.compile(base_patt + r'\bfan_power_per_flow\s*=\s*([0-9.]+)')
    }

    tokens = []
    for i, line in enumerate(content.splitlines()):
        for key, regex in patterns.items():
            match = regex.search(line)
            if match: tokens.append({'line': i, 'key': key, 'value': match.group(1).strip().replace('"', '')})

    systems = [t for t in tokens if t['key'] == 'sys_name']
    fan_rows, hvac_rows = [], []

    for sys_token in systems:
        sys_internal_name = sys_token['value']
        sys_line = sys_token['line']
        
        category = "Main"
        if "_ALT" in sys_internal_name or "-ALT" in sys_internal_name: category = "Alternative"
        else:
            for cz in custom_zones:
                if cz in sys_internal_name.lower():
                    category = "Customized"; break
        
        if category == "Main": continue

        def get_nearest(target_key):
            candidates = [t for t in tokens if t['key'] == target_key]
            if not candidates: return "N/A"
            best = min(candidates, key=lambda t: abs(t['line'] - sys_line))
            return best['value']

        def get_first(target_key):
            candidates = [t for t in tokens if t['key'] == target_key]
            return candidates[0]['value'] if candidates else "N/A"

        # Efficiency logic based on Coil Type
        cool_type_val = get_nearest('cool_type')
        heat_type_val = get_nearest('heat_type')

        target_cool_key = "chiller_cop" if cool_type_val.upper() == "WATER" else ("cool_coil_cop" if "DX" in cool_type_val.upper() else defaults["cool"])
        cool_val = get_first("chiller_cop") if target_cool_key == "chiller_cop" else get_nearest(target_cool_key)

        target_heat_key = "boiler_eff" if heat_type_val.upper() == "WATER" else ("heat_coil_eff" if heat_type_val.upper() == "COMBUSTION" else ("heat_coil_cop" if "HP" in heat_type_val.upper() else defaults["heat"]))
        heat_val = get_first("boiler_eff") if target_heat_key == "boiler_eff" else ("N/A" if target_heat_key == "None" else get_nearest(target_heat_key))

        hvac_dist = get_nearest('hvac_type')

        fan_rows.append({
            "Vintage": vintage_label, "HVAC name": system_code_from_filename, "HVAC System Identifier": category,
            "System": hvac_dist, "Total Static Pressure (TSP) (in w.c.)": get_nearest('fan_rise'),
            "Fan Efficiency": get_nearest('fan_eff'), "Fan Motor and Drive Efficiency": get_nearest('fan_motor_eff'), "W/cfm": get_nearest('fan_power')
        })

        hvac_rows.append({
            "Vintage": vintage_label, "System Name": system_code_from_filename, "HVAC System Identifier": category,
            "Air Distribution": hvac_dist, 
            "Cooling Coil Type": cool_type_val, 
            "Heating Coil Type": heat_type_val, 
            "Heating Efficiency": heat_val, "Cooling Efficiency": cool_val
        })

    df_fan = pd.DataFrame(fan_rows)
    df_hvac = pd.DataFrame(hvac_rows)
    if not df_hvac.empty:
        h_cols = ["Vintage", "System Name", "HVAC System Identifier", "Air Distribution", 
                  "Cooling Coil Type", "Heating Coil Type", "Heating Efficiency", "Cooling Efficiency"]
        df_hvac = df_hvac[h_cols]

    return df_fan, df_hvac


def convert_setpoint_schedules_C_to_F(df_in: pd.DataFrame, sched_name_col: str = "Schedule Name") -> pd.DataFrame:
    """
    Convert hourly schedule values from C to F ONLY for:
      - Heating Setpoint Schedule
      - Cooling Setpoint Schedule
    Leaves non-numeric cells (e.g., 'Inconsistent') unchanged.
    """
    if df_in is None or df_in.empty or sched_name_col not in df_in.columns:
        return df_in

    df_out = df_in.copy()
    hourly_cols = [str(i) for i in range(1, 25)]
    valid_hourly_cols = [c for c in hourly_cols if c in df_out.columns]
    if not valid_hourly_cols:
        return df_out

    mask = df_out[sched_name_col].astype(str).str.strip().isin(
        ["Heating Setpoint Schedule", "Cooling Setpoint Schedule"]
    )
    if not mask.any():
        return df_out

    for c in valid_hourly_cols:
        s = df_out.loc[mask, c].astype(str).str.strip()
        num = pd.to_numeric(s.str.replace(r"[^0-9.\-]+", "", regex=True), errors="coerce")
        converted = num * 9/5 + 32  # C → F
        df_out.loc[mask, c] = converted.round(2).where(num.notna(), s)

    return df_out

# Main Processing Function

def process_file_full(file_path, output_folder, bldg_code, zone_map, search_root):
    """
    Process one extracted CSV file and write an "intermediate processed" CSV that:
      - Adds Zone Type / HVAC System Identifier to Zone Summary
      - Adds Height (ft) = Volume (ft3) / Area (Including Plenums) (ft2) to Zone Summary
      - Computes avg Height for plenum vs non-plenum (based on Zone Type containing 'plenum')
        and appends those values to the ### BUILDING ### table as two new columns.
      - Keeps existing enhancements (fan/HVAC parsing, thermostat summaries, schedule aggregation, DHW mapping, etc.)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='ISO-8859-1') as f:
            lines = f.readlines()

    filename_base = os.path.basename(file_path)
    if re.search(r'_Ex_', filename_base, re.IGNORECASE) or "_Ex." in filename_base:
        vintage_label = "Existing"
    elif re.search(r'_New_', filename_base, re.IGNORECASE) or "_New." in filename_base:
        vintage_label = "New Construction"
    else:
        vintage_label = filename_base.replace('.csv', '')

    target_filename_no_ext = os.path.splitext(filename_base)[0]
    idf_path = find_idf_file(search_root, target_filename_no_ext)
    system_code = extract_hvac_system_code(filename_base)

    bldg_map_data = zone_map.get(bldg_code, {})

    def _read_df(buf_lines):
        if not buf_lines:
            return pd.DataFrame()
        try:
            return pd.read_csv(io.StringIO("".join(buf_lines)), skip_blank_lines=True)
        except Exception:
            return pd.DataFrame()

    def _safe_float(x):
        try:
            return float(str(x).replace('"', '').strip())
        except Exception:
            return 0.0

    # Captured tables for downstream calculations
    df_zone_summary_captured = pd.DataFrame()
    df_gas_captured = pd.DataFrame()

    already_processed = False
    new_lines = []

    # State machine for block capture
    state = None  # one of: zone_summary, building, gas_equip, fan, hvac, tstat, schedules, dhw, other
    buf = []

    def _finalize_zone_summary(df_zs):
        """
        Add Zone Type, HVAC System Identifier, Height (ft) to df_zs.
        """
        if df_zs.empty or "Zone Name" not in df_zs.columns:
            return df_zs

        # Add Zone Type & HVAC system identifier
        df_zs = df_zs.copy()
        df_zs["Zone Type"] = df_zs["Zone Name"].apply(lambda z: find_zone_info(z, bldg_map_data)[0])
        df_zs["HVAC System Identifier"] = df_zs["Zone Name"].apply(lambda z: find_zone_info(z, bldg_map_data)[1])
        df_zs["Schedule Identifier"] = df_zs["Zone Name"].apply(lambda z: find_zone_info(z, bldg_map_data)[2])


        # Height (ft) = Volume (ft3) / Area (Including Plenums) (ft2)
        col_vol = next((c for c in df_zs.columns if "Volume" in c and "ft3" in c), None)
        col_area_inc = next((c for c in df_zs.columns if "Area" in c and "Including Plenums" in c and "ft2" in c), None)

        if col_vol and col_area_inc:
            vol = pd.to_numeric(df_zs[col_vol], errors='coerce').fillna(0)
            area = pd.to_numeric(df_zs[col_area_inc], errors='coerce').fillna(0)
            df_zs["Height (ft)"] = (vol / area).replace([float("inf"), float("-inf")], 0).fillna(0)
        else:
            df_zs["Height (ft)"] = 0.0

        return df_zs

    def _flush(current_state):
        """
        Flush buffered lines for the current_state into new_lines, applying transformations.
        """
        nonlocal buf, df_zone_summary_captured, df_gas_captured, already_processed

        if current_state is None:
            buf = []
            return

        # Default passthrough
        if current_state == "other":
            new_lines.extend(buf)
            buf = []
            return

        if current_state == "zone_summary":
            df_zs = _read_df(buf)
            df_zs = _finalize_zone_summary(df_zs)
            df_zone_summary_captured = df_zs.copy()
            if not df_zs.empty:
                new_lines.append(df_zs.to_csv(index=False, lineterminator='\n'))
            else:
                new_lines.extend(buf)
            buf = []
            return

        if current_state == "building":
            df_bldg = _read_df(buf)
            if not df_bldg.empty:
                new_lines.append(df_bldg.to_csv(index=False, lineterminator="\n"))
            else:
                new_lines.extend(buf)
            buf = []
            return


        if current_state == "gas_equip":
            df_gas = _read_df(buf)
            if not df_gas.empty and "Zone Name" in df_gas.columns:
                df_gas = df_gas.copy()
                df_gas["Zone Type"] = df_gas["Zone Name"].apply(lambda z: find_zone_info(z, bldg_map_data)[0])
                df_gas_captured = df_gas.copy()
                new_lines.append(df_gas.to_csv(index=False, lineterminator='\n'))
            else:
                new_lines.extend(buf)
            buf = []
            return

        if current_state == "fan":
            df_existing = _read_df(buf)

            # Fan table should already be populated from Two_Direct_Extraction (HTM+IDF).
            # Here we only attach HVAC System Identifier using System name + zone map rules.
            df_final = df_existing.copy() if not df_existing.empty else pd.DataFrame()

            if not df_final.empty:
                df_final = attach_fan_hvac_identifier(df_final, df_zone_summary_captured)

                # De-dup per actual fan row (keep System name)
                subset_cols = []
                for c in ["Vintage", "HVAC name", "System name", "System Name", "System", "System type",
                          "Total Static Pressure (TSP) (in w.c.)",
                          "Fan Efficiency", "Fan Motor and Drive Efficiency", "W/cfm",
                          "HVAC System Identifier"]:
                    if c in df_final.columns:
                        subset_cols.append(c)

                if subset_cols:
                    df_final = df_final.drop_duplicates(subset=subset_cols, keep="first")

                # Write fan table
                new_lines.append(df_final.to_csv(index=False, lineterminator='\n'))

                sys_type_col = "System type" if "System type" in df_final.columns else ("System" if "System" in df_final.columns else None)

                overview_cols = [
                    "Vintage",
                    "HVAC name",
                    sys_type_col,
                    "HVAC System Identifier",
                    "Total Static Pressure (TSP) (in w.c.)",
                    "Fan Efficiency",
                    "Fan Motor and Drive Efficiency",
                    "W/cfm",
                ]

                # keep only cols that exist; if a required col is missing, skip overview generation safely
                if sys_type_col and all(c in df_final.columns for c in overview_cols):
                    df_overview = df_final[overview_cols].copy()
                    df_overview = df_overview.rename(columns={sys_type_col: "System type"})
                    df_overview = df_overview.drop_duplicates(subset=df_overview.columns.tolist(), keep="first")

                    new_lines.append("\n\n### FAN OVERVIEW ###\n")
                    new_lines.append(df_overview.to_csv(index=False, lineterminator='\n'))
                else:
                    # still add the section header for visibility (optional)
                    new_lines.append("\n\n### FAN OVERVIEW ###\n")
                    new_lines.append("No data\n")

            else:
                new_lines.extend(buf)

            buf = []
            return

        if current_state == "hvac":
            df_existing = _read_df(buf)
            _, df_new_hvac = extract_hvac_and_fan_info(idf_path, vintage_label, bldg_map_data, system_code)

            if not df_existing.empty and not df_new_hvac.empty:
                df_final = pd.concat([df_existing, df_new_hvac], ignore_index=True)
            elif not df_existing.empty:
                df_final = df_existing
            else:
                df_final = df_new_hvac

            subset_cols = ["HVAC System Identifier", "Air Distribution", "Heating Efficiency", "Cooling Efficiency"]
            if not df_final.empty:
                df_final = df_final.drop_duplicates(subset=subset_cols, keep='first')
                new_lines.append(df_final.to_csv(index=False, lineterminator='\n'))
            else:
                new_lines.extend(buf)

            buf = []
            return

        if current_state == "tstat":
            df_tstat = _read_df(buf)
            if not df_tstat.empty and "Zone Name" in df_tstat.columns:
                df_tstat = df_tstat.copy()

                # Add Schedule Identifier based on Zone Name → Zone Info mapping
                df_tstat["Schedule Identifier"] = df_tstat["Zone Name"].apply(
                    lambda z: find_zone_info(str(z).replace('"',''), bldg_map_data)[2]
                )

                # Drop Zone Type if it exists (since we have Schedule Identifier now, and Zone Type is redundant for this table)
                df_tstat = df_tstat.drop(columns=["Zone Type"], errors="ignore")

                # Write original thermostat table (still C)
                new_lines.append(df_tstat.to_csv(index=False, lineterminator="\n"))
                new_lines.append("\n")

                # apply C → F conversion and aggregate by Schedule Identifier
                summary_csv = generate_thermostat_summary_by_schedule_identifier(df_tstat)
                if summary_csv:
                    new_lines.append(summary_csv)
                    new_lines.append("\n")
            else:
                new_lines.extend(buf)

            buf = []
            return

        if current_state == "schedules":
            df_sched = _read_df(buf)
            if not df_sched.empty and "Zone Name" in df_sched.columns:
                df_sched = df_sched.copy()
                df_sched["Schedule Identifier"] = df_sched["Zone Name"].apply(
                    lambda z: find_zone_info(str(z).replace('"',''), bldg_map_data)[2]
                )

                # Clean/canonicalize schedule name first (so mask matches reliably)
                def keep_after_paren(s):
                    if pd.isna(s):
                        return s
                    s = str(s)
                    return s.split(")", 1)[1].strip() if ")" in s else s.strip()

                df_sched["Schedule Name"] = df_sched["Schedule Name"].apply(keep_after_paren)

                # Reuse canonical naming logic (same as in generate_aggregated_schedules)
                def canonical_schedule_name(s: str) -> str:
                    if pd.isna(s):
                        return s
                    s = re.sub(r"\s+", " ", str(s).strip())
                    s = re.sub(r"\s+\d+\s*$", "", s)

                    canonical = [
                        "Cooling Setpoint Schedule",
                        "Heating Setpoint Schedule",
                        "Infiltration Schedule",
                        "Lighting Schedule",
                        "OA Schedule",
                        "Occupant Sch",
                        "DHW Sch",
                        "Elec Equip Sch",
                    ]
                    sl = s.lower()
                    for lab in canonical:
                        if lab.lower() in sl:
                            return lab
                    return s

                df_sched["Schedule Name"] = df_sched["Schedule Name"].apply(canonical_schedule_name)
                df_sched = convert_setpoint_schedules_C_to_F(df_sched, "Schedule Name")
                new_lines.append(df_sched.to_csv(index=False, lineterminator='\n'))
                agg_df = generate_aggregated_schedules(df_sched)

                if not agg_df.empty:
                    new_lines.append("\n\n### SCHEDULE ###\n")
                    new_lines.append(agg_df.to_csv(index=False, lineterminator='\n'))
            else:
                new_lines.extend(buf)

            buf = []
            return

        if current_state == "dhw":
            df_dhw = _read_df(buf)
            if (not df_dhw.empty and not df_zone_summary_captured.empty
                and "Space" in df_dhw.columns and "Zone Name" in df_zone_summary_captured.columns):

                # ---------- helpers ----------
                def get_id_norm(x):
                    """Extract identifier in (...) and normalize (case-insensitive)."""
                    m = re.search(r"\(([^)]+)\)", str(x))
                    if not m:
                        return None
                    ident = " ".join(m.group(1).strip().split())
                    return ident.upper()

                def norm_name(s):
                    """Normalize names for case-insensitive matching."""
                    s = str(s).replace('"', "").strip()
                    s = re.sub(r"\s+", " ", s)
                    return s.casefold()

                def is_crs(name: str) -> bool:
                    return "CRS" in str(name).upper()

                # build map from zone name
                # store *lists* so we can prefer non-CRS
                id_map_list = {}    # (G.C5) -> [ZoneName1, ZoneName2, ...]
                name_map_list = {}  # normalized name -> [ZoneName1, ZoneName2, ...]

                for zn in df_zone_summary_captured["Zone Name"].astype(str):
                    # ID-based bucket
                    k_id = get_id_norm(zn)
                    if k_id:
                        id_map_list.setdefault(k_id, []).append(zn)

                    # Name-based bucket
                    k_nm = norm_name(zn)
                    name_map_list.setdefault(k_nm, []).append(zn)

                def pick_best(candidates):
                    """Prefer a non-CRS Zone Name; fallback to first if all are CRS."""
                    if not candidates:
                        return None
                    non_crs = [z for z in candidates if not is_crs(z)]
                    return non_crs[0] if non_crs else candidates[0]

                # assign Zone Name to DHW
                df_dhw = df_dhw.copy()

                def map_zone_name(space_val):
                    k_id = get_id_norm(space_val)
                    if k_id and k_id in id_map_list:
                        best = pick_best(id_map_list.get(k_id))
                        if best:
                            return best

                    k_nm = norm_name(space_val)
                    if k_nm in name_map_list:
                        best = pick_best(name_map_list.get(k_nm))
                        if best:
                            return best

                    stripped = re.sub(r"\s+DHW\b.*$", "", str(space_val), flags=re.IGNORECASE).strip()
                    k_nm2 = norm_name(stripped)
                    if k_nm2 in name_map_list:
                        best = pick_best(name_map_list.get(k_nm2))
                        if best:
                            return best

                    return "Unknown"

                df_dhw["Zone Name"] = df_dhw["Space"].apply(map_zone_name)

                new_lines.append(df_dhw.to_csv(index=False, lineterminator="\n"))
            else:
                new_lines.extend(buf)

            buf = []
            return


        # Fallback
        new_lines.extend(buf)
        buf = []

    # Iterate through lines, detect blocks, and capture tables
    for line in lines:
        stripped = line.strip()

        if "### INTERIOR LIGHTS ###" in stripped:
            already_processed = True

        # Detect block markers
        if stripped.startswith("###") and stripped.endswith("###"):
            # Flush previous block
            _flush(state)

            # Start new block
            state = "other"
            buf = []

            # Always write the marker line itself
            new_lines.append(line)

            if "### ZONE SUMMARY ###" in stripped:
                state = "zone_summary"
                continue
            if "### BUILDING ###" in stripped:
                state = "building"
                continue
            if "### GAS EQUIPMENT ###" in stripped:
                state = "gas_equip"
                continue
            if "### FAN ###" in stripped:
                state = "fan"
                continue
            if "### HVAC ###" in stripped:
                state = "hvac"
                continue
            if "### THERMOSTAT SETPOINTS (C) ###" in stripped:
                state = "tstat"
                continue
            if "### SCHEDULE PROFILES BY ZONE NAME ###" in stripped:
                state = "schedules"
                continue
            if "### DHW PEAK FLOW BY ZONE ###" in stripped:
                state = "dhw"
                continue

            state = "other"
            continue

        # End block on blank line (preserve blank line, but flush before it)
        if state in ["zone_summary", "building", "gas_equip", "fan", "hvac", "tstat", "schedules", "dhw"] and (not stripped):
            _flush(state)
            state = None
            new_lines.append(line)
            continue

        # Buffer or passthrough
        if state is None:
            new_lines.append(line)
        elif state == "other":
            new_lines.append(line)
        else:
            buf.append(line)

    # Flush trailing block if file doesn't end with blank line
    _flush(state)

    # Append derived summary tables if not already processed
    if not already_processed:
        if not df_zone_summary_captured.empty:
            try:
                df_gas = df_gas_captured if not df_gas_captured.empty else None
                table1, table2, table3, table4 = generate_summary_tables(df_zone_summary_captured, vintage_label, df_gas)

                if table1 and table2 and table3:
                    new_lines.append(table1 + "\n")
                    new_lines.append("\n" + table2 + "\n")
                    new_lines.append("\n" + table3 + "\n")
                if table4:
                    new_lines.append("\n" + table4 + "\n")
            except Exception as e:
                # print(f"  [Warning] Could not generate summary tables for {os.path.basename(file_path)}: {e}")
                pass
        else:
            # print(f"  [Warning] No Zone Summary captured for {os.path.basename(file_path)}; skipping summary tables.")
            pass
    else:
        # print(f"  [Info] '{os.path.basename(file_path)}' already processed.")
        pass

    # Write to new output location
    output_path = os.path.join(output_folder, os.path.basename(file_path))
    try:
        with open(output_path, 'w', encoding='utf-8-sig') as f:
            f.writelines(new_lines)
        # print(f"  [Success] Saved to '{os.path.basename(output_path)}'")
    except Exception as e:
        # print(f"  [Error] Could not write file: {e}")
        pass


# Exacuation
if __name__ == "__main__":
    # Define paths and constants
    pxt_root_path = PXT_ROOT_PATH
    scorecard_folder = SCORECARD_FOLDER
    base_ep_files = BASE_EP_FILES
    csv_target_folder = CSV_TARGET_FOLDER
    csv_output_folder = CSV_OUTPUT_FOLDER
    
    raw_json_path = RAW_JSON_PATH
    processed_json_path = PROCESSED_JSON_PATH

    # Generate & Save Maps
    raw_map = generate_zone_map(pxt_root_path)
    if raw_map:
        processed_map = create_processed_map(raw_map)
        
        try:
            os.makedirs(scorecard_folder, exist_ok=True)
            with open(raw_json_path, 'w', encoding='utf-8') as f:
                json.dump(raw_map, f, indent=4)
            with open(processed_json_path, 'w', encoding='utf-8') as f:
                json.dump(processed_map, f, indent=4)
        except Exception:
            pass

        # Process Files
        # print(f"Scanning files in: {csv_target_folder}")
        if os.path.exists(csv_target_folder):
            os.makedirs(csv_output_folder, exist_ok=True)
            files = [f for f in os.listdir(csv_target_folder) if f.lower().endswith('.csv')]
            
            for filename in files:
                file_path = os.path.join(csv_target_folder, filename)
                bldg_code = filename[:3]
                
                if bldg_code in processed_map:
                    process_file_full(file_path, csv_output_folder, bldg_code, processed_map, base_ep_files)
        else:
            # print(f"Error: Target directory not found at {csv_target_folder}")
            pass