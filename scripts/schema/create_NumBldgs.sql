--SET search_path TO "MC_results_database";
CREATE TABLE IF NOT EXISTS "NumBldgs" (
  "bldgtype" VARCHAR(255) NOT NULL,
  "numbldgs" REAL,
  PRIMARY KEY ("bldgtype")
);
