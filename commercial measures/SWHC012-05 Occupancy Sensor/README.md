# SWHC012 Occupancy Sensor, Classroom

This document describes the steps necessary to reproduce simulations and model outputs for this measure.

Prepared by Kelsey Yen and Nicholas Fette (Solaris Technical). 
Created 2025-10-22, revised 2026-01-03.

## Generating temperature setback schedules

Run the script included in this folder to output Schedule_Primary.csv, Schedule_Relocatable.csv, and Schedule_Secondary.csv.

```
python schedule.py
```

The schedules will be referenced by EnergyPlus models via a Schedule:File object.

## Running simulation

Providing a filename via the parameter classroom_class_setpoint_temp_schedule parameter triggers the prototypes to read in a temperature setpoint schedule from file.
The filename is specified in the hvac-zone template using a relative path to its location in the measure folder.
If EnergyPlus issues a warning due to the relative path, a user apply a workaround by editing the hvac-zone template to hard-code the folder where schedules are located, for example:

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

## Extracting Normalizing Units for Classrooms

Developers applied the measure to only those zones representing
classrooms, taken to mean where zone_type prefix is `classroom_class`.
Developers considered area (from zones), cooling capacity (from cooling coils),
and cooling capacity (from AirLoopHVAC systems) as candidates for normalizing units,
ultimately choosing cooling capacity from AirLoopHVAC systems.

The total cooling capacity of classroom zones in a given building simulation is
calculated using a multi-step process to tabulate cooling capacity for
each system in the model and then filter relevant systems and aggregate
the capacity of matching systems.

### To reproduce the computations, a user should enter these command line statements:

1. Change directory into the first vintage subfolder and run the data extraction script:

```
cd "C:/DEER-Prototypes-EnergyPlus/commercial measures/SWHC012-05 Occupancy Sensor/SWHC012-05 Occupancy Sensor_Ex"
python result2.py -s -t -q ../query_SWHC012_normalizing.txt
```

At this point, the user should have a new SQLite file `simdata.sqlite` saved by the
script with tables sim_metadata and sim_tabular, which contains cooling capacity figures for each building instance and system.

2. Continue with the command to reformat sizing data:

```
cat ../extract_sizing_data_sqlite.sql | sqlite3 simdata.sqlite -csv -header > results-sizing-detail.csv
```

At this point, the user should have a new file `results-sizing-detail.csv` with
similar information in plain text / CSV format. If sqlite3 is not installed,
download a portable executable or execute the query statement using a database preview application.

3. Repeat above steps for each vintage subfolder (Ex, New).

4. Then, continue with commands:

```
cd "C:/DEER-Prototypes-EnergyPlus/commercial measures/SWHC012-05 Occupancy Sensor"
python result_filtered.py
```

The result_filtered script cross-references the result_sizing_detail.csv and coil_list.xlsx in order to filter relevant zones or systems.
At this point, the user should have a new files "sizing_agg_filtered.csv" in each vintage subfolder.

5. Combine the sizing_agg_filtered files into one CSV file and archive the result among energy model outputs.

The combined sizing_agg_filtered.csv contains the normalizing unit lookup table, which
can be used for example by pasting into an energy savings calculation workbook.

### Developer Notes
1. The classroom system names were manually identified by inspection of
prototype root files and tabulated in the file `coil_list.xlsx` (sheet "Main coils").
2. Cooling capacity was obtained in bulk using the tabular report fields listed
in query_SWHC012_normalizing.txt. Based on trial and error, measure developers
determined that outputs from AirLoopHVAC:UnitarySystem were preferred over
outputs from individual cooling coils due to ambiguous labeling of total
cooling capacity in multispeed coils; and that with linked-sizing active, the query
strings vary slightly between base case and measure case models.
3. For a convenience, the distinct query file used to collate model usage (`query_SWHC012.txt`)
may include query strings to gather area or cooling capacity of some classroom zones. 
These are useful during model testing as a sanity check but are ultimately unused
in calculating normalizing units, UEC, and UES.
