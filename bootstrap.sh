#!/usr/bin/env bash

cd "$(dirname "${BASH_SOURCE}")";

echo "";
echo "$(tput setaf 6)Checking for updates in repo..$(tput setaf 7)"
git pull origin master;


# install xcode
echo "";
echo "$(tput setaf 6)Checking xcode cli$(tput setaf 7)"
if type xcode-select >&- && xpath=$( xcode-select --print-path ) && test -d "${xpath}" && test -x "${xpath}"
   then
	echo "xcode cli already installed;"
else
	echo "Installing xcode cli"
	xcode-select --install
	echo "Accepting xcode terms"
	sudo xcodebuild -license accept
fi


# main menu
function menu() {
	echo "";
	echo "$(tput bold)What do you want to do?$(tput sgr0)";
	read -p " 1. Install dotfiles `
		echo $'\n '`2. Install apps `
		echo $'\n '`3. Set preferences`
		echo $'\n '`> ";

	if [[ $REPLY =~ ^[1]$ ]]; then
		installDotfilesMenu;
	fi;

	if [[ $REPLY =~ ^[2]$ ]]; then
		installAppsMenu;
	fi;

	if [[ $REPLY =~ ^[3]$ ]]; then
		setPreferencesMenu;
	fi;
}

# menu for intalling dotfiles
function installDotfilesMenu() {
	echo "";
	read -p "$(tput bold)Set dotfiles? Caution, this removes old dotfiles, proceed? (y/n)$(tput sgr0) ";

	if [[ $REPLY =~ ^[Yy]$ ]]; then
		installDotfiles
	fi;

	menu;
}

# copies dotfiles into ~/
function installDotfiles() {

	rsync --exclude ".git/" \
		--exclude ".DS_Store" \
		--exclude ".osx" \
		--exclude "bootstrap.sh" \
		--exclude "README.md" \
		--exclude "LICENSE-MIT.txt" \
		-avh --no-perms . ~;

		echo "$(tput setaf 2)Dotfiles installed$(tput setaf 7)"
}

# installs homebrew apps
function installHomebrewApps() {

	read -p "$(tput bold)Please login into App Store, proceed? (y/n)$(tput sgr0) ";

	if [[ $REPLY =~ ^[Yy]$ ]]; then
		sudo -v

		cd ~
		./brew.sh
	fi;
}

# menu for intalling apps
function installAppsMenu() {
	echo "";
	echo "$(tput bold)What do you want to install?$(tput sgr0)";
	read -p " 1. homebrew apps `
		echo $'\n '`2. oh my zsh  `
		echo $'\n '`3. show licenses`
		echo $'\n '`9. all`
		echo $'\n '`0. back`
		echo $'\n '`> ";

	if [[ $REPLY =~ ^[1]$ ]]; then
		echo ""

		installHomebrewApps;

		installAppsMenu
	fi;

	if [[ $REPLY =~ ^[2]$ ]]; then
		echo ""
		echo "$(tput setaf 6)Installing oh my zsh$(tput setaf 7)"
		echo ""

		installOhMyZsh;
		installAppsMenu
	fi;

	if [[ $REPLY =~ ^[3]$ ]]; then
		echo ""
		echo "$(tput setaf 6)Opening finder with licenses$(tput setaf 7)"

		open ~/Dropbox/.serials/

		installAppsMenu
	fi;

	if [[ $REPLY =~ ^[9]$ ]]; then
		echo ""
		echo "$(tput setaf 6)Installing all$(tput setaf 7)"
		echo ""

		installHomebrewApps
		installOhMyZsh

		installAppsMenu
	fi;

	if [[ $REPLY =~ ^[0]$ ]]; then
		menu
	fi;
}

function installOhMyZsh() {
	# Ask for the administrator password upfront
	sudo -v

	# Install shell
	sh -c "$(curl -fsSL https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh)"

	# set ohmyzsh as default shell
	chsh -s $(which zsh)

	echo "$(tput setaf 2)Oh My ZSH installed$(tput setaf 7)"
}

# menu for setting preferences
function setPreferencesMenu() {
	echo "";
	echo "$(tput bold)What do you want to set?$(tput sgr0)";
	read -p " 1. macos `
		echo $'\n '`2. folders  `
		echo $'\n '`3. ssh *dropbox`
		echo $'\n '`4. git *dropbox`
		echo $'\n '`5. sublime-text`
		echo $'\n '`6. oh my zsh`
		echo $'\n '`9. all`
		echo $'\n '`0. back`
		echo $'\n '`> ";

	if [[ $REPLY =~ ^[1]$ ]]; then
		echo ""
		echo "Set OSX"

		cd ~
		~/.macos

		setPreferencesMenu
	fi;

	if [[ $REPLY =~ ^[2]$ ]]; then
		echo ""
		echo "Set folders"

		mkdir ~/Development

		setPreferencesMenu
	fi;

	if [[ $REPLY =~ ^[3]$ ]]; then
		cd ~/Dropbox/.configs/ssh/
		chmod +x setup.sh
		./setup.sh

		setPreferencesMenu
	fi;

	if [[ $REPLY =~ ^[4]$ ]]; then
		cd ~/Dropbox/.configs/git/
		chmod +x setup.sh
		./setup.sh

		setPreferencesMenu
	fi;

	if [[ $REPLY =~ ^[5]$ ]]; then
		echo ""
		echo "Set sublime"

		cd ~/.sublime
		./setup.sh

		setPreferencesMenu
	fi;

	if [[ $REPLY =~ ^[6]$ ]]; then
		echo ""
		echo "Set ohmyzsh"

		# install oh my zsh package manager
		curl -L git.io/antigen > antigen.zsh
		source antigen.zsh

		# BUG

		#plugins
		antigen bundle djui/alias-tips
		antigen bundle kennethreitz/autoenv
		antigen bundle walesmd/caniuse.plugin.zsh
		antigen bundle zsh-users/zsh-autosuggestions
		antigen bundle zsh-users/zsh-syntax-highlighting

		# iterm2 fonts
		brew tap caskroom/fonts
		brew cask install font-droid-sans-mono
		brew cask install font-droid-sans-mono-for-powerline
		brew cask install font-awesome-terminal-fonts

		# iterm2 colors
		cd ~/Downloads
		wget https://raw.githubusercontent.com/JamieMason/All-iTerm-Colors/master/itermcolors/3024%20Night.itermcolors

		echo 'change iterm font into: "Droid Sans Mono for Powerline Nerd Font Complete // 14px"'
		echo "import 3024 Night.itermcolors @ preferences > appearance -> colors"

		setPreferencesMenu
	fi;

	if [[ $REPLY =~ ^[9]$ ]]; then
		echo ""
		echo "Set all"
		setPreferencesMenu
	fi;

	if [[ $REPLY =~ ^[0]$ ]]; then
		menu
	fi;
}

menu

unset installDotFiles;
