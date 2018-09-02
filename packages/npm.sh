#!/usr/bin/env bash
source ./helpers.sh
source ./packages/brew.sh

header "Installing global node packages"

brew install node
cleanBrewCache

PACKAGES=(bower
    browser-sync
    expo-cli
    karma-cli
    nodemon
    prettier
    trash-cli
    tslint
    typescript
    vue-cli
    webpack
    git+https://github.com/ramitos/jsctags.git
)
install 'npm install -g ' "${PACKAGES[@]}"

footer
