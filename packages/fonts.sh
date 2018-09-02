#!/usr/bin/env bash
source ./helpers.sh
source ./packages/brew.sh

header "Installing fonts"

brew tap caskroom/fonts

FONTS=(font-alegreya font-alegreya-sans
    font-archivo-narrow
    font-awesome-terminal-fonts
    font-bitter
    font-cardo
    font-crimson-text
    font-domine
    font-droid-sans-mono
    font-droid-sans-mono-for-powerline
    font-fira-sans
    font-inconsolata
    font-pt-sans
    font-pt-serif
    font-gentium-basic
    font-karla
    font-lato
    font-libre-baskerville
    font-libre-franklin
    font-lora
    font-merriweather
    font-merriweather-sans
    font-neuton
    font-open-sans
    font-open-sans-condensed
    font-playfair-display
    font-poppins
    font-rajdhani
    font-raleway
    font-roboto
    font-roboto-slab
    font-source-sans-pro
    font-source-serif-pro
    font-space-mono
    font-work-sans
)
install 'brew cask install' "${FONTS[@]}"

cleanBrewCache

footer
