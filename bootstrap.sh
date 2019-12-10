#!/usr/bin/env zsh

place="$PWD"

if [ -n "$ZSH_VERSION" ]; then
	# assume Zsh
	cd "$(dirname "${(%):-%x}")"
elif [ -n "$BASH_VERSION" ]; then
	# assume Bash
	cd "$(dirname "${BASH_SOURCE}")";
else
   # asume something else
fi

git pull origin master;

function doIt() {
	rsync --dry-run \
		--exclude ".git/" \
		--exclude ".DS_Store" \
		--exclude ".osx" \
		--exclude "bootstrap.sh" \
		--exclude "README.md" \
		--exclude "LICENSE-MIT.txt" \
		-avh --no-perms . ~;
	# source ~/.bash_profile;
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
cd $place
