import platform
import csv
import re
from pathlib import Path, PurePath


def make_search_paths(root, folder):
    return PurePath.joinpath(PurePath(root), PurePath(folder))


def search_directories(path, file_name):
    paths = []
    for dir_name, sub_dirs, files in Path.walk(path):
        for file in files:
            if file.lower() == file_name:
                paths.append(PurePath.joinpath(dir_name, file))

    return paths


def by_batch(offset, all_files):
    batches = {}
    for file in all_files:
        parts = PurePath(file).parts
        building_type = parts[offset + 2]
        # print(building_type)
        cz = parts[offset + 1]
        # print(cz)
        run = parts[offset + 3].split("-")
        measure = run[0]
        system_type = run[1]
        type = run[2]
        if building_type not in batches.keys():
            batches[building_type] = {}
        if measure not in batches[building_type].keys():
            batches[building_type][measure] = {}
        if system_type not in batches[building_type][measure].keys():
            batches[building_type][measure][system_type] = {}
        if type not in batches[building_type][measure][system_type].keys():
            batches[building_type][measure][system_type][type] = []
        batches[building_type][measure][system_type][type].append(file)

    return batches


def should_ignore(building_type, system_type, column):

    if system_type in ["cDXGF", "cDXHP", "cPTAC"]:
        if not re.search("SZ-CAV", column, flags=re.IGNORECASE):
            return True
        if building_type in ["EPr", "ESe", "EUn", "MBT", "RFF", "RSD", "RtL", "Htl"]:
            if re.search("KITCHEN", column, flags=re.IGNORECASE):
                return True
        if building_type in ["EUn"]:
            if re.search("DORM", column, flags=re.IGNORECASE):
                return True
        if building_type in ["Htl"]:
            if re.search("GUESTRM", column, flags=re.IGNORECASE):
                return True
    if system_type in ["cPVVG"]:
        if not re.search("SZ-VAV", column, flags=re.IGNORECASE):
            return True
        if building_type in ["ECC", "Htl"]:
            if re.search("KITCHEN", column, flags=re.IGNORECASE):
                return True
        if building_type in ["MBT"]:
            if re.search("LAB", column, flags=re.IGNORECASE):
                return True
        if re.search(" ATU", column, flags=re.IGNORECASE):
            return True
    return False


def process(batch, offset):

    result_rows = []
    for file in batch:
        result_row = {}
        parts = PurePath(file).parts
        building_type = parts[offset + 2]
        cz = parts[offset + 1]
        run = parts[offset + 3].split("-")
        measure = run[0]
        system_type = run[1]
        type = run[2]
        result_row["Filename"] = file
        result_row["Measure"] = measure
        result_row["BldgType"] = building_type
        result_row["BldgLoc"] = cz
        result_row["BldgHVAC"] = system_type
        result_row["Run Type"] = type

        with open(file, newline="") as csvfile:
            reader = csv.reader(csvfile)
            end_use_flag = False
            unmet_hours_flag = False
            building_area_flag = False
            report_flag = False
            cooling_flag = False
            heating_flag = False
            cooling_total_capacity = 0.0
            heating_total_capacity = 0.0
            for row in reader:
                if len(row) != 0:
                    if row[0] == "End Uses":
                        end_use_flag = True
                        continue
                    if row[0] == "Time Setpoint Not Met":
                        unmet_hours_flag = True
                        continue
                    if row[0] == "Building Area":
                        building_area_flag = True
                        continue
                    if row[0] == "REPORT:" and row[1] == "Equipment Summary":
                        report_flag = True
                        continue
                    if report_flag and row[0] == "Cooling Coils":
                        cooling_flag = True
                        continue
                    elif report_flag and row[0] == "Heating Coils":
                        heating_flag = True
                        continue
                    elif report_flag and (not cooling_flag and not heating_flag):
                        continue
                    if report_flag and cooling_flag:
                        if row[0] == "" and row[1] != "":
                            # print(row)
                            if not should_ignore(building_type, system_type, row[1]):
                                cooling_total_capacity += float(row[4])
                            continue
                        elif row[0] != "":
                            cooling_flag = False
                            result_row["Cooling Capacity"] = cooling_total_capacity
                            continue
                    if report_flag and heating_flag:
                        if row[0] == "" and row[1] == "None":
                            heating_flag = False
                            report_flag = False
                            result_row["Heating Capacity"] = heating_total_capacity
                        elif row[0] == "" and row[1] != "":
                            # print(row)
                            if not should_ignore(building_type, system_type, row[1]):
                                heating_total_capacity += float(row[4])
                            continue
                        elif row[0] != "":
                            heating_flag = False
                            report_flag = False
                            result_row["Heating Capacity"] = heating_total_capacity
                            continue
                    if building_area_flag:
                        if row[1] == "Net Conditioned Building Area":
                            result_row["Conditioned Area"] = float(row[2])
                            building_area_flag = False
                            continue
                        else:
                            continue
                    if end_use_flag:
                        if row[1] == "Heating":
                            result_row["Electricity Heating"] = float(row[2])
                            result_row["Natural Gas Heating"] = float(row[3])
                            continue
                        elif row[1] == "Cooling":
                            result_row["Electricity Cooling"] = float(row[2])
                            continue
                        elif row[1] == "Fans":
                            result_row["Electricity Fans"] = float(row[2])
                            continue
                        elif row[1] == "Total End Uses":
                            end_use_flag = False
                            continue
                        else:
                            continue
                    if unmet_hours_flag:
                        if row[1] == "Facility":
                            result_row["Unmet Hours Heating"] = float(row[2])
                            result_row["Unmet Hours Cooling"] = float(row[3])
                            unmet_hours_flag = False
                            continue
                        else:
                            continue
            if end_use_flag or unmet_hours_flag or building_area_flag or report_flag:
                print("That's not Good")
            csvfile.close()
            result_rows.append(result_row)
    return result_rows


def write_results(results_rows, output_file):

    with open(output_file, "a", newline="") as csvfile:
        fieldnames = [
            "Filename",
            "Measure",
            "BldgType",
            "BldgLoc",
            "BldgHVAC",
            "Run Type",
            "Cooling Capacity",
            "Heating Capacity",
            "Conditioned Area",
            "Electricity Heating",
            "Natural Gas Heating",
            "Electricity Cooling",
            "Electricity Fans",
            "Unmet Hours Heating",
            "Unmet Hours Cooling",
        ]
        writer = csv.DictWriter(csvfile, fieldnames)
        # writer.writeheader()
        writer.writerows(results_rows)


def write_header(output_file):

    with open(output_file, "w", newline="") as csvfile:
        fieldnames = [
            "Filename",
            "Measure",
            "BldgType",
            "BldgLoc",
            "BldgHVAC",
            "Run Type",
            "Cooling Capacity",
            "Heating Capacity",
            "Conditioned Area",
            "Electricity Heating",
            "Natural Gas Heating",
            "Electricity Cooling",
            "Electricity Fans",
            "Unmet Hours Heating",
            "Unmet Hours Cooling",
        ]
        writer = csv.DictWriter(csvfile, fieldnames)
        writer.writeheader()


def main():

    # root of the DEER package install
    if platform.system() in ["Windows"]:
        root = "C:\\DEER-Prototypes-EnergyPlus-SWHC009\\commercial measures\\SWHC062-05 Supply Fan Controls\\"
        search_folder = "SWHC062-05 Supply Fan Controls_Htl_Ex\\"
        results_folder = PurePath("C:\\test\\")
    elif platform.system() in ["Linux", "Darwin"]:
        root = "/Users/jwj/"
        search_folder = "e_plus_runs/"
        results_folder = PurePath("/Users/jwj/e_plus_results/")
    else:
        print("What, exactly, are you running this on!")
        exit()

    search_path = make_search_paths(root, search_folder)
    offset = len(PurePath(root).parts) + len(PurePath(search_folder).parts)

    # Results file_name
    results_file_name = "eplustbl.csv"

    # Get all the results files
    all_files = search_directories(search_path, results_file_name)

    # Create batches
    batches = by_batch(offset, all_files)

    results_output_file = PurePath.joinpath(
        results_folder,
        PurePath("Summary-Report.csv"),
    )
    write_header(results_output_file)

    # Do each batch
    for building_type in batches.keys():
        for measure in batches[building_type].keys():
            for system_type in batches[building_type][measure].keys():
                for type in batches[building_type][measure][system_type].keys():
                    print(
                        "Processing {} {} {} {}".format(
                            building_type, measure, system_type, type
                        )
                    )
                    rows = process(
                        batches[building_type][measure][system_type][type], offset
                    )
                    write_results(rows, results_output_file)


if __name__ == "__main__":
    main()
