#
# Enables local Haskell package installation.
#
# Authors:
#   Sebastian Wiesner <lunaryorn@googlemail.com>
#

# Return if requirements are not found.
if (( ! $+commands[ghc] )); then
  return 1
fi

# Prepend Cabal per user directories to PATH.
if [[ "$OSTYPE" == darwin* && -d $HOME/Library/Haskell ]]; then
  path=($HOME/Library/Haskell/bin(/N) $path)
else
  path=($HOME/.cabal/bin(/N) $path)
fi
