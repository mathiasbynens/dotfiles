#
# Sets terminal window and tab titles.
#
# Authors:
#   Sorin Ionescu <sorin.ionescu@gmail.com>
#

# Return if requirements are not found.
if [[ "$TERM" == (dumb|linux|*bsd*|eterm*) ]]; then
  return 1
fi

# Sets the terminal or terminal multiplexer window title.
function set-window-title {
  local title_format{,ted}
  zstyle -s ':prezto:module:terminal:window-title' format 'title_format' || title_format="%s"
  zformat -f title_formatted "$title_format" "s:$argv"

  if [[ "$TERM" == screen* ]]; then
    title_format="\ek%s\e\\"
  else
    title_format="\e]2;%s\a"
  fi

  printf "$title_format" "${(V%)title_formatted}"
}

# Sets the terminal tab title.
function set-tab-title {
  local title_format{,ted}
  zstyle -s ':prezto:module:terminal:tab-title' format 'title_format' || title_format="%s"
  zformat -f title_formatted "$title_format" "s:$argv"

  printf "\e]1;%s\a" ${(V%)title_formatted}
}

# Sets the tab and window titles with a given command.
function _terminal-set-titles-with-command {
  emulate -L zsh
  setopt EXTENDED_GLOB

  # Get the command name that is under job control.
  if [[ "${2[(w)1]}" == (fg|%*)(\;|) ]]; then
    # Get the job name, and, if missing, set it to the default %+.
    local job_name="${${2[(wr)%*(\;|)]}:-%+}"

    # Make a local copy for use in the subshell.
    local -A jobtexts_from_parent_shell
    jobtexts_from_parent_shell=(${(kv)jobtexts})

    jobs "$job_name" 2>/dev/null > >(
      read index discarded
      # The index is already surrounded by brackets: [1].
      _terminal-set-titles-with-command "${(e):-\$jobtexts_from_parent_shell$index}"
    )
  else
    # Set the command name, or in the case of sudo or ssh, the next command.
    local cmd="${${2[(wr)^(*=*|sudo|ssh|-*)]}:t}"
    local truncated_cmd="${cmd/(#m)?(#c15,)/${MATCH[1,12]}...}"
    unset MATCH

    set-window-title "$cmd"
    set-tab-title "$truncated_cmd"
  fi
}

# Sets the tab and window titles with a given path.
function _terminal-set-titles-with-path {
  emulate -L zsh
  setopt EXTENDED_GLOB

  local absolute_path="${${1:a}:-$PWD}"
  local abbreviated_path="${absolute_path/#$HOME/~}"
  local truncated_path="${abbreviated_path/(#m)?(#c15,)/...${MATCH[-12,-1]}}"
  unset MATCH

  set-window-title "$abbreviated_path"
  set-tab-title "$truncated_path"
}

# Do not override precmd/preexec; append to the hook array.
autoload -Uz add-zsh-hook

# Set up the Apple Terminal.
if [[ "$TERM_PROGRAM" == 'Apple_Terminal' ]] \
  && ( ! [[ -n "$STY" || -n "$TMUX" || -n "$DVTM" ]] )
then
  # Sets the Terminal.app current working directory before the prompt is
  # displayed.
  function _terminal-set-terminal-app-proxy-icon {
    printf '\e]7;%s\a' "file://${HOST}${PWD// /%20}"
  }
  add-zsh-hook precmd _terminal-set-terminal-app-proxy-icon

  # Unsets the Terminal.app current working directory when a terminal
  # multiplexer or remote connection is started since it can no longer be
  # updated, and it becomes confusing when the directory displayed in the title
  # bar is no longer synchronized with real current working directory.
  function _terminal-unset-terminal-app-proxy-icon {
    if [[ "${2[(w)1]:t}" == (screen|tmux|dvtm|ssh|mosh) ]]; then
      print '\e]7;\a'
    fi
  }
  add-zsh-hook preexec _terminal-unset-terminal-app-proxy-icon

  # Do not set the tab and window titles in Terminal.app since it sets the tab
  # title to the currently running process by default and the current working
  # directory is set separately.
  return
fi

# Set up non-Apple terminals.
if zstyle -t ':prezto:module:terminal' auto-title \
  && ( ! [[ -n "$STY" || -n "$TMUX" ]] )
then
  # Sets the tab and window titles before the prompt is displayed.
  add-zsh-hook precmd _terminal-set-titles-with-path

  # Sets the tab and window titles before command execution.
  add-zsh-hook preexec _terminal-set-titles-with-command
fi
