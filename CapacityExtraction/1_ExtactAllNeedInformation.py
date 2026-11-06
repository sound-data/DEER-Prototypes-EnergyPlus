import os
import csv
import glob

from Extraction_Lib import (
    extract_fan_data,
    extract_dx_cooling_coil_data,
    extract_cooling_coil_load
)

# Define the path to the target IDF file
base_root_dir = os.environ.get(
    "EP_FILES_ROOT",
    r"C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\CapacityExtraction\EP_Files"
)
output_folder = os.environ.get(
    "EXTRACTED_RAW_DIR",
    r"C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\CapacityExtraction\Extracted_Data_Raw"
)
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

for building_type_folder in os.listdir(base_root_dir):
    building_type_path = os.path.join(base_root_dir, building_type_folder)
 
    if not os.path.isdir(building_type_path) or building_type_folder == "Extracted_Data":
        continue
 
    for vintage_folder in os.listdir(building_type_path):
        vintage_path = os.path.join(building_type_path, vintage_folder)
        report_vintage = vintage_folder.replace("-", " ")
 
        if not os.path.isdir(vintage_path):
            continue
 
        cz01_path = os.path.join(vintage_path, "CZ01")
        if not os.path.exists(cz01_path):
            continue
 
        cz01_files = glob.glob(os.path.join(cz01_path, "*.idf"))
 
        for cz01_file_path in cz01_files:
            filename   = os.path.basename(cz01_file_path)
            hvac_name  = filename.split("_")[2]
 
            csv_filename    = filename.replace(".idf", ".csv")
            output_csv_path = os.path.join(output_folder, csv_filename)
 
            all_fan_rows          = []
            all_dx_coil_rows      = []   # keyed by CZ for sentinel logic
            all_cooling_coil_rows = []
 
            for i in range(1, 17):
                cz_name = f"CZ{i:02}"
                cz_idf  = os.path.join(vintage_path, cz_name, filename)
 
                if not os.path.exists(cz_idf):
                    continue
 
                for rec in extract_fan_data(cz_idf):
                    rec["Climate Zone"] = cz_name
                    all_fan_rows.append(rec)
 
                for rec in extract_dx_cooling_coil_data(cz_idf):
                    rec["Climate Zone"] = cz_name
                    all_dx_coil_rows.append(rec)
 
                for rec in extract_cooling_coil_load(cz_idf):
                    rec["Climate Zone"] = cz_name
                    all_cooling_coil_rows.append(rec)
 
            try:
                with open(output_csv_path, "w", newline="") as f:
                    writer = csv.writer(f)
 
                    # Table 1: Fan
                    writer.writerow(["### FAN ###"])
                    writer.writerow([
                        "Climate Zone", "Vintage", "HVAC name",
                        "System name", "Rated Electricity Rate [W]",
                    ])
                    for rec in all_fan_rows:
                        writer.writerow([
                            rec["Climate Zone"],
                            rec["Vintage"],
                            rec["HVAC name"],
                            rec["System name"],
                            rec.get("Rated Electricity Rate [W]", "N/A"),
                        ])
 
                    writer.writerow([])
                    writer.writerow([])
 
                    # Table 2: DX Cooling Coils [SEER2]
                    writer.writerow(["### DX COOLING COILS [SEER2] ###"])
                    writer.writerow([
                        "Climate Zone", "Vintage", "HVAC name",
                        "Coil name", "Standard Rated Net Cooling Capacity [W]",
                    ])
 
                    # Group real DX rows by CZ for interleaved sentinel insertion
                    dx_by_cz = {}
                    for rec in all_dx_coil_rows:
                        dx_by_cz.setdefault(rec["Climate Zone"], []).append(rec)
 
                    for i in range(1, 17):
                        cz_name = f"CZ{i:02}"
                        cz_rows = dx_by_cz.get(cz_name, [])
                        if cz_rows:
                            for rec in cz_rows:
                                writer.writerow([
                                    rec["Climate Zone"],
                                    rec["Vintage"],
                                    rec["HVAC name"],
                                    rec["Coil name"],
                                    rec["Standard Rated Net Cooling Capacity [W]"],
                                ])
                        else:
                            # No DX coils for this CZ — write sentinel
                            writer.writerow([cz_name, report_vintage, hvac_name, "None", "N/A"])
 
                    writer.writerow([])
                    writer.writerow([])
 
                    # Table 3: Cooling Coils (Design Load)
                    writer.writerow(["### COOLING COILS ###"])
                    writer.writerow([
                        "Climate Zone", "Vintage", "HVAC name",
                        "Coil name", "Design Coil Load [W]",
                    ])
                    for rec in all_cooling_coil_rows:
                        writer.writerow([
                            rec["Climate Zone"],
                            rec["Vintage"],
                            rec["HVAC name"],
                            rec["Coil name"],
                            rec["Design Coil Load [W]"],
                        ])
 
            except IOError as e:
                print(f"Error writing CSV {csv_filename}: {e}")
 
print("\nData extraction complete.")
 