import pandas as pd
import io
import re
import os

def _require_env(key: str) -> str:
    v = os.environ.get(key)
    if not v or not str(v).strip():
        raise EnvironmentError(
            f"Missing required environment variable '{key}'. "
            f"Run this script via Run3_Scorecard_Generation.py."
        )
    return str(v)


# INPUT: compiled raw CSVs
raw_data_dir = _require_env("COMPILED_DATA_DIR")

# OUTPUT: Tab_from_Raw under SCORECARD_PATH
scorecard_root = _require_env("SCORECARD_PATH")

# If SCORECARD_PATH folder doesn't exist, create it
os.makedirs(scorecard_root, exist_ok=True)

output_folder_name = "Tab_from_Raw"
source_dir = scorecard_root
output_dir = os.path.join(source_dir, output_folder_name)

# Create Tab_from_Raw if missing
os.makedirs(output_dir, exist_ok=True)

def clean_sheet_name(name):
    """
    Cleans the table name to be a valid Excel sheet name:
    1. Remove all non-letter characters (spaces, numbers, symbols).
    2. Convert to lowercase.
    3. Add 'Raw_' prefix (Capital R).
    4. Truncate to 31 characters due to Excel sheet name limit.
    """
    clean_name = re.sub(r'[^a-zA-Z]', '', name)
    clean_name = clean_name.lower()
    clean_name = f"Raw_{clean_name}"
    return clean_name[:31]

def main():
    # Verify output base directory exists
    if not os.path.exists(source_dir):
        # print(f"Error: The output base directory '{source_dir}' does not exist.")
        return

    # Verify raw data directory exists
    if not os.path.exists(raw_data_dir):
        # print(f"Error: The raw data directory '{raw_data_dir}' does not exist.")
        return

    # Setup Output Directory inside the output base directory
    output_dir = os.path.join(source_dir, output_folder_name)
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            # print(f"Created output folder: {output_dir}")
        except OSError as e:
            # print(f"Error creating output folder: {e}")
            return
            return
    else:
        # print(f"Output folder already exists: {output_dir}")
        pass

    # Find all _raw.csv files in the RAW DATA directory (NEW)
    try:
        all_files = os.listdir(raw_data_dir)
        target_files = [f for f in all_files if f.lower().endswith('_raw.csv')]
    except Exception as e:
        # print(f"Error reading raw data directory: {e}")
        return

    if not target_files:
        # print(f"No *_raw.csv files found in {raw_data_dir}")
        return

    # print(f"Found {len(target_files)} files to process...")

    # Process each file
    for filename in target_files:
        input_full_path = os.path.join(raw_data_dir, filename)  # NEW
        
        # Determine output filename: remove "_raw.csv" (last 8 chars) and add "_Raw.xlsx"
        prefix = filename[:-8]
        output_filename = f"{prefix}_Raw.xlsx"
        output_full_path = os.path.join(output_dir, output_filename)

        print(f"Processing: {filename}...")

        try:
            with open(input_full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split content by '###' delimiter
            parts = content.split('###')

            if len(parts) < 3:
                # print(f"  Skipping: Structure does not match expected '###' format.")
                continue

            with pd.ExcelWriter(output_full_path, engine='openpyxl') as writer:
                has_data = False

                # Iterate through parts: [Header, TableName1, Data1, TableName2, Data2, ...]
                for i in range(1, len(parts), 2):
                    if i + 1 >= len(parts):
                        break

                    table_name = parts[i].strip()
                    csv_data = parts[i + 1].strip()

                    if not table_name or not csv_data:
                        continue

                    try:
                        df = pd.read_csv(io.StringIO(csv_data))
                        sheet_name = clean_sheet_name(table_name)

                        # Handle duplicate sheet names within the same file
                        if sheet_name in writer.book.sheetnames:
                            count = 1
                            base_length = 28  # Leave room for "_1"
                            while f"{sheet_name[:base_length]}_{count}" in writer.book.sheetnames:
                                count += 1
                            sheet_name = f"{sheet_name[:base_length]}_{count}"

                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        has_data = True

                    except pd.errors.EmptyDataError:
                        # print(f"  Warning: Empty data for table '{table_name}'")
                        pass
                    except Exception as e:
                        # print(f"  Error processing table '{table_name}': {e}")
                        pass

            if has_data:
                # print(f"  -> Saved to: {output_full_path}")
                pass
            else:
                # print(f"  -> No valid tables found.")
                pass

        except Exception as e:
            # print(f"  An error occurred: {e}")
            pass

    print("\nProcessing complete.")

if __name__ == "__main__":
    main()
