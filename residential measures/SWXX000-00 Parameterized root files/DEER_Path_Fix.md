# Issue: 

How to enable the global path of the repository directory?

<%= repository_dir %>/templates/hot water profile/site_mains_water_temp_CZ<%= climate_zone_str %>.csv,  !- File Name

## Testing information
Git repo branch: TRC-RTC/DEER-Prototypes-EnergyPlus-Working at harvest-thermal-combi-HP

Root file: C:\Users\YYang\GitHub\DEER-Prototypes-EnergyPlus-Working\prototypes\residential\DMo-combi\templates\root.pxt

## 1. Hardcoded path in root.pxt (works)
```bash
parameter "repository_dir", :default=> "C:/Users/YYang/GitHub/DEER-Prototypes-EnergyPlus-Working"
<%= repository_dir %>/templates/hot water profile/site_mains_water_temp_CZ<%= climate_zone_str %>.csv,  !- File Name
```

## 2. Automatically derive repository path based on the location of rakefile.rb (works)

Referring to the Workaround 2 in: [Schedule:File gives EnergyPlus error Invalid String Position when using relative path · Issue #129 · sound-data/DEER-Prototypes-EnergyPlus](https://github.com/sound-data/DEER-Prototypes-EnergyPlus/issues/129), the following changes were made.

rakefile.rb
```bash
def generate_site_pxt(idd, ddy_path, site_path, study_dir, config)
  repository_dir = File.expand_path('../..', __dir__) # Automatically determine repository root, if rakefile.rb is in ".../residential measures/HP Combi/", so go up two levels to reach ".../DEER-Prototypes-EnergyPlus-Working/"
  site_file = File.open(site_path, "w")

  # Pass directories from modelkit-config into site.pxt
  site_file.puts(<<-HEREDOC)
<%
# Directory paths
$study_dir = '#{study_dir}'
$prototypes_dir = '#{config[:prototypes_dir][0]}'
$templates_dir = '#{config[:templates_dir][0]}'
$weather_dir = '#{config[:weather_dir][0]}'
$codes_dir = '#{config[:codes_dir][0]}'
$repository_dir = '#{repository_dir}'
%>

  HEREDOC
```
rakefile.rb
```bash
    # generate site.pxt from .ddy file
	file site_path => [ddy_path] do
	  idd = open_data_dictionary
	  pathname = Pathname.new(site_path).relative_path_from(runs_pathname)
	  puts "Generating: #{pathname}"
	  generate_site_pxt(idd, ddy_path, site_path, study_dir, config)
	end
```
root.pxt
```bash
<%= $repository_dir %>/templates/hot water profile/site_mains_water_temp_CZ<%= climate_zone_str %>.csv,  !- File Name
```

## Conclusion and updates

### The issue was fixed by automatically detecting the repository path from the location of rakefile.rb, so manual path input is no longer needed.

### The changes have been pushed to the following folders and branches:

\residential measures\HP Combi\rakefile.rb and combi root files in

- TRC-RTC/DEER-Prototypes-EnergyPlus-TRC_HVAC at SWWH037-01-HP-Combi-Space-and-DHW-with-TES-Res-FS
- TRC-RTC/DEER-Prototypes-EnergyPlus-TRC_HVAC at Res-Dev-Alternative-Residential-Prototypes