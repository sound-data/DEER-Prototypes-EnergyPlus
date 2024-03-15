-- Sum the vintage weight multiplied version of the annual results created in the previous step, 
--  Also, add the New vintage results from the measure impacts table as the final vintage.
--  Note: results from this query form the starting point for the final results table, to be augmented with 
--        additional results from subsequent queries.
SET search_path TO "MC_results_database";
DROP TABLE IF EXISTS meas_impacts_wtd;
CREATE TABLE meas_impacts_wtd AS 
SELECT
"EnergyImpactID",
'DEER2024'::VARCHAR as "Version",
'D24v0'::VARCHAR as "VersionSource",
date_trunc('second', now()) as "LastMod",
"PA",
"BldgType"::VARCHAR,
era as "BldgVint",
"BldgLoc"::VARCHAR,
"BldgHVAC"::VARCHAR,
'Cap-Tons'::VARCHAR as "NormUnit",
(Sum("NumUnit") / Sum(wt_vint))::numeric(15,5) AS "NumUnit",
(Sum("MeasArea") / Sum(wt_vint))::numeric(15,0) AS "MeasArea",
'None'::VARCHAR as "ScaleBasis",
(Sum("APreWBkWh") / Sum(wt_vint))::numeric(15,5) as "APreWBkWh",
(Sum("APreWBkW") / Sum(wt_vint))::numeric(15,5) as "APreWBkW",
(Sum("APreWBtherm") / Sum(wt_vint))::numeric(15,5) as "APreWBtherm",
(Sum("AStdWBkWh") / Sum(wt_vint))::numeric(15,5) as "AStdWBkWh",
(Sum("AStdWBkW") / Sum(wt_vint))::numeric(15,5) as "AStdWBkW",
(Sum("AStdWBtherm") / Sum(wt_vint))::numeric(15,5) as "AStdWBtherm",

--new fields added 6/20/2022
(Sum("APreUseWBkWh") / Sum(wt_vint)) as "APreUseWBkWh",
(Sum("APreUseWBtherm") / Sum(wt_vint)) as "APreUseWBtherm",
(Sum("AStdUseWBkWh") / Sum(wt_vint)) as "AStdUseWBkWh",
(Sum("AStdUseWBtherm") / Sum(wt_vint)) as "AStdUseWBtherm",
(Sum("AMsrUseWBkWh") / Sum(wt_vint)) as "AMsrUseWBkWh",
(Sum("AMsrUseWBtherm") / Sum(wt_vint)) as "AMsrUseWBtherm",
(Sum("APreUseEUkWh") / Sum(wt_vint)) as "APreUseEUkWh",
(Sum("APreUseEUtherm") / Sum(wt_vint)) as "APreUseEUtherm",
(Sum("AStdUseEUkWh") / Sum(wt_vint)) as "AStdUseEUkWh",
(Sum("AStdUseEUtherm") / Sum(wt_vint)) as "AStdUseEUtherm",
(Sum("AMsrUseEUkWh") / Sum(wt_vint)) as "AMsrUseEUkWh",
(Sum("AMsrUseEUtherm") / Sum(wt_vint)) as "AMsrUseEUtherm"

from meas_impacts_tmp
GROUP BY
"EnergyImpactID",
"PA",
"BldgType",
era,
"BldgLoc",
"BldgHVAC"

ORDER BY 
"EnergyImpactID",
"PA",
"BldgType",
"BldgVint",
"BldgLoc",
"BldgHVAC";

ALTER TABLE "meas_impacts_wtd"
ALTER COLUMN "EnergyImpactID" SET NOT NULL,
ALTER COLUMN "PA" SET NOT NULL,
ALTER COLUMN "BldgType" SET NOT NULL,
ALTER COLUMN "BldgVint" SET NOT NULL,
ALTER COLUMN "BldgLoc" SET NOT NULL,
ALTER COLUMN "BldgHVAC" SET NOT NULL,
ADD PRIMARY KEY ("EnergyImpactID", "PA", "BldgType", "BldgVint", "BldgLoc", "BldgHVAC");
