# Copyright (c) 2011-2020 Big Ladder Software LLC. All rights reserved.
# See the file "license.txt" for additional terms and conditions.

if (not defined?(Modelkit))
  begin
    require("modelkit")
  rescue LoadError => exception
    args = ARGV.join(" ")
    puts exception
    puts "\e[1m\e[31mERROR: This rakefile requires the Modelkit library. Make sure that you have the\nModelkit gem installed in your local Rubygems environment, or try running the\nrakefile using your stand-alone installation of Modelkit by typing:\e[0m\n  \e[1mmodelkit rake #{args}\e[0m"
    exit
  end
end


old_root_dir = File.expand_path("#{__dir__}/../..")

require("pathname")
require("json")

require("modelkit/config")
require("modelkit/multitable")
require("modelkit/parametrics")  # need this now
require("modelkit/parametrics/worksheet")
require("modelkit/energyplus")


# Add to modelkit-energyplus:
# other args:
# - which design days
# - water mains temp?
# - daylight saving time?
def generate_site_pxt(idd, ddy_path, site_path)
  site_file = File.open(site_path, "w")

  if (File.exists?(ddy_path))
    input_file = OpenStudio::InputFile.open(idd, ddy_path)
  else
    puts "File not found: #{ddy_path}"
    exit
  end

  site_locations = input_file.find_objects_by_class_name("Site:Location").to_a

  if (site_locations.empty?)
    puts "Error: could not find Site:Location object"
    exit
  else
    site_file.puts(site_locations.first.to_idf)
  end

  all_design_days = input_file.find_objects_by_class_name("SizingPeriod:DesignDay").to_a

  # Better to pass in array of requested days, e.g., ["Ann Htg 99.6% Condns DB"), "Ann Clg .4% Condns DB=>MWB"]
  selected_design_days = all_design_days.find_all { |dd| dd.name.include?("Ann Htg 99.6% Condns DB") or dd.name.include?("Ann Clg .4% Condns DB=>MWB") }  # or "Ann Htg 99% Condns DB" and "Ann Clg 1% Condns DB=>MWB"

  if (selected_design_days.length < 2)
    puts "Warning:  Could not find requested design days; including all design days"
    selected_design_days = all_design_days
  end

  # Write design days to site file.
  selected_design_days.each { |dd| site_file.puts(dd.to_idf) }


# 'CorrelationFromWeatherFile' is available starting in EP 9.0.

# Does this work for design-day only runs?
# Seems to work for annual.
  site_file.puts("\n\nSite:WaterMainsTemperature,\n  CorrelationFromWeatherFile;\n")

  daylight_saving_time = input_file.find_objects_by_class_name("RunPeriodControl:DaylightSavingTime").to_a
  if (not daylight_saving_time.empty?)
    site_file.puts
    site_file.puts(daylight_saving_time.first.to_idf)
  end

  site_file.close
end


# NOPUB Should move into Modelkit somewhere.
# Support for running simulations in parallel.
require("open3")
require("set")

$child_pids = Set.new  # Global tracking of child PIDs

# Return PID?
def run_process(command, dir)
  # ':chdir => dir' will force the process to run in the specified directory.
  # NOTE: Separate processes are required to make the EnergyPlus runs thread safe!
  Open3.popen3(command) do |stdin, stdout, stderr, thread|
    $child_pids.add(thread.pid)
    # This might work with just an instance variable or similar.

    stdin.close  # All input already sent with command

    file_out = File.open("#{dir}/stdout", "w")
    file_err = File.open("#{dir}/stderr", "w")

    while (line = stdout.gets)
      file_out.puts(line)
      #@proc_out.call(line) if (@proc_out)
    end

    # This is probably not right.
    while (line = stderr.gets)
      file_err.puts(line)
      #@proc_err.call(line) if (@proc_err)
    end

    stdout.close
    stderr.close

    file_out.close
    file_err.close

    #print "Completed: #{File.basename(dir)}\n"
    $child_pids.delete(thread.pid)
  end
end


climates_csv_path = "climates.csv"
cohorts_csv_path = "cohorts.csv"


# will change old_root_dir to be same as __dir__

# will have project_dir because there should be just one rakefile!


global_pxv_path = "#{old_root_dir}/analysis/global.pxv"
query_path = "#{__dir__}/query.txt"
results_summary_path = "#{__dir__}/results-summary.csv"
results_profile_elec_path = "#{__dir__}/results-profile-elec.csv"
results_profile_gas_path = "#{__dir__}/results-profile-gas.csv"
results_paths = [results_summary_path, results_profile_elec_path, results_profile_gas_path]

runs_dir = "#{__dir__}/runs"
runs_pathname = Pathname.new(runs_dir)

MUTEX = Mutex.new  # Thread lock for when something needs to run in a single thread

config_path = "#{old_root_dir}/.modelkit-config"
if (File.exist?(config_path))
  CONFIG = Modelkit::Config.new(config_path)
else
  raise(".modelkit-config file not found: #{config_path}")
end

config = Hash.new
[:prototypes_dir, :templates_dir, :weather_dir, :codes_dir].each do |key|
  field = key.to_s.gsub(/_/, "-")
  if (path = CONFIG[field])
    # Resolve relative path and normalize the slashes.
    path = File.expand_path(path.gsub(/\\/, "/"), old_root_dir)
    if (not File.exist?(path))
      raise("#{field} directory not found: #{path}")
    end
  else
    raise("#{field} field missing in .modelkit-config")
  end
  config[key] = path
end

max_workers = CONFIG["max-workers"]
if (max_workers.nil?)
  max_workers = 1
end


rake_tasks = Rake.application.top_level_tasks
rake_task_name = rake_tasks.first  # Multiple tasks are allowed, but assume one

rake_options = Rake.application.options
rake_options.always_multitask = true  # --multitask, -m
#rake_options.job_stats = true  # --job-stats   true | :history
rake_options.thread_pool_size = max_workers - 1  # --jobs, -j (default 12 on Mac)

if (rake_options.dryrun or rake_options.show_all_tasks or
  rake_options.show_prereqs or rake_options.show_tasks)
  # These are information-only requests. Rake nonetheless registers as invoked
  # with the "default" task name but nothing actually gets run.
  rake_task_name = "none"
end


# Show threads message and info about how to change
#   Running with 8 threads (edit .modelkit-config to change).
#   Type Ctrl+C to cancel all tasks.

require "io/console"  # need this anyway for progress bar

#$stdin.echo = false  # turn off echo; in Mac shows a cursor with a key icon
# This prevents the user from over-typing the output stream.

# also try switching to raw mode--should also block user input; maybe no key icon?

#print "\e[?25l"  # hide the cursor; MUST remember to show it again on exit or else it's permanent for the session!


trap("INT") do  # Ctrl+C (polite kill)
  puts "Canceling all tasks.\n"
  if ($child_pids)
    $child_pids.each { |pid| Process.kill("KILL", pid) }
  end
  exit
end

if (Modelkit::Platform.unix?)
  trap("TSTP") do  # Ctrl+Z (suspend)
    puts "Suspending all tasks. Type 'fg' to resume.\n"
    exit
  end
end

if (not rake_task_name =~ /^(prune|clean|none)$/)

# If possible, detect if any tasks will be run before showing this message:
puts "\e[1mType Ctrl+C to cancel all tasks.\e[0m\n"

end

# modelkit rake -A crashes for some reason

# NOPUB Some of above could be included here too.
# Don't evaluate worksheets and generate file tasks if not necessary!
# NOTE: prune does need to evaluate worksheets.
if (not rake_task_name =~ /^(clean|none)$/)

  pxv_paths = []
  site_paths = []

  compose_idf_paths = []


  #rename size_ to sizerun_  size_run_  sizing_run_
  size_ref_paths = []
  size_idf_paths = []
  size_sql_paths = []
  size_json_paths = []

  hardsize_idf_paths = []

  run_sql_paths = []
  run_csv_paths = []



  old_site_paths = Dir.glob("#{runs_dir}/*/site.pxt")
  old_pxv_paths = Dir.glob("#{runs_dir}/**/instance.pxv")

  climates = Modelkit::Parametrics::Worksheet.open(climates_csv_path)
  cohorts = Modelkit::Parametrics::Worksheet.open(cohorts_csv_path)

  climate_pattern = ENV["CLIMATE"] || ""


  puts "Evaluating worksheets...\n"

  csv_table = climates.each_row do |row1, index1, variables1, parameters1|
    #puts "climate_index = #{index1}"

    weather_name = variables1[:weather_file]
    epw_path = "#{config[:weather_dir]}/#{weather_name}"
    ddy_path = "#{config[:weather_dir]}/#{File.basename(weather_name, ".*")}.ddy"  # just put basename in CSV? instead of .epw?

    if (not File.exist?(epw_path))
      raise("weather file \"#{epw_path}\" not found for row #{index1 + 2} of #{climates_csv_path}")
    end

    if (not File.exist?(ddy_path))
      raise("ddy file \"#{ddy_path}\" not found for row #{index1 + 2} of #{climates_csv_path}")
    end

    climate_name = variables1[:climate]

    if (not climate_name)
      raise("required column \"climate\" is missing in climates.csv")
    end

    next if (not climate_name =~ Regexp.new(climate_pattern))

    FileUtils.mkdir_p("#{runs_dir}/#{climate_name}")

    # This file only exists to indicate if the weather file changes for dependency purposes.
    # The weather file is the one input that is separate from instance parameters.
    weather_name_path = "#{runs_dir}/#{climate_name}/weather"
    pathname = Pathname.new(weather_name_path).relative_path_from(runs_pathname)

    if (File.exist?(weather_name_path))
      old_weather_name = File.read(weather_name_path)
      if (weather_name != old_weather_name)
        puts "Updating: #{pathname}\n"
        File.write(weather_name_path, weather_name)
      end
    else
      puts "Writing: #{pathname}\n"
      File.write(weather_name_path, weather_name)
    end

    site_path = "#{runs_dir}/#{climate_name}/site.pxt"
    site_paths << site_path

    # generate site.pxt from .ddy file
    file site_path => [weather_name_path, ddy_path] do
      idd = open_data_dictionary
      pathname = Pathname.new(site_path).relative_path_from(runs_pathname)
      puts "Generating: #{pathname}\n"
      generate_site_pxt(idd, ddy_path, site_path)
    end

    if (variables1[:codes_file] and not variables1[:codes_file].empty?)
      codes_path = "#{config[:codes_dir]}/#{variables1[:codes_file]}"
      if (not File.exist?(codes_path))
        raise("codes file \"#{codes_path}\" not found for row #{index1 + 2} of #{climates_csv_path}")
      end

      codes_table = Modelkit::MultiTable.new(codes_path)

    else
      codes_table = nil  # Must set something to pass to next worksheet
    end

  # Make sure objects passed in are not mutated by the Worksheet. Make dupes?

    cohorts.each_row(:codes => codes_table, :ashrae_climate => variables1[:ashrae_climate]) do |_, index2, variables2, parameters2|
      #puts "  cohort_index = #{index2}"

      cases_csv_path = "cases/#{variables2[:cohort]}.csv"
      if (not File.exist?(cases_csv_path))
        puts("Cases worksheet \"#{cases_csv_path}\" not found for row #{index2 + 2} of #{cohorts_csv_path}\n")
        next
      end

      root_path = "#{config[:prototypes_dir]}/#{variables2[:root]}"
      if (not File.exist?(root_path))
        puts("Root template \"#{root_path}\" not found for row #{index2 + 2} of #{cohorts_csv_path}\n")
        next
      end

      # Better to pre-read and cache this outside the looping?
      # There are only N worksheets...1 per building type.
      cases = Modelkit::Parametrics::Worksheet.open(cases_csv_path)

      cases.each_row(:ashrae_climate => variables1[:ashrae_climate]) do |_, index3, variables3, parameters3|
        #puts "    case_index = #{index3}"

  # Use run_name to identify an individual simulation run:
        run_name = "#{climate_name}/#{variables2[:cohort]}/#{variables3[:case_name]}"
        case_dir = "#{runs_dir}/#{run_name}"
        FileUtils.mkdir_p(case_dir)

  # better to create this dynamically in cases.csv by combining variables from other layers.
  # all variables need to be propagated first from layer to layer.
  # for example:
  #   :run_name
  #   %= "My Prefix Something: #{climate}/#{cohort}/#{case_name}"
        pxv_string = ":run_name => #{run_name.inspect},\n"
        #pxv_string = ""

        parameters = parameters1 | parameters2 | parameters3
        parameters.each do |key, value|
          if (not value.nil?)
            value_inspect = value.inspect
            if (value.kind_of?(String))
              # Using `inspect` on strings is useful because it reveals invisible
              # characters and invalid byte sequeces. The downside is that the
              # string must be unescaped.
              value_inspect.gsub!(/\\\\/, "\\")
            end
            pxv_string << ":#{key} => #{value_inspect},\n"
          end
        end

        pxv_path = "#{case_dir}/instance.pxv"
        pxv_paths << pxv_path

  # is this needed if run_name is available?
        pathname = Pathname.new(pxv_path).relative_path_from(runs_pathname)

        if (File.exist?(pxv_path))
          old_pxv_string = File.read(pxv_path)
          if (pxv_string != old_pxv_string)
            puts "Updating: #{pathname}\n"
            File.write(pxv_path, pxv_string)
          end
        else
          puts "Writing: #{pathname}\n"
          File.write(pxv_path, pxv_string)
        end

        compose_idf_path = "#{case_dir}/instance.idf"
        compose_idf_paths << compose_idf_path

        if (variables3[:sizing_case])
          size_name = "#{climate_name}/#{variables2[:cohort]}/#{variables3[:sizing_case]}"
          size_dir = "#{runs_dir}/#{size_name}"
          size_ref_path = "#{size_dir}/instance.idf"

          size_idf_path = "#{size_dir}/instance-size.idf"
          size_sql_path = "#{size_dir}/instance-size-out.sql"
          size_json_path = "#{size_dir}/instance-size-out.json"

          if (size_ref_paths.include?(size_ref_path))
            # Avoid creating redundant tasks when multiple cases reference same sizing case.
            create_sizing_tasks = false
          else
            create_sizing_tasks = true

            size_ref_paths << size_ref_path
            size_idf_paths << size_idf_path
            size_sql_paths << size_sql_path
            size_json_paths << size_json_path
          end

          hardsize_idf_path = "#{case_dir}/instance-hardsize.idf"
          hardsize_idf_paths << hardsize_idf_path

          run_idf_path = hardsize_idf_path  # Which input file to run

          run_sql_path = "#{case_dir}/instance-hardsize-out.sql"
          run_sql_paths << run_sql_path

          run_csv_path = "#{case_dir}/instance-hardsize-var.csv"
          run_csv_paths << run_csv_path

        else
          # Autosize-only run.
          size_ref_path = nil

          run_idf_path = compose_idf_path  # Which input file to run

          run_sql_path = "#{case_dir}/instance-out.sql"
          run_sql_paths << run_sql_path

          run_csv_path = "#{case_dir}/instance-var.csv"
          run_csv_paths << run_csv_path
        end

        # Compose input file from parameter file.
        #   need more dependencies here: template files
        file compose_idf_path => [site_path, root_path, pxv_path, global_pxv_path] do
          pathname = Pathname.new(compose_idf_path).relative_path_from(runs_pathname)
          puts "Composing: #{pathname}\n"

          site_dir = File.dirname(site_path)
          begin
            Modelkit::Parametrics.template_compose(root_path,
              :annotate => CONFIG["template-compose.annotate"],
              :indent => CONFIG["template-compose.indent"],
              :esc_line => CONFIG["template-compose.esc-line"],
              :dirs => [site_dir, config[:templates_dir]],
              :files => [global_pxv_path, pxv_path],
              :output => compose_idf_path)
          rescue Exception => exception
            puts "#{exception.class.name}: #{exception.message}\n"
            puts "#{exception.backtrace.first}\n" if (not SyntaxError === exception)
            puts "Skipping: #{pathname}\n"
          end
        end

        if (create_sizing_tasks)
          # Generate a modified input file in order to run a design-day-only simulation.
          # NOTE: This can be eliminated if a design-day option is added to energyplus-run.
          file size_idf_path => size_ref_path do
            pathname = Pathname.new(size_idf_path).relative_path_from(runs_pathname)
            puts "Generating size run: #{pathname}\n"

            FileUtils.cp(size_ref_path, size_idf_path)

            idd = open_data_dictionary
            input_file = OpenStudio::InputFile.open(idd, size_idf_path)

            sc_objs = input_file.find_objects_by_class_name("SimulationControl")
            if sc_objs.length != 1
              raise "More than one SimulationControl object found"
            end
            sc = sc_objs[0]
            sc.fields[1] = "Yes"
            sc.fields[2] = "Yes"
            sc.fields[3] = "Yes"
            sc.fields[4] = "Yes"
            sc.fields[5] = "No"

            input_file.write(size_idf_path)
          end

          # Run sizing input files for design days only.
          file size_sql_path => size_idf_path do
            pathname = Pathname.new(size_idf_path).relative_path_from(runs_pathname)
            puts "Running size run: #{pathname}\n"

            command = "modelkit-energyplus energyplus-run --weather=\"#{epw_path}\" \"#{size_idf_path}\""
            run_process(command, size_dir)
          end

          # Generate size data file (instance-size-out.json).
          file size_json_path => size_sql_path do
            pathname = Pathname.new(size_json_path).relative_path_from(runs_pathname)
            puts "Extracting size data: #{pathname}\n"

            # Make a copy to work on because the original gets overwritten by EnergyPlus.size.
            temp_path = "#{File.dirname(size_idf_path)}/instance-temp.idf"
            FileUtils.cp(size_idf_path, temp_path)

            idd = open_data_dictionary
            input_file = OpenStudio::InputFile.open(idd, temp_path)
            sql = Modelkit::EnergyPlus::SQLOutput.new(size_sql_path)

            # This will be fixed to only generate JSON and not modify the input file.
            _, count, output_file = Modelkit::EnergyPlus.size(
              sql, input_file, {json: size_json_path, version: "9-2"})
            #puts("#{count} modifications made")

            FileUtils.rm_f(temp_path)
          end
        end

        if (hardsize_idf_path)
          # This would be a reasonable place to use `multitask` because compose_idf_path and
          # size_json_path are independent and can be run concurrently. However, it seems
          # like `multitask` doesn't compare timestamps like `file` does. Instead it
          # always runs like a regular `task`.
          file hardsize_idf_path => [compose_idf_path, size_json_path] do
            pathname = Pathname.new(hardsize_idf_path).relative_path_from(runs_pathname)
            puts "Applying hard sizes: #{pathname}\n"

            idd = open_data_dictionary
            input_file = OpenStudio::InputFile.open(idd, compose_idf_path)

            json_string = File.read(size_json_path)
            value_map = JSON.parse(json_string, {:symbolize_names=>true})
            output_file, count = Modelkit::EnergyPlus.modify_objects(input_file, value_map)
            #puts("#{count} modifications made")

            # Set SimulationControl fields 1, 2, and 3 to "No", "No", and "No"
            sc_objs = output_file.find_objects_by_class_name("SimulationControl")
            if sc_objs.length != 1
              raise "More than one SimulationControl object found"
            end
            sc = sc_objs[0]
            sc.fields[1] = "No"
            sc.fields[2] = "No"
            sc.fields[3] = "No"
            # Remove Sizing:Zone and Sizing:System objects
            sizing_zones = output_file.find_objects_by_class_name("Sizing:Zone")
            sizing_systems = output_file.find_objects_by_class_name("Sizing:System")
            sizing_plants = output_file.find_objects_by_class_name("Sizing:Plant")
            (sizing_zones + sizing_systems + sizing_plants).each {|x| output_file.delete_object(x)}

            output_file.write(hardsize_idf_path)
          end
        end

        # Run input file in a separate process.
        file run_sql_path => [epw_path, run_idf_path] do
          # Not sure why this check is needed; seems to try to run if even IDF does not exist.
          # May need in other places, like sizing run.
          next if (not File.exist?(run_idf_path))

          pathname = Pathname.new(run_idf_path).relative_path_from(runs_pathname)
          puts "Running: #{pathname}\n"

          # Because this is spawned to the shell, .modelkit-config options will be
          # automatically applied.
          # NOTE: If modelkit-energyplus was thread safe, would not have to run this
          #   as a separate process.
          command = "modelkit-energyplus energyplus-run --weather=\"#{epw_path}\" \"#{run_idf_path}\""
          run_process(command, case_dir)
          #$bar.inc
        end


  # see discussion with Michael
        file run_csv_path => run_sql_path

  # deleting instance-out.csv breaks it; doesn't know how to recover

      end

    end
  end


  prune_paths = (old_site_paths - site_paths) + (old_pxv_paths - pxv_paths)

  if (not prune_paths.empty? and not rake_task_name =~ /^(prune|clean|none)$/)
    puts "\e[1m\e[33mNote: There are cases in the runs directory that are not referenced by any\n" \
      "worksheet. You may want to delete them by typing:\e[0m\n  \e[1mmodelkit rake prune\e[0m\n"
  end

end


desc "Generate case files"
task :cases do
  new_case_csv = "skip,case_name\n,defaults\n"  # Could be read from an argument instead

  cohorts.each_row(:codes => nil, :ashrae_climate => nil) do |_, index2, variables2, parameters2|
    csv_path = "cases/#{variables2[:cohort]}.csv"
    if (File.exist?(csv_path))
      puts "Found cases for cohort \"#{variables2[:cohort]}\" at #{csv_path}\n"
    else
      puts "Missing cases for cohort \"#{variables2[:cohort]}\""
      puts "Creating: #{csv_path}\n"
      FileUtils.mkdir_p("cases")
      File.write(csv_path, new_case_csv)
    end
  end
end


desc "Delete unreferenced files"
task :prune do
  if (prune_paths.empty?)
    puts "Prune has nothing to delete."
  else
    prune_dirs = []
    puts "\e[1m\e[31mPrune will delete the following files:\e[0m"

# show each as:  dirname/* (106 files)

    prune_paths.each do |path|
      dir = File.dirname(path)
      prune_dirs << dir
      pathname = Pathname.new(dir).relative_path_from(runs_pathname)
      puts "  \e[31m#{pathname}\e[0m"
    end
    print "\e[1m\e[31mConfirm (y/n)?\e[0m "

    input = ENV["CONFIRM"] || $stdin.gets || ""
    if (ENV["CONFIRM"] or not $stdin.tty?)
      puts input  # Echo when not already written to STDOUT
    end

    $start_time = Time.now  # Reset to cut out wait time on the user prompt
    if (input.strip =~ /^y/i)
      puts "Pruning files..."

      # maybe don't have to repeat this--already said what was to be deleted
      prune_dirs.each do |dir|
        pathname = Pathname.new(dir).relative_path_from(runs_pathname)
        puts "Deleting: #{pathname}"
        FileUtils.rm_rf(dir)
      end
    else
      puts "Task canceled."
    end
  end
end


desc "Delete all files and results"
task :clean do
  paths = []; names = []
  [runs_dir, *results_paths].each do |path|
    if (File.directory?(path))
      count = Dir.glob("#{path}/**/*").count { |f| File.file?(f) }
      if (count.nonzero?)
        paths << Dir.glob("#{path}/*")
        names << "#{File.basename(path)}/* (#{count} files)"
      end
    elsif (File.file?(path))
      paths << path
      names << File.basename(path)
    end
  end

  if (paths.empty?)
    puts "Clean has nothing to delete."
  else
    puts "\e[1m\e[31mClean will delete the following files:\e[0m"
    names.each { |name| puts "  \e[31m#{name}\e[0m"}
    print "\e[1m\e[31mConfirm (y/n)?\e[0m "

    input = ENV["CONFIRM"] || $stdin.gets || ""
    if (ENV["CONFIRM"] or not $stdin.tty?)
      puts input  # Echo when not already written to STDOUT
    end

    $start_time = Time.now  # Reset to cut out wait time on the user prompt
    if (input.strip =~ /^y/i)
      puts "Cleaning files..."
      FileUtils.rm_rf(paths)
    else
      puts "Task canceled."
    end
  end
end


desc "Generate site files (site.pxt)"
multitask :sites => site_paths


desc "Compose input files"
multitask :compose => compose_idf_paths


# Generate size input files
multitask :"size-idf" => size_idf_paths


# Run size input files
multitask :"size-sql" => size_sql_paths


# Extract size data
multitask :"size-json" => size_json_paths


desc "Apply hard sizes to input files"
multitask :hardsize => hardsize_idf_paths


desc "Run input files"
multitask :run => run_sql_paths


# was file
# as multitask, it runs everytime...
file results_summary_path => [*run_sql_paths, query_path] do
  pathname = Pathname.new(results_summary_path).relative_path_from(Pathname.new(__dir__))
  puts "Processing: #{pathname}\n"

  short_paths = run_sql_paths.map { |path| Pathname.new(path).relative_path_from(runs_pathname) }
  Modelkit::EnergyPlus.sql(short_paths, query_path, :dir => runs_dir, :output => results_summary_path)
end


file results_profile_elec_path => run_csv_paths do
  aggregate_profiles("Electricity:Facility [J](Hourly)", results_profile_elec_path, run_csv_paths, runs_pathname)
end


file results_profile_gas_path => run_csv_paths do
  # NOTE: If Gas:Facility is the last column, there is an extra blank space after
  #   the column name. The blank space must be included for CSV to find the column.
  aggregate_profiles("Gas:Facility [J](Hourly) ", results_profile_gas_path, run_csv_paths, runs_pathname)
end


desc "Aggregate the simulation results"
task :results => results_paths


task :default => :results


def aggregate_profiles(column_name, output_path, run_csv_paths, runs_pathname)
  pathname = Pathname.new(output_path).relative_path_from(Pathname.new(__dir__))
  puts "Processing: #{pathname}\n"

  short_paths = run_csv_paths.map { |path| Pathname.new(path).relative_path_from(runs_pathname) }

  columns = []
  date_time = true
  short_paths.each do |short_path|
    csv_path = "#{runs_pathname}/#{short_path}"
    if (File.exist?(csv_path))
      csv = CSV.read(csv_path, :headers=>true)
      if (date_time)
        column = csv["Date/Time"]
        column.unshift("Date/Time")  # Add header
        columns << column
        date_time = false
      end
      column = csv[column_name]
      column.unshift(short_path)  # Add header
      columns << column
    else
      puts "WARNING: file not found: #{csv_path}\n"
    end
  end

  File.open(output_path, "w") do |file|
    columns.transpose.each { |row| file.puts(row.join(",")) }
  end
end


# NOPUB consider building this into modelkit-energyplus.
#   basically caches IDD path and avoids concurrent openings.

# Open the EnergyPlus IDD if needed, but only do it once.
def open_data_dictionary
  MUTEX.synchronize do  # Lock to prevent opening multiple times concurrently
    if (@idd.nil?)
      puts "Opening Energy+.idd...\n"

      if (path = CONFIG["energyplus-run.engine"])
        path = File.expand_path(path.gsub(/\\/, "/"))  # Resolve path and normalize
        if (File.exist?(path))
          idd_path = "#{path}/Energy+.idd"
          if (not File.exist?(idd_path))
            raise("Energy+.idd not found in specified EnergyPlus directory: #{path}")
          end
        else
          raise("EnergyPlus directory not found: #{path}")
        end
      else
        raise("energyplus-run.engine field missing in .modelkit-config")
      end

      @idd = OpenStudio::DataDictionary.open(idd_path)
    end
  end
  return(@idd)
end


# NICE, works
#require "rake/cpu_counter"
#puts "cpu=#{Rake::CpuCounter.count}"

# Almost works but not quite:

# shows what command was invoked from CLI
# if blank (even with -T), it's "default".
#puts "top level:"
# cli_tasks = Rake.application.top_level_tasks
# cli_task_name = cli_tasks.first  # could be more than one; just grab first for now
# puts "cli_task_name=#{cli_task_name}"  # returns String

# cli_task = Rake.application.tasks.find { |t| t.name == cli_task_name }  # returns Rake::Task
# puts "cli_task=#{cli_task}"
#

#
## Rake has this builtin:
#  Rake.application.lookup(task_name) => task

# work_to_do = false
# if (cli_task.needed?)
#   # Just because needed doesn't mean there is any work to do--check prereqs!
#   cli_task.prerequisite_tasks.each do |prereq|
#     if (prereq.needed?)
#       work_to_do = true
#       break
#     end
#   end
# end
#
# if (work_to_do)
#   puts "Work to do!"
# else
#   puts "Up to date; nothing to do."
# end


$start_time = Time.now
#$bar = RakeProgressbar.new(run_sql_paths.length)

at_exit do
  #$bar.finished
  if (not rake_task_name =~ /^none$/)
    puts "Elapsed task duration: #{Time.now - $start_time} sec"
  end
end
