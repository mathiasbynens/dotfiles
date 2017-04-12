#!/usr/bin/env bash

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

# # Install some other useful utilities like `sponge`.
# brew install moreutils
# # Install GNU `find`, `locate`, `updatedb`, and `xargs`, `g`-prefixed.
# brew install findutils
# # Install GNU `sed`, overwriting the built-in `sed`.
# brew install gnu-sed --with-default-names
# # Install Bash 4.
# # Note: don’t forget to add `/usr/local/bin/bash` to `/etc/shells` before
# # running `chsh`.
# brew install bash
# brew tap homebrew/versions
# brew install bash-completion2

# # Switch to using brew-installed bash as default shell
# if ! fgrep -q '/usr/local/bin/bash' /etc/shells; then
#   echo '/usr/local/bin/bash' | sudo tee -a /etc/shells;
#   chsh -s /usr/local/bin/bash;
# fi;

# # Install `wget` with IRI support.
# brew install wget --with-iri

# # Install RingoJS and Narwhal.
# # Note that the order in which these are installed is important;
# # see http://git.io/brew-narwhal-ringo.
# brew install ringojs
# brew install narwhal

# # Install more recent versions of some macOS tools.
# brew install vim --with-override-system-vi
# brew install homebrew/dupes/grep
# brew install homebrew/dupes/openssh
# brew install homebrew/dupes/screen
# brew install homebrew/php/php56 --with-gmp

# # Install font tools.
# brew tap bramstein/webfonttools
# brew install sfnt2woff
# brew install sfnt2woff-zopfli
# brew install woff2

# # Install some CTF tools; see https://github.com/ctfs/write-ups.
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

# # Install other useful binaries.
# brew install ack
# brew install dark-mode
# #brew install exiv2
# brew install git
# brew install git-lfs
# brew install imagemagick --with-webp
# brew install lua
# brew install lynx
# brew install p7zip
# brew install pigz
# brew install pv
# brew install rename
# brew install rhino
# brew install speedtest_cli
# brew install ssh-copy-id
# brew install testssl
# brew install tree
# brew install vbindiff
# brew install webkit2png
# brew install zopfli

# programs
brew install mas
brew install wget
brew install lynx
brew install git
brew install git-flow
brew install gpg
brew install grc
brew install gls
brew install heroku-toolbelt
heroku update
brew install pyenv
brew install pyenv-virtualenv
brew install pyenv-virtualenvwrapper
brew install nodeenv
brew install mysql
brew install redis
brew install node
brew install mongodb --with-openssl
sudo mkdir -p /data/db
sudo chown -R `id -u` /data/db

npm install -g  trash-cli
npm install -g bower
npm install -g nodemon
npm install -g foundation-cli
npm install -g vue-cli
npm install -g cordova

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
brew cask install sublime-text2
brew cask install transmission
brew cask install vagrant
brew cask install virtualbox
brew cask install vlc
brew cask install whatsapp

# some plugins to enable different files to work with mac quicklook.includes features like syntax highlighting, markdown rendering, preview of jsons, patch files, csv, zip files etc.
brew cask install qlcolorcode
brew cask install qlstephen
brew cask install qlmarkdown
brew cask install quicklook-json
brew cask install qlprettypatch
brew cask install quicklook-csv
brew cask install betterzipql
brew cask install webpquicklook
brew cask install suspicious-package

# Remove outdated versions from the cellar.
brew cleanup --force
rm -f -r /Library/Caches/Homebrew/*