#
# Configures Emacs dependency management.
#
# Authors: Sebastian Wiesner <lunaryorn@gmail.com>
#

# Return if requirements are not found.
if [[ ! -d "$HOME/.cask" ]]; then
  return 1
fi

# Prepend Cask bin directory.
path=($HOME/.cask/bin $path)

# Load Carton completion
source "$HOME/.cask/etc/cask_completion.zsh" 2> /dev/null

#
# Aliases
#

alias cai='cask install'
alias cau='cask update'
alias caI='cask init'
alias cae='cask exec'
