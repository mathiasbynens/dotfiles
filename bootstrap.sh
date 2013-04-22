#!/bin/bash
cd "$(dirname "${BASH_SOURCE}")"
git pull origin master
function update() {
	files=$(find .* -type f -maxdepth 0)
	for filename in $files 
	do
		rm -f ~/"$filename"
		ln -s "$(pwd)/$filename" ~
	done
}

if [ "$1" == "--force" -o "$1" == "-f" ]; then
	update
else
	read -p "This may overwrite existing files in your home directory. Are you sure? (y/n) " -n 1
	echo
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		update
	fi
fi

unset doIt
