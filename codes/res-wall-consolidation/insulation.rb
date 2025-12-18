# Title: insulation.rb
# Description: Script to run Envelope.rb function for residential wall and roof
#              insulation using a CSV input file of insulation parameters and a
#              CSV output file with thickness and conductivity results of all
#              input rows.
#
# Usage:
#     (1) Install modelkit caboodle.
#     (2) On command line enter:
#         modelkit ruby insulation.rb
#
# Inputs:
#     Code requirements for residential wall or ceiling R-value expressed as:
#         lookup_id, Construction type, Cavity R-value (0), and continuous R-value (from Title 24)
#     and read from the following files:
#         t24_2025_wall_insul_inputs.csv
#         t24_2025_roof_insul_inputs.csv
#
#     lookup_id: User label to be displayed in output file
#
#     Construction type: Takes a value from modelkit.envelope.WALL_BASE_TYPES and ROOF_BASE_TYPES.
#         Wall types
#         Concrete MW Solid Grouted
#         Metal Panels
#         Steel Framing at 16 in. on center
#         Wood Framing at 16 in. on center
#         Concrete NW Solid
#         Concrete MW Partially Grouted
#         Concrete with Steel Framing
#         Concrete with Wood Framing
#         Granite 10in
#         Steel Framing at 24 in. on center
#         Wood Framing at 24 in. on center
#
#         Roof types
#         Insulation Entirely Above Deck
#         Metal Roof
#         Attic Roof with Wood Joists
#         Attic Roof with Steel Joists
#         Concrete Roof
#
#
#     Cavity R-value and Continuous R-value in units (ft²·°F·h/BTU) ['R-IP']:
#         For initial analysis, analysts entered 0 as cavity R-value and
#         entered the code required R-value as continuous R-value.
#
# Outputs:
#     Parameters for use with EnergyPlus Material object and EnergyPlus units:
#       output_wall.csv
#           lookup_id
#           wall_cont_thick: Wall thickness for equivalent consolidated layer ['m']
#           wall_cont_cond: Wall thermal conductivity for equivalent consolidated layer ['W/m-K']
#           wall_cav_thick: Wall thickness for equivalent cavity layer ['m'] (0 if input for cavity R-value is 0)
#           wall_cav_cond: Wall thermal conductivity for equivalent cavity layer ['W/m-K']
#       output_roof.csv:
#           lookup_id, roof_cont_thick, roof_cont_cond, roof_cav_thick, roof_cav_cond
#
# Authors:
#     (C) 2025 Kelsey Yen (Solaris Technical LLC)
#     (C) 2025 Nicholas Fette (Solaris Technical LLC)


require("modelkit")
require("gli")
require("rubygems/patches/gli-2.13.2/lib/gli/app_support")
require("rubygems/patches/gli-2.13.2/lib/gli/commands/help")
require("modelkit/units")
require("modelkit/thermalbridging")
require("modelkit/energyplus")
require("modelkit/envelope")
require("csv")

# Function from Envelope.rb
include Envelope

def results_roof(roof_base_type, roof_base_cavity_insul, roof_base_cont_insul)
  begin
    return Envelope.roof_insulation(roof_base_type, roof_base_cavity_insul['R-IP'], roof_base_cont_insul['R-IP'])
  rescue StandardError => err
    puts "Error calling roof_insulation(#{roof_base_type}, #{roof_base_cavity_insul}, #{roof_base_cont_insul}, ...)"
    puts err.backtrace
    return "error: " + err.message,0,0,0,0
  end
end

def results_wall(wall_base_type, wall_base_cavity_insul, wall_base_cont_insul)

  begin
    # Arbitrary values for wall_area, floor_length, parapet_length are okay but must provide wall_area > 0.
    return Envelope.wall_insulation(wall_base_type, wall_base_cavity_insul['R-IP'], wall_base_cont_insul['R-IP'],
      :wall_area=>1.0, :floor_length=>0.0, :parapet_length=>0.0)
  rescue StandardError => err
    puts "Error calling wall_insulation(#{wall_base_type}, #{wall_base_cavity_insul}, #{wall_base_cont_insul}, ...)"
    puts err.backtrace
    return "error: " + err.message,0,0,0,0
  end
end

# Loop through input file for roof insulation requirements
input_roof = CSV.read("t24_2025_roof_insul_inputs.csv")

CSV.open("output_roof.csv", "w") do |output_roof|
  output_roof << ["lookup_id", "roof_base_type", "roof_cont_thick", "roof_cont_cond", "roof_cav_thick", "roof_cav_cond"]

  # skip header row
  input_roof[1..-1].each_with_index do |row, index|

    lookup_id = row[0].to_str
    roof_base_type = row[1].to_str
    roof_base_cavity_insul = row[2].to_f
    roof_base_cont_insul = row[3].to_f
    final_roof = results_roof(roof_base_type, roof_base_cavity_insul, roof_base_cont_insul)

    # write output to file
    output_roof << [lookup_id, roof_base_type, final_roof[0], final_roof[1], final_roof[2], final_roof[3]]

    puts "output_roof success #{index}"
  end
end

# Loop through input file for wall insulation requirements
input_wall = CSV.read("t24_2025_wall_insul_inputs.csv")

CSV.open("output_wall.csv", "w") do |output_wall|
  output_wall << ["lookup_id", "wall_base_type", "wall_cont_thick", "wall_cont_cond", "wall_cav_thick", "wall_cav_cond"]

  # skip header row
  input_wall[1..-1].each_with_index do |row, index|

    lookup_id = row[0].to_str
    wall_base_type = row[1].to_str
    wall_base_cavity_insul = row[2].to_f
    wall_base_cont_insul = row[3].to_f
    final_wall = results_wall(wall_base_type, wall_base_cavity_insul, wall_base_cont_insul)

    # write output to file
    output_wall << [lookup_id, wall_base_type, final_wall[0], final_wall[1], final_wall[2], final_wall[3]]

    puts "output_wall success #{index}"
  end
end
