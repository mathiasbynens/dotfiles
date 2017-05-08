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
echo "Installing programs"
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

echo "npm global packages"
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

echo "Installing apps"
brew cask install balsamiq-mockups
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
brew cask install on-the-job
brew cask install opera
brew cask install postman
brew cask install robomongo
brew cask install slack
brew cask install sourcetree
brew cask install spotify
brew cask install spotify-notifications
brew cask install skype-for-business
brew cask install steam
brew cask install sublime-text
brew cask install transmission
brew cask install vagrant
brew cask install virtualbox
brew cask install vlc
brew cask install whatsapp

echo "Installing quicklook helpers"
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

# fonts
echo "Installing fonts"
brew tap caskroom/fonts
brew cask install font-alegreya font-alegreya-sans
brew cask install font-archivo-narrow
brew cask install font-awesome-terminal-fonts
brew cask install font-bitter
brew cask install font-cardo
brew cask install font-crimson-text
brew cask install font-domine
brew cask install font-droid-sans-mono
brew cask install font-droid-sans-mono-for-powerline
brew cask install font-fira-sans
brew cask install font-inconsolata
brew cask install font-pt-sans
brew cask install font-pt-serif
brew cask install font-gentium-basic
brew cask install font-karla
brew cask install font-lato
brew cask install font-libre-baskerville
brew cask install font-libre-franklin
brew cask install font-lora
brew cask install font-merriweather
brew cask install font-merriweather-sans
brew cask install font-neuton
brew cask install font-open-sans
brew cask install font-open-sans-condensed
brew cask install font-playfair-display
brew cask install font-poppins
brew cask install font-rajdhani
brew cask install font-raleway
brew cask install font-roboto
brew cask install font-roboto-slab
brew cask install font-source-sans-pro
brew cask install font-source-serif-pro
brew cask install font-space-mono
brew cask install font-work-sans

echo 'Please login into App Store to install App Store apps';
echo 'Press any key to continue...'; read -k1 -s
echo  '\n'

# app store applications
echo "Installing App Store apps"
mas install 497799835 # xcode
mas install 402398561 # mindNode Pro
mas install 443987910 # 1Password
mas install 422025166 # screenFlow
mas install 409203825 # numbers
mas install 403388562 # panic transmit
mas install 409201541 # pages
mas upgrade

# Remove outdated versions from the cellar.
echo "cleaning cache"
brew cleanup --force
rm -f -r /Library/Caches/Homebrew/*

echo ""
echo "$(tput setaf 6)Finished installing homebrew apps$(tput setaf 7)"
echo ""