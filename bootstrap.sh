#!/usr/bin/env bash
#
#
set -x
#
__DIR__=`dirname $0`
cd ${__DIR__}
__PWD__=`pwd`
__CURRDIR__=${__PWD__}

TOBE_LINKED=(
    ".gitconfig"
    ".gitignore"
    ".gvimrc"
    ".macos"
    ".vimrc"
    ".vim"
    ".wgetrc"
    ".zprezto"
    ".editorconfig"
    ".curlrc"
    ".screenrc"
    ".wgetrc"
)

while [ "x${TOBE_LINKED[count]}" != "x" ]
do
   count=$(( $count + 1 ))
   link=${TOBE_LINKED[count]}
   # echo $link
   if [[ -e $link ]]; then
       ln -sf ${__CURRDIR__}/$link ~/$link
   fi
done


# Setup zsh using .zprezto
#

ZPREZTORCS=(
    "zshenv"
    "zprofile"
    "zshrc"
    "zpreztorc"
    "zlogin"
    "zlogout"
)
while [[ "x${ZPREZTORCS[zcount]}" != "x" ]]; do
    zcount=$(( $zcount + 1 ))
    rcfile=${ZPREZTORCS[zcount]}
    rcpath=$__CURRDIR__/.zprezto/runcoms/${ZPREZTORCS[zcount]}
    # echo $rcpath
    if [[ -f $rcpath ]]; then
        ln -sf $rcpath ~/.${rcfile}
    fi
done



