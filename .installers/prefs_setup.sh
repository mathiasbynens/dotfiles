#!/usr/bin/env bash

cd "$(dirname "${BASH_SOURCE}")"/..;

** setup powerline fonts **
clone
git clone https://github.com/powerline/fonts.git --depth=1
# install
cd fonts
./install.sh
# clean-up a bit
cd ..
rm -rf fonts

# ** configure iterm2 settings **
cp -r .prefs/com.googlecode.iterm2.plist ~/Library/Preferences/com.googlecode.iterm2.plist

# ** configure vscode settings **
cp -r .prefs/vscode/settings.json ~/Library/Application\ Support/Code/User/settings.json

