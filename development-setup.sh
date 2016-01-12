#!/usr/bin/env bash

# Install command-line tools using Homebrew.

# Ask for the administrator password upfront.
sudo -v

# Keep-alive: update existing `sudo` time stamp until the script has finished.
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &

# Make sure we’re using the latest Homebrew.
brew update

# Upgrade any already-installed formulae.
brew upgrade --all

# Development environment
brew install node
gem install scss_lint
npm install -g gulp
npm install -g eslint

# Frontend development software
brew cask install atom
brew cask install google-chrome
brew cask install google-drive
brew cask install java
brew install maven
brew cask install sourcetree

# Personal
brew cask install spotify
brew cask install cyberduck

# Remove outdated versions from the cellar.
brew cleanup
