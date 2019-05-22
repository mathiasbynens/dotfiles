#!/usr/bin/env bash

cd "$(dirname "${BASH_SOURCE}")"/..;

git pull origin master;

function doIt() {
    mkdir -p ~/.config
	rsync -avh --no-perms .config/ ~/.config
}

if ! [ -x "$(command -v fish)" ]; then
	read -p "Install fish? (y/n) " -n 1;
	echo "";
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		echo 'Installing fish...' >&2
        brew install fish
		echo /usr/local/bin/fish | sudo tee -a /etc/shells
    else
        exit 1
	fi;
fi

### Check if a directory does not exist ###
if [ ! -d ~/.local/share/omf ]; then
	read -p "Install omf? (y/n) " -n 1;
	echo "";
	if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
		echo 'Installing omf...' >&2
        curl -L https://github.com/oh-my-fish/oh-my-fish/raw/master/bin/install > /tmp/omf_install
        chmod 755 /tmp/omf_install
        fish -c "source /tmp/omf_install --noninteractive --yes"
    else
        exit 1
	fi;
fi

if ! [ -x "$(command -v fzf)" ]; then
	read -p "Install fzf? (y/n) " -n 1;
	echo "";
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		echo 'Installing fzf...' >&2
        brew install fzf
    else
        exit 1
	fi;
fi

echo ""
echo ""

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

fish -c "$(brew --prefix)/opt/fzf/install --all"

fish -c "if not type -q fisher; curl https://git.io/fisher --create-dirs -sLo ~/.config/fish/functions/fisher.fish; end"

fish -c "if not type -q z; fisher add jethrokuan/z; end"
