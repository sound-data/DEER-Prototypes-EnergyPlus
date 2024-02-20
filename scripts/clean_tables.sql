--Drop all tables from post-processing.
--Arranged in reverse order from creation.

SET search_path TO "MC_results_database";

--P8
DROP TABLE IF EXISTS "meas_impacts_2022_res";
--P6
DROP TABLE IF EXISTS "meas_impacts_tmp3_2022";
--P5
DROP TABLE IF EXISTS "meas_impacts_wtd_2022";
--P4
DROP TABLE IF EXISTS "meas_impacts_hvacwtd";
--P3
DROP TABLE IF EXISTS "meas_impacts_hvactmp";
--P2.1A
DROP TABLE IF EXISTS "meas_impacts_2022_do_mod";
--P2.1A
DROP TABLE IF EXISTS "meas_impacts_2022_ds_mod";
--P2
DROP TABLE IF EXISTS "meas_impacts_2022";
--P1
DROP TABLE IF EXISTS "sim_peakper";
--R4
DROP TABLE IF EXISTS "sim_hourly_twtd_2022";
--R3
DROP TABLE IF EXISTS "sim_annual_twtd_2022";
--R2
DROP TABLE IF EXISTS "sim_hourly_wb_wtd";
--R1
DROP TABLE IF EXISTS "sim_annual_wtd";

--Input data
DROP TABLE IF EXISTS "sfm_annual";
DROP TABLE IF EXISTS "sfm_hourly_wb";
DROP TABLE IF EXISTS "sim_annual";
DROP TABLE IF EXISTS "sim_hourly_wb";
DROP TABLE IF EXISTS "current_msr_mat";

--Support tables
DROP TABLE IF EXISTS "wts_res_bldg_2022";
DROP TABLE IF EXISTS "wts_res_hvac";
DROP TABLE IF EXISTS "peakperspec";
DROP TABLE IF EXISTS "ImpactProfiles";
DROP TABLE IF EXISTS "NumStor";
DROP TABLE IF EXISTS "NumBldgs";
DROP TABLE IF EXISTS "FloorArea_2022";
