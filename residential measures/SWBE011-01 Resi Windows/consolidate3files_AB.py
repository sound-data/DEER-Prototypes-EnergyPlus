import os
import pandas as pd

#This file was specifc to Resindetial Windows measure which had climate-dependent parameters namely U-factor and SHGC
#This will be used if there are multiple subfolders for a measure. For ex, Resi windows has Msr1, Msr2, Ms3 subfolders
#This will conolidate postgreSQL input CSV files e.g:current_msr_mat.csv,sim_annual.csv,sim_hourly_wb.csv for multiple sets

# Base filenames to consolidate
BASE_FILES = [
    "sim_annual",
    "sim_hourly_wb",
    "current_msr_mat"
]

# Use the current working directory (relative path)
INPUT_FOLDER = os.getcwd()
OUTPUT_FOLDER = INPUT_FOLDER  # same folder for output

def consolidate_files(base_name):
    """
    Consolidate all CSV files that:
    - start with the base_name (no prefix allowed)
    - have a filename longer than the base_name (meaning they have suffixes)
    - end with .csv
    """
    files_to_merge = []

    for fname in os.listdir(INPUT_FOLDER):
        if not fname.endswith(".csv"):
            continue

        name_without_ext = fname[:-4]  # remove .csv

        # Must start with base_name (no prefix allowed)
        if not name_without_ext.startswith(base_name):
            continue

        # Must be longer than base_name (meaning it has a suffix)
        if len(name_without_ext) <= len(base_name):
            continue

        files_to_merge.append(os.path.join(INPUT_FOLDER, fname))

    if not files_to_merge:
        print(f"No suffixed files found for {base_name}. Skipping.")
        return

    print(f"Found {len(files_to_merge)} files for {base_name}:")
    for f in files_to_merge:
        print("  -", os.path.basename(f))

    # Read all files as text to preserve formatting
    df_list = [
        pd.read_csv(
            f,
            dtype=str,
            keep_default_na=False,  # preserve "None"
            na_values=[]            # do not convert anything to NaN
        )
        for f in files_to_merge
    ]

    # Capture the header row from the first file
    header_row = df_list[0].iloc[0].to_dict()

    # Concatenate
    combined = pd.concat(df_list, ignore_index=True)

    # Remove any row that matches the header row
    combined = combined[~combined.apply(lambda row: row.to_dict() == header_row, axis=1)]

    # Universal deduplication (safe for all tables)
    combined = combined.drop_duplicates()

    # Output file
    output_file = os.path.join(OUTPUT_FOLDER, f"{base_name}.csv")
    combined.to_csv(output_file, index=False)

    print(f"✅ Consolidated file written to: {output_file}\n")


def main():
    for base in BASE_FILES:
        consolidate_files(base)


if __name__ == "__main__":
    main()
