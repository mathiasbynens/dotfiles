#!/usr/bin/env bash

cd "$(dirname "${BASH_SOURCE}")";

git pull origin master;
git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim

function doIt() {
	rsync --exclude ".git/" --exclude "link/" --exclude "dircolors-solarized/" --exclude "extra-*" --exclude ".DS_Store" --exclude "bootstrap.sh" \
		--exclude "README.md" --exclude "LICENSE-MIT.txt" -avh --no-perms . ~;
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
