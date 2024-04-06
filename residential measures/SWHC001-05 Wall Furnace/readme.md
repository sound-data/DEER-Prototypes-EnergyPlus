Processing steps for this measure

```
cd C:\DEER-Prototypes-EnergyPlus
cd "residential measures/SWHC001-05 Wall Furnace/SWHC001-05 Wall Furnace_DMo"
modelkit rake
python "../../../scripts/data transformation/DMo.py"
copy "../../../scripts/data transformation/sim_annual.csv" .
python "../../../scripts/result.py" . --queryfile "query_Wall Furnace.txt"
python "../../../scripts/data transformation/insert_normunits.py" results-sizing-agg.csv sim_annual.csv results-per-dwelling.csv sim_annual_withunits.csv "Coil:Heating:Fuel Design Size Nominal Capacity (W)" "CapOut-kBtuh" 0.2930710701832112 "Wall Furnace"
```

```
cd C:\DEER-Prototypes-EnergyPlus
cd "residential measures/SWHC001-05 Wall Furnace/SWHC001-05 Wall Furnace_MFm_Ex"
modelkit rake
python "../../../scripts/data transformation/MFm.py"
copy "../../../scripts/data transformation/sim_annual.csv" .
python "../../../scripts/result.py" . --queryfile "query_Wall Furnace.txt"
python "../../../scripts/data transformation/insert_normunits.py" results-sizing-agg.csv sim_annual.csv results-per-dwelling.csv sim_annual_withunits.csv "Coil:Heating:Fuel Design Size Nominal Capacity (W)" "CapOut-kBtuh" 0.2930710701832112 "Wall Furnace"
```

```
cd C:\DEER-Prototypes-EnergyPlus
cd "residential measures/SWHC001-05 Wall Furnace/SWHC001-05 Wall Furnace_SFm_1975"
modelkit rake
python "../../../scripts/data transformation/SFm.py"
copy "../../../scripts/data transformation/sfm_annual.csv" .
python "../../../scripts/result.py" . --queryfile "query_Wall Furnace.txt"
python "../../../scripts/data transformation/insert_normunits.py" results-sizing-agg.csv sfm_annual.csv results-per-dwelling.csv sfm_annual_withunits.csv "Coil:Heating:Fuel Design Size Nominal Capacity (W)" "CapOut-kBtuh" 0.2930710701832112 "Wall Furnace"
```

```
cd C:\DEER-Prototypes-EnergyPlus
cd "residential measures/SWHC001-05 Wall Furnace/SWHC001-05 Wall Furnace_SFm_1985"
modelkit rake
python "../../../scripts/data transformation/SFm.py"
cp "../../../scripts/data transformation/sim_annual.csv" .
python "../../../scripts/result.py" . --queryfile "query_Wall Furnace.txt"
python "../../../scripts/data transformation/insert_normunits.py" results-sizing-agg.csv sfm_annual.csv results-per-dwelling.csv sfm_annual_withunits.csv "Coil:Heating:Fuel Design Size Nominal Capacity (W)" "CapOut-kBtuh" 0.2930710701832112 "Wall Furnace"
```

