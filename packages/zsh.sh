#!/usr/bin/env bash
source ./helpers.sh

header "Installing ZSH"

# ZSH package manager
echo "Removing ~/.antigen"
rm -rf ~/.antigen
echo "Starting to install antigen into ~/.antigen"
curl -L git.io/antigen > antigen.zsh
echo "antigen installed"

footer