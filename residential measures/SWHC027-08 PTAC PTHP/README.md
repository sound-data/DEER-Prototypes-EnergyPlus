Processing steps for this measure

```
cd C:\DEER-Prototypes-EnergyPlus
cd "residential measures/SWHC027-08 PTAC PTHP"
modelkit rake run
python result2.py --queryfile "query_SWHC027_res.txt"
```

Then find "simdata.csv". Use Excel workbook provided in eTRM to compute UEC and UES.
