import platform
import csv
import re
from pathlib import Path, PurePath


def get_all_column_headings(file):
    col_list = []
    with open(file, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            all_col_list = list(row.keys())
            break

    return all_col_list


def find_column_headings(file, filter_expression):
    col_list = []
    all_col_list = get_all_column_headings(file)

    for col in all_col_list:
        if re.search(filter_expression, col):
            col_list.append(col)

    return col_list


def make_search_paths(root, search_folders):
    search_paths = []
    for folder in search_folders:
        search_paths.append(PurePath.joinpath(PurePath(root), PurePath(folder)))

    return search_paths


def search_directories(root_paths, file_name):
    paths = []
    for path in root_paths:
        for dir_name, sub_dirs, files in Path.walk(path):
            for file in files:
                if file.lower() == file_name:
                    paths.append(PurePath.joinpath(dir_name, file))

    return paths


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
    if system_type in ["cPVVG"]:
        if not re.search("SZ-VAV", column, flags=re.IGNORECASE):
            return True
        if building_type in ["ECC", "Htl"]:
            if re.search("KITCHEN", column, flags=re.IGNORECASE):
                return True
        if building_type in ["MBT"]:
            if re.search("LAB", column, flags=re.IGNORECASE):
                return True
        if re.search("ATU", column, flags=re.IGNORECASE):
            return True
    return False


def set_up(offset, all_files):

    results = {}

    for file in all_files:
        parts = PurePath(file).parts
        building_type = parts[6 + offset].split("&")[0]
        measure = parts[7 + offset].split("-")[4]
        system_type = parts[7 + offset].split("-")[3]
        cz = parts[5 + offset]

        if system_type in ["cPVVG"]:
            continue
        if measure not in ["Unocc"]:
            continue

        if building_type not in results.keys():
            results[building_type] = {}
        if cz not in results[building_type].keys():
            results[building_type][cz] = {}
        if system_type not in results[building_type][cz].keys():
            results[building_type][cz][system_type] = {}
        if measure not in results[building_type][cz][system_type].keys():
            results[building_type][cz][system_type][measure] = {}
        results[building_type][cz][system_type][measure]["file"] = file
        results[building_type][cz][system_type][measure]["columns"] = {}

        heating_gas = find_column_headings(file, "Heating Coil NaturalGas Energy")
        heating_electricity = find_column_headings(
            file, "Heating Coil Electricity Energy"
        )
        cooling = find_column_headings(file, "Cooling Coil .* Energy")
        fans = find_column_headings(file, "Fan Part Load Ratio")

        results[building_type][cz][system_type][measure]["columns"]["heating_gas"] = {}
        for heating_col in heating_gas:
            if should_ignore(building_type, system_type, heating_col):
                results[building_type][cz][system_type][measure]["columns"][
                    "heating_gas"
                ][heating_col] = "Ignore"
                continue
            for fan_col in fans:
                # if heating_col.split(":")[0].removesuffix(
                #     "HEATING COIL"
                # ) == fan_col.split(":")[0].removesuffix("SUPPLY FAN"):
                #     results[building_type][cz][system_type][measure]["columns"][
                #         "heating_gas"
                #     ][heating_col] = fan_col
                #     break
                if heating_col.split(":")[0].removesuffix(
                    "HEATING COIL"
                ) == fan_col.split(":")[0].removesuffix("UNITARY"):
                    results[building_type][cz][system_type][measure]["columns"][
                        "heating_gas"
                    ][heating_col] = fan_col

        results[building_type][cz][system_type][measure]["columns"][
            "heating_electricity"
        ] = {}
        for heating_col in heating_electricity:
            if should_ignore(building_type, system_type, heating_col):
                results[building_type][cz][system_type][measure]["columns"][
                    "heating_electricity"
                ][heating_col] = "Ignore"
                continue
            for fan_col in fans:
                # if heating_col.split(":")[0].removesuffix(
                #     "HEATING COIL"
                # ) == fan_col.split(":")[0].removesuffix("SUPPLY FAN"):
                #     results[building_type][cz][system_type][measure]["columns"][
                #         "heating_electricity"
                #     ][heating_col] = fan_col
                #     break
                if heating_col.split(":")[0].removesuffix(
                    "HEATING COIL"
                ) == fan_col.split(":")[0].removesuffix("UNITARY"):
                    results[building_type][cz][system_type][measure]["columns"][
                        "heating_electricity"
                    ][heating_col] = fan_col

        results[building_type][cz][system_type][measure]["columns"]["cooling"] = {}
        for cooling_col in cooling:
            if should_ignore(building_type, system_type, cooling_col):
                results[building_type][cz][system_type][measure]["columns"]["cooling"][
                    cooling_col
                ] = "Ignore"
                continue
            for fan_col in fans:
                # if cooling_col.split(":")[0].removesuffix(
                #     "COOLING COIL"
                # ) == fan_col.split(":")[0].removesuffix("SUPPLY FAN"):
                #     results[building_type][cz][system_type][measure]["columns"][
                #         "cooling"
                #     ][cooling_col] = fan_col
                #     break
                if cooling_col.split(":")[0].removesuffix(
                    "COOLING COIL"
                ) == fan_col.split(":")[0].removesuffix("UNITARY"):
                    results[building_type][cz][system_type][measure]["columns"][
                        "cooling"
                    ][cooling_col] = fan_col

        results[building_type][cz][system_type][measure][
            "heating_gas_accumulator"
        ] = 0.0
        results[building_type][cz][system_type][measure][
            "heating_electricity_accumulator"
        ] = 0.0
        results[building_type][cz][system_type][measure]["cooling_accumulator"] = 0.0

        results[building_type][cz][system_type][measure][
            "heating_gas_total_accumulator"
        ] = 0.0
        results[building_type][cz][system_type][measure][
            "heating_electricity_total_accumulator"
        ] = 0.0
        results[building_type][cz][system_type][measure][
            "cooling_total_accumulator"
        ] = 0.0

    return results


def calculate_sums(results):

    building_type_list = list(results.keys())
    building_type_list.sort()
    for building_type in building_type_list:
        cz_list = list(results[building_type].keys())
        cz_list.sort()
        for cz in cz_list:
            system_type_list = list(results[building_type][cz].keys())
            system_type_list.sort()
            for system_type in system_type_list:
                measure_list = list(results[building_type][cz][system_type].keys())
                measure_list.sort()
                for measure in measure_list:
                    file = results[building_type][cz][system_type][measure]["file"]
                    with open(file, newline="") as csvfile:
                        reader = csv.DictReader(csvfile)
                        for row in reader:
                            for heating_gas_col in results[building_type][cz][
                                system_type
                            ][measure]["columns"]["heating_gas"].keys():
                                if (
                                    results[building_type][cz][system_type][measure][
                                        "columns"
                                    ]["heating_gas"][heating_gas_col]
                                    == "Ignore"
                                ):
                                    continue
                                if (
                                    float(
                                        row[
                                            results[building_type][cz][system_type][
                                                measure
                                            ]["columns"]["heating_gas"][heating_gas_col]
                                        ]
                                    )
                                    < 1.0
                                ):
                                    results[building_type][cz][system_type][measure][
                                        "heating_gas_accumulator"
                                    ] += float(row[heating_gas_col])
                                results[building_type][cz][system_type][measure][
                                    "heating_gas_total_accumulator"
                                ] += float(row[heating_gas_col])

                            for heating_electricity_col in results[building_type][cz][
                                system_type
                            ][measure]["columns"]["heating_electricity"].keys():
                                if (
                                    results[building_type][cz][system_type][measure][
                                        "columns"
                                    ]["heating_electricity"][heating_electricity_col]
                                    == "Ignore"
                                ):
                                    continue
                                if (
                                    float(
                                        row[
                                            results[building_type][cz][system_type][
                                                measure
                                            ]["columns"]["heating_electricity"][
                                                heating_electricity_col
                                            ]
                                        ]
                                    )
                                    < 1.0
                                ):
                                    results[building_type][cz][system_type][measure][
                                        "heating_electricity_accumulator"
                                    ] += float(row[heating_electricity_col])
                                results[building_type][cz][system_type][measure][
                                    "heating_electricity_total_accumulator"
                                ] += float(row[heating_electricity_col])

                            for cooling_col in results[building_type][cz][system_type][
                                measure
                            ]["columns"]["cooling"].keys():
                                if (
                                    results[building_type][cz][system_type][measure][
                                        "columns"
                                    ]["cooling"][cooling_col]
                                    == "Ignore"
                                ):
                                    continue
                                if (
                                    float(
                                        row[
                                            results[building_type][cz][system_type][
                                                measure
                                            ]["columns"]["cooling"][cooling_col]
                                        ]
                                    )
                                    < 1.0
                                ):
                                    results[building_type][cz][system_type][measure][
                                        "cooling_accumulator"
                                    ] += float(row[cooling_col])
                                results[building_type][cz][system_type][measure][
                                    "cooling_total_accumulator"
                                ] += float(row[cooling_col])


def print_column_matchings(results, output_file):

    with open(output_file, "w") as columns:
        building_type_list = list(results.keys())
        building_type_list.sort()
        for building_type in building_type_list:
            columns.write("{}\n".format(building_type))
            cz_list = list(results[building_type].keys())
            cz_list.sort()
            for cz in cz_list:
                columns.write("\t{}\n".format(cz))
                system_type_list = list(results[building_type][cz].keys())
                system_type_list.sort()
                for system_type in system_type_list:
                    columns.write("\t\t{}\n".format(system_type))
                    measure_list = list(results[building_type][cz][system_type].keys())
                    measure_list.sort()
                    for measure in measure_list:

                        columns.write("\t\t\tHeating Natural Gas\n")
                        heating_gas = list(
                            results[building_type][cz][system_type][measure]["columns"][
                                "heating_gas"
                            ].keys()
                        )
                        for heating_gas_col in heating_gas:
                            columns.write("\t\t\t\tCoil: {}\n".format(heating_gas_col))
                            columns.write(
                                "\t\t\t\tFan: {}\n".format(
                                    results[building_type][cz][system_type][measure][
                                        "columns"
                                    ]["heating_gas"][heating_gas_col]
                                )
                            )

                        columns.write("\t\t\tHeating Electricity\n")
                        heating_electricity = list(
                            results[building_type][cz][system_type][measure]["columns"][
                                "heating_electricity"
                            ].keys()
                        )
                        for heating_electricity_col in heating_electricity:
                            columns.write(
                                "\t\t\t\tCoil: {}\n".format(heating_electricity_col)
                            )
                            columns.write(
                                "\t\t\t\tFan: {}\n".format(
                                    results[building_type][cz][system_type][measure][
                                        "columns"
                                    ]["heating_electricity"][heating_electricity_col]
                                )
                            )

                        columns.write("\t\t\tCooling\n")
                        cooling = list(
                            results[building_type][cz][system_type][measure]["columns"][
                                "cooling"
                            ].keys()
                        )
                        for cooling_col in cooling:
                            columns.write("\t\t\t\tCoil: {}\n".format(cooling_col))
                            columns.write(
                                "\t\t\t\tFan: {}\n".format(
                                    results[building_type][cz][system_type][measure][
                                        "columns"
                                    ]["cooling"][cooling_col]
                                )
                            )
        columns.close()


def write_results(results, output_file):
    energy_results = []
    building_type_list = list(results.keys())
    building_type_list.sort()
    for building_type in building_type_list:
        cz_list = list(results[building_type].keys())
        cz_list.sort()
        for cz in cz_list:
            system_type_list = list(results[building_type][cz].keys())
            system_type_list.sort()
            for system_type in system_type_list:
                measure_list = list(results[building_type][cz][system_type].keys())
                measure_list.sort()
                for measure in measure_list:
                    row = {
                        "Building Type": building_type,
                        "Climate Zone": cz,
                        "System Type": system_type,
                        "Heating Gas Energy": round(
                            results[building_type][cz][system_type][measure][
                                "heating_gas_accumulator"
                            ],
                            2,
                        ),
                        "Heating Electricity Energy": round(
                            results[building_type][cz][system_type][measure][
                                "heating_electricity_accumulator"
                            ],
                            2,
                        ),
                        "Cooling Energy": round(
                            results[building_type][cz][system_type][measure][
                                "cooling_accumulator"
                            ],
                            2,
                        ),
                        "Heating Gas Total Energy": round(
                            results[building_type][cz][system_type][measure][
                                "heating_gas_total_accumulator"
                            ],
                            2,
                        ),
                        "Heating Electricity Total Energy": round(
                            results[building_type][cz][system_type][measure][
                                "heating_electricity_total_accumulator"
                            ],
                            2,
                        ),
                        "Cooling Total Energy": round(
                            results[building_type][cz][system_type][measure][
                                "cooling_total_accumulator"
                            ],
                            2,
                        ),
                    }

                    energy_results.append(row)

    with open(output_file, "a", newline="") as csvfile:
        fieldnames = [
            "Building Type",
            "Climate Zone",
            "System Type",
            "Heating Gas Energy",
            "Heating Electricity Energy",
            "Cooling Energy",
            "Heating Gas Total Energy",
            "Heating Electricity Total Energy",
            "Cooling Total Energy",
        ]
        writer = csv.DictWriter(csvfile, fieldnames)
        writer.writeheader()
        writer.writerows(energy_results)


def main():

    # root of the DEER package install
    if platform.system() in ["Windows"]:
        root = "C:\\"
    elif platform.system() in ["Linux", "Darwin"]:
        root = "/Users/jwj/Work/"
    else:
        print("What, exactly, are you running this on!")
        exit()

    search_folders = ["DEER-Prototypes-EnergyPlus-SWHC009/commercial measures/"]
    search_paths = make_search_paths(root, search_folders)
    offset = len(PurePath(root).parts)

    # Results file_name
    results_file_name = "instance-var.csv"

    # Get all the results files
    all_files = search_directories(search_paths, results_file_name)

    results = set_up(offset, all_files)

    output_file = "columns.txt"
    results_folder = root + "results"
    print_column_matchings(
        results, PurePath.joinpath(PurePath(results_folder), PurePath(output_file))
    )

    calculate_sums(results)

    output_file = "results.csv"
    results_folder = root + "Results"
    write_results(
        results, PurePath.joinpath(PurePath(results_folder), PurePath(output_file))
    )


if __name__ == "__main__":
    main()
