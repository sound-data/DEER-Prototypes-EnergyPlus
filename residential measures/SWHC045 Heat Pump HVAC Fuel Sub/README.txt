Purpose:

This document describes the workaround implemented to resolve the relative path issue in EnergyPlus models that causes the
** Severe ** Invalid string position error when loading external schedule files.

Prepared by Solaris Technical, Behzad S. Rizi - 2025-10-17

Known Issue: ** Severe ** Invalid String Position Error

When running EnergyPlus simulations, you may encounter the following error message:
** Severe  ** Invalid string position in input line

This issue occurs when the SCHEDULE:FILE object in the IDF references a relative file path instead of an absolute path.

Example of Problematic Code
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

Corrected Example (Workaround)
The workaround is to replace the relative path with the absolute path to the schedule file:

<%# Schedules %>
     Schedule:File,
         <%= water_heater_name %>_demand_frac_sch,  !- Name
         fraction,                !- Schedule Type Limits Name
         C:/DEER_Commercial/EnergyPlus/TRC-res-templates/templates/hot water profile/<%= dhw_demand_sch %>,  !- File Name
         1,                       !- Column Number
         1,                       !- Rows to Skip at Top
         8760,                    !- Number of Hours of Data
         Comma,                   !- Column Separator
         No,                      !- Interpolate to Timestep


<% zones = ["01","02","03","04","05","06","07","08","09","10","11","12","13","14","15","16"]
 climate_zone_str = zones[climate_zone - 1] %>
 Schedule:File,
     site_mains_water_temp,  !- Name
     Temperature,                !- Schedule Type Limits Name
     C:/DEER_Commercial/EnergyPlus/TRC-res-templates/templates/hot water profile/site_mains_water_temp_CZ<%= climate_zone_str %>.csv,  !- File Name
     1,                       !- Column Number
     1,                       !- Rows to Skip at Top
     8760,                    !- Number of Hours of Data
     Comma,                   !- Column Separator
     No,                      !- Interpolate to Timestep		 

Notes

   1. This issue typically appears when EnergyPlus cannot resolve the relative directory structure in certain automation or deployment environments.
   2. Using absolute paths ensures that EnergyPlus can locate the CSV file regardless of where the model is executed.