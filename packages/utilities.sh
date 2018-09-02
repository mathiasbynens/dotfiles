#!/usr/bin/env bash
source ./helpers.sh
source ./packages/brew.sh

header "INSTALLING UTILITIES"

UTILITIES=(#
    #Install GNU core utilities (those that come with macOS are outdated).
    #Don’t forget to add `$(brew --prefix coreutils)/libexec/gnubin` to `$PATH`.
    coreutils

    #Install some other useful utilities like `sponge`.
    moreutils

    #Install GNU `find`, `locate`, `updatedb`, and `xargs`, `g`-prefixed.
    findutils

    #Install GNU `sed`, overwriting the built-in `sed`.
    gnu-sed --with-default-names

    #Install `wget` with IRI support.
    wget --with-iri

    #Install more recent versions of some macOS tools.
    homebrew/dupes/grep
    homebrew/dupes/openssh
    homebrew/dupes/screen
    homebrew/php/php56 --with-gmp

    #Install other useful binaries.
    python
    node
    mysql
    docker-cloud
    docker-compose
    ack
    ctags
    cmake
    dark-mode
    git
    git-flow
    gpg
    grc
    htop
    lynx
    mas
    pyenv
    pyenv-virtualenv
    pyenv-virtualenvwrapper
    nodeenv
    redis
    rename
    testssl
    the_silver_searcher
    tree
    mongodb --with-openssl
    watchman
    webkit2png
    wget
    yarn
    heroku-toolbelt
)

install 'brew cask install' "${UTILITIES[@]}"

heroku update

cleanBrewCache

footer
