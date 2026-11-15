#Run Com_SWHC062.py once per building-type workbook in DEER_EnergyPlus_Modelkit_Measure_list_working_dir,
#stashing each pass's outputs under outputs_by_bldgtype/<BldgType>/.
#Each pass points COM_WORKBOOK at the per-type workbook and sets COM_BT_FILTER so
#only that building type's runs are read. The shared measure-list workbook is
#never touched.
import os, shutil, subprocess, sys, time

os.chdir(os.path.dirname(os.path.abspath(__file__)))

WB_DIR = "DEER_EnergyPlus_Modelkit_Measure_list_working_dir"
OUT = "outputs_by_bldgtype"
OUTPUTS = [
    "current_msr_mat.csv",
    "sim_annual.csv",
    "sim_hourly_wb.csv",
    "CEDARS_LoadShape_Com.zip",
    "CEDARS_ls_annual_loads_Com.csv",
]
# CEDARS_long_ls_Com.csv duplicates the zip content uncompressed (~hundreds of MB
# per building type); deleted after each pass instead of stashed.
DISCARD = ["CEDARS_long_ls_Com.csv"]

wbs = sorted(f for f in os.listdir(WB_DIR) if f.endswith(".xlsx") and not f.startswith("~"))
print(f"{len(wbs)} workbooks to process", flush=True)

failures = []
for wb in wbs:
    bt = wb.rsplit(" ", 1)[-1][:-5]  # '... OFC EPr.xlsx' -> 'EPr'
    dest = os.path.join(OUT, bt)
    os.makedirs(dest, exist_ok=True)
    env = dict(os.environ, COM_BT_FILTER=bt,
               COM_WORKBOOK=os.path.abspath(os.path.join(WB_DIR, wb)))
    t0 = time.time()
    with open(os.path.join(dest, "com_run.log"), "w") as log:
        r = subprocess.run([sys.executable, "Com_SWHC062.py"], stdout=log, stderr=subprocess.STDOUT, env=env)
    moved = []
    for f in OUTPUTS:
        if os.path.exists(f):
            shutil.move(f, os.path.join(dest, f))
            moved.append(f)
    for f in DISCARD:
        if os.path.exists(f):
            os.remove(f)
    status = "OK" if r.returncode == 0 else f"FAIL rc={r.returncode}"
    if r.returncode != 0:
        failures.append(bt)
    print(f"{bt}: {status}, {len(moved)}/{len(OUTPUTS)} outputs, {time.time()-t0:.0f}s", flush=True)

print(f"done. failures: {failures if failures else 'none'}", flush=True)
sys.exit(1 if failures else 0)
