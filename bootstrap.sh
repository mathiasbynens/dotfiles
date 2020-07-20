#!/usr/bin/env zsh

place="$PWD"

if [ -n "$ZSH_VERSION" ]; then
	# assume Zsh
	cd "$(dirname "${(%):-%x}")"
elif [ -n "$BASH_VERSION" ]; then
	# assume Bash
	cd "$(dirname "${BASH_SOURCE}")";
else
   echo "oops"# assume something else
fi

echo $PWD
# git pull origin master;

function doIt() {
	/usr/local/bin/rsync \
		--exclude ".git/" \
		--exclude ".DS_Store" \
		--exclude ".osx" \
		--exclude "bootstrap.sh" \
		--exclude "README.md" \
		--exclude "LICENSE-MIT.txt" \
		-avh --no-perms . ~;
	source ~/.zprofile ;
}

if [[ ( $# > 0 ) && ( "$1" = "--force" || "$1" = "-f" ) ]]; then
	doIt;
else
	read -qs "REPLY?*** Overwrite existing files in your home directory? (y/N) "
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		doIt;
	else
		echo "Aborting."
	fi;
fi;
unset doIt;
cd $place
