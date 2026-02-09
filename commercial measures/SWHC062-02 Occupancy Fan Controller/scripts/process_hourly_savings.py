import platform
import csv
import shutil
import sqlite3
from pathlib import Path, PurePath
import math


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
        if building_type not in batches.keys():
            batches[building_type] = {}
        if measure not in batches[building_type].keys():
            batches[building_type][measure] = {}
        if system_type not in batches[building_type][measure].keys():
            batches[building_type][measure][system_type] = {}
        if type not in batches[building_type][measure][system_type].keys():
            batches[building_type][measure][system_type][type] = {}
        if cz not in batches[building_type][measure][system_type][type].keys():
            batches[building_type][measure][system_type][type][cz] = []
        batches[building_type][measure][system_type][type][cz].append(file)

    return batches


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


def file_copy(building_type, measure, system_type, type, batch, results_folder):

    for cz in batch.keys():
        dest_name = building_type + measure + system_type + cz
        shutil.copy(
            batch[cz][0],
            PurePath.joinpath(results_folder, PurePath(dest_name + ".csv")),
        )


def process(building_type, measure, system_type, type, batch, output_file):

    def dict_of_lists_to_list_of_dicts(d):
        # All lists must be the same length or zip will truncate
        keys = d.keys()
        values = zip(*d.values())
        return [dict(zip(keys, vals)) for vals in values]

    needed_data = [
        "Cooling Coil Total Cooling Rate",
        "Cooling Coil Electricity Energy",
        "Heating Coil Heating Rate",
        "Heating Coil NaturalGas Energy",
        "Heating Coil Electricity Energy",
        "Fan Electricity Rate",
        "Fan Runtime Fraction",
        "Unitary System Fan Part Load Ratio",
        "Unitary System Compressor Part Load Ratio",
    ]

    for cz in batch.keys():
        print(cz)
        file = batch[cz][0]
        print(file)

        with open(output_file, "a", newline="") as csvfile:
            fieldnames = [
                "Building Type",
                "Measure",
                "System Type",
                "Climate Zone",
            ]
            writer = csv.DictWriter(csvfile, fieldnames)
            writer.writeheader()

            output_row = {
                "Building Type": building_type,
                "Measure": measure,
                "System Type": system_type,
                "Climate Zone": cz,
            }
            writer.writerow(output_row)

        query_zones = "SELECT DISTINCT SUBSTR(KeyValue, 1, INSTR(KeyValue,{}) - 2)\
                            FROM ReportVariableDataDictionary \
                            WHERE  IndexGroup = {} AND TimestepType = {}".format(
            '"SZ"', '"System"', '"HVAC System"'
        )

        with sqlite3.connect(file) as conn:
            cur = conn.cursor()
            cur.execute(query_zones)
            zone_rows = cur.fetchall()

        temp_zones = [x[0] for x in zone_rows]

        work_list = {}
        for temp_zone in temp_zones:
            query_variables = 'Select VariableName, KeyValue \
                                FROM ReportVariableDataDictionary \
                                Where IndexGroup = {} And TimeStepType = {} \
                                    AND INSTR(KeyValue,"{}") > 0'.format(
                '"System"', '"HVAC System"', temp_zone
            )

            with sqlite3.connect(file) as conn:
                cur = conn.cursor()
                cur.execute(query_variables)
                variable_rows = cur.fetchall()

            var_work_list = []
            for vars in variable_rows:
                if (
                    should_ignore(building_type, system_type, vars[1])
                    or vars[0] not in needed_data
                ):
                    continue
                else:
                    work = {vars[1]: vars[0]}
                    var_work_list.append(work)

            if var_work_list:
                work_list[temp_zone] = var_work_list

        # Now I have a list of work to do, lets get some data

        data = {}
        for zone in work_list.keys():
            zone_data = {}
            for var_list in work_list[zone]:
                KeyValueTemp = list(var_list.keys())
                KeyValue = KeyValueTemp[0]
                VariableName = var_list[KeyValue]

                data_query = 'Select VariableValue \
                                FROM ReportVariableDataDictionary, ReportVariableData \
                                WHERE ReportVariableDataDictionary.IndexGroup = {} AND \
                                    ReportVariableDataDictionary.TimestepType = {} AND \
                                    ReportVariableDataDictionary.KeyValue = "{}" AND \
                                    ReportVariableDataDictionary.VariableName = "{}" AND \
                                    ReportVariableDataDictionary.ReportVariableDataDictionaryIndex = \
                                        ReportVariableData.ReportVariableDataDictionaryIndex'.format(
                    '"System"',
                    '"HVAC System"',
                    KeyValue,
                    VariableName,
                )

                with sqlite3.connect(file) as conn:
                    cur = conn.cursor()
                    cur.execute(data_query)
                    data_rows = cur.fetchall()

                data_list = [x[0] for x in data_rows]
                zone_data[VariableName] = data_list

            data[zone] = zone_data

        # Now it needs to be rearranged to be useful. What I need is for each zone a list of dict's
        # using zip to do that

        working_data = {}
        for zone in data.keys():
            working_data[zone] = dict_of_lists_to_list_of_dicts(data[zone])

        # calculations

        # For each zone
        with open(output_file, "a", newline="") as csvfile:
            fieldnames = [
                "Zone",
                "Gas Heat Savings",
                "Electric Heat Savings",
                "Electric Cooling Savings",
                "Fan Interaction Energy",
                "Gas Heat PLR Avg",
                "Electric Heat PLR Avg",
                "Electric Cooling PLR Avg",
            ]
            writer = csv.DictWriter(csvfile, fieldnames)
            writer.writeheader()

        for zone in working_data.keys():
            # Accumulators and counters
            tot_gas_heat_savings = 0
            tot_elec_heat_savings = 0
            tot_elec_cooling_savings = 0
            tot_fan_interactions_energy = 0
            plr_gas_heat_accumulator = 0
            plr_gas_heat_counter = 0
            plr_elec_heat_accumulator = 0
            plr_elec_heat_counter = 0
            plr_elec_cooling_accumulator = 0
            plr_elec_cooling_counter = 0

            for row in working_data[zone]:
                # Gas heat?
                if system_type in ["cDXGF", "cPVVG"]:
                    # Any savings this hour
                    if (
                        float(row["Unitary System Fan Part Load Ratio"]) >= 0.033
                        and float(row["Unitary System Fan Part Load Ratio"]) < 0.999
                        and float(row["Heating Coil NaturalGas Energy"]) > 0
                    ):
                        plr_gas_heat_accumulator += float(
                            row["Unitary System Fan Part Load Ratio"]
                        )
                        plr_gas_heat_counter += 1

                        if measure in ["M1", "M4", "M5"]:
                            gas_heat_percent_savings = (
                                0.0357
                                * float(row["Unitary System Fan Part Load Ratio"])
                                ** -0.523
                            )
                        else:
                            gas_heat_percent_savings = (
                                0.0418
                                * float(row["Unitary System Fan Part Load Ratio"])
                                ** -0.601
                            )
                        # In therms
                        gas_heat_savings = (
                            gas_heat_percent_savings
                            * float(row["Heating Coil NaturalGas Energy"])
                        ) / 105500000
                        # add it to the total
                        tot_gas_heat_savings += gas_heat_savings

                        # Fan interactions energy use
                        if measure in ["M1", "M4", "M5"]:
                            additional_fan_energy = (
                                gas_heat_savings
                                * 1.352
                                * float(row["Unitary System Fan Part Load Ratio"])
                                ** 0.268
                            )
                        else:
                            additional_fan_energy = (
                                gas_heat_savings
                                * 1.0867
                                * float(row["Unitary System Fan Part Load Ratio"])
                                ** 0.165
                            )
                        # add it to the total
                        tot_fan_interactions_energy += additional_fan_energy

                # Electric heat?
                if system_type in ["cDXHP"]:
                    # Any savings this hour
                    if (
                        float(row["Unitary System Compressor Part Load Ratio"]) >= 0.033
                        and float(row["Unitary System Compressor Part Load Ratio"])
                        < 0.999
                        and float(row["Heating Coil Electricity Energy"]) > 0
                    ):

                        plr_elec_heat_accumulator += float(
                            row["Unitary System Compressor Part Load Ratio"]
                        )
                        plr_elec_heat_counter += 1

                        if measure in ["M2", "M3"]:
                            elec_heat_percent_savings = (
                                0.0591
                                * float(
                                    row["Unitary System Compressor Part Load Ratio"]
                                )
                                ** -0.4334
                            )
                            elec_heat_savings = (
                                elec_heat_percent_savings
                                * float(row["Heating Coil Electricity Energy"])
                            ) / 3600000
                            # add to the total
                            tot_elec_heat_savings += elec_heat_savings

                # Cooling
                # Cooling this hour?
                if (
                    float(row["Cooling Coil Electricity Energy"]) > 0.0
                    and float(row["Unitary System Compressor Part Load Ratio"]) >= 0.033
                    and float(row["Unitary System Compressor Part Load Ratio"]) < 0.999
                ):

                    plr_elec_cooling_accumulator += float(
                        row["Unitary System Compressor Part Load Ratio"]
                    )
                    plr_elec_cooling_counter += 1

                    if measure in ["M1", "M4", "M5"]:
                        cooling_percent_savings = (
                            0.0328
                            * float(row["Unitary System Compressor Part Load Ratio"])
                            ** -0.602
                        )
                    else:
                        cooling_percent_savings = (
                            -0.2
                            * math.log(
                                float(row["Unitary System Compressor Part Load Ratio"])
                            )
                            + 0.0006
                        )
                        if cooling_percent_savings > 0.206:
                            cooling_percent_savings = 0.206

                    cooling_elec_savings = (
                        cooling_percent_savings
                        * float(row["Cooling Coil Electricity Energy"])
                        / 3600000
                    )
                    # add to total
                    tot_elec_cooling_savings += cooling_elec_savings

            if plr_gas_heat_counter > 0:
                plr_gas_heat_avg = plr_gas_heat_accumulator / plr_gas_heat_counter
            else:
                plr_gas_heat_avg = 0

            if plr_elec_heat_counter > 0:
                plr_elec_heat_avg = plr_elec_heat_accumulator / plr_elec_heat_counter
            else:
                plr_elec_heat_avg = 0

            if plr_elec_cooling_counter > 0:
                plr_elec_cooling_avg = (
                    plr_elec_cooling_accumulator / plr_elec_cooling_counter
                )
            else:
                plr_elec_cooling_avg = 0

            with open(output_file, "a", newline="") as csvfile:
                fieldnames = [
                    "Zone",
                    "Gas Heat Savings",
                    "Electric Heat Savings",
                    "Electric Cooling Savings",
                    "Fan Interaction Energy",
                    "Gas Heat PLR Avg",
                    "Electric Heat PLR Avg",
                    "Electric Cooling PLR Avg",
                ]
                writer = csv.DictWriter(csvfile, fieldnames)

                output_row = {
                    "Zone": zone,
                    "Gas Heat Savings": tot_gas_heat_savings,
                    "Electric Heat Savings": tot_elec_heat_savings,
                    "Electric Cooling Savings": tot_elec_cooling_savings,
                    "Fan Interaction Energy": tot_fan_interactions_energy,
                    "Gas Heat PLR Avg": plr_gas_heat_avg,
                    "Electric Heat PLR Avg": plr_elec_heat_avg,
                    "Electric Cooling PLR Avg": plr_elec_cooling_avg,
                }
                writer.writerow(output_row)


def main():

    # root of the DEER package install
    if platform.system() in ["Windows"]:
        root = "D:\\"
        search_folder = "Simulations\\"
        results_folder = PurePath("D:\\savings\\")
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
    # results_file_name = "instance-var.csv"

    # # Output file
    # output_file = PurePath.joinpath(
    #     results_folder,
    #     PurePath("hourly_savings.csv"),
    # )

    # Get all the results files
    all_files = search_directories(search_path, results_file_name)

    # Create batches
    batches = by_batch(offset, all_files)

    # Do each batch
    for building_type in batches.keys():
        if building_type.lower() in ["asm", "ecc", "epr"]:
            continue
        print(building_type)

        output_file = PurePath.joinpath(
            results_folder,
            PurePath("hourly_savings_{}.csv".format(building_type.lower())),
        )

        for measure in batches[building_type].keys():
            print(measure)
            for system_type in batches[building_type][measure].keys():
                print(system_type)
                for type in batches[building_type][measure][system_type].keys():
                    if type not in ["Measure"]:
                        continue
                    print(type)
                    process(
                        building_type,
                        measure,
                        system_type,
                        type,
                        batches[building_type][measure][system_type][type],
                        output_file,
                    )
                    # file_copy(
                    #     building_type,
                    #     measure,
                    #     system_type,
                    #     type,
                    #     batches[building_type][measure][system_type][type],
                    #     results_folder,
                    # )


if __name__ == "__main__":
    main()
