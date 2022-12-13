--finish weighting hourly results with numbldgs
SET search_path TO "MC_results_database";
DROP TABLE IF EXISTS sim_hourly_wb_wtd;
CREATE TABLE sim_hourly_wb_wtd AS 
SELECT
"TechID",
"SizingID",
"BldgType",
"BldgVint",
"BldgLoc",
"BldgHVAC",
daynum,
(sum(hr01)/numbldgs)::numeric(15,3) as hr01,
(sum(hr02)/numbldgs)::numeric(15,3) as hr02,
(sum(hr03)/numbldgs)::numeric(15,3) as hr03,
(sum(hr04)/numbldgs)::numeric(15,3) as hr04,
(sum(hr05)/numbldgs)::numeric(15,3) as hr05,
(sum(hr06)/numbldgs)::numeric(15,3) as hr06,
(sum(hr07)/numbldgs)::numeric(15,3) as hr07,
(sum(hr08)/numbldgs)::numeric(15,3) as hr08,
(sum(hr09)/numbldgs)::numeric(15,3) as hr09,
(sum(hr10)/numbldgs)::numeric(15,3) as hr10,
(sum(hr11)/numbldgs)::numeric(15,3) as hr11,
(sum(hr12)/numbldgs)::numeric(15,3) as hr12,
(sum(hr13)/numbldgs)::numeric(15,3) as hr13,
(sum(hr14)/numbldgs)::numeric(15,3) as hr14,
(sum(hr15)/numbldgs)::numeric(15,3) as hr15,
(sum(hr16)/numbldgs)::numeric(15,3) as hr16,
(sum(hr17)/numbldgs)::numeric(15,3) as hr17,
(sum(hr18)/numbldgs)::numeric(15,3) as hr18,
(sum(hr19)/numbldgs)::numeric(15,3) as hr19,
(sum(hr20)/numbldgs)::numeric(15,3) as hr20,
(sum(hr21)/numbldgs)::numeric(15,3) as hr21,
(sum(hr22)/numbldgs)::numeric(15,3) as hr22,
(sum(hr23)/numbldgs)::numeric(15,3) as hr23,
(sum(hr24)/numbldgs)::numeric(15,3) as hr24
from sim_hourly_twtd_2022
JOIN "NumBldgs" on "NumBldgs".bldgtype = sim_hourly_twtd_2022."BldgType"
GROUP BY  
"TechID",
"SizingID",
"BldgType",
"BldgVint",
"BldgLoc",
"BldgHVAC",
 daynum,
 numbldgs
ORDER BY
"TechID",
"SizingID",
"BldgType",
"BldgVint",
"BldgLoc",
"BldgHVAC",
 daynum;

-- Add primary key to table:
ALTER TABLE "sim_hourly_wb_wtd"
ALTER COLUMN "TechID" SET NOT NULL,
ALTER COLUMN "SizingID" SET NOT NULL,
ALTER COLUMN "BldgType" SET NOT NULL,
ALTER COLUMN "BldgVint" SET NOT NULL,
ALTER COLUMN "BldgLoc" SET NOT NULL,
ALTER COLUMN "BldgHVAC" SET NOT NULL,
ALTER COLUMN daynum SET NOT NULL,
ADD PRIMARY KEY ("TechID", "SizingID", "BldgType", "BldgVint", "BldgLoc", "BldgHVAC",daynum);
