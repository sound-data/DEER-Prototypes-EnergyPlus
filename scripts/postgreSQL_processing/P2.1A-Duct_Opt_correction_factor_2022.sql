--modification 7/27/2022 (due to EMS over calculating heat losses. Temporary fix for Duct Sealing Measure
--multiply retrofit savings record by a factor of 1/2
SET search_path TO "MC_results_database";
DROP TABLE IF EXISTS meas_impacts_2022_do_mod;
CREATE TABLE meas_impacts_2022_do_mod AS 

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
"NormUnit",
"NumUnit",
"MeasArea",
"ScaleBasis",
("APreWBkWh" * (0.5)) as "APreWBkWh",
("APreWBkW25" * (0.5)) as "APreWBkW25",
("APreWBkW49" * (0.5)) as "APreWBkW49",
("APreWBtherm" * (0.5)) as "APreWBtherm",
("AStdWBkWh" * (0.5)) as "AStdWBkWh",
("AStdWBkW25" * (0.5)) as "AStdWBkW25",
("AStdWBkW49" * (0.5)) as "AStdWBkW49",
("AStdWBtherm" * (0.5)) as "AStdWBtherm",
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
WHERE (meas_impacts_2022."EnergyImpactID" = 'Res-DuctSeal-HighToLow-wtd_retrofit')

ORDER BY 
"EnergyImpactID",
"PA",
"BldgType",
"BldgVint",
"BldgLoc",
"BldgHVAC";
