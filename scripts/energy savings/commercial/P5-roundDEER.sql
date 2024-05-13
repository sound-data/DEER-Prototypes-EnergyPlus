-- Format the measures impacts table for the ex ante database, using three significant figures where appropriate 
--   and adding the appropriate text for the impact profiles for this measure group.
SET search_path TO "MC_results_database";
DROP TABLE IF EXISTS meas_impacts_2024_com;
CREATE TABLE meas_impacts_2024_com AS 
SELECT

meas_impacts_vint_wtd."EnergyImpactID"::VARCHAR,
"Version"::VARCHAR,
"VersionSource"::VARCHAR, --Note Version must reflect prototype version used (COP, sizing, etc.)
"LastMod"::TIMESTAMP,
"PA",
"BldgType",
"BldgVint",
"BldgLoc",
"BldgHVAC",
--(CASE WHEN "NormUnit" = 'ResCoolCap' THEN 'Cap-Tons' ELSE 'Cap-kBTUh' END)::VARCHAR as "NormUnit", #3/10/2022 changed this line to follow whatever Norm unit it was before
"NormUnit",
(case "NumUnit" when 0 then 0 else round("NumUnit"::Numeric(15,5),(2-floor(log(abs("NumUnit"))))::SMALLINT) end)::float4 as "NumUnit", 
(case "MeasArea" when 0 then 0 else round("MeasArea"::Numeric(15,5),(2-floor(log(abs("MeasArea"))))::SMALLINT) end)::float4 as "MeasArea", 
"ScaleBasis",
--"APreWBkWh_0",
(case "APreWBkWh" when 0 then 0 else round("APreWBkWh"::Numeric(15,6),(2-floor(log(abs("APreWBkWh"))))::SMALLINT) end)::float4 as "APreWBkWh", 
--"APreWBkW_0",
(case "APreWBkW" when 0 then 0 else round("APreWBkW"::Numeric(15,6),(2-floor(log(abs("APreWBkW"))))::SMALLINT) end)::float4 as "APreWBkW", 
--"APreWBtherm_0",
(case "APreWBtherm" when 0 then 0 else round("APreWBtherm"::Numeric(15,6),(2-floor(log(abs("APreWBtherm"))))::SMALLINT) end)::float4 as "APreWBtherm", 
--"AStdWBkWh_0",
(case "AStdWBkWh" when 0 then 0 else round("AStdWBkWh"::Numeric(15,6),(2-floor(log(abs("AStdWBkWh"))))::SMALLINT) end)::float4 as "AStdWBkWh", 
--"AStdWBkW_0",
(case "AStdWBkW" when 0 then 0 else round("AStdWBkW"::Numeric(15,6),(2-floor(log(abs("AStdWBkW"))))::SMALLINT) end)::float4 as "AStdWBkW", 
--"AStdWBtherm_0",
(case "AStdWBtherm" when 0 then 0 else round("AStdWBtherm"::Numeric(15,6),(2-floor(log(abs("AStdWBtherm"))))::SMALLINT) end)::float4 as "AStdWBtherm",
NULL::FLOAT4 as "APreEUkWh",
NULL::FLOAT4 as "APreEUkW",
NULL::FLOAT4 as "APreEUtherm",
NULL::FLOAT4 as "AStdEUkWh",
NULL::FLOAT4 as "AStdEUkW",
NULL::FLOAT4 as "AStdEUtherm",
NULL as "ElecImpactProfileID",
NULL as "GasImpactProfileID",
20::INT2 as "Flag",
''::VARCHAR as "SourceDesc",
--new fields added 6/20/2022
(case "APreUseWBkWh" when 0 then 0 else round("APreUseWBkWh"::numeric(15,5), 4-floor(log(abs("APreUseWBkWh")))::INT) end) as "APreUseWBkWh",
(case "APreUseWBtherm" when 0 then 0 else round("APreUseWBtherm"::numeric(15,5), 4-floor(log(abs("APreUseWBtherm")))::INT) end) as "APreUseWBtherm",
(case "AStdUseWBkWh" when 0 then 0 else round("AStdUseWBkWh"::numeric(15,5), 4-floor(log(abs("AStdUseWBkWh")))::INT) end) as "AStdUseWBkWh",
(case "AStdUseWBtherm" when 0 then 0 else round("AStdUseWBtherm"::numeric(15,5), 4-floor(log(abs("AStdUseWBtherm")))::INT) end) as "AStdUseWBtherm",
(case "AMsrUseWBkWh" when 0 then 0 else round("AMsrUseWBkWh"::numeric(15,5), 4-floor(log(abs("AMsrUseWBkWh")))::INT) end) as "AMsrUseWBkWh",
(case "AMsrUseWBtherm" when 0 then 0 else round("AMsrUseWBtherm"::numeric(15,5), 4-floor(log(abs("AMsrUseWBtherm")))::INT) end) as "AMsrUseWBtherm",
"APreUseEUkWh",
"APreUseEUtherm",
"AStdUseEUkWh",
"AStdUseEUtherm",
"AMsrUseEUkWh",
"AMsrUseEUtherm"


FROM
meas_impacts_vint_wtd;

--only use when ElecImpactProfileID / GasImpactProfileID needs to be populated
--LEFT JOIN "ImpactProfiles" on "ImpactProfiles"."EnergyImpactID" = meas_impacts_vint_wtd."EnergyImpactID";

ALTER TABLE "meas_impacts_2024_com"
ALTER COLUMN "EnergyImpactID" SET NOT NULL,
ALTER COLUMN "PA" SET NOT NULL,
ALTER COLUMN "BldgType" SET NOT NULL,
ALTER COLUMN "BldgVint" SET NOT NULL,
ALTER COLUMN "BldgLoc" SET NOT NULL,
ALTER COLUMN "BldgHVAC" SET NOT NULL,
ADD PRIMARY KEY ("EnergyImpactID", "PA", "BldgType", "BldgVint", "BldgLoc", "BldgHVAC");