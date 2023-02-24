# Post-processing scripts for Modelkit outputs for DEER

## Introduction
Scripts provided here are used to automate a batch file and to transform Modelkit simulation results into measure savings/impacts records suitable for the DEER database. 

Before using these scripts make sure:
1. Python is installed (at least version 3.8.8)
2. A database management software that supports postgreSQL is installed (such as pgAdmin4)

## How to use the scripts in these folders
After the simulation is done, please make sure simulation is finished successfully, where a particular subdirectory in the Analysis folder (i.e. **DMo_Ductless Heat Pump**) contains the file _results-summary.csv_ as well as the subfolder **runs**, which contains climate-zone specific output files.

1. Open one of three provided .py scripts in the **data transformation** folder (either DMo.py, MFm.py, or SFm.py). The corresponding building type script should be used.
2. Open up the accompanying excel spreadsheet ***DEER_EnergyPlus_Modelkit_Measure_list.xlsx***, identify the corresponding measure name in column A of the sheet `Measure_list`.
3. In line 23 of the python script, specify the measure name identified in step 2. For example: `measure_name = 'Ductless Heat Pump'`
4. In line 33 of the python script (line 34 and 35 in the Single Family script), specify the path to the simulation directory starting with the folder Analysis. For example: `path = 'Analysis/DMo_Ductless Heat Pump'` (For Single Family, if existing vintage, assign both the 1975 and 1985 directory to path_1975 and path_1985 respectively, and leave path_new blank; if new vintage, assign the New directory to path_new ) 
5. run the whole script. The script should produce 3 files, ***current_msr_mat.csv***, ***sim_annual.csv***, ***sim_hourly_wb.csv*** (***sfm_annual.csv*** and ***sfm_hourly_csv*** instead for Single Family). These files should appear in the same directory as the python script. For better organization, save these files somewhere else trackable. Note that these files are part of **gitignore**, but the user can produce them in their local repo and move them to a desirable location after the process is finished.
6. In a postgreSQL database management software (such as [pgadmin4](https://www.pgadmin.org/download/)), import the csv files generated from step 5, along with the other csv tables provided in the **energy savings** folder. Also, run the ***ImpactProfiles.sql*** in the postgreSQL environment to create its corresponding support table. The support tables provided in the **energy savings** folder only needed to be imported once.
7. From the **energy savings** folder, run provided .sql queries labelled "R1..", "R2.." etc. in the following order: R1, R2, R3, R4, P1, P2, P3, P4, P5, P6, P7, P8. Only run P2.1A and P2.1B after P2 if processing Duct optimization or Duct seal measure.
8. After running the queries in sequence, a table named `meas_impacts_2022_res` should be generated in the postgreSQL environment. Export this table, this is the final output.
