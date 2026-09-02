# SWHC050-09 Ductless Heat Pump, Residential

## Measure Description

This folder contains the residential Ductless Heat Pump measure setup used for DEER prototype simulation, result scraping, and downstream post-processing.

### Key Changes in This Revision
- Update to CZ2025 weather files
- Switching model setup to align with templatized DEER residential prototypes
- Consolidated some measure offering tiers based on market availability
- Renamed techIDs for clarity and consistency
- Updated HP templates to include CCH and defrost proposed parameters consistent with Update residential crankcase and defrost heater parameters sound-data/DEER-Prototypes-EnergyPlus#179.

## Cohorts and Case Names

Tables below show the origin of TechIDs present in this folder.

### Cohorts - Measure Applicability and Prototype

| BldgType-BldgVint | Cohort | Prototype root | Introduced |
|---|---|---|---|
| DMo | `DMo&0&rDXHP&Ex&dxHP_equip` | `DMo-combi/templates/root.pxt` | SWHC050-09 |
| DMo | `DMo&0&rDXHP&New&dxHP_equip` | `DMo-combi-New/templates/root.pxt` | SWHC050-09 |
| MFm_Ex | `MFm&0&rDXHP&Ex&dxHP_equip` | `MFm-1985-combi/templates/root.pxt` | SWHC050-09 |
| MFm_New | `MFm&0&rDXHP&New&dxHP_equip` | `MFm-New-combi/templates/root.pxt` | SWHC050-09 |
| SFm_1975 | `SFm&1&rDXHP&Ex&dxHP_equip` | `SFm-1 Story-1975-combi/templates/root.pxt` | SWHC050-09 |
| SFm_1975 | `SFm&2&rDXHP&Ex&dxHP_equip` | `SFm-2 Story-1975-combi/templates/root.pxt` | SWHC050-09 |
| SFm_1985 | `SFm&1&rDXHP&Ex&dxHP_equip` | `SFm-1 Story-1985-combi/templates/root.pxt` | SWHC050-09 |
| SFm_1985 | `SFm&2&rDXHP&Ex&dxHP_equip` | `SFm-2 Story-1985-combi/templates/root.pxt` | SWHC050-09 |
| SFm_New | `SFm&1&rDXHP&New&dxHP_equip` | `SFm-1 Story-New-combi/templates/root.pxt` | SWHC050-09 |
| SFm_New | `SFm&2&rDXHP&New&dxHP_equip` | `SFm-2 Story-New-combi/templates/root.pxt` | SWHC050-09 |

### Case Names (TechIDs)

| Case Name (TechID) | Type | SEER2 | HSPF2 | Applicable Building Types | Vintages |
|---|---|---|---|---|---|
| `Pre-RE-HV-RoomAC-9.0E-ERheat` | Room AC baseline | — | — | DMo, SFm, MFm | Ex, New |
| `Std-RE-HV-RoomAC-9.8E-ERheat` | Room AC baseline | — | — | DMo, SFm, MFm | Ex, New |
| `RE-dxHP_equip-spltSEER-12.5-SEER2-6.4-HSPF2` | Ductless HP | 12.5 | 6.4 | DMo, SFm, MFm | Ex, New |
| `RE-dxHP_equip-spltSEER-14.3-SEER2-7.5-HSPF2` | Ductless HP | 14.3 | 7.5 | DMo, SFm, MFm | Ex, New |
| `RE-dxHP_equip-spltSEER-16.0-SEER2-8.1-HSPF2` | Ductless HP | 16.0 | 8.1 | DMo, SFm, MFm | Ex, New |
| `RE-dxHP_equip-spltSEER-18.7-SEER2-8.7-HSPF2` | Ductless HP | 18.7 | 8.7 | DMo, SFm, MFm | Ex, New |
| `RE-dxHP_equip-spltSEER-20.5-SEER2-9.1-HSPF2` | Ductless HP | 20.5 | 9.1 | DMo, SFm, MFm | Ex, New |

## Query File for Normalizing Units

The file `query_swhc050.txt` includes queries for cooling and heating capacity
for the models generated in this folder. After running simulations:

```bash
cd "residential measures/SWHC050-09"
python result2.py -q query_swhc050.txt
```
## Data Transformation and Post-Processing
Measure Working List: DEER_EnergyPlus_Modelkit_Measure_list_working_swhc050.xlsx

## Post-Processing Steps
- Run simulations and confirm result files
- Scrape outputs with scripts/result2.py using query_swhc050.txt
- Run transformation scripts from scripts/data transformation/
- Review generated files: current_msr_mat.csv, sim_annual.csv, sim_hourly_eu.csv, sim_hourly_wb.csv
