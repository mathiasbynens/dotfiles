#!/usr/bin/env bash

# Install command-line tools using Homebrew.

# Ask for the administrator password upfront.
sudo -v

# Keep-alive: update existing `sudo` time stamp until the script has finished.
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &

# Make sure we’re using the latest Homebrew
brew update

# Upgrade any already-installed formulae.
brew upgrade --all

# Install GNU core utilities (those that come with OS X are outdated)
# Don’t forget to add `$(brew --prefix coreutils)/libexec/gnubin` to `$PATH`.
brew install coreutils
sudo ln -s /usr/local/bin/gsha256sum /usr/local/bin/sha256sum

# Install some other useful utilities like `sponge`
brew install moreutils
# Install GNU `find`, `locate`, `updatedb`, and `xargs`, `g`-prefixed
brew install findutils
# Install GNU `sed`, overwriting the built-in `sed`
brew install gnu-sed --with-default-names
# Install Bash 4
brew install bash
brew tap homebrew/versions
brew install bash-completion2

# Install wget with IRI support
brew install wget --with-iri

# Install RingoJS and Narwhal
# Note that the order in which these are installed is important; see http://git.io/brew-narwhal-ringo.
brew install ringojs
brew install narwhal

# Install more recent versions of some OS X tools
brew install vim --override-system-vi
brew install homebrew/dupes/grep
brew install homebrew/dupes/openssh
brew install homebrew/dupes/screen
brew install homebrew/php/php55 --with-gmp


# Install other useful binaries
brew install ack
#brew install exiv2
brew install foremost
brew install imagemagick --with-webp
brew install lynx
brew install mongodb
brew install nmap
brew install ucspi-tcp # `tcpserver` et al.
brew install node
brew install pigz
brew install phantomjs
brew install pv
brew install rename
brew install sqlmap
brew install tree
brew install webkit2png
# usage webkit2png http://www.google.com/
brew install xpdf


# Remove outdated versions from the cellar
brew cleanup
