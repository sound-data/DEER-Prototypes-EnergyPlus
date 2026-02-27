import os
import csv
import glob

# TODO: Add roof angle calculation to determine roof type (low sloped and steep sloped)

from Extraction_Lib import (
    get_building_type, 
    get_building_category, 
    extract_run_begin_day, 
    extract_special_days,
    get_roof_type,
    get_glazing_sill_height,
    extract_zone_summary,
    extract_wwr,
    get_win_dimension,
    extract_envelope_data,
    extract_infiltration_rate,
    extract_water_heater,
    extract_oa_controller_temp,
    extract_dhw_peak_flow,
    # get_whole_building_peak_water,
    extract_total_end_uses,
    extract_schedule_profile,
    extract_hvac_params,
    extract_fan_data,
    extract_gas_equipment,
    extract_refrigeration_system,
    extract_zone_thermostats,
    extract_end_use_breakdown,
    extract_shading_data
)

def _require_env(key: str) -> str:
    v = os.environ.get(key)
    if not v or not str(v).strip():
        raise EnvironmentError(
            f"Missing required environment variable '{key}'. "
            "Run this script via Run2_Data_Extraction_Processing.py."
        )
    return str(v)

# Define the path to the target IDF file
base_root_dir = _require_env("EP_FILES_ROOT")
output_folder = _require_env("EXTRACTED_RAW_DIR")

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# # Define the path to the target IDF file
# base_root_dir = os.environ.get(
#     "EP_FILES_ROOT",
#     r"C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\ScorecardAutomation\EP_Files"
# )
# output_folder = os.environ.get("EXTRACTED_RAW_DIR", os.path.join(base_root_dir, "Extracted_Data_Raw"))

# if not os.path.exists(output_folder):
#     os.makedirs(output_folder)

# Main Processing Loop

# Loop through Building Types (e.g., OfS, Asm...)
for building_type_folder in os.listdir(base_root_dir):
    building_type_path = os.path.join(base_root_dir, building_type_folder)
    
    if not os.path.isdir(building_type_path) or building_type_folder == "Extracted_Data":
        continue

    # Loop through Vintages
    for vintage_folder in os.listdir(building_type_path):
        vintage_path = os.path.join(building_type_path, vintage_folder)
        
        # Clean up the name for reporting
        report_vintage = vintage_folder.replace('-', ' ') 
        
        if not os.path.isdir(vintage_path):
            continue

        # Locate CZ01 Folder
        cz01_path = os.path.join(vintage_path, "CZ01")
        if os.path.exists(cz01_path):
            cz01_files = glob.glob(os.path.join(cz01_path, "*.idf"))

        for cz01_file_path in cz01_files:
                filename = os.path.basename(cz01_file_path)
                hvac_name = filename.split('_')[2]

                # Output CSV Name
                csv_filename = filename.replace('.idf', '.csv')
                output_csv_path = os.path.join(output_folder, csv_filename)

                bldg_type = get_building_type(filename)
                category = get_building_category(filename)
                roof_type = get_roof_type(cz01_file_path)
                
                # Define paths for HTM and EIO
                cz01_htm = cz01_file_path.replace(".idf", "tbl.htm")
                cz01_eio = cz01_file_path.replace(".idf", "out.eio")
                cz01_sql = cz01_file_path.replace(".idf", "out.sql")

                
                # extract various data
                zone_rows = extract_zone_summary(cz01_htm, cz01_eio, cz01_file_path)
                wwr_value = extract_wwr(cz01_htm)
                window_rows = get_win_dimension(cz01_eio)
                sill_height = get_glazing_sill_height(cz01_file_path)
                shading_info = extract_shading_data(cz01_file_path)
                dhw_rows = extract_dhw_peak_flow(cz01_file_path)
                run_begin_day = extract_run_begin_day(cz01_file_path)  
                special_days_rows = extract_special_days(cz01_file_path)
                schedule_rows = []
                if os.path.exists(cz01_eio):
                    schedule_rows = extract_schedule_profile(cz01_eio, cz01_file_path)
                else:
                    schedule_rows = []
                    # print(f"Warning: EIO file not found at {cz01_eio}")
                hvac_data = extract_hvac_params(cz01_file_path, filename)
                fan_rows = extract_fan_data(cz01_file_path)
                gas_data = extract_gas_equipment(cz01_file_path)
                ref_data = extract_refrigeration_system(cz01_file_path, filename)

                # Loop through Climate Zones CZ01 to CZ16
                envelope_rows = []
                infil_map = {}
                wh_rows_all = []
                oa_rows = []
                peak_water_rows = []
                energy_rows = []
                all_thermostat_rows = []
                all_end_use_breakdown_rows = []
                for i in range(1, 17):
                    cz_name = f"CZ{i:02}"
                    current_idf = os.path.join(vintage_path, cz_name, filename)
                    current_htm = current_idf.replace(".idf", "tbl.htm")
                    current_result_csv = current_idf.replace(".idf", "out.csv")

                    if os.path.exists(current_idf):
                        # Envelope
                        env = extract_envelope_data(current_idf, current_htm)
                        env["Climate Zone"] = cz_name
                        envelope_rows.append(env)
                        
                        # Water heater
                        wh_list = extract_water_heater(current_idf, current_htm)
                        for wh in wh_list:
                            wh["Climate Zone"] = cz_name
                            wh_rows_all.append(wh)
 
                        oa_temp = extract_oa_controller_temp(current_idf)
                        oa_rows.append({"Climate Zone": cz_name, "Temp": oa_temp})

                        # peak_val = get_whole_building_peak_water(current_result_csv)
                        # peak_water_rows.append({
                        #     "Climate Zone": cz_name, 
                        #     "Peak Flow": peak_val
                        # })

                        # Annual Energy
                        elec_val, gas_val = extract_total_end_uses(current_htm)
                        energy_rows.append({
                            "Climate Zone": cz_name,
                            "Electricity": elec_val,
                            "Natural Gas": gas_val
                        })

                        # Detailed End Use Breakdown (NEW LOOP LOGIC)
                        breakdown_rows = extract_end_use_breakdown(current_htm)
                        if breakdown_rows:
                            for br in breakdown_rows:
                                br["Climate Zone"] = cz_name
                                all_end_use_breakdown_rows.append(br)

                        infil_val = extract_infiltration_rate(current_idf)
                        infil_map[cz_name] = infil_val
                        tstat_data = extract_zone_thermostats(current_idf)
                        for t_row in tstat_data:
                            t_row["Climate Zone"] = cz_name
                            all_thermostat_rows.append(t_row)
                        
                    else:
                        # Handle missing files
                        envelope_rows.append({"Climate Zone": cz_name, "Vintage": "File Not Found"})
                        oa_rows.append({"Climate Zone": cz_name, "Temp": "File Not Found"})
                        peak_water_rows.append({"Climate Zone": cz_name, "Peak Flow": "File Not Found"})
                        energy_rows.append({
                            "Climate Zone": cz_name, 
                            "Electricity": "File Not Found", 
                            "Natural Gas": "File Not Found"
                        })
                        all_thermostat_rows.append({
                            "Climate Zone": cz_name,
                            "Zone Name": "File Not Found",
                            "Heating Setpoint": "-", "Heating Setback": "-",
                            "Cooling Setpoint": "-", "Cooling Setback": "-"
                        })

                # Write to CSV
                try:
                    with open(output_csv_path, 'w', newline='') as f:
                        writer = csv.writer(f)

                        # Table 1: Metadata (UPDATED with WWR)
                        writer.writerow(["### BUILDING ###"])
                        writer.writerow(["File Name", "Building Type", "Building Category", "Roof Type", "Window Wall Ratio (%)"])
                        writer.writerow([filename, bldg_type, category, roof_type, wwr_value])
                        if window_rows:
                            writer.writerow([])
                            writer.writerow([])
                            writer.writerow(["### WINDOW DIMENSION & SILL HEIGHT ###"])
                            writer.writerow(["Window Name", "Width [ft]", "Height [ft]", "Sill Height [ft]"])
                            
                            for w in window_rows:
                                w_name = w["Window Name"]
                                # Lookup sill height, default to N/A if not found
                                s_height = sill_height.get(w_name, "N/A")
                                writer.writerow([w_name, w["Width [ft]"], w["Height [ft]"], s_height])
                        else:
                            writer.writerow([])
                            writer.writerow([])
                            writer.writerow(["No Window Dimensions Found"])

                        writer.writerow([])
                        writer.writerow([])

                        # Table 1.1: run begin day (NEW)
                        writer.writerow(["### RUN BEGIN DAY ###"])
                        writer.writerow(["Begin Month", "Begin Day of Month", "Day of Week for Start Day"])
                        writer.writerow([
                            run_begin_day.get("Begin Month", "N/A"),
                            run_begin_day.get("Begin Day of Month", "N/A"),
                            run_begin_day.get("Day of Week for Start Day", "N/A")
                        ])
                        writer.writerow([])
                        writer.writerow([])

                        # Table 1.2: Special Days (NEW)
                        writer.writerow(["### SPECIAL DAYS ###"])
                        writer.writerow(["Name", "Start Day", "Duration", "Special Day Type"])

                        if special_days_rows:
                            for r in special_days_rows:
                                writer.writerow([
                                    r.get("Name", "N/A"),
                                    r.get("Start Day", "N/A"),
                                    r.get("Duration", "N/A"),
                                    r.get("Special Day Type", "N/A")
                                ])
                        else:
                            writer.writerow(["No RunPeriodControl:SpecialDays found.", "", "", ""])
                        writer.writerow([])
                        writer.writerow([])
                        
                        # Table 1.3: Shading Geometry
                        writer.writerow(["### SHADING GEOMETRY ###"])
                        writer.writerow(["Shading Name", "Width [ft]", "Length [ft]"])
                        
                        if shading_info:
                            for row in shading_info:
                                writer.writerow([
                                    row.get("Shading Name", "Unknown"),
                                    row.get("Width", "0"),
                                    row.get("Length", "0")
                                ])
                        else:
                            # If no shading, keep headers but input "No Shading"
                            writer.writerow(["No Shading", "", ""])
                        
                        writer.writerow([])
                        writer.writerow([])

                        # Table 2: Zone Summary
                        writer.writerow(["### ZONE SUMMARY ###"])
                        writer.writerow([
                            "Space", "Zone Name", "Conditioned", 
                            "Area (Excluding Plenums and CrawlSpace) (ft2)", "Area (Including Plenums and CrawlSpace) (ft2)", # New Column Added
                            "Width (ft)", "Length (ft)",
                            "Volume (ft3)", "Multipliers", "People (Persons/1000 ft2)", 
                            "Lighting (Btu/h-ft2)", "Plug Loads (Btu/h-ft2)",
                            "Outdoor Air Flow per Person (cfm/person)",
                            "Outdoor Air Flow per Zone Floor Area (cfm/ft2)"
                        ])
                        if zone_rows:
                            for z in zone_rows:
                                writer.writerow([
                                    z["Space"], z["Zone Name"], z["Conditioned"], 
                                    z["Area (Excluding Plenums and CrawlSpace) (ft²)"], 
                                    z.get("Area (Including Plenums and CrawlSpace) (ft²)", 0.0),
                                    z["Width [ft]"], z["Length [ft]"], 
                                    z["Volume [ft3]"], z["Multipliers"],
                                    z["People (Persons/1000 ft2)"], z["Lighting (Btu/h-ft2)"], z["Plug Loads (Btu/h-ft2)"],
                                    z.get("Outdoor Air Flow per Person (cfm/person)", "N/A"),
                                    z.get("Outdoor Air Flow per Zone Floor Area (cfm/ft2)", "N/A")
                                ])
                        else: writer.writerow(["No zone data found."])
                        
                        writer.writerow([])
                        writer.writerow([])

                        # Table 3: Envelope Summary
                        writer.writerow(["### ENVELOPE ###"])
                        writer.writerow([
                            "Climate Zone", "Vintage", 
                            "Exterior Roof Layers", "Roof U-Value [Btu/h-ft2-F]", 
                            "Exterior Wall Layers", "Wall U-Value [Btu/h-ft2-F]",
                            "Exterior Window Layers", "Window U-Value [Btu/h-ft2-F]", "Window SHGC", "Window VT"
                        ])
                        
                        for e in envelope_rows:
                            if e.get("Vintage") == "File Not Found":
                                writer.writerow([e["Climate Zone"], "File Not Found"])
                            else:
                                writer.writerow([
                                    e["Climate Zone"], e["Vintage"],
                                    e["Roof Layers"], e["Roof U-Value IP"],
                                    e["Wall Layers"], e["Wall U-Value IP"],
                                    e["Window Layers"], e["Window U-Value IP"], e["Window SHGC"], e["Window VT"]
                                ])

                        writer.writerow([])
                        writer.writerow([])

                        # Table 4: Infiltration Rate Summary
                        writer.writerow(["### INFILTRATION (CFM/ft2) ###"])
                        # Generate headers: Vintage, CZ01, ... CZ16
                        cz_headers = [f"CZ{i:02}" for i in range(1, 17)]
                        writer.writerow(["Vintage"] + cz_headers)
                        
                        # Generate row: Vintage, Val_01, Val_02...
                        infil_row = [report_vintage]
                        for cz in cz_headers:
                            infil_row.append(infil_map.get(cz, "N/A"))
                        
                        writer.writerow(infil_row)
                        
                        writer.writerow([])
                        writer.writerow([])
                        
                        # Table 5: Water Heater Summary
                        writer.writerow(["### WATER HEATER ###"])
                        writer.writerow(["Climate Zone", "Vintage", "Burner Efficiency", "Maximum Heater Capacity (Btu/h)", "Tank Volume (ft3)", "Tank Loss_Off Cycle (W/K)", "Tank Loss_On Cycle (W/K)"])
                        
                        if wh_rows_all:
                            for wh in wh_rows_all:
                                writer.writerow([
                                    wh.get("Climate Zone", ""),
                                    report_vintage,
                                    wh.get("Burner Efficiency", ""),
                                    wh.get("Maximum Heater Capacity (Btu/h)", ""),
                                    wh.get("Tank Volume (ft3)", ""),
                                    wh.get("Tank Loss_Off Cycle (W/K)", ""),
                                    wh.get("Tank Loss_On Cycle (W/K)", "")
                                ])
                        else: writer.writerow(["No WaterHeater:Mixed objects found in any zone."])

                        writer.writerow([])
                        writer.writerow([])

                        # Table 6: OA Controller Economizer Max Limit Dry-Bulb Temp
                        writer.writerow(["### OA CONTROLLER ###"])
                        writer.writerow(["Climate Zone", "Vintage", "Economizer Maximum Limit Dry-Bulb Temperature (F)"])
                        if oa_rows:
                            for row in oa_rows:
                                writer.writerow([
                                    row["Climate Zone"], 
                                    report_vintage, 
                                    row["Temp"]
                                ])
                        else:
                            writer.writerow(["No OA Controller data found."])
                        
                        writer.writerow([])
                        writer.writerow([])

                        # Table 7: DHW Peak Flow by Zone
                        writer.writerow(["### DHW PEAK FLOW BY ZONE ###"])
                        writer.writerow(["Space", "Peak hot water usage (gal/hr)"])
                        
                        if dhw_rows:
                            for row in dhw_rows:
                                writer.writerow([row["Space"], row["Peak hot water usage"]])
                        else:
                            writer.writerow(["No WaterUse:Equipment found."])

                        writer.writerow([]); 
                        writer.writerow([])

                        # # Table 7: Whole Building Peak Water Flow (Simulated)
                        # writer.writerow(["### WHOLE BUILDING PEAK WATER FLOW (Simulated) ###"])
                        # writer.writerow(["Climate Zone", "Whole Building Peak Water Flow (gal/hr)"])
                        
                        # if peak_water_rows:
                        #     for row in peak_water_rows:
                        #         writer.writerow([row["Climate Zone"], row["Peak Flow"]])
                        # else:
                        #     writer.writerow(["No simulation results found."])

                        # writer.writerow([]); 
                        # writer.writerow([])

                        # Table 8: Total End Uses (Annual)
                        writer.writerow(["### TOTAL END USES (Annual) ###"])
                        writer.writerow(["Climate Zone", "HVAC System", "Electricity (kBtu)", "Natural Gas (kBtu)"])
                        if energy_rows:
                            for row in energy_rows:
                                writer.writerow([
                                    row["Climate Zone"],
                                    hvac_name,
                                    row["Electricity"], 
                                    row["Natural Gas"]
                                ])
                        else:
                            writer.writerow(["No energy data extracted."])
                        
                        writer.writerow([])
                        writer.writerow([])

                        # Table 9: End Use Breakdown (Annual)
                        writer.writerow(["### END USE BREAKDOWN (Annual) ###"])
                        writer.writerow(["Climate Zone", "HVAC System", "End Use", "Electricity [kBtu]", "Natural Gas [kBtu]"])
                        
                        if all_end_use_breakdown_rows:
                            for row in all_end_use_breakdown_rows:
                                writer.writerow([
                                    row["Climate Zone"],
                                    hvac_name,
                                    row["End Use"],
                                    row["Electricity [kBtu]"],
                                    row["Natural Gas [kBtu]"]
                                ])
                        else:
                            writer.writerow(["No breakdown data extracted."])

                        writer.writerow([])
                        writer.writerow([])

                        # Table 10: Schedule Profiles
                        writer.writerow(["### SCHEDULE PROFILES BY ZONE NAME ###"])
                        # Generate headers 1..24
                        hours_header = [str(i) for i in range(1, 25)]
                        writer.writerow(["Zone Name", "Schedule Name", "Type"] + hours_header)
                        
                        if schedule_rows:
                            for s_row in schedule_rows:
                                # Construct row data
                                out_row = [s_row["Zone Name"], s_row["Schedule Name"], s_row["Type"]]
                                # Append values for hours 1-24
                                for h in range(1, 25):
                                    out_row.append(s_row.get(str(h), ""))
                                writer.writerow(out_row)
                        else:
                            writer.writerow(["No matching schedules found in EIO."])

                        writer.writerow([])
                        writer.writerow([])

                        # Table 11: HVAC Summary
                        writer.writerow(["### HVAC ###"])
                        writer.writerow(["Vintage", "System Name", "HVAC System Identifier", "Air Distribution", "Heating Efficiency", "Cooling Efficiency"])
                        writer.writerow([
                            report_vintage,
                            hvac_data["System Name"],
                            hvac_data["HVAC System Identifier"],
                            hvac_data["Air Distribution"],
                            hvac_data["Heating Efficiency"],
                            hvac_data["Cooling Efficiency"]
                        ])

                        writer.writerow([])
                        writer.writerow([])

                        # Table 12: Fan Summary
                        writer.writerow(["### FAN ###"])
                        writer.writerow(["Vintage","HVAC name","System name","System type",
                                        "Total Static Pressure (TSP) (in w.c.)",
                                        "Fan Efficiency","Fan Motor and Drive Efficiency","W/cfm"])

                        for rec in fan_rows:
                            writer.writerow([
                                rec["Vintage"], rec["HVAC name"], rec["System name"], rec["System type"],
                                rec["Total Static Pressure (TSP) (in w.c.)"],
                                rec["Fan Efficiency"], rec["Fan Motor and Drive Efficiency"], rec["W/cfm"]
                            ])
                        writer.writerow([])
                        writer.writerow([])

                        # Table 13: Gas Equipment
                        writer.writerow(["### GAS EQUIPMENT ###"])
                        writer.writerow(["Zone Name", "Gas Loads (Btu/h-ft2)"])
                        
                        if gas_data:
                            for row in gas_data:
                                writer.writerow([
                                    row["Zone Name"], 
                                    row["Gas Loads (Btu/h-ft2)"]
                                ])
                        else:
                            writer.writerow(["No GasEquipment found."])

                        writer.writerow([])
                        writer.writerow([])

                        # Table 14: Refrigeration System Summary
                        writer.writerow(["### REFRIGERATION SYSTEM ###"])
                        writer.writerow(["Vintage", "Refrigeration System Name", "Condenser Fan Power", "Working fluid", "Condenser Type"])
                        
                        if ref_data:
                            for row in ref_data:
                                writer.writerow([
                                    row["Vintage"],
                                    row["Refrigeration System Name"],
                                    row["Condenser Fan Power"],
                                    row["Working fluid"],
                                    row["Condenser Type"]
                                ])
                        else:
                            writer.writerow(["No refrigeration system was found"])
                        
                        writer.writerow([])
                        writer.writerow([])

                        # Table 15: Thermostat Setpoints (Detailed by Zone & CZ)
                        writer.writerow(["### THERMOSTAT SETPOINTS (C) ###"])
                        writer.writerow([
                            "Climate Zone", 
                            # "Vintage", 
                            "Zone Name",
                            "Heating Setpoint (C)", 
                            "Heating Setback (C)", 
                            "Cooling Setpoint (C)", 
                            "Cooling Setback (C)"
                        ])
                        
                        if all_thermostat_rows:
                            for row in all_thermostat_rows:
                                writer.writerow([
                                    row.get("Climate Zone", ""),
                                    # report_vintage,
                                    row.get("Zone Name", ""),
                                    row.get("Heating Setpoint", "-"),
                                    row.get("Heating Setback", "-"),
                                    row.get("Cooling Setpoint", "-"),
                                    row.get("Cooling Setback", "-")
                                ])
                        else:
                            writer.writerow(["No Thermostats Found"])

                        writer.writerow([])
                        writer.writerow([])

                except IOError as e:
                    # print(f"Error writing CSV {csv_filename}: {e}")
                    pass
print(f"\nData extraction complete.")

