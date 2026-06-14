--SET search_path TO "MC_results_database";
CREATE TABLE IF NOT EXISTS "FloorArea_2022" (
  "BldgType" VARCHAR(255) NOT NULL,
  "BldgVint" VARCHAR(255) NOT NULL,
  "BldgLoc" VARCHAR(255) NOT NULL,
  "Area" REAL,
  PRIMARY KEY ("BldgType","BldgVint","BldgLoc")
);
