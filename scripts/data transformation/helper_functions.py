#helper functions used for CEDARS long format extraction

#Used to get "Start Day of the week" from the RunPeriod object in the IDF file, 
# which is needed for determining the correct starting date of the simulation 
# and thus the correct hourly distribution of consumption across the year.
def get_runperiod_start_day(idf_path):
    '''Extracts the "Day of Week for Start Day" from the RunPeriod object in the IDF file.
    
    Args:
        idf_path (str): Path to the IDF file.
    
    Returns:
        str: The day of the week for the start day (e.g., "Monday"), or None if not found.
    
    '''
    with open(idf_path, "r") as f:
        text = f.read()

    # Remove comments and collapse into one line
    clean = []
    for line in text.splitlines():
        line = line.split("!")[0]  # strip inline comments
        if line.strip():
            clean.append(line)
    text = " ".join(clean)

    # Split into objects and look for RunPeriod
    for obj in text.split(";"):
        obj = obj.strip()
        if not obj:
            continue

        head = obj.split(",", 1)[0].strip().lower()
        if head == "runperiod":
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

            return fields[8].strip() if len(fields) > 8 and fields[8] else None
            # If the field is missing or empty, return None

    return None


            
