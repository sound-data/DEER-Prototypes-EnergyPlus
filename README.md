# Prototype Models Generation System

## Introduction
This repository houses the modeling system developed for transitioning DEER prototype building simulation models from DOE2-eQuest to EnergyPlus. EnergyPlus is a modern energy simulation engine with strong support from the Department of Energy and NREL. Previously, MASControl3 was used for batch simulations, but the new system employs Modelkit, a free and open-source, cross-platform framework for parametric modeling developed by [Big Ladder Software](https://bigladdersoftware.com). Big Ladder Software specializes in providing support for EnergyPlus.

This repository includes Modelkit files for generating EnergyPlus input files and various types of scripts. There's a script for running batch simulations for one or more measures in a specific folder. Python scripts are provided for transforming Modelkit energy consumption results into the DEER database format. Additionally, Python and SQL scripts calculate permutation-level energy savings from simulation outputs. While the current process reuses most of the scripts developed by the previous DEER Ex Ante team to manipulate MASControl3 outputs, future optimization of those scripts and the Modelkit-based modeling framework are planned.

This repository also contains static models (prototypes/WaterHeaterModels) for modeling water heaters in residential homes. These models are not parametrized; they are intended to serve as templates to replace the water heater calculator.

## Required Tools and Installation
To install and use the prototype energy models on Windows (instructions for Mac will be provided in the future), follow these steps:

1. Install EnergyPlus [version 9.5](https://github.com/NREL/EnergyPlus/releases/tag/v9.5.0) (for residential prototypes) and [version 22.2](https://github.com/NREL/EnergyPlus/releases/tag/v22.2.0) (for commercial prototypes).
2. Install [Modelkit Caboodle](https://share.bigladdersoftware.com/files/modelkit-caboodle-0.9.3+59d2aa1.exe). If Modelkit Catalyst is already installed, you may need to uninstall it before installing Modelkit Caboodle.
3. Install Python.
4. Install a database management software that supports PostgreSQL, such as pgAdmin4.
5. Install Git.
6. (Optional) Install a GUI for Git if preferred over the command line.
7. Clone the repository to your machine using Git or your preferred tool. It's recommended to clone it as close to the (C:) drive as possible to avoid path length limit-related issues.

## How to Use This Modeling Framework
To run measure cases, open a command line in one of the folders (e.g., '_SWSV001-05 Duct Seal_DMo_') within the '_residential measures/_' directory and execute the command `modelkit rake`. This command runs all predefined simulations in the specified directory. To run all measures in all folders within '_residential measures/_' or '_commercial measures/_', use the provided '_automated_run.py_' Python script located in '_scripts/_'. The predefined measures are grouped by general measure group name, building type, and vintage. Each of these folders contains a set of measure cases (offerings and baselines) defined in the '_cases/_' folder, per building type in '_prototypes/_'. Modelkit runs all measures and stores simulation outputs (IDFs, hourly output variables, etc.) in multiple folders named after the measure case names in '_runs/_' (this folder appears after simulations are complete). To exclude specific simulations based on climate or cohorts, insert the pound sign '#' in the 'skip' column of the respective '_climate.csv_' or '_cohorts.csv_' row for the simulations you wish to skip. A results summary file, mainly containing annual energy consumptions, is stored in '_summary-results.csv_'. More detailed information about how Modelkit works and its features can be found on the [developer's website](https://bigladdersoftware.com/projects/modelkit/).

Post-processing steps for residential measures:
- Open one of the three Python scripts (building type-specific).
- Specify the specific subdirectories in the analysis folder (containing simulation results) in the script, and specify the '_measure name_' to be processed (a list of measure names can be found in '_DEER_EnergyPlus_Modelkit_Measure_list.xlsx_' under the '_Measure_list_' sheet, in the '_Measure (general name)_' column.
- Run the script to generate three CSV files: '_current_msr_mat.csv_', '_sim_annual.csv_', and '_sim_hourly_wb.csv_' (or '_sfm_annual.csv_' and '_sfm_hourly_csv_' for single-family).
- Load these three CSV files into the PostgreSQL database management software.
- Run the post-processing SQL queries R1 to R4 (for residential measures only), then P1 to P8 (for all measures), in order.
- Export '_meas_impacts_2022_res_' as the output.

Post-processing steps for commercial measures:
- (scripts for commerical measures will be updated by 12/22/2023, high level steps will be very similar to residental ones.)

## How to Contribute to the Project
Contributions to the project are welcome. To add new measures or fix bugs, follow these steps:

### How to Add a New Measure
1. Install the modeling framework as described above.
2. If the proposed measure doesn't fit into any general measure categories (see folder names in '_residential measures/_' or '_commercial measures/_'), create a new folder with the MeasureVersionID followed by the a short version of the measure package name in one of the two directories. Refer to the [DEER Prototype System User Guide](https://cedars.sound-data.com/deer-resources/tools/energy-plus/) on CEDARS for further folder naming, cohort naming and case naming instructions. Also please refer to [DRAFT Technology ID Creation template](https://cedars.sound-data.com/deer-resources/tools/energy-plus/) for the naming conventions of TechIDs (the case_name of each simulation run)
3. Within the newly created folder, create a subfolder named '_cases/_'.
4. Copy the file named '_query.txt_' from any existing measure and paste it into the new folder.
5. Create two new files in the newly created folder: '_climates.csv_' and '_cohort.csv_'. Populate '_cohort.csv_' with necessary information about weather files and prototype buildings to be used. Additional details on preparing the cohort file are also in the User Guide.
6. If needed, modify the prototype, root.pxt file in '_prototypes/_' to define the new measure (e.g., a new HVAC system or equipment).
7. In the '_cases/_' folder, create a *.csv file and provide parameter values corresponding to each measure (offerings and baselines). Each *.csv file is related to a given building prototype referred to as the root file, whose path should be provided in '_cohort.csv_'. Case names should coincide with Technology IDs, see the User Guide for more information.
8. Run all the newly added measures and provide the generated '_results-summary.csv_' files with your [pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests) for review.
9. If the proposed measure fits within an existing general measure category, simply add it to the appropriate folder and files.
10. Follow steps 7 and 8.

### How to Fix Bugs
1. Install the modeling framework as described above.
2. Fix the identified bug on your local repository.
3. Run all the existing measures and provide the generated '_results-summary.csv_' files with your [pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests) for review.

## Features to Be Added in the Future
In the future, the following features will be added or improved:

1. Optimization of residential prototype model files to reduce the number of root files.
2. Streamlining the data transformation process from Modelkit system outputs to the DEER database.
3. Development of a script to produce measure permutation energy savings information in eTRM format.
4. Reduction of the number of residential measure folders by parameterizing code fields in '_climates.csv_' that vary by building type, in a separate table.
5. Addition of the Airflow Network model to the Modelkit residential prototypes.
