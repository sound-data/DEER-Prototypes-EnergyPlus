--SET search_path TO "MC_results_database";
DROP TABLE IF EXISTS "wts_com_bldg";
CREATE TABLE "wts_com_bldg" (
"PA" varchar(255) NOT NULL,
"BldgType" varchar(255) NOT NULL,
"BldgVint" varchar(255) NOT NULL,
"BldgLoc" varchar NOT NULL,
"sum_bldg" numeric(16,4),
PRIMARY KEY ("PA", "BldgType", "BldgVint", "BldgLoc")
)
;
