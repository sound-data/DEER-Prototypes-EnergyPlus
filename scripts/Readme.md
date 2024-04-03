# Post-processing scripts for Modelkit outputs for DEER

## Introduction
Scripts provided here are used to automate a batch file and to transform Modelkit simulation results into measure savings/impacts records suitable for the DEER database. 

Before using these scripts make sure:
1. Python is installed (at least version 3.8.8)
2. A database management software that supports postgreSQL is installed (such as pgAdmin4)

## How to use the scripts in these folders
After the simulation is done, please make sure simulation is finished successfully, where a particular subdirectory in the measures folder (i.e. **SWSV001-05 Duct Seal_DMo**) contains the file _results-summary.csv_ as well as the subfolder **runs**, which contains climate-zone specific output files.

### Post-processing steps for residential measures:
1. Open one of the provided .py scripts in the **data transformation** directory (either DMo.py, MFm.py, or SFm.py). The corresponding building type script should be used.
2. Open up the accompanying excel spreadsheet ***DEER_EnergyPlus_Modelkit_Measure_list_working.xlsx***, identify the corresponding measure name in column A of the sheet `Measure_list`.
3. In line 23 of the python script (line 26 for the Com script), specify the measure name identified in step 2. For example: `measure_name = 'SWSV001-05 Duct Seal_DMo'`
4. In line 33 of the python script (line 34 and 35 in the Single Family script, line 40 in Com script but that one should be automatic, double check to make sure), specify the path to the simulation directory starting with the folder Analysis. For example: `path = 'residential measures/SWSV001-05 Duct Seal_DMo'` (For Single Family, if existing vintage, assign both the 1975 and 1985 directory to path_1975 and path_1985 respectively, and leave path_new blank; if new vintage, assign the New directory to path_new ) 
5. run the python script. The script should produce 3 files, ***current_msr_mat.csv***, ***sim_annual.csv***, ***sim_hourly_wb.csv*** (***sfm_annual.csv*** and ***sfm_hourly_csv*** instead for Single Family). These files should appear in the same directory as the python script. For better organization, save these files somewhere else trackable. Note that these files are part of **gitignore**, but the user can produce them in their local repo and move them to a desirable location after the process is finished.
6. If tables "wts_res_bldg.csv" and "wts_res_hvac.csv" is not consistent with the DEER weights table (DEER.BldgWts), run DEER_weights_extraction.py to extract the most up-to-date weights table needed for post-procesing. Use the the most up-to-date tables during the POSTgreSQL steps.
7. In a postgreSQL database management software (such as [pgadmin4](https://www.pgadmin.org/download/)), import the csv files generated from step 5, along with the other csv tables provided in the **energy savings** folder. Also, run the ***ImpactProfiles.sql*** in the postgreSQL environment to create its corresponding support table. The support tables provided in the **energy savings** folder only needed to be imported once.
8. From the **energy savings** folder, run provided .sql queries labelled "R1..", "R2.." etc. in the following order: R1, R2, R3, R4, P1, P2, P3, P4, P5, P6, P7, P8. Only run P2.1A and P2.1B after P2 if processing Duct optimization or Duct seal measure. (for Commercial, a separate set of commercial scripts are provided, use those instead and run in numerical order)
9. After running the queries in sequence, a table named `meas_impacts_2022_res` (or 'meas_impacts_2023_com') should be generated in the postgreSQL environment. Export this table, this is the final output.

### Post-processing steps for commercial measures:
1. Open the Python script Com.py in the **data transformation** directory.
2. In line 27, or the line defining “measure_name = ..”, specify the corresponding measure folder. In the example code, it is specified as “**SWXX111-00 Example_SEER_AC**”. This should be the same name as the folder name under the directory “commercial measures”. A corresponding measure record with matching cohort/case file names should be present in the workbook ***DEER_EnergyPlus_Modelkit_Measure_list_working.xlsx*** under the same directory.
3. 
   NOTE: the example directory **SWXX111-00 Example_SEER_AC** and all its subdirectories are only used to illustrate the workflow for post-processing. The case files and its parameter in this example directory do not reflect how an actual measure should be set up, as they are only the most basic set up for a modelkit run.
   Update on 3/22/2024: the example directory **SWXX111-00 Example_SEER_AC** reflects the vintage consolidation update (with only Ex and New vintages)
5. If the table "wts_com_bldg.csv" is not consistent with the DEER weights table (DEER.BldgWts), run DEER_weights_extraction.py to extract the most up-to-date weights table needed for post-procesing. Use the the most up-to-date tables during the POSTgreSQL steps.
6.	Run the python script to generate three CSV files: 'current_msr_mat.csv', 'sim_annual.csv', and 'sim_hourly_wb.csv'
7.	Load these three CSV files into the PostgreSQL database management software (see residential section of the README, step 6)
8.	Run the post-processing SQL queries P1 to P5 for commercial, located in 'scripts/energy savings/commercial/'.
9.	Export ‘meas_impacts_2024_com” as the output.
