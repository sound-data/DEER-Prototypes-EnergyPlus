SWHC001 Wall Furnace Measure
Prepared by Solaris Technical, Janik Somaiya - 2026-07-23

This document describes the steps necessary to reproduce simulations and model outputs for this measure.

Step 1
cd C:\DEER-Prototypes-EnergyPlus
cd "residential measures/SWHC001-08 Wall Furnace"
modelkit rake

Confirm Modelkit completed runs for:
DMo
MFm_Ex
SFm_1975
SFm_1985

Step 2
python result2.py --queryfile "query_Wall Furnace.txt"

Confirm script generated 'simdata.csv'.

The final simulation output file for this measure is 'simdata.csv'.


