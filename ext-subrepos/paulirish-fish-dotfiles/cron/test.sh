#!/bin/bash
set -x

PATH=/Users/paulirish/.homebrew/bin:/Users/paulirish/.homebrew/sbin:/Users/paulirish/code/depot_tools:$PATH

goma_ensure_start_py=$(cat << EOM
import sys
sys.path.append('/Users/paulirish/goma/')

from goma_ctl import *

goma = GetGomaDriver()
goma.Dispatch(['ensure_start'])
EOM
)
env GOMAMAILTO=/dev/null env GOMA_OAUTH2_CONFIG_FILE=/Users/paulirish/.goma_oauth2_config env GOMA_ENABLE_REMOTE_LINK=yes python3 -c "$goma_ensure_start_py"
