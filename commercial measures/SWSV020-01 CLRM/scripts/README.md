The python script gel_c;rm_daya.py extracts the required data from the instance-out.sql sqlite database for each simulation run.

No additional python packages are need.

The script needs to be edited to point to the results as indicated, note the use of forward slahes:

def main():

    def search_directories(path, file_name):
        paths = []
        for dir_name, sub_dirs, files in Path.walk(path, on_error=print):
            for file in files:
                if file.lower() == file_name:
                    paths.append(PurePath.joinpath(dir_name, file))

        return paths

    if platform.system() in ["Windows"]:
        # root of the DEER package install
    --> root = PurePath("C:/DEER-Prototypes-EnergyPlus")
        # measure to search
    --> search_folder = PurePath("commercial measures/SWSV020-01 CLRM")
        # sqlite database to use
        input_file = "instance-out.sql"
        # where to write the results
    --> results_folder = "C:/CLRM Results"
        results_file = "CLRM_data.csv"
    elif platform.system() in ["Linux", "Darwin"]:
        root = ""
        search_folder = ""
        input_file = "instance-out.sql"
        results_folder = ""
        results_file = "CLRM_data.csv"
    else:
        print("What, exactly, are you running this on!")
        exit()

    # get the files
    search_path = PurePath.joinpath(root, search_folder)
    all_files = search_directories(search_path, input_file)

    output_file = PurePath.joinpath(PurePath(results_folder), PurePath(results_file))
    offset = len(PurePath(root).parts) + len(PurePath(search_folder).parts)
    process(offset, all_files, output_file)