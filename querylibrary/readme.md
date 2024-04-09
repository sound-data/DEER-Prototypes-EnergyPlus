Query files govern the output from result scraping scripts.

* Result-summary.csv files are output automatically by `modelkit rake results`.
* A python script in this repository can be used to regenerate or disaggregate results.

Sample query files provided in this folder demonstrate examples of items that can be queried. Available items are those that appear in the `instance-out.sql` SQLite tabular output report file after simulation, and similar entries in `instance-tbl.htm` (HTML).

To regenerate a result file or disaggregate sizing results, use one of these command line statements after simulation.

1. Using modelkit built-in results

```
cd C:/DEER-Prototypes-EnergyPlus/
cd "commercial measures/SWXX000-00 Measure Name/SWXX000-00 Measure Name_1975"
modelkit rake results
```

Now, check the file `results-summary.csv`.

2. Using python script to reproduce `results-summary.csv`.

```
cd C:/DEER-Prototypes-EnergyPlus/
cd "commercial measures/SWXX000-00 Measure Name/SWXX000-00 Measure Name_1975"
python "../../../scripts/result.py" "."
```

The python script has some limitations compared to Modelkit.

1. Does not recognize "hardsize" simulation runs where naming pattern differs (instance-hardsize-out.sql).
2. Does not recognize missing simulation runs.

3. Using python script to extract additional information for manual review.

```
cd C:/DEER-Prototypes-EnergyPlus/
python "scripts/result.py" "commercial measures/SWXX000-00 Measure Name/" --queryfile "querylibrary/query_benchmark.txt" --detailfile "commercial measures/SWXX000-00 Measure Name/results-sizing-detail.csv" --aggfile "commercial measures/SWXX000-00 Measure Name/results-sizing-agg.csv"
```
