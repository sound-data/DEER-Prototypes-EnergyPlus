import platform
import csv
import sqlite3
from pathlib import Path, PurePath
import datetime


def get_avg_peak_cooling_energy(file, cz):

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

    peak = get_deer_peak_range(file, cz)
    query = "SELECT VariableValue \
                FROM ReportVariableData, ReportVariableDataDictionary \
                WHERE ReportVariableDataDictionary.VariableName = {} \
                    and ReportVariableData.ReportVariableDataDictionaryIndex = \
                        ReportVariableDataDictionary.ReportVariableDataDictionaryIndex \
                    and ReportVariableData.TimeIndex IN ({seq})".format(
        '"Cooling:Electricity"', seq=",".join(["?"] * len(peak))
    )

    with sqlite3.connect(file) as conn:
        cur = conn.cursor()
        cur.execute(query, peak)
        energy_rows = cur.fetchall()
        energy = [float(x[0]) for x in energy_rows]

    return round(sum(energy) / len(energy), 2)


def process(offset, all_files, output_file):

    fieldnames = [
        "File Name",
        "Building Type",
        "Climate Zone",
        "System Type",
        "Cooling Capacity",
        "Heating Capacity",
        "Conditioned Area",
        "Electricity Heating",
        "Natural Gas Heating",
        "Electricity Cooling",
        "Electricity Fans",
        "Unmet Hours Heating",
        "Unmet Hours Cooling",
        "Average Peak Cooling Energy",
    ]

    with open(output_file, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames)
        writer.writeheader()

    output_rows = []
    for file in all_files:
        parts = PurePath(file).parts
        building_type = parts[offset + 3].split("&")[0]
        cz = parts[offset + 2]
        system_type = parts[offset + 4].split("-")[1]

        avg_peak_cooling_energy = get_avg_peak_cooling_energy(file, cz)

        conditioned_area_query = "SELECT Value \
                FROM TabularDataWithStrings \
                WHERE TableName = {} \
                    and RowName = {} \
                    and ColumnName = {}".format(
            "'Zone Summary'", "'Conditioned Total'", "'Area'"
        )

        cooling_capacity_query = "SELECT sum(Value) \
                FROM TabularDataWithStrings \
                WHERE ColumnName = {}".format(
            "'Design Size Nominal Cooling Capacity'"
        )

        heating_capacity_query = "SELECT sum(Value) \
                FROM TabularDataWithStrings \
                WHERE ColumnName = {}".format(
            "'Design Size Nominal Heating Capacity'"
        )

        electricity_heating_query = "SELECT Value \
                FROM TabularDataWithStrings \
                WHERE TableName = {} \
                and RowName = {} \
                and ColumnName = {}".format(
            "'End Uses'", "'Heating'", "'Electricity'"
        )

        naturalgas_heating_query = "SELECT Value \
                FROM TabularDataWithStrings \
                WHERE TableName = {} \
                and RowName = {} \
                and ColumnName = {}".format(
            "'End Uses'", "'Heating'", "'Natural Gas'"
        )

        electricity_cooling_query = "SELECT Value \
                FROM TabularDataWithStrings \
                WHERE TableName = {} \
                and RowName = {} \
                and ColumnName = {}".format(
            "'End Uses'", "'Cooling'", "'Electricity'"
        )

        electricity_fans_query = "SELECT Value \
                FROM TabularDataWithStrings \
                WHERE TableName = {} \
                and RowName = {} \
                and ColumnName = {}".format(
            "'End Uses'", "'Fans'", "'Electricity'"
        )

        setpoint_not_met_heating_query = "SELECT Value \
                FROM TabularDataWithStrings \
                WHERE TableName = {} \
                and RowName = {} \
                and ColumnName = {}".format(
            "'Comfort and Setpoint Not Met Summary'",
            "'Time Setpoint Not Met During Occupied Heating'",
            "'Facility'",
        )

        setpoint_not_met_cooling_query = "SELECT Value \
                FROM TabularDataWithStrings \
                WHERE TableName = {} \
                and RowName = {} \
                and ColumnName = {}".format(
            "'Comfort and Setpoint Not Met Summary'",
            "'Time Setpoint Not Met During Occupied Cooling'",
            "'Facility'",
        )

        with sqlite3.connect(file) as conn:
            cur = conn.cursor()
            cur.execute(conditioned_area_query)
            conditioned_area = round(float(cur.fetchone()[0]), 2)
            cur.execute(cooling_capacity_query)
            cooling_capacity = round(float(cur.fetchone()[0]), 2)
            cur.execute(heating_capacity_query)
            heating_capacity = round(float(cur.fetchone()[0]), 2)
            cur.execute(electricity_heating_query)
            electricity_heating = round(float(cur.fetchone()[0]), 2)
            cur.execute(naturalgas_heating_query)
            naturalgas_heating = round(float(cur.fetchone()[0]), 2)
            cur.execute(electricity_cooling_query)
            electricity_cooling = round(float(cur.fetchone()[0]), 2)
            cur.execute(electricity_fans_query)
            electricity_fans = round(float(cur.fetchone()[0]), 2)
            cur.execute(setpoint_not_met_heating_query)
            setpoint_not_met_heating = round(float(cur.fetchone()[0]), 2)
            cur.execute(setpoint_not_met_cooling_query)
            setpoint_not_met_cooling = round(float(cur.fetchone()[0]), 2)

        output_row = {
            "File Name": file,
            "Building Type": building_type,
            "Climate Zone": cz,
            "System Type": system_type,
            "Cooling Capacity": cooling_capacity,
            "Heating Capacity": heating_capacity,
            "Conditioned Area": conditioned_area,
            "Electricity Heating": electricity_heating,
            "Natural Gas Heating": naturalgas_heating,
            "Electricity Cooling": electricity_cooling,
            "Electricity Fans": electricity_fans,
            "Unmet Hours Heating": setpoint_not_met_heating,
            "Unmet Hours Cooling": setpoint_not_met_cooling,
            "Average Peak Cooling Energy": avg_peak_cooling_energy,
        }
        output_rows.append(output_row)

    with open(output_file, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames)
        writer.writerows(output_rows)


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
        root = PurePath("C:/DEER-Prototypes-EnergyPlus")
        # measure to search
        search_folder = PurePath("commercial measures/SWSV020-01 CLRM")
        # sqlite database to use
        input_file = "instance-out.sql"
        # where to write the results
        results_folder = PurePath("C:/CLRM Results")
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


if __name__ == "__main__":
    main()
