# SWCR003-05 Fan Motor Retrofit for a Refrigerated Display Case

## Measure Description

This folder contains the commercial refrigerated fan motor measure setup used for DEER prototype simulation, result scraping, and downstream post-processing.

### Key Changes in This Revision
- Update to CZ2025 weather files
- **Retired PMS offerings** — the measure case is only ECM

## Cohorts and Case Names

### Building Type and Vintage
- Gro (Grocery Store) — Ex

### Equipment and Fan Motor Type
- MT (medium temperture)
- LT (low temperature)
- PSC (permanent split capacitor motor)
- SHP (shaded pole motor)
- ECM (electronically commutated motor)

### Case Names (TechIDs)

| Case Name (TechID) | Equipment Type | Fan Motor Type |
|-------------------|--------------|--------------|
| NE-Ref_Storage-ReachIn-MT-PSC-Std | MT | PSC |
| NE-Ref_Storage-ReachIn-MT-SHP-Std | MT | SHP |
| NE-Ref_Storage-ReachIn-LT-PSC-Std | LT | PSC |
| NE-Ref_Storage-ReachIn-LT-SHP-Std | LT | SHP |
| NE-Ref_Storage-ReachIn-MT-ECM-Msr | MT | ECM |
| NE-Ref_Storage-ReachIn-LT-ECM-Msr | LT | ECM |

## Query File for Normalizing Units

The file `query.txt` includes queries for cooling and heating capacity. After running simulations:

```bash
cd 'commercial measures/SWCR003-05'
python result2.py -q query.txt
```
## Data Transformation and Post-Processing
Measure Working List: DEER_EnergyPlus_Modelkit_Measure_list_working_SWCR003-05.xlsx

## Post-Processing Steps
- Run simulations and confirm result files
- Scrape outputs with 'scripts/result2.py using query.txt'
- Run transformation 'scripts from scripts/data transformation'
- Review generated files: current_msr_mat.csv, sim_annual.csv, sim_hourly_eu.csv, sim_hourly_wb.csv

## Load Shape Workaround
The load shape files (found in CEDARS_LoadShape_Com.zip) are missing the 'NormUnit' column required for uploading to CEDARS. The missing column must be added manually into each of the 3 load shape files (one for each building type). The column must be added in between the 'BldgLoc' and 'Type (Whole Building or End Use)' columns with the column header 'NormUnit' and value 'Cap-Tons' for each line.