-- Optional: only if HVAC wtd results are needed
--Create Res HVAC weight multiplied ver. of measure impacts table (to be summed later)
SET search_path TO "MC_results_database";
DROP TABLE IF EXISTS meas_impacts_hvactmp;
CREATE TABLE meas_impacts_hvactmp AS 
SELECT
"EnergyImpactID",
"Version",
"VersionSource",
"LastMod",
"PA",
meas_impacts_2022."BldgType",
meas_impacts_2022."BldgVint",
meas_impacts_2022."BldgLoc",
meas_impacts_2022."BldgHVAC",
wtval as "wt_hvac",
--calculate the weight-multiplied version of the corresponding parameter
"NormUnit",
"NumUnit" * wtval as "NumUnit",
"MeasArea" * wtval   as "MeasArea",
'None'::VARCHAR as "ScaleBasis",
"APreWBkWh" * wtval   as "APreWBkWh",
"APreWBkW25" * wtval    as "APreWBkW25",
"APreWBkW49" * wtval    as "APreWBkW49",
"APreWBtherm" * wtval as "APreWBtherm",
"AStdWBkWh" * wtval   as "AStdWBkWh",
"AStdWBkW25" * wtval    as "AStdWBkW25",
"AStdWBkW49" * wtval    as "AStdWBkW49",
"AStdWBtherm" * wtval as "AStdWBtherm",
--new fields added 6/20/2022
"APreUseWBkWh" * wtval as "APreUseWBkWh",
"APreUseWBtherm" * wtval as "APreUseWBtherm",
"AStdUseWBkWh" * wtval as "AStdUseWBkWh",
"AStdUseWBtherm" * wtval as "AStdUseWBtherm",
"AMsrUseWBkWh" * wtval as "AMsrUseWBkWh",
"AMsrUseWBtherm" * wtval as "AMsrUseWBtherm",
"APreUseEUkWh" * wtval as "APreUseEUkWh",
"APreUseEUtherm" * wtval as "APreUseEUtherm",
"AStdUseEUkWh" * wtval as "AStdUseEUkWh",
"AStdUseEUtherm" * wtval as "AStdUseEUtherm",
"AMsrUseEUkWh" * wtval as "AMsrUseEUkWh",
"AMsrUseEUtherm" * wtval as "AMsrUseEUtherm"
FROM meas_impacts_2022

JOIN wts_res_hvac on 
 wts_res_hvac.pa       = meas_impacts_2022."PA" and 
 wts_res_hvac.bldgtype = meas_impacts_2022."BldgType" and 
 wts_res_hvac.bldgloc  = meas_impacts_2022."BldgLoc" and
 wts_res_hvac.bldghvac = meas_impacts_2022."BldgHVAC"
;
