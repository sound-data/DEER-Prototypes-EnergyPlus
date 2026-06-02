# TRC - jdeblois@trccompanies.com
#
# 
# Use when the measure is identical for all prototypes
# There should be one template file for each system type that is applicable to the measure, in the \cases\ directory
# The script takes cohorts data from cohorts_old.csv and creates a new cohorts.csv. It overwrites cohorts.csv.
#
# 1. Update system_types on line 17 to include the ones needed for the measure
# 2. Update cohorts_list to list all of the Measure Group Names (column N) from DEER_EnergyPlus_Modelkit_Measure_list_working.xlsx
# 3. Run this file from \cases\


import pandas as pd
import os

# match the names of the .csv files in the \cases\ folder
system_types = ["cDXGF", "cDXHP", "cDXOH"]

# Path to the script and cohorts files
script_directory = os.path.dirname(os.path.abspath(__file__))
cohorts_directory = os.path.dirname(script_directory)


# Read the cohorts_list file into a DataFrame
cohorts_list_file_path = cohorts_directory + r"\cohorts_list.csv"  # Assumes the file is located up one directory
# Test path to cohorts_list.csv
if not os.path.exists(cohorts_list_file_path):
    print("cohorts_list.csv file not found.")
    exit()
# Read the cohorts_list file into a DataFrame
cohorts_list_df = pd.read_csv(cohorts_list_file_path, comment="#")
# Extract the second column skipping the first row
cohorts_list = cohorts_list_df.iloc[0:, 1].tolist()
# Print the extracted cohorts_list
print("Cohorts_list array:", cohorts_list)

# Read in the cases files for each system type
cases_df = {}
print(system_types)
for system_type in system_types:
    cases_file_path = os.path.join(script_directory, system_type + ".csv") # Assumes the file is located in the same directory
    # Check if the cases file exists
    if not os.path.exists(cases_file_path):
        print(system_type, "CSV file not found at", cases_file_path)
        continue
    # Read the cases file into a DataFrame
    cases_df[system_type] = pd.read_csv(cases_file_path, comment="#")

#print one csv file for each entry in the cohorts list
for cohort in cohorts_list:
    system_type = cohort.split('&')[2]
    case_file_name = cohort + ".csv"
    cases_df[system_type].to_csv(os.path.join(script_directory, case_file_name), index=False)

#read the cohorts_old.csv file into a DataFrame
cohorts_old_file_path = cohorts_directory + r"\cohorts_old.csv"  # Assumes the file is located up one directory
# Test path to cohorts_old.csv
if not os.path.exists(cohorts_old_file_path):
    print("cohorts_old.csv file not found.")
    exit()
# Read the cohorts_old file into a DataFrame
cohorts_old_df = pd.read_csv(cohorts_old_file_path, comment="#")

#create a dictionary of cohorts data for each prototype
cohorts_old_dict = {}
for i in range(len(cohorts_old_df)):
    prototype = cohorts_old_df.iloc[i,1]
    cohorts_old_dict[prototype] = list(cohorts_old_df.iloc[i,2:])
#write a new cohorts.csv file that combines the list from cohorts_list.csv and the prototype data from cohorts_old

cohorts_df = pd.DataFrame(None,index=range(len(cohorts_list)),columns=cohorts_old_df.columns)
for i in range(len(cohorts_list)):
    prototype = cohorts_list[i].split('&')[0]
    cohorts_df.iloc[i,1:] = [cohorts_list[i]] + cohorts_old_dict[prototype]
cohorts_new_file_path = cohorts_directory + r"\cohorts.csv"
cohorts_df.to_csv(cohorts_new_file_path, index=False)