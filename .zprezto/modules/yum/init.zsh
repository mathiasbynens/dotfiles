#
# Defines yum aliases.
#
# Authors:
#   Simon <contact@saimon.org>
#   Sorin Ionescu <sorin.ionescu@gmail.com>
#

# Return if requirements are not found.
if (( ! $+commands[yum] )); then
  return 1
fi

#
# Aliases
#

alias yumc='sudo yum clean all'    # Cleans the cache.
alias yumh='yum history'           # Displays history.
alias yumi='sudo yum install'      # Installs package(s).
alias yuml='yum list'              # Lists packages.
alias yumL='yum list installed'    # Lists installed packages.
alias yumq='yum info'              # Displays package information.
alias yumr='sudo yum remove'       # Removes package(s).
alias yums='yum search'            # Searches for a package.
alias yumu='sudo yum update'       # Updates packages.
alias yumU='sudo yum upgrade'      # Upgrades packages.
