# SWHC062 model description

Applies a fan fault corrective measure to the follow building types and zones:

- Asm/office_large
- Asm/auditorium
- ECC/classroom_shop
- ECC/classroom_class
- ECC/dining_fast
- ECC/kitchen
- ECC/computer
- ECC/office_large
- EPr/classroom_class
- EPr/dining_fast
- EPr/gym
- EPr/kitchen
- ERC/classroom_class
- ESe/classroom_class
- ESe/gym
- ESe/kitchen
- ESe/computer
- ESe/dining_fast
- EUn/classroom_class
- EUn/dining_fast
- EUn/industrial_low
- EUn/kitchen
- EUn/computer
- EUn/office_large
- EUn/guestroom
- Gro/grocery
- Gro/industrial_high
- Gro/office_large
- Htl/dining_fine
- Htl/kitchen
- Htl/laundry
- Htl/lobby
- Htl/office_large
- Htl/guestroom
- MBT/computer
- MBT/conference
- MBT/dining_fast
- MBT/kitchen
- MBT/lab
- MBT/office_large
- MLI/storage_warehouse
- MLI/industrial_low
- OfL/lobby
- OfL/mech
- OfL/office_open
- OfL/office_large
- OfS/office_large
- RFF/dining_fast
- RFF/kitchen
- RFF/lobby
- RFF/restroom
- RSD/dining_fast
- RSD/kitchen
- RSD/lobby
- RSD/restroom
- Rt3/retail_sales
- RtL/auto
- RtL/kitchen
- RtL/office_large
- RtL/retail_sales
- RtL/storage_warehouse
- RtS/retail_sales
- RtS/storage_warehouse
- SCn/storage_warehouse

Disclaimer: this list does not imply measure eligibility. Refer to eTRM for eligibility and list of building types simulated.


## Base conditions and offerings

There are five base conditions:

- **Base 1**: economizer, variable outdoor airflow, continuous 24x7 fan operation (offerings A-D)
- **Base 2**: no economizer, no outdoor airflow, continuous 24x7 fan operation (offerings E-H)
- **Base 3**: no economizer, no outdoor airflow, intermittent fan operation (offerings I-K)
- **Base 4**: no economizer, fixed outdoor airflow, continuous 24x7 fan operation (offerings M-P)
- **Base 5**: no economizer, fixed outdoor airflow, intermittent fan operation (offerings Q-S)

The Base 3 and Base 5 measure cases (M3/M5 `-Measure` rows in the cases CSVs)
model OFC fan-off-delay savings directly, with increased cooling and heat-pump
COP and gas furnace efficiency. Base 1, 2, and 4 measures are calculated by
post-processing continuous-fan off-hour energy from the base simulations
(`scripts/process_hourly_data_multi_measure.py`).

## Running the simulations

Two studies, both Existing vintage: `..._Ex` (15 building types) and
`..._Htl_Ex` (Hotel, run separately). From each study folder run
`modelkit rake` (default task: compose -> run -> harvest). Key configuration:

- **Calendar**: Thursday start day with weather-file holidays, DST, and the
  weekend-holiday rule enabled (`templates/energyplus/templates/general.pxt`),
  reproducing the DEER 2009-basis calendar per the CEC ACM Reference Manual.
  Holidays come from `holidays.pxt` (`RunPeriodControl:SpecialDays`), inserted
  in every commercial prototype root.
- **Weather**: CZ2025 files (`weather/*_CZ2025.epw`), wired via each study's
  `climates.csv`. `_Ex` uses codes file `T24_weight_averaged_ex.csv`;
  `_Htl_Ex` uses `T24_weight_averaged_ex_Htl.csv`.
- Rake warnings `Undefined parameter (zone_area / demand_controlled_vent)`
  are benign (identical on the main branch). The harvest's
  `results-profile-gas.csv` is all zeros (EnergyPlus 22.2 renamed the meter
  to `NaturalGas:Facility`); annual gas is read from each run's SQL instead.

## Post-processing pipeline

QC review files (this folder):

1. `scripts/process_summary_data_multi_measure.py` -> `Summary-Report.csv`
2. `scripts/process_hourly_data_multi_measure.py` -> `hourly_results/`
3. `scripts/process_deer_peak_sql.py` -> `Deer Peak.csv` (CZ2025 DEER peak
   days, aligned with main's `scripts/energy savings/commercial/peakperspec.csv`)

DEER tables and CEDARS load shapes (`scripts/data transformation/`):

4. `run_com_by_bldgtype.py` runs `Com_SWHC062.py` once per building-type
   workbook in `DEER_EnergyPlus_Modelkit_Measure_list_working_dir/` (16
   workbooks; `COM_WORKBOOK` selects the workbook, `COM_BT_FILTER` limits the
   run scan), stashing outputs under `outputs_by_bldgtype/<BldgType>/`.
5. `make_mfmcmn_dupes.py` duplicates OfS as MFmCmn (multi-family common =
   small office, BldgType relabeled) and assembles the combined
   `CEDARS_LoadShape_Com.zip` (17 building types).
6. `fix_cedars_techid.py` maps path TechIDs (`M1-cPTAC-Base`) to real measure
   TechIDs; `package_8760_for_pge.py` builds the per-building-type
   `SWHC062_8760_Load_Shapes_<BT>.zip` files (16 per-CZ CSVs each).

Energy Savings workbook (`postprocess/`):

7. `make_deer_peak_electric.py` -> `Deer Peak - Electric.csv`, then
   `build_all_files.py` (-all files with MFmCmn dupes),
   `make_measure_off_hour.py` (off-hour merge from `hourly_results/`), and
   `com_energy_savings_calc.py` (fills the Base/Measure/Pk tabs of the
   savings workbook template; recalculate in Excel before use).

eTRM deliverable packages: `scripts/postprocessing/build_etrm_swhc062.py`
(date-stamped Inputs / per-building-type Outputs / Postprocessed / CEDARS /
8760 packages into `eTRM deliverables/`).

## Run history (2026-08)

- 2026-08-19/20: full re-simulation of both studies on the corrected
  Thursday/2009-basis calendar (replacing 2017/Sunday-start runs).
- 2026-08-21: M3/M5 measure-case update (higher cooling/HP COP, fan
  efficiency, furnace efficiency); `_Ex` re-ran the 1,920 affected runs.
- 2026-08-23: `_Htl_Ex` re-ran its 128 affected runs; all QC outputs and
  deliverables regenerated from the updated 10,240-run set.
