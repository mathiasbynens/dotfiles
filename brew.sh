#!/usr/bin/env bash

# Install command-line tools using Homebrew.

# Make sure we’re using the latest Homebrew.
brew update

# Upgrade any already-installed formulae.
brew upgrade

# Install GNU core utilities (those that come with macOS are outdated).
# Don’t forget to add `$(brew --prefix coreutils)/libexec/gnubin` to `$PATH`.
brew install coreutils

# Install some other useful utilities like `sponge`.
brew install moreutils
# Install GNU `find`, `locate`, `updatedb`, and `xargs`, `g`-prefixed.
brew install findutils
# Install GNU `sed`, overwriting the built-in `sed`.
brew install gnu-sed --with-default-names
# Install Bash 4.
# Note: don’t forget to add `/usr/local/bin/bash` to `/etc/shells` before
# running `chsh`. To do so, run `sudo chsh -s /usr/local/bin/bash`.
brew install bash
brew tap homebrew/versions
brew install bash-completion2

# Switch to using brew-installed bash as default shell
if ! fgrep -q '/usr/local/bin/bash' /etc/shells; then
  echo '/usr/local/bin/bash' | sudo tee -a /etc/shells;
  chsh -s /usr/local/bin/bash;
fi;

# Install `wget` with IRI support.
brew install wget --with-iri

# Install more recent versions of some macOS tools.
brew install vim --with-override-system-vi
brew install homebrew/dupes/grep
brew install homebrew/dupes/openssh
brew install homebrew/dupes/screen

# Install other useful binaries.
brew install the_silver_searcher
brew install dark-mode
brew install git
brew install git-lfs
brew install tree
brew install nmap
brew install mtr
brew install colordiff
brew install ipcalc
brew install unrar
brew install w3m
brew install jq

# work bits
brew install cli53
brew install subversion
brew install terraform
brew install terraform-docs
brew install awscli
brew install percona-toolkit
brew install mysql
brew cask install java
brew install maven

# puppet-site shit
brew cask install virtualbox
brew cask install vagrant
vagrant plugin install vagrant-host-shell
vagrant plugin install vagrant-share --plugin-version 1.1.8
# not technically from homebrew
# gem install r10k --user-install

# personal
brew install wakeonlan
brew install thefuck
brew install tiny-fugue
brew install wallpaper
brew cask install microsoft-remote-desktop-beta

# Cask time
brew cask install sublime-text
brew cask install spectacle
brew cask install slack
brew cask install viscosity
brew cask install google-chrome
brew cask install flux
brew cask install vassal

# Remove outdated versions from the cellar.
brew cleanup
