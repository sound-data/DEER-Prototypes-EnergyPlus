# SWHC045 Heat Pump HVAC Fuel Substitution

This document describes the steps necessary to reproduce simulations and model outputs for this measure.

Prepared by Solaris Technical, Behzad S. Rizi - 2025-10-17

## Known Issue: `** Severe ** Invalid String Position` Error

It is necessary to apply a workaround to resolve an EnergyPlus implementation bug.
When running EnergyPlus simulations (modelkit rake run), you may encounter the following error message:

**instance-out.err**
```
** Severe  ** Invalid string position in input line
```

This issue occurs when the SCHEDULE:FILE object in the EnergyPlus model (.IDF)
references a schedule file via a relative file path instead of an absolute path.
(When EnergyPlus attempts to resolve the actual filename, it concatenates the
simulation directory and the relative path, resulting in an intermediate file
path string longer than EnergyPlus routines can handle, even if the absolute
path to the file would not cause an error.) The templates are defined using relative
paths for portability, which is not itself an issue.

### Example of Problematic Code

**templates/energyplus/templates/system/res-water-heater-combi.pxt near line 189**

```ruby
<%# Schedules %>
     Schedule:File,
         <%= water_heater_name %>_demand_frac_sch,  !- Name
         fraction,                !- Schedule Type Limits Name
         ../../../../../../../../templates/hot water profile/<%= dhw_demand_sch %>,  !- File Name
         1,                       !- Column Number
         1,                       !- Rows to Skip at Top
         8760,                    !- Number of Hours of Data
         Comma,                   !- Column Separator
         No,                      !- Interpolate to Timestep
```

**prototypes/residential/MFm-1985-combi/templates/root.pxt near line 316**

```ruby
<% zones = ["01","02","03","04","05","06","07","08","09","10","11","12","13","14","15","16"]
 climate_zone_str = zones[climate_zone - 1] %>
 Schedule:File,
     site_mains_water_temp,  !- Name
     Temperature,                !- Schedule Type Limits Name
     ../../../../../../../../templates/hot water profile/site_mains_water_temp_CZ<%= climate_zone_str %>.csv,  !- File Name
     1,                       !- Column Number
     1,                       !- Rows to Skip at Top
     8760,                    !- Number of Hours of Data
     Comma,                   !- Column Separator
     No,                      !- Interpolate to Timestep		 
```

### Corrected Example (Workaround)

The workaround is to replace the relative path with the absolute path to the schedule file:

**templates/energyplus/templates/system/res-water-heater-combi.pxt near line 189**

```ruby
<%# Schedules %>
     Schedule:File,
         <%= water_heater_name %>_demand_frac_sch,  !- Name
         fraction,                !- Schedule Type Limits Name
         C:/DEER-Prototypes-EnergyPlus/templates/hot water profile/<%= dhw_demand_sch %>,  !- File Name
         1,                       !- Column Number
         1,                       !- Rows to Skip at Top
         8760,                    !- Number of Hours of Data
         Comma,                   !- Column Separator
         No,                      !- Interpolate to Timestep
```

**prototypes/residential/MFm-1985-combi/templates/root.pxt near line 316**

```ruby
<% zones = ["01","02","03","04","05","06","07","08","09","10","11","12","13","14","15","16"]
 climate_zone_str = zones[climate_zone - 1] %>
 Schedule:File,
     site_mains_water_temp,  !- Name
     Temperature,                !- Schedule Type Limits Name
     C:/DEER-Prototypes-EnergyPlus/templates/hot water profile/site_mains_water_temp_CZ<%= climate_zone_str %>.csv,  !- File Name
     1,                       !- Column Number
     1,                       !- Rows to Skip at Top
     8760,                    !- Number of Hours of Data
     Comma,                   !- Column Separator
     No,                      !- Interpolate to Timestep		 
```

### Notes

   1. This issue typically appears when EnergyPlus cannot resolve the relative directory structure in certain automation or deployment environments.
   2. Using absolute paths ensures that EnergyPlus can locate the CSV file regardless of where the model is executed.
