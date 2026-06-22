import os
import glob
import pandas as pd
import io

def _require_env(key: str) -> str:
    v = os.environ.get(key)
    if not v or not str(v).strip():
        raise EnvironmentError(
            f"Missing required environment variable '{key}'. "
            "Run this script via Run2_Data_Extraction_Processing.py."
        )
    return str(v)

base_directory = _require_env("EP_FILES_ROOT")

input_dir = _require_env("INTERMEDIATE_DIR")
output_dir = _require_env("COMPILED_DIR")

input_pattern = os.path.join(input_dir, "*.csv")

# # Update path as needed
# base_directory = os.environ.get(
#     "EP_FILES_ROOT",
#     r"C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\ScorecardAutomation\EP_Files"
# )

# input_dir = os.environ.get("INTERMEDIATE_DIR", os.path.join(base_directory, "Extracted_Data_Intermediate_Processed"))
# output_dir = os.environ.get("COMPILED_DIR", os.path.join(base_directory, "Compiled_Data"))

# input_pattern = os.path.join(input_dir, "*.csv")

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


def get_metadata(filename):
    base = os.path.basename(filename)
    if "_Ex_" in base or base.endswith("_Ex.csv") or "Ex_" in base:
        return "Existing"
    elif "_New_" in base or base.endswith("_New.csv") or "New_" in base:
        return "New Construction"
    return "Unknown"

def clean_header(header_line):
    # Removes invisible BOM characters (\ufeff) and extra spaces
    return header_line.strip().replace('\ufeff', '')

def parse_multi_table_csv(filepath):
    sections = {}
    current_lines = []
    current_key = None
    
    try:
        # utf-8-sig handles the invisible BOM character automatically
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if not line: continue
            
            clean_line = clean_header(line)
            
            # Detect section headers
            is_header = (clean_line.startswith("###") and clean_line.endswith("###")) or \
                        (clean_line.startswith("---") and clean_line.endswith("---"))
            
            if is_header:
                # Process previous section
                if current_key is not None and current_lines:
                    csv_str = "\n".join(current_lines)
                    try:
                        # keep_default_na=False prevents "None" from becoming NaN immediately
                        sections[current_key] = pd.read_csv(io.StringIO(csv_str), keep_default_na=False, na_values=[''])
                    except:
                        sections[current_key] = pd.DataFrame()
                
                current_key = clean_line
                current_lines = []
            else:
                if current_key:
                    current_lines.append(line)
                    
        # Process last section
        if current_key is not None and current_lines:
            csv_str = "\n".join(current_lines)
            try:
                sections[current_key] = pd.read_csv(io.StringIO(csv_str), keep_default_na=False, na_values=[''])
            except:
                sections[current_key] = pd.DataFrame()
                
    except Exception as e:
        # print(f"Error reading file {filepath}: {e}")
        return {}

    return sections

def process_building_group(bldg_code, files, save_folder):
    print(f"Processing Group: {bldg_code} ({len(files)} files)")
    
    static_tables = {}  
    dynamic_tables = {} 
    
    dynamic_headers = [
        "### ZONE SUMMARY ###",
        "### ENVELOPE ###",
        "### INFILTRATION (CFM/ft2) ###",
        "### WATER HEATER ###",
        "### OA CONTROLLER ###",
        "### TOTAL END USES (Annual) ###",
        "### END USE BREAKDOWN (Annual) ###",
        "### HVAC ###",
        "### FAN OVERVIEW ###",
        "### INTERIOR LIGHTS ###",
        "### EQUIPMENT ###",
        "### REFRIGERATION SYSTEM ###",
        "### GAS EQUIPMENT ###"
    ]
    
    for file_path in files:
        vintage = get_metadata(file_path)
        sections = parse_multi_table_csv(file_path)
        
        for header, df in sections.items():
            if df.empty: continue


            # ### BUILDING ###
            if "### BUILDING ###" in header:
                if "File Name" in df.columns:
                    df = df.drop(columns=["File Name"])

            # # ### WHOLE BUILDING PEAK WATER FLOW ###
            # if "### WHOLE BUILDING PEAK WATER FLOW" in header:
            #     cols_to_drop = [c for c in df.columns if "Climate Zone" in c]
            #     df = df.drop(columns=cols_to_drop, errors='ignore')

            # ### WATER HEATER SUMMARY ###
            if "### WATER HEATER" in header:
                cols_to_drop = [c for c in df.columns if "Climate Zone" in c]
                df = df.drop(columns=cols_to_drop, errors='ignore')

            # Ensure 'None' becomes '-' in Zone Summary
            if "### ZONE SUMMARY ###" in header:
                # 1. Fill NaNs with "-"
                # 2. Replace empty strings/whitespace with "-"
                # 3. Replace literal string "None" with "-"
                df = df.fillna("-").replace(r'^\s*$', '-', regex=True).replace('None', '-')

            # Add "Vintage" column to dynamic tables
            if header in dynamic_headers:
                if "Vintage" not in df.columns:
                    df.insert(0, "Vintage", vintage)

            
            if header in dynamic_headers:
                if header not in dynamic_tables:
                    dynamic_tables[header] = []
                dynamic_tables[header].append(df)
            else:
                if header not in static_tables:
                    static_tables[header] = df

    
    output_order = [
        "### BUILDING ###",
        "### WINDOW DIMENSION & SILL HEIGHT ###",
        "### SHADING GEOMETRY ###",
        "### RUN BEGIN DAY ###",
        "### SPECIAL DAYS ###",
        "### ZONE SUMMARY ###",
        "### ENVELOPE ###",
        "### INFILTRATION (CFM/ft2) ###",
        "### WATER HEATER ###",
        "### OA CONTROLLER ###",
        "### DHW PEAK FLOW BY ZONE ###",
        # "### WHOLE BUILDING PEAK WATER FLOW (Simulated) ###",
        "### TOTAL END USES (Annual) ###",
        "### END USE BREAKDOWN (Annual) ###",
        # "### SCHEDULE PROFILES BY ZONE NAME ###",
        "### HVAC ###",
        "### FAN OVERVIEW ###",
        "### INTERIOR LIGHTS ###",
        "### EQUIPMENT ###",
        "### OUTDOOR AIRFLOW RATE ###",
        "### REFRIGERATION SYSTEM ###",
        "### THERMOSTAT SETPOINTS ###",
        "### SCHEDULE ###",
        "### GAS EQUIPMENT ###"
    ]
    
    final_dfs = []
    
    for header in output_order:
        df_result = pd.DataFrame()
        
        # Combine data
        if header in dynamic_tables and dynamic_tables[header]:
            df_result = pd.concat(dynamic_tables[header], ignore_index=True)
        elif header in static_tables:
            df_result = static_tables[header]
            
        # Drop duplicates
        if not df_result.empty:
            df_result = df_result.drop_duplicates()
            final_dfs.append((header, df_result))


    out_filename = os.path.join(save_folder, f"{bldg_code}_raw.csv")
    
    try:
        with open(out_filename, 'w', newline='', encoding='utf-8') as f:
            for header, df in final_dfs:
                f.write(f"{header}\n")
                df.to_csv(f, index=False)
                f.write("\n\n") 
        # print(f"  -> Saved: {out_filename}")
    except PermissionError:
        # print(f"  -> ERROR: Could not write to {out_filename}. Is it open in Excel?")
        pass


# Execution
if __name__ == "__main__":
    if not os.path.exists(input_dir):
        # print(f"Error: Input directory not found: {input_dir}")
        exit()
        
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    all_files = glob.glob(input_pattern)
    # print(f"Found {len(all_files)} CSV files.")
    
    grouped_files = {}
    for f in all_files:
        basename = os.path.basename(f)
        parts = basename.split('_')
        if len(parts) > 0:
            code = parts[0]
            if code in building_type_map:
                if code not in grouped_files:
                    grouped_files[code] = []
                grouped_files[code].append(f)
    
    for code, file_list in grouped_files.items():
        process_building_group(code, file_list, output_dir)

    print("\nAll processing complete.")