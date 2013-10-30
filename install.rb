#!/usr/bin/ruby

require './dotfiles_installer'

installer = DotfilesInstaller.new
#installer..install_homebrew
#installer..install_oh_my_zsh
installer.copy_confiles
installer.copy_dotfiles
#installer..add_shellrc_data
installer.install_fonts
installer.install_themes
#installer..set_osx_defaults