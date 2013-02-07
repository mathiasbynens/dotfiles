#!/bin/bash
cd "$(dirname "${BASH_SOURCE}")"

echo "Self update"
git pull

function doIt() {
    dirss=`find . -type d \( ! -name ".git*" ! -path "*/.git/*" \) | cut -c 3-`

    files=`find . -type f \( ! -path "*/.git/*" \
                             ! -name "README.md" \
                             ! -name ".DS_Store" \
                             ! -name "bootstrap.sh" \) | cut -c 3-`

    echo "Create directory hierarchy"
    for d in $dirss
    do
        mkdir -p "$HOME/$d"
    done

    echo "Setting up symlinks"
    for f in $files
    do
        ln -snf "$PWD/$f" "$HOME/$f"
    done
}

if [ "$1" == "--force" -o "$1" == "-f" ]; then
    doIt
else
    read -p "This may overwrite existing files in your home directory. Are you sure? (y/n) " -n 1
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        doIt
    fi
fi
unset doIt
source ~/.bash_profile