
# Water-Cooled Chiller Statewide Measure Simulation

This repository supports the simulation and post-processing workflow for evaluating the **statewide water-cooled chiller energy efficiency measure**.

## Prototype and template customization for this measure

Initial work (2024)
- Added water-cooled chiller performance curve definitions from Energy Solutions research and from EnergyPlus library file "[chiller.idf](https://github.com/NREL/EnergyPlus/tree/develop/datasets)".
- Added new parameter `(chw_)wc_option` to allow switching water-cooled chiller object type from Chiller:Electric:ReformulatedEIR to Chiller:Electric:EIR (in the `chw.pxt` template).
- Added new parameter `(chw_)chiller_eir_fplr_type` to support Lift type EIR curve as a function of PLR. Initially, we do not propose linking this to chiller_model (in chw.pxt).
- Introduced query file for collecting data for IPLV and chiller cooling capacity (query_wcc.txt).
- Measure setup for chillers reflects distinct offerings varying by chiller type, capacity, and tier since code requirements vary by chiller type and capacity.

Revisions (2025)
- Apply 2025 Title 24 updates to SWHC005.
- Tech runs for screw type chiller are defined but skipped for simulation.

### Performance curves proposed to add to chw.pxt

Measure case performance curve candidates
- "Model 9 WC Chiller" (ReformEIRChiller type, EIR_fPLR curve type = Lift, curves provided by email Energy Solutions)
- "Model 7 WC Chiller" (ReformEIRChiller type, EIR_fPLR curve type = Lift, curves provided by email Energy Solutions)
Base case performance curve candidates from EnergyPlus dataset chillers.idf
- Added "WC Cent Carrier 19XR 1234kW/5.39COP/VSD" (ElectricEIRChiller type)
- Added "WC Trane RTHB 1051kW/5.05COP/Valve" (ElectricEIRChiller type)
- Added "ReformEIRChiller WC Cent Carrier 19XR 1234kW/5.39COP/VSD" (ReformEIRChiller type)
- Added "ReformEIRChiller Screw WC Carrier 23XL 1062kW/5.50COP/Valve" (ReformEIRChiller type)

## 📁 Project Structure

```
/
├── query_wcc.txt
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
   python result2.py . -q query_wcc.txt
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
