-- Table: MC_results_database.wts_com_bldg

-- 2025-09-29 Nicholas Fette (Solaris Technical): Don't hard-code the search_path.

-- Uncomment this line if you need to run this query manually.
--SET search_path TO "MC_results_database";

-- Uncomment this line if you need to redefine this table.
--DROP TABLE IF EXISTS wts_com_bldg;

CREATE TABLE IF NOT EXISTS wts_com_bldg
(
    pa character varying(255) COLLATE pg_catalog."default",
    bldgtype character varying(255) COLLATE pg_catalog."default",
    era character varying(255) COLLATE pg_catalog."default",
    bldgloc character varying COLLATE pg_catalog."default",
    sum_bldg numeric,
    -- 2025-09-29 Nicholas Fette (Solaris Technical)
    -- Cause explicit error if user tries to load duplicate data. This helps avoid accidental mistakes.
    PRIMARY KEY ("pa", "bldgtype", "era", "bldgloc")
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;
