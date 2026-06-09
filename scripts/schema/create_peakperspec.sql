--SET search_path TO "MC_results_database";
CREATE TABLE IF NOT EXISTS "peakperspec" (
"BldgLoc"  VARCHAR(255),
"PkDay"  SMALLINT,
"PkHr"  SMALLINT,
PRIMARY KEY ("BldgLoc")
);
