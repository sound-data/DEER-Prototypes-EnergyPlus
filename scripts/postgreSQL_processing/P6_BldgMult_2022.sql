--building type weights, multiplication step

SET search_path TO "MC_results_database";
DROP TABLE IF EXISTS meas_impacts_tmp3_2022;
CREATE TABLE meas_impacts_tmp3_2022 AS 
SELECT

"EnergyImpactID",
meas_impacts_wtd_2022."PA",
meas_impacts_wtd_2022."BldgType",
meas_impacts_wtd_2022."BldgVint",
meas_impacts_wtd_2022."BldgLoc",
meas_impacts_wtd_2022."BldgHVAC",
sum_bldg as "wt_bldg",
"NormUnit",
"NumUnit" * sum_bldg as "NumUnit",
"MeasArea" * sum_bldg   as "MeasArea",
'None'::VARCHAR as "ScaleBasis",
"APreWBkWh" * sum_bldg   as "APreWBkWh",
"APreWBkW" * sum_bldg    as "APreWBkW",
"APreWBtherm" * sum_bldg as "APreWBtherm",
"AStdWBkWh" * sum_bldg   as "AStdWBkWh",
"AStdWBkW" * sum_bldg    as "AStdWBkW",
"AStdWBtherm" * sum_bldg as "AStdWBtherm",

--new fields added 6/20/2022
"APreUseWBkWh" * sum_bldg as "APreUseWBkWh",
"APreUseWBtherm" * sum_bldg as "APreUseWBtherm",
"AStdUseWBkWh" * sum_bldg as "AStdUseWBkWh",
"AStdUseWBtherm" * sum_bldg as "AStdUseWBtherm",
"AMsrUseWBkWh" * sum_bldg as "AMsrUseWBkWh",
"AMsrUseWBtherm" * sum_bldg as "AMsrUseWBtherm",
"APreUseEUkWh" * sum_bldg as "APreUseEUkWh",
"APreUseEUtherm" * sum_bldg as "APreUseEUtherm",
"AStdUseEUkWh" * sum_bldg as "AStdUseEUkWh",
"AStdUseEUtherm" * sum_bldg as "AStdUseEUtherm",
"AMsrUseEUkWh" * sum_bldg as "AMsrUseEUkWh",
"AMsrUseEUtherm" * sum_bldg as "AMsrUseEUtherm"

from meas_impacts_wtd_2022

LEFT JOIN wts_res_bldg_2022 on 
 wts_res_bldg_2022.bldgtype = meas_impacts_wtd_2022."BldgType" and 
 wts_res_bldg_2022.bldgloc  = meas_impacts_wtd_2022."BldgLoc" and 
 wts_res_bldg_2022.era      = meas_impacts_wtd_2022."BldgVint"
WHERE meas_impacts_wtd_2022."BldgType" <> 'Res'

ORDER BY 
"EnergyImpactID",
"PA",
"BldgType",
"BldgVint",
"BldgLoc",
"BldgHVAC";