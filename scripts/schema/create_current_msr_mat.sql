--SET search_path TO "MC_results_database";
CREATE TABLE IF NOT EXISTS "current_msr_mat"(
  "MeasureID" VARCHAR(255),
  "BldgType" VARCHAR(255),
  "BldgVint" VARCHAR(255),
  "BldgLoc" VARCHAR(255),
  "BldgHVAC" VARCHAR(255),
  "tstat" SMALLINT,
  "PreTechID" VARCHAR(255),
  "PreSizingID" VARCHAR(255),
  "StdTechID" VARCHAR(255),
  "StdSizingID" VARCHAR(255),
  "MeasTechID" VARCHAR(255),
  "MsrSizingID" VARCHAR(255),
  "SizingSrc" VARCHAR(255),
  "EU_HrRepVar" VARCHAR(255),
  "NormUnit" VARCHAR(255),
  PRIMARY KEY ("MeasureID","BldgType","BldgVint","BldgLoc","BldgHVAC","tstat","NormUnit")
);
