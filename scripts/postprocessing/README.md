# Repeatable Measure Post-Processing & Deliverables Toolkit

Measure-agnostic scripts for turning finished ModelKit simulations into the
review files and eTRM deliverable packages. Proven on SWSV014 (residential
LRM); intended next for the SFC/OFC measures. The SWSV014-specific walkthrough
is at `../data transformation/README_CEDARS_LRM.md`.

## The pipeline at a glance

    modelkit rake (per study, from a subst'd short drive)
        |- results-summary.csv, results-profile-elec/gas.csv, runs/
        |
        |-- TRACK A (per-run review files)
        |     result2.py <study> -c / -w        -> simdata.csv / simdata.sqlite
        |     weight_sfm_simdata.py             -> simdata_weighted.csv (SFm story weighting)
        |     passthrough_weight.py             -> simdata_weighted.csv (single-story types)
        |     normalize_simdata.py              -> simdata_norm.csv (per-ft2)
        |
        |-- TRACK B (DEER impacts + CEDARS)
              DMo.py / MFm.py / SFm.py / Com.py -> sim(sfm)_annual, sim(sfm)_hourly_wb,
                                                   current_msr_mat, CEDARS_LoadShape_*.zip
              (stash outputs per building type - the scripts overwrite shared names)
              split_cedars_by_cz.py             -> per-CZ CEDARS csvs, plain decimals
              (PostgreSQL R1-R4/P1-P8 for meas_impacts - see scripts/energy savings/)

    build_etrm_packages.py                      -> the three dated eTRM zips

## Scripts in this folder

| Script | Purpose |
|---|---|
| `weight_sfm_simdata.py` | SFm story weighting: `story1*(2-numstor) + story2*(numstor-1)` per CZ, weights = official NumStor table (1975: CZ01-09, 1985: CZ10-16) |
| `passthrough_weight.py` | Single-story building types (DMo/MFm): emits the same weighted-file layout at weight 1.0 for uniform deliverables |
| `normalize_simdata.py` | Divides energy + DEER peak by Net Conditioned Building Area (query.txt must extract "Conditioned Area") |
| `aggregate_profiles.py` | Memory-safe replacement for the rakefile's hourly profile aggregation (32-bit Ruby OOMs on large studies); trims design-day rows |
| `build_etrm_packages.py` | Builds the three dated eTRM zips for any measure (see `--help`) |

Also: `../data transformation/split_cedars_by_cz.py` (per-CZ CEDARS splitter,
plain-decimal rewrite).

## Invariants to verify before sending anything

1. Rake logs contain no "Undefined parameter" lines (except the unused
   `n_floor`) - anything else means a template is silently ignoring an input.
2. Every run has a non-empty instance-out.sql (a 0-byte sql = the Windows
   260-char path limit; run from `subst X: <repo>` instead).
3. simdata row count = studies' full CZ x TechID x story grid; weighting
   reports zero unpaired rows.
4. Track B outputs are non-trivial in size (header-only sim_annual = the
   workbook's Common_*TechID columns don't match the simulated TechIDs).
5. CEDARS: every TechID x CZ shape sums to 1.0; per-CZ csv = 175,201 rows
   incl. header (for a 20-TechID measure); values in plain decimals.

## eTRM deliverables folder format

    eTRM deliverables/
      <ID> Energy Models Inputs YYYY-MM-DD.zip
      <ID> Energy Models Outputs YYYY-MM-DD.zip
      <ID> Postprocessed Outputs YYYY-MM-DD.zip
      <ID> CEDARS 8760s by CZ YYYY-MM-DD/
        CEDARS_LoadShape_<BT>.zip        full per-building-type deliverable
        CEDARS_LoadShape_<BT>-2/         folder of 16 per-CZ csvs
        CEDARS_LoadShape_<BT>-2.zip      that folder zipped

Date-stamp everything; when a package is superseded, delete the stale one
from the repo folder AND OneDrive so nobody can download an old version.

## Adapting to a new measure (SFC/OFC checklist)

1. Cases CSVs: use the final TechIDs as case names; keep names short enough
   for the path limit (test the longest full path + 40 chars < 260).
2. Workbook: add the measure's rows; `Common_*TechID` = `*TechID` when case
   names are already final.
3. Cohorts: wire any hard-sizing lookups; confirm the referenced rows exist
   in the codes CSVs; then check rake logs per invariant 1.
4. query.txt per study: include the "Net Conditioned Building Area" line if
   floor-area normalization is wanted.
5. Commercial measures use Com.py and the commercial PostgreSQL scripts
   instead of the residential ones; there is no story weighting.
