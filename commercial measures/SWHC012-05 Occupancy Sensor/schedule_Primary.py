import csv
from datetime import datetime, timedelta

YEAR = 2026

# Function to determine temperature status based on day type and hour
def determine_temperature_status(day_type, hour, minute):
    if day_type == "School_Wkday":
        if (hour in range(0, 8) or hour in range(19, 24)) or (hour == 11 and minute >= 40) or (hour == 12 and minute >= 40) or (hour == 13 and minute >= 40) or (hour == 16 and minute < 50) or (hour == 17 and minute < 50) or (hour == 18 and minute < 50):
            return "setback"
        elif ((hour == 8) or (hour == 9) or (hour == 10) or (hour == 14) or (hour == 15) or ((hour in range(11, 14)) and minute < 40) or (hour == 16 and minute >= 50) or (hour == 17 and minute >= 50) or (hour == 18 and minute >= 50)):
            return "active"


    elif day_type == "Summer_Wkday":
        if (hour in range(0, 10) or hour in range(14, 23)) or (hour == 10 and minute <= 49) or (hour == 11 and minute <= 49) or (hour == 12 and minute <= 49) or (hour == 13 and minute <= 49):
            return "setback"
        elif (hour == 10 and minute >= 50) or (hour in range(11, 14) and minute >= 50):
            return "active"
        else:
            return "setback"
    else:
        return "setback"

# Function to check if a date falls within a holiday range
def is_holiday(date):
    holidays = {
        "New Years Day": datetime(YEAR, 1, 1),
        "MLK Day": datetime(YEAR, 1, 19),
        "Presidents Day": datetime(YEAR, 2, 16),
        "Memorial Day": datetime(YEAR, 5, 25),
        "Independence Day": datetime(YEAR, 7, 4),
        "Labor Day": datetime(YEAR, 9, 7),
        "Columbus Day": datetime(YEAR, 10, 12),
        "Veterans Day": datetime(YEAR, 11, 11),
        "Thanksgiving Day": datetime(YEAR, 11, 26),
        "Christmas Day": datetime(YEAR, 12, 25),
        "Winter Break 1": (datetime(YEAR, 1, 1), datetime(YEAR, 1, 11)),
        "Spring Break": (datetime(YEAR, 4, 4), datetime(YEAR, 4, 12)),
        "Summer Break 1": (datetime(YEAR, 5, 23), datetime(YEAR, 5, 31)),
        "Summer Break 2": (datetime(YEAR, 8, 8), datetime(YEAR, 8, 16)),
        "Winter Break 2": (datetime(YEAR, 12, 12), datetime(YEAR, 12, 31))
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
timestamp_range = [datetime.strptime("00:00", "%H:%M") + timedelta(minutes=10*i) for i in range(6*24)]

# Write data to CSV
with open('temperature_data_primary.csv', 'w', newline='') as csvfile:
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
