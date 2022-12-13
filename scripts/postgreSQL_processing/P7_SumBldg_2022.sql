--building type weight, sum/division step

SET search_path TO "MC_results_database";
DELETE FROM meas_impacts_wtd_2022 WHERE "BldgType" = 'Res';
INSERT INTO meas_impacts_wtd_2022
SELECT
"EnergyImpactID",
'DEER2024'::text as "Version",
'D24_E+_Res_v5'::text as "VersionSource",
date_trunc('second', now()) as "LastMod",
"PA",
'Res'::VARCHAR as "BldgType",
"BldgVint",
"BldgLoc",
"BldgHVAC",
"NormUnit",
(Sum("NumUnit") / Sum(wt_bldg))::numeric(15,1) AS "NumUnit",
(Sum("MeasArea") / Sum(wt_bldg))::numeric(15,0) AS "MeasArea",
"ScaleBasis",
(Sum("APreWBkWh") / Sum(wt_bldg))::numeric(15,5) as "APreWBkWh",
(Sum("APreWBkW") / Sum(wt_bldg))::numeric(15,5) as "APreWBkW",
(Sum("APreWBtherm") / Sum(wt_bldg))::numeric(15,5) as "APreWBtherm",
(Sum("AStdWBkWh") / Sum(wt_bldg))::numeric(15,5) as "AStdWBkWh",
(Sum("AStdWBkW") / Sum(wt_bldg))::numeric(15,5) as "AStdWBkW",
(Sum("AStdWBtherm") / Sum(wt_bldg))::numeric(15,5) as "AStdWBtherm",

--new fields added 6/20/2022
(Sum("APreUseWBkWh") / Sum(wt_bldg)) as "APreUseWBkWh",
(Sum("APreUseWBtherm") / Sum(wt_bldg)) as "APreUseWBtherm",
(Sum("AStdUseWBkWh") / Sum(wt_bldg)) as "AStdUseWBkWh",
(Sum("AStdUseWBtherm") / Sum(wt_bldg)) as "AStdUseWBtherm",
(Sum("AMsrUseWBkWh") / Sum(wt_bldg)) as "AMsrUseWBkWh",
(Sum("AMsrUseWBtherm") / Sum(wt_bldg)) as "AMsrUseWBtherm",
(Sum("APreUseEUkWh") / Sum(wt_bldg)) as "APreUseEUkWh",
(Sum("APreUseEUtherm") / Sum(wt_bldg)) as "APreUseEUtherm",
(Sum("AStdUseEUkWh") / Sum(wt_bldg)) as "AStdUseEUkWh",
(Sum("AStdUseEUtherm") / Sum(wt_bldg)) as "AStdUseEUtherm",
(Sum("AMsrUseEUkWh") / Sum(wt_bldg)) as "AMsrUseEUkWh",
(Sum("AMsrUseEUtherm") / Sum(wt_bldg)) as "AMsrUseEUtherm"

from meas_impacts_tmp3_2022
GROUP BY
"EnergyImpactID",
"PA",
"BldgVint",
"BldgLoc",
"BldgHVAC",
"NormUnit",
"ScaleBasis"
ORDER BY 
"EnergyImpactID",
"PA",
"BldgVint",
"BldgLoc",
"BldgHVAC";