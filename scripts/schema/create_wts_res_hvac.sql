--SET search_path TO "MC_results_database";
CREATE TABLE IF NOT EXISTS "wts_res_hvac" (
"pa" varchar(255) NOT NULL,
"bldgtype" varchar(255) NOT NULL,
"bldgloc" varchar(255) NOT NULL,
"bldghvac" varchar(255) NOT NULL,
"wtval" numeric(16,4) NOT NULL,
PRIMARY KEY ("pa", "bldgtype", "bldgloc", "bldghvac")
)
;
