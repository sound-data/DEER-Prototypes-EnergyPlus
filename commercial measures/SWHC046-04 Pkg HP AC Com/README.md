# Steps to run simulations, gather outputs, and post-process results for this measure

Note if `result2.py` is not present, see https://github.com/sound-data/DEER-Prototypes-EnergyPlus/pull/65.

```
REM In command prompt, change directory to a clone of the repository. You may have a different path.
cd "C:/DEER-Prototypes-EnergyPlus"
```

## 1. Run simulations and generate output files

### 1.1. Run simulations

```
cd "commercial measures/SWHC046-04 Pkg HP AC Com/SWHC046-04 Pkg HP AC Com_Ex"
modelkit rake compose
REM For large number of simulations, rakefile may fail to gather results, so just run simulations.
modelkit rake run
```

Then, repeat for subfolder `SWHC046-04 Pkg HP AC Com_Htl_Ex`.

Optionally, while `modelkit rake run` is running, use how-to-track-progress.py to see a progress bar.

Optionally, after model runs are complete, use "QC incomplete simulations.ipynb" to get statistics on failed simulations and a count of warning and error messages from EnergyPlus.

### 1.2. Gather summary output files for raw usage and QC

#### Generate results-summary.csv (using standard query file, for use with post-process scripts) 

Option 1 (using modelkit). If option 1 fails, try option 2.

```
modelkit rake results
```

Option 2 (using equivalent python script)

```
cd "commercial measures/SWHC046-04 Pkg HP AC Com/SWHC046-04 Pkg HP AC Com_Ex"
python "../../../scripts/result.py" . --queryfile "query.txt" --detailfile results-sizing-detail.csv --aggfile results-summary.csv
```

Note that the python script has a side effect of outputting a file with disaggregated quantities for any query items that represent aggregate totals, such as cooling capacity of all coils.

Repeat for each subfolder (`SWHC046-04 Pkg HP AC Com_Ex` and `SWHC046-04 Pkg HP AC Com_Htl_Ex`).

#### Generate customized simdata.csv

```
cd "commercial measures/SWHC046-04 Pkg HP AC Com/"
python "result2.py" . --queryfile "query_SWHC046_QC.txt"
```

The dot represents the current directory. This script runs outside the vintage subfolders, so only run this script once.

Use simdata.csv to perform QC, calculate UEC for all categories of load, and obtain DEER Peak Demand results bypassing the post-processing tool.

## 2. Determine cooling capacity subject to measure

### 2.1. Extract cooling capacity from every coil in model

Extract results to results-sizing-detail.csv

```
cd "commercial measures/SWHC046-04 Pkg HP AC Com/SWHC046-04 Pkg HP AC Com_Ex"
python "../../../scripts/result.py" . --queryfile "query_SWHC046_sizing.txt" --detailfile results-sizing-detail.csv --aggfile results-sizing-agg.csv
```

### 2.2. Filter cooling capacity

Filter and aggregate results into sizing_agg_filtered.csv

```
cd "commercial measures/SWHC046-04 Pkg HP AC Com/SWHC046-04 Pkg HP AC Com_Ex"
python result_filtered.py
```

### 2.3. Repeat for each vintage subfolder

SWHC046-04 Pkg HP AC Com_Ex

## 3. Apply post-processing for commercial sector weighted average (with normalizing units from models)

For commercial sector weighted averages, post-process according to instructions in [../../scripts](../../scripts). The command line steps include:

### 3.1 Run data transformation script to get current_msr_mat, sim_annual, and sim_hourly_wb

First, copy the DEER_EnergyPlus_Modelkit_Measure_list workbook from this folder into "C:/DEER-Prototypes-EnergyPlus/scripts/data transformation". Then, follow the standard procedures for data transformation per instructions in [../../scripts](../../scripts).

```
cd "C:/DEER-Prototypes-EnergyPlus"
cd "scripts/data transformation"
REM Generate current_msr_mat.csv, sim_annual.csv, and sim_hourly_wb.csv.
python Com.py
REM Optionally, copy the outputs to the measure folder
copy "current_msr_mat.csv" "commercial measures/SWHC046-04 Pkg HP AC Com"
copy "sim_annual.csv" "commercial measures/SWHC046-04 Pkg HP AC Com"
copy "sim_hourly_wb.csv" "commercial measures/SWHC046-04 Pkg HP AC Com"
```

### 3.2. Insert results from cooling capacity into sim_annual

The script insert_normunits.py inserts results from sizing_agg_filtered.csv into a copy of sim_annual.csv and saves it to sim_annual_withunits.csv. The command line pattern for this script is:

```
python insert_normunits.py <sizing_column> <normunit> <conversion_factor> <measure_name>
```

For this measure the options are
- `<sizing_column>` = "DX Coil Cooling Capacity Single and Multi Speed [W]"
- `<normunit>` = Cap-Ton
- `<conversion_factor>` = (W thermal / 1 ton cooling) = 3516.85284
- `<measure_name>` = "Pkg HP AC Com"

First copy the sizing_agg_filtered.csv into the scripts folder. Then run the script:

```
python insert_normunits.py "DX Coil Cooling Capacity Single and Multi Speed [W]" Cap-Ton 3516.85284 "Pkg HP AC Com"
```

At this point, you should have an updated copy of sim_annual.csv with cooling capacity in the normalizing units column.

### 3.3. Run commercial post-processing script

Refer to standard instructions in [../../scripts](../../scripts).
