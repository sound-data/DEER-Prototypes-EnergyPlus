-- 2025-09-29 Nicholas Fette (Solaris Technical): Don't hard-code the search_path.

-- Uncomment this line if you need to run this query manually.
--SET search_path TO "MC_results_database";

-- Uncomment this line if you need to redefine this table.
--DROP TABLE IF EXISTS "sim_annual";

CREATE TABLE IF NOT EXISTS sim_annual
(
    "TechID" text COLLATE pg_catalog."default",
    "SizingID" text COLLATE pg_catalog."default",
    "BldgType" text COLLATE pg_catalog."default",
    "BldgVint" text COLLATE pg_catalog."default",
    "BldgLoc" text COLLATE pg_catalog."default",
    "BldgHVAC" text COLLATE pg_catalog."default",
    tstat text COLLATE pg_catalog."default",
    normunit text COLLATE pg_catalog."default",
    numunits real,
    measarea real,
    kwh_tot real,
    kwh_ltg real,
    kwh_task real,
    kwh_equip real,
    kwh_htg real,
    kwh_clg real,
    kwh_twr real,
    kwh_aux real,
    kwh_vent real,
    kwh_venthtg real,
    kwh_ventclg real,
    kwh_refg real,
    kwh_hpsup real,
    kwh_shw real,
    kwh_ext real,
    thm_tot real,
    thm_equip real,
    thm_htg real,
    thm_shw real,
    deskw_ltg real,
    deskw_equ real,
    lastmod text COLLATE pg_catalog."default",
    -- 2025-09-29 Nicholas Fette (Solaris Technical)
    -- Cause explicit error if user tries to load duplicate data
    PRIMARY KEY ("TechID", "SizingID", "BldgType", "BldgVint", "BldgLoc", "BldgHVAC", "tstat", "normunit")
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;
