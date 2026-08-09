# SWHC027 Packaged terminal air conditioner and heat pump - residential models

## Running simulations

This measure uses the "templatized" residential prototypes, which use a
SCHEDULE:FILE object to define schedules like `site_mains_water_temp` and
`DHW_demand_frac_sch`. EnergyPlus does not robustly handle relative file paths
to schedules. To avoid an EnergyPlus simulation error, this measure uses a modified
`rakefile.rb` that defines a global variable `$repository_dir` so that schedule
files are referenced via an absolute file path.

## Processing steps for this measure

```
cd C:\DEER-Prototypes-EnergyPlus
cd "residential measures/SWHC027-09 PTAC PTHP"
modelkit rake run
if there is an issue with warm up for SFm from dummy plenums. Update template file to 'singlefamily_ductonly_SWHC027.imf'

python result2.py --queryfile "query_SWHC027_res.txt"
```

Then find "simdata.csv". Use Excel workbook provided in eTRM to compute UEC and UES.

## Load Shapes

For each vintage subfolder, the `results-summary.csv` file is a prerequisite for load shapes post-processing.
If Modelkit failed to generate the file due to an out-of-memory error, generate the file using the following procedure.

```
cd C:\DEER-Prototypes-EnergyPlus
cd "residential measures/SWHC027-09 PTAC PTHP/SWHC027-09 PTAC PTHP_MFm_Ex"
python ../../../scripts/result.py . --queryfile query.txt
```
Confirm output file `results-sizing-agg.csv` has been created. Rename to `results-summary.csv`
Delete `results-sizing-detail.csv` made by this query file (unused for further steps).

Repeat for each vintage subfolder:

- SWHC027-09 PTAC PTHP_MFm_Ex
- SWHC027-09 PTAC PTHP_MFm_New
- SWHC027-09 PTAC PTHP_SFm_1975
- SWHC027-09 PTAC PTHP_SFm_1985
- SWHC027-09 PTAC PTHP_SFm_New

Then, following the data transformation instructions in the [scripts folder](../../scripts), e.g.:

```
cd C:\DEER-Prototypes-EnergyPlus
cd "scripts/data tranformation"
python MFm.py
python SFm.py
Repeat each for new and existing.
```
If NormUnits column do not generate and/or Bldg HVAC column does not match eTRM, run
```
python clean_loadshapes_SWHC027_res.py
```
