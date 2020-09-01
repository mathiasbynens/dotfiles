#!/usr/bin/env bash

# Install command-line tools using Homebrew.

if ! command -v brew &>/dev/null 2>&1; then
  notice "Installing Homebrew..."
  #   Ensure that we can actually, like, compile anything.
  if [[ ! $(command -v gcc) || ! "$(command -v git)" ]]; then
    _commandLineTools_
  fi

  # Install Homebrew
  /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
  brew analytics off
else
  return 0
fi
command -v brew >/dev/null 2>&1 || /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)" 

# Make sure we’re using the latest Homebrew.
brew update

# Use the Brewfile if it is found
# Allows for use of Bucklet's latest brew dump, e.g., 'Brewfile-20200831T135042'
shopt -s nullglob
set -- ./Brewfile-*
if [ "$#" -gt 0 ]; then
  cp $(ls -1t "$@" | head -1) ./Brewfile
fi
set -- $HOME/Brewfile-*
if [ "$#" -gt 0 ]; then
  cp $(ls -1t "$@" | head -1) ./Brewfile
fi
shopt -u nullglob
if [ -e ./Brewfile ]; then
  brew bundle
fi

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
# Install a modern version of zsh.
brew install zsh
brew install zsh-completions
brew install zsh-history-substring-search
brew install zsh-syntax-highlighting

NEWSHELLS=("bash" "zsh")
for TMPSHL in "${NEWSHELLS[@]}";
do 
  # Add brew-installed shell to /etc/shells if missing
  if ! grep -F -q "${BREW_PREFIX}/bin/${TMPSHL}" /etc/shells; then
    echo "${BREW_PREFIX}/bin/${TMPSHL}" | sudo tee -a /etc/shells;
    echo "Added ${BREW_PREFIX}/bin/${TMPSHL} to /etc/shells";
  fi;
  # Switch to using brew-installed shell as default shell
  if grep -F -q "${BREW_PREFIX}/bin/${TMPSHL}" /etc/shells && [ "$SHELL" != "${BREW_PREFIX}/bin/${TMPSHL}" ]; then
    chsh -s "${BREW_PREFIX}/bin/${TMPSHL}";
    echo "Your default shell is now ${BREW_PREFIX}/bin/${TMPSHL}"
  fi;
done
unset NEWSHELLS

# Install `wget` with IRI support.
brew install wget # --with-iri

# Install GnuPG to enable PGP-signing commits.
brew install gnupg

# Install rsync
brew install rsync

# Install perl
brew install perl
brew link --overwrite perl
# update perl modules
# sudo su -c 'curl -L https://cpanmin.us | perl - App::cpanminus ; cpanm App::cpanoutdated ; cpan-outdated -p | cpanm'

# Install more recent versions of some macOS tools.
brew install vim # --with-override-system-vi
brew install grep
brew install openssh
brew install openssl
brew install screen
brew install php
brew install gmp

# Install font tools.
# brew tap bramstein/webfonttools
# brew install sfnt2woff
# brew install sfnt2woff-zopfli
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
brew install imagemagick
brew install lua luarocks
brew install lynx
brew install p7zip
brew install pigz
brew install zopfli
brew install pv
brew install rename
brew install rlwrap
brew install ssh-copy-id
brew install tree
brew install vbindiff

# Remove outdated versions from the cellar.
brew cleanup
