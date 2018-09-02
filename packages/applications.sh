#!/usr/bin/env bash
source ./helpers.sh
source ./packages/brew.sh

header "Installing applications"

APPPATH="/Applications/"
export HOMEBREW_CASK_OPTS="--appdir=$APPPATH"

APPLICATIONS=(balsamiq-mockups
    dropbox
    firefox
    focus
    ghostlab
    google-chrome
    iterm2
    java
    keka
    little-snitch
    mamp
    on-the-job
    opera
    pgadmin4
    postgres
    postman
    robo-3t
    sketch
    sequel-pro
    slack
    sourcetree
    spotify
    sublime-text
    transmission
    vagrant
    virtualbox
    vlc
    whatsapp
    docker
)
install 'brew cask install' ${APPLICATIONS[@]}

#some plugins to enable different files to work with mac quicklook.
#includes features like syntax highlighting, markdown rendering, preview of jsons, patch files, csv, zip files etc.
QUICKLOOK_PLUGINS=(qlcolorcode
    qlstephen
    qlmarkdown
    quicklook-json
    qlprettypatch
    quicklook-csv
    betterzipql
    webpquicklook
    suspicious-package
)
install 'brew cask install' ${QUICKLOOK_PLUGINS[@]}

APPLE_STORE_APPS=(497799835 # xcode
    402398561 # mindNode Pro
    443987910 # 1Password
    422025166 # screenFlow
    409203825 # numbers
    403388562 # panic transmit
    409201541 # pages
)
install 'mas install' ${APPLE_STORE_APPS[@]}

cleanBrewCache

footer
