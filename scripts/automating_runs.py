# %%
import os
import subprocess
# TODO: Add option to handle existing run folders
measure_folder_path = "..\\residential measures\\SWBE006-02 Ceiling Insulation" # or "..\\commercial measures\\SWXX000-00 Measure Name", an absolute path is recommended.
os.chdir(measure_folder_path) 
current_dir = os.getcwd()
dir_content = os.listdir(current_dir)
dir_prototypes = [dir for dir in dir_content if os.path.isdir(f'{current_dir}\\{dir}')]
#%%
print("*** IMPORTANT ***\n- Always check modelkit_cmd_output.txt for potential modelkit output errors\n")
print("- This script will not override existing runs\n")

for prototype in dir_prototypes:
    print("* Running: " + prototype + "\n")
    os.chdir(f'{prototype}/')
    try:
        result = subprocess.run("modelkit rake", shell=True, check=True, capture_output=True,text=True)
        with open('modelkit_cmd_output.txt', 'w') as f:
            f.write(result.stdout)
        if "rror" in result.stdout:
            print("*** Potential error ***\n- Check modelkit_cmd_output.txt in " + prototype + " for a potential modelkit case running error\n")

    except subprocess.CalledProcessError as err:
        print("*** cmd error ***\n-Prototype '"+ prototype + "'\n-modelkit error:\n" + err.stderr)
    os.chdir("..")
# %%
