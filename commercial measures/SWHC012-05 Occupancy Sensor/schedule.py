# # Temperature Setpoint Schedule Generator (10‑minute Resolution)
# 
# This notebook builds a year-long schedule of "active" vs. "setback" temperature states based on:
# - Building type: Primary (EPr), Secondary (ESe), and Relocatable (ERC)
# - Day type: school weekday, summer weekday, weekend/holiday  
# - Holiday calendar: fixed/calculated dates/ranges  
# - Time-of-day logic: minute-level windows for partial occupancy (e.g., lunch)  
# 
# It also maps those labels to numeric setpoints for use in EnergyPlus "Schedule:File" (cooling & heating).
# - Author: Behzad Salimian Rizi - Solaris Technical - 08/27/2025
# - Author: Kelsey Yen - Solaris Technical - 9/12/2025
# Updated the occupancy fraction by applying time hysterisis (vacancy delay): considering 10 minutes delay for switching setpoint to setback mode.

# Imports
import csv
from datetime import datetime, timedelta
import calendar
from typing import Optional, Tuple
import pandas as pd


# Parameters set the calendar year, time step minutes, and setpoint values for active vs setback
# User parameters

YEAR = 2023
TIME_STEP_MIN = 10



# Setpoint mapping (°C) — edit to match your measure/baseline
COOL_ACTIVE = 23.89
COOL_SETBACK = 29.44
HEAT_ACTIVE = 21.11
HEAT_SETBACK = 15.56


# Holiday and Break Calendar function returns holiday/break name if date is within a defined range

# code edited from online source
def get_holiday(year, n, weekday, month):
    # Note that weekday = 0 for monday, 6 for sunday
    daysInMonth = calendar.monthrange(year, month)[1]
    count = 0
    for day in range(daysInMonth):
        holiday = datetime(year, month, day+1)
        holiday_weekday = holiday.weekday()
        if holiday_weekday == weekday:
            count += 1
            if n == count:
                return holiday
            
# code edited from online source
def get_memday(year):
    # retrieving the required month from the calendar
    month = calendar.monthcalendar(year, 5)

    # checking if the last week of the month has a Monday
    if month[-1][0]:
        return datetime(year, 5, month[-1][0])

    # else return the saturday of the second to last week of the month  
    else:
        return datetime(year, 5, month[-2][0])

def is_holiday(date: datetime) ->Optional[str]:
    holidays = {
        "New Years Day": datetime(YEAR, 1, 1),
        "MLK Day": get_holiday(YEAR, 3, 0, 1), # third Monday in January
        "Presidents Day": get_holiday(YEAR, 3, 0, 2), # third Monday in February
        "Memorial Day": get_memday(YEAR), # last Monday in May
        "Independence Day": datetime(YEAR, 7, 4),
        "Labor Day": get_holiday(YEAR, 1, 0, 9), # first Monday in September
        "Columbus Day": get_holiday(YEAR, 2, 0, 10), # second Monday in October
        "Veterans Day": datetime(YEAR, 11, 11),
        "Thanksgiving Day": get_holiday(YEAR, 4, 3, 11), # fourth Thursday in November
        "Christmas Day": datetime(YEAR, 12, 25),
        "Winter Break 1": (datetime(YEAR, 1, 1), datetime(YEAR, 1, 11)),
        "Spring Break": (datetime(YEAR, 4, 4), datetime(YEAR, 4, 12)),
        "Summer Break 1": (datetime(YEAR, 5, 23), datetime(YEAR, 5, 31)),
        "Summer Break 2": (datetime(YEAR, 8, 8), datetime(YEAR, 8, 16)),
        "Winter Break 2": (datetime(YEAR, 12, 12), datetime(YEAR, 12, 31))
    }
    for name, date_range in holidays.items():
        if isinstance(date_range, tuple):
            if date_range[0] <= date <= date_range[1]:
                return name
        else:
            if date == date_range:
                return name
    return None

# Day Type function labels each date as School_Wkday (Mon-Fri during school terms), Summer_Wkday (Mon-Fri during summer term), or Wkend (Sat, Sun, and holidays)
def day_type(date: datetime) -> str:
    school_term_1 = (datetime(YEAR, 1, 1), datetime(YEAR, 5, 31))
    summer_term = (datetime(YEAR, 6, 1), datetime(YEAR, 8, 16))
    school_term_2 = (datetime(YEAR, 8, 17), datetime(YEAR, 12, 31))

    def in_range(rng: Tuple[datetime, datetime]) -> bool:
        return rng[0] <= date <= rng[1]
    
    if is_holiday(date):
        return "Wkend"
    if in_range(school_term_1) or in_range(school_term_2):
        return "School_Wkday" if date.weekday() < 5 else "Wkend"
    if in_range(summer_term):
        return "Summer_Wkday" if date.weekday() < 5 else "Wkend"
    return ""


def generate_schedule(BT):
    """Generate schedule files for the given building type.

    Inputs:
        BT: one of Primary (EPr), Secondary (ESe), or Relocatable (ERC)
    Outputs:
        None
    Side effects:
        Writes files Labels_BT.csv and Schedule_BT.csv.
        Labels includes categories at each timestep for QC: Date,Time Stamp,Temperature,Day of the Week,Day Type,Holiday.
        Schedules includes all labels plus data columns: Cooling Setpoint (C),Heating Setpoint (C).
    """
    # Output files
    LABEL_CSV = f"Labels_{BT}.csv"
    SETPOINT_CSV = f"Schedule_{BT}.csv"

    # Time-of-Day Logic determines temperature status based on day type and hour, with 10 min warm-up from unoccupied to setpoint and 10-min delay between setpoint and setback.

    if BT == "Secondary":
        def determine_temperature_status(day_type_str: str, hour: int, minute: int) -> str:
            if day_type_str == "School_Wkday":
                if hour in range(8, 11) or hour == 11 and minute <=10 or hour in range(13, 14) or hour == 14 and minute <= 10:
                    return "active"
                else:
                    return "setback"

            elif day_type_str == "Summer_Wkday":
                if hour in range(9, 13) or hour == 13 and minute <= 10:
                    return "active"
                else:
                    return "setback"

            return "setback"
    else: # temperature status for EPr and ECR
        def determine_temperature_status(day_type_str: str, hour: int, minute: int) -> str:
            if day_type_str == "School_Wkday":
                if hour in range(8, 11) or hour == 11 and minute <=10 or hour in range(13, 15) or hour == 15 and minute <= 10:
                    return "active"
                else:
                    return "setback"

            elif day_type_str == "Summer_Wkday":
                if hour in range(9, 13) or hour == 13 and minute <= 10:
                    return "active"
                else:
                    return "setback"

            return "setback"

    # Build calendar and time grid for the year by time step minutes
    start_date = datetime(YEAR, 1, 1)
    end_date = datetime(YEAR, 12, 31)
    date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

    steps_per_day = int(24 * 60 / TIME_STEP_MIN)
    timestamp_range = [datetime.strptime("00:00", "%H:%M") + timedelta(minutes=TIME_STEP_MIN*i) for i in range(steps_per_day)]
    len(date_range), len(timestamp_range)

    # Write data to CSV temp_labels_EPr_2026.csv
    with open(LABEL_CSV, 'w', newline='') as csvfile:
        fieldnames = ['Date', 'Time Stamp', 'Temperature', 'Day of the Week', 'Day Type', 'Holiday']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for date in date_range:
            current_day_type = day_type(date)
            hol = is_holiday(date)
            hol_name = hol if hol else ""
            
            for timestamp in timestamp_range:
                hour = timestamp.hour
                minute = timestamp.minute
                label = determine_temperature_status(current_day_type, hour, minute)
                writer.writerow({
                    'Date': date.strftime('%m/%d/%y'),
                    'Time Stamp': timestamp.strftime('%H:%M'),
                    'Temperature': label,
                    'Day of the Week': date.strftime('%A'),
                    'Day Type': current_day_type,
                    'Holiday': hol_name,
                })

    print(f"Label CSV written: {LABEL_CSV}")

    # Map Labels → Numeric Setpoints (Cooling & Heating) and Save generates `temp_setpoints_YEAR_EPr.csv` with numeric °F columns suitable for EnergyPlus `Schedule:File`.
    rows = []
    for date in date_range:
        current_day_type = day_type(date)
        hol = is_holiday(date)
        hol_name = hol if hol else ""

        for timestamp in timestamp_range:
            hour = timestamp.hour
            minute = timestamp.minute
            label = determine_temperature_status(current_day_type, hour, minute)
            cool_sp = COOL_ACTIVE if label == "active" else COOL_SETBACK
            heat_sp = HEAT_ACTIVE if label == "active" else HEAT_SETBACK
            rows.append({
                'Date': date.strftime('%m/%d/%y'),
                'Time Stamp': timestamp.strftime('%H:%M'),
                'Cooling Setpoint (C)': cool_sp,
                'Heating Setpoint (C)': heat_sp,
                'Label': label,
                'Day Type': current_day_type,
                'Holiday': hol_name
            })

    df_sp = pd.DataFrame(rows)
    df_sp.to_csv(SETPOINT_CSV, index=False)
    df_sp.head(12)

    print(f"Setpoint CSV written: {SETPOINT_CSV}")


if __name__ == "__main__":
    # BT options are Primary (EPr), Secondary (ESe), and Relocatable (ERC)
    generate_schedule(BT = "Primary")
    generate_schedule(BT = "Secondary")
    generate_schedule(BT = "Relocatable")

