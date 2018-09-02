#!/usr/bin/env bash
source ./helpers.sh
source ./packages/brew.sh

header "Installing vim"

brew cask install vim --with-override-system-vi
brew cask install macvim
brew cask install neovim

echo "installing vim plugins"
# step 1 install, install Vim package manager
git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim

cd  ~/.vim/bundle/tern_for_vim/
npm install

cd ~/.vim/bundle/youcompleteme
./install.py

footer