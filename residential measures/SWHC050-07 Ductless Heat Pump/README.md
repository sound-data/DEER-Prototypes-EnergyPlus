# SWHC050 Ductless Heat Pump, Residential

## Cohorts and case names

SWHC044 shares some measure case models with SWHC050 but does not have its own subfolder.
Tables below show the origin of TechIDs present in this folder.

BldgType-BldgVint | Cohort | Prototype root | Introduced
--- | --- | --- | ---
DMo | DMo&0&rDXHP&Ex&dxHP_equip__spltHP-SEER-BA | DMo-HP/templates/root.pxt | By DNV for SWHC050 (Dv24)
DMo | DMo&0&rDXHP&New&dxHP_equip__spltHP-SEER-BA | Dmo-HP-New/templates/root.pxt | By DNV for SWHC050 (Dv24)
DMo | DMo&0&rDXHP&Ex&dxHP_equip__spltHP-SEER-BA&dxAC_equip__RoomAC | DMo-PTAC/templates/root.pxt | By DNV for SWHC050 (Dv24)
DMo | DMo&0&rDXGF&Ex&SpaceHtg_eq__GasFurnace | DMo/templates/root.pxt | By Solaris Technical for SWHC044
MFm_Ex | MFm&0&rDXHP&Ex&dxHP_equip__spltHP-SEER-BAp | MFm-1985-HP/templates/root.pxt | By DNV for SWHC050 (Dv24)
MFm_Ex | MFm&0&rDXHP&Ex&dxHP_equip__spltHP-SEER-BA&dxAC_equip__RoomAC | MFm-1985-PTAC/templates/root_PTAC.pxt | By DNV for SWHC050 (Dv24)
MFm_Ex | MFm&0&rDXGF&Ex&SpaceHtg_eq__GasFurnace | MFm-1985/templates/root.pxt | By Solaris Technical for SWHC044
MFm_New | MFm&0&rDXHP&New&dxHP_equip__spltHP-SEER-BA | MFm-New-HP/templates/root_highSEER.pxt | By DNV for SWHC050 (Dv24)
SFm 1975 | SFm&1&rDXHP&Ex&dxHP_equip__spltHP-SEER-BA | SFm-1 Story-1975-HP/templates/root.pxt | By DNV for SWHC050 (Dv24)
SFm 1975 | SFm&2&rDXHP&Ex&dxHP_equip__spltHP-SEER-BA | SFm-2 Story-1975-HP/templates/root.pxt | By DNV for SWHC050 (Dv24)
SFm 1975 | SFm&1&rDXHP&Ex&dxHP_equip__spltHP-SEER-BA&dxAC_equip__RoomA | SFm-1 Story-1975-PTAC/templates/root.pxt | By DNV for SWHC050 (Dv24)
SFm 1975 | SFm&2&rDXHP&Ex&dxHP_equip__spltHP-SEER-BA&dxAC_equip__RoomAC | SFm-2 Story-1975-PTAC/templates/root.pxt | By DNV for SWHC050 (Dv24)
SFm 1975 | SFm&1&rDXGF&Ex&SpaceHtg_eq__GasFurnace | SFm-1 Story-1975/templates/root.pxt | By Solaris Technical for SWHC044
SFm 1975 | SFm&2&rDXGF&Ex&SpaceHtg_eq__GasFurnace | SFm-2 Story-1975/templates/root.pxt | By Solaris Technical for SWHC044
SFm 1985 | SFm&1&rDXHP&Ex&dxHP_equip__spltHP-SEER-BA | SFm-1 Story-1985-HP/templates/root.pxt | By DNV for SWHC050 (Dv24)
SFm 1985 | SFm&2&rDXHP&Ex&dxHP_equip__spltHP-SEER-BA | SFm-2 Story-1985-HP/templates/root.pxt | By DNV for SWHC050 (Dv24)
SFm 1985 | SFm&1&rDXHP&Ex&dxHP_equip__spltHP-SEER-BA&dxAC_equip__RoomAC | SFm-1 Story-1985-PTAC/templates/root.pxt | By DNV for SWHC050 (Dv24)
SFm 1985 | SFm&2&rDXHP&Ex&dxHP_equip__spltHP-SEER-BA&dxAC_equip__RoomAC | SFm-2 Story-1985-PTAC/templates/root.pxt | By DNV for SWHC050 (Dv24)
SFm 1985 | SFm&1&rDXGF&Ex&SpaceHtg_eq__GasFurnace | SFm-1 Story-1985/templates/root.pxt | By Solaris Technical for SWHC044
SFm 1985 | SFm&2&rDXGF&Ex&SpaceHtg_eq__GasFurnace | SFm-2 Story-1985/templates/root.pxt | By Solaris Technical for SWHC044
SFm New | SFm&1&rDXHP&New&dxHP_equip | SFm-1 Story-New-HP/templates/root.pxt | By DNV for SWHC050 (Dv24)
SFm New | SFm&2&rDXHP&New&dxHP_equip | SFm-2 Story-New-HP/templates/root.pxt | By DNV for SWHC050 (Dv24)

Representative Cohort | Case | Applicable building types | Applicable vintages | Used in measure | Comments
--- | --- | --- | --- | --- | ---
DMo&0&rDXGF&Ex&SpaceHtg_eq__GasFurnace | RG-SpaceHtg_eq-GasFurnace-rDXGF-AFUE75-PoweredFan | DMo, SFm, MFm | Ex | SWHC044 | Added by Solaris Technical for SWHC044
DMo&0&rDXGF&Ex&SpaceHtg_eq__GasFurnace | RG-SpaceHtg_eq-GasFurnace-rDXGF-AFUE82-PoweredFan | DMo, SFm, MFm | Ex | SWHC044 | Added by Solaris Technical for SWHC044
DMo&0&rDXHP&Ex&dxHP_equip__spltHP-SEER-BA | Pre-RE-HV-DHP-13S | DMo, SFm, MFm | Ex, New | SWHC050 | Base case for SWHC050. Added by DNV.
DMo&0&rDXHP&Ex&dxHP_equip__spltHP-SEER-BA | Std-RE-HV-DHP-15S | DMo, SFm, MFm | Ex, New | SWHC050 | Base case for SWHC050. Added by DNV.
DMo&0&rDXHP&Ex&dxHP_equip__spltHP-SEER-BA | Msr-RE-HV-DHP-16S | DMo, SFm, MFm | Ex, New | SWHC050 | Base case for SWHC050. Added by DNV.
DMo&0&rDXHP&Ex&dxHP_equip__spltHP-SEER-BA | Msr-RE-HV-DHP-17S | DMo, SFm, MFm | Ex, New | SWHC050 | Base case for SWHC050. Added by DNV.
DMo&0&rDXHP&Ex&dxHP_equip__spltHP-SEER-BA | Msr-RE-HV-DHP-18S | DMo, SFm, MFm | Ex, New | SWHC050 | Base case for SWHC050. Added by DNV.
DMo&0&rDXHP&Ex&dxHP_equip__spltHP-SEER-BA | Msr-RE-HV-DHP-19S | DMo, SFm, MFm | Ex, New | SWHC050 | Base case for SWHC050. Added by DNV.
DMo&0&rDXHP&Ex&dxHP_equip__spltHP-SEER-BA | Msr-RE-HV-DHP-20S | DMo, SFm, MFm | Ex, New | SWHC050 | Base case for SWHC050. Added by DNV.
DMo&0&rDXHP&Ex&dxHP_equip__spltHP-SEER-BA | Msr-RE-HV-DHP-21S | DMo, SFm, MFm | Ex, New | SWHC050 | Base case for SWHC050. Added by DNV.
DMo&0&rDXHP&Ex&dxHP_equip__spltHP-SEER-BA | Msr-RE-HV-DHP-22S | DMo, SFm, MFm | Ex, New | SWHC050 | Base case for SWHC050. Added by DNV.
DMo&0&rDXHP&Ex&dxHP_equip__spltHP-SEER-BA&dxAC_equip__RoomAC | Pre-RE-HV-RoomAC-9.0E-ERheat | DMo, SFm, MFm | Ex, New | SWHC050 | Base case for SWHC050. Added by DNV.
DMo&0&rDXHP&Ex&dxHP_equip__spltHP-SEER-BA&dxAC_equip__RoomAC | Std-RE-HV-RoomAC-9.8E-ERheat | DMo, SFm, MFm | Ex, New | SWHC050 | Base case for SWHC050. Added by DNV.

## Query file for normalizing units

The file `query_swhc050.txt` includes queries for cooling and heating capacity for the models generated in this folder. After running simulations, the user may gather outputs using the following command:

```
cd "residential measures/SWHC050-07 Ductless Heat Pump"
python result2.py -q query_swhc050.txt
```
