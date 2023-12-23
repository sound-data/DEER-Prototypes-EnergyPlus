--for electric (predominantely) sites (where MeasureID starts with "RE" or "NE"
--different rules are applied if gas sites (MeasureID starts with "RG" or "NG")
--3/20/20, instead of changing records, make duplicate and change to "any"

SET search_path TO "MC_results_database";
DROP TABLE IF EXISTS meas_impacts_pa_corrected;
CREATE TABLE meas_impacts_pa_corrected AS 
SELECT
*
FROM meas_impacts_2023_com --input whatever table needs to be processed here (after all weighting had been done)

--below for predominantely electric measures
where ("PA"='PGE' and "BldgLoc" IN ('CZ01','CZ02','CZ03','CZ04','CZ05','CZ11','CZ12','CZ13'))
OR ("PA" = 'SCE' and "BldgLoc" IN ('CZ06'))
OR ("PA" = 'SDG' and "BldgLoc" IN ('CZ07'))
OR ("PA" = 'SCE' and "BldgLoc" IN ('CZ08','CZ10'))	
OR ("PA" = 'SCE' and "BldgLoc" IN ('CZ09'))								  
OR ("PA" = 'SCE' and "BldgLoc" IN ('CZ14','CZ15','CZ16'))											  
;
														  															  															 															  
UPDATE meas_impacts_pa_corrected
SET "PA"='Any';
								   
INSERT INTO meas_impacts_2023_com
SELECT
*
FROM meas_impacts_pa_corrected

ORDER BY
"EnergyImpactID",
"PA",
"BldgType",
"BldgVint",
"BldgLoc",
"BldgHVAC";



-----------for BldgType = Com only records, use this:-----------

/* SET search_path TO "MC_results_database";
DROP TABLE IF EXISTS meas_impacts_pa_corrected;
CREATE TABLE meas_impacts_pa_corrected AS 
SELECT
*
FROM meas_impacts_2020_com --input whatever table needs to be processed here (after all weighting had been done)

--below for predominantely electric measures
where ("PA"='PGE' and "BldgLoc" IN ('CZ01','CZ02','CZ03','CZ04','CZ05','CZ11','CZ12','CZ13') and "BldgType"='Com')
OR ("PA" = 'SCE' and "BldgLoc" IN ('CZ06') and "BldgType"='Com')
OR ("PA" = 'SDG' and "BldgLoc" IN ('CZ07') and "BldgType"='Com')
OR ("PA" = 'SCE' and "BldgLoc" IN ('CZ08','CZ10') and "BldgType"='Com')	
OR ("PA" = 'SCE' and "BldgLoc" IN ('CZ09') and "BldgType"='Com')								  
OR ("PA" = 'SCE' and "BldgLoc" IN ('CZ14','CZ15','CZ16') and "BldgType"='Com')											  
;
														  															  															 															  
UPDATE meas_impacts_pa_corrected
SET "PA"='Any';
								   
INSERT INTO meas_impacts_2020_com
SELECT
*
FROM meas_impacts_pa_corrected

ORDER BY 
"EnergyImpactID",
"PA",
"BldgType",
"BldgVint",
"BldgLoc",
"BldgHVAC"; */
