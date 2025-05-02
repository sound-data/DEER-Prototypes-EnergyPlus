
# Water-Cooled Chiller Statewide Measure Simulation

This repository supports the simulation and post-processing workflow for evaluating the **statewide water-cooled chiller energy efficiency measure**.

## 📁 Project Structure

```
/
├── query_wcc.txt
├── result_wcc.py
├── result2.py
└── simdata.csv (generated)
```

## 🏗️ Simulation Setup

No special instructions are required for setting up or running the EnergyPlus models. Standard simulation procedures apply.

## 🧾 Post-Processing Instructions

### Chiller Cooling Capacity Extraction

To normalize results by cooling capacity, the following procedure is used:

1. **Edit the query file**  
   Append the following output variables to `query_wcc.txt`:

   ```
   Chiller:Electric:EIR/Design Size Reference Capacity
   Chiller:Electric:ReformulatedEIR/Design Size Reference Capacity
   ```

2. **Run the post-processing script**  
   Execute `result2.py` to extract and sum the capacities from all simulation runs.

   ```bash
   python result2.py
   ```

   The resulting file `simdata.csv` will contain chiller cooling capacities in watts (W).

### IPLV/COP Ratio Verification

To validate model inputs related to chiller efficiency:

- `query_wcc.txt` includes a line that extracts the modeled **IPLV** value.
- `result_wcc.py` processes this data and outputs it to `simdata.csv`.

This enables verification of the **IPLV-to-COP ratio** as applied during measure setup.

## 📝 Notes

- The scripts assume a consistent directory structure and naming convention across simulation result files.
- `simdata.csv` includes data from all simulation runs, with fields needed for both normalization and QA/QC.

## 👤 Authors & Contributors

Measure development and scripting by the Solaris-Technical team.
Nicholas Fette "nfette@solaris-technical.com"
Behzad Salimian Rizi "brizi@solaris-technical.com"
