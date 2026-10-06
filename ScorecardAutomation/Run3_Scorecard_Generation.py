import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

# ONLY EDIT PATHS HERE
# ----------------------------------------
COMPILED_DATA_DIR       = ROOT / "EP_Files" / "Compiled_Data"
SCORECARD_TEMPLATE_PATH = ROOT / "src" / "DEER_PrototypeName_ScoreCard.xlsx"
SCORECARD_PATH          = ROOT / "SpreadsheetGeneration"
# ----------------------------------------

SCRIPTS = [
    "5_Raw2Excel.py",
    "6_Tab_Import.py",
]

def run_script(script_name: str, env: dict[str, str]) -> None:
    script_path = SRC / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Missing script: {script_path}")

    print(f"\nRunning: {script_name}")
    proc = subprocess.run([sys.executable, str(script_path)], cwd=str(SRC), env=env)
    if proc.returncode != 0:
        raise SystemExit(f"FAILED: {script_name} (exit code {proc.returncode})")
    print(f"Done: {script_name}")

def main() -> None:
    env = os.environ.copy()
    env["COMPILED_DATA_DIR"] = str(COMPILED_DATA_DIR)
    env["SCORECARD_TEMPLATE_PATH"] = str(SCORECARD_TEMPLATE_PATH)
    env["SCORECARD_PATH"] = str(SCORECARD_PATH)

    for s in SCRIPTS:
        run_script(s, env)

    print("\nRun3_Scorecard_Generation finished.")

if __name__ == "__main__":
    main()