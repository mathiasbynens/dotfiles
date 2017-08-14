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
    if [[ "$workflag" -eq "1" ]]; then
        echo "Using .extra-work"
	    successfully cp ./babun/.extra-work ~/.extra
    else
	    successfully cp ./babun/.extra ~/
    fi
	
	successfully rsync -azh --exclude .git/ .aliases .inputrc .ssh-agent .git* ~

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
		rsync --exclude ".git/" --exclude "link/" --exclude "babun/" --exclude "dircolors-solarized/" --exclude {"bootstrap.sh"} --exclude "extra/" \
			--exclude "README.md" --exclude "LICENSE-MIT.txt" -avh --no-perms . ~;
		if [[ "$workflag" -eq "1" ]]; then
		    echo "Using .extra-work"
		    successfully cp .extra-work ~/.extra
		fi
		source ~/.bash_profile;
	fi

	if [[ ! -d ~/.vim/bundle/Vundle.vim ]]; then
		echo "Vundle not found, installing..."
		git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim
	fi
}

workflag=""
forceflag=""

while getopts "fwh" opt; do
  case $opt in
    f)
        echo "-f was triggered" >&2
        forceflag=1
        ;;
    w)
        echo "-w was triggered" >&2
        workflag=1
        ;;
	h)
		echo "Usage: bootstrap.sh [-h] [-w] [-f]"
		exit 1
		;;
    \?)
        echo "Invalid option" >&2
        exit 1
        ;;
    :)
        echo "Option -$OPTARG requires an argument." >&2
        exit 1
        ;;
  esac
done

if [[ $forceflag -eq 1 ]]; then
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
