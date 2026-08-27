import os
import subprocess
import re


def _require_env(key: str) -> str:
    v = os.environ.get(key)
    if not v or not str(v).strip():
        raise EnvironmentError(
            f"Missing required environment variable '{key}'. "
            "Run this script via Run1_Pre_Data_Extraction.py."
        )
    return str(v)

ep_install_dir = _require_env("EP_INSTALL_DIR")
ep_exe_path = os.path.join(ep_install_dir, "energyplus.exe")

idf_root_dir = _require_env("EP_FILES_ROOT")
weather_dir = _require_env("WEATHER_DIR")

# # Path to the EnergyPlus executable
# ep_install_dir = r"C:\EnergyPlusV22-2-0"
# ep_exe_path = os.path.join(ep_install_dir, "energyplus.exe")

# # Root folder where we extracted the IDFs
# idf_root_dir = r"C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\ScorecardAutomation\EP_Files"

# # Folder containing your .epw weather files
# weather_dir = r"C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\weather"

# MAPPING: Climate Zone -> Weather Filename
weather_map = {
    "CZ01": "CA_EUREKA_725940S_CZ2022.epw", 
    "CZ02": "CA_NAPA-CO_724955S_CZ2022.epw",
    "CZ03": "CA_OAKLAND-METRO-AP_724930S_CZ2022.epw",
    "CZ04": "CA_SAN-JOSE-IAP_724945S_CZ2022.epw",
    "CZ05": "CA_SANTA-MARIA-PUBLIC-AP_723940S_CZ2022.epw",
    "CZ06": "CA_LOS-ANGELES-IAP_722950S_CZ2022.epw",
    "CZ07": "CA_SAN-DIEGO-LINDBERGH-FLD_722900S_CZ2022.epw",
    "CZ08": "CA_LONG-BEACH-DAUGHERTY-FLD_722970S_CZ2022.epw",
    "CZ09": "CA_LOS-ANGELES-DOWNTOWN-USC_722874S_CZ2022.epw",
    "CZ10": "CA_RIVERSIDE-MUNI_722869S_CZ2022.epw",
    "CZ11": "CA_RED-BLUFF-MUNI-AP_725910S_CZ2022.epw",
    "CZ12": "CA_STOCKTON-METRO-AP_724920S_CZ2022.epw",
    "CZ13": "CA_FRESNO-YOSEMITE-IAP_723890S_CZ2022.epw",
    "CZ14": "CA_DAGGETT-BARSTOW-AP_723815S_CZ2022.epw",
    "CZ15": "CA_EL-CENTRO-NAF_722810S_CZ2022.epw",
    "CZ16": "CA_BISHOP-AP_724800S_CZ2022.epw"
}


def modify_idf(idf_path):
    """
    Edits the IDF file in place.
    1. Replaces (or adds) OutputControl:Table:Style with InchPound.
    2. Adds Water Use Equipment output variable after Site Outdoor Air Drybulb Temperature.
    """
    try:
        with open(idf_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Replacement block
        new_style_block = "OutputControl:Table:Style,\n    CommaAndHTML,            !- Column Separator\n    InchPound;               !- Unit Conversion"
        
        # Regex to match existing object and consume the trailing comment
        style_pattern = r"OutputControl:Table:Style\s*,[\s\S]*?;[^\n]*"
        
        if re.search(style_pattern, content, re.IGNORECASE):
            content = re.sub(style_pattern, new_style_block, content, flags=re.IGNORECASE)
            # print(f"  [Info] Replaced existing OutputControl:Table:Style.")
        else:
            # print(f"  [Info] OutputControl:Table:Style not found. Appending to end.")
            content += "\n\n" + new_style_block + "\n"

        # The new variable block to insert
        new_variable = "\n	Output:Variable,*,Water Use Equipment Hot Water Volume Flow Rate,Hourly; !- Zone Average\n	Output:Schedules, Hourly;     ! values on hourly increments\n"
        # Anchor Regex: 
        # 1. Start with Output:Variable
        # 2. Match anything (non-greedy) until "Site Outdoor Air Drybulb Temperature"
        # 3. Match anything until the closing semicolon
        # 4. Consume the rest of that line (comments like !- Zone Average [C])
        anchor_pattern = r"(Output:Variable,[^;]*?Site Outdoor Air Drybulb Temperature[^;]*?;[^\n]*)"
        
        if re.search(anchor_pattern, content, re.IGNORECASE):
            # Insert AFTER the entire matched anchor line/block
            content = re.sub(anchor_pattern, r"\1" + new_variable, content, flags=re.IGNORECASE)
            # print(f"  [Info] Inserted Water Variable after 'Site Outdoor Air'.")
        else:
            # print(f"  [Info] Anchor variable not found. Appending Water Variable to end.")
            content += "\n" + new_variable

        with open(idf_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return True

    except Exception as e:
        # print(f"  [Error] Failed to modify IDF: {e}")
        return False

print(f"Working through IDFs in: {idf_root_dir}\n")

success_count = 0
error_count = 0

# Walk through the directory structure
for root, dirs, files in os.walk(idf_root_dir):
    for file in files:
        if file.lower().endswith(".idf"):
            idf_path = os.path.join(root, file)
            
            parent_folder = os.path.basename(root)  # e.g., "CZ01"
            
            if parent_folder in weather_map:
                weather_file_name = weather_map[parent_folder]
                weather_path = os.path.join(weather_dir, weather_file_name)
                
                # Check if weather file exists
                if not os.path.exists(weather_path):
                    # print(f"[Error] Weather file not found: {weather_path}")
                    error_count += 1
                    continue
                
                print(f"Processing: {file} (Zone: {parent_folder})")

                # --- STEP 1: MODIFY IDF ---
                if modify_idf(idf_path):
                    # print(f"  [Info] IDF Modified successfully.")
                    pass
                else:
                    # print(f"  [Fail] Could not modify IDF. Skipping simulation.")
                    error_count += 1
                    continue

                # --- STEP 2: RUN SIMULATION ---
                file_prefix = os.path.splitext(file)[0]

                cmd = [
                    ep_exe_path,
                    "-w", weather_path,
                    "-d", root,         # Output results to the same folder as the IDF
                    "-p", file_prefix,  # Name outputs: OfS_0_cAVVG.csv, etc.
                    "-r", # cannot skip this, it tells EP to run the simulation
                    idf_path
                ]

                try:
                    # Run simulation
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print(f"  [Success] Simulation complete.")
                        success_count += 1
                    else:
                        print(f"  [Fail] EnergyPlus returned error code {result.returncode}")
                        # Uncomment below to see detailed EnergyPlus error messages
                        # print(result.stderr)
                        error_count += 1
                        
                except Exception as e:
                    print(f"  [Error] Script execution failed: {e}")
                    error_count += 1

            else:
                # If folder isn't CZ01-CZ16, skip
                pass

print(f"\n Simulation Complete")
print(f"Successful Runs: {success_count}")
print(f"Failed Runs:     {error_count}")