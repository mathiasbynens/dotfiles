# Install command-line tools using Homebrew
# Usage: `brew bundle Brewfile`

# Make sure we’re using the latest Homebrew
update

# Upgrade any already-installed formulae
upgrade

# Install GNU core utilities (those that come with OS X are outdated)
# Don’t forget to add `$(brew --prefix coreutils)/libexec/gnubin` to `$PATH`.
install coreutils
# Install some other useful utilities like `sponge`
install moreutils
# Install GNU `find`, `locate`, `updatedb`, and `xargs`, `g`-prefixed
install findutils
# Install GNU `sed`, overwriting the built-in `sed`
install gnu-sed --default-names

# Install RingoJS and Narwhal
# Note that the order in which these are installed is important; see http://git.io/brew-narwhal-ringo.
install ringojs
install narwhal

# Install more recent versions of some OS X tools
install vim --override-system-vi
install homebrew/dupes/grep

# Install other useful binaries
install ack
install nmap
install node
install p7zip
install webkit2png

# Remove outdated versions from the cellar
cleanup
