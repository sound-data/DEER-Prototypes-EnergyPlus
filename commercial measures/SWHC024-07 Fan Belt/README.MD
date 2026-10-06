# SWHC024-07 Fan Belt, Commercial

## Measure Description

This folder contains the commercial Fan Belt (Cogged V-Belt) measure setup used for DEER prototype simulation, result scraping, and downstream post-processing.

### Key updates:
- Updated to CZ2025 weather files
- Updated heat sizing factor from 2.5 to 1.25 and cool sizing factor from 2.3 to 1.15 (per ASHRAE 90.1 Appendix G)
- Revised `coil_list.xlsx` to reflect the current list of cooling coils serving main zones this cycle
- Used normalization procedure to extract Cap-Ton capacity from main-zone coils only, using `result_filtered.py`
- Refreshed `DEER_EnergyPlus_Modelkit_Measure_list_FanBelt.xlsx` with current TechIDs

## Cohorts and Case Names

### Cohorts

**Existing**
- `Asm&0&rDXHP&Ex&HV_AirDist__SupFanMtr`
- `ECC&0&rDXHP&Ex&HV_AirDist__SupFanMtr`
- `EPr&0&rDXHP&Ex&HV_AirDist__SupFanMtr`
- `ERC&0&rDXHP&Ex&HV_AirDist__SupFanMtr`
- `ESe&0&rDXHP&Ex&HV_AirDist__SupFanMtr`
- `EUn&0&rDXHP&Ex&HV_AirDist__SupFanMtr`
- `Gro&0&rDXHP&Ex&HV_AirDist__SupFanMtr`
- `Hsp&0&rDXHP&Ex&HV_AirDist__SupFanMtr`
- `Htl&0&rDXHP&Ex&HV_AirDist__SupFanMtr`
- `MBT&0&rDXHP&Ex&HV_AirDist__SupFanMtr`
- `MLI&0&rDXHP&Ex&HV_AirDist__SupFanMtr`
- `Mtl&0&rDXHP&Ex&HV_AirDist__SupFanMtr`
- `Nrs&0&rDXHP&Ex&HV_AirDist__SupFanMtr`
- `OfL&0&rDXHP&Ex&HV_AirDist__SupFanMtr`
- `OfS&0&rDXHP&Ex&HV_AirDist__SupFanMtr`
- `RFF&0&rDXHP&Ex&HV_AirDist__SupFanMtr`
- `RSD&0&rDXHP&Ex&HV_AirDist__SupFanMtr`
- `Rt3&0&rDXHP&Ex&HV_AirDist__SupFanMtr`
- `RtL&0&rDXHP&Ex&HV_AirDist__SupFanMtr`
- `RtS&0&rDXHP&Ex&HV_AirDist__SupFanMtr`
- `SCn&0&rDXHP&Ex&HV_AirDist__SupFanMtr`

**New**
- `Asm&0&rDXHP&New&HV_AirDist__SupFanMtr`
- `ECC&0&rDXHP&New&HV_AirDist__SupFanMtr`
- `EPr&0&rDXHP&New&HV_AirDist__SupFanMtr`
- `ERC&0&rDXHP&New&HV_AirDist__SupFanMtr`
- `ESe&0&rDXHP&New&HV_AirDist__SupFanMtr`
- `EUn&0&rDXHP&New&HV_AirDist__SupFanMtr`
- `Gro&0&rDXHP&New&HV_AirDist__SupFanMtr`
- `Hsp&0&rDXHP&New&HV_AirDist__SupFanMtr`
- `Htl&0&rDXHP&New&HV_AirDist__SupFanMtr`
- `MBT&0&rDXHP&New&HV_AirDist__SupFanMtr`
- `MLI&0&rDXHP&New&HV_AirDist__SupFanMtr`
- `Mtl&0&rDXHP&New&HV_AirDist__SupFanMtr`
- `Nrs&0&rDXHP&New&HV_AirDist__SupFanMtr`
- `OfL&0&rDXHP&New&HV_AirDist__SupFanMtr`
- `OfS&0&rDXHP&New&HV_AirDist__SupFanMtr`
- `RFF&0&rDXHP&New&HV_AirDist__SupFanMtr`
- `RSD&0&rDXHP&New&HV_AirDist__SupFanMtr`
- `Rt3&0&rDXHP&New&HV_AirDist__SupFanMtr`
- `RtL&0&rDXHP&New&HV_AirDist__SupFanMtr`
- `RtS&0&rDXHP&New&HV_AirDist__SupFanMtr`
- `SCn&0&rDXHP&New&HV_AirDist__SupFanMtr`

### Case Names (TechIDs)

| Case Name (TechID) | Role | `main_fan_eff` |
|--------------------|------|----------------|
| `NE-HVAC-FanBelt-VBelt-Std` | Baseline | 0.55 |
| `NE-HVAC-FanBelt-CoggedVBelt-Msr` | Measure | 0.561 |
| `NE-HVAC-FanBelt-SynchVBelt-Msr` | Measure | 0.5775 |

All cases use `:heat_sizing_factor = 1.25`, `:cool_sizing_factor = 1.15`.

## Post-Processing

To collect normalizing units from results, additional files were introduced to collect and sum relevant coil sizes.

Run the following from the measure folder root after simulations complete:

```bash
python result2.py -q query_Captons.txt     # → simdata.csv
python result.py . -q query_default.txt    # → results-sizing-detail.csv
python result_filtered.py .                # → sizing_agg_filtered.csv
```
coil_list.xlsx tabulates the cooling coils relevant to the measure, created manually by inspection. 
- Run Com.py from scripts/data transformation/
- Review generated files: current_msr_mat.csv, sim_annual.csv, sim_hourly_eu.csv, sim_hourly_wb.csv
