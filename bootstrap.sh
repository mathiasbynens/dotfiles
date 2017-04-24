#!/usr/bin/env bash

cd "$(dirname "${BASH_SOURCE}")";

git pull origin master;

function doIt() {
	rsync --exclude ".git/" \
		--exclude ".DS_Store" \
		--exclude ".osx" \
		--exclude "bootstrap.sh" \
		--exclude "README.md" \
		--exclude "LICENSE-MIT.txt" \
		-avh --no-perms . ~;
	source ~/.zshrc;

	echo "Done!"
}

# install xcode
xcode-select --install

#accept xcode terms
sudo xcodebuild -license accept

if [[ "$1" == "--force" || "$1" == "-f" ]]; then
	doIt;
else
	read -p "This may overwrite existing files in your home directory. Are you sure? (y/n) ";
	echo "";
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		doIt;
	fi;

	read -p "Make desired folders? (y/n) ";
	echo "";
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		mkdir ~/Development
	fi;

	read -p "Install apps? (y/n) ";
	echo "";
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		cd ~
		./brew.sh
	fi;


	read -p "Setup OSX settings? (y/n) ";
	echo "";
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		cd ~
		~/.macos
	fi;

	read -p "Setup sublime 3? (y/n) ";
	echo "";
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		cd ~/.sublime
		./setup.sh
	fi;

	read -p "Install oh-my-zsh? (y/n) ";
	echo "";
	if [[ $REPLY =~ ^[Yy]$ ]]; then

		# Ask for the administrator password upfront
		sudo -v

		# Install shell
		sh -c "$(curl -fsSL https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh)"

		# set ohmyzsh as default shell
		chsh -s $(which zsh)

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
	fi;
fi;

unset doIt;
