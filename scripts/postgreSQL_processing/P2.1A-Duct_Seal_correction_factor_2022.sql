--modification 7/14/2022 (due to EMS over calculating heat losses. Temporary fix for Duct Sealing Measure
--multiply MFm and SFm savings record by a factor of 1/3
SET search_path TO "MC_results_database";
DROP TABLE IF EXISTS meas_impacts_2022_ds_mod;
CREATE TABLE meas_impacts_2022_ds_mod AS 

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
("APreWBkWh" * (0.333)) as "APreWBkWh",
("APreWBkW25" * (0.333)) as "APreWBkW25",
("APreWBkW49" * (0.333)) as "APreWBkW49",
("APreWBtherm" * (0.333)) as "APreWBtherm",
("AStdWBkWh" * (0.333)) as "AStdWBkWh",
("AStdWBkW25" * (0.333)) as "AStdWBkW25",
("AStdWBkW49" * (0.333)) as "AStdWBkW49",
("AStdWBtherm" * (0.333)) as "AStdWBtherm",
"APreUseEUkWh",
"APreUseEUtherm",
"AStdUseEUkWh",
"AStdUseEUtherm",
"AMsrUseEUkWh",
"AMsrUseEUtherm"
FROM 
meas_impacts_2022
WHERE (meas_impacts_2022."BldgType" = 'MFm') OR (meas_impacts_2022."BldgType" = 'SFm')

ORDER BY 
"EnergyImpactID",
"PA",
"BldgType",
"BldgVint",
"BldgLoc",
"BldgHVAC";
