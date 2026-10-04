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
    # DEER peak days for CZ2025 weather files, per main branch
    # scripts/energy savings/commercial/peakperspec.csv.
    peakspec = dict(
        [
            ("CZ01", 266),
            ("CZ02", 203),
            ("CZ03", 266),
            ("CZ04", 217),
            ("CZ05", 266),
            ("CZ06", 266),
            ("CZ07", 271),
            ("CZ08", 168),
            ("CZ09", 168),
            ("CZ10", 168),
            ("CZ11", 187),
            ("CZ12", 217),
            ("CZ13", 187),
            ("CZ14", 187),
            ("CZ15", 238),
            ("CZ16", 187),
        ]
    )

    start_datetime = datetime.datetime.strptime(
        "2009" + "-" + str(peakspec[cz]), "%Y-%j"
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

        peak = get_deer_peak_range(file, cz)

        sql = "SELECT VariableValue \
                    FROM ReportVariableData, ReportVariableDataDictionary \
                    WHERE ReportVariableDataDictionary.VariableName = {} \
                        and ReportVariableData.ReportVariableDataDictionaryIndex = \
                            ReportVariableDataDictionary.ReportVariableDataDictionaryIndex \
                        and ReportVariableData.TimeIndex IN ({seq})".format(
            '"Electricity:Facility"', seq=",".join(["?"] * len(peak))
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
            cur.execute(sql, peak)
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
            "Average Electric Energy": electric_usage_avg,
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
            "Average Electric Energy",
        ]
        writer = csv.DictWriter(csvfile, fieldnames)
        writer.writerows(output_rows)


def main():

    # Root of the measure folder that contains the experiment subfolders.
    root = "C:\\dev\\SWHC062-03\\commercial measures\\SWHC062-03 Occupancy Fan Controller\\"

    # Experiment subfolders to process. Each is expected to contain a "runs"
    # directory laid out as runs/CZ##/<BldgType>/<M#-cSYS-Base|Measure>/instance-out.sql.
    study_folders = [
        "SWHC062-03 Occupancy Fan Controller_Htl_Ex",  # Hotel
        "SWHC062-03 Occupancy Fan Controller_Ex",      # all other building types
    ]

    results_folder = PurePath(root)

    # Both studies sit at the same depth under root, so one offset works for all.
    offset = len(PurePath(root).parts) + 1

    # Results file_name
    results_file_name = "instance-out.sql"

    # Output file_name

    output_file = PurePath.joinpath(
        results_folder,
        PurePath("Deer Peak.csv"),
    )

    # Get all the results files
    all_files = []
    for study in study_folders:
        search_path = Path(make_search_paths(root, study))
        found = search_directories(search_path, results_file_name)
        print("{}: {} runs".format(study, len(found)))
        all_files.extend(found)

    process(offset, all_files, output_file)


if __name__ == "__main__":
    main()
