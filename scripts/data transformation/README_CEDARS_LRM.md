# Producing the SWSV014 CEDARS 8760 Load Shape Deliverables

End-to-end procedure for the SWSV014 Lifecycle Refrigerant Management
(Residential) measure. Written 2026-08-17 after the hard-sized re-runs.

## 0. Prerequisites

* ModelKit Caboodle, EnergyPlus 9.5, Python 3.12 with pandas/openpyxl.
* Map a short drive before running any simulations (two of the case names
  otherwise exceed the Windows 260-character path limit inside EnergyPlus's
  working folder, and those sims die with "The SQLite database failed to
  open"):

      subst X: C:\DEER-Prototypes-EnergyPlus

* The measure-list workbook (`DEER_EnergyPlus_Modelkit_Measure_list_working.xlsx`,
  sheet `Measure_list`) must have `Common_PreTechID` / `Common_StdTechID` /
  `Common_MeasTechID` equal to the corresponding final TechID columns for the
  LRM rows. The cases CSVs use the final `RB-...` TechIDs as case names, so
  the sims already emit final IDs; if the Common columns hold anything else,
  the transformation scripts silently produce EMPTY outputs.

## 1. Run the simulations

For each study folder under
`residential measures/SWSV014-06-1 LRM/`
(`_DMo_Ex`, `_MFm_Ex`, `_SFm_1975`, `_SFm_1985`):

    cd "X:\residential measures\SWSV014-06-1 LRM\<study>"
    modelkit rake

Notes:
* ModelKit only re-runs cases whose worksheet parameters changed. After a
  **template** (.pxt) change you must delete the study's `runs/` folder and
  `results-*.csv` files to force full recomposition.
* After any large rake, grep the console output for "Undefined parameter" —
  anything other than `n_floor` (unused) means a template is silently
  ignoring an input and the results are wrong.
* SFm existing stock is two studies by DEER convention: 1975 vintage covers
  CZ01-CZ09, 1985 vintage covers CZ10-CZ16. SFm runs 1-story and 2-story.

## 2. Extract per-run results (simdata)

    cd "<study folder>"   # must run FROM the study folder (query.txt is resolved from the cwd)
    python <repo>\scripts\result2.py . -c    # simdata.csv
    python <repo>\scripts\result2.py . -w    # simdata.sqlite

Then story-weight and normalize (scripts in the sibling
DEER-Prototypes-EnergyPlus repo copy under scripts/):

    python weight_sfm_simdata.py simdata.csv simdata_weighted.csv 1975|1985   # SFm only
    python passthrough_weight.py simdata.csv simdata_weighted.csv            # DMo/MFm
    python normalize_simdata.py simdata_weighted.csv simdata_norm.csv

## 3. Generate the CEDARS load shapes (8760s)

Run per building type from `scripts/data transformation/` (each overwrites
the shared output names — copy outputs aside between runs):

    python DMo.py     -> current_msr_mat.csv, sim_annual.csv, sim_hourly_wb.csv,
                         CEDARS_LoadShape_DMo.zip, CEDARS_ls_annual_loads_DMo.csv
    python MFm.py     -> same names, MFm content
    python SFm.py     -> current_msr_mat.csv, sfm_annual.csv, sfm_hourly_wb.csv,
                         CEDARS_LoadShape_SFm.zip, CEDARS_ls_annual_loads_SFm.csv

CEDARS csv schema (12 columns): Sector, BldgType, BldgVint, BldgHVAC,
BldgLoc, Type (Whole Building or End Use), Source Year, TechGroup, TechType,
TechID, Hour of Year, UECproportion. One row per hour: 8,760 rows per
TechID x CZ. `UECproportion` is dimensionless (each hour / that shape's
annual total) and every shape sums to exactly 1.0.

## 4. Split by climate zone for review (split_cedars_by_cz.py)

    python split_cedars_by_cz.py

* Rewrites every UECproportion in plain fixed-point notation. pandas writes
  values below 1e-4 in scientific notation ("8.3e-05"), and some Excel
  configurations import those as TEXT — SUM() then silently skips them
  (that is how a column that truly sums to 20 can appear to sum to 12.7).
* Emits, per building type: the full csv (zipped) and 16 per-CZ csvs
  (175,200 data rows each = 20 TechIDs x 8,760 h), plus zipped copies.

## 5. Deliverable folder format (eTRM)

    eTRM deliverables/
      SWSV014 Energy Models Inputs YYYY-MM-DD.zip       (repo minus runs/other measures + README)
      SWSV014 Energy Models Outputs YYYY-MM-DD.zip      (runs: instance.idf/-out.err/-tbl.htm/-out.sql only)
      SWSV014 Postprocessed Outputs YYYY-MM-DD.zip      (results, simdata, 8760s, CEDARS, workbooks)
      SWSV014 CEDARS 8760s by CZ YYYY-MM-DD/
        CEDARS_LoadShape_DMo.zip           <- full per-type deliverable
        CEDARS_LoadShape_DMo-2/            <- folder of 16 per-CZ csvs
        CEDARS_LoadShape_DMo-2.zip         <- that folder zipped
        (same trio for MFm and SFm)

## 6. Verification checklist (run before sending anything)

* Per-CZ csv: 175,201 rows including header.
* `=SUM(L:L)` = 20 (20 TechIDs x 1.0). Any single TechID (SUMIF on column J,
  or a pivot of TechID vs Sum of UECproportion) = 1.0.
* If a sum comes up short: cells imported as text (select column L ->
  Data -> Text to Columns -> Finish), or the file was opened from inside a
  zip (extract first — zip preview opens a Temp copy that goes stale).
* No "Undefined parameter" (except n_floor) in rake logs; no TechID
  containing `dxAC_equip` paired with BldgHVAC `rDXHP` anywhere.
