Sizing information

For this measure, additional query files are provided to document boiler auto-sizing results.

To compile the results, enter these commands after simulation.

```
cd "residential measures/SWHC004-07 Space Heating Boiler"
python "../../data transformation/result.py" . --queryfile query_boiler_sizing.txt --detailfile results-sizing-detail.csv --aggfile results-sizing-agg.csv
```

Edit the following script then run it:

```
python "../../data transformation/insert_normunits.py" 
```
