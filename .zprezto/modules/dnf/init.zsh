#
# Defines dnf aliases.
#
# Authors:
#   FireWave <firewave@free.fr>
#   Sorin Ionescu <sorin.ionescu@gmail.com>
#

# Return if requirements are not found.
if (( ! $+commands[dnf] )); then
  return 1
fi

#
# Aliases
#

alias dnfc='sudo dnf clean all'    # Cleans the cache.
alias dnfh='dnf history'           # Displays history.
alias dnfi='sudo dnf install'      # Installs package(s).
alias dnfl='dnf list'              # Lists packages.
alias dnfL='dnf list installed'    # Lists installed packages.
alias dnfq='dnf info'              # Displays package information.
alias dnfr='sudo dnf remove'       # Removes package(s).
alias dnfs='dnf search'            # Searches for a package.
alias dnfu='sudo dnf update'       # Updates packages.
alias dnfU='sudo dnf upgrade'      # Upgrades packages.

