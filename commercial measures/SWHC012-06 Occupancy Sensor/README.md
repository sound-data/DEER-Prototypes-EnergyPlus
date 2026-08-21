# SWHC012-06 Occupancy Sensor, Classroom

## Measure Description

This folder contians the commercial Occupancy Sensor measure setup used for DEER prototype simulation, result scraping, andd ownstream post-processing.

### Key Changes in This Revision
- Updated to CZ2025 weather files
- Updated sizing map 22-2 to accomodate Pump:VariableSpeed (breaking change from main branch)
- Reverted interim workaround (old version of prototypes)
- For generated schedules, use calendar year 2009 (start day = Thursday)
- Added lines to Com.py to deal with hardsize instance files
- Removed DXGF case for ERC and DXHP for EPr and ESe to align with eTRM offerings

## Cohorts and Cases

| Case Name (TechID) | Case Type |Building Type | Building Vintage |
|-------------------|-------|------|--------|
| NE-HV_Tech-OccSens-cDXGF-NoOccSens | Base Case| EPr, ESe | Ex, New |
| NE-HV_Tech-OccSens-cDXHP-NoOccSens | Base Case | ERC | Ex, New |
| NE-HV_Tech-OccSens-cDXGF | Measure Case| EPr, ESe | Ex, New |
| NE-HV_Tech-OccSens-cDXHP | Measure Case| ERC | Ex, New |

## Query File for Normalizing Units
The file 'query_SWHC012.txt' includes queries for cooling capacity. After running simulations: 
'''
cd 'commercial measures/SWHC012-06'
python result2.py -q query_SWHC012.txt
'''

## Data Transformation and Post-Processing
Measure Working List: DEER_EnergyPlus_Modelkit_Measure_list_working_SWHC012-06.xlsx

## Simulation and Post-Processing Steps
- Copy '22-2.csv' from sizing-map folder into 'C:\Program Files (x86)\Modelkit Caboodle\lib\rubygems\gems\modelkit-energyplus-0.3.0\resources\sizing-map' to ensure simulations run
- Run schedule.py to generate schedules for each building type
- Run simulations and confirm result files
- Scrape outputs with 'scripts/result2.py' using query_SWHC012.txt
- Run transformation scripts from 'scripts/data transformation'
- Review generated files: current_msr_mat.csv, sim_annual.csv, sim_hourly_eu.csv, sim_hourly_wb.csv, CEDARS_LoadShape_Com.zip

## Load Shape Workaround
The load shape files (found in CEDARS_LoadShape_Com.zip) are missing the 'NormUnit' column required for uploading to CEDARS. The missing column must be added manually into each of the 3 load shape files (one for each building type). The column must be added in between the 'BldgLoc' and 'Type (Whole Building or End Use)' columns with the column header 'NormUnit' and value 'Cap-Tons' for each line.

## Other Simulation Notes

### HVAC-Zone Template

Providing a filename via the parameter classroom_class_setpoint_temp_schedule parameter triggers the prototypes to read in a temperature setpoint schedule from file. The filename is specified in the hvac-zone template using a relative path to its location in the measure folder.

**templates\energyplus\templates\zonehvac\hvac-zone.pxt near line 590**

```
  Schedule:File,
	<%=zone_name %> Cooling Setpoint Schedule,  !- Name
    Temperature,             !- Schedule Type Limits Name
	C:/DEER-Prototypes-EnergyPlus/commercial measures/SWHC012-05 Occupancy Sensor/<%= setpoint_temp_schedule %>,  !- File Name
    3,                       !- Column Number
    1,                       !- Rows to Skip at Top
    8760,                    !- Number of Hours of Data
    Comma,                   !- Column Separator
    No,                      !- Interpolate to Timestep
    10,                      !- Minutes per Item
    Yes;                     !- Adjust Schedule for Daylight Savings
```
**templates\energyplus\templates\zonehvac\hvac-zone.pxt near line 612**

```
  Schedule:File,
	<%=zone_name %> Heating Setpoint Schedule,  !- Name
    Temperature,             !- Schedule Type Limits Name
	C:/DEER-Prototypes-EnergyPlus/commercial measures/SWHC012-05 Occupancy Sensor/<%= setpoint_temp_schedule %>,  !- File Name
    4,                       !- Column Number
    1,                       !- Rows to Skip at Top
    8760,                    !- Number of Hours of Data
    Comma,                   !- Column Separator
    No,                      !- Interpolate to Timestep
    10,                      !- Minutes per Item
    Yes;                     !- Adjust Schedule for Daylight Savings
```

### Extracting Normalizing Units for Classrooms

Developers applied the measure to only those zones representing classrooms, taken to mean where zone_type prefix is `classroom_class`. Developers considered area (from zones), cooling capacity (from cooling coils), and cooling capacity (from AirLoopHVAC systems) as candidates for normalizing units, ultimately choosing cooling capacity from AirLoopHVAC systems.

The total cooling capacity of classroom zones in a given building simulation is calculated using a multi-step process to tabulate cooling capacity for each system in the model and then filter relevant systems and aggregate the capacity of matching systems.

To reproduce the computations, enter these command line statements:

1. Change directory into the first vintage subfolder and run the data extraction script:

```
cd 'C:/DEER-Prototypes-EnergyPlus/commercial measures/SWHC012-06 Occupancy Sensor/SWHC012-06 Occupancy Sensor_Ex'
python result2.py -s -t -q ../query_SWHC012_normalizing.txt
```

At this point, the user should have a new SQLite file `simdata.sqlite` saved by the script with tables sim_metadata and sim_tabular, which contains cooling capacity figures for each building instance and system.

2. Continue with the command to reformat sizing data:

```
cat ../extract_sizing_data_sqlite.sql | sqlite3 simdata.sqlite -csv -header > results-sizing-detail.csv
```

At this point, the user should have a new file `results-sizing-detail.csv` with similar information in plain text / CSV format. If sqlite3 is not installed, download a portable executable or execute the query statement using a database preview application.

3. Repeat above steps for each vintage subfolder (Ex, New).

4. Then, continue with commands:

```
cd 'C:/DEER-Prototypes-EnergyPlus/commercial measures/SWHC012-06 Occupancy Sensor'
python result_filtered.py
```

The result_filtered script cross-references the result_sizing_detail.csv and coil_list.xlsx in order to filter relevant zones or systems. At this point, the user should have a new files "sizing_agg_filtered.csv" in each vintage subfolder.

5. Combine the sizing_agg_filtered files into one CSV file and archive the result among energy model outputs. The combined sizing_agg_filtered.csv contains the normalizing unit lookup table, which can be used for example by pasting into an energy savings calculation workbook.

### Classroom System Names
The classroom system names were manually identified by inspection of prototype root files and tabulated in the file `coil_list.xlsx` (sheet "Main coils").

### Occupancy Schedule
`OccSchedule vs TempSetpointSch.xlsx` shows details of the occupancy schedule and assigned temperature setpoints based on classroom usage, days of the week, and holidays.
