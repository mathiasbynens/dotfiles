#!/usr/bin/ruby

require 'fileutils'

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

class DotfilesInstaller


    # desc 'copy_confiles', 'Copies configuration files to the home directory'
    def copy_confiles

        pwd = `pwd`.chomp

        FileRsyncer.new("#{pwd}/.confiles", "~/").rsync_files

        puts    
        puts "Finished"

    end

    # desc "add_shellrc_data", "Adds initialization data in the shell rc file"
    def add_shellrc_data

        pwd = `pwd`.chomp
        shell_rcfile = `echo $SHELL`.chomp =~ /[zsh]/ ? "#{pwd}/.zshrc" : "#{pwd}/.bash_profile"

        puts "Adding the shell rc file: #{shell_rcfile}"

        FileRsyncer.new(shell_rcfile, "~/").rsync_files
        puts
        puts "Finished"
    end
    
    # desc 'copy_dotfiles', 'Copies dotfiles to the home directory and references it in the shell'
    def copy_dotfiles        
        FileRsyncer.new("dotfiles/", "~/").rsync_files

        puts
        puts "Finished"
    end

    # https://github.com/robbyrussell/oh-my-zsh
    # desc 'install_oh_my_zsh', 'Also installs oh my zsh'
    def install_oh_my_zsh

        # Clone the repository
        system 'git clone git://github.com/robbyrussell/oh-my-zsh.git ~/.oh-my-zsh'

        # Backup existing zshrc file
        FileUtils.cp('~/.zshrc','~/.zshrc.orig') if File.exists? '~/.zshrc'

        # Set zsh as system shell
        system 'chsh -s /bin/zsh'
    end

    # desc 'install_osx_defaults', 'Sets my personal OSX configuration defaults'
    def set_osx_defaults
        system './defaults/osx/init'
    end

    # desc 'install_homebrew', 'Installs homebrew and sets some optional repositories'
    def install_homebrew
        system './defaults/brew/init'
    end


    def install_fonts
        FileRsyncer.new('./fonts/', "#{ENV['HOME']}/Library/Fonts/").rsync_files
    end

    def install_themes
        FileRsyncer.new('./themes/', '~/.oh-my-zsh/themes').rsync_files
    end

end