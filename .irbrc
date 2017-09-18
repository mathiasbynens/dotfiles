require 'irb/completion'
ARGV.concat [ "--readline", "--prompt-mode", "simple" ]

HISTFILE = "~/.irb.hist"
MAXHISTSIZE = 100
   
  begin
    if defined? Readline::HISTORY
      histfile = File::expand_path( HISTFILE )
      if File::exists?( histfile )
        lines = IO::readlines( histfile ).collect {|line| line.chomp}
        puts "Read %d saved history commands from %s." %
          [ lines.size, histfile ] if $DEBUG || $VERBOSE
        Readline::HISTORY.push( *lines )
      else
        puts "History file '%s' was empty or non-existant." %
          histfile if $DEBUG || $VERBOSE
      end
  
      Kernel::at_exit {
        lines = Readline::HISTORY.to_a.reverse.uniq.reverse
        lines = lines[ -MAXHISTSIZE, MAXHISTSIZE ] if lines.size > MAXHISTSIZE
        $stderr.puts "Saving %d history lines to %s." %

          [ lines.length, histfile ] if $VERBOSE || $DEBUG
        File::open( histfile, File::WRONLY|File::CREAT|File::TRUNC ) {|ofh|
          lines.each {|line| ofh.puts line }
        }
      }
    end
  end
  
  
#  def define_model_find_shortcuts
#    model_files = Dir.glob("app/models/**/*.rb")
#n    table_names = model_files.map { |f| File.basename(f).split('.')[0..-2].join }
#    table_names.each do |table_name|
#      Object.instance_eval do
#n        define_method(table_name) do |*args|
#          table_name.camelize.constantize.send(:find, *args)
#        end
#      end
#    end
#  end

  # Called when the irb session is ready, after
  # the Rails goodies used above have been loaded.
#  IRB.conf[:IRB_RC] = Proc.new { define_model_find_shortcuts }
  