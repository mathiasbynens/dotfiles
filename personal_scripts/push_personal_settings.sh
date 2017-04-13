#!/bin/bash

# Pushes bash, vim, etc. settings to remote server. 
rsync -aLv ~/remote_settings/ "$1":~/
scp ~/.gitconfig_bonnier "$1":~/.gitconfig
rsync -av ~/scripts/bonnier/ "$1":~/bin/
