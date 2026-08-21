import pandas as pd
import glob
import os

# Folder path
folder = r"C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\CapacityExtraction\Compiled_Data"
result_folder = r"C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\CapacityExtraction"
csv_files = glob.glob(os.path.join(folder, "*_capacity.csv"))

dfs = []
for filepath in csv_files:
    filename = os.path.basename(filepath)                  
    prototype = filename.replace("_capacity.csv", "")      # before _capacity
    
    df = pd.read_csv(filepath, encoding="utf-8-sig")       
    df.insert(0, "Prototype", prototype)                   # add as a new column name
    dfs.append(df)

merged = pd.concat(dfs, ignore_index=True)

output_path = os.path.join(result_folder, "merged_prototype.csv")
merged.to_csv(output_path, index=False)

print(f"Merged {len(csv_files)} files → {output_path}")
print(f"Total rows: {len(merged)}")
print(merged["Prototype"].unique())