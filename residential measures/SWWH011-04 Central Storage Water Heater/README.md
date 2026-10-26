# SWWH011-04 Central Storage Water Heater, Multifamily

This document describes the steps necessary to reproduce simulations and model outputs for this measure.

Prepared by Solaris Technical, Yasemin Agi - 2026-10-26

# Running simulations
``
cd MEASURE FOLDER\residential measures\SWWH011-04 Central Storage Water Heater\SWWH011 Central Storage Water Heater_MFm_Ex
modelkit rake run

cd MEASURE FOLDER\residential measures\SWWH011-04 Central Storage Water Heater\SWWH011 Central Storage Water Heater_MFm_New
modelkit rake run
``
# Post-processing
Run post-processing script.
Note: query.txt in the measure folder includes an additional parameter from the default query file for normalization.
ComponentSizingSummary/Entire Facility/WaterHeater:Stratified/Maximum Heater Capacity/CENTRAL DHW
```
cd MEASURE FOLDER\residential measures\SWWH011-04 Central Storage Water Heater
python result3.py
```
Verify simdata.sqlite was created.

Export simdata to excel for energy savings calculations.
```
python export_simdata.py
```
Verfiy simdata_export.xlsx was created.

# Load shapes (not required for this measure)
If needed, run result.py in each sub folder (SWWH011 Central Storage Water Heater_MFm_Ex, SWWH011 Central Storage Water Heater_MFm_New)
``
python result.py
``
Verify results-sizing-agg.csv was created. Rename to results-summary.csv

Run measure-specific load shape scripts.
``
cd MEASURE FOLDER\residential measures\SWWH011-04 Central Storage Water Heater
python MFm_SWWH011_Ex.py
python MFm_SWWH011_Ex.py
``