# SWHC008-04 VSD Central Plant

## Unconventional aspects of measure setup

Note that this measure uses condenser water pump minimum flow rate lookup as a
function of cohort (building type/vintage) and climate zone. Based on modelkit
and rakefile capabilities during development, measure developers chose to store
the lookup values in the codes files, although these are based on measure
definition, not code requirements.

See related files:

- commercial measures/SWHC008-04 VSD Central Plant/CW_pump_flowrate.xlsx
- commercial measures/SWHC008-04 VSD Central Plant/pump_min_flow.csv
- codes/T24_2025_new.csv
- codes/T24_2025_new_Htl.csv
- codes/T24_weight_averaged_ex.csv
- codes/T24_weight_averaged_ex_Htl.csv
