-- Optional: only if HVAC wtd results are needed
-- Run P2.5 first: Create the res HVAC weighted version of the annual results by summing the results of the previous table
-- Add the results to the measure impacts table

SET search_path TO "MC_results_database";
DROP TABLE IF EXISTS meas_impacts_hvacwtd;
CREATE TABLE meas_impacts_hvacwtd AS 

SELECT
"EnergyImpactID",
"Version",
"VersionSource",
date_trunc('second', now()) as "LastMod",
"PA",
"BldgType"::VARCHAR,
"BldgVint"::VARCHAR,
"BldgLoc"::VARCHAR,
'rWtd'::VARCHAR AS "BldgHVAC", --note single quote defines a new string name, double quote refer to column name 
"NormUnit"::VARCHAR,
--apply multiplied weights to all numeric parameters
(Sum("NumUnit") / Sum(wt_hvac))::numeric(15,5) AS "NumUnit",
(Sum("MeasArea") / Sum(wt_hvac))::numeric(15,1) AS "MeasArea",
"ScaleBasis"::VARCHAR,
(Sum("APreWBkWh") / Sum(wt_hvac))::numeric(15,5) as "APreWBkWh",
(Sum("APreWBkW25") / Sum(wt_hvac))::numeric(15,5) as "APreWBkW25",
(Sum("APreWBkW49") / Sum(wt_hvac))::numeric(15,5) as "APreWBkW49",
(Sum("APreWBtherm") / Sum(wt_hvac))::numeric(15,5) as "APreWBtherm",
(Sum("AStdWBkWh") / Sum(wt_hvac))::numeric(15,5) as "AStdWBkWh",
(Sum("AStdWBkW25") / Sum(wt_hvac))::numeric(15,5) as "AStdWBkW25",
(Sum("AStdWBkW49") / Sum(wt_hvac))::numeric(15,5) as "AStdWBkW49",
(Sum("AStdWBtherm") / Sum(wt_hvac))::numeric(15,5) as "AStdWBtherm",
--new fields added 6/20/2022
(Sum("APreUseWBkWh") / Sum(wt_hvac))::numeric(15,5)  as "APreUseWBkWh",
(Sum("APreUseWBtherm") / Sum(wt_hvac))::numeric(15,5)  as "APreUseWBtherm",
(Sum("AStdUseWBkWh") / Sum(wt_hvac))::numeric(15,5)  as "AStdUseWBkWh",
(Sum("AStdUseWBtherm") / Sum(wt_hvac))::numeric(15,5)  as "AStdUseWBtherm",
(Sum("AMsrUseWBkWh") / Sum(wt_hvac))::numeric(15,5)  as "AMsrUseWBkWh",
(Sum("AMsrUseWBtherm") / Sum(wt_hvac))::numeric(15,5)  as "AMsrUseWBtherm",
(Sum("APreUseEUkWh") / Sum(wt_hvac))::numeric(15,5)  as "APreUseEUkWh",
(Sum("APreUseEUtherm") / Sum(wt_hvac))::numeric(15,5)  as "APreUseEUtherm",
(Sum("AStdUseEUkWh") / Sum(wt_hvac))::numeric(15,5)  as "AStdUseEUkWh",
(Sum("AStdUseEUtherm") / Sum(wt_hvac))::numeric(15,5)  as "AStdUseEUtherm",
(Sum("AMsrUseEUkWh") / Sum(wt_hvac))::numeric(15,5)  as "AMsrUseEUkWh",
(Sum("AMsrUseEUtherm") / Sum(wt_hvac))::numeric(15,5)  as "AMsrUseEUtherm"
from meas_impacts_hvactmp
WHERE meas_impacts_hvactmp."wt_hvac" <> 0
GROUP BY
"EnergyImpactID",
"Version",
"VersionSource",
"PA",
"BldgType",
"BldgVint",
"BldgLoc",
"NormUnit",
"ScaleBasis"
ORDER BY 
"EnergyImpactID",
"PA",
"BldgType",
"BldgVint",
"BldgLoc";

---creates BldgHVAC = "rWtd" entries only
---
---then Run second: insert into existing measure impacts results below
---after this step, THEN apply subsequent weighting steps (Vint, Loc, BldgType)
SET search_path TO "MC_results_database";
INSERT INTO meas_impacts_2022
SELECT
*
FROM meas_impacts_hvacwtd

ORDER BY 
"EnergyImpactID",
"PA",
"BldgType",
"BldgVint",
"BldgLoc",
"BldgHVAC";

