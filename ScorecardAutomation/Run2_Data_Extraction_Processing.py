import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
SRC = ROOT / "src"

# ONLY EDIT PATHS HERE
# ----------------------------------------
SCORECARD_FOLDER = ROOT                 # ...\ScorecardAutomation
PXT_ROOT_PATH    = REPO_ROOT / "prototypes"

EP_FILES_ROOT    = SCORECARD_FOLDER / "EP_Files"
EXTRACTED_RAW_DIR = EP_FILES_ROOT / "Extracted_Data_Raw"
INTERMEDIATE_DIR  = EP_FILES_ROOT / "Extracted_Data_Intermediate_Processed"
COMPILED_DIR      = EP_FILES_ROOT / "Compiled_Data"
# ----------------------------------------

SCRIPTS = [
    "2_Main.py",
    "3_Intermediate_Process.py",
    "4_Merge_Result.py",
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

    env["SCORECARD_FOLDER"] = str(SCORECARD_FOLDER)
    env["PXT_ROOT_PATH"]    = str(PXT_ROOT_PATH)
    env["EP_FILES_ROOT"]    = str(EP_FILES_ROOT)
    env["EXTRACTED_RAW_DIR"]= str(EXTRACTED_RAW_DIR)
    env["INTERMEDIATE_DIR"] = str(INTERMEDIATE_DIR)
    env["COMPILED_DIR"]     = str(COMPILED_DIR)

    for s in SCRIPTS:
        run_script(s, env)

    print("\nRun2_data_extraction_processing finished.")

if __name__ == "__main__":
    main()