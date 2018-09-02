#!/usr/bin/env bash

# ask password upfront
sudo -v

echo "Checking xcode cli"
if type xcode-select >&- && xpath=$( xcode-select --print-path ) && test -d "${xpath}" && test -x "${xpath}"
   then
    echo "xcode cli already installed;"
else
    echo "Installing xcode cli"
    xcode-select --install
    echo "Accepting xcode terms"
    sudo xcodebuild -license accept
fi

source ./packages/applications.sh
source ./packages/fonts.sh
source ./packages/npm.sh
source ./packages/utilities.sh
source ./packages/vim.sh
source ./packages/zsh.sh
