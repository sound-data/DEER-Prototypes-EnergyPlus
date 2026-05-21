-- Table: MC_results_database.sim_hourly_wb

-- DROP TABLE "MC_results_database".sim_hourly_wb;

CREATE TABLE IF NOT EXISTS "MC_results_database".sim_hourly_wb
(
    "TechID" text COLLATE pg_catalog."default",
    "SizingID" text COLLATE pg_catalog."default",
    "BldgType" text COLLATE pg_catalog."default",
    "BldgVint" text COLLATE pg_catalog."default",
    "BldgLoc" text COLLATE pg_catalog."default",
    "BldgHVAC" text COLLATE pg_catalog."default",
    tstat text COLLATE pg_catalog."default",
    enduse text COLLATE pg_catalog."default",
    daynum integer,
    hr01 real,
    hr02 real,
    hr03 real,
    hr04 real,
    hr05 real,
    hr06 real,
    hr07 real,
    hr08 real,
    hr09 real,
    hr10 real,
    hr11 real,
    hr12 real,
    hr13 real,
    hr14 real,
    hr15 real,
    hr16 real,
    hr17 real,
    hr18 real,
    hr19 real,
    hr20 real,
    hr21 real,
    hr22 real,
    hr23 real,
    hr24 real,
    lastmod text COLLATE pg_catalog."default"
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;