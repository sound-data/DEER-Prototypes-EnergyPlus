
# Processing steps for this measure

## Step 1 - Run models

```
cd C:\DEER-Prototypes-EnergyPlus
cd "commercial measures/SWHC027-09 Package Terminal ACHP"
modelkit rake run
```

## Step 2 - Gather annual results

```
cd C:\DEER-Prototypes-EnergyPlus
cd "commercial measures/SWHC027-09 Package Terminal ACHP"
python result2.py --queryfile "query_SWHC027_com.txt"
```

Then find `simdata.csv`.

## Step 3 - Gather cooling coil capacity figures

First, create the `results-summary.csv` which will be used for load shapes post-processing.
```
cd C:\DEER-Prototypes-EnergyPlus
cd "commercial measures/SWHC027-09 Package Terminal ACHP/SWHC027-09 Package Terminal ACHP_Ex"
python ../../../scripts/result.py . --queryfile query.txt
```
Confirm output file `results-sizing-agg.csv` has been created. Rename to `results-summary.csv`
Delete `results-sizing-detail.csv` made by this query file.

Then, generate an output file listing individual cooling coil capacities.

```
cd C:\DEER-Prototypes-EnergyPlus
cd "commercial measures/SWHC027-09 Package Terminal ACHP/SWHC027-09 Package Terminal ACHP_Ex"
python ../../../scripts/result.py . --queryfile query_SWHC027_com.txt
```

Confirm output file `results-sizing-detail.csv` has been created.

Next, aggregate the cooling capacities from only select cooling coils corresponding to main HVAC system found in `coil_list.xlsx`.

```
python result_filtered.py
```

Confirm output file `sizing_agg_filtered.csv` has been created.

Repeat the above step 3 for the following folders:
- SWHC027-09 Package Terminal ACHP_Htl_Ex
- SWHC027-09 Package Terminal ACHP_Htl_New
- SWHC027-09 Package Terminal ACHP_New

## Step 4

Use Excel workbook provided in eTRM to combine the cooling coil capacity
figures with annual results via lookup tables, then compute UEC and UES.

Assumptions:

- Gst modeled as Htl
- Com modeled as OfL

## Step 5 - Load Shapes

```
cd C:\DEER-Prototypes-EnergyPlus
cd "scripts/data tranformation"
python Com.py
```