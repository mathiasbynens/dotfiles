#!/usr/bin/env bash

opts='-avh --no-perms'
opts+=' --exclude .git/'
opts+=' --exclude .DS_Store'
opts+=' --exclude bootstrap.sh'
opts+=' --exclude README.md'
opts+=' --exclude LICENSE-MIT.txt'
opts+=' --exclude .osx'

if [ "$OSTYPE" != "cygwin" ]; then
    opts+=' --exclude .minttyrc'
fi 

cd "$(dirname "${BASH_SOURCE}")"

rsync $opts . ~
