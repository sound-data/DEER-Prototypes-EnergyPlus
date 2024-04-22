--2022 new post-processing, 
--Residential Step 2: Weight hourly consumption (WB) based on number of stories (no more thermostat weights)

SET search_path TO "MC_results_database";

DROP TABLE IF EXISTS sim_hourly_twtd_2022;
CREATE TABLE sim_hourly_twtd_2022 AS

SELECT
sim_hourly_wb."TechID",
sim_hourly_wb."SizingID",
sim_hourly_wb."BldgType",
sim_hourly_wb."BldgVint",
sim_hourly_wb."BldgLoc",
sim_hourly_wb."BldgHVAC",
sim_hourly_wb.tstat,
sim_hourly_wb.enduse,
sim_hourly_wb.daynum::int2,
(hr01)::numeric(15,3) AS hr01,
(hr02)::numeric(15,3) AS hr02,
(hr03)::numeric(15,3) AS hr03,
(hr04)::numeric(15,3) AS hr04,
(hr05)::numeric(15,3) AS hr05,
(hr06)::numeric(15,3) AS hr06,
(hr07)::numeric(15,3) AS hr07,
(hr08)::numeric(15,3) AS hr08,
(hr09)::numeric(15,3) AS hr09,
(hr10)::numeric(15,3) AS hr10,
(hr11)::numeric(15,3) AS hr11,
(hr12)::numeric(15,3) AS hr12,
(hr13)::numeric(15,3) AS hr13,
(hr14)::numeric(15,3) AS hr14,
(hr15)::numeric(15,3) AS hr15,
(hr16)::numeric(15,3) AS hr16,
(hr17)::numeric(15,3) AS hr17,
(hr18)::numeric(15,3) AS hr18,
(hr19)::numeric(15,3) AS hr19,
(hr20)::numeric(15,3) AS hr20,
(hr21)::numeric(15,3) AS hr21,
(hr22)::numeric(15,3) AS hr22,
(hr23)::numeric(15,3) AS hr23,
(hr24)::numeric(15,3) AS hr24
from sim_hourly_wb

UNION

SELECT
sfm_hourly_wb."TechID",
sfm_hourly_wb."SizingID",
sfm_hourly_wb."BldgType",
sfm_hourly_wb."BldgVint",
sfm_hourly_wb."BldgLoc",
sfm_hourly_wb."BldgHVAC",
sfm_hourly_wb.tstat,
sfm_hourly_wb.enduse,
sfm_hourly_wb.daynum::int2,
((hr01a * (2 - numstor) + hr01b * (numstor - 1)))::numeric(15,3) AS hr01,
((hr02a * (2 - numstor) + hr02b * (numstor - 1)))::numeric(15,3) AS hr02,
((hr03a * (2 - numstor) + hr03b * (numstor - 1)))::numeric(15,3) AS hr03,
((hr04a * (2 - numstor) + hr04b * (numstor - 1)))::numeric(15,3) AS hr04,
((hr05a * (2 - numstor) + hr05b * (numstor - 1)))::numeric(15,3) AS hr05,
((hr06a * (2 - numstor) + hr06b * (numstor - 1)))::numeric(15,3) AS hr06,
((hr07a * (2 - numstor) + hr07b * (numstor - 1)))::numeric(15,3) AS hr07,
((hr08a * (2 - numstor) + hr08b * (numstor - 1)))::numeric(15,3) AS hr08,
((hr09a * (2 - numstor) + hr09b * (numstor - 1)))::numeric(15,3) AS hr09,
((hr10a * (2 - numstor) + hr10b * (numstor - 1)))::numeric(15,3) AS hr10,
((hr11a * (2 - numstor) + hr11b * (numstor - 1)))::numeric(15,3) AS hr11,
((hr12a * (2 - numstor) + hr12b * (numstor - 1)))::numeric(15,3) AS hr12,
((hr13a * (2 - numstor) + hr13b * (numstor - 1)))::numeric(15,3) AS hr13,
((hr14a * (2 - numstor) + hr14b * (numstor - 1)))::numeric(15,3) AS hr14,
((hr15a * (2 - numstor) + hr15b * (numstor - 1)))::numeric(15,3) AS hr15,
((hr16a * (2 - numstor) + hr16b * (numstor - 1)))::numeric(15,3) AS hr16,
((hr17a * (2 - numstor) + hr17b * (numstor - 1)))::numeric(15,3) AS hr17,
((hr18a * (2 - numstor) + hr18b * (numstor - 1)))::numeric(15,3) AS hr18,
((hr19a * (2 - numstor) + hr19b * (numstor - 1)))::numeric(15,3) AS hr19,
((hr20a * (2 - numstor) + hr20b * (numstor - 1)))::numeric(15,3) AS hr20,
((hr21a * (2 - numstor) + hr21b * (numstor - 1)))::numeric(15,3) AS hr21,
((hr22a * (2 - numstor) + hr22b * (numstor - 1)))::numeric(15,3) AS hr22,
((hr23a * (2 - numstor) + hr23b * (numstor - 1)))::numeric(15,3) AS hr23,
((hr24a * (2 - numstor) + hr24b * (numstor - 1)))::numeric(15,3) AS hr24
from sfm_hourly_wb
JOIN "NumStor" on "NumStor"."VintYear" = sfm_hourly_wb."BldgVint" and "NumStor"."BldgLoc" = sfm_hourly_wb."BldgLoc"
;
