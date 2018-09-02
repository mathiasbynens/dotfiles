#!/usr/bin/env bash
source ./helpers.sh

header "INSTALLING DOTFILES"

CPATH="$(pwd)/dotfiles"
DOTFILES=($(cd ./dotfiles && ls -A | egrep '^\.'))

for FILE in "${DOTFILES[@]}"
do
  rm -rf ~/$FILE
  ln -s $CPATH/$FILE ~/$FILE
  echo "created symlink ~/$FILE refers to $CPATH/$FILE"
done


footer
