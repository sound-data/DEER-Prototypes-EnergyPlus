--Delete the unmodded MFm/SFm records, insert the modded MFm/SFm records

SET search_path TO "MC_results_database";

DELETE FROM meas_impacts_2022
WHERE (meas_impacts_2022."BldgType" = 'MFm') OR (meas_impacts_2022."BldgType" = 'SFm');

INSERT INTO meas_impacts_2022
SELECT
*
/* "EnergyImpactID",
"Version",
"VersionSource",
"LastMod",
"PA",
"BldgType",
"BldgVint", 
"BldgLoc",
"BldgHVAC",
"NormUnit",
"NumUnit",
"MeasArea",
"ScaleBasis",
"APreWBkWh",
"APreWBkW49",
"APreWBtherm",
"AStdWBkWh",
"AStdWBkW49",
"AStdWBtherm",
"APreUseEUkWh",
"APreUseEUtherm",
"AStdUseEUkWh",
"AStdUseEUtherm",
"AMsrUseEUkWh",
"AMsrUseEUtherm" */
FROM meas_impacts_2022_ds_mod;
