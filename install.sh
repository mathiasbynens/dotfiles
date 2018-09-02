#!/usr/bin/env bash

cd "$(dirname "${BASH_SOURCE}")";

echo "Checking for updates in dotfiles.."
git pull origin master;



# main menu
function menu() {
    echo -e "\nWhat do you want to do?";
    read -p " 1. Install dotfiles`
    echo $'\n '`2. Install applications`
    echo $'\n '`> ";

    if [[ $REPLY =~ ^[1]$ ]]; then
        dotfiles;
    fi;

    if [[ $REPLY =~ ^[2]$ ]]; then
        packages;
    fi;
}

function dotfiles() {
    source ./dotfiles.sh
    menu
}

function packages() {
    source ./packages.sh
    menu
}

menu
