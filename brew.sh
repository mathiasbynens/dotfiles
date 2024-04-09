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
brew install moreutils
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

# Install `wget` with IRI support.
brew install wget --with-iri

# Install GnuPG to enable PGP-signing commits.
brew install gnupg

# Install more recent versions of some macOS tools.
brew install vim --with-override-system-vi
brew install grep
brew install openssh
brew install screen
brew install php
brew install gmp

# Install font tools.
brew tap bramstein/webfonttools
brew install sfnt2woff
brew install sfnt2woff-zopfli
brew install woff2

# Install some CTF tools; see https://github.com/ctfs/write-ups.
brew install aircrack-ng
brew install bfg
brew install binutils
brew install binwalk
brew install cifer
brew install dex2jar
brew install dns2tcp
brew install fcrackzip
brew install foremost
brew install hashpump
brew install hydra
brew install john
brew install knock
brew install netpbm
brew install nmap
brew install pngcheck
brew install socat
brew install sqlmap
brew install tcpflow
brew install tcpreplay
brew install tcptrace
brew install ucspi-tcp # `tcpserver` etc.
brew install xpdf
brew install xz

# Install other useful binaries.
brew install ack
#brew install exiv2
brew install git
brew install git-lfs
brew install gs
brew install imagemagick --with-webp
brew install lua
brew install lynx
brew install p7zip
brew install pigz
brew install pv
brew install rename
brew install rlwrap
brew install ssh-copy-id
brew install tree
brew install vbindiff
brew install zopfli
brew install archey

# Install macos casks
brew install --cask google-chrome
brew install --cask brave-browser
brew install --cask firefox
brew install --cask vivaldi
brew install --cask bettertouchtool
brew install --cask alfred
brew install --cask sublime-text
brew install --cask kitty
brew install --cask local
brew install --cask tinypng4mac
brew install --cask suspicious-package
brew install --cask svgcleaner
brew install --cask runjs
brew install --cask poedit
brew install --cask nsregextester
brew install --cask noun-project
brew install --cask keka
brew install --cask jdiskreport
brew install --cask hacker-menu
brew install --cask geekbench
brew install --cask geektool
brew install --cask docker
brew install --cask deepl
brew install --cask console
brew install --cask bigsur-cache-cleaner


brew install --cask vlc
brew install --cask xld
brew install --cask vox
brew install --cask spek
brew install --cask soulseek
brew install --cask transmission
brew install --cask musicbrainz-picard
brew install --cask moebius
brew install --cask mixed-in-key
brew install --cask losslesscut
brew install --cask fastclicker
brew install --cask cocktail
brew install --cask cncnet
brew install --cask camera-live
brew install bandcamp-dl


# Remove outdated versions from the cellar.
brew cleanup
