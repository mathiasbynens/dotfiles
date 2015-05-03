
export ZSH=$HOME/.oh-my-zsh

# Set name of the theme to load.
# Look in ~/.oh-my-zsh/themes/
# Optionally, if you set this to "random", it'll load a random theme each
# time that oh-my-zsh is loaded.
ZSH_THEME="robbyrussell"

# Plugins
# Which plugins would you like to load? (plugins can be found in ~/.oh-my-zsh/plugins/*)
# Custom plugins may be added to ~/.oh-my-zsh/custom/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
plugins=(git)

# Path configuration
export PATH="/usr/local/bin:/usr/local/share/python:/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:/opt/X11/bin"
export PATH=/Users/mickaellegal/Dropbox/.tools:$PATH

# Save a ton of history
HISTSIZE=10000
HISTFILE=~/.zsh_history
SAVEHIST=10000

# Enable completion
autoload -U compinit
compinit

# Bind keys to use vim mode in shell
bindkey -v
bindkey -M viins 'jj' vi-cmd-mode
bindkey '^R' history-incremental-search-backward

# Sourcing to other files
source $ZSH/oh-my-zsh.sh
source /usr/local/bin/virtualenvwrapper.sh
source $HOME/.aliases
source $HOME/.functions
source $HOME/.exports

# Getting the names of the columns in a csv file (comma as separator)
names () {sed -e 's/,/\
/g;q'}

function gvim { /Applications/MacVim.app/Contents/MacOS/Vim -g $*; }