#!/usr/bin/env bash

if [ "$1" == "-h" ] ; then
	echo "Usage: init"
	echo "Options: "
	echo "-h  Show this message"
	echo "-a  Install all the options (gem, pip, npm, nvm, oh-my-zsh, oh-my-fish)"
	echo "-g  Install Gemfile"
	echo "-n  Install node apps & nvm"
	echo "-p  Install python requirements"
	return
elif [ "$#" -gt 1 ]; then
	echo "Too many parameters"
	return
fi

function gem() {
  echo "Installing gems"
  bundle install
}

function pip() {
  echo "Installing pip requirements"
  pip install -r requirements.txt
}

function npm() {
  echo "Installing npm apps"
  npm install -g $(cat npmfile)
}

function nvm() {
  echo "Installing nvm"
  curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.34.0/install.sh | bash
}

function omz() {
  echo "Installing oh-my-zsh"
  sh -c "$(curl -fsSL https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh)"
}

function omf() {
  echo "Installing oh-my-fish"
  curl -L https://github.com/oh-my-fish/oh-my-fish/raw/master/bin/install | fish
}

function mac-cli() {
  echo "Installing mac-cli"
  sh -c "$(curl -fsSL https://raw.githubusercontent.com/guarinogabriel/mac-cli/master/mac-cli/tools/install)"
}

if [ "$1" == "-a" ]; then
	gem
  pip
  npm
  omz
  omf
  mac-cli
elif [[ "$1" == "-g" ]]; then
	gem
elif [[ "$1" == "-n" ]]; then
	npm
  nvm
elif [[ "$1" == "-p" ]]; then
	pip
elif [[ "$1" == "-o" ]]; then
	omz
  omf
  mac-cli
else
  gem
  pip
  npm
	echo "For specific categories, run again with appropriate flags (-h for more info)"
fi;
