# Main System Net Cooling Coil Capacity and Fan Power Extraction - DEER Nonresidential Prototype
Extracts main HVAC system net cooling coil capacity and fan power from DEER nonresidential prototype outputs and compiles them into a single CSV.

---

## Requirements

- **Python 3.10+**
- **EnergyPlus 22.2** — the HTML report parser reads fan and coil tables by fixed column position. A different EP version may shift column order and cause silent wrong results. Verify the EnergyPlus version before using the scripts
- Dependencies: `pip install pandas numpy`

---

## Paths to Update Before Running

### Step 0 — `0_Extract_EP_HTM.py`
| Variable | What to set |
|---|---|
| `run_configurations` | List of source `runs\` directories and their vintage label. Add hotel runs as a separate entry. |
| `base_destination_root` | Where organized `EP_Files\` will be written |

### Step 1 — `1_ExtactAllNeedInformation.py`
| Variable | What to set |
|---|---|
| `base_root_dir` | Path to `EP_Files\` created in Step 0 |
| `output_folder` | Destination for raw extracted CSVs |

### Step 2 — `2_ExtractMainHVACFanOnly.py`
| Variable | What to set |
|---|---|
| `CSV_TARGET_FOLDER` | Path to raw CSVs from Step 1 |
| `CSV_OUTPUT_FOLDER` | Destination for processed CSVs |
| `PXT_ROOT_PATH` | Path to `prototypes\` root — which contains a `templates\root.pxt` for each prototype, used to classify Main/Alternative/Customized HVAC systems |

### Step 3 — `3_Merge_Result.py`
| Variable | What to set |
|---|---|
| `INPUT_DIR` | Path to processed CSVs from Step 2 |
| `OUTPUT_DIR` | Destination for per-prototype capacity CSVs |

### Step 4 — `4_MergeInOne.py`
| Variable | What to set |
|---|---|
| `folder` | Path to compiled CSVs from Step 3 |
| `result_folder` | Destination for final `merged_prototype.csv` |