-- Calculate the measure impacts (per dwelling, per numunit) for the measures specified in the current_msr_mat table.
--  Note: use more decimals than necessary, as they will be rounded in the final query of the process
SET search_path TO "MC_results_database";
DROP TABLE IF EXISTS meas_impacts_vint_wtd;
CREATE TABLE meas_impacts_vint_wtd AS 
SELECT
current_msr_mat."MeasureID" as "EnergyImpactID",
'DEER2024'::text as "Version",
'D24_E+_Com_v1'::text as "VersionSource", --Note Version must reflect prototype version used (COP, sizing, etc.) (Note version)
date_trunc('second', now()) as "LastMod",
'Any'::text as "PA",
current_msr_mat."BldgType",
current_msr_mat."BldgVint",
current_msr_mat."BldgLoc",
current_msr_mat."BldgHVAC",
msr.normunit as "NormUnit",
msr.numunits as "NumUnit",
msr.measarea as "MeasArea",
'None'::text as "ScaleBasis",
-- Pre-Existing case Values:
--pre.kwh_tot as "PreWBkWh", 
--ppk.bldg_kw25::numeric(15,3) as "PreWBkW25", 
--ppk.bldg_kw49::numeric(15,3) as "PreWBkW49", 
--pre.thm_tot::Numeric(15,4) as "PreWBthm",
-- DEER whole-building, above pre-exising impacts
case (pre.kwh_tot - msr.kwh_tot) when 0 then 0 
  else round(((pre.kwh_tot - msr.kwh_tot)/msr.numunits)::Numeric(15,6),(2-floor(log(abs(((pre.kwh_tot - msr.kwh_tot)/msr.numunits)))))::SMALLINT) end as "APreWBkWh", 
-- case (ppk.bldg_kw25 - mpk.bldg_kw25) when 0 then 0 
  -- else round(((ppk.bldg_kw25 - mpk.bldg_kw25)/msr.numunits)::Numeric(15,6),(2-floor(log(abs(((ppk.bldg_kw25 - mpk.bldg_kw25)/msr.numunits)))))::SMALLINT) end as "APreWBkW25", 
case (ppk.bldg_kw49 - mpk.bldg_kw49) when 0 then 0 
  else round(((ppk.bldg_kw49 - mpk.bldg_kw49)/msr.numunits)::Numeric(15,6),(2-floor(log(abs(((ppk.bldg_kw49 - mpk.bldg_kw49)/msr.numunits)))))::SMALLINT) end as "APreWBkW", 
case (pre.thm_tot - msr.thm_tot) when 0 then 0 
  else round(((pre.thm_tot - msr.thm_tot)/msr.numunits)::Numeric(15,6),(2-floor(log(abs(((pre.thm_tot - msr.thm_tot)/1e5/msr.numunits)))))::SMALLINT) end as "APreWBtherm", 
-- DEER whole-building, above code/standard impacts
case (std.kwh_tot - msr.kwh_tot) when 0 then 0 
  else round(((std.kwh_tot - msr.kwh_tot)/msr.numunits)::Numeric(15,6),(2-floor(log(abs(((std.kwh_tot - msr.kwh_tot)/msr.numunits)))))::SMALLINT) end as "AStdWBkWh", 
-- case (spk.bldg_kw25 - mpk.bldg_kw25) when 0 then 0 
  -- else round(((spk.bldg_kw25 - mpk.bldg_kw25)/msr.numunits)::Numeric(15,6),(2-floor(log(abs(((spk.bldg_kw25 - mpk.bldg_kw25)/msr.numunits)))))::SMALLINT) end as "AStdWBkW25", 
case (spk.bldg_kw49 - mpk.bldg_kw49) when 0 then 0 
  else round(((spk.bldg_kw49 - mpk.bldg_kw49)/msr.numunits)::Numeric(15,6),(2-floor(log(abs(((spk.bldg_kw49 - mpk.bldg_kw49)/msr.numunits)))))::SMALLINT) end as "AStdWBkW", 
case (std.thm_tot - msr.thm_tot) when 0 then 0 
  else round(((std.thm_tot - msr.thm_tot)/msr.numunits)::Numeric(15,6),(2-floor(log(abs(((std.thm_tot - msr.thm_tot)/1e5/msr.numunits)))))::SMALLINT) end as "AStdWBtherm",


--New Field Names for pre/std/msr case consumptions: Added for 2022/2023 modeling from EnergyPlus
--note WB and EU difference
--sig fig change. 4 = 5 digits - 1 in formula
((pre.kwh_tot)/msr.numunits)::numeric(15,5) as "APreUseWBkWh",
((pre.thm_tot)/msr.numunits)::numeric(15,5) as "APreUseWBtherm",
((std.kwh_tot)/msr.numunits)::numeric(15,5) as "AStdUseWBkWh",
((std.thm_tot)/msr.numunits)::numeric(15,5) as "AStdUseWBtherm",
((msr.kwh_tot)/msr.numunits)::numeric(15,5) as "AMsrUseWBkWh",
((msr.thm_tot)/msr.numunits)::numeric(15,5) as "AMsrUseWBtherm",

NULL::numeric(15,5) as "APreUseEUkWh",
NULL::numeric(15,5) as "APreUseEUtherm",
NULL::numeric(15,5) as "AStdUseEUkWh",
NULL::numeric(15,5) as "AStdUseEUtherm",
NULL::numeric(15,5) as "AMsrUseEUkWh",
NULL::numeric(15,5) as "AMsrUseEUtherm"

FROM current_msr_mat
LEFT JOIN sim_annual msr on 
  msr."TechID"   = current_msr_mat."MeasTechID" AND  
  msr."SizingID" = current_msr_mat."MsrSizingID" AND  
  msr."BldgType" = current_msr_mat."BldgType" AND
  msr."BldgVint" = current_msr_mat."BldgVint" AND  
  msr."BldgLoc"  = current_msr_mat."BldgLoc" AND  
  msr."BldgHVAC" = current_msr_mat."BldgHVAC"
LEFT JOIN sim_annual pre on 
  pre."TechID"   = current_msr_mat."PreTechID" AND  
  pre."SizingID" = current_msr_mat."PreSizingID" AND  
  pre."BldgType" = current_msr_mat."BldgType" AND
  pre."BldgVint" = current_msr_mat."BldgVint" AND  
  pre."BldgLoc"  = current_msr_mat."BldgLoc" AND  
  pre."BldgHVAC" = current_msr_mat."BldgHVAC"
LEFT JOIN sim_annual std on 
  std."TechID"   = current_msr_mat."StdTechID" AND  
  std."SizingID" = current_msr_mat."StdSizingID" AND  
  std."BldgType" = current_msr_mat."BldgType" AND
  std."BldgVint" = current_msr_mat."BldgVint" AND  
  std."BldgLoc"  = current_msr_mat."BldgLoc" AND  
  std."BldgHVAC" = current_msr_mat."BldgHVAC"
LEFT JOIN sim_peakper mpk ON
  mpk."TechID"   = current_msr_mat."MeasTechID" AND  
  mpk."SizingID" = current_msr_mat."MsrSizingID" AND  
  mpk."BldgType" = current_msr_mat."BldgType" AND
  mpk."BldgVint" = current_msr_mat."BldgVint" AND  
  mpk."BldgLoc"  = current_msr_mat."BldgLoc" AND  
  mpk."BldgHVAC" = current_msr_mat."BldgHVAC"
LEFT JOIN sim_peakper ppk ON
  ppk."TechID"   = current_msr_mat."PreTechID" AND  
  ppk."SizingID" = current_msr_mat."PreSizingID" AND  
  ppk."BldgType" = current_msr_mat."BldgType" AND
  ppk."BldgVint" = current_msr_mat."BldgVint" AND  
  ppk."BldgLoc"  = current_msr_mat."BldgLoc" AND  
  ppk."BldgHVAC" = current_msr_mat."BldgHVAC"
LEFT JOIN sim_peakper spk ON
  spk."TechID"   = current_msr_mat."StdTechID" AND  
  spk."SizingID" = current_msr_mat."StdSizingID" AND  
  spk."BldgType" = current_msr_mat."BldgType" AND
  spk."BldgVint" = current_msr_mat."BldgVint" AND  
  spk."BldgLoc"  = current_msr_mat."BldgLoc" AND  
  spk."BldgHVAC" = current_msr_mat."BldgHVAC"

ORDER BY 
 current_msr_mat."MeasureID",current_msr_mat."BldgType",current_msr_mat."BldgHVAC",current_msr_mat."BldgVint",current_msr_mat."BldgLoc"