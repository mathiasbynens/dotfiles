#!/usr/bin/env bash

# Ask for the administrator password upfront
sudo -v

echo ""
echo "$(tput setaf 6)Installing homebrew apps$(tput setaf 7)"
echo ""

#Install Homebrew
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

# Install command-line tools using Homebrew.

# Make sure we’re using the latest Homebrew.
brew update

# Upgrade any already-installed formulae.
brew upgrade

# deactive OSX GateKeeper
sudo spctl --master-disable

# Install GNU core utilities (those that come with macOS are outdated).
# Don’t forget to add `$(brew --prefix coreutils)/libexec/gnubin` to `$PATH`.
brew install coreutils

# Install some other useful utilities like `sponge`.
brew install moreutils
# Install GNU `find`, `locate`, `updatedb`, and `xargs`, `g`-prefixed.
brew install findutils
# Install GNU `sed`, overwriting the built-in `sed`.
brew install gnu-sed --with-default-names

# # Install `wget` with IRI support.
brew install wget --with-iri

# # Install more recent versions of some macOS tools.
# brew install vim --with-override-system-vi
# brew install homebrew/dupes/grep
# brew install homebrew/dupes/openssh
# brew install homebrew/dupes/screen
# brew install homebrew/php/php56 --with-gmp

# Install other useful binaries.

# programs
brew install dark-mode
brew install git
brew install git-flow
brew install gpg
brew install grc
brew install heroku-toolbelt
heroku update
brew install lynx
brew install mas
brew install python
brew install pyenv
brew install pyenv-virtualenv
brew install pyenv-virtualenvwrapper
brew install nodeenv
brew install mysql
brew install redis
brew install rename
brew install testssl
brew install tree
brew install node
brew install mongodb --with-openssl
sudo mkdir -p /data/db
sudo chown -R `id -u` /data/db
brew install webkit2png
brew install wget

npm install -g bower
npm install -g cordova
npm install -g jasmine
npm install -g foundation-cli
npm install -g karma-cli
npm install -g nodemon
npm install -g phantomjs
npm install -g trash-cli
npm install -g vue-cli
npm install -g webpack

# applications
APPPATH="/Applications/"
export HOMEBREW_CASK_OPTS="--appdir=$APPPATH"

brew cask install dropbox
brew cask install firefox
brew cask install flux
brew cask install focus
brew cask install google-chrome
brew cask install iterm2
brew cask install java
brew cask install keka
brew cask install little-snitch
brew cask install mamp
brew cask install macvim
brew cask install opera
brew cask install slack
brew cask install sourcetree
brew cask install spotify
brew cask install spotify-notifications
brew cask install skyfonts
brew cask install skype-for-business
brew cask install sublime-text
brew cask install transmission
brew cask install vagrant
brew cask install virtualbox
brew cask install vlc
brew cask install whatsapp

# some plugins to enable different files to work with mac quicklook.
# includes features like syntax highlighting, markdown rendering, preview of jsons, patch files, csv, zip files etc.
brew cask install qlcolorcode
brew cask install qlstephen
brew cask install qlmarkdown
brew cask install quicklook-json
brew cask install qlprettypatch
brew cask install quicklook-csv
brew cask install betterzipql
brew cask install webpquicklook
brew cask install suspicious-package

echo 'Please login into App Store to install App Store apps';
echo 'Press any key to continue...'; read -k1 -s
echo  '\n'

# app store applications
mas install 497799835 # xcode
mas install 402398561 # mindNode Pro
mas install 443987910 # 1Password
mas install 422025166 # screenFlow
mas install 409203825 # numbers
mas install 403388562 # panic transmit
mas install 409201541 # pages
mas upgrade

# Remove outdated versions from the cellar.
brew cleanup --force
rm -f -r /Library/Caches/Homebrew/*

echo ""
echo "$(tput setaf 6)Finished installing homebrew apps$(tput setaf 7)"
echo ""