"""One-off: point the Windows path config of each process_*.py at this checkout.
Only the FIRST (Windows) branch's root/search_folder/results_folder are changed;
the Linux/Darwin branch is left alone.
"""
import re, glob, os

ROOT = r'"C:\\dev\\DEER-Prototypes-EnergyPlus\\commercial measures\\SWHC062-02 Occupancy Fan Controller\\"'
SEARCH = r'"SWHC062-02 Occupancy Fan Controller_Ex\\"'
RESULTS = r'PurePath("C:\\dev\\DEER-Prototypes-EnergyPlus\\commercial measures\\SWHC062-02 Occupancy Fan Controller\\scripts\\")'

FILES = [
    "process_deer_peak_cooling_sql.py",
    "process_deer_peak_sql.py",
    "process_hourly_data_multi_measure.py",
    "process_hourly_savings.py",
    "process_outdoorair_sql.py",
    "process_summary_data_multi_measure.py",
]

for fn in FILES:
    if not os.path.exists(fn):
        print(f"SKIP (missing): {fn}")
        continue
    with open(fn, encoding="utf-8", newline="") as f:
        raw = f.read()
    nl = "\r\n" if "\r\n" in raw else "\n"
    lines = raw.split(nl)
    # find the Windows branch
    win = next((i for i, l in enumerate(lines) if 'platform.system() in ["Windows"]' in l), None)
    if win is None:
        print(f"SKIP (no Windows branch): {fn}")
        continue
    done = {"root": False, "search_folder": False, "results_folder": False}
    for i in range(win + 1, len(lines)):
        if "elif" in lines[i] or lines[i].strip().startswith("else"):
            break
        m = re.match(r"^(\s*)(root|search_folder|results_folder)\s*=", lines[i])
        if m and not done[m.group(2)]:
            indent, key = m.group(1), m.group(2)
            val = {"root": ROOT, "search_folder": SEARCH, "results_folder": RESULTS}[key]
            lines[i] = f"{indent}{key} = {val}"
            done[key] = True
    with open(fn, "w", encoding="utf-8", newline="") as f:
        f.write(nl.join(lines))
    print(f"updated: {fn}  ({', '.join(k for k,v in done.items() if v)})")

print("done")
