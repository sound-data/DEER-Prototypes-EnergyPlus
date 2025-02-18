Steps to run and processing results for this measure

Note if `result2.py` is not present, see https://github.com/sound-data/DEER-Prototypes-EnergyPlus/pull/65.

```
REM In command prompt, change directory to a clone of the repository. You may have a different path.
cd "C:/DEER-Prototypes-EnergyPlus"
```

Run simulations and generate output files

```
cd "commercial measures/SWHC046-04 Pkg HP AC Com/SWHC046-04 Pkg HP AC Com_Ex"
modelkit rake compose
REM For large number of simulations, rakefile may fail to gather results, so just run simulations.
modelkit rake run
REM Generate results-summary.csv. 
python "../../../scripts/result.py" . --queryfile "query.txt" --detailfile results-sizing-detail.csv --aggfile results-summary.csv
REM Generate customized simdata.csv
python "result2.py" . --queryfile "query_SWHC046.txt"
```

Repeat for subfolder `SWHC046-04 Pkg HP AC Com_Htl_Ex`. Use simdata.csv to perform QC, calculate UEC for all categories of load, and obtain DEER Peak results bypassing the next step.

For commercial sector weighted averages, post-process according to instructions in [../../scripts](../../scripts). The command line steps include:

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
