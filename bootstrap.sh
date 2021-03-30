#!/bin/sh
set -eu # for safety


cd "$(dirname "${BASH_SOURCE}")";

git pull origin main;

doIt() {
	rsync --exclude ".git/" \
		--exclude ".DS_Store" \
		--exclude ".osx" \
		--exclude "bootstrap.sh" \
		--exclude "README.md" \
		--exclude "LICENSE-MIT.txt" \
		-avh --no-perms . "$HOME";
	. "$HOME"/.bash_profile;
}

case "$1" in ("--force"|"-f")
	doIt;
;;(*)
	echo "This may overwrite existing files in your home directory. Are you sure? (y/n) " 2>&1;
	REPLY=$(stty raw; dd bs=1 count=1 2>/dev/null; stty -raw)
	echo "";
	case $REPLY in ([Yy])
		doIt;
	esac;
esac;
unset -f doIt;
