require 'rake'
require 'date'
require 'yaml'

task :default do
    Rake::Task['symlink_dotfiles'].invoke
end

task :symlink_dotfiles do
    # inspoired heavily from https://github.com/henrik/dotfiles/blob/master/Rakefile and https://github.com/ryanb/dotfiles/blob/master/Rakefile
    Dir["./.*"].each do |file|
      # full path to file
      source = File.join(Dir.pwd, file)
      # just the file name
      basename = File.basename(file)
      puts "Symlinking #{basename}"
      # where we want it to be
      destination = File.expand_path("~/test/.#{basename}")

      conditionally_symlink(source, destination)
    end
end

def conditionally_symlink(source, destination)
  source = File.expand_path(source)
  destination = File.expand_path(destination)
  if File.exist?(source)
    if File.symlink?(destination)
      symlink_to = File.readlink(destination)
      if symlink_to == source
        puts "  #{destination} already symlinked, nothing to do"
      else
        puts "  relinking #{destination} from #{symlink_to} to #{source}"
        FileUtils.rm(destination)
        FileUtils.ln_s(source, destination)
      end
    elsif File.exist?(destination)
      # tack on today's date in YYYYMMDD
      backup_location = "#{destination}.#{Date.today.strftime("%Y%m%d")}"
      puts "  #{destination} already exists. Backing up to #{backup_location}"
      FileUtils.mv(destination, backup_location)
      FileUtils.ln_s(source, destination)
    else
      puts "  creating symlink for #{destination}"
      FileUtils.ln_s(source, destination)
    end
  else
    puts "  #{destination} doesn't exist, cannot create symlink"
  end
end
