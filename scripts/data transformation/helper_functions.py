
#Used to get "Start Day of the week" from the RunPeriod object in the IDF file, 
# which is needed for determining the correct starting date of the simulation 
# and thus the correct hourly distribution of consumption across the year.

def get_runperiod_start_day(idf_path):
    with open(idf_path, "r") as f:
        text = f.read()

    # Remove comments and collapse into one line
    clean = []
    for line in text.splitlines():
        line = line.split("!")[0]  # strip inline comments
        if line.strip():
            clean.append(line)
    text = " ".join(clean)

    # Split into objects
    objects = text.split(";")

    for obj in objects:
        if obj.strip().lower().startswith("runperiod"):
            fields = [f.strip() for f in obj.split(",")]

            # fields[0] = "RunPeriod"
            # fields[1] = Name
            # fields[2] = Begin Month
            # fields[3] = Begin Day of Month
            # fields[4] = Begin Year
            # fields[5] = End Month
            # fields[6] = End Day of Month
            # fields[7] = End Year
            # fields[8] = Day of Week for Start Day  <-- target
            return fields[8] if len(fields) > 8 else None

    return None
