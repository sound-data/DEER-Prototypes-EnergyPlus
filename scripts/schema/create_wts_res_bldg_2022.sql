--SET search_path TO "MC_results_database";
DROP TABLE IF EXISTS "wts_res_bldg_2022";
CREATE TABLE "wts_res_bldg_2022" (
"bldgtype" varchar(255) NOT NULL,
"era" varchar(255) NOT NULL,
"bldgloc" varchar NOT NULL,
"sum_bldg" numeric(16,4),
PRIMARY KEY ("bldgtype", "era", "bldgloc")
)
;
