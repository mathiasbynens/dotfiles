#
# Loads the Node Version Manager and enables npm completion.
#
# Authors:
#   Sorin Ionescu <sorin.ionescu@gmail.com>
#   Zeh Rizzatti <zehrizzatti@gmail.com>
#

# Load manually installed NVM into the shell session.
if [[ -s "$HOME/.nvm/nvm.sh" ]]; then
  source "$HOME/.nvm/nvm.sh"

# Load package manager installed NVM into the shell session.
elif (( $+commands[brew] )) && [[ -d "$(brew --prefix nvm 2>/dev/null)" ]]; then
  source $(brew --prefix nvm)/nvm.sh

# Return if requirements are not found.
elif (( ! $+commands[node] )); then
  return 1
fi

# Load NPM completion.
if (( $+commands[npm] )); then
  cache_file="${0:h}/cache.zsh"

  if [[ "$commands[npm]" -nt "$cache_file" || ! -s "$cache_file" ]]; then
    # npm is slow; cache its output.
    npm completion >! "$cache_file" 2> /dev/null
  fi

  source "$cache_file"

  unset cache_file
fi
