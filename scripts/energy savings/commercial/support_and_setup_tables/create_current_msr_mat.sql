-- 2025-09-29 Nicholas Fette (Solaris Technical): Don't hard-code the search_path.

-- Uncomment this line if you need to run this query manually.
--SET search_path TO "MC_results_database";

-- Uncomment this line if you need to redefine this table.
-- DROP TABLE IF EXISTS current_msr_mat;

CREATE TABLE IF NOT EXISTS current_msr_mat
(
    "MeasureID" text COLLATE pg_catalog."default",
    "BldgType" text COLLATE pg_catalog."default",
    "BldgVint" text COLLATE pg_catalog."default",
    "BldgLoc" text COLLATE pg_catalog."default",
    "BldgHVAC" text COLLATE pg_catalog."default",
    tstat text COLLATE pg_catalog."default",
    "PreTechID" text COLLATE pg_catalog."default",
    "PreSizingID" text COLLATE pg_catalog."default",
    "StdTechID" text COLLATE pg_catalog."default",
    "StdSizingID" text COLLATE pg_catalog."default",
    "MeasTechID" text COLLATE pg_catalog."default",
    "MsrSizingID" text COLLATE pg_catalog."default",
    "SizingSrc" text COLLATE pg_catalog."default",
    "EU_HrRepVar" text COLLATE pg_catalog."default",
    "NormUnit" text COLLATE pg_catalog."default",
    -- 2025-09-29 Nicholas Fette (Solaris Technical)
    -- Cause explicit error if user tries to load duplicate data. This helps avoid accidental mistakes.
    PRIMARY KEY ("MeasureID","BldgType","BldgVint","BldgLoc","BldgHVAC","tstat","NormUnit")
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;
