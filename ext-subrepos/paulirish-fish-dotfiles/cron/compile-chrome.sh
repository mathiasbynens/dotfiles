#!/bin/bash

set -x

PATH=/Users/paulirish/bin:/Users/paulirish/.homebrew/bin:/Users/paulirish/.homebrew/sbin:/Users/paulirish/code/depot_tools:/Applications/Xcode.app/Contents/Developer/usr/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/X11/bin:/usr/local/sbin:/Users/paulirish/.homebrew/Cellar/node/7.7.1_1/bin:/Users/paulirish/code/depot_tools:$PATH

chromium_path="$HOME/chromium/src"
chromium_pristine_path="$HOME/chromium-tot/src"

cd $chromium_path
git fetch origin

# Pop any stashed changes
unstash() {
  if [[ ! "$stash" =~ "No local changes to save" ]]; then
    echo
    echo "🍯  Popping stash..."
    git stash pop
  fi
}

# Stash any local changes
stash=$(git stash)

# checkout last known compilable version (touch more reliable than master)
# if we can't switch branches then just stop
git checkout origin/lkcr || exit 1
env GYP_DEFINES=disable_nacl=1 gclient sync --jobs=70

# start goma
	# goma_ensure_start_py=$(cat << EOM
	# import sys
	# sys.path.append('/Users/paulirish/goma/')

	# from goma_ctl import *

	# goma = GetGomaDriver()
	# goma.Dispatch(['ensure_start'])
	# EOM
	# )
	# env GOMAMAILTO=/dev/null env GOMA_OAUTH2_CONFIG_FILE=/Users/paulirish/.goma_oauth2_config env GOMA_ENABLE_REMOTE_LINK=yes python -c "$goma_ensure_start_py"

env GOMAMAILTO=/dev/null env GOMA_OAUTH2_CONFIG_FILE=/Users/paulirish/.goma_oauth2_config env GOMA_ENABLE_REMOTE_LINK=yes $HOME/goma/goma_ctl.py ensure_start


# start the build
ninja -C "$chromium_path/out/Default" -j600 chrome blink_tests


# build is finished?!
cd $chromium_path
unstash


# update the pristine repo so pull is faster
cd $chromium_pristine_path
git fetch origin

