#!/usr/bin/env bash

cd "$(dirname "${BASH_SOURCE}")";

git pull origin master;

function doIt() {
	rsync --exclude ".git/" \
		--exclude ".DS_Store" \
		--exclude ".osx" \
		--exclude "bootstrap.sh" \
		--exclude "README.md" \
		--exclude "LICENSE-MIT.txt" \
		-avh --no-perms . ~;

        echo 'source ~/virtualenvs/default/bin/activate' >> ~/.bash_profile
        echo "execute pathogen#infect()" >> ~/.vimrc

        cd ~/.vim/bundle
        git clone git://github.com/tpope/vim-sensible.git
        git clone https://github.com/scrooloose/nerdtree.git
        git clone https://github.com/Xuyuanp/nerdtree-git-plugin.git
        git clone https://github.com/tpope/vim-surround.git
        git clone https://github.com/scrooloose/syntastic.git
        git clone https://github.com/bling/vim-airline.git
        git clone https://github.com/valloric/youcompleteme.git
        git clone git://github.com/godlygeek/tabular.git
        cd -

        echo '" Start NERDTree when no file is passed to vim' >> ~/.vimrc
        echo autocmd StdinReadPre * let s:std_in=1 >> ~/.vimrc
        echo 'autocmd VimEnter * if argc() == 0 && !exists("s:std_in") | NERDTree | endif' >> ~/.vimrc

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

cd -
