#!/usr/bin/env bash

cd "$(dirname "${BASH_SOURCE}")"

rsync --exclude ".git/" --exclude ".DS_Store" --exclude "bootstrap.sh" \
      --exclude "README.md" --exclude "LICENSE-MIT.txt" -avh --no-perms . ~
