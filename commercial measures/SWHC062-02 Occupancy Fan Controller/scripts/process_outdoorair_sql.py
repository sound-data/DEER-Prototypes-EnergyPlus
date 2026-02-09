import platform
import csv
import sqlite3
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


def should_ignore(building_type, system_type, column):

    if system_type in ["cDXGF", "cDXHP", "cPTAC"]:
        if "SZ-CAV" not in column:
            return True
        if building_type.lower() in [
            "epr",
            "ese",
            "eun",
            "mbt",
            "rff",
            "rsd",
            "rtl",
            "htl",
        ]:
            if "KITCHEN" in column:
                return True
        if building_type.lower() in ["eun"]:
            if "DORM" in column:
                return True
        if building_type.lower() in ["htl"]:
            if "GUESTRM" in column:
                return True
    if system_type in ["cPVVG"]:
        if "SZ-VAV" not in column:
            return True
        if building_type.lower() in ["ecc", "htl"]:
            if "KITCHEN" in column:
                return True
        if building_type.lower() in ["mbt"]:
            if "LAB" in column:
                return True
        if " ATU" in column:
            return True
    return False


def process(offset, all_files, output_file):

    for file in all_files:
        with open(output_file, "a", newline="") as csvfile:
            fieldnames = [
                "Building Type",
                "Measure",
                "System Type",
                "Run Type",
                "Climate Zone",
            ]
            writer = csv.DictWriter(csvfile, fieldnames)
            writer.writeheader()
        parts = PurePath(file).parts
        building_type = parts[offset + 2]
        cz = parts[offset + 1]
        run = parts[offset + 3].split("-")
        measure = run[0]
        system_type = run[1]
        run_type = run[2]

        print(building_type, cz, measure, system_type, run_type)

        query_filter = "SELECT RowName \
                            FROM TabularDataWithStrings \
                            WHERE TableName = {}".format(
            '"Controller:OutdoorAir"'
        )

        with sqlite3.connect(file) as conn:
            cur = conn.cursor()
            cur.execute(query_filter)
            system_rows = cur.fetchall()
            systems = [x[0] for x in system_rows]

        ignore_list = []
        keep_list = []

        for system in systems:
            if should_ignore(building_type, system_type, system):
                ignore_list.append(system)
            else:
                keep_list.append(system)

        sql = "SELECT RowName, ColumnName, Value \
                    FROM TabularDataWithStrings \
                    WHERE TableName = {} \
                        and RowName IN ({seq})".format(
            '"Controller:OutdoorAir"',
            seq=",".join(["?"] * len(keep_list)),
        )

        with sqlite3.connect(file) as conn:
            cur = conn.cursor()
            cur.execute(sql, keep_list)
            outdoorairrows = cur.fetchall()

            outdoorair = [x for x in outdoorairrows]

        output_row = {
            "Building Type": building_type,
            "Measure": measure,
            "System Type": system_type,
            "Run Type": run_type,
            "Climate Zone": cz,
        }

        with open(output_file, "a", newline="") as csvfile:
            fieldnames = [
                "Building Type",
                "Measure",
                "System Type",
                "Run Type",
                "Climate Zone",
            ]
            writer = csv.DictWriter(csvfile, fieldnames)
            writer.writerow(output_row)

        with open(output_file, "a", newline="") as csvfile:
            fieldnames = [
                "System",
                "Maximum Outdoor Air Flow Rate",
                "Minimum Outdoor Air Flow Rate",
            ]
            writer = csv.DictWriter(csvfile, fieldnames)
            writer.writeheader()
            sys_dict = {}
            for row in outdoorair:
                if row[0] not in sys_dict:
                    sys_dict[row[0]] = {
                        "Maximum Outdoor Air Flow Rate": 0,
                        "Minimum Outdoor Air Flow Rate": 0,
                    }
                if row[1] == "Maximum Outdoor Air Flow Rate":
                    sys_dict[row[0]]["Maximum Outdoor Air Flow Rate"] = row[2]
                if row[1] == "Minimum Outdoor Air Flow Rate":
                    sys_dict[row[0]]["Minimum Outdoor Air Flow Rate"] = row[2]

            for system in sys_dict.keys():
                output_row = {
                    "System": system,
                    "Maximum Outdoor Air Flow Rate": sys_dict[system][
                        "Maximum Outdoor Air Flow Rate"
                    ],
                    "Minimum Outdoor Air Flow Rate": sys_dict[system][
                        "Minimum Outdoor Air Flow Rate"
                    ],
                }
                writer.writerow(output_row)


def main():

    # root of the DEER package install
    if platform.system() in ["Windows"]:
        root = "D:\\"
        search_folder = "Simulations\\"
        results_folder = PurePath("D:\\Peak Results\\")
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
    results_file_name = "instance-out.sql"

    # Output file_name

    output_file = PurePath.joinpath(
        results_folder,
        PurePath("Outdoor Air.csv"),
    )

    # Get all the results files
    all_files = search_directories(search_path, results_file_name)

    process(offset, all_files, output_file)


if __name__ == "__main__":
    main()
