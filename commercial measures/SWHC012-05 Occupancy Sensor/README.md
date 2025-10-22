# SWHC012 Occupancy Sensor, Classroom

This document describes the steps necessary to reproduce simulations and model outputs for this measure.

Prepared by Solaris Technical, Kelsey Yen - 2025-10-22


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


To extract the necessary area and cooling coil capacity for all classroom types, each classroom area and cooling coil name was added to query_SWHC012.txt to output the area and cooling coil capacity in the simdata results. The areas and cooling coil capacities were then summed respectively and used as the normalizing units for the energy savings calculations. Note that the following code includes area and cooling capacities from EPr, ERC, and ESe building types.

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

