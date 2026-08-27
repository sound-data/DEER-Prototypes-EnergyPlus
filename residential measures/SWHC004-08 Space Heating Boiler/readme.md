Sizing information

For this measure, additional query files are provided to document boiler auto-sizing results.
To compile the results, use the `result.py` and `insert_normunit.py` scripts after simulation, as below.

Notes
* Separate output files are produced for HotWater and Steam boilers, based on the corresponding component sizing output variable.
* A multiplier is used to convert from outputs per capacity (W) to outputs per capacity (kBtuh):

```
Outputs / capacity (kBtuh) = (outputs / capacity (W)) * (W / kBtuh)
Sizing_multiplier = (W / kBtuh) = 293.0710701832112
```

```
cd C:/DEER-Prototypes-EnergyPlus
cd "residential measures/SWHC004-07 Space Heating Boiler/SWHC004-07 Space Heating Boiler_MFm_Ex"
modelkit rake
python "../../../scripts/data transformation/MFm.py"
copy "../../../scripts/data transformation/sim_annual.csv" .
python "../../../scripts/result.py" . --queryfile "query_boiler_sizing.txt" --detailfile results-sizing-detail.csv --aggfile results-sizing-agg.csv
python "../../../scripts/data transformation/insert_normunits.py" results-sizing-agg.csv sim_annual.csv results-per-dwelling-hwboiler.csv sim_annual_withunits-hwboiler.csv "Boiler:HotWater Design Size Nominal Capacity (W)" "CapOut-kBtuh" 293.0710701832112 "HW Boiler Space Heating"
python "../../../scripts/data transformation/insert_normunits.py" results-sizing-agg.csv sim_annual.csv results-per-dwelling-steamboiler.csv sim_annual_withunits-steamboiler.csv "Boiler:Steam Design Size Nominal Capacity (W)" "CapOut-kBtuh" 293.0710701832112 "Steam Boiler Space Heating"
```

```
cd C:/DEER-Prototypes-EnergyPlus
cd "residential measures/SWHC004-07 Space Heating Boiler/SWHC004-07 Space Heating Boiler_MFm_New"
modelkit rake
python "../../../scripts/data transformation/MFm.py"
copy "../../../scripts/data transformation/sim_annual.csv" .
python "../../../scripts/result.py" . --queryfile "query_boiler_sizing.txt" --detailfile results-sizing-detail.csv --aggfile results-sizing-agg.csv
python "../../../scripts/data transformation/insert_normunits.py" results-sizing-agg.csv sim_annual.csv results-per-dwelling-hwboiler.csv sim_annual_withunits-hwboiler.csv "Boiler:HotWater Design Size Nominal Capacity (W)" "CapOut-kBtuh" 293.0710701832112 "HW Boiler Space Heating"
python "../../../scripts/data transformation/insert_normunits.py" results-sizing-agg.csv sim_annual.csv results-per-dwelling-steamboiler.csv sim_annual_withunits-steamboiler.csv "Boiler:Steam Design Size Nominal Capacity (W)" "CapOut-kBtuh" 293.0710701832112 "Steam Boiler Space Heating"
```
