This is the setup for simulating the statewide measure for cogged v-belts.

There are no special instructions for measure setup or running.

For post-processing, to collect normalizing units from results, measure developers introduced additional files to collect and sum relevant coil sizes:
- query_Captons.txt for use with "scripts/result.py" will output "results-sizing-detail.csv" after simulation.
- coil_list.xlsx tabulates the cooling coils relevant to the measure, created manually by inspection.
- Python script result_filtered.py reads "results-sizing-detail.csv" and "coil_list.xlsx", filters the coil sizes, and aggregates the result into "sizing_agg_filtered.csv"

For simdata (energy usage breakdown):
- query.txt for use with "scripts/result2.py"
