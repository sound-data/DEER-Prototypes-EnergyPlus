Processing steps for this measure

```
cd C:\DEER-Prototypes-EnergyPlus
cd "commercial measures/SWHC027-08 Package Terminal ACHP"
modelkit rake run
python result2.py --queryfile "query_SWHC027_com.txt"
```

Then find "simdata.csv". Use Excel workbook provided in eTRM to compute UEC and UES.

Assumptions:

- Gst modeled as Htl
- Com modeled as OfL

