# Prototype models generation system

## Introduction
This repository contains the modeling system developed to transition the DEER prototype building simulation models from DOE2-eQuest to EnergyPlus, a more modern energy simulation engine which has more support from the Department of Energy and NREL. MASControl3 was the tool previously used to perform batch simulations for the measure permutations. The new system uses a a free and open-source, cross-platform framework for parametric modeling, Modelkit, developed by Big Ladder Software, a software company that specializes in providing support for EnergyPlus. (https://bigladdersoftware.com/projects/modelkit/)

This repository contains Modelkit files used to generate EnergyPlus input files and several types of scripts. There is one script to run a batch file to execute a full set of permutations for one or more measures. There is a set of Python scripts that transform modelkit energy consumption results to the database format previously used for outputs of MASControl3. And another set of Python and SQL scripts that calculate energy savings from simulation outputs. The current process builds and reuses most of the scripts that previous DEER Ex Ante team developed to manipulate outputs of the MASControl3 tool. An optimization and a complete adaptation of the scripts to the current modelkit based modeling framework will take place in the future.

## Required tools and installation
The following steps must be completed in order to install and use the developed prototype energy models on Windows (directions for Mac will be provided in the future):
1.	Install the [EnergyPlus engine version 9.5](https://github.com/NREL/EnergyPlus/releases/tag/v9.5.0).
2.	Install the [Modelki tool](https://share.bigladdersoftware.com/files/modelkit-catalyst-0.7.0.exe).
3.	Replace the file at this path (or similar) _C:\Program Files (x86)\Modelkit Catalyst\lib\rubygems\gems\modelkit-0.8.1\lib\modelkit\parametrics\template.rb_ by the file in available on this repository in folder _concurrency bug_.
4.	Install Python.
5.	Install a database management software that supports postgreSQL such as pgAdmin4.
7.	Install Git.
8.	Optional: install a GUI to use Git if preferred instead of using the command line.
9.	Clone the repository to your machine using Git or your preferred tool. We recommend cloning the repository as close to (C:) drive as possible to avoid path length limits related problems.

## How to use this modeling framework
To run measure cases, open a new command line in one of the folders (such as _DMo_Duct Seal_) in _analysis/_ directory and run the command `modelkit rake`. This will run all predefined measures in that given directory. To run all measures in all folders in _analysis/_ use the provided automated_run.py Python script located in _scripts/_. The existing predefined measures were grouped by general measure group name, building type and vintage. Each of these folders contains a set of measure cases, defined in the folder _cases/_, per building prototype, defined in the folder _prototypes/residential/_. Modelkit will run all measures and store simulation outputs (IDFs, hourly output variables, etc.) in multiple folders, named based on measure cases names, in _runs/_ (this folder appears after simulations run) and a results summary file containing mainly annual energy consumptions in _results.csv_. More detailed information about how Modelkit works and its features can be found on the [developers website](https://bigladdersoftware.com/projects/modelkit/).

Postprocessing steps:
+ open one of three python scripts (building type specific)
+ specify the specific subdirectories in analysis folder (with simulation results in them) in the script, and specify "measure name" to be processed (list of measure names can be found from "DEER_EnergyPlus_Modelkit_Measure_list.xlsx", in the "Measure_list" sheet, the "Measure (general name)" column.
+ run script to get three csv files 'current_msr_mat.csv', 'sim_annual.csv', 'sim_hourly_wb.csv' (or 'sfm_annual.csv' and 'sfm_hourly_csv' for single family)
+ load these three csv files into the postgreSQL database management software
+ run the post-processing SQL queries R1 to R4 (for residential measures only), then P1 to P8 (for all measures), in order
+ export 'meas_impacts_2022_res' as the output

## How to Contribute to the Project
Every user can create a new branch of the repository to add new measures or fix bugs. The DEER DNV team will approve the request and merge it to the main branch after an internal review of the proposed addition or bug fix.

### How to add a new measure
1. Install the modeling framework as described above
2. If the proposed measure doesn’t fall in any of the general measure categories (see folders names in _analysis/_), create a new folder with a descriptive name in _analysis/_.
3. In the new created folder, create a folder named _cases_.
4. Copy from any existing measure the file named rakefile.rb (e.g. _analysis/DMo_Duct Seal/rakefile.rb_) and paste to new created folder.
5. Copy from any existing measure the file named _query.txt_ and paste to new created folder.
6. Create in new created folder the new files _climates.csv_ and _cohort.csv_ and add all necessary information about the weather files and prototype buildings to be used in _cohort.csv_. Additional information about how to prepare the cohort file will be provided in the future.
7. If necessary, modify the prototype buildings to define the new measure (i.e. new HVAC system or equipment, etc.).
8. In the _cases_ folder create a *.csv file and provide parameter values corresponding to each measure. Each *.csv file is related to a given building prototype called root file whose path should be provided in _cohort.csv_. Instruction for measures names will be provided in the future.
9. Run all the new added measures and provide with the [pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests) the generated _results-summary.csv_ files.
10. If the proposed measure falls in one of the existing general measure categories just add the new measure in existing folders and files.
11. Do step 8 and 9.

### How to fix bugs
1. Install the modeling framework as described above.
2. Fix the identified bug on your local repository.
3. Run all the existing measures and provide with the [pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests) the generated _results-summary.csv_ files.

## Features to be added in the future
1. Optimize the prototype models’ files to reduce the number of root files.
2. Optimize the data transformation process from the Modelkit system outputs to DEER database.
3. Write a script to produce measure permutation energy savings information in eTRM format
4. Reduce the number of measure folders by parameterizing codes’ fields, in _climates.csv_ that vary by building type, in a separate table.
5. Add the Aiflow Network model to the Modelkit residential prototypes.
