import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

# ONLY EDIT PATHS HERE
# ----------------------------------------
ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
SRC = ROOT / "src"

# output root for all EP files generated in this run (input and output of all scripts in Run1 and Run2), the name of this folder can be changed but it should be the same in all scripts in Run1 and Run2
EP_FILES_ROOT = ROOT / "EP_Files"

# EP installation directory
EP_INSTALL_DIR = Path(os.environ.get("EP_INSTALL_DIR", r"C:\EnergyPlusV22-2-0"))
# Weather data directory within the repo
WEATHER_DIR = REPO_ROOT / "weather"

# 26 prototypes (start with hotel then go with other 25 nonres prototypes)
RUN_SETS: List[Dict[str, Path]] = [
    {
        "runs_existing_dir": REPO_ROOT / "commercial measures" / "SWXX000-00 TRC System Types" / "SWXX000-00 TRC System Types_Htl_Ex" / "runs",
        "runs_new_dir":      REPO_ROOT / "commercial measures" / "SWXX111-00 Example_SEER_AC" / "SWXX111-00 Example_SEER_AC_Htl_New" / "runs",
    },
    {
        "runs_existing_dir": REPO_ROOT / "commercial measures" / "SWXX000-00 TRC System Types" / "SWXX000-00 TRC System Types_Ex" / "runs",
        "runs_new_dir":      REPO_ROOT / "commercial measures" / "SWXX111-00 Example_SEER_AC" / "SWXX111-00 Example_SEER_AC_New" / "runs",
    },
]
# ----------------------------------------

SCRIPTS = [
    "0_EP_Input_Sort.py",
    "1_EP_Run.py",
]


def _require_dir(p: Path, label: str) -> None:
    if not p.exists() or not p.is_dir():
        raise FileNotFoundError(f"{label} not found or not a directory:\n  {p}")


def _require_file(p: Path, label: str) -> None:
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"{label} not found:\n  {p}")


def run_script(script_name: str, env: dict[str, str]) -> None:
    script_path = SRC / script_name
    _require_file(script_path, f"Missing script {script_name}")

    print(f"\nRunning: {script_name}")
    proc = subprocess.run([sys.executable, str(script_path)], cwd=str(SRC), env=env)
    if proc.returncode != 0:
        raise SystemExit(f"FAILED: {script_name} (exit code {proc.returncode})")
    print(f"Done: {script_name}")


def build_env_for_runset(base_env: dict[str, str], runset: Dict[str, Path]) -> dict[str, str]:
    runs_existing_dir = Path(runset["runs_existing_dir"])
    runs_new_dir = Path(runset["runs_new_dir"])

    _require_dir(SRC, "SRC folder")
    _require_dir(runs_existing_dir, "RUNS_EXISTING_DIR")
    _require_dir(runs_new_dir, "RUNS_NEW_DIR")
    _require_dir(WEATHER_DIR, "WEATHER_DIR")
    _require_dir(EP_INSTALL_DIR, "EP_INSTALL_DIR")

    # One merged output folder for all run sets
    EP_FILES_ROOT.mkdir(parents=True, exist_ok=True)

    env = base_env.copy()
    env["RUNS_EXISTING_DIR"] = str(runs_existing_dir)
    env["RUNS_NEW_DIR"] = str(runs_new_dir)
    env["EP_FILES_ROOT"] = str(EP_FILES_ROOT)
    env["EP_INSTALL_DIR"] = str(EP_INSTALL_DIR)
    env["WEATHER_DIR"] = str(WEATHER_DIR)
    return env


def main() -> None:
    base_env = os.environ.copy()

    for runset in RUN_SETS:
        env = build_env_for_runset(base_env, runset)
        for s in SCRIPTS:
            run_script(s, env)

    print("\nRun1_pre_data_extraction finished.")


if __name__ == "__main__":
    main()