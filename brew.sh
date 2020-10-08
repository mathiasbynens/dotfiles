#!/usr/bin/env bash

# Install command-line tools using Homebrew.

# Make sure we’re using the latest Homebrew.
brew update

# Upgrade any already-installed formulae.
brew upgrade

# Save Homebrew’s installed location.
BREW_PREFIX=$(brew --prefix)

# Install GNU core utilities (those that come with macOS are outdated).
# Don’t forget to add `$(brew --prefix coreutils)/libexec/gnubin` to `$PATH`.
brew install gnu-sed

brew install coreutils
brew install wget
brew install ripgrep
brew install bat
brew install jq
brew install fzf
brew install xmlsec1
brew install node
brew install tree
brew install starship

# Cask applications
brew cask install virtualbox
brew cask install spotify

# Docker
brew install docker
brew install docker-compose
brew install docker-machine

# Remove outdated versions from the cellar.
brew cleanup
