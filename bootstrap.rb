#!/usr/bin/ruby

class FileRsyncer
    @@rsync_args ="-av"
    @@rsync_test_args = "--dry-run"
    @@rsync_cmd  ="rsync"

    def initialize source_path, dest_path
        @source_path = source_path
        @dest_path = dest_path
    end

    def test_rsync_files
        puts '[Test Mode]'
        rsync_files [@@rsync_args, @@rsync_test_args].join(' ')
    end

    def rsync_files args=nil

        rsync_args = args || @@rsync_args
        cmd = "#{@@rsync_cmd} #{rsync_args} #{@source_path} #{@dest_path}"

        puts "Command: [#{cmd}]"
        puts "List of operations to be performed:"
        puts `#{cmd}`
    end


end


fileSyncer = FileRsyncer.new "dotfiles", "~/.dotfiles"



if (ARGV.include?('--force') || ARGV.include?('-f'))
    puts "Force option found. Copying files"
    fileSyncer.rsync_files
    exit 0
else
    fileSyncer.test_rsync_files
    puts
    puts "This will apply the above operations in the directory #{ENV['HOME']}/.dotfiles"
    puts "Are you sure? (y/n) "
    if (gets.chomp =~ /^[Yy]$/)
        fileSyncer.rsync_files
        exit 0
    else
        exit 1
    end
end
