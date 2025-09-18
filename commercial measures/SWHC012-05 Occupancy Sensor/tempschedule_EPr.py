#!/usr/bin/env python
# coding: utf-8

# 
# # Temperature Setpoint Schedule Generator (15‑minute Resolution)
# 
# This notebook builds a **year-long schedule** of "active" vs. "setback" temperature states based on:
# - **Building type:** Primary School
# - **Day type:** school weekday, summer weekday, weekend/holiday  
# - **Holiday calendar:** fixed dates/ranges  
# - **Time-of-day logic:** minute-level windows for partial occupancy (e.g., lunch)  
# 
# It also **maps those labels to numeric setpoints** for use in EnergyPlus `Schedule:File` (cooling & heating).
# - **Author:** Behzad Salimian Rizi - Solaris Technical - 08/27/2025
# - **Author:** Kelsey Yen - Solaris Technical - 9/12/2025
# 

# 
# ## 1) Imports
# We use Python's built-in libraries for dates and CSV. Pandas is used for a quick preview.
# 

# In[7]:


import csv
from datetime import datetime, timedelta
from typing import Optional, Tuple
import pandas as pd


# 
# ## 2) Parameters
# Set the calendar year, time step, and setpoint values for **active** vs **setback**.  
# > Edit these to match your project (°F shown; you can switch to °C if preferred).
# 

# In[10]:


# ---- User parameters ----
YEAR = 2026
TIME_STEP_MIN = 15

# Output files
LABEL_CSV = f"temp_labels_{YEAR}_EPr.csv"
SETPOINT_CSV = f"temp_setpoints_{YEAR}_EPr.csv"

# Setpoint mapping (°F) — edit to match your measure/baseline
COOL_ACTIVE_F = 75.0
COOL_SETBACK_F = 85.0
HEAT_ACTIVE_F = 70.0
HEAT_SETBACK_F = 60.0


# 
# ## 3) Holiday / Break Calendar
# `is_holiday(date)` returns the holiday/break name if the date is within a defined day or range; otherwise `None`.
# 

# In[11]:


def is_holiday(date: datetime) -> Optional[str]:
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
    for name, date_range in holidays.items():
        if isinstance(date_range, tuple):
            if date_range[0] <= date <= date_range[1]:
                return name
        else:
            if date == date_range:
                return name
    return None


# 
# ## 4) Day Type Classifier
# Labels each date as:
# - `School_Wkday` (Mon–Fri during school terms, not holidays)
# - `Summer_Wkday` (Mon–Fri during summer)
# - `Wkend` (Sat/Sun and holidays)
# 

# In[12]:


def day_type(date: datetime) -> str:
    school_term_1 = (datetime(YEAR, 1, 1), datetime(YEAR, 5, 31))
    summer_term = (datetime(YEAR, 7, 1), datetime(YEAR, 8, 16))
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


# 
# ## 5) Time‑of‑Day Logic → Active vs. Setback
# `determine_temperature_status(day_type, hour, minute)`
# 

# In[23]:


def determine_temperature_status(day_type_str: str, hour: int, minute: int) -> str:
    if day_type_str == "School_Wkday":
        if hour in (range(0, 8), range(17, 24), hour == 11 and minute >= 45, hour == 12 and minute >= 45, hour == 13 and minute >= 45, hour == 16 and minute < 45, hour == 17 and minute >= 45):
            return "setback"
        elif hour in (hour == 7 and minute >= 45, (8, 9, 10, 13, 14), range(11, 14) and minute < 15):
            return "active"
        else:
            return "setback"

    elif day_type_str == "Summer_Wkday":
        if hour in (range(0, 9), range(13, 24), (10, 11, 12, 13) and minute < 45):
            return "setback"
        elif hour in (8 and minute >= 45, range(9, 13), hour == 13 and minute >= 45):
            return "active"
        else:
            return "setback"

    return "setback"


# 
# ## 6) Build Calendar and Time Grid
# Creates all dates for the year and timestamps every `TIME_STEP_MIN` minutes.
# 

# In[24]:


start_date = datetime(YEAR, 1, 1)
end_date = datetime(YEAR, 12, 31)
date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

steps_per_day = int(24 * 60 / TIME_STEP_MIN)
timestamp_range = [datetime.strptime("00:00", "%H:%M") + timedelta(minutes=TIME_STEP_MIN*i)
                   for i in range(steps_per_day)]
len(date_range), len(timestamp_range)


# 
# ## 7) Write Label CSV (`active` / `setback`)
# 

# In[25]:


with open(LABEL_CSV, 'w', newline='') as csvfile:
    fieldnames = ['Date', 'Time Stamp', 'Temperature', 'Day of the Week', 'Holiday', 'Day Type']
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
                'Holiday': hol_name,
                'Day Type': current_day_type
            })

print(f"Label CSV written: {LABEL_CSV}")


# 
# ## 8) Map Labels → Numeric Setpoints (Cooling & Heating) and Save
# Generates `temperature_setpoints_YEAR.csv` with numeric °F columns suitable for EnergyPlus `Schedule:File`.
# 

# In[26]:


rows = []
for date in date_range:
    current_day_type = day_type(date)
    hol = is_holiday(date)
    hol_name = hol if hol else ""
    for timestamp in timestamp_range:
        hour = timestamp.hour
        minute = timestamp.minute
        label = determine_temperature_status(current_day_type, hour, minute)
        cool_sp = COOL_ACTIVE_F if label == "active" else COOL_SETBACK_F
        heat_sp = HEAT_ACTIVE_F if label == "active" else HEAT_SETBACK_F
        rows.append({
            'Date': date.strftime('%m/%d/%y'),
            'Time Stamp': timestamp.strftime('%H:%M'),
            'Cooling Setpoint (F)': cool_sp,
            'Heating Setpoint (F)': heat_sp,
            'Label': label,
            'Day Type': current_day_type,
            'Holiday': hol_name
        })

df_sp = pd.DataFrame(rows)
df_sp.to_csv(SETPOINT_CSV, index=False)
df_sp.head(12)


# 
# ## 9) Notes on Using with EnergyPlus
# - Use the **Cooling Setpoint (F)** and **Heating Setpoint (F)** columns to create separate `Schedule:File` objects.
# - Convert setpoints to °C before export or in IDF using formula:
#   - °C = (°F − 32) × 5/9




