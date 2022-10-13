export PATH=$HOME/bin:$PATH;

# Make vim the default editor.
export EDITOR='nano';

# Enable persistent REPL history for `node`.
NODE_REPL_HISTORY_FILE=~/.node_history;
# Allow 32³ entries; the default is 1000.
NODE_REPL_HISTORY_SIZE='32768';

# Increase Bash history size. Allow 32³ entries; the default is 500.
export HISTSIZE='32768';
export HISTFILESIZE="${HISTSIZE}";
# Omit duplicates and commands that begin with a space from history.
export HISTCONTROL='ignoreboth';

# Prefer US English and use UTF-8.
export LANG='en_US.UTF-8';
export LC_ALL='en_US.UTF-8';

# Highlight section titles in manual pages.
export LESS_TERMCAP_md="${yellow}";

# Don’t clear the screen after quitting a manual page.
export MANPAGER='less -X';

## Needed for flipper
COMPANION_PATH=/usr/local/Cellar/idb-companion/1.0.14/bin/idb_companion

# We don't ever want to send fastlane analytics
# http://docs.fastlane.tools/#metrics
FASTLANE_OPT_OUT_USAGE=1

# https://nextjs.org/telemetry#how-do-i-opt-out
NEXT_TELEMETRY_DISABLED=1

## volta
export VOLTA_HOME=$HOME/.volta
export PATH=$PATH:$VOLTA_HOME/bin
