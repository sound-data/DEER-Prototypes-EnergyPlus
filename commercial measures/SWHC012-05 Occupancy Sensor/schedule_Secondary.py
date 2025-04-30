import csv
from datetime import datetime, timedelta

# Function to determine temperature status based on day type and hour
def determine_temperature_status(day_type, hour, minute):
    if day_type == "School_Wkday":
        if (hour == 9) or (hour == 10 and minute <= 53) or (hour == 11 and minute <= 23) or (hour == 12 and minute <= 23) or (hour == 13 and minute <= 23) or (hour == 14 and minute <= 53) or (hour == 15 and minute <= 35) or (hour == 16 and minute >= 53) or (hour == 17 and minute >= 53) or (hour == 18 and minute >= 53):
            return "active"
        elif ((hour == 10 and minute >= 54) or (hour == 11 and minute >= 24) or (hour == 12 and minute >= 24) or (hour == 13 and minute >= 24) or (hour == 14 and minute >= 54) or (hour == 15 and minute >= 36) or (hour == 16 and minute < 54) or (hour == 17 and minute < 54) or (hour == 18 and minute < 54)):
            return "setback"
        elif ((hour == 16 and minute >= 54) or (hour == 17 and minute >= 54) or (hour == 18 and minute >= 54)):
            return "active"
        else:
            return "setback"


    elif day_type == "Summer_Wkday":
        if (hour in range(0, 10) or hour in range(14, 23)) or (hour == 10 and minute <= 53) or (hour == 11 and minute <= 53) or (hour == 12 and minute <= 53) or (hour == 13 and minute <= 53):
            return "setback"
        elif (hour == 10 and minute >= 54) or (hour in range(11, 14) and minute >= 54):
            return "active"
        else:
            return "setback"
    else:
        return "setback"

# Function to check if a date falls within a holiday range
def is_holiday(date):
    holidays = {
        "Winterbreak": (datetime(2023, 1, 1), datetime(2023, 1, 8)),
        "Martin Luther King Day": datetime(2023, 1, 15),
        "Presidents Day": datetime(2023, 1, 19),
        "Spring Break": (datetime(2023, 3, 25), datetime(2023, 3, 29)),
        "Cesar Chavez Day": datetime(2023, 4, 1),
        "Holiday": datetime(2023, 4, 24),
        "Memorial Day": datetime(2023, 5, 27),
        "Independence Day": datetime(2023, 7, 4),
        "Labor Day": datetime(2023, 9, 2),
        "Veterans Day": datetime(2023, 11, 11),
        "Thanksgiving": (datetime(2023, 11, 28), datetime(2023, 11, 29)),
        "Winterbreak 2": (datetime(2023, 12, 16), datetime(2023, 12, 31)),
        "Summer Break": (datetime(2023, 6, 10), datetime(2023, 8, 11))
    }
    for holiday, date_range in holidays.items():
        if isinstance(date_range, tuple):
            if date_range[0] <= date <= date_range[1]:
                return holiday
        else:
            if date == date_range:
                return holiday
    return None

# Function to check the day type
def day_type(date):
    if datetime(2023, 1, 1) <= date <= datetime(2023, 6, 10) or datetime(2023, 8, 12) <= date <= datetime(2023, 12, 31):
        if date.weekday() < 5 and not is_holiday(date):
            return "School_Wkday"
        else:
            return "Wkend" if date.weekday() >= 5 else ""
    elif datetime(2023, 6, 10) <= date <= datetime(2023, 8, 11):
        return "Summer_Wkday" if date.weekday() < 5 else "Wkend"
    else:
        return ""

# Generate list of dates from 1/1/24 to 12/31/24
start_date = datetime(2023, 1, 1)
end_date = datetime(2023, 12, 31)
date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

# Generate list of timestamps for every 10 minutes of the day
timestamp_range = [datetime.strptime("00:00", "%H:%M") + timedelta(minutes=6*i) for i in range(10*24)]

# Write data to CSV
with open('temperature_data_secondary.csv', 'w', newline='') as csvfile:
    fieldnames = ['Date', 'Time stamp', 'Temperature', 'Day of the Week', 'Holiday', 'Day Type']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for date in date_range:
        for timestamp in timestamp_range:
            hour = timestamp.hour
            minute = timestamp.minute
            current_day_type = day_type(date)
            temperature_status = determine_temperature_status(current_day_type, hour, minute)
            writer.writerow({'Date': date.strftime('%m/%d/%y'), 
                             'Time stamp': timestamp.strftime('%H:%M'), 
                             'Temperature': temperature_status,
                             'Day of the Week': date.strftime('%A'),
                             'Holiday': is_holiday(date) if is_holiday(date) else '',
                             'Day Type': current_day_type})

print("CSV file generated successfully!")
