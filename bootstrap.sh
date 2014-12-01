#!/usr/bin/env bash

cd "$(dirname "${BASH_SOURCE}")";

# git pull origin master;

RSYNC_EXCLUDE_LIST=('.git/' '.DS_Store' 'bootstrap.sh' 'README.md' 'init' 'brew.sh' 'LICENSE-MIT.txt')
[ -f ~/.gitconfig ] && RSYNC_EXCLUDE_LIST+=('.gitconfig')

function doIt() {
    exclude_args=""
    for file in ${RSYNC_EXCLUDE_LIST[@]};do
        exclude_args="--exclude $file $exclude_args";
    done
	rsync $exclude_args -avh --no-perms . ~;
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
