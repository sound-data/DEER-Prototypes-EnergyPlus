# Extract CZ2025 Weather Files

Use "Extract weather files.ipynb" to extract .epw files from CALMAC and design day files from One Building.

## Sources
### CZ2025 weather files: CALMAC
CALMAC file is a nested zip file containing folders for each weather station. Each weather station file contains the associated weather files (.epw, .BINM, .FIN4).
https://www.calmac.org/weather/CZ2025/CZ2025_ALL.zip

### CZ2025 DDY files: OneBuilding
One Building does not have a nested zip file for all weather stations. The script directly links URLs for each relevant weather station to extract .ddy files. 
https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/California_Climate_Zones/index.html#IDCalifornia_CTZ_2025-

## Process
The stations associated with each climate zone are mapped as cec_cz_map_cz2025, based on the Title 24 Energy Code Accounting Report. The script downloads the zip files, matches the file names to the stations listed in the map, and extracts the relevant .epw and .ddy files. The files are saved in the CZ2025 folder and named as "CZXX"-"station name"-"station number" with the relevant file extension (.epw, .ddy).

## Output
The output is a folder (CZ2025) with .epw and .ddy files for climate zones CZ01-CZ16.