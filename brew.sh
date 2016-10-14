#!/usr/bin/env bash

# Brewfile for macOS

# Ask for the administrator password upfront
sudo -v

# Keep-alive: update existing 'sudo' time stamp until this script has finished
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &

# Install Homebrew
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

# Disable Homebrew (Google-powered) analytics
export HOMEBREW_NO_ANALYTICS=1

# Make sure we’re using the latest Homebrew.
brew update

# Add Caskroom
brew tap caskroom/cask

# Update & Upgrade
brew update
brew upgrade --all

# Install Brew packages
brew install \
    android-platform-tools \
    bash \
    coreutils \
    npm

# Set login shell to homebrew-sourced Bash
if ! fgrep -q '/usr/local/bin/bash' /etc/shells; then
  echo '/usr/local/bin/bash' | sudo tee -a /etc/shells;
  chsh -s /usr/local/bin/bash;
fi;

# Install Cask packages
brew cask install \
    airparrot \
    calibre \
    dropbox \
    flux \
    google-chrome \
    iterm2 \
    libreoffice \
    skype \
    spotify \
    sublime-text \
    the-unarchiver \
    transmission \
    viscosity \
    vlc \
    whatsapp

# Remove outdated versions from the cellar.
brew cleanup
