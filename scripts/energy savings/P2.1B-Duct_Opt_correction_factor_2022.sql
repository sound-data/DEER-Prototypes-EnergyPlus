--Delete the unmodded records, insert the modded records
--TRC Updated Energy Imapct ID, 07/07/2026

SET search_path TO "MC_results_database";

DELETE FROM meas_impacts_2022
WHERE (meas_impacts_2022."EnergyImpactID" = 'Res-DuctOpt-HighToLow-Retrofit');

INSERT INTO meas_impacts_2022
SELECT
*
FROM meas_impacts_2022_do_mod;
