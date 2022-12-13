--Delete the unmodded MFm/SFm records, insert the modded MFm/SFm records

SET search_path TO "MC_results_database";

DELETE FROM meas_impacts_2022
WHERE (meas_impacts_2022."EnergyImpactID" = 'Res-DuctSeal-HighToLow-wtd_retrofit');

INSERT INTO meas_impacts_2022
SELECT
*
FROM meas_impacts_2022_do_mod;
