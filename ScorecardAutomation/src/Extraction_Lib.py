import os
import re
import pandas as pd
import numpy as np
import math
from io import StringIO
#from eppy.modeleditor import IDF

# Define the dictionary for mapping abbreviations
building_type_map = {
    "Asm": "Assembly",
    "ECC": "Education - Community College",
    "EPr": "Education - Primary School",
    "ERC": "Education - Relocatable Classroom",
    "ESe": "Education - Secondary School",
    "EUn": "Education - University",
    "Fin": "Financial buildings, incl. banks",
    "Gro": "Grocery",
    "Hsp": "Health/Medical - Hospital",
    "Htl": "Lodging - Hotel",
    "Lib": "Libraries",
    "MBT": "Manufacturing Biotech",
    "MLI": "Manufacturing Light Industrial",
    "Mtl": "Lodging - Motel",
    "Nrs": "Health/Medical - Nursing Home",
    "OfL": "Office - Large",
    "OfS": "Office - Small",
    "Rel": "Religious assembly buildings",
    "RFF": "Restaurant - Fast-Food",
    "RSD": "Restaurant - Sit-Down",
    "Rt3": "Retail - Multistory Large",
    "RtL": "Retail - Single-Story Large",
    "RtS": "Retail - Small",
    "SCn": "Storage - Conditioned",
    "SUn": "Storage - Unconditioned",
    "WRf": "Warehouse - Refrigerated"
}

# Building Type
def get_building_type(filename):
    # Extract the first part of the filename (e.g., "Asm" from "Asm&0...")
    abbrev = filename.split('_')[0]
    return building_type_map.get(abbrev, "Unknown Type")

# Category
def get_building_category(filename):
    abbrev = filename.split('_')[0]
    # If the abbreviation exists in our map, it is Nonresidential
    if abbrev in building_type_map:
        return "Nonresidential"
    return "Unknown"

# Vintage
def get_vintage():
    # Hardcoded as per requirements
    return "Existing, New Construction"
def extract_run_begin_day(idf_path):
    """
    Extract RunPeriod begin day info from IDF.

    Output dict keys:
      - Begin Month
      - Begin Day of Month
      - Day of Week for Start Day
    """
    out = {
        "Begin Month": "N/A",
        "Begin Day of Month": "N/A",
        "Day of Week for Start Day": "N/A",
    }

    if not os.path.exists(idf_path):
        return out

    try:
        with open(idf_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Remove comments and normalize whitespace
        no_comments = re.sub(r"!.*", "", content)
        cleaned_text = " ".join(no_comments.split())
        objects = cleaned_text.split(";")

        for obj in objects:
            s = obj.strip()
            if not s:
                continue

            # Keep blanks (important for Begin Year/End Year empty fields)
            fields = [f.strip() for f in s.split(",")]

            if not fields:
                continue

            obj_type = fields[0].strip().lower()
            if obj_type != "runperiod":
                continue

            # Expected indices:
            # 0 RunPeriod
            # 1 Name
            # 2 Begin Month
            # 3 Begin Day of Month
            # 4 Begin Year
            # 5 End Month
            # 6 End Day of Month
            # 7 End Year
            # 8 Day of Week for Start Day
            if len(fields) >= 9:
                out["Begin Month"] = fields[2] if fields[2] != "" else "N/A"
                out["Begin Day of Month"] = fields[3] if fields[3] != "" else "N/A"
                out["Day of Week for Start Day"] = fields[8] if fields[8] != "" else "N/A"
            return out  # use the first RunPeriod found

    except Exception as e:
        print(f"Error extracting RunPeriod begin day in {idf_path}: {e}")

    return out


def extract_special_days(idf_path):
    """
    Extract RunPeriodControl:SpecialDays objects from IDF.

    Output list of dicts with keys:
      - Name
      - Start Day
      - Duration
      - Special Day Type
    """
    rows = []

    if not os.path.exists(idf_path):
        return rows

    try:
        with open(idf_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        no_comments = re.sub(r"!.*", "", content)
        cleaned_text = " ".join(no_comments.split())
        objects = cleaned_text.split(";")

        for obj in objects:
            s = obj.strip()
            if not s:
                continue

            fields = [f.strip() for f in s.split(",")]
            if len(fields) < 2:
                continue

            obj_type = fields[0].strip().lower()
            if obj_type != "runperiodcontrol:specialdays":
                continue

            # Expected indices:
            # 0 RunPeriodControl:SpecialDays
            # 1 Name
            # 2 Start Date
            # 3 Duration {days}
            # 4 Special Day Type
            name = fields[1] if len(fields) > 1 else ""
            start_day = fields[2] if len(fields) > 2 else ""
            duration = fields[3] if len(fields) > 3 else ""
            sday_type = fields[4] if len(fields) > 4 else ""

            rows.append({
                "Name": name if name != "" else "N/A",
                "Start Day": start_day if start_day != "" else "N/A",
                "Duration": duration if duration != "" else "N/A",
                "Special Day Type": sday_type if sday_type != "" else "N/A",
            })

    except Exception as e:
        print(f"Error extracting SpecialDays in {idf_path}: {e}")

    return rows

# Roof Type
def get_roof_type(file_path):
    """
    Parses IDF for BuildingSurface:Detailed where Surface Type is Roof.
    Checks Z-coordinates of vertices to determine if Flat or Sloped.
    """
    try:
        with open(file_path, 'r', errors='ignore') as f:
            content = f.read()

        # Strip inline comments
        content = re.sub(r'!.*', '', content)

        # Extract every BuildingSurface:Detailed block (keyword included)
        blocks = re.findall(
            r'(BuildingSurface:Detailed\s*,.*?);',
            content, re.DOTALL | re.IGNORECASE
        )

        has_roof = False

        for block in blocks:
            fields = [f.strip() for f in block.split(',')]

            # Minimum fields needed: keyword + 11 header fields + at least 3 vertices (9 coords)
            if len(fields) < 21:
                continue

            # fields[2] = Surface Type
            if fields[2].lower() != 'roof':
                continue

            has_roof = True

            # fields[11] = Number of Vertices
            try:
                num_vertices = int(fields[11])
            except (ValueError, IndexError):
                continue

            # Z is the 3rd coordinate in each X,Y,Z triplet starting at index 12
            z_coords = []
            for i in range(num_vertices):
                z_index = 12 + i * 3 + 2
                if z_index < len(fields):
                    try:
                        z_coords.append(round(float(fields[z_index]), 4))
                    except ValueError:
                        continue

            if not z_coords:
                continue

            unique_z = set(z_coords)

            # If Z values differ across vertices, the surface is tilted
            if len(unique_z) > 1:
                return "Sloped Roof"

        if has_roof:
            return "Flat Roof"
        else:
            return "Unknown"

    except Exception as e:
        return f"Error: {str(e)}"

# Glazing sill height 
def get_glazing_sill_height(file_path):
    """
    Parses IDF to calculate sill height using robust coordinate extraction.
    """
    try:
        with open(file_path, 'r', errors='ignore') as f:
            content = f.read()

        objects = content.split(';')
        
        zone_floor_min_z = {}   
        wall_to_zone_map = {}   
        windows_data = []       

        for obj in objects:
            clean_obj = obj.strip()
            if not clean_obj: continue

            lines = clean_obj.splitlines()
            cleaned_lines = [line.split('!')[0].strip() for line in lines]
            full_text = ''.join(cleaned_lines)
            fields = [f.strip() for f in full_text.split(',')]

            if len(fields) < 2: continue
            
            obj_type = fields[0].lower()

            # Process Surfaces/Windows
            if obj_type in ['buildingsurface:detailed', 'fenestrationsurface:detailed']:
                if len(fields) < 5: continue
                
                # Extract Name and Zone/Wall Reference
                surf_name = " ".join(fields[1].upper().strip().split())
                ref_name = " ".join(fields[4].upper().strip().split()) # Zone for Surf, Wall for Win
                
                # Extract ALL trailing numbers (Coordinates + Header fields like Multiplier/N_Vertices)
                coords = []
                for field in reversed(fields):
                    try:
                        val = float(field)
                        coords.insert(0, val)
                    except ValueError:
                        break
                
                # robust coordinate extraction:
                # Determine how many "header" numbers exist (0, 1, or 2) by checking the remainder when divided by 3.
                header_count = len(coords) % 3
                
                # Slice off the headers to get pure [x, y, z, x, y, z...]
                clean_coords = coords[header_count:]
                
                if not clean_coords: continue

                # Extract Z values (every 3rd value, starting at index 2)
                z_coords = clean_coords[2::3]
                min_z = min(z_coords)

                # window and floor surface processing
                if obj_type == 'buildingsurface:detailed':
                    surf_type = fields[2].lower()
                    if surf_type == 'floor':
                        if ref_name not in zone_floor_min_z:
                            zone_floor_min_z[ref_name] = min_z
                        else:
                            if min_z < zone_floor_min_z[ref_name]:
                                zone_floor_min_z[ref_name] = min_z
                    
                    wall_to_zone_map[surf_name] = ref_name

                elif obj_type == 'fenestrationsurface:detailed':
                    windows_data.append({
                        'name': surf_name, 
                        'wall': ref_name,
                        'min_z': min_z
                    })

        results = {}
        for win in windows_data:
            key_name = win['name']
            wall_name = win['wall']
            zone_name = wall_to_zone_map.get(wall_name)
            
            if zone_name and zone_name in zone_floor_min_z:
                floor_z = zone_floor_min_z[zone_name]
                # Calculation: Window Bottom Z - Floor Z
                sill_height_m = win['min_z'] - floor_z
                sill_height_ft = sill_height_m * 3.28084
                results[key_name] = round(sill_height_ft, 2)
            else:
                results[key_name] = "N/A"
        
        return results

    except Exception as e:
        print(f"Error in sill height calc: {e}")
        return {}

# WWR
def extract_wwr(htm_path):
    """
    Parses the HTML file for the 'Window-Wall Ratio' table.
    Extracts the value for 'Above Ground Window-Wall Ratio [%]' from the 'Total' column.
    """
    wwr_value = "N/A"
    
    if not os.path.exists(htm_path):
        return wwr_value

    try:
        with open(htm_path, 'r', errors='ignore') as f:
            html_content = f.read()

        search_term = "Above Ground Window-Wall Ratio [%]"
        row_idx = html_content.find(search_term)
        
        if row_idx != -1:
            start_td = html_content.find("<td", row_idx + len(search_term))
            
            if start_td != -1:
                end_td = html_content.find("</td>", start_td)
                cell_content = html_content[start_td:end_td]
                val = cell_content.split(">")[-1].strip()
                wwr_value = val
                
    except Exception as e:
        print(f"Error parsing WWR from HTML: {e}")
        
    return wwr_value

# Window Dimensions
def get_win_dimension(eio_path):
    """
    Parses the EIO file for 'HeatTransfer Surface' lines where Class is 'Window'.
    Extracts Window Name, Width, and Height.
    Returns a list of dictionaries.
    """
    windows = []
    
    if not os.path.exists(eio_path):
        return windows

    try:
        with open(eio_path, 'r', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line.startswith("HeatTransfer Surface"):
                    parts = line.split(',')
                    if len(parts) >= 16 and parts[2].strip().lower() == "window":
                        try:
                            w_name = parts[1].strip()
                            width_m = float(parts[14])
                            height_m = float(parts[15])
                            
                            width_ft = width_m * 3.28084
                            height_ft = height_m * 3.28084
                            
                            windows.append({
                                "Window Name": w_name,
                                "Width [ft]": round(width_ft, 2),
                                "Height [ft]": round(height_ft, 2)
                            })
                        except ValueError:
                            continue
    except Exception as e:
        print(f"Error parsing Window Dimensions from EIO: {e}")
        
    return windows

# Zone Summary
def extract_zone_summary(htm_path, eio_path, idf_path):
    """
    Parses the HTML file for the 'Zone Summary' table.
    Parses the EIO file for Zone Dimensions (Width/Length).
    Parses the IDF file for DesignSpecification:OutdoorAir.
    """
    zone_data = []
    temp_zone_map = {}

    # Parse HTM for zone summary
    if os.path.exists(htm_path):
        try:
            with open(htm_path, 'r', errors='ignore') as f:
                html_content = f.read()

            start_marker = "<b>Zone Summary</b>"
            start_idx = html_content.find(start_marker)
            
            if start_idx != -1:
                table_start = html_content.find("<table", start_idx)
                table_end = html_content.find("</table>", table_start)
                
                if table_start != -1:
                    table_html = html_content[table_start:table_end]
                    rows = table_html.split("<tr>")
                    
                    for row in rows:
                        if "<td" not in row: continue
                        
                        cells = []
                        parts = row.split("</td>")
                        for p in parts:
                            if "<td" in p:
                                val = p.split(">")[-1].strip()
                                cells.append(val)
                        
                        if len(cells) >= 12:
                            z_name = cells[0]
                            if "Total" in z_name or not z_name: continue
                            
                            # Raw Values
                            area_raw = cells[1]
                            conditioned = cells[2]
                            volume_raw = cells[4]
                            multipliers = cells[5]
                            lighting_raw = cells[10]
                            people_raw = cells[11]
                            plug_raw = cells[12]

                            # Exclude Plenums + CrawlSpace (Forces 0.0)
                            if ("PLNM" in z_name.upper()) or ("CRS" in z_name.upper()):
                                area_excl = 0.0
                            else:
                                try:
                                    area_excl = float(area_raw)
                                except ValueError:
                                    area_excl = 0.0

                            # Include Plenums + CrawlSpace (Raw Value)
                            try:
                                area_incl = float(area_raw)
                            except ValueError:
                                area_incl = 0.0

                            try: volume_val = float(volume_raw)
                            except ValueError: volume_val = 0.0

                            try: lighting_val = float(lighting_raw)
                            except ValueError: lighting_val = 0.0

                            try: plug_val = float(plug_raw)
                            except ValueError: plug_val = 0.0

                            people_density = 0.0
                            try:
                                ft2_per_person = float(people_raw)
                                if ft2_per_person > 0:
                                    people_density = 1000.0 / ft2_per_person
                            except ValueError:
                                people_density = 0.0

                            # Create entry
                            entry = {
                                "Space": z_name,
                                "Zone Name": z_name,
                                "Conditioned": conditioned,
                                "Area (Excluding Plenums and CrawlSpace) (ft²)": area_excl,
                                "Area (Including Plenums and CrawlSpace) (ft²)": area_incl,
                                "Volume [ft3]": volume_val,
                                "Multipliers": multipliers,
                                "Lighting (Btu/h-ft2)": lighting_val,
                                "People (Persons/1000 ft2)": round(people_density, 2),
                                "Plug Loads (Btu/h-ft2)": plug_val,
                                "Width [ft]": "N/A", 
                                "Length [ft]": "N/A", 
                                "Outdoor Air Flow per Zone Floor Area (cfm/ft2)": "N/A",
                                "Outdoor Air Flow per Person (cfm/person)": "N/A"
                            }
                            
                            temp_zone_map[z_name] = entry

        except Exception as e:
            print(f"Error parsing HTML: {e}")

    # Parse EIO for dimensions (Width/Length)
    zone_dim_candidates = {}  
    if os.path.exists(eio_path):
        try:
            with open(eio_path, "r", errors="ignore") as f:
                current_zone = None
                for line in f:
                    line = line.strip()
                    parts = line.split(",")

                    if line.startswith("Zone Surfaces,"):
                        if len(parts) >= 2:
                            current_zone = parts[1].strip()
                        continue

                    if line.startswith("HeatTransfer Surface,") and current_zone:
                        if len(parts) >= 16 and current_zone in temp_zone_map:
                            surf_name  = parts[1].strip().lower() if len(parts) > 1 else ""
                            surf_class = parts[2].strip().lower() if len(parts) > 2 else ""
                            surf_desc  = parts[5].strip().lower() if len(parts) > 5 else ""
                            outside_bc = parts[18].strip().lower() if len(parts) > 18 else ""

                            is_ceiling_by_name = ("ceiling" in surf_name)

                            is_exterior_roof = (surf_class == "roof") and ("exterior roof" in surf_desc)

                            # include reversed / interior-ceiling surfaces
                            is_radiant_interior_ceiling = ("radiant interior ceiling" in surf_desc)

                            # include ground/slab floors
                            is_ground_floor = (
                                outside_bc == "fcground" or
                                ("slabon" in surf_desc) or
                                ("belowgrade" in surf_desc) or
                                ("slab" in surf_desc)
                            )

                            # include normal interior floors (your new example)
                            is_interior_floor = ("interior floor" in surf_desc)

                            eligible = (
                                is_ceiling_by_name or
                                is_exterior_roof or
                                is_radiant_interior_ceiling or
                                is_ground_floor or
                                is_interior_floor
                            )
                            if not eligible:
                                continue

                            try:
                                width_m = float(parts[14])
                                length_m = float(parts[15])
                            except ValueError:
                                continue

                            width_ft = width_m * 3.28084
                            length_ft = length_m * 3.28084

                            cand = zone_dim_candidates.get(current_zone)
                            if cand is None:
                                zone_dim_candidates[current_zone] = {"max_w": width_ft, "max_l": length_ft}
                            else:
                                cand["max_w"] = max(cand["max_w"], width_ft)
                                cand["max_l"] = max(cand["max_l"], length_ft)

            # Apply max dims to temp_zone_map
            for z, cand in zone_dim_candidates.items():
                temp_zone_map[z]["Width [ft]"] = round(cand["max_w"], 2)
                temp_zone_map[z]["Length [ft]"] = round(cand["max_l"], 2)

        except Exception as e:
            print(f"Error parsing EIO for dimensions: {e}")


    # Parse IDF for Outdoor Air specs and build lookup map
    oa_lookup_map = {}
    if os.path.exists(idf_path):
        try:
            with open(idf_path, 'r', errors='ignore') as f: lines = f.readlines()
            clean_text = ""
            for line in lines:
                if '!' in line: line = line.split('!')[0]
                clean_text += line.strip()
            objects = clean_text.split(';')
            for obj in objects:
                if "DesignSpecification:OutdoorAir" in obj:
                    fields = [f.strip() for f in obj.split(',')]
                    if len(fields) >= 5:
                        obj_name = fields[1]; oa_per_person = fields[3]; oa_per_area = fields[4]
                        lower_name = obj_name.lower(); suffix = " design oa"
                        if lower_name.endswith(suffix): cleaned_name = lower_name[:-len(suffix)].strip(); oa_lookup_map[cleaned_name] = (oa_per_person, oa_per_area)
                        else: oa_lookup_map[lower_name] = (oa_per_person, oa_per_area)
        except Exception as e: print(f"Error parsing IDF: {e}")

    # Finalize OA values for each zone
    for z_name, data in temp_zone_map.items():
        target_key = z_name.lower()
        found_values = oa_lookup_map.get(target_key, None)
        if found_values:
            raw_person, raw_area = found_values
            # Convert m3/s to cfm
            try: val_float = float(raw_person); val_ip = round(val_float * 2118.88, 2); data["Outdoor Air Flow per Person (cfm/person)"] = val_ip
            # If conversion fails (not a number), keep raw
            except ValueError: data["Outdoor Air Flow per Person (cfm/person)"] = raw_person
            # Convert m3/s-m2 to cfm/ft2
            try: val_float = float(raw_area); val_ip = round(val_float * 196.8504, 4); data["Outdoor Air Flow per Zone Floor Area (cfm/ft2)"] = val_ip
            # If conversion fails (not a number), keep raw
            except ValueError: data["Outdoor Air Flow per Zone Floor Area (cfm/ft2)"] = raw_area
        zone_data.append(data)

    return zone_data

# Envelope
def extract_envelope_data(idf_path, htm_path):
    """
    1. IDF: Extracts Construction Layers (Roof, Wall, Window) and Window Performance.
    2. HTM: Extracts U-Factor no Film for Exterior Roof/Wall and converts to IP.
    3. Vintage: Determines Existing vs New Construction based on filename.
    """
    env_data = {
        "Vintage": "Unknown",
        "Roof Layers": "N/A", "Roof U-Value IP": 0.0,
        "Wall Layers": "N/A", "Wall U-Value IP": 0.0,
        "Window Layers": "N/A", "Window U-Value IP": 0.0, "Window SHGC": 0.0, "Window VT": 0.0
    }

    filename = os.path.basename(idf_path)
    name_parts = filename.split('&')
    
    if "Ex" in name_parts or "Ex" in filename:
        env_data["Vintage"] = "Existing"
    elif "New" in name_parts or "New" in filename:
        env_data["Vintage"] = "New Construction"
    if os.path.exists(idf_path):
        with open(idf_path, 'r', errors='ignore') as f:
            idf_content = f.read()
        
        objects = idf_content.split(';')
        constructions = {}    
        window_materials = {} 

        for obj in objects:
            clean_obj = obj.strip()
            if not clean_obj: continue
            
            lines = clean_obj.splitlines()
            cleaned_lines = [line.split('!')[0].strip() for line in lines]
            full_text = ''.join(cleaned_lines)
            fields = [f.strip() for f in full_text.split(',')]
            if not fields: continue
            
            obj_type = fields[0].lower()
            
            if obj_type == "construction":
                if len(fields) > 2:
                    name = fields[1].lower()
                    layers = fields[2:]
                    constructions[name] = layers
            
            elif obj_type == "windowmaterial:simpleglazingsystem":
                if len(fields) >= 5:
                    mat_name = fields[1].lower()
                    u_val = float(fields[2])
                    shgc_val = float(fields[3])
                    vt_val = float(fields[4].replace(';', '')) 
                    window_materials[mat_name] = {"u": u_val, "shgc": shgc_val, "vt": vt_val}

        for c_name, layers in constructions.items():
            if "exterior roof" in c_name:
                env_data["Roof Layers"] = "+".join(layers)
            elif "exterior wall" in c_name:
                env_data["Wall Layers"] = "+".join(layers)
            elif "exterior window" in c_name:
                env_data["Window Layers"] = "+".join(layers)
                if layers:
                    glazing_name = layers[0].lower()
                    if glazing_name in window_materials:
                        mat = window_materials[glazing_name]
                        env_data["Window U-Value IP"] = round(mat["u"] * 0.17611, 3)
                        env_data["Window SHGC"] = mat["shgc"]
                        env_data["Window VT"] = mat["vt"]

    if os.path.exists(htm_path):
        try:
            with open(htm_path, 'r', errors='ignore') as f:
                html_content = f.read()

            start_idx = html_content.find("Opaque Exterior")
            if start_idx != -1:
                table_start = html_content.find("<table", start_idx)
                table_end = html_content.find("</table>", table_start)
                table_html = html_content[table_start:table_end]
                rows = table_html.split("<tr>")
                
                for row in rows:
                    if "EXTERIOR ROOF" in row or "EXTERIOR WALL" in row:
                        cells = []
                        parts = row.split("</td>")
                        for p in parts:
                            if "<td" in p:
                                cells.append(p.split(">")[-1].strip())
                        
                        if len(cells) > 4:
                            construction_name = cells[1].upper()
                            u_val_str = cells[4]
                            try:
                                u_val_ip = float(u_val_str)
                                # if it is si, need conversion
                                #u_val_ip = u_val_si * 0.17611 
                                if "EXTERIOR ROOF" in construction_name:
                                    env_data["Roof U-Value IP"] = round(u_val_ip, 3)
                                elif "EXTERIOR WALL" in construction_name:
                                    env_data["Wall U-Value IP"] = round(u_val_ip, 3)
                            except ValueError:
                                pass
        except Exception as e:
            print(f"Error parsing HTM Envelope: {e}")

    return env_data

def extract_water_heater(idf_path, htm_path):
    """
    Extracts Water Heater properties from IDF and HTM.
    """
    wh_list = []
    
    # Read HTM for Capacity and Volume
    htm_data = {} 
    if os.path.exists(htm_path):
        try:
            with open(htm_path, 'r', errors='ignore') as f:
                html_content = f.read()
            
            start_idx = html_content.find("<b>WaterHeater:Mixed</b>")
            if start_idx != -1:
                table_start = html_content.find("<table", start_idx)
                table_end = html_content.find("</table>", table_start)
                table_html = html_content[table_start:table_end]
                rows = table_html.split("<tr>")
                cap_idx = -1
                vol_idx = -1
                
                for r_idx, row in enumerate(rows):
                    if "Maximum Heater Capacity [Btu/h]" in row and cap_idx == -1:
                        cells = row.split("</td>")
                        for c_i, c in enumerate(cells):
                            if "Maximum Heater Capacity [Btu/h]" in c: cap_idx = c_i
                            if "Tank Volume [ft3]" in c: vol_idx = c_i
                    elif cap_idx != -1 and "<td" in row:
                        cells = []
                        parts = row.split("</td>")
                        for p in parts:
                            if "<td" in p: cells.append(p.split(">")[-1].strip())
                        if len(cells) > 0:
                            name = cells[0]
                            cap = cells[cap_idx] if len(cells) > cap_idx else "N/A"
                            vol = cells[vol_idx] if len(cells) > vol_idx else "N/A"
                            htm_data[name.upper()] = {"Capacity": cap, "Volume": vol}
        except Exception as e:
            pass

    # Read IDF for Efficiency and Loss Coefficients
    if os.path.exists(idf_path):
        try:
            with open(idf_path, 'r', errors='ignore') as f:
                idf_content = f.read()
            
            objects = idf_content.split(';')
            for obj in objects:
                if "WaterHeater:Mixed" in obj:
                    wh_obj = {}
                    lines = obj.splitlines()
                    name = "Unknown"
                    eff = "N/A"
                    loss_off = "N/A"
                    loss_on = "N/A"
                    
                    for line in lines:
                        clean_line = line.strip()
                        if "!" not in clean_line: continue
                        val_part = clean_line.split('!')[0].strip().replace(',', '')
                        comment_part = clean_line.split('!')[1].strip()
                        
                        if not name or name == "Unknown":
                             if "Name" in comment_part and "Type" not in comment_part:
                                  name = val_part
                        if "Heater Thermal Efficiency" in comment_part: eff = val_part
                        if "Off Cycle Loss Coefficient to Ambient Temperature" in comment_part: loss_off = val_part
                        if "On Cycle Loss Coefficient to Ambient Temperature" in comment_part: loss_on = val_part

                    if name == "Unknown":
                         fields = [f.strip() for f in obj.replace('\n','').split(',')]
                         if len(fields) > 1: name = fields[1]
                    
                    if "DHW WATER HEATER" in name.upper():
                        wh_obj["Name"] = name
                        wh_obj["Burner Efficiency"] = eff
                        wh_obj["Tank Loss_Off Cycle (W/K)"] = loss_off
                        wh_obj["Tank Loss_On Cycle (W/K)"] = loss_on
                        
                        match = htm_data.get(name.upper())
                        if match:
                            wh_obj["Maximum Heater Capacity (Btu/h)"] = match["Capacity"]
                            wh_obj["Tank Volume (ft3)"] = match["Volume"]
                        else:
                            wh_obj["Maximum Heater Capacity (Btu/h)"] = "N/A"
                            wh_obj["Tank Volume (ft3)"] = "N/A"
                        
                        wh_list.append(wh_obj)

        except Exception as e:
            print(f"IDF Water Heater Parsing Error: {e}")
            pass
            
    return wh_list

def extract_oa_controller_temp(idf_path):
    econ_temp = "N/A"
    if os.path.exists(idf_path):
        try:
            with open(idf_path, 'r', errors='ignore') as f:
                for line in f:
                    if "oa_econ_max_temp =" in line:
                        parts = line.split('=')
                        if len(parts) > 1:
                            value_part = parts[1].strip()
                            if value_part:
                                econ_temp = value_part.split()[0]
                                break 
        except Exception:
            pass
    return econ_temp


def extract_dhw_peak_flow(idf_path):
    """
    Extracts peak flow rates for each zone from WaterUse:Equipment objects
    by parsing the IDF text directly (no eppy/IDD required).
    """
    try:
        with open(idf_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading IDF file: {e}")
        return []

    # Clean the content: Remove comments (!) and newlines to treat it as a stream
    # Remove everything after '!' on each line
    no_comments = re.sub(r'!.*', '', content)
    
    # Normalize whitespace to single spaces (handles newlines inside objects)
    # This makes "WaterUse:Equipment, \n Name," turn into "WaterUse:Equipment, Name,"
    cleaned_text = ' '.join(no_comments.split())

    # Split into objects by semicolon
    # IDF objects end with a semicolon
    objects = cleaned_text.split(';')

    dhw_data = []

    # Regex to capture Zone Name: "Prefix [Zone Name] DHW"
    name_pattern = re.compile(r"^(.*?)\s+DHW\b", re.IGNORECASE)

    for obj_str in objects:
        # Split fields by comma
        fields = [f.strip() for f in obj_str.split(',')]
        
        if not fields:
            continue

        # Check object type (first field)
        obj_type = fields[0]
        if obj_type.lower() == 'wateruse:equipment':
            # Field indices for WaterUse:Equipment:
            # 0: Object Type
            # 1: Name
            # 2: End-Use Subcategory
            # 3: Peak Flow Rate
            
            if len(fields) >= 4:
                full_name = fields[1]
                peak_flow_str = fields[3]
                
                # Parse Zone Name
                m = name_pattern.search(full_name)
                if m:
                    zone_name = m.group(1).strip()
                else:
                    zone_name = full_name

                # Parse Flow Rate
                try:
                    # 1 m³/s = 264.172 gal/m3 × 3600 s/hr = 951019.2 gal/hr
                    peak_flow = float(peak_flow_str) * 951019.2  # m3/s to gal/hr
                except ValueError:
                    peak_flow = 0.0

                dhw_data.append({
                    "Space": zone_name,
                    "Peak hot water usage": peak_flow
                })

    # Sort for cleaner output
    dhw_data.sort(key=lambda x: x["Space"])
    
    return dhw_data

def get_whole_building_peak_water(result_csv_path):
    """
    Reads the E+ output CSV, sums all columns ending in
    'Hot Water Volume Flow Rate [m3/s](Hourly)', and returns the max hourly sum
    converted to gal/hr.
    """
    try:
        if not os.path.exists(result_csv_path):
            return "File Not Found"

        df = pd.read_csv(result_csv_path)

        target_suffix = "Hot Water Volume Flow Rate [m3/s](Hourly)"
        hw_cols = [c for c in df.columns if str(c).strip().endswith(target_suffix)]
        if not hw_cols:
            return "No HW Columns Found"

        # Ensure numeric (handles strings/blank cells gracefully)
        hw_numeric = df[hw_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)

        # Sum across zones for each hour, then take the peak hour
        total_hourly_flow_m3s = hw_numeric.sum(axis=1)
        peak_flow_m3s = float(total_hourly_flow_m3s.max())

        # Convert m3/s -> gal/hr
        M3S_TO_GALHR = 951019.2  # 1 m³/s = 264.172 gal/m3 × 3600 s/hr
        peak_flow_galhr = peak_flow_m3s * M3S_TO_GALHR

        return peak_flow_galhr

    except Exception as e:
        return f"Error: {str(e)}"
    

def extract_total_end_uses(htm_path):
    """
    Parses *tbl.htm as text to find the 'Total End Uses' row 
    and returns (electricity, natural_gas).
    """
    if not os.path.exists(htm_path):
        return "File Not Found", "File Not Found"

    try:
        with open(htm_path, 'r', errors='ignore') as f:
            content = f.read()

        # Split content into rows based on <tr> tags. This is a simple way to isolate table rows.
        rows = content.split("<tr>")

        for row in rows:
            # Check if this row is the "Total End Uses" row
            if "Total End Uses" in row:
                # Split the row into cells based on </td>
                cells = row.split("</td>")
                
                # Expect the structure:
                # <td>Total End Uses</td> <td>Electricity</td> <td>Natural Gas</td> ...
                
                # cells[0] -> ...>Total End Uses
                # cells[1] -> ...>Electricity Value
                # cells[2] -> ...>Natural Gas Value
                
                if len(cells) > 2:
                    # Helper to strip HTML tags (get text after the last '>')
                    def clean_val(c):
                        val = c.split(">")[-1].strip()
                        return val.replace(",", "")

                    elec_str = clean_val(cells[1])
                    gas_str = clean_val(cells[2])

                    # Convert to float if possible
                    try: 
                        elec = float(elec_str)
                    except ValueError: 
                        elec = elec_str

                    try: 
                        gas = float(gas_str)
                    except ValueError: 
                        gas = gas_str

                    return elec, gas

        return "Row Not Found", "Row Not Found"

    except Exception as e:
        return f"Error: {str(e)}", f"Error: {str(e)}"
    
def extract_schedule_profile(eio_path, idf_path):
    """
    Extracts 24-hour schedule profiles by reconciling IDF definitions with EIO outputs.

    Updates vs prior version:
    - Properly parses Schedule:Compact with MULTIPLE Through blocks (common in schools).
    - Keeps 'For:' labels EXACTLY as written (no splitting/normalization).
    - Deduplicates repeated (For-label, profile) definitions across Through blocks.
    - If same For-label appears with different profiles, keeps both (adds Through tag).
    """
    final_rows = []

    if not os.path.exists(eio_path) or not os.path.exists(idf_path):
        return final_rows

    # 1. Parse IDF schedules
    idf_defs = {}  # { SCHEDNAME_UPPER: (real_sched_name, definitions_list) }

    target_keywords = [
        "INFILTRATION SCHEDULE", "LIGHTING SCHEDULE", "OCCUPANT SCH",
        "ELEC EQUIP SCH", "DHW SCH", "OA SCHEDULE",
        "COOLING SETPOINT SCHEDULE", "HEATING SETPOINT SCHEDULE"
    ]

    def _time_to_hour_index(time_part: str) -> int:
        """Convert HH:MM to end hour index [0..24]. Floors to hour as EnergyPlus hourly schedule convention."""
        try:
            hh, mm = map(int, time_part.split(":"))
            frac = hh + mm / 60.0
        except Exception:
            frac = 24.0
        return min(int(frac), 24)

    try:
        with open(idf_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_idf = f.read()

        # Remove comments and normalize whitespace
        no_comments = re.sub(r"!.*", "", raw_idf)
        cleaned_text = " ".join(no_comments.split())
        objects = cleaned_text.split(";")

        for obj in objects:
            fields = [f.strip() for f in obj.split(",") if f.strip() != ""]
            if len(fields) < 3:
                continue

            obj_type = fields[0].lower()
            sched_name = fields[1].strip()

            if not any(k in sched_name.upper() for k in target_keywords):
                continue

            definitions_raw = []  # may contain duplicates across Through blocks

            # Schedule:Constant
            if obj_type == "schedule:constant" and len(fields) >= 4:
                try:
                    val = float(fields[3])
                except Exception:
                    val = 0.0
                definitions_raw.append({
                    "type_label": "AllDays",
                    "profile": [val] * 24,
                    "through": None
                })

            # Schedule:Compact
            elif obj_type == "schedule:compact":
                current_label = "General"
                current_through = None
                hourly_vals = [0.0] * 24
                last_hour = 0

                # In compact objects:
                # fields[0]=objtype, [1]=name, [2]=type limits name, then tokens start at index 3
                i = 3
                while i < len(fields):
                    field = fields[i]

                    low = field.lower()

                    if low.startswith("through:"):
                        # New date range block; keep parsing (do NOT break)
                        # Store the exact string after Through:
                        try:
                            current_through = field.split(":", 1)[1].strip()
                        except Exception:
                            current_through = None
                        i += 1
                        continue

                    if low.startswith("for:"):
                        # Exact label after For:
                        try:
                            raw_label = field.split(":", 1)[1].strip()
                        except Exception:
                            raw_label = ""
                        current_label = raw_label

                        # Reset for this For-block
                        hourly_vals = [0.0] * 24
                        last_hour = 0
                        i += 1
                        continue

                    if low.startswith("until:"):
                        # Keep time format exactly (handles Until: 24:00)
                        # field example: "Until: 06:00"
                        time_part = field.split(":", 1)[1].strip()  # "06:00" or "24:00"

                        # Next token should be the value
                        if i + 1 >= len(fields):
                            break
                        val_str = fields[i + 1]
                        i_increment = 2

                        try:
                            val = float(val_str)
                        except Exception:
                            val = 0.0

                        end_idx = _time_to_hour_index(time_part)

                        for h in range(last_hour, end_idx):
                            hourly_vals[h] = val
                        last_hour = end_idx

                        if last_hour == 24:
                            definitions_raw.append({
                                "type_label": current_label,         # EXACT "For:" string
                                "profile": list(hourly_vals),
                                "through": current_through           # keep Through for conflict resolution
                            })

                        i += i_increment
                        continue

                    # Otherwise skip token
                    i += 1

            if definitions_raw:
                # If there are multiple Through blocks in this schedule,
                # Always keep rows per Through (even if profiles repeat later).
                through_set = set(
                    d.get("through") for d in definitions_raw
                    if isinstance(d.get("through"), str) and d.get("through").strip()
                )
                has_multi_through = len(through_set) > 1

                final_defs = []
                for d in definitions_raw:
                    label = d["type_label"]  # exact For: label
                    prof = d["profile"]
                    thr = d.get("through")

                    if has_multi_through:
                        thr_txt = thr.strip() if isinstance(thr, str) and thr.strip() else "?"
                        out_label = f"{label} (Through {thr_txt})"
                    else:
                        out_label = label

                    final_defs.append({
                        "type_label": out_label,
                        "profile": prof
                    })

                
                idf_defs[sched_name.upper()] = (sched_name, final_defs)


    except Exception as e:
        print(f"Error parsing IDF: {e}")

    # 2. Parse EIO schedules
    eio_data = {}  # { SchedName_Upper: [ [24], [24], ... ] }

    try:
        with open(eio_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not line.startswith("DaySchedule,"):
                    continue

                parts = line.split(",")
                if len(parts) < 29:
                    continue

                full_eio_name = parts[1].strip()

                try:
                    vals = [float(x) for x in parts[5:29]]
                except Exception:
                    continue

                matched_key = None
                u = full_eio_name.upper()
                for idf_key in idf_defs:
                    if idf_key in u:
                        matched_key = idf_key
                        break

                if matched_key:
                    eio_data.setdefault(matched_key, []).append(vals)

    except Exception as e:
        print(f"Error parsing EIO: {e}")

    # 3. Reconcile IDF defs with EIO values
    for idf_key, (real_sched_name, definitions) in idf_defs.items():
        eio_profiles_list = eio_data.get(idf_key, [])

        match = re.search(
            r"^(.*)\s+(INFILTRATION|LIGHTING|OCCUPANT|ELEC|DHW|OA|COOLING|HEATING)",
            real_sched_name,
            re.IGNORECASE
        )
        zone_name = match.group(1).strip() if match else real_sched_name

        is_temp = "SETPOINT" in real_sched_name.upper()

        for definition in definitions:
            label = definition["type_label"]
            theo_profile = definition["profile"]

            best_vals = theo_profile

            if eio_profiles_list:
                theo_arr = np.array(theo_profile, dtype=float)
                min_diff = float("inf")

                for eio_p in eio_profiles_list:
                    diff = float(np.sum(np.abs(theo_arr - np.array(eio_p, dtype=float))))
                    if diff < 0.1:
                        best_vals = eio_p
                        min_diff = diff
                        break
                    if diff < min_diff:
                        min_diff = diff
                        best_vals = eio_p

            formatted_vals = []
            for v in best_vals:
                formatted_vals.append(f"{v:.1f}" if is_temp else f"{v:.2f}")

            row = {
                "Zone Name": zone_name,
                "Schedule Name": real_sched_name,
                "Type": label
            }
            for h in range(24):
                row[str(h + 1)] = formatted_vals[h]

            final_rows.append(row)

    def _parse_through_mmdd(type_str: str):
        """
        Returns (month, day) if ' (Through M/D)' exists, else None.
        Works for both 'AllOtherDays' and 'AllOtherdays' etc.
        """
        m = re.search(r"\(Through\s*(\d{1,2})/(\d{1,2})\)", type_str)
        if not m:
            return None
        return (int(m.group(1)), int(m.group(2)))

    def _type_sort_key(type_str: str):
        """
        Sort by:
        1) base label (case-insensitive) so AllOtherDays and AllOtherdays group together
        2) through month/day if present
        3) original type string as tiebreaker (keeps stable ordering)
        """
        base = re.sub(r"\s*\(Through.*\)\s*$", "", type_str).strip().lower()
        md = _parse_through_mmdd(type_str)
        if md is None:
            md = (99, 99)  # non-through types go after through-types
        return (base, md[0], md[1], type_str)

    final_rows.sort(key=lambda x: (x["Zone Name"], x["Schedule Name"], _type_sort_key(x["Type"])))
    return final_rows

def extract_hvac_params(idf_path, filename):
    """
    Extracts HVAC parameters (Air Distribution, Heating Eff, Cooling Eff)
    based on the HVAC system tag in the filename.
    
    Filename format expected: Building_Vintage_HVACType_... (e.g. OfS_0_cAVVG_Ex.idf)
    """
    # Determine HVAC Type from filename
    parts = filename.split('_')
    if len(parts) < 3:
        return {"System Name": "Unknown", "Air": "N/A", "Heat": "N/A", "Cool": "N/A"}
    
    hvac_type = parts[2] # e.g., cAVVG, cDXGF
    
    # 2. Define Search Keys based on HVAC Type
    config = {
        "cAVVG": {
            "heat_key": "! → hw_boiler_eff =",
            "cool_key": "! → chw_chiller_cop ="
        },
        "cDXGF": {
            "heat_key": "! → main_heat_coil_eff =",
            "cool_key": "! → main_cool_coil_cop ="
        },
        "cPVVG": {
            "heat_key": "! → main_heat_coil_eff =",
            "cool_key": "! → main_cool_coil_cop ="
        },
        "cDXHP": {
            "heat_key": "! → main_heat_coil_cop =",
            "cool_key": "! → main_cool_coil_cop ="
        },
        "cDXOH": {
            "heat_key": None,
            "cool_key": "! → main_cool_coil_cop ="
        }
    }
    
    # If the HVAC type isn't in our list, return basic info
    if hvac_type not in config:
         return {
             "System Name": hvac_type, 
             "HVAC System Identifier": "Unknown",
             "Air Distribution": "Unknown System", 
             "Heating Efficiency": "N/A", 
             "Cooling Efficiency": "N/A"
         }

    search_rules = config[hvac_type]
    
    # Determine Category (Separated Logic)
    category = "TBD"

    # Condition 1: Check for explicit "main" keyword (Standard DX)
    is_explicit_main = False
    if search_rules["heat_key"] and "! → main" in search_rules["heat_key"]: is_explicit_main = True
    if search_rules["cool_key"] and "! → main" in search_rules["cool_key"]: is_explicit_main = True
    
    # Condition 2: Check for Central Plant keywords (Boiler / Chiller)
    # E.g. "! → hw_boiler_eff", "! → chw_chiller_cop"
    is_central_plant = False
    if search_rules["heat_key"] and "boiler" in search_rules["heat_key"]: is_central_plant = True
    if search_rules["cool_key"] and "chiller" in search_rules["cool_key"]: is_central_plant = True
    
    # Apply "Main" if either condition is met
    if is_explicit_main or is_central_plant:
        category = "Main"
    
    # Initialize results
    air_dist = "N/A"
    heat_eff = "-" if search_rules["heat_key"] is None else "N/A"
    cool_eff = "N/A"

    # 4. Scan the File
    try:
        with open(idf_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        def get_val(text, key):
            if not key: return None
            # Escape key, allow whitespace, capture non-whitespace value
            pattern = re.compile(re.escape(key) + r"\s*([^\s(]+)")
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
            return None

        # Extract Air Distribution
        val = get_val(content, "! → main_hvac_type =")
        if val:
            air_dist = val.replace('"', '')

        # Extract Heating
        if search_rules["heat_key"]:
            val = get_val(content, search_rules["heat_key"])
            if val: heat_eff = val

        # Extract Cooling
        if search_rules["cool_key"]:
            val = get_val(content, search_rules["cool_key"])
            if val: cool_eff = val

    except Exception as e:
        print(f"Error reading HVAC params from {filename}: {e}")

    return {
        "System Name": hvac_type,
        "HVAC System Identifier": category,
        "Air Distribution": air_dist,
        "Heating Efficiency": heat_eff,
        "Cooling Efficiency": cool_eff
    }

def extract_fan_data(idf_path, htm_path=None):
    """
    Read Fans table from *_etctbl.htm and match each System name to the IDF fan object.

    IDF name example: Hsp_0_cPVVG_Ex_etc.idf
      - HVAC name = cPVVG
      - Vintage token = Ex -> Existing; New -> New Construction

    HTM name example: Hsp_0_cPVVG_Ex_etctbl.htm (auto-inferred if not provided)

    For each fan row in HTM, output a dict with:
      Vintage, HVAC name,
      System name, System type,
      Total Static Pressure (TSP) (in w.c.),
      Fan Efficiency,
      Fan Motor and Drive Efficiency,
      W/cfm
    """
    import re
    from pathlib import Path

    idf_path = Path(idf_path)

    # Parse Vintage + HVAC name from IDF filename
    parts = idf_path.stem.split("_")  # e.g., Hsp,0,cPVVG,Ex,etc
    hvac_name = parts[2] if len(parts) >= 3 else "Unknown"
    vintage_token = parts[3] if len(parts) >= 4 else "Unknown"
    vintage = {"Ex": "Existing", "New": "New Construction"}.get(vintage_token, vintage_token)

    # Helpers for normalization and parsing
    def _norm(s: str) -> str:
        # normalize HTM vs IDF name: case + whitespace + nbsp
        s = str(s or "")
        s = s.replace("\u00A0", " ")
        s = re.sub(r"\s+", " ", s)
        return s.strip().upper()

    def _coerce_float(x):
        try:
            s = str(x).strip()
            s = s.replace("\u00A0", " ")
            s = re.sub(r"[,\s]+", "", s)
            return float(s)
        except Exception:
            return None

    # HTM path inference: *_etc.idf -> *_etctbl.htm
    def _infer_htm_path(p: Path) -> Path | None:
        if htm_path:
            hp = Path(htm_path)
            if hp.exists():
                return hp

        if p.name.lower().endswith("_etc.idf"):
            cand = p.with_name(p.name[:-8] + "_etctbl.htm")  # remove "_etc.idf"
            if cand.exists():
                return cand

        prefix = "_".join(p.stem.split("_")[:4])  # Hsp_0_cPVVG_Ex
        cands = sorted(p.parent.glob(prefix + "*_etctbl.htm"))
        if cands:
            return cands[0]

        cands = sorted(p.parent.glob("*_etctbl.htm"))
        if cands:
            return cands[0]

        cands = sorted(p.parent.glob("*.htm")) + sorted(p.parent.glob("*.html"))
        return cands[0] if cands else None

    # HTML table parsing
    def _html_unescape(s: str) -> str:
        return (s.replace("&nbsp;", " ")
                 .replace("&amp;", "&")
                 .replace("&lt;", "<")
                 .replace("&gt;", ">")
                 .replace("&quot;", '"')
                 .replace("&#39;", "'"))

    def _clean_cell(cell_html: str) -> str:
        cell_html = re.sub(r"(?is)<br\s*/?>", " ", cell_html)
        cell_html = re.sub(r"(?is)<.*?>", " ", cell_html)
        cell_html = _html_unescape(cell_html)
        return re.sub(r"\s+", " ", cell_html).strip()

    def _find_fans_table_html(html: str) -> str | None:
        tables = re.findall(r"(?is)<table\b.*?>.*?</table>", html)
        for t in tables:
            tl = t.lower()
            if (("end use subcategory" in tl) or ("end-use subcategory" in tl)) and \
               ("rated power per max air flow rate" in tl) and \
               ("max air flow rate" in tl):
                return t
        for t in tables:
            tl = t.lower()
            if (("end use subcategory" in tl) or ("end-use subcategory" in tl)) and \
               ("rated power per max air flow rate" in tl):
                return t
        return None

    def _parse_html_table(table_html: str):
        trs = re.findall(r"(?is)<tr\b.*?>(.*?)</tr>", table_html)
        all_rows = []
        for tr in trs:
            cells = re.findall(r"(?is)<t[dh]\b.*?>(.*?)</t[dh]>", tr)
            cells = [_clean_cell(c) for c in cells]
            if cells and any(c != "" for c in cells):
                all_rows.append(cells)

        if not all_rows:
            return [], []

        # header row = first row containing key headers
        hdr_idx = None
        for i, r in enumerate(all_rows[:30]):
            joined = " | ".join(r).lower()
            if ("rated power per max air flow rate" in joined) and \
               (("end use subcategory" in joined) or ("end-use subcategory" in joined)):
                hdr_idx = i
                break
        if hdr_idx is None:
            hdr_idx = 0

        header = all_rows[hdr_idx][:]
        header[0] = "System name"  # first col has blank header in E+ -> system name
        rows = all_rows[hdr_idx + 1:]
        return header, rows

    # IDF parsing for Fan:SystemModel and Fan:VariableVolume
    def _build_fan_systemmodel_map(idf_text: str) -> dict[str, str]:
        out = {}
        for m in re.finditer(r"(?is)Fan:SystemModel\s*,(.*?);", idf_text):
            body = m.group(1)
            name = body.split(",", 1)[0].strip().strip('"')
            out[_norm(name)] = "Fan:SystemModel," + body + ";"
        return out

    def _build_fan_varvol_map(idf_text: str) -> dict[str, str]:
        out = {}
        for m in re.finditer(r"(?is)Fan:VariableVolume\s*,(.*?);", idf_text):
            body = m.group(1)
            name = body.split(",", 1)[0].strip().strip('"')
            out[_norm(name)] = "Fan:VariableVolume," + body + ";"
        return out

    def _value_by_field_comment(block: str, field_label: str) -> str | None:
        # extract the value before ",  !- <field_label>"
        pat = re.compile(
            r"^\s*([^,;]+)\s*,\s*!-\s*" + re.escape(field_label) + r"(?:\s*\{[^}]*\})?\s*$",
            re.I | re.M
        )
        mm = pat.search(block)
        return mm.group(1).strip().strip('"') if mm else None

    # main extraction logic
    htm_file = _infer_htm_path(idf_path)
    if not htm_file or not htm_file.exists():
        return []

    html = htm_file.read_text(encoding="utf-8", errors="ignore")
    fans_table_html = _find_fans_table_html(html)
    if not fans_table_html:
        return []

    header, rows = _parse_html_table(fans_table_html)
    if not header or not rows:
        return []

    def _idx_contains(sub: str):
        sub_l = sub.lower()
        for i, h in enumerate(header):
            if sub_l in str(h).lower():
                return i
        return None

    idx_name = 0
    idx_sys_type = _idx_contains("End Use Subcategory")
    if idx_sys_type is None:
        idx_sys_type = _idx_contains("End-Use Subcategory")

    idx_wminft3 = _idx_contains("Rated Power Per Max Air Flow Rate")

    # Load IDF once, build maps once
    idf_text = idf_path.read_text(encoding="utf-8", errors="ignore")
    sysmodel_map = _build_fan_systemmodel_map(idf_text)
    varvol_map = _build_fan_varvol_map(idf_text)

    out = []
    for r in rows:
        if len(r) < len(header):
            r = r + [""] * (len(header) - len(r))

        system_name_raw = str(r[idx_name]).strip()
        if not system_name_raw or system_name_raw.lower() == "nan":
            continue
        if system_name_raw.lower() in {"type", "system name"}:
            continue

        system_key = _norm(system_name_raw)

        rec = {
            "Vintage": vintage,
            "HVAC name": hvac_name,
            "System name": system_name_raw,
            "System type": (lambda raw: raw if raw.lower() not in {"", "n/a", "general", "nan"} else system_name_raw)(str(r[idx_sys_type]).strip() if idx_sys_type is not None else ""),
            "Total Static Pressure (TSP) (in w.c.)": "N/A",
            "Fan Efficiency": "N/A",
            "Fan Motor and Drive Efficiency": "N/A",
            "W/cfm": "N/A",
        }

        # HTM: W-min/ft3 -> W/cfm
        if idx_wminft3 is not None:
            v = _coerce_float(r[idx_wminft3])
            if v is not None:
                rec["W/cfm"] = v

        # IDF: try Fan:SystemModel first
        block = sysmodel_map.get(system_key)
        if block:
            dp_pa = _coerce_float(_value_by_field_comment(block, "Design Pressure Rise"))
            if dp_pa is not None:
                rec["Total Static Pressure (TSP) (in w.c.)"] = dp_pa / 249.08891  # Pa -> in.w.c.

            me = _coerce_float(_value_by_field_comment(block, "Motor Efficiency"))
            if me is not None:
                rec["Fan Motor and Drive Efficiency"] = me

            fe = _coerce_float(_value_by_field_comment(block, "Fan Total Efficiency"))
            if fe is not None:
                rec["Fan Efficiency"] = fe

        else:
            # IDF: Fan:VariableVolume
            block2 = varvol_map.get(system_key)
            if block2:
                # For VariableVolume object, the comment labels are:
                #   Fan Efficiency
                #   Pressure Rise {Pa}
                #   Motor Efficiency
                fe = _coerce_float(_value_by_field_comment(block2, "Fan Efficiency"))
                if fe is not None:
                    rec["Fan Efficiency"] = fe

                dp_pa = _coerce_float(_value_by_field_comment(block2, "Pressure Rise {Pa}"))
                if dp_pa is None:
                    dp_pa = _coerce_float(_value_by_field_comment(block2, "Pressure Rise"))
                if dp_pa is not None:
                    rec["Total Static Pressure (TSP) (in w.c.)"] = dp_pa / 249.08891

                me = _coerce_float(_value_by_field_comment(block2, "Motor Efficiency"))
                if me is not None:
                    rec["Fan Motor and Drive Efficiency"] = me

        out.append(rec)

    return out

def extract_infiltration_rate(idf_path, tol=1e-9, decimals=6):
    """
    Extract infiltration from an IDF by finding the field:
      !- Flow per Exterior Surface Area {m3/s-m2}

    Logic:
    - Collect *all* values for that field in the file.
    - If all values are identical (within tol), use that value.
    - Otherwise, use the average.
    - Convert from (m3/s-m2) to (cfm/ft2).

    Returns:
      str: converted value in cfm/ft2 (formatted), or "N/A" if not found.
    """
    # (m3/s)/m2 -> (cfm)/ft2
    # 1 m3/s = 2118.880003 cfm
    # 1 m2   = 10.763910417 ft2
    M3S_M2_TO_CFM_FT2 = 2118.880003 / 10.763910417  # ≈ 196.8503937

    try:
        with open(idf_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        # Grab the numeric field value that appears immediately before the label comment.
        # Works whether the line ends with "," or ";" (last field in object).
        pattern = re.compile(
            r"""
            ^\s*
            (?P<val>[+-]?(?:\d+\.?\d*|\.\d+)(?:[Ee][+-]?\d+)?)   # number (incl. sci notation)
            \s*[,;]\s*
            !-\s*Flow\s+per\s+Exterior\s+Surface\s+Area\s*\{m3/s-m2\}
            """,
            re.IGNORECASE | re.MULTILINE | re.VERBOSE,
        )

        vals_m3s_m2 = [float(m.group("val")) for m in pattern.finditer(text)]
        if not vals_m3s_m2:
            return "N/A"

        # Decide identical vs average (tolerance-based)
        first = vals_m3s_m2[0]
        if all(abs(v - first) <= tol for v in vals_m3s_m2):
            chosen = first
        else:
            chosen = sum(vals_m3s_m2) / len(vals_m3s_m2)

        cfm_ft2 = chosen * M3S_M2_TO_CFM_FT2
        return f"{cfm_ft2:.{decimals}f}"

    except Exception as e:
        print(f"Error reading infiltration from {idf_path}: {e}")
        return "N/A"

def extract_gas_equipment(idf_path):
    """
    Parses IDF for GasEquipment objects.
    Extracts 'Zone or ZoneList Name' and 'Power per Zone Floor Area {W/m2}'.
    Converts W/m2 to Btu/h-ft2 (IP Unit).
    Returns a list of dictionaries.
    """
    gas_data = []
    
    if not os.path.exists(idf_path):
        return gas_data

    try:
        with open(idf_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Split file into objects by semicolon
        objects = content.split(';')
        
        for obj in objects:
            # Clean comments and whitespace
            lines = obj.splitlines()
            cleaned_lines = [line.split('!')[0].strip() for line in lines]
            joined_obj = ''.join(cleaned_lines)
            
            # Split into fields
            fields = [f.strip() for f in joined_obj.split(',')]
            
            if not fields: 
                continue
            
            # Check if object is GasEquipment
            if fields[0].lower() == 'gasequipment':
                # GasEquipment Structure:
                # ...
                # Power per Zone Floor Area {W/m2}
                
                if len(fields) >= 7:
                    zone_name = fields[2]
                    watts_per_area = fields[6]
                    
                    try:
                        val_si = float(watts_per_area)
                        
                        # 1 W/m2 = 0.3169983306 Btu/h-ft2
                        val_ip = val_si * 0.3169983306
                        
                        gas_data.append({
                            "Zone Name": zone_name,
                            "Gas Loads (Btu/h-ft2)": round(val_ip, 4)
                        })
                    except ValueError:
                        continue
                        
    except Exception as e:
        print(f"Error parsing GasEquipment in {idf_path}: {e}")
        
    gas_data.sort(key=lambda x: x["Zone Name"])
    
    return gas_data

def extract_refrigeration_system(idf_path, filename):
    """
    Extracts Refrigeration System parameters using proximity search in IDF comments.
    """
    # Determine Vintage
    if "_Ex_" in filename or "_Ex." in filename or "Ex_" in filename:
        vintage = "Existing"
    elif "_New_" in filename or "_New." in filename or "New_" in filename:
        vintage = "New Construction"
    else:
        vintage = "Unknown"

    if not os.path.exists(idf_path):
        return [{"Vintage": vintage, "Refrigeration System Name": "File Not Found"}]

    try:
        with open(idf_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        return [{"Vintage": vintage, "Refrigeration System Name": f"Error: {e}"}]

    lines = content.splitlines()
    
    # Matches: ! [arrow/bullet] key = value
    base_patt = r'!\s*(?:→|->|•)?\s*'
    
    patterns = {
        'sys_name': re.compile(base_patt + r'ref_system_name\s*=\s*"?([^"\r\n]+)"?', re.IGNORECASE),
        'cond_type': re.compile(base_patt + r'condenser_type\s*=\s*"?([^"\r\n]+)"?', re.IGNORECASE),
        'fan_power': re.compile(base_patt + r'cond_fan_power\s*=\s*([0-9.]+)', re.IGNORECASE),
        'fluid': re.compile(base_patt + r'working_fluid\s*=\s*"?([^"\r\n]+)"?', re.IGNORECASE)
    }

    # Scan lines and record matches with line numbers
    tokens = []
    for i, line in enumerate(lines):
        for key, regex in patterns.items():
            match = regex.search(line)
            if match:
                val = match.group(1).strip()
                tokens.append({'line': i, 'key': key, 'value': val})

    # Group by System Name
    systems = [t for t in tokens if t['key'] == 'sys_name']
    
    if not systems:
        return [] # Return empty to trigger "No refrigeration system was found" in Main

    results = []
    for sys_token in systems:
        sys_line = sys_token['line']
        
        # Helper to find nearest parameter
        def get_nearest(target_key):
            candidates = [t for t in tokens if t['key'] == target_key]
            if not candidates: return "N/A"
            # Find candidate with minimum distance to system line
            best = min(candidates, key=lambda t: abs(t['line'] - sys_line))
            # Potential TODO: Add a threshold (e.g., must be within 50 lines) to avoid bad matches in huge files
            return best['value']

        row = {
            "Vintage": vintage,
            "Refrigeration System Name": sys_token['value'],
            "Condenser Fan Power": get_nearest('fan_power'),
            "Working fluid": get_nearest('fluid'),
            "Condenser Type": get_nearest('cond_type')
        }
        # Add units to Fan Power if found and numeric
        if row["Condenser Fan Power"] != "N/A":
             row["Condenser Fan Power"] += " W"

        results.append(row)

    return results

def extract_zone_thermostats(idf_path):
    """
    Extracts Heating/Cooling Setpoints and Setbacks for EACH Zone.
    
    Chain of Logic:
    1. ZoneControl:Thermostat -> Links 'Zone Name' to a 'Control Object Name'.
    2. ThermostatSetpoint:DualSetpoint -> Links 'Control Object Name' to 'Heating/Cooling Schedules'.
    3. Schedule:Compact -> Contains the actual numeric temperature values.
    """
    zone_data = []

    if not os.path.exists(idf_path):
        return zone_data

    try:
        with open(idf_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Clean comments and split into objects
        no_comments = re.sub(r'!.*', '', content)
        objects = no_comments.split(';')

        schedule_map = {}
        
        for obj in objects:
            if "Schedule:Compact" in obj:
                fields = [f.strip() for f in obj.replace('\n', ' ').split(',')]
                if len(fields) < 3: continue
                
                sched_name = fields[1].upper()
                values = []
                
                for field in fields[2:]:
                    try:
                        val = float(field)
                        if 5 <= val <= 60: 
                            values.append(val)
                    except ValueError:
                        continue
                
                if values:
                    schedule_map[sched_name] = {"min": min(values), "max": max(values)}

        dual_setpoint_map = {}
        
        for obj in objects:
            if "ThermostatSetpoint:DualSetpoint" in obj:
                fields = [f.strip() for f in obj.replace('\n', ' ').split(',')]
                if len(fields) >= 4:
                    name = fields[1].upper()
                    htg_sched = fields[2].upper()
                    clg_sched = fields[3].upper()
                    dual_setpoint_map[name] = {"heat": htg_sched, "cool": clg_sched}

        for obj in objects:
            if "ZoneControl:Thermostat" in obj:
                fields = [f.strip() for f in obj.replace('\n', ' ').split(',')]
                # Field 0: Type, 1: Name, 2: Zone Name, 3: Control Type Sched, 4: Type 1, 5: Name 1
                if len(fields) >= 6:
                    zone_name = fields[2] # Actual Zone Name
                    
                    # Look for the DualSetpoint object name
                    control_name = None
                    
                    # Loop through fields to find the DualSetpoint declaration
                    for i in range(4, len(fields)-1, 2):
                        if "DualSetpoint" in fields[i]:
                            control_name = fields[i+1].upper()
                            break
                    
                    if control_name and control_name in dual_setpoint_map:
                        scheds = dual_setpoint_map[control_name]
                        
                        # Heating Defaults
                        h_setpoint = "N/A"
                        h_setback = "N/A"
                        if scheds["heat"] in schedule_map:
                            # Heating: Max = Setpoint, Min = Setback
                            h_vals = schedule_map[scheds["heat"]]
                            h_setpoint = h_vals["max"]
                            h_setback = h_vals["min"]

                        # Cooling Defaults
                        c_setpoint = "N/A"
                        c_setback = "N/A"
                        if scheds["cool"] in schedule_map:
                            # Cooling: Min = Setpoint, Max = Setback
                            c_vals = schedule_map[scheds["cool"]]
                            c_setpoint = c_vals["min"]
                            c_setback = c_vals["max"]

                        zone_data.append({
                            "Zone Name": zone_name,
                            "Heating Setpoint": h_setpoint,
                            "Heating Setback": h_setback,
                            "Cooling Setpoint": c_setpoint,
                            "Cooling Setback": c_setback
                        })

    except Exception as e:
        print(f"Error extracting zone thermostats in {idf_path}: {e}")

    # Sort by Zone Name
    zone_data.sort(key=lambda x: x["Zone Name"])
    return zone_data


def extract_end_use_breakdown(htm_path):
    """
    Parses *tbl.htm to extract the 'End Uses' breakdown table.
    Returns a list of dictionaries with keys: 'End Use', 'Electricity [kBtu]', 'Natural Gas [kBtu]'.
    """
    data_rows = []
    
    if not os.path.exists(htm_path):
        return data_rows

    try:
        with open(htm_path, 'r', errors='ignore') as f:
            html_content = f.read()

        # Locate the "End Uses" table
        search_term = "<b>End Uses</b>"
        start_idx = html_content.find(search_term)
        
        if start_idx != -1:
            table_start = html_content.find("<table", start_idx)
            table_end = html_content.find("</table>", table_start)
            
            if table_start != -1:
                table_html = html_content[table_start:table_end]
                rows = table_html.split("<tr>")
                
                for row in rows:
                    if "<td" not in row: continue
                    
                    cells = []
                    parts = row.split("</td>")
                    for p in parts:
                        if "<td" in p:
                            # Robust cleaning: remove tags, then strip whitespace
                            clean_text = re.sub(r'<[^>]+>', '', p).strip()
                            cells.append(clean_text)
                    
                    # Expecting at least 3 cells: Category, Electricity, Natural Gas
                    if len(cells) >= 3:
                        category = cells[0]
                        elec = cells[1]
                        gas = cells[2]
                        
                        # Filter out Header rows (usually contain units like [kBtu])
                        if "Electricity" in elec or "Natural Gas" in gas:
                            continue
                        
                        # check for blank category
                        is_blank = (not category) or (not category.strip()) or ("&nbsp" in category) or ("\xa0" in category)
                        
                        if is_blank:
                             continue # SKIP THIS ROW
                        
                        data_rows.append({
                            "End Use": category,
                            "Electricity [kBtu]": elec,
                            "Natural Gas [kBtu]": gas
                        })
                        
    except Exception as e:
        print(f"Error parsing End Uses Breakdown in {htm_path}: {e}")
        
    return data_rows




def extract_shading_data(idf_path, window_map=None):
    """
    Parses IDF for Shading objects.
    - Shading:Zone:Detailed: Calculates dimensions (Width/Length) using vertex coordinates.
    - Shading:Overhang/Fin: Calculates dimensions using window size + extensions.
    
    Returns list of dicts with keys: 'Shading Name', 'Width', 'Length'
    """
    shading_rows = []
    if window_map is None:
        window_map = {}
    
    if not os.path.exists(idf_path):
        return shading_rows

    try:
        with open(idf_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Clean comments and normalize whitespace
        no_comments = re.sub(r'!.*', '', content)
        cleaned_text = ' '.join(no_comments.split())
        objects = cleaned_text.split(';')

        for obj in objects:
            fields = [f.strip() for f in obj.split(',')]
            if len(fields) < 2: continue
            
            obj_type = fields[0].lower()
            
            # Shading:Zone:Detailed
            if obj_type == "shading:zone:detailed":
                # Fields: Name(1), Base(2), Sched(3), NumVerts(4), X1(5), Y1(6), Z1(7)...
                if len(fields) >= 11:
                    try:
                        name = fields[1]
                        
                        # Extract Vertices 1, 2, and 3 to determine rectangle size
                        x1 = float(fields[5]); y1 = float(fields[6]); z1 = float(fields[7])
                        x2 = float(fields[8]); y2 = float(fields[9]); z2 = float(fields[10])
                        x3 = float(fields[11]); y3 = float(fields[12]); z3 = float(fields[13])
                        
                        # Calculate Euclidean Distance between V1-V2 and V2-V3
                        dist_1_2 = math.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)
                        dist_2_3 = math.sqrt((x3 - x2)**2 + (y3 - y2)**2 + (z3 - z2)**2)
                        
                        # Convert Meters to Feet
                        side_a_ft = dist_1_2 * 3.28084
                        side_b_ft = dist_2_3 * 3.28084
                        
                        # Logic: Longest side is "Width", Shortest is "Length"
                        width = max(side_a_ft, side_b_ft)
                        length = min(side_a_ft, side_b_ft)
                        
                        shading_rows.append({
                            "Shading Name": name,
                            "Width": round(width, 2),
                            "Length": round(length, 2)
                        })
                    except (ValueError, IndexError):
                        continue

            # Shading:Overhang
            elif obj_type == "shading:overhang":
                if len(fields) >= 8:
                    try:
                        name = fields[1]
                        win_name = fields[2]
                        left_ext = float(fields[5])
                        right_ext = float(fields[6])
                        depth_m = float(fields[7])
                        
                        win_dims = window_map.get(win_name.upper(), {"w": 0, "h": 0})
                        win_w = win_dims["w"]
                        
                        # Width = Window Width + Extensions
                        # Length = Projection Depth
                        width_ft = win_w + ((left_ext + right_ext) * 3.28084)
                        length_ft = depth_m * 3.28084
                        
                        shading_rows.append({
                            "Shading Name": name,
                            "Width": round(width_ft, 2),
                            "Length": round(length_ft, 2)
                        })
                    except ValueError: continue

            # Shading:Fin
            elif obj_type == "shading:fin":
                if len(fields) >= 8:
                    try:
                        name = fields[1]
                        win_name = fields[2]
                        l_depth = float(fields[7])
                        
                        win_dims = window_map.get(win_name.upper(), {"w": 0, "h": 0})
                        win_h = win_dims["h"]
                        
                        l_above = float(fields[4])
                        l_below = float(fields[5])
                        
                        # Width = Vertical Span (Window Height + Extensions)
                        # Length = Projection Depth
                        height_ft = win_h + ((l_above + l_below) * 3.28084)
                        proj_ft = l_depth * 3.28084
                        
                        shading_rows.append({
                            "Shading Name": name,
                            "Width": round(height_ft, 2),
                            "Length": round(proj_ft, 2)
                        })
                    except ValueError: continue

    except Exception as e:
        print(f"Error parsing shading geometry: {e}")

    return shading_rows