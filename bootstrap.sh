#!/usr/bin/env bash

cd "$(dirname "${BASH_SOURCE}")";

rsync --exclude ".git/" \
	--exclude ".DS_Store" \
	--exclude ".osx" \
	--exclude "bootstrap.sh" \
	--exclude "README.md" \
	--exclude "LICENSE-MIT.txt" \
	-avh --no-perms . ~;

curl https://raw.githubusercontent.com/oh-my-fish/oh-my-fish/master/bin/install > install;
fish install --noninteractive && rm -f install

fish -C "omf install fzf https://github.com/jhillyerd/plugin-git"
