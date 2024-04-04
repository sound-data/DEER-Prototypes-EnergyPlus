import csv
from datetime import datetime, timedelta

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
        "Winterbreak": (datetime(2024, 1, 1), datetime(2024, 1, 8)),
        "Martin Luther King Day": datetime(2024, 1, 15),
        "Presidents Day": datetime(2024, 1, 19),
        "Spring Break": (datetime(2024, 3, 25), datetime(2024, 3, 29)),
        "Cesar Chavez Day": datetime(2024, 4, 1),
        "Holiday": datetime(2024, 4, 24),
        "Memorial Day": datetime(2024, 5, 27),
        "Independence Day": datetime(2024, 7, 4),
        "Labor Day": datetime(2024, 9, 2),
        "Veterans Day": datetime(2024, 11, 11),
        "Thanksgiving": (datetime(2024, 11, 28), datetime(2024, 11, 29)),
        "Winterbreak 2": (datetime(2024, 12, 16), datetime(2024, 12, 31)),
        "Summer Break": (datetime(2024, 6, 10), datetime(2024, 8, 11))
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
    if datetime(2024, 1, 1) <= date <= datetime(2024, 6, 10) or datetime(2024, 8, 12) <= date <= datetime(2024, 12, 31):
        if date.weekday() < 5 and not is_holiday(date):
            return "School_Wkday"
        else:
            return "Wkend" if date.weekday() >= 5 else ""
    elif datetime(2024, 6, 10) <= date <= datetime(2024, 8, 11):
        return "Summer_Wkday" if date.weekday() < 5 else "Wkend"
    else:
        return ""

# Generate list of dates from 1/1/24 to 12/31/24
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 12, 31)
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
