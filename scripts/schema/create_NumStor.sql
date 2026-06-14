--SET search_path TO "MC_results_database";
CREATE TABLE IF NOT EXISTS "NumStor" (
  "BldgType" VARCHAR(255) NOT NULL,
  "VintYear" VARCHAR(255) NOT NULL,
  "BldgLoc" VARCHAR(255) NOT NULL,
  "numstor" REAL,
  PRIMARY KEY ("BldgType","VintYear","BldgLoc")
);
