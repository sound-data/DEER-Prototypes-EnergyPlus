-- Create the simulation peak period demand value table from the hourly data table.
-- Whole Building kw: PeakDay 2 - 5 (previous DEER), 4 - 9 (DEER2020) on 3-day Heatwave
-- Time Estimate: 600 seconds
SET search_path TO "MC_results_database";
DROP TABLE IF EXISTS sim_peakper;
CREATE TABLE sim_peakper AS 
SELECT "TechID","SizingID","BldgType","BldgVint",sim_hourly_wb."BldgLoc" as "BldgLoc","BldgHVAC",
       round(((Sum(hr14)+Sum(hr15)+Sum(hr16))/9)::NUMERIC(15,3),3) as bldg_kw25,
       round(((Sum(hr16)+Sum(hr17)+Sum(hr18)+Sum(hr19)+Sum(hr20))/15)::NUMERIC(15,3),3) as bldg_kw49
 FROM sim_hourly_wb
 JOIN peakperspec ON sim_hourly_wb."BldgLoc" = peakperspec."BldgLoc"
 WHERE ((daynum = "PkDay"::smallint) or (daynum = "PkDay"::SMALLINT+1) or (daynum = "PkDay"::SMALLINT+2))-- and enduse::SMALLINT = 20
 GROUP BY "TechID","SizingID","BldgType","BldgVint",sim_hourly_wb."BldgLoc","BldgHVAC"
 ORDER BY "TechID","SizingID","BldgType","BldgVint",sim_hourly_wb."BldgLoc","BldgHVAC";