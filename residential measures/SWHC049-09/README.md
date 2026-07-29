# SWHC049-09 Ducted SEER Rated Heat Pump, Residential


## Measure Description

This folder contains the residential Ducted SEER Rated Heat Pump measure setup used for DEER prototype simulation, result scraping, and downstream post-processing.

### Key Changes in This Revision
- Update to CZ2025 weather files
- Switching model setup to align with templatized DEER residential prototypes
- **Retired packaged AC offerings** — this measure now includes heat pump equipment only
- Removed SEER2>=15.2 measure offering, merged SEER2>=16.9 offering with SEER2>=16.0 offering
- Renamed techIDs for clarity and consistency
- Updated HP templates to include CCH and defrost proposed parameters consistent with Update residential crankcase and defrost heater parameters sound-data/DEER-Prototypes-EnergyPlus#179.

## Cohorts and Case Names

### Building Types
- DMo (Mobile Home) — Existing, New
- MFm_Ex (Multi-family Existing) — 1985 and older
- MFm_New (Multi-family New) — New construction
- SFm_1975 (Single-family 1975) — Existing, 1-story and 2-story
- SFm_1985 (Single-family 1985) — Existing, 1-story and 2-story
- SFm_New (Single-family New) — New construction, 1-story and 2-story

### Case Names (TechIDs)

| Case Name (TechID) | SEER2 Rating | HSPF2 Rating |
|-------------------|--------------|--------------|
| RE-dxHP_eq-pkgSEER-12.5-SEER2-6.4-HSPF2 | 12.5 | 6.4 |
| RE-dxHP_eq-pkgSEER-14.3-SEER2-7.5-HSPF2 | 14.3 | 7.5 |
| RE-dxHP_eq-pkgSEER-15.2-SEER2-7.7-HSPF2 | 15.2 | 7.7 |
| RE-dxHP_eq-pkgSEER-16.0-SEER2-8.0-HSPF2 | 16.0 | 8.0 |
| RE-dxHP_eq-pkgSEER-17.8-SEER2-8.1-HSPF2 | 17.8 | 8.1 |
| RE-dxHP_eq-pkgSEER-18.7-SEER2-8.5-HSPF2 | 18.7 | 8.5 |
| RE-dxHP_eq-pkgSEER-19.6-SEER2-8.9-HSPF2 | 19.6 | 8.9 |

## Query File for Normalizing Units

The file `query_swhc049.txt` includes queries for cooling and heating capacity. After running simulations:

```bash
cd "residential measures/SWHC049-09"
python result2.py -q query_swhc049.txt
```
## Data Transformation and Post-Processing
Measure Working List: DEER_EnergyPlus_Modelkit_Measure_list_working_SWHC049-09.xlsx

## Post-Processing Steps
- Run simulations and confirm result files
- Scrape outputs with scripts/result2.py using query_swhc049.txt
- Run transformation scripts from scripts/data transformation/
- Review generated files: current_msr_mat.csv, sim_annual.csv, sim_hourly_eu.csv, sim_hourly_wb.csv

