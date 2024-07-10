#!/usr/bin/env bash

cd "$(dirname "${BASH_SOURCE}")";

git pull origin main;

function doIt() {
	rsync --exclude ".git/" \
		--exclude "setup/" \
  		--exclude "docs/" \
		--exclude ".DS_Store" \
		--exclude ".osx" \
		--exclude "bootstrap.sh" \
		--exclude "README.md" \
		--exclude "LICENSE-MIT.txt" \
		--exclude ".DS_Store" \
		--exclude ".github/" \
		--exclude ".travis.yml" \
		-avh --no-perms . ~;
  if [ -n "$ZSH_VERSION" ]; then
     source ~/.zshrc;
  elif [ -n "$BASH_VERSION" ]; then
     source ~/.bash_profile;
  else
     echo 'unknown shell'
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
