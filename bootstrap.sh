#!/usr/bin/env bash

os=$(uname -s)
cd "$(dirname "${BASH_SOURCE}")";

git pull origin master;

if [[ ! -d ~/.vim/bundle/Vundle.vim ]]; then
    echo "Vundle not found, installing..."
    git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim
fi

if [[ $os =~ CYGWIN* ]]; then
    echo "-------------------------------"
	echo "      Bootstrapping Babun      "
	echo "-------------------------------"
	
	# rsync the relevant babun files 
	# Exclude the bash_profile and possibly others...
	#echo "babun bootstrapping partially completed.  Please run babun/babun-post-install.sh"
	rsync --exclude ".git/" --exclude "link/" --exclude "babun/" --exclude "bin/" --exclude "dircolors-solarized/" -exclude "bootstrap.sh" \
		--exclude "README.md" --exclude "LICENSE-MIT.txt" -avh --no-perms . ~;

fi


function doIt() {
	rsync --exclude ".git/" --exclude "link/" --exclude "babun/" --exclude "dircolors-solarized/" --exclude {"bootstrap.sh","bootstrap-babun.sh"} --exclude "extra/" \
		--exclude "README.md" --exclude "LICENSE-MIT.txt" -avh --no-perms . ~;

	curl https://raw.githubusercontent.com/git/git/master/contrib/completion/git-completion.bash -o ~/.git-completion.bash
	source ~/.bash_profile;
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