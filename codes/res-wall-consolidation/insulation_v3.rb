'''
Title: insulation_v3.rb
Description: Script to run Envelope.rb function for wall and roof insulation using a CSV input file of insulation parameters 
             and a CSV output file with thickness and conductivity results of all input rows.
'''

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
  Envelope.roof_insulation(roof_base_type, roof_base_cavity_insul, roof_base_cont_insul)
end

def results_wall(wall_base_type, wall_base_cavity_insul, wall_base_cont_insul)
  Envelope.wall_insulation(wall_base_type, wall_base_cavity_insul, wall_base_cont_insul)
end

input_roof = CSV.read("t24_2025_roof_insul_inputs.csv")

output_roof = CSV.open("output_roof.csv", "a") do |output_roof|
  output_roof << ["lookup_id", "roof_base_type", "roof_cont_thick", "roof_cont_cond", "roof_cav_thick", "roof_cav_cond"]
end

input_roof.length.times do |i|
  next if i == 0
  lookup_id = input_roof[i][0].to_str
  roof_base_type = input_roof[i][1].to_str
  roof_base_cavity_insul = input_roof[i][2].to_f
  roof_base_cont_insul = input_roof[i][3].to_f
  final_roof = results_roof(roof_base_type, roof_base_cavity_insul, roof_base_cont_insul)

  output_roof = CSV.open("output_roof.csv", "a") do |output_roof|
    output_roof << [lookup_id, roof_base_type, final_roof[0], final_roof[1], final_roof[2], final_roof[3]]
  end
  i+1
  puts "output_roof success #{i}"
end

input_wall = CSV.read("t24_2025_wall_insul_inputs.csv")

output_wall = CSV.open("output_wall.csv", "a") do |output_wall|
  output_wall << ["lookup_id", "wall_base_type", "wall_cont_thick", "wall_cont_cond", "wall_cav_thick", "wall_cav_cond"]
end

input_wall.length.times do |i|
  next if i == 0
  lookup_id = input_wall[i][0].to_str
  wall_base_type = input_wall[i][1].to_str
  wall_base_cavity_insul = input_wall[i][2].to_f
  wall_base_cont_insul = input_wall[i][3].to_f
  final_wall = results_wall(wall_base_type, wall_base_cavity_insul, wall_base_cont_insul)

  outpu_wall = CSV.open("output_wall.csv", "a") do |output_wall|
    output_wall << [lookup_id, wall_base_type, final_wall[0], final_wall[1], final_wall[2], final_wall[3]]
  end
  i+1
  puts "output_wall success #{i}"
end


