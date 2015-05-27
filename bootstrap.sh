#!/usr/bin/env bash

cd "$(dirname "${BASH_SOURCE}")";

git pull origin master;

function doIt() {
	ls -a | awk '!/^.$/ && !/^..$/        \
		&& !/^.git$/                      \
		&& !/^.DS_Store$/                 \
		&& !/^bootstrap.sh$/              \
		&& !/^README.md$/                 \
		&& !/^LICENSE-MIT.txt$/           \
		' | xargs -I {} sh -c '           \
			rm -rf ~/{} 2> /dev/null;
			ln -s $(pwd)/{} ~/
		'
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
