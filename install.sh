#!/bin/bash

# Install all homebrew packages inside Brewfile

# Check for Homebrew Installation
if ! which brew > /dev/null; then
     # Install Homebrew
     /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
fi;

# Update Homebrew
brew update

# Upgrade any already-installed formulae.
brew upgrade

# Install everything inside Brewfile
brew bundle

# Switch to using brew-installed bash as default shell
if ! fgrep -q '/usr/local/bin/bash' /etc/shells; then
  echo '/usr/local/bin/bash' | sudo tee -a /etc/shells;
  chsh -s /usr/local/bin/bash;
fi;

# Remove outdated versions from the cellar.
brew cleanup
