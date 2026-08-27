# SWHC045 Heat Pump HVAC Fuel Substitution
Prepared by Solaris Technical, Yasemin Agi - 2026-07-23
This document describes the steps necessary to reproduce simulations and model outputs for this measure.

## Step 1
```
cd C:/DEER-Prototypes-EnergyPlus
cd C:/.../SWHC045-07 Heat Pump HVAC Fuel Sub/SWHC045-07 Heat Pump HVAC Fuel Sub_DMo_Ex
modelkit rake run
python ../../../scripts/result.py . --queryfile query.txt

Confirm script generated 'results-sizing-agg.csv' and 'results-sizing-detail.csv'.
Rename 'results-sizing-agg.csv' to 'results-summary.csv' for use in load shapes later.
```
Repeat for:
SWHC045-07 Heat Pump HVAC Fuel Sub_MFm_Ex
SWHC045-07 Heat Pump HVAC Fuel Sub_SFm_1975
SWHC045-07 Heat Pump HVAC Fuel Sub_SFm_1985

## Step 2
cd C:/.../SWHC045-07 Heat Pump HVAC Fuel Sub
python result2.py --queryfile "query.txt"
```
Confirm script generated 'simdata.csv'.

## Step 3 
```
cd C:\DEER-Prototypes-EnergyPlus
cd "scripts/data transformation"
```
Paste 'DEER_EnergyPlus_Modelkit_Measure_list_SWHC045.xlsx' into 'data transformation' folder.
Modify DMo.py, MFm.py, SFm.py to correct measure.
```
python DMo.py
python MFm.py
python SFm.py
```