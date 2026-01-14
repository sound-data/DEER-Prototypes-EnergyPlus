-- Create the location weight multiplied version of the measure impacts table (to be summed later), 
--  The weights table has to be linked differently for the New vintage for the climate-zone specific results
SET search_path TO "MC_results_database";
DROP TABLE IF EXISTS meas_impacts_tmp3;
CREATE TABLE meas_impacts_tmp3 AS 
SELECT
"EnergyImpactID",
meas_impacts_vint_wtd."PA",
meas_impacts_vint_wtd."BldgType",
meas_impacts_vint_wtd."BldgVint",
meas_impacts_vint_wtd."BldgLoc",
meas_impacts_vint_wtd."BldgHVAC",
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

from meas_impacts_vint_wtd
LEFT JOIN wts_com_bldg on 
 wts_com_bldg.pa       = meas_impacts_vint_wtd."PA" and 
 wts_com_bldg.bldgtype = meas_impacts_vint_wtd."BldgType" and 
 wts_com_bldg.era      = meas_impacts_vint_wtd."BldgVint" and
 wts_com_bldg.bldgloc  = meas_impacts_vint_wtd."BldgLoc"
--WHERE meas_impacts_vint_wtd."BldgLoc" = 'IOU'
WHERE meas_impacts_vint_wtd."BldgType" <> 'Com' 
  and not ((meas_impacts_vint_wtd."BldgVint" = 'New') AND (meas_impacts_vint_wtd."BldgLoc" like 'CZ%'))

--this union part was causing error for chillers.
UNION

SELECT
"EnergyImpactID",
wts_com_bldg.pa AS "PA",
meas_impacts_vint_wtd."BldgType",
meas_impacts_vint_wtd."BldgVint",
meas_impacts_vint_wtd."BldgLoc",
meas_impacts_vint_wtd."BldgHVAC",
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

from meas_impacts_vint_wtd
LEFT JOIN wts_com_bldg on 
 wts_com_bldg.bldgtype = meas_impacts_vint_wtd."BldgType" and 
 wts_com_bldg.era      = meas_impacts_vint_wtd."BldgVint" and
 wts_com_bldg.bldgloc  = meas_impacts_vint_wtd."BldgLoc"
--WHERE meas_impacts_vint_wtd."BldgLoc" = 'IOU'
WHERE meas_impacts_vint_wtd."BldgType" <> 'Com' 
  and ((meas_impacts_vint_wtd."BldgVint" = 'New') AND (meas_impacts_vint_wtd."BldgLoc" like 'CZ%'))

ORDER BY 
"EnergyImpactID",
"PA",
"BldgVint",
"BldgLoc",
"BldgHVAC";

ALTER TABLE "meas_impacts_tmp3"
ALTER COLUMN "EnergyImpactID" SET NOT NULL,
ALTER COLUMN "PA" SET NOT NULL,
ALTER COLUMN "BldgType" SET NOT NULL,
ALTER COLUMN "BldgVint" SET NOT NULL,
ALTER COLUMN "BldgLoc" SET NOT NULL,
ALTER COLUMN "BldgHVAC" SET NOT NULL,
ADD PRIMARY KEY ("EnergyImpactID", "PA", "BldgType", "BldgVint", "BldgLoc", "BldgHVAC");
