#!/usr/bin/env bash

os=$(uname -s)
cd "$(dirname "${BASH_SOURCE}")";

git pull origin master;

successfully() {
	$* || (echo "failed" 1>&2 && exit 1)
}

fancy_echo() {
	echo "$1"
}

update_babun(){
	fancy_echo "Updating babun"
	successfully pact update

	fancy_echo "Updating babun HOME"
	#successfully curl -k https://raw.githubusercontent.com/joshball/dot-files/master/files/babun-home/.zshrc -o ~/.zshrc
	# Need to rsync the necessary files from the babun folder over to the HOME directory
	#   vim config
	#   mintty.rc
	#   zshrc
	#   Anything else I'm missing...
	successfully ln -fs $USERPROFILE ~/home
	successfully rsync -azh ./babun/.minttyrc ./babun/.zshrc ~
	
	# Need to do something with ssh-agent and extra-babun
	# successfully rsync -azh ./babun/.extra-babun .ssh-agent ~
	successfully rsync -azh --exclude .git/ .aliases .inputrc .git* ~

	fancy_echo "Updating VIM Configuration"
	successfully rsync -azh --exclude=".vim/bundle/Vundle.vim" '.vim' '.vimrc' ~

	if [[ ! -d ~/powerline-fonts ]]; then
		fancy_echo "Retrieving powerline fonts"
		successfully git clone https://github.com/powerline/fonts.git ~/powerline-fonts
	fi

	echo "babun bootstrap complete!"
	echo "You will need to install the DejaVu Sans Mono for Powerline font from the ~/powerline-fonts directory"
}

function doIt() {
	if [[ ! -z $BABUN_HOME ]]; then
		echo "-------------------------------"
		echo "      Bootstrapping Babun      "
		echo "-------------------------------"
		update_babun
	else
		rsync --exclude ".git/" --exclude "link/" --exclude "babun/" --exclude "dircolors-solarized/" --exclude {"bootstrap.sh","bootstrap-babun.sh"} --exclude "extra/" \
			--exclude "README.md" --exclude "LICENSE-MIT.txt" -avh --no-perms . ~;
		source ~/.bash_profile;
	fi

	if [[ ! -d ~/.vim/bundle/Vundle.vim ]]; then
		echo "Vundle not found, installing..."
		git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim
	fi
}

if [ "$1" == "--force" -o "$1" == "-f" ]; then
	doIt;
else
	read -p "This may overwrite existing files in your home directory. Are you sure? (y/n) " -n 1;
	echo "";
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		doIt;
	fi;
fi;

unset doIt;

git submodule update --init