--finish weighting annual results with numbldgs
SET search_path TO "MC_results_database";
DROP TABLE IF EXISTS sim_annual_wtd;
CREATE TABLE sim_annual_wtd AS 

SELECT
"TechID",
"SizingID",
sim_annual_twtd_2022."BldgType",
sim_annual_twtd_2022."BldgVint",
sim_annual_twtd_2022."BldgLoc",
"BldgHVAC",
normunit,
numunits, --numunit is already per dwelling from python script, gets simply carried over
("FloorArea_2022"."Area"/numbldgs)::NUMERIC(15,0) as "measarea",  --this calculates per dwelling area for each building type
(sum(kwh_tot)/numbldgs)::NUMERIC(15,3) as kwh_tot,
(sum(kwh_ltg)/numbldgs)::NUMERIC(15,3) as kwh_ltg,
(sum(kwh_task)/numbldgs)::NUMERIC(15,3) as kwh_task,
(sum(kwh_equip)/numbldgs)::NUMERIC(15,3) as kwh_equip,
(sum(kwh_htg)/numbldgs)::NUMERIC(15,3) as kwh_htg,
(sum(kwh_clg)/numbldgs)::NUMERIC(15,3) as kwh_clg,
(sum(kwh_twr)/numbldgs)::NUMERIC(15,3) as kwh_twr,
(sum(kwh_aux)/numbldgs)::NUMERIC(15,3) as kwh_aux,
(sum(kwh_vent)/numbldgs)::NUMERIC(15,3) as kwh_vent,
(sum(kwh_venthtg)/numbldgs)::NUMERIC(15,3) as kwh_venthtg,
(sum(kwh_ventclg)/numbldgs)::NUMERIC(15,3) as kwh_ventclg,
(sum(kwh_refg)/numbldgs)::NUMERIC(15,3) as kwh_refg,
(sum(kwh_hpsup)/numbldgs)::NUMERIC(15,3) as kwh_hpsup,
(sum(kwh_shw)/numbldgs)::NUMERIC(15,3) as kwh_shw,
(sum(kwh_ext)/numbldgs)::NUMERIC(15,3) as kwh_ext,
(sum(thm_tot)/numbldgs)::NUMERIC(15,4) as thm_tot,
(sum(thm_equip)/numbldgs)::NUMERIC(15,4) as thm_equip,
(sum(thm_htg)/numbldgs)::NUMERIC(15,4) as thm_htg,
(sum(thm_shw)/numbldgs)::NUMERIC(15,4) as thm_shw,
(sum(deskw_ltg)/numbldgs)::NUMERIC(15,3) as deskw_ltg,
(sum(deskw_equ)/numbldgs)::NUMERIC(15,3) as deskw_equ
from sim_annual_twtd_2022
JOIN "NumBldgs" on "NumBldgs".bldgtype = sim_annual_twtd_2022."BldgType"
JOIN "FloorArea_2022" on "FloorArea_2022"."BldgType" = sim_annual_twtd_2022."BldgType" AND 
                    "FloorArea_2022"."BldgVint" = sim_annual_twtd_2022."BldgVint" AND 
                    "FloorArea_2022"."BldgLoc" = sim_annual_twtd_2022."BldgLoc"
GROUP BY  
"TechID",
"SizingID",
sim_annual_twtd_2022."BldgType",
sim_annual_twtd_2022."BldgVint",
sim_annual_twtd_2022."BldgLoc",
"BldgHVAC",
normunit,
numunits,
numbldgs,
"FloorArea_2022"."Area"
ORDER BY
"TechID",
"SizingID",
sim_annual_twtd_2022."BldgType",
sim_annual_twtd_2022."BldgVint",
sim_annual_twtd_2022."BldgLoc",
"BldgHVAC";

-- Add primary key to table:
ALTER TABLE "sim_annual_wtd"
ALTER COLUMN "TechID" SET NOT NULL,
ALTER COLUMN "SizingID" SET NOT NULL,
ALTER COLUMN "BldgType" SET NOT NULL,
ALTER COLUMN "BldgVint" SET NOT NULL,
ALTER COLUMN "BldgLoc" SET NOT NULL,
ALTER COLUMN "BldgHVAC" SET NOT NULL,
ADD PRIMARY KEY ("TechID", "SizingID", "BldgType", "BldgVint", "BldgLoc", "BldgHVAC");