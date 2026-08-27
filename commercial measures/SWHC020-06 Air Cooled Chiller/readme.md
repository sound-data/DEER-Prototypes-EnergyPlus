SWHC020 Air-Cooled Screw Chiller, Path A.

# Setup
For this measure, we have made the following setup:

- Added chiller performance curves (in chw.pxt, compatible with Chiller:Electric:EIR type chiller object) for the base and measure cases selected from the set of performance curves in EnergyPlus library "[chiller.idf](https://github.com/NREL/EnergyPlus/tree/develop/datasets)".

- Measure setup for chillers reflects distinct offerings varying by chiller type, capacity, and tier since code requirements vary by chiller type and capacity.

Why we need new performance curves and how we selected them:

- Modeling the measure requires controlling both COP and IPLV. Although COP is a direct input to the model, IPLV is an output resulting from COP and performance curves.

- For the base and measure case model, the prototype’s default performance curves do not yield an IPLV/COP ratio close to the base and measure case defined in the measure. Using a workbook to implement the IPLV calculations, we tabulated the IPLV/COP ratio for chiller models provided by EPlus in a reference file. Then, we selected a model matching the chiller type with a Chiller:Electric:EIR object type and IPLV closest to the base and measure cases definition. During testing, we also rejected a chiller model for which simulation yielded unphysical results at part load.

# Post-processing

Query files govern the output from result scraping scripts.

* Result-summary.csv files are output automatically by `modelkit rake results`.
* A python script in this repository can be used to regenerate or disaggregate results.

Sample query files provided in this folder demonstrate examples of items that can be queried. Available items are those that appear in the `instance-out.sql` SQLite tabular output report file after simulation, and similar entries in `instance-tbl.htm` (HTML).

To regenerate a result file or disaggregate sizing results, use one of these command line statements after simulation.

1. Using modelkit built-in results

```
cd C:/DEER-Prototypes-EnergyPlus/
cd "commercial measures/SWHC020-06 Air Cooled Chiller/SWHC020-06 Air Cooled Chiller_Ex"
modelkit rake results
```

Now, check the file `results-summary.csv`.

2. Using python script to reproduce `results-summary.csv`.

```
cd C:/DEER-Prototypes-EnergyPlus/
cd "commercial measures/SWHC020-06 Air Cooled Chiller/SWHC020-06 Air Cooled Chiller_Ex"
python "../../../scripts/result.py" "."
```

The python script has some limitations compared to Modelkit.

1. Does not recognize "hardsize" simulation runs where naming pattern differs (instance-hardsize-out.sql).
2. Does not recognize missing simulation runs.

3. Using python script to extract additional information for manual review.

```
cd C:/DEER-Prototypes-EnergyPlus/
python "scripts/result.py" "commercial measures/SWHC020-06 Air Cooled Chiller/" --queryfile "querylibrary/query_benchmark.txt" --detailfile "commercial measuresSWHC020-06 Air Cooled Chiller/results-sizing-detail.csv" --aggfile "commercial measures/SWHC020-06 Air Cooled Chiller/results-sizing-agg.csv"
```
