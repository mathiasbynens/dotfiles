#!/bin/bash
cd "$(dirname "$0")"
git pull
function doIt() {
	rsync --exclude ".git/" --exclude ".DS_Store" --exclude "bootstrap.sh" --exclude "README.md" -av . ~
	if [ -f ~/.extra ]; then
		echo "These changes have been made in the .extra.dist file, please handle these manually"
    	diff .extra.dist ~/.extra
	else
	    mv ~/.extra.dist ~/.extra
	fi
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

# git config

#make "ci" alias for "commit"
git config --global alias.ci commit
#make "co" alias for checkout
git config --global alias.co checkout
#make "br" alias for branch
git config --global alias.br branch
#make "st" alias for status
git config --global alias.st status

# config name and mail
git config --global user.name "Bruno Germano"
git config --global user.email bruno.germano@gmail.com

# colorize git
git config --global color.branch auto
git config --global color.diff auto
git config --global color.interactive auto
git config --global color.status auto

source ~/.bash_profile