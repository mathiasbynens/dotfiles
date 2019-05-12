#!/bin/bash

# `crontab -l` sez this runs every hour on the hour

set -x

PATH=/Users/paulirish/bin:/Users/paulirish/.homebrew/bin:/Users/paulirish/.homebrew/sbin:/Users/paulirish/code/depot_tools:$PATH

local_script_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"


which node
node --version

# https://github.com/ChromeDevTools/devtools-protocol
cd "$HOME/code/pristine/devtools-protocol/scripts" && ./update-to-latest.sh
cd "$HOME/code/pristine/devtools-protocol/scripts" && ./update-n-publish-docs.sh

# https://github.com/ChromeDevTools/devtools-frontend
cd "$HOME/code/npm-publish-devtools-frontend" && ./update-github-mirror.sh

