from datetime import datetime, date
import calendar

YEAR = 2023

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
            
print(get_holiday(YEAR, 3, 0, 1)) # third Monday in January