--2022 new post-processing, 
--Residential Step 1: Weight annual consumption based on number of stories (no more thermostat weights)
--need to add union statement when dealing with MFm / DMo data

SET search_path TO "MC_results_database";

DROP TABLE IF EXISTS sim_annual_twtd_2022;
CREATE TABLE sim_annual_twtd_2022 AS
SELECT
sim_annual."TechID",
sim_annual."SizingID",
sim_annual."BldgType",
sim_annual."BldgVint",
sim_annual."BldgLoc",
sim_annual."BldgHVAC",
sim_annual.tstat,
sim_annual.normunit,
sim_annual.numunits,
(sim_annual.kwh_tot)::NUMERIC(15,3) as kwh_tot,
(sim_annual.kwh_ltg)::NUMERIC(15,3) as kwh_ltg,
(sim_annual.kwh_task)::NUMERIC(15,3) as kwh_task,
(sim_annual.kwh_equip)::NUMERIC(15,3) as kwh_equip,
(sim_annual.kwh_htg)::NUMERIC(15,3) as kwh_htg,
(sim_annual.kwh_clg)::NUMERIC(15,3) as kwh_clg,
(sim_annual.kwh_twr)::NUMERIC(15,3) as kwh_twr,
(sim_annual.kwh_aux)::NUMERIC(15,3) as kwh_aux,
(sim_annual.kwh_vent)::NUMERIC(15,3) as kwh_vent,
(sim_annual.kwh_venthtg)::NUMERIC(15,3) as kwh_venthtg,
(sim_annual.kwh_ventclg)::NUMERIC(15,3) as kwh_ventclg,
(sim_annual.kwh_refg)::NUMERIC(15,3) as kwh_refg,
(sim_annual.kwh_hpsup)::NUMERIC(15,3) as kwh_hpsup,
(sim_annual.kwh_shw)::NUMERIC(15,3) as kwh_shw,
(sim_annual.kwh_ext)::NUMERIC(15,3) as kwh_ext,
(sim_annual.thm_tot)::NUMERIC(15,4) as thm_tot,
(sim_annual.thm_equip)::NUMERIC(15,4) as thm_equip,
(sim_annual.thm_htg)::NUMERIC(15,4) as thm_htg,
(sim_annual.thm_shw)::NUMERIC(15,4) as thm_shw,
(sim_annual.deskw_ltg)::NUMERIC(15,3) as deskw_ltg,
(sim_annual.deskw_equ)::NUMERIC(15,3) as deskw_equ,
lastmod
from sim_annual

UNION

SELECT
sfm_annual."TechID",
sfm_annual."SizingID",
sfm_annual."BldgType",
sfm_annual."BldgVint",
sfm_annual."BldgLoc",
sfm_annual."BldgHVAC",
sfm_annual.tstat,
sfm_annual.normunit,
sfm_annual.numunits,
((kwh_tot1 * (2 - numstor) + kwh_tot2 * (numstor - 1)) )::numeric(15,3) AS kwh_tot,
((kwh_ltg1 * (2 - numstor) + kwh_ltg2 * (numstor - 1)) )::NUMERIC(15,3) AS kwh_ltg,
((kwh_task1 * (2 - numstor) + kwh_task2 * (numstor - 1)) )::numeric(15,3) AS kwh_task,
((kwh_equip1 * (2 - numstor) + kwh_equip2 * (numstor - 1)) )::numeric(15,3) AS kwh_equip,
((kwh_htg1 * (2 - numstor) + kwh_htg2 * (numstor - 1)) )::numeric(15,3) AS kwh_htg,
((kwh_clg1 * (2 - numstor) + kwh_clg2 * (numstor - 1)) )::numeric(15,3) AS kwh_clg,
((kwh_twr1 * (2 - numstor) + kwh_twr2 * (numstor - 1)) )::numeric(15,3) AS kwh_twr,
((kwh_aux1 * (2 - numstor) + kwh_aux2 * (numstor - 1)) )::numeric(15,3) AS kwh_aux,
((kwh_vent1 * (2 - numstor) + kwh_vent2 * (numstor - 1)) )::numeric(15,3) AS kwh_vent,
(((kwh_venthtg1a + kwh_venthtg1b) * (2 - numstor) + (kwh_venthtg2a + kwh_venthtg2b)* (numstor - 1)) )::numeric(15,3) AS kwh_venthtg,
(((kwh_ventclg1a + kwh_ventclg1b) * (2 - numstor) + (kwh_ventclg2a + kwh_ventclg2b)* (numstor - 1)) )::numeric(15,3) AS kwh_ventclg,
((kwh_refg1 * (2 - numstor) + kwh_refg2 * (numstor - 1)) )::numeric(15,3) AS kwh_refg,
((kwh_hpsup1 * (2 - numstor) + kwh_hpsup2 * (numstor - 1)) )::numeric(15,3) AS kwh_hpsup,
((kwh_shw1 * (2 - numstor) + kwh_shw2 * (numstor - 1)) )::numeric(15,3) AS kwh_shw,
((kwh_ext1 * (2 - numstor) + kwh_ext2 * (numstor - 1)) )::numeric(15,3) AS kwh_ext,
((thm_tot1 * (2 - numstor) + thm_tot2 * (numstor - 1)) )::numeric(15,4) AS thm_tot,
((thm_equip1 * (2 - numstor) + thm_equip2 * (numstor - 1)) )::numeric(15,4) AS thm_equip,
((thm_htg1 * (2 - numstor) + thm_htg2 * (numstor - 1)) )::numeric(15,4) AS thm_htg,
((thm_shw1 * (2 - numstor) + thm_shw2 * (numstor - 1)) )::numeric(15,4) AS thm_shw,
-1 as deskw_ltg,
-1 as deskw_equ,
lastmod
from sfm_annual
JOIN "NumStor" on "NumStor"."VintYear" = sfm_annual."BldgVint" and "NumStor"."BldgLoc" = sfm_annual."BldgLoc"

ORDER BY 
"TechID",
"SizingID",
"BldgType",
"BldgVint",
"BldgLoc",
"BldgHVAC",
tstat;
