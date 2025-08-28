
# Processing steps for this measure

## Step 1 - Run models

```
cd C:\DEER-Prototypes-EnergyPlus
cd "commercial measures/SWHC027-08 Package Terminal ACHP"
modelkit rake run
```

## Step 2 - Gather annual results

```
cd C:\DEER-Prototypes-EnergyPlus
cd "commercial measures/SWHC027-08 Package Terminal ACHP"
python result2.py --queryfile "query_SWHC027_com.txt"
```

Then find `simdata.csv`.

## Step 3 - Gather cooling coil capacity figures

First, generate an output file listing individual cooling coil capacities.

```
cd C:\DEER-Prototypes-EnergyPlus
cd "commercial measures/SWHC027-08 PTAC PTHP"
python ../../scripts/result.py --queryfile query_SWHC027_com.txt
```

Confirm output file `results-sizing-detail.csv` has been created.

Next, aggregate the cooling capacities from only select cooling coils corresponding to main HVAC system found in `coil_list.xlsx`.

```
python result_filtered.py
```

Confirm output file `sizing_agg_filtered.csv` has been created.

Finally, combine the cooling coil capacity figures with annual results. TO DO: fill in this step.

```
python insert_normunits.py ...
```

## Step 4

Use Excel workbook provided in eTRM to compute UEC and UES.

Assumptions:

- Gst modeled as Htl
- Com modeled as OfL

