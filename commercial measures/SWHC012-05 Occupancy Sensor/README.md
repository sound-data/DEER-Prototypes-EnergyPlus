# SWHC012 Occupancy Sensor, Classroom

This document describes the steps necessary to reproduce simulations and model outputs for this measure.

Prepared by Solaris Technical, Kelsey Yen - 2025-10-22

## Generating temperature setback schedules

Run the script included in this folder to output Schedule_Primary.csv, Schedule_Relocatable.csv, and Schedule_Secondary.csv.

```
python schedule.py
```

The schedules will be referenced by EnergyPlus models via a Schedule:File object.

## Running simulation

Providing a filename via the parameter classroom_class_setpoint_temp_schedule parameter triggers the prototypes to read in a temperature setpoint schedule from file.
The filename is specified in the hvac-zone template using a relative path to its location in the measure folder.
Some users may get an EnergyPlus warning due to the relative path.
In order to run the models, apply a workaround by editing the hvac-zone template to hard-code the folder where schedules are located, for example:

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

In the development of this measure, both area and cooling capacity (from cooling coils) are used as normalizing units for the classroom zones. Only zones with "CLASSROOM" in the zone name are included. 

Classroom area and cooling coil names by zone from ESe model:

|Area Name|Cooling Coil Name|
|-|-|
|CLASSROOM E1 WEST PERIM (G.W1)|CLASSROOM E1 WEST PERIM (G.W1) SZ-VAV COOLING COIL|
|CLASSROOM E2 NORTH PERIM (G.N3)|CLASSROOM E2 NORTH PERIM (G.N3) SZ-CAV COOLING COIL|
|CLASSROOM E2 SOUTH PERIM (G.S2)|CLASSROOM E2 SOUTH PERIM (G.S2) SZ-CAV COOLING COIL|
|CLASSROOM E2 WEST PERIM (G.W1)|CLASSROOM E2 WEST PERIM (G.W1) SZ-CAV COOLING COIL|
|CLASSROOM E4 CORE (G.C6)|CLASSROOM E4 CORE (G.C6) SZ-CAV COOLING COIL|
|CLASSROOM E4 EAST PERIM (G.E2)|CLASSROOM E4 EAST PERIM (G.E2) SZ-CAV COOLING COIL|
|CLASSROOM E4 NORTH PERIM (G.N3)|CLASSROOM E4 NORTH PERIM (G.N3) SZ-CAV COOLING COIL|
|CLASSROOM E4 SOUTH PERIM (G.S1)|CLASSROOM E4 SOUTH PERIM (G.S1) SZ-CAV COOLING COIL|
|CLASSROOM E4 WEST PERIM (G.W4)|CLASSROOM E4 WEST PERIM (G.W4) SZ-CAV COOLING COIL|	
|COMPUTER CLASSROOM E4 CORE SPC (G.C5)|COMPUTER CLASSROOM E4 CORE SPC (G.C5) SZ-CRAC COOLING COIL|


To extract the necessary area and cooling coil capacity for all classroom types, each classroom area and cooling coil name was added to query_SWHC012.txt. The query file is then used with result2.py to output the simdata results. The areas and cooling coil capacities are then summed respectively and used as the normalizing units for the energy savings calculations along with the rest of the simdata outputs. Note that the following code includes area and cooling capacities from EPr, ERC, and ESe building types, but does not show the other lines in the query file.

Area and cooling capacity lines added to **query_SWHC012.txt**:
```
InputVerificationandResultsSummary/Entire Facility/Zone Summary/Area/CLASSROOM G.E1
InputVerificationandResultsSummary/Entire Facility/Zone Summary/Area/CLASSROOM G.NNE2
InputVerificationandResultsSummary/Entire Facility/Zone Summary/Area/CLASSROOM G.SSE3
InputVerificationandResultsSummary/Entire Facility/Zone Summary/Area/CLASSROOM G.W4
InputVerificationandResultsSummary/Entire Facility/Zone Summary/Area/CLASSROOM E1 WEST PERIM (G.W1)
InputVerificationandResultsSummary/Entire Facility/Zone Summary/Area/CLASSROOM E2 NORTH PERIM (G.N3)
InputVerificationandResultsSummary/Entire Facility/Zone Summary/Area/CLASSROOM E2 SOUTH PERIM (G.S2)
InputVerificationandResultsSummary/Entire Facility/Zone Summary/Area/CLASSROOM E2 WEST PERIM (G.W1)
InputVerificationandResultsSummary/Entire Facility/Zone Summary/Area/CLASSROOM E4 CORE (G.C6)	
InputVerificationandResultsSummary/Entire Facility/Zone Summary/Area/CLASSROOM E4 EAST PERIM (G.E2)	
InputVerificationandResultsSummary/Entire Facility/Zone Summary/Area/CLASSROOM E4 NORTH PERIM (G.N3)
InputVerificationandResultsSummary/Entire Facility/Zone Summary/Area/CLASSROOM E4 SOUTH PERIM (G.S1)
InputVerificationandResultsSummary/Entire Facility/Zone Summary/Area/CLASSROOM E4 WEST PERIM (G.W4)	
InputVerificationandResultsSummary/Entire Facility/Zone Summary/Area/COMPUTER CLASSROOM E4 CORE SPC (G.C5)
InputVerificationandResultsSummary/Entire Facility/Zone Summary/Area/CLASSROOM EL1 SPC (G.1)
ComponentSizingSummary/Entire Facility/Coil:Cooling:DX:SingleSpeed/Design Size Gross Rated Total Cooling Capacity/CLASSROOM G.E1 SZ-CAV COOLING COIL
ComponentSizingSummary/Entire Facility/Coil:Cooling:DX:SingleSpeed/Design Size Gross Rated Total Cooling Capacity/CLASSROOM G.NNE2 SZ-CAV COOLING COIL
ComponentSizingSummary/Entire Facility/Coil:Cooling:DX:SingleSpeed/Design Size Gross Rated Total Cooling Capacity/CLASSROOM G.SSE3 SZ-CAV COOLING COIL
ComponentSizingSummary/Entire Facility/Coil:Cooling:DX:SingleSpeed/Design Size Gross Rated Total Cooling Capacity/CLASSROOM G.W4 SZ-CAV COOLING COIL
ComponentSizingSummary/Entire Facility/Coil:Cooling:DX:SingleSpeed/Design Size Gross Rated Total Cooling Capacity/CLASSROOM E2 NORTH PERIM (G.N3) SZ-CAV COOLING COIL
ComponentSizingSummary/Entire Facility/Coil:Cooling:DX:SingleSpeed/Design Size Gross Rated Total Cooling Capacity/CLASSROOM E2 SOUTH PERIM (G.S2) SZ-CAV COOLING COIL
ComponentSizingSummary/Entire Facility/Coil:Cooling:DX:SingleSpeed/Design Size Gross Rated Total Cooling Capacity/CLASSROOM E2 WEST PERIM (G.W1) SZ-CAV COOLING COIL
ComponentSizingSummary/Entire Facility/Coil:Cooling:DX:SingleSpeed/Design Size Gross Rated Total Cooling Capacity/CLASSROOM E4 CORE (G.C6) SZ-CAV COOLING COIL
ComponentSizingSummary/Entire Facility/Coil:Cooling:DX:SingleSpeed/Design Size Gross Rated Total Cooling Capacity/CLASSROOM E4 EAST PERIM (G.E2) SZ-CAV COOLING COIL	
ComponentSizingSummary/Entire Facility/Coil:Cooling:DX:SingleSpeed/Design Size Gross Rated Total Cooling Capacity/CLASSROOM E4 NORTH PERIM (G.N3) SZ-CAV COOLING COIL
ComponentSizingSummary/Entire Facility/Coil:Cooling:DX:SingleSpeed/Design Size Gross Rated Total Cooling Capacity/CLASSROOM E4 SOUTH PERIM (G.S1) SZ-CAV COOLING COIL
ComponentSizingSummary/Entire Facility/Coil:Cooling:DX:SingleSpeed/Design Size Gross Rated Total Cooling Capacity/CLASSROOM E4 WEST PERIM (G.W4) SZ-CAV COOLING COIL	
ComponentSizingSummary/Entire Facility/Coil:Cooling:DX:SingleSpeed/Design Size Gross Rated Total Cooling Capacity/CLASSROOM EL1 SPC (G.1) SZ-CAV COOLING COIL
ComponentSizingSummary/Entire Facility/Coil:Cooling:DX:MultiSpeed/Design Size Speed 1 Gross Rated Total Cooling Capacity/CLASSROOM E1 WEST PERIM (G.W1) SZ-VAV COOLING COIL
ComponentSizingSummary/Entire Facility/Coil:Cooling:DX:MultiSpeed/Design Size Speed 1 Gross Rated Total Cooling Capacity/COMPUTER CLASSROOM E4 CORE SPC (G.C5) SZ-CRAC COOLING COIL
```
