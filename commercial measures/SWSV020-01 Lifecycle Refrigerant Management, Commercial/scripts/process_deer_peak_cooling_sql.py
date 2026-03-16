import platform
import csv
import sqlite3
from pathlib import Path, PurePath
import datetime


def make_search_paths(root, folder):
    return PurePath.joinpath(PurePath(root), PurePath(folder))


def search_directories(path, file_name):
    paths = []
    for dir_name, sub_dirs, files in Path.walk(path):
        for file in files:
            if file.lower() == file_name:
                paths.append(PurePath.joinpath(dir_name, file))

    return paths


def get_deer_peak_range(file, cz):
    # This is a little crazy. The data is stamped ending hour. What we want is the
    # hours between 16:00 and 21:00 STANDARD TIME.
    # All of the peak days fall in Day light savings time. So we need to subtract an hour.
    #
    # In the end we get what we want which is the 5 hours starting with the hour ENDING 16:00
    # to the hour ending 20:00 daylight savings time which is the same as the hours BETWEEN 16:00
    # and 21:00 Standard time.
    peakspec = dict(
        [
            ("CZ01", 238),
            ("CZ02", 238),
            ("CZ03", 238),
            ("CZ04", 238),
            ("CZ05", 259),
            ("CZ06", 245),
            ("CZ07", 245),
            ("CZ08", 245),
            ("CZ09", 244),
            ("CZ10", 180),
            ("CZ11", 180),
            ("CZ12", 180),
            ("CZ13", 180),
            ("CZ14", 180),
            ("CZ15", 180),
            ("CZ16", 224),
        ]
    )

    start_datetime = datetime.datetime.strptime(
        "2017" + "-" + str(peakspec[cz]), "%Y-%j"
    )
    start_date = start_datetime.date()
    numdays = 3
    date_range = [start_date + datetime.timedelta(days=x) for x in range(numdays)]
    with sqlite3.connect(file) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT TimeIndex \
                FROM Time \
                WHERE ((Month = ? and Day = ?) and (Hour BETWEEN ? and ?)) or \
                      ((Month = ? and Day = ?) and (Hour BETWEEN ? and ?)) or \
                      ((Month = ? and Day = ?) and (Hour BETWEEN ? and ?))",
            (
                date_range[0].month,
                date_range[0].day,
                15,
                19,
                date_range[1].month,
                date_range[1].day,
                15,
                19,
                date_range[2].month,
                date_range[2].day,
                15,
                19,
            ),
        )
        rows = cur.fetchall()

    return [x[0] for x in rows]


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

    with open(output_file, "w", newline="") as csvfile:
        fieldnames = [
            "Building Type",
            "Measure",
            "System Type",
            "Run Type",
            "Climate Zone",
            "Average Temperature",
            "Average Electric Energy",
        ]
        writer = csv.DictWriter(csvfile, fieldnames)
        writer.writeheader()

    output_rows = []
    for file in all_files:
        parts = PurePath(file).parts
        building_type = parts[offset + 2]
        cz = parts[offset + 1]
        run = parts[offset + 3].split("-")
        measure = run[0]
        system_type = run[1]
        run_type = run[2]

        print(building_type, cz, measure, system_type, run_type)

        peak = get_deer_peak_range(file, cz)

        query_filter = "SELECT KeyValue \
                            FROM ReportVariableDataDictionary \
                            WHERE VariableName = {}".format(
            '"Cooling Coil Electricity Energy"'
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

        sql = "SELECT sum(VariableValue) \
                    FROM ReportVariableData, ReportVariableDataDictionary \
                    WHERE ReportVariableDataDictionary.VariableName = {} \
                        and ReportVariableData.ReportVariableDataDictionaryIndex = \
                            ReportVariableDataDictionary.ReportVariableDataDictionaryIndex \
                        and ReportVariableDataDictionary.KeyValue IN ({seq}) \
                        and ReportVariableData.TimeIndex IN ({seq1}) \
                    Group BY TimeIndex".format(
            '"Cooling Coil Electricity Energy"',
            seq=",".join(["?"] * len(keep_list)),
            seq1=",".join(["?"] * len(peak)),
        )

        sql2 = "SELECT VariableValue \
                    FROM ReportVariableData, ReportVariableDataDictionary \
                    WHERE ReportVariableDataDictionary.VariableName = {} \
                        and ReportVariableData.ReportVariableDataDictionaryIndex = \
                            ReportVariableDataDictionary.ReportVariableDataDictionaryIndex \
                        and ReportVariableData.TimeIndex IN ({seq})".format(
            '"Site Outdoor Air Drybulb Temperature"', seq=",".join(["?"] * len(peak))
        )

        with sqlite3.connect(file) as conn:
            cur = conn.cursor()
            cur.execute(sql, keep_list + peak)
            energy_rows = cur.fetchall()
            cur.execute(sql2, peak)
            temperature_rows = cur.fetchall()

            energy = [x[0] for x in energy_rows]
            temperature = [x[0] for x in temperature_rows]

        temperature_avg = sum(temperature) / len(temperature)
        electric_usage_avg = sum(energy) / len(energy)
        output_row = {
            "Building Type": building_type,
            "Measure": measure,
            "System Type": system_type,
            "Run Type": run_type,
            "Climate Zone": cz,
            "Average Temperature": temperature_avg,
            "Average Cooling Electric Energy": electric_usage_avg,
        }
        output_rows.append(output_row)

    with open(output_file, "a", newline="") as csvfile:
        fieldnames = [
            "Building Type",
            "Measure",
            "System Type",
            "Run Type",
            "Climate Zone",
            "Average Temperature",
            "Average Cooling Electric Energy",
        ]
        writer = csv.DictWriter(csvfile, fieldnames)
        writer.writerows(output_rows)


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
        PurePath("Deer Peak.csv"),
    )

    # Get all the results files
    all_files = search_directories(search_path, results_file_name)

    process(offset, all_files, output_file)


if __name__ == "__main__":
    main()
