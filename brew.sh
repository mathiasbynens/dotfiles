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
brew install coreutils
ln -s "${BREW_PREFIX}/bin/gsha256sum" "${BREW_PREFIX}/bin/sha256sum"

# Install some other useful utilities like `sponge`.
# brew install moreutils
# Install GNU `find`, `locate`, `updatedb`, and `xargs`, `g`-prefixed.
brew install findutils
# Install GNU `sed`, overwriting the built-in `sed`.
brew install gnu-sed --with-default-names
# Install a modern version of Bash.
brew install bash
brew install bash-completion2
# Switch to using brew-installed bash as default shell
if ! fgrep -q "${BREW_PREFIX}/bin/bash" /etc/shells; then
  echo "${BREW_PREFIX}/bin/bash" | sudo tee -a /etc/shells;
  chsh -s "${BREW_PREFIX}/bin/bash";
fi;



brew install caskroom/cask/brew-cask
# brew tap caskroom/cask # !!! ERROR HERE ?

## Generic utilities
##############################################

# command line json editor
brew install jq

# AWS command line interface
brew install awscli

# file compressor
brew cask install keka

# multi-protocol (HTTP(S), FTP, SFTP, BitTorrent, and Metalink) download utility
# brew install aria2

# npm environment manager
brew install nvm

# http test tool (curl-like)
brew install httpie

# file system watch and execute command on file change
brew install fswatch

# yaml/json merger -> https://github.com/geofffranks/spruce
brew tap starkandwayne/cf
brew install spruce

# how to add licence number?
brew cask install atext
brew cask install tomighty

brew cask install macdown && ./addDockIcon.sh "MacDown"
brew cask install google-chrome && ./addDockIcon.sh "Google Chrome"
brew cask install firefox && ./addDockIcon.sh "Firefox"
# brew cask slack !!! ERROR HERE ?
brew cask install slack && ./addDockIcon.sh "Slack"
brew cask install authy && ./addDockIcon.sh "Authy Desktop"
brew cask install iterm2 && ./addDockIcon.sh "iTerm"
brew cask install atom && ./addDockIcon.sh "Atom"

# brew cask install virtualbox-extension-pack
# brew cask install docker

brew cask install dropbox
brew cask install google-backup-and-sync

# office related
brew cask install microsoft-office
brew cask install onedrive

# requires extra consent in Security & Privacy panel
brew cask install avira-antivirus

# DEV tools
# Attention: this installs latest Oracle java (10.x currently), requires password
# brew cask install java
# brew install maven
# brew cask install intellij-idea-ce && ./addDockIcon.sh "IntelliJ IDEA CE"



# DG end




# Install `wget` with IRI support.
brew install wget --with-iri

# Install GnuPG to enable PGP-signing commits.
brew install gnupg

# Install more recent versions of some macOS tools.
brew install vim
brew install grep
brew install openssh
# brew install screen
# brew install php
# brew install gmp

# # Install font tools.
# brew tap bramstein/webfonttools
# brew install sfnt2woff
# brew install sfnt2woff-zopfli
# brew install woff2

# Install some CTF tools; see https://github.com/ctfs/write-ups.
# brew install aircrack-ng
# brew install bfg
# brew install binutils
# brew install binwalk
# brew install cifer
# brew install dex2jar
# brew install dns2tcp
# brew install fcrackzip
# brew install foremost
# brew install hashpump
# brew install hydra
# brew install john
# brew install knock
# brew install netpbm
# brew install nmap
# brew install pngcheck
# brew install socat
# brew install sqlmap
# brew install tcpflow
# brew install tcpreplay
# brew install tcptrace
# brew install ucspi-tcp # `tcpserver` etc.
# brew install xpdf
# brew install xz

# Install other useful binaries.
brew install ack
#brew install exiv2
brew install git
brew install git-lfs
brew install gs
brew install imagemagick --with-webp
brew install lua
# brew install lynx
# brew install p7zip
# # brew install pigz
brew install pv
brew install rename
brew install rlwrap
brew install ssh-copy-id
brew install tree
# brew install vbindiff
# brew install zopfli



# # failed on first install & requires password
# brew cask install virtualbox
# # requires password
# brew cask install tunnelblick




# Remove outdated versions from the cellar.
brew cleanup
