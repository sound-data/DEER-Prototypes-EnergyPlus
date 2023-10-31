SET search_path TO "MC_results_database";
DROP TABLE IF EXISTS meas_impacts_wtd_2022;
CREATE TABLE meas_impacts_wtd_2022 AS 

SELECT
"EnergyImpactID",
"Version",
"VersionSource",
"LastMod",
"PA",
meas_impacts_2022."BldgType",
meas_impacts_2022."BldgVint",  -- this can be Ex or New depending on the prototype used to generate results
meas_impacts_2022."BldgLoc",
meas_impacts_2022."BldgHVAC",
"NormUnit",
"NumUnit",
"MeasArea",
"ScaleBasis",
"APreWBkWh",
"APreWBkW49" as "APreWBkW",
"APreWBtherm",
"AStdWBkWh",
"AStdWBkW49" as "AStdWBkW",
"AStdWBtherm",
"APreUseWBkWh",
"APreUseWBtherm",
"AStdUseWBkWh",
"AStdUseWBtherm",
"AMsrUseWBkWh",
"AMsrUseWBtherm",
"APreUseEUkWh",
"APreUseEUtherm",
"AStdUseEUkWh",
"AStdUseEUtherm",
"AMsrUseEUkWh",
"AMsrUseEUtherm"
FROM 
meas_impacts_2022

ORDER BY 
"EnergyImpactID",
"PA",
"BldgType",
"BldgVint",
"BldgLoc",
"BldgHVAC";

--update the BldgVint columns

UPDATE meas_impacts_wtd_2022
SET "BldgVint" = 'Ex'
WHERE "BldgVint" = '1975' OR "BldgVint" = '1985'
;
