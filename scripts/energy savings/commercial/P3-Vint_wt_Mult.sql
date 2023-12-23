-- Create the vintage weight multiplied version of the annual results (to be summed later), 
--  If the total ERA weight is 0, then don't multiply by wt_vint, set the wt to 1.0; 
--     the sum process in the next step will then use the average of the vintage impact values for era
--  Also, decide here which peak demand value is used in subsequent tables (2 - 5, or 4 - 9)
--  Note: "New" vintage results are not included here, as they are merely added insted of summed in the next step
SET search_path TO "MC_results_database";
DROP TABLE IF EXISTS "meas_impacts_tmp";
CREATE TABLE "meas_impacts_tmp" AS 
SELECT
"EnergyImpactID",
"Version",
"VersionSource",
"LastMod",
wts_com_vintage.pa as "PA",
meas_impacts_2022."BldgType",
meas_impacts_2022."BldgVint",
wts_com_vintage.era as "era",
meas_impacts_2022."BldgLoc",
meas_impacts_2022."BldgHVAC",
CASE WHEN wts_com_loc.sum_loc = 0 THEN 1 ELSE wts_com_vintage.wt_vint END as "wt_vint",
"NormUnit",
"NumUnit" * wt_vint as "NumUnit",
"MeasArea" * wt_vint as "MeasArea",
'None'::VARCHAR as "ScaleBasis",
CASE WHEN wts_com_loc.sum_loc = 0 THEN "APreWBkWh"   ELSE "APreWBkWh" * wt_vint   END as "APreWBkWh",
CASE WHEN wts_com_loc.sum_loc = 0 THEN "APreWBkW49"  ELSE "APreWBkW49" * wt_vint  END as "APreWBkW",
CASE WHEN wts_com_loc.sum_loc = 0 THEN "APreWBtherm" ELSE "APreWBtherm" * wt_vint END as "APreWBtherm",
CASE WHEN wts_com_loc.sum_loc = 0 THEN "AStdWBkWh"   ELSE "AStdWBkWh" * wt_vint   END as "AStdWBkWh",
CASE WHEN wts_com_loc.sum_loc = 0 THEN "AStdWBkW49"  ELSE "AStdWBkW49" * wt_vint  END as "AStdWBkW",
CASE WHEN wts_com_loc.sum_loc = 0 THEN "AStdWBtherm" ELSE "AStdWBtherm" * wt_vint END as "AStdWBtherm",

--new fields added 6/20/2022
"APreUseWBkWh" * wt_vint as "APreUseWBkWh",
"APreUseWBtherm" * wt_vint as "APreUseWBtherm",
"AStdUseWBkWh" * wt_vint as "AStdUseWBkWh",
"AStdUseWBtherm" * wt_vint as "AStdUseWBtherm",
"AMsrUseWBkWh" * wt_vint as "AMsrUseWBkWh",
"AMsrUseWBtherm" * wt_vint as "AMsrUseWBtherm",
"APreUseEUkWh" * wt_vint as "APreUseEUkWh",
"APreUseEUtherm" * wt_vint as "APreUseEUtherm",
"AStdUseEUkWh" * wt_vint as "AStdUseEUkWh",
"AStdUseEUtherm" * wt_vint as "AStdUseEUtherm",
"AMsrUseEUkWh" * wt_vint as "AMsrUseEUkWh",
"AMsrUseEUtherm" * wt_vint as "AMsrUseEUtherm"

from "meas_impacts_2022"
JOIN wts_com_vintage on 
 wts_com_vintage.bldgtype = meas_impacts_2022."BldgType" and 
 wts_com_vintage.bldgvint = meas_impacts_2022."BldgVint" and 
 wts_com_vintage.bldgloc  = meas_impacts_2022."BldgLoc"
JOIN wts_com_loc on 
 wts_com_vintage.pa       = wts_com_loc.pa and 
 wts_com_vintage.bldgtype = wts_com_loc.bldgtype and 
 wts_com_vintage.bldgloc  = wts_com_loc.bldgloc and
 wts_com_vintage.era      = wts_com_loc.era
WHERE meas_impacts_2022."BldgVint" <> 'New'

ORDER BY 
"EnergyImpactID",
wts_com_vintage.pa,
meas_impacts_2022."BldgType",
meas_impacts_2022."BldgVint",
meas_impacts_2022."BldgLoc",
meas_impacts_2022."BldgHVAC";

ALTER TABLE "meas_impacts_tmp"
ALTER COLUMN "EnergyImpactID" SET NOT NULL,
ALTER COLUMN "PA" SET NOT NULL,
ALTER COLUMN "BldgType" SET NOT NULL,
ALTER COLUMN "BldgVint" SET NOT NULL,
ALTER COLUMN "BldgLoc" SET NOT NULL,
ALTER COLUMN "BldgHVAC" SET NOT NULL,
ADD PRIMARY KEY ("EnergyImpactID", "PA", "BldgType", "BldgVint", "BldgLoc", "BldgHVAC");
