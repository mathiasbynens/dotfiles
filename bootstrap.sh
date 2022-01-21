#!/usr/bin/env zsh

cd "$(dirname "${BASH_SOURCE}")";

git pull origin master;

function doIt() {
	cp -rf ./dotfiles/ ~;

	source ./install.sh;

	if [ -z "$GIT_NAME" ]; then
		read -p "Enter your Git Name ";
		echo "";
		GIT_NAME=$REPLY
	fi
	if [ -z "$GIT_EMAIL" ]; then
		read -p "Enter your Git email address ";
		echo "";
		GIT_EMAIL=$REPLY
	fi
	git config --global user.name "$GIT_NAME"
	git config --global user.email $GIT_EMAIL

	source ~/.zshrc
	echo "Finished installing"
}

doIt;

unset doIt;
