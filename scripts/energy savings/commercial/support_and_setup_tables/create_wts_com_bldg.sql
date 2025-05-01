-- Table: MC_results_database.wts_com_bldg

-- DROP TABLE "MC_results_database".wts_com_bldg;

CREATE TABLE IF NOT EXISTS "MC_results_database".wts_com_bldg
(
    pa character varying(255) COLLATE pg_catalog."default",
    bldgtype character varying(255) COLLATE pg_catalog."default",
    era character varying(255) COLLATE pg_catalog."default",
    bldgloc character varying COLLATE pg_catalog."default",
    sum_bldg numeric
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;