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
        cz = parts[offset + 1]
        run = parts[offset + 3].split("-")
        measure = run[0]
        system_type = run[1]
        type = run[2]
        if type not in ["Measure"]:
            continue
        if building_type not in batches.keys():
            batches[building_type] = {}
        if measure not in batches[building_type].keys():
            batches[building_type][measure] = []
        batches[building_type][measure].append(file)

    return batches


def should_ignore(building_type, system_type, column):

    # if "DORM" in column:
    #     print(column)
    # if "KITCHEN" in column:
    #     print(column)
    if system_type in ["cDXGF", "cDXHP", "cPTAC"]:
        if not re.search("SZ-CAV", column, flags=re.IGNORECASE):
            return True
        if building_type in ["Epr", "Ese", "Eun", "MBT", "RFF", "RSD", "RtL", "Htl"]:
            if "KITCHEN" in column:
                # if re.search("KITCHEN", column, flags=re.IGNORECASE):
                # print(f"Ignoring: {column}")
                return True
        if building_type in ["Eun"]:
            if "DORM" in column:
                # if re.search("DORM", column, flags=re.IGNORECASE):
                print(f"Ignoring: {column}")
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


def set_up(offset, batch):

    results = {}

    for file in batch:
        parts = PurePath(file).parts
        building_type = parts[offset + 2]
        cz = parts[offset + 1]
        run = parts[offset + 3].split("-")
        measure = run[0]
        system_type = run[1]
        type = run[2]

        # print("File: {}".format(file))
        # print("Building Type: {}".format(building_type))
        # print("Measure: {}".format(measure))
        # print("System Type: {}".format(system_type))
        # print("Climate Zone: {}".format(cz))
        # print("Run Type: {}".format(type))

        # Setup the data structure skeleton
        if building_type not in results.keys():
            results[building_type] = {}
        if cz not in results[building_type].keys():
            results[building_type][cz] = {}
        if system_type not in results[building_type][cz].keys():
            results[building_type][cz][system_type] = {}
        if type not in results[building_type][cz][system_type].keys():
            results[building_type][cz][system_type][type] = {}
        results[building_type][cz][system_type][type]["file"] = file
        results[building_type][cz][system_type][type]["columns"] = {}

        # Get relevant column headings
        heating_gas = find_column_headings(file, "Heating Coil NaturalGas Energy")
        heating_electricity = find_column_headings(
            file, "Heating Coil Electricity Energy"
        )
        cooling = find_column_headings(file, "Cooling Coil .* Energy")
        schedules = find_column_headings(file, "SCHEDULE")
        fan_part_load_ratios = find_column_headings(file, "Fan Part Load Ratio")

        # print("Gas Heating Energy Columns: {}".format(heating_gas))
        # print("Electricity Heating Energy Columns: {}".format(heating_electricity))
        # print("Cooling Energy Columns: {}".format(cooling))
        # print("Operation Schedules: {}".format(schedules))
        # print("Fan Part Load Ratio Columns: {}".format(fan_part_load_ratios))

        # There are two sets of calculation stratagies depending on Measure (M1, M2, etc) and System type
        # If the system type is "cPVVG" we are going to sum when Fan Operation Schedules are 0 for all measures
        # If the system type is "cDXGF, cDXHP, cPTAC" we will sum when Fan Operation Schedule is 0 for measures M1, M2, M4
        # and sum when Fan PLR is less than 1 for measures M3, M5

        if system_type in ["cPVVG"] or (
            system_type in ["cDXGF", "cDXHP", "cPTAC"] and measure in ["M1", "M2", "M4"]
        ):
            results[building_type][cz][system_type][type]["columns"]["heating_gas"] = {}
            for heating_col in heating_gas:
                if should_ignore(building_type, system_type, heating_col):
                    results[building_type][cz][system_type][type]["columns"][
                        "heating_gas"
                    ][heating_col] = "Ignore"
                    continue
                for schedule_col in schedules:
                    if heating_col.split(":")[0].removesuffix(
                        "HEATING COIL"
                    ) == schedule_col.split(":")[0].removesuffix("OPERATION SCHEDULE"):
                        results[building_type][cz][system_type][type]["columns"][
                            "heating_gas"
                        ][heating_col] = schedule_col

            results[building_type][cz][system_type][type]["columns"][
                "heating_electricity"
            ] = {}
            for heating_col in heating_electricity:
                if should_ignore(building_type, system_type, heating_col):
                    results[building_type][cz][system_type][type]["columns"][
                        "heating_electricity"
                    ][heating_col] = "Ignore"
                    continue
                for schedule_col in schedules:
                    if heating_col.split(":")[0].removesuffix(
                        "HEATING COIL"
                    ) == schedule_col.split(":")[0].removesuffix("OPERATION SCHEDULE"):
                        results[building_type][cz][system_type][type]["columns"][
                            "heating_electricity"
                        ][heating_col] = schedule_col

            results[building_type][cz][system_type][type]["columns"]["cooling"] = {}
            for cooling_col in cooling:
                if should_ignore(building_type, system_type, cooling_col):
                    results[building_type][cz][system_type][type]["columns"]["cooling"][
                        cooling_col
                    ] = "Ignore"
                    continue
                for schedule_col in schedules:
                    if cooling_col.split(":")[0].removesuffix(
                        "COOLING COIL"
                    ) == schedule_col.split(":")[0].removesuffix("OPERATION SCHEDULE"):
                        results[building_type][cz][system_type][type]["columns"][
                            "cooling"
                        ][cooling_col] = schedule_col

        elif system_type in ["cDXGF", "cDXHP", "cPTAC"] and measure in ["M3", "M5"]:
            results[building_type][cz][system_type][type]["columns"]["heating_gas"] = {}
            for heating_col in heating_gas:
                if should_ignore(building_type, system_type, heating_col):
                    results[building_type][cz][system_type][type]["columns"][
                        "heating_gas"
                    ][heating_col] = "Ignore"
                    continue
                for fan_col in fan_part_load_ratios:
                    if heating_col.split(":")[0].removesuffix(
                        "HEATING COIL"
                    ) == fan_col.split(":")[0].removesuffix("SUPPLY FAN"):
                        results[building_type][cz][system_type][type]["columns"][
                            "heating_gas"
                        ][heating_col] = fan_col
                        break
                    if heating_col.split(":")[0].removesuffix(
                        "HEATING COIL"
                    ) == fan_col.split(":")[0].removesuffix("UNITARY"):
                        results[building_type][cz][system_type][type]["columns"][
                            "heating_gas"
                        ][heating_col] = fan_col

            results[building_type][cz][system_type][type]["columns"][
                "heating_electricity"
            ] = {}
            for heating_col in heating_electricity:
                if should_ignore(building_type, system_type, heating_col):
                    results[building_type][cz][system_type][type]["columns"][
                        "heating_electricity"
                    ][heating_col] = "Ignore"
                    continue
                for fan_col in fan_part_load_ratios:
                    if heating_col.split(":")[0].removesuffix(
                        "HEATING COIL"
                    ) == fan_col.split(":")[0].removesuffix("SUPPLY FAN"):
                        results[building_type][cz][system_type][type]["columns"][
                            "heating_electricity"
                        ][heating_col] = fan_col
                        break
                    if heating_col.split(":")[0].removesuffix(
                        "HEATING COIL"
                    ) == fan_col.split(":")[0].removesuffix("UNITARY"):
                        results[building_type][cz][system_type][type]["columns"][
                            "heating_electricity"
                        ][heating_col] = fan_col

            results[building_type][cz][system_type][type]["columns"]["cooling"] = {}
            for cooling_col in cooling:
                if should_ignore(building_type, system_type, cooling_col):
                    results[building_type][cz][system_type][type]["columns"]["cooling"][
                        cooling_col
                    ] = "Ignore"
                    continue
                for fan_col in fan_part_load_ratios:
                    if cooling_col.split(":")[0].removesuffix(
                        "COOLING COIL"
                    ) == fan_col.split(":")[0].removesuffix("SUPPLY FAN"):
                        results[building_type][cz][system_type][type]["columns"][
                            "cooling"
                        ][cooling_col] = fan_col
                        break
                    if cooling_col.split(":")[0].removesuffix(
                        "COOLING COIL"
                    ) == fan_col.split(":")[0].removesuffix("UNITARY"):
                        results[building_type][cz][system_type][type]["columns"][
                            "cooling"
                        ][cooling_col] = fan_col
        else:
            print(
                "Building Type: {}, Measure: {}, System Type: {}".format(
                    building_type, measure, system_type
                )
            )

        results[building_type][cz][system_type][type]["heating_gas_accumulator"] = 0.0
        results[building_type][cz][system_type][type][
            "heating_electricity_accumulator"
        ] = 0.0
        results[building_type][cz][system_type][type]["cooling_accumulator"] = 0.0

        results[building_type][cz][system_type][type][
            "heating_gas_total_accumulator"
        ] = 0.0
        results[building_type][cz][system_type][type][
            "heating_electricity_total_accumulator"
        ] = 0.0
        results[building_type][cz][system_type][type]["cooling_total_accumulator"] = 0.0

    return results


# There are two stratagies for calculating off hours. Fan PLR < 1 and Operation Schedule == 0
# The setup function assigned the "matching" column as needed. As 0 IS less than one a single
# test is all that is needed here


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
                                    < 1
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
                                    < 1
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
                                    < 1
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
                    type_list = list(results[building_type][cz][system_type].keys())
                    type_list.sort()
                    for type in type_list:

                        columns.write("\t\t\tHeating Natural Gas\n")
                        heating_gas = list(
                            results[building_type][cz][system_type][type]["columns"][
                                "heating_gas"
                            ].keys()
                        )
                        for heating_gas_col in heating_gas:
                            columns.write("\t\t\t\tCoil: {}\n".format(heating_gas_col))
                            columns.write(
                                "\t\t\t\tSchedule Value: {}\n".format(
                                    results[building_type][cz][system_type][type][
                                        "columns"
                                    ]["heating_gas"][heating_gas_col]
                                )
                            )

                        columns.write("\t\t\tHeating Electricity\n")
                        heating_electricity = list(
                            results[building_type][cz][system_type][type]["columns"][
                                "heating_electricity"
                            ].keys()
                        )
                        for heating_electricity_col in heating_electricity:
                            columns.write(
                                "\t\t\t\tCoil: {}\n".format(heating_electricity_col)
                            )
                            columns.write(
                                "\t\t\t\tSchedule Value: {}\n".format(
                                    results[building_type][cz][system_type][type][
                                        "columns"
                                    ]["heating_electricity"][heating_electricity_col]
                                )
                            )

                        columns.write("\t\t\tCooling\n")
                        cooling = list(
                            results[building_type][cz][system_type][type]["columns"][
                                "cooling"
                            ].keys()
                        )
                        for cooling_col in cooling:
                            columns.write("\t\t\t\tCoil: {}\n".format(cooling_col))
                            columns.write(
                                "\t\t\t\tSchedule Value: {}\n".format(
                                    results[building_type][cz][system_type][type][
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
        root = "D:\\"
        search_folder = "Simulations Test\\"
        results_folder = PurePath("D:\\Hourly Results Test\\")
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
    results_file_name = "instance-var.csv"

    # Get all the results files
    all_files = search_directories(search_path, results_file_name)

    # Create batches by building type and measure, only for the measure type not the baseline type
    batches = by_batch(offset, all_files)

    # Do each batch
    for building_type in batches.keys():
        for measure in batches[building_type].keys():
            print(
                "Processing Building Type: {}, Measure: {}".format(
                    building_type, measure
                )
            )
            results_output_file = PurePath.joinpath(
                results_folder, PurePath("{}-{}.csv".format(building_type, measure))
            )
            column_match_output_file = PurePath.joinpath(
                results_folder,
                PurePath("{}-{}-columns.txt".format(building_type, measure)),
            )
            print("Into Results File {}".format(str(results_output_file)))
            batch = batches[building_type][measure]
            results = set_up(offset, batch)
            print_column_matchings(results, column_match_output_file)
            calculate_sums(results)
            write_results(results, results_output_file)


if __name__ == "__main__":
    main()
