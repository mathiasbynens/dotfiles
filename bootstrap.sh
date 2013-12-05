#!/usr/bin/env bash
OPTIND=1

cd "$(dirname "${BASH_SOURCE}")"
git pull origin master
function doIt() {
	rsync --exclude ".git/" --exclude ".DS_Store" --exclude "bootstrap.sh" \
		--exclude "README.md" --exclude "LICENSE-MIT.txt" -av --no-perms . ~
}
function linkIt() {
	FILES=$(find . -type f -maxdepth 1 -name ".*" -not -name .DS_Store -not -name .git -not -name .osx | sed -e 's|//|/|' | sed -e 's|./.|.|')
  	for file in $FILES; do 
		ln -sf $(dirname "${BASH_SOURCE}")/${file} ~/${file}
	done	
}

while getopts "fl" opt; do
	case "$opt" in
		f)
			FORCE=1
			;;
		l)
			LINK=1
			;;
	esac
done

if [ "$FORCE" == "1" ]; then
	if [ "$LINK" == "1" ]; then
		linkIt
	else
		doIt
	fi
else
	read -p "This may overwrite existing files in your home directory. Are you sure? (y/n) " -n 1
	echo
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		if [ "$LINK" == "1" ]; then
			linkIt
		else
			doIt
		fi
	fi
fi
source ~/.bash_profile
unset doIt
