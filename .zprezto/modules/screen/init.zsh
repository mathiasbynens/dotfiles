#
# Defines GNU Screen aliases and provides for auto launching it at start-up.
#
# Authors:
#   Sorin Ionescu <sorin.ionescu@gmail.com>
#   Georges Discry <georges@discry.be>
#

# Return if requirements are not found.
if (( ! $+commands[screen] )); then
  return 1
fi

#
# Auto Start
#

if [[ -z "$STY" && -z "$EMACS" && -z "$VIM" ]] && ( \
  ( [[ -n "$SSH_TTY" ]] && zstyle -t ':prezto:module:screen:auto-start' remote ) ||
  ( [[ -z "$SSH_TTY" ]] && zstyle -t ':prezto:module:screen:auto-start' local ) \
); then
  session="$(
    screen -list 2> /dev/null \
      | sed '1d;$d' \
      | awk '{print $1}' \
      | head -1)"

  if [[ -n "$session" ]]; then
    exec screen -x "$session"
  else
    exec screen -a -A -U -D -R -m "$SHELL" -l
  fi
fi

#
# Aliases
#

alias scr='screen'
alias scrl='screen -list'
alias scrn='screen -U -S'
alias scrr='screen -a -A -U -D -R'
