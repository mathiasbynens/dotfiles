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


if [[ "$1" == "--force" || "$1" == "-f" ]]; then
	doIt;
else
	read -q "REPLY?This may overwrite existing files in your home directory. Are you sure? (y/n) ";
	echo "";
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		doIt;
	fi;

	read -q "REPLY?Make desired folders? (y/n) ";
	echo "";
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		mkdir ~/Development
	fi;

	read -q "REPLY?Install apps? (y/n) ";
	echo "";
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		cd ~
		./brew.sh
	fi;

	read -q "REPLY?Set userdata? (y/n) ";
	echo "";
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		cd ~
		./private.sh
	fi;

	read -q "REPLY?Install oh-my-zsh? (y/n) ";
	echo "";
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		sh -c "$(curl -fsSL https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh)"
	fi;
fi;

unset doIt;