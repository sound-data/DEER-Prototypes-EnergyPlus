# Copyright (c) 2011-2020 Big Ladder Software LLC. All rights reserved.
# See the file "license.txt" for additional terms and conditions.

require("erb")
require("stringio")

require("modelkit/parametrics/interface_scope")
require("modelkit/parametrics/template_scope")
require("modelkit/parametrics/template_error")
  require("modelkit/exception_parser")  # could move into template_error?

# where does this belong?
require("modelkit/path")
require("modelkit/path_search")
require("modelkit/units")


$READ_COUNT = 0
$COMPILE_COUNT = 0

# THE RULES
# 1.  Anything available in the scope of a TemplateScope object is available within the template,
#     e.g., 'require'-d modules (ERB), class methods, object methods, object attributes.
# 2.  The scope of each template is private to other templates...unless passed with parameters.
# 3.

module Modelkit
  module Parametrics

    class Template

# NOPUB make it an option? YES, yes
#   referenced from template_scope.rb:  Template::DEPTH_LIMIT
      DEPTH_LIMIT = 9  # Maximum allowable nesting; zero means no sub templates allowed

      COMPILER = ERB::Compiler.new("<>")
      eoutvar = "@local_output"
      COMPILER.put_cmd = "#{eoutvar}.<<"
      COMPILER.insert_cmd = "#{eoutvar}.<<"
      COMPILER.pre_cmd = []  # TemplateScope initializes @local_output
      COMPILER.post_cmd = [eoutvar]

      COMPILER_MUTEX = Mutex.new

# Is this global locally scoped? Can it be accessed from outside this module without Parametrics::
      MUTEX = {}
      CACHE = {}
      NO_CACHE = false  # Set true to disable caching

# NOPUB possible block form that returns line by line of output as it's rendered?
      def self.parse(string, options = {})
        #puts "Template.parse"

        # could strings be indexed in hash by creating a unique hash value
        # from the entire string itself?
        # can the string itself just be used naively as the hash key?  YES

        # bit weird because self.read may have already checked the CACHE
        # could just move CACHE checking in here--handles .parse and .read

        template = self.allocate
        template.send(:initialize, options)
        template.send(:parse, string)
        return(template)
      end

# NOPUB Make sure this works with File-like things (IO, etc.)
      def self.read(path, options = {})
        #puts "Template.read [#{$READ_COUNT}] => #{path}"

        key = path.hash
        if (not MUTEX[key])
          # test this does not have its own concurrency problems!
          MUTEX[key] = Mutex.new
        end

        MUTEX[key].synchronize do
          if (not CACHE.key?(key) or NO_CACHE)

            $READ_COUNT = $READ_COUNT + 1
            #puts "File.read [#{$READ_COUNT}] => #{path}\n"
            string = File.read(path, :encoding => "UTF-8")

  # NOPUB need error checking of file
            options[:path] = path
            template = self.parse(string, options)

            #puts "CACHE[#{key}] => #{path}\n"
            CACHE[key] = template
          else
            # already cached
          end
        end

        return(CACHE[key])
      end

# NOPUB add << method to append new text to content?
#   or make Template immutable
# NOPUB are all these accessors needed?
      attr_accessor :path, :dirs, :options
      attr_reader :group
      attr_reader :groups, :parameters, :rules
      attr_reader :description, :source, :target

# NOPUB include option for no-cache  ?

      def initialize(options = {})
        @source = "".freeze
        @target = ""
        @line_offset = 0

        @group = Group.new("__index__")

        @groups = []
        @parameters = []
        @rules = []

        @description = ""

        @options = options
        @path = options[:path]  # optional
        @dirs = options[:dirs] || []



        if (@path)
          # Search first in local directory of this template, if it has a path.
          @path_search = PathSearch.new(File.dirname(@path), *@dirs)
        else
          @path_search = PathSearch.new(*@dirs)
        end

        @block = nil
      end


      ####### Return array of valid parameter definitions extracted from template
# NOPUB private?
# NOPUB can this method be used on an already-populated template to replace its content?
      def parse(string)
# NOPUB type checks
        source = string.dup

        if (not source.empty? and source[-1] != "\n")
          # Ensure templates always have a final newline character (unless empty).
          # This prevents problems where content of the next template gets appended
          # to the end of the last line of this template without a line break.
          source << "\n"
        end

# NOPUB Ruby 2.2 has String#scrub which is better.
        # Fix invalid byte sequences.
        if (not source.valid_encoding?)
          source = source.encode("UTF-16be", :invalid => :replace, :replace => "?").encode("UTF-8") # check
        end

        if (source.gsub!(/^<%#INITIALIZE\b/, "<%#INTERFACE"))
          # Hide this warning until template library is updated!
          #puts "Warning: The INITIALIZE keyword is deprecated; use INTERFACE instead in template #{@path.inspect}."
        end

# NOPUB consider using this marker instead: <%#Modelkit

# NOPUB Additional error if instances of <%#INTERFACE exist elsewhere besides first line

# NOPUB would like to support this: <%#INTERFACE version: 1.2 encoding: UTF-8
#   these variations must also work: <%#INTERFACE%>
#   MUST be the very first line
        matches = source.scan(/^<%#INTERFACE\b(.*?)%>/m)
        if (matches.length > 1)
          #puts "Warning: Only one INTERFACE block is allowed per template; only the first occurrence will be used in template #{@path.inspect}."
# NOPUB also include the template call chain
          raise(TemplateError, "only one INTERFACE block is allowed in a template")

        elsif (not matches.empty?)
# NOPUB Use this:  interface = source[/.../, 1]
          interface_block = matches[0][0]  # Use first match only
          scope = InterfaceScope.new(@group, self)

          begin
            new_text = scope.instance_eval(interface_block, @path, 1)

            # new_text has errors/warnings from parsing interface header

            # @path sets the __FILE__ variable in the template scope
            # As a result __dir__ also works, and require_relative without any additional code

# don't rescue all exceptions here!
# *********************** temporary
          rescue NoMemoryError => exception  #Exception => exception  # same as $!
            output = Modelkit.parse_exception(exception, interface)
# NOPUB changes to just raising a TemplateError
            output = "Error: Ruby exception in template #{@path.inspect}\n#{output}"
            puts output  # Echo error to console (or log file)

            # Ideally we would raise a new fatal error here that terminates Modelkit but still finishes writing the output file.
            # Calling 'exit' at least stops the program from continuing and overwriting the initial exception.
            exit
          end
          # Interface has been fully parsed now.
          @groups = @group.descendants.select { |child| child.class == Group }
          @parameters = @group.descendants.select { |child| child.class == Parameter }
          @rules = @group.descendants.select { |child| child.class == Rule }
        end

        # ERB strips out block comments <%# ... %> before evaluating which throws
        # off the line numbers for exceptions. To fix, convert all block comments
        # to empty, non-comment blocks with the same number of lines.

        # Strip the entire INTERFACE block but count the line offset.
        source.sub!(/\A<%#INTERFACE\b.*?%>\n?/m) do |block|
          @line_offset = block.count("\n".freeze)
          next("".freeze)
        end

        # Replace other comment blocks with an equivalent number of blank lines.
        source.gsub!(/<%#.*?%>/m) do |block|
          count = block.count("\n".freeze)
          next("<%#{count > 0 ? "\n" * count : " "}%>".freeze)
        end

        @source = string.dup.freeze  # Save original for reference
        #puts "*** CONTENT ***"
        #puts source
        #puts "*** END ***"

        $COMPILE_COUNT = $COMPILE_COUNT + 1
        #puts "COMPILER.compile [#{$COMPILE_COUNT}] => #{path}\n"

        COMPILER_MUTEX.synchronize do
          compiled, encoding = COMPILER.compile(source)
          @target = compiled.freeze
        end

        #puts "*** CODE ***"
        #puts @target
        #puts "*** END ***"

        # parse could also:
        # - compile => checks syntax, finds unused parameters, warnings
        # - postponed compile => faster when just an :inherit reference is needed

        return(nil)  # ? what to return here?
      end

# NOPUB there is a method in Ruby 2.2+ that is better/safer:
#   binding.local_variable_set(key, value)
      # Use to set any type of variable (local, instance, or otherwise) in the template scope.
      # def set_variable(name, value)
      #   scope_eval("#{name} = #{value.inspect}")
      # end

# better name?  validate, filter, fillout, expand, fill, interpolate, interpret, evaluate_parameters
# this can be called on its own to examine what parameters will be actually used with compose.
      def normalize(inputs = Hash.new)
        normalized = {}  #inputs.dup  # Make a copy to preserve original user parameters for later
        audit = {}  # Audit is a Hash of Hashes for now; need real objects later

        # FIRST, have to complete the full set of parameters => needed to check rules!
        # Also good time to check for missing values.

        #puts "normalize: #{@path}"

        parameters.each do |param_def|
          key = param_def.variable_name.to_sym  #param_def.key.to_sym
          #puts "key=#{key.inspect}"

          if (not inputs[key].nil?)
            value = inputs[key]
            if (param_def.valid?(value))
              normalized[key] = value
              audit[key] = {:value => value, :state => :specified, :rule => nil}
            else
              puts "Error: Value #{value} is not in domain for #{key}; template failed.\n"
              puts "  #{value.class} was specified, expecting #{param_def.domain}\n"
            end

          elsif (param_def.required?)
            # Could a required parameter be filled with a force or default from a rule??
            # For now, assume not.
            normalized[key] = nil
            audit[key] = {:value => nil, :state => :missing, :rule => nil}
            puts "Error: Required parameter missing (#{key}); template failed.\n"

          else  # Parameter not specified or nil
            normalized[key] = param_def.default
            audit[key] = {:value => param_def.default, :state => :defaulted, :rule => nil}
          end
        end

        # Test all the rules with the given parameters; figure out which ones actually apply and will be run.
#        true_rules = []
        rules.each do |rule_def|
# NOPUB need to test here against the _results_ of earlier rules within this template scope,
#   not just the normalize user inputs.

          #puts "evaluating rule: #{rule_def.key}"
          if (rule_def.test(normalized))
#            true_rules << rule_def
            #puts "true rule: #{rule_def.key}"
#          end
#        end

        # Run the qualified rules and get the scope objects for each one.
        # The scope results will be looped over.

# Temporarily comment stuff out. Need to fix indent later.
#        true_rules.each do |rule_def|
          rule_scope = rule_def.evaluate

          rule_scope.defaulted.each do |key, value|
            # Skip any parameter in this rule that does not exist in the template.
            next if (not normalized.keys.include?(key))

            # Apply defaulted value if state is merely defaulted by something else.
            # (Could be defaulted by parameter definition or another prior rule.)
            # Maybe apply if missing?
            # Ignore if state is specified, forced, or disabled.
            if (audit[key][:state] == :defaulted or audit[key][:state] == :defaulted_by)

              normalized[key] = value
              audit[key] = {:value => value, :state => :defaulted_by, :rule => rule_def}

              # In debug mode, provide extra information when overridding :defaulted_by
              # Don't warn if the value is the same!
              #puts "Warning: For rule #{rule_def.key}, parameter (#{key}) was previously defaulted in rule #{audit[key][:rule].key}.\n"
            end
          end

          rule_scope.forced.each do |key, value|
            # Skip any parameter in this rule that does not exist in the template.
            next if (not normalized.keys.include?(key))

            # Apply forced value if not already forced by something else.
            # Don't warn if the values is the same!
            if (audit[key][:state] == :forced_by and normalized[key] != value)
              puts "Warning: For rule #{rule_def.key}, parameter (#{key}) was previously forced in rule #{audit[key][:rule].key}; " \
                "previous value will be applied.\n"

            # Should force or disable win if they conflict?
            elsif (audit[key][:state] == :disabled)
              puts "Warning: For rule #{rule_def.key}, parameter (#{key}) was previously disabled in rule #{audit[key][:rule].key}; " \
                "parameter cannot be forced.\n"

            else
              normalized[key] = value
              audit[key] = {:value => value, :state => :forced_by, :rule => rule_def}

              if (audit[key][:state] == :specified and normalized[key] != value)
                puts "Warning: specified input for (#{key}) was overridden by forced value in rule #{rule_def.key}\n"
                # in template and line number? or whole stack trace
                # in strict mode this is an error
              end
            end
          end

          rule_scope.restricted.each do |key, value|
            # Skip any parameter in this rule that does not exist in the template.
            next if (not normalized.keys.include?(key))

            # Check for violations of restricted parameters.
            # Could be caused by defaulted or forced values in the rule even...

            # puts "Error" out of range

            # Doesn't actually change the audit
          end

          rule_scope.enabled.each do |key|
            # Skip any parameter in this rule that does not exist in the template.
            next if (not normalized.keys.include?(key))

            # How will this work?
            # Enabled just allows user to specify (or default) a value--when previous was disabled
            # Probably this has to be one of the first things to call...
            # Needs to check :enabled attribute on Parameter

            # normalized[key] = ???
            # audit[key] = {:value => ???, :state => :enabled, :rule => rule_def}
          end

          rule_scope.disabled.each do |key|
            # Skip any parameter in this rule that does not exist in the template.
            next if (not normalized.keys.include?(key))

            # Disable parameter unless forced by previous rule.
            if (audit[key].nil?)
              puts "#{key} was nil in #{@path}"
              next
            end

            if (audit[key][:state] == :forced_by)
              puts "Warning: For rule #{rule_def.key}, parameter (#{key}) was previously forced in rule #{audit[key][:rule].key}; " \
                "parameter cannot be disabled.\n"

            else
              normalized[key] = nil
              audit[key] = {:value => nil, :state => :disabled_by, :rule => rule_def}

              if (audit[key][:state] == :specified)
                puts "Warning: specified input for (#{key}) was ignored because parameter was disabled in rule #{rule_def.key}\n"
                # in template and line number? or whole stack trace
                # in strict mode this is an error
              end
            end
          end

        end
      end  # fix indent

        # Check for undefined parameters
        inputs.each do |key, value|
          if (not parameters.any? {|param| param.variable_name == key.to_s })

            #text << annotate("PARAMETER ERROR:  Undefined parameter specified (#{key}); parameter ignored.")
            puts "Error: Undefined parameter specified (#{key}); parameter ignored.\n"
            #puts "Template referenced from: #{@path.inspect}"
            # NOPUB line number would be nice
          end
        end

        # Returns a detailed structure: ParameterStatus
        # Order should match the definition order.
        # norms = {
        #   :key => "p1", :value => "value", :status => DEFAULTED,  # OVERIDDEN, RESTRICTED, DISABLED
        #   :key => "p2", :value => 42, :status => FORCED,  # MISSING/REQUIRED
        #}

        state_data = {
          :defaulted => {:char => " ", :desc => "defaulted by interface"},
          :hidden => {:char => "\u00a4", :desc => "hidden by interface"},  # ¤
          :specified => {:char => "\u2192", :desc => "specified by input"},  # →
          :missing => {:char => "\u00d8", :desc => "missing"},  # Ø
          :forced_by => {:char => "\u25fc", :desc => "forced by rule"},  # ◼
          :defaulted_by => {:char => "\u2022", :desc => "defaulted by rule"},  # •
          :enabled_by => {:char => "\u2713", :desc => "enabled by rule"}, # ✓
          :disabled_by => {:char => "\u00d7", :desc => "disabled by rule"},  # ×
          :hidden_by => {:char => "\u00a4", :desc => "hidden by rule"},  # ¤
        }

        strings = []
        audit.each do |key, value|
          row = audit[key]
# NOPUB Not sure about this
          if (row[:value].kind_of?(Units::Quantity))
            display_value = row[:value].format
          else
            display_value = row[:value].inspect
          end

          rule_name = row[:rule] ? " '#{row[:rule].key}'" : ""
          strings << "#{state_data[row[:state]][:char]} " \
            "#{key} = #{display_value} " \
            "(#{state_data[row[:state]][:desc]}#{rule_name})"
        end
        audit_string = strings.join("\n")  # Avoid last newline because of annotate

        return([normalized, audit_string])
      end

# NOPUB use a block for callback notifications of errors, warnings, progress, etc.
# NOPUB
# parameters => Parameter definitions => [<Parameter>, <Parameter>, ...]
# inputs => Hash of key-value data => [:param1 => value1, :param2 => value2, ...]
# values => Array of values; consistent with Hash method: hash.values => [...]
      def compose(options = Hash.new)
        inputs = options[:inputs] || {}
        inputs, audit_string = normalize(inputs)
        options[:inputs] = inputs


        template_scope = TemplateScope.new(self, options)
        template_scope.annotate("BEGIN TEMPLATE #{@path.inspect}")

        if (not audit_string.empty?)
          template_scope.annotate(audit_string)
        end

          begin
  #puts "$VERBOSE=#{$VERBOSE.inspect}"
            # This somewhat increases warnings that are reported (default seems to `false` or level 1).
            # However, this does not show certain warnings that only occur during parsing
            # e.g., unused variables.
            #   `if (x = 4)` is always a good one to generate a warning: "= in conditional"

# Temporarily disable $VERBOSE because it was resulting in confusing warning:
# "warning: loading in progress, circular require considered harmful"
# only happens when multi-threading and two files are required at the same time
# NOTE: This _might_ not happen anymore because Templates are compiled safely using a Mutex thread lock...?

#            _verbose = $VERBOSE
#            $VERBOSE = true
            # Does this need to go before ERB.new? Or just before erb.result?

            _stderr = $stderr
            $stderr = StringIO.new  # Capture any warnings written to stderr during compile/eval

            template_scope.local_binding.eval(@target, @path, @line_offset)

# NOPUB this is cool! could be used to parse for unused parameters/variables.
#   Or looking like best way is to call `ruby -wc src.rb`
#   Can possibly open a pipe (Open3) to `ruby -wc -e` and "puts" the source string directly to Ruby
#   without writing a file.

            #puts erb.src
            #$erb_src = erb.src

# NOPUB can warnings (from $VERBOSE) be rescued or collected somehow too?
#   probably need to reassign $stderr
#   https://stackoverflow.com/questions/12761995/capturing-warning-messages/32941696#32941696

            # probably swap back _stderr first
#            puts "stderr captured: #{$stderr.string}"  # This totally works!
            # Now can iterate over each line and generate a warning.

          rescue NoMemoryError => exception  #ScriptError, StandardError, SecurityError => exception
            output = Modelkit.parse_exception(exception, @content)
            output = "Error: Ruby exception in template #{@path.inspect}\n#{output}"
# NOPUB awkward; there's a new line hidden in output returned from parse_exception
            #if (@caller)
              #output << "call_chain=#{@call_chain}"
            #end
            new_text = annotate(output)

  # NOPUB all puts should go away inside this class; happens at CLI level
            puts output  # Echo error to console (or log file)

  # Needs to write out the caller backtrace of _templates_ !

            # Ideally we would raise a new fatal error here that terminates Modelkit but still finishes writing the output file.
            # Calling 'exit' at least stops the program from continuing and overwriting the initial exception.
            exit

          rescue NoMemoryError => exception  #SystemExit => exception
            # Still need to parse to get line number
            output = Modelkit.parse_exception(exception, @content)
            output = "TEMPLATE EXIT: user exit in template #{@path.inspect}\n#{output}"
            new_text = annotate(output)
            puts output  # Echo error to console (or log file)

          ensure
            $stderr = _stderr
#            $VERBOSE = _verbose
          end

# NOPUB raise(exception [, string [, array]])
#   could re-raise as a TemplateError
#   These could be filtered and written to output file.

# NOPUB  does this happen here or on `insert`  ?
#  don't add spaces for indent when it's a blank line -- easy fix
#  makes it so that trailing spaces are not cut on resave
          # if (@annotate and not @indent.empty?)
          #   new_text = (new_text.lines.collect { |line| @indent + line }).join
          # end

# NOPUB There are 2 scopes now: interface and template. "scope_eval" is now ambiguous.
      # Evaluate some Ruby code in the protected scope of the template.
      # 'eval' is weird;  better:  protected_eval, or something else
      # def scope_eval(string)
      #   return(eval(string, @template_scope.local_binding))
      # end
        template_scope.annotate("END TEMPLATE #{@path.inspect}")

        return(template_scope)
      end


      # Resolve a path according to the search directories for this template.
      def resolve_path(path)
        return(@path_search.resolve(path))
      end

# NOPUB dump the content...and header? reformat to canonical string?
#   probably dump the original string; will ensure roundtripping if needed
      def to_s
        return(@source)
      end

      def inspect
        return("#<#{self.class} path=#{@path.inspect}>")
      end

    end

  end
end
