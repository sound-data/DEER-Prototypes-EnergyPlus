-- Table: MC_results_database.current_msr_mat

-- DROP TABLE "MC_results_database".current_msr_mat;

CREATE TABLE IF NOT EXISTS "MC_results_database".current_msr_mat
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
    "NormUnit" text COLLATE pg_catalog."default"
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;