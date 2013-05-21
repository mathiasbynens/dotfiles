#!/usr/bin/env bash
cd "$(dirname "${BASH_SOURCE}")"

CURRENT_BOOTSTRAP=$(md5sum $BASH_SOURCE)
git pull origin master
NEW_BOOTSTRAP=$(md5sum $BASH_SOURCE)

if [ ! "$CURRENT_BOOTSTRAP" = "$NEW_BOOTSTRAP" ]; then
    echo "$BASH_SOURCE has changed. Please run the script again."
    exit 0
fi


function doIt() {
	rsync --exclude ".git/" --exclude ".DS_Store" --exclude "bootstrap.sh" \
		--exclude "README.md" --exclude "LICENSE-GPL.txt" \
		--exclude "LICENSE-MIT.txt" -av --no-perms . ~
}
if [ "$1" == "--force" -o "$1" == "-f" ]; then
	doIt
else
	read -p "This may overwrite existing files in your home directory. Are you sure? (y/n) " -n 1
	echo
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		doIt
	fi
fi
unset doIt
source ~/.bash_profile
