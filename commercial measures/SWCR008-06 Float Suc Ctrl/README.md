# SWCR008-06 Floating Suction Controls, Multiplex

## Measure Description

This folder contains the commercial floating suction controls measure setup used for DEER prototype simulation, result scraping, and downstream post-processing.

### Key Changes in This Revision
- Update to CZ2025 weather files
- Added condenser sizing for air-cooled condensers

## Cohorts and Case Names

### Building Types
- Gro (Grocery Store) — Ex, New

### Case Names (TechIDs)

| Case Name (TechID) | Case Type |
|-------------------|--------------|
| NE-Ref_Storage-RefControl-FixSucTemp-AirCool | Base |
| NE-Ref_Storage-RefControl-FltSucTemp-EvapCool | Measure |

## Query File for Normalizing Units

The file `query.txt` includes queries for cooling and heating capacity. After running simulations:

```bash
cd 'commercial measures/SWCR008-06'
python result2.py -q query.txt
```
## Data Transformation and Post-Processing
Measure Working List: DEER_EnergyPlus_Modelkit_Measure_list_working_SWCR008-06.xlsx

## Post-Processing Steps
- Run simulations and confirm result files
- Scrape outputs with 'scripts/result2.py' using 'query.txt'
- Run transformation scripts from 'scripts/data transformation'
- Review generated files: current_msr_mat.csv, sim_annual.csv, sim_hourly_eu.csv, sim_hourly_wb.csv

## Normalizing Units
The measure's normalizing unit is cooling capacity (detail in eTRM). EnergyPlus does not autosize nor output design refrigeration compressor
capacity. However, the maximum capacity available from compressors can be determined by inspecting the capacity performance curves, and hourly outputs are available for cooling demand and cooling delivered to evaporators.

- Compressor capacity available: [Gro_compressor_list.xlsx](Gro_compressor_list.xlsx).
- Cooling demand / capacity utilized: not analyzed.

## Load Shape Workaround
The load shape files (found in CEDARS_LoadShape_Com.zip) are missing the 'NormUnit' column required for uploading to CEDARS. The missing column must be added manually into each of the 3 load shape files (one for each building type). The column must be added in between the 'BldgLoc' and 'Type (Whole Building or End Use)' columns with the column header 'NormUnit' and value 'Cap-Tons' for each line.

