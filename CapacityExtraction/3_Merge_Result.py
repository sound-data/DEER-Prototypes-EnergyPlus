import os
import io
import glob
import pandas as pd

INPUT_DIR = os.environ.get(
    "INTERMEDIATE_DIR",
    r"C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\CapacityExtraction\Extracted_Data_Intermediate_Processed"
)
OUTPUT_DIR = os.environ.get(
    "COMPILED_DIR",
    r"C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\CapacityExtraction\Compiled_Data"
)

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

COL_CZ       = "Climate Zone"
COL_VINT     = "Vintage"
COL_HVAC     = "HVAC name"
COL_COIL     = "Coil name"
COL_IDENT    = "HVAC System Identifier"
COL_CAP_DX   = "Standard Rated Net Cooling Capacity [W]"
COL_LOAD     = "Design Coil Load [W]"
COL_FAN_RATE = "Rated Electricity Rate [W]"

COL_NET_CAP  = "Net Cooling Capacity [W]"
COL_FAN_OUT  = "Fan Rated Electricity Rate [W]"

GROUP_KEYS   = [COL_CZ, COL_VINT, COL_HVAC, COL_IDENT]

def _to_float(val) -> float | None:
    """Return float if val is a valid number, else None."""
    try:
        v = float(str(val).strip())
        return v if pd.notna(v) else None
    except (ValueError, TypeError):
        return None


def _read_main_capacity_section(filepath: str) -> pd.DataFrame:
    """
    Parse ### MAIN CAPACITY SUMMARY ### from a multi-section CSV.
    Uses keep_default_na=False so 'N/A' stays as the string 'N/A'.
    """
    in_section = False
    buf = []
    with open(filepath, encoding="utf-8-sig", errors="ignore") as f:
        for line in f:
            stripped = line.strip()
            if stripped == "### MAIN CAPACITY SUMMARY ###":
                in_section = True
                continue
            if in_section:
                if stripped.startswith("###"):
                    break
                buf.append(line)
    if not buf:
        return pd.DataFrame()
    try:
        return pd.read_csv(
            io.StringIO("".join(buf)),
            skip_blank_lines=True,
            keep_default_na=False,
            na_values=[""]
        )
    except Exception:
        return pd.DataFrame()


def compute_net_capacity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add Net Cooling Capacity [W] and Fan Rated Electricity Rate [W] columns
    at row level, then return the enriched DataFrame.

    Row logic:
      cap_dx  = Standard Rated Net Cooling Capacity [W]  (number or None)
      load    = Design Coil Load [W]                     (number or None)
      fan     = Rated Electricity Rate [W]               (number or None)

      Net Cooling Capacity [W]:
        if cap_dx is number  -> cap_dx
        elif load is number  -> load - fan  (fan treated as 0 if None)
        else                 -> None  (will become N/A after aggregation)
    """
    rows_net = []
    rows_fan = []

    for _, row in df.iterrows():
        cap_dx = _to_float(row.get(COL_CAP_DX))
        load   = _to_float(row.get(COL_LOAD))
        fan    = _to_float(row.get(COL_FAN_RATE))

        # Net Cooling Capacity
        if cap_dx is not None:
            net = cap_dx
        elif load is not None:
            net = load - (fan if fan is not None else 0.0)
        else:
            net = None

        rows_net.append(net)
        rows_fan.append(fan)

    df = df.copy()
    df[COL_NET_CAP] = rows_net   # float or None
    df[COL_FAN_OUT] = rows_fan   # float or None
    return df


def aggregate_by_group(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sum Net Cooling Capacity [W] and Fan Rated Electricity Rate [W]
    within each (Climate Zone, Vintage, HVAC name, HVAC System Identifier) group.
    Groups where ALL rows are None in a column get 'N/A'; otherwise numeric sum.
    """
    df = compute_net_capacity(df)

    results = []
    for keys, grp in df.groupby(GROUP_KEYS, sort=False):
        cz, vint, hvac, ident = keys

        net_vals = [v for v in grp[COL_NET_CAP] if v is not None]
        fan_vals = [v for v in grp[COL_FAN_OUT] if v is not None]

        net_sum = round(sum(net_vals), 4) if net_vals else "N/A"
        fan_sum = round(sum(fan_vals), 4) if fan_vals else "N/A"

        results.append({
            COL_CZ:    cz,
            COL_VINT:  vint,
            COL_HVAC:  hvac,
            COL_IDENT: ident,
            COL_NET_CAP: net_sum,
            COL_FAN_OUT: fan_sum,
        })

    return pd.DataFrame(results, columns=[
        COL_CZ, COL_VINT, COL_HVAC, COL_IDENT, COL_NET_CAP, COL_FAN_OUT
    ])

def process_prototype(bldg_code: str, files: list[str], output_dir: str):
    print(f"  Processing {bldg_code} ({len(files)} files)...")

    all_rows = []
    for fp in sorted(files):
        df = _read_main_capacity_section(fp)
        if df.empty:
            continue
        # Tag with source filename for debugging if needed
        all_rows.append(df)

    if not all_rows:
        print(f"    [Skip] No MAIN CAPACITY SUMMARY data found.")
        return

    df_all = pd.concat(all_rows, ignore_index=True)

    # Drop rows where HVAC System Identifier is not "Main"
    # (safety guard — section should already be Main-only)
    if COL_IDENT in df_all.columns:
        df_all = df_all[
            df_all[COL_IDENT].astype(str).str.strip().str.upper() == "MAIN"
        ].copy()

    if df_all.empty:
        print(f"    [Skip] No Main rows after filtering.")
        return

    df_result = aggregate_by_group(df_all)

    out_path = os.path.join(output_dir, f"{bldg_code}_capacity.csv")
    df_result.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"    [OK] {len(df_result)} rows -> {os.path.basename(out_path)}")


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_files = glob.glob(os.path.join(INPUT_DIR, "*.csv"))
    if not all_files:
        print(f"[Error] No CSV files found in: {INPUT_DIR}")
        exit(1)

    print(f"Found {len(all_files)} files in {INPUT_DIR}")

    # Group files by building prototype code (first 3 chars of filename)
    grouped: dict[str, list[str]] = {}
    for fp in all_files:
        code = os.path.basename(fp)[:3]
        if code in BUILDING_TYPE_MAP:
            grouped.setdefault(code, []).append(fp)
        else:
            print(f"  [Note] Unknown code '{code}' for {os.path.basename(fp)} — skipped")

    for code, file_list in sorted(grouped.items()):
        process_prototype(code, file_list, OUTPUT_DIR)

    print("\nAll done.")