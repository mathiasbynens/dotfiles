# Install command-line tools using Homebrew
# Usage: `brew bundle Brewfile`

# Make sure we’re using the latest Homebrew
update

# Upgrade any already-installed formulae
upgrade

# Install GNU core utilities (those that come with OS X are outdated)
# Don’t forget to add `$(brew --prefix coreutils)/libexec/gnubin` to `$PATH`.
install coreutils
#sudo ln -s /usr/local/bin/gsha256sum /usr/local/bin/sha256sum

# Install some other useful utilities like `sponge`
install moreutils
# Install GNU `find`, `locate`, `updatedb`, and `xargs`, `g`-prefixed
install findutils
# Install GNU `sed`, overwriting the built-in `sed`
install gnu-sed --default-names
# Install Bash 4
# Note: don’t forget to add `/usr/local/bin/bash` to `/etc/shells` before running `chsh`.
install bash
install bash-completion

# Install wget with IRI support
install wget --enable-iri

# Install RingoJS and Narwhal
# Note that the order in which these are installed is important; see http://git.io/brew-narwhal-ringo.
install ringojs
install narwhal

# Install more recent versions of some OS X tools
install vim --override-system-vi
install homebrew/dupes/grep
install homebrew/dupes/screen
install homebrew/php/php55 --with-gmp

# Install some CTF tools; see https://github.com/ctfs/write-ups
install bfg
install binutils
install binwalk
install cifer
install dex2jar
install dns2tcp
install fcrackzip
install foremost
install hashpump
install hydra
install john
install knock
install nmap
install pngcheck
install sqlmap
install tcpflow
install tcpreplay
install tcptrace
install ucspi-tcp # `tcpserver` et al.
install xpdf
install xz

# Install other useful binaries
install ack
#install exiv2
install git
install imagemagick --with-webp
install lynx
install node # This installs `npm` too using the recommended installation method
install p7zip
install pigz
install pv
install rename
install rhino
install tree
install webkit2png
install zopfli

install homebrew/versions/lua52

# Remove outdated versions from the cellar
cleanup
