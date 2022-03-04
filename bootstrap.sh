#!/usr/bin/env zsh

place="$PWD"

if [ -n "$ZSH_VERSION" ]; then
	# assume Zsh
	src_dir=$(dirname "${(%):-%x}")
elif [ -n "$BASH_VERSION" ]; then
	# assume Bash
	src_dir=$(dirname "${BASH_SOURCE}")
else
   echo "oops"# assume something else
   exit 1
fi

echo "${place} > ${src_dir}" 
# git pull origin master;

function doIt() {
	cd "${src_dir}"
	/usr/local/bin/rsync \
		--exclude ".git/" \
		--exclude ".idea/" \
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

cd $place
echo "${src_dir} > ${place}" 

unset src_dir;
unset doIt;