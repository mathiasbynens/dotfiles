# Install command-line tools using Homebrew.

# Install GNU core utilities (those that come with macOS are outdated).
# Don’t forget to add `$(brew --prefix coreutils)/libexec/gnubin` to `$PATH`.
brew 'coreutils'

# Install some other useful utilities like `sponge`.
brew 'moreutils'
# Install GNU `find`, `locate`, `updatedb`, and `xargs`, `g`-prefixed.
brew 'findutils'
# Install GNU `sed`, overwriting the built-in `sed`.
brew 'gnu-sed' #--with-default-names
# Install Bash 4.
# Note: don’t forget to add `/usr/local/bin/bash` to `/etc/shells` before
# running `chsh`.
brew 'bash'
tap 'homebrew/versions'
brew 'bash-completion2'

# Install `wget` with IRI support.
brew 'wget', args: ['with-iri']

# Install RingoJS and Narwhal.
# Note that the order in which these are installed is important;
# see http://git.io/brew-narwhal-ringo.
brew 'ringojs'
brew 'narwhal'

# Install more recent versions of some macOS tools.
brew 'vim', args: ['override-system-vi']
brew 'homebrew/dupes/grep'
brew 'homebrew/dupes/openssh'
brew 'homebrew/dupes/screen'
brew 'homebrew/php/php56', args: ['with-gmp']

# Install font tools.
tap 'bramstein/webfonttools'
brew 'sfnt2woff'
brew 'sfnt2woff-zopfli'
brew 'woff2'

# Install some CTF tools; see https://github.com/ctfs/write-ups.
brew 'aircrack-ng'
brew 'bfg'
brew 'binutils'
brew 'binwalk'
brew 'cifer'
brew 'dex2jar'
brew 'dns2tcp'
brew 'fcrackzip'
brew 'foremost'
brew 'hashpump'
brew 'hydra'
brew 'john'
brew 'knock'
brew 'netpbm'
brew 'nmap'
brew 'pngcheck'
brew 'socat'
brew 'sqlmap'
brew 'tcpflow'
brew 'tcpreplay'
brew 'tcptrace'
brew 'ucspi-tcp '# `tcpserver` etc.
brew 'xpdf'
brew 'xz'

# Install other useful binaries.
brew 'ack'
brew 'dark-mode'
#brew install exiv2
brew 'git'
brew 'git-lfs'
brew 'imagemagick', args:['with-webp']
brew 'lua'
brew 'lynx'
brew 'p7zip'
brew 'pigz'
brew 'pv'
brew 'rename'
brew 'rhino'
brew 'speedtest_cli'
brew 'ssh-copy-id'
brew 'testssl'
brew 'tree'
brew 'vbindiff'
brew 'webkit2png'
brew 'zopfli'
