puts("hey its me!")

require("modelkit/parametrics/worksheet")

def get_water_params()
  # Reads CSV file with headers climate_name,weather_name,:tout_ave,:delta_t_max
  # Returns:
  #   water_params: Hash table mapping climate_name => item
  # where each item = {Hash table with keys tout_ave and delta_t_max}

  water_params = Hash.new
  worksheet_rows = Modelkit::Worksheet.open("weather_params_for_water_mains.csv")
  #puts worksheet_rows
  worksheet_rows.each_row do |row1, index1, variables1, parameters1|
    #  puts "row1 = #{row1}"
    #  puts "index1 = #{index1}"
    # puts "variables1 = #{variables1}"
    # puts "parameters1 = #{parameters1}"
    key = variables1[:climate_name]
    water_params[key] = parameters1
  end

  # puts water_params
  # puts water_params["CZ01"]

  return (water_params)
end
