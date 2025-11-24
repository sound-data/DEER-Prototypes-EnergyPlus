
-- ----------------------------
-- Table structure for peakperspec
-- ----------------------------
-- 2025-09-29 Nicholas Fette (Solaris Technical): Don't hard-code the search_path.

-- Uncomment this line if you need to run this query manually.
--SET search_path TO "MC_results_database";

-- Uncomment this line if you need to redefine this table.
--DROP TABLE IF EXISTS "peakperspec";

CREATE TABLE IF NOT EXISTS "peakperspec" (
"BldgLoc" text COLLATE "default",
"PkDay" text COLLATE "default",
"PkHr" text COLLATE "default",
-- 2025-09-29 Nicholas Fette (Solaris Technical)
-- Cause explicit error if user tries to load duplicate data. This helps avoid accidental mistakes.
PRIMARY KEY ("BldgLoc")
)
WITH (OIDS=FALSE)
;
-- 2025-09-29 Nicholas Fette (Solaris Technical)
-- Don't import the data via the schema definition, but instead use the CSV file after creating the table structure.
