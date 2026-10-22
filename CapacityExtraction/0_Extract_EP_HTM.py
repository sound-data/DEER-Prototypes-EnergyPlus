import os
import shutil

# def _require_env(key: str) -> str:
#     v = os.environ.get(key)
#     if not v or not str(v).strip():
#         raise EnvironmentError(
#             f"Missing required environment variable '{key}'. "
#             "Run this script via Run1_Pre_Data_Extraction.py."
#         )
#     return str(v)


# defines the source directories and categories
# format: ("Source Path", "Category Name for Destination")


# Read from env (Run1_Pre_Data_Extraction.py sets these)
# RUNS_EXISTING_DIR = _require_env("RUNS_EXISTING_DIR")
# RUNS_NEW_DIR = _require_env("RUNS_NEW_DIR")
# run_configurations = [
#     (RUNS_EXISTING_DIR, "Existing"),
#     (RUNS_NEW_DIR, "New-Construction"),
# ]

# base_destination_root = _require_env("EP_FILES_ROOT")
# files_to_extract = {
#     "instance.idf": ".idf",
# }

run_configurations = [
    (
        [
            # For prototype excluding hotel
            r"C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\commercial measures\SWXX000-00 TRC System Types\SWXX000-00 TRC System Types_Ex\runs",
            r"C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\commercial measures\SWXX000-00 TRC System Types\SWXX000-00 TRC System Types_Ex_1\runs",
            r"C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\commercial measures\SWXX000-00 TRC System Types\SWXX000-00 TRC System Types_Ex_2\runs",
            r"C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\commercial measures\SWXX000-00 TRC System Types\SWXX000-00 TRC System Types_Ex_3\runs",
            # For hotel
            r"C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\commercial measures\SWXX000-00 TRC System Types\SWXX000-00 TRC System Types_Htl_Ex\runs",
        ],
        "Existing"
    ),
    # (
    #     # For prototype excluding hotel
    #     # r"C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\commercial measures\SWXX111-00 Example_SEER_AC\SWXX111-00 Example_SEER_AC_New\runs",
    #     # For hotel
    #     # r"C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\commercial measures\SWXX111-00 Example_SEER_AC\SWXX111-00 Example_SEER_AC_Htl_New\runs",
    #     "New-Construction"
    # )
]

# The main destination root
base_destination_root = r"C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\CapacityExtraction\EP_Files"

# files to extract and their extensions
files_to_extract = {
    "instance.idf": ".idf", # Optional
    "instance-tbl.htm": ".htm" 
}

total_extracted = 0

# Start processing each configuration
for run_dirs, category_name in run_configurations:
    for base_runs_dir in run_dirs:         
        print(f"Processing Category: {category_name}")
        print(f"Source: {base_runs_dir}")

        # loop through CZ01 to CZ16
        for i in range(1, 17):
            cz_string = f"CZ{i:02}"
            source_cz_path = os.path.join(base_runs_dir, cz_string)

            if os.path.exists(source_cz_path):
                # print(f"Processing {cz_string}")

                # Loop through the folders inside this CZ (e.g., OfS&0&cAVVG&Ex&etc)
                for folder_name in os.listdir(source_cz_path):
                    folder_path = os.path.join(source_cz_path, folder_name)

                    if os.path.isdir(folder_path):
                        
                        # split folder name to get building type
                        # e.g., "OfS&0&..." -> "OfS" -> first part before '&'
                        try:
                            parts = folder_name.split('&')
                            building_type = parts[0]
                        except IndexError:
                            building_type = "Unknown"

                        # 2. Construct final destination path including CZ
                        # Result: ...\EP_Files\OfS\existing\CZ01
                        final_dest_dir = os.path.join(base_destination_root, building_type, category_name, cz_string)

                        # Create destination if it doesn't exist
                        if not os.path.exists(final_dest_dir):
                            os.makedirs(final_dest_dir)

                        # Path to ...\TechIDBase
                        tech_id_path = os.path.join(folder_path, "TechIDBase")

                        if os.path.exists(tech_id_path):
                            for original_filename, extension in files_to_extract.items():
                                source_file = os.path.join(tech_id_path, original_filename)
                                
                                if os.path.exists(source_file):
                                    # Rename: Replace '&' with '_'
                                    modified_folder_name = folder_name.replace('&', '_')
                                    new_filename = f"{modified_folder_name}{extension}"
                                    destination_file = os.path.join(final_dest_dir, new_filename)
                                    
                                    shutil.copy2(source_file, destination_file)
                                    total_extracted += 1
                                    # print(f"Saved: {new_filename} -> {final_dest_dir}") 

# Check final count
print(f"Total files extracted: {total_extracted}")