"""
Update hard-sized HVAC capacities in the residential codes files.

Values from "Res Hard Sizing parameters.xlsx" (Matt's "use the values below" block).
Tiers: CZ1-9 vs CZ10-16 (CZ16 reuses the CZ10-15 tier per direction).

- deer-mfm-1985.csv : set MFm values in the per-CZ base tables (no story split).
- deer-sfm-1975-1985.csv : set SFm 1-story values in the base tables AND append
  "... | 2 Story" tables holding the 2-story values.
Only the capacity rows (coolCap, coolShr, heatCap, heatPumpHeatCap, airflow) are
touched; everything else (units, Notes, other rows) is preserved verbatim.
"""
import re, sys

SIZING_KEYS = ("coolCap", "coolShr", "heatCap", "heatPumpHeatCap", "airflow")

# value[file][story][tier] = dict(param -> value as string)
VALUES = {
    "mfm": {
        "base": {
            "lo": {"coolCap": "8792.5",  "coolShr": "0.8", "heatCap": "17585.0", "heatPumpHeatCap": "8499.4", "airflow": "0.472"},
            "hi": {"coolCap": "10551.0", "coolShr": "0.8", "heatCap": "23446.7", "heatPumpHeatCap": "9964.8", "airflow": "0.566"},
        },
    },
    "sfm": {
        "base": {  # 1-story
            "lo": {"coolCap": "14068.0", "coolShr": "0.8", "heatCap": "23446.7", "heatPumpHeatCap": "13481.8", "airflow": "0.755"},
            "hi": {"coolCap": "17585.0", "coolShr": "0.8", "heatCap": "29308.3", "heatPumpHeatCap": "16705.7", "airflow": "0.944"},
        },
        "2story": {
            "lo": {"coolCap": "28136.0", "coolShr": "0.8", "heatCap": "46893.3", "heatPumpHeatCap": "26963.7", "airflow": "1.51"},
            "hi": {"coolCap": "35170.0", "coolShr": "0.8", "heatCap": "58616.6", "heatPumpHeatCap": "33411.5", "airflow": "1.89"},
        },
    },
}

TABLE_RE = re.compile(r'^table:\s*Res Key Prototype Values \| Climate Zone (\d+)\s*,')

def tier(cz):
    return "lo" if cz <= 9 else "hi"

def update_base(path, key):
    with open(path, encoding="utf-8-sig", newline="") as f:
        raw = f.read()
    nl = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.split(nl)
    cz = None
    changed = 0
    for i, line in enumerate(lines):
        m = TABLE_RE.match(line)
        if m:
            cz = int(m.group(1))
            continue
        if cz is None:
            continue
        parts = line.split(",")
        if parts and parts[0] in SIZING_KEYS:
            newval = VALUES[key]["base"][tier(cz)][parts[0]]
            if len(parts) > 1 and parts[1] != newval:
                parts[1] = newval
                lines[i] = ",".join(parts)
                changed += 1
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(nl.join(lines))
    print(f"{path}: updated {changed} base sizing cells")

def append_2story(path, key):
    with open(path, encoding="utf-8-sig", newline="") as f:
        raw = f.read()
    if "| 2 Story" in raw:
        print(f"{path}: '| 2 Story' tables already present, skipping append")
        return
    nl = "\r\n" if "\r\n" in raw else "\n"
    blocks = [raw.rstrip(nl)]
    for cz in range(1, 17):
        v = VALUES[key]["2story"][tier(cz)]
        blocks.append(nl.join([
            f"table:   Res Key Prototype Values | Climate Zone {cz} | 2 Story,,,,",
            "Key Values,Value, R-Value,Extent,Notes",
            f"coolCap,{v['coolCap']},,,Watts",
            f"coolShr,{v['coolShr']},,,",
            f"heatCap,{v['heatCap']},,,Watts",
            f"heatPumpHeatCap,{v['heatPumpHeatCap']},,,Watts",
            f"airflow,{v['airflow']},,,M3/s",
            "",
        ]))
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write((nl).join(blocks) + nl)
    print(f"{path}: appended 16 '| 2 Story' tables")

if __name__ == "__main__":
    base = "codes/"
    update_base(base + "deer-mfm-1985.csv", "mfm")
    update_base(base + "deer-sfm-1975-1985.csv", "sfm")
    append_2story(base + "deer-sfm-1975-1985.csv", "sfm")
    print("done")
