#
# A monochrome theme that displays basic information.
#
# Authors:
#   Brian Tse <briankftse@gmail.com>
#   Sorin Ionescu <sorin.ionescu@gmail.com>
#
# Screenshots:
#   http://i.imgur.com/zLZNK.png
#

function +vi-git_status {
  # Check for untracked files or updated submodules since vcs_info does not.
  if [[ -n $(git ls-files --other --exclude-standard 2> /dev/null) ]]; then
    hook_com[unstaged]='%F{red}●%f'
  fi
}

function prompt_minimal_precmd {
  vcs_info
}

function prompt_minimal_setup {
  setopt LOCAL_OPTIONS
  unsetopt XTRACE KSH_ARRAYS
  prompt_opts=(cr percent subst)

  # Load required functions.
  autoload -Uz add-zsh-hook
  autoload -Uz vcs_info

  # Add hook for calling vcs_info before each command.
  add-zsh-hook precmd prompt_minimal_precmd

  # Set vcs_info parameters.
  zstyle ':vcs_info:*' enable bzr git hg svn
  zstyle ':vcs_info:*' check-for-changes true
  zstyle ':vcs_info:*' stagedstr '%F{green}●%f'
  zstyle ':vcs_info:*' unstagedstr '%F{yellow}●%f'
  zstyle ':vcs_info:*' formats ' - [%b%c%u]'
  zstyle ':vcs_info:*' actionformats " - [%b%c%u|%F{cyan}%a%f]"
  zstyle ':vcs_info:(sv[nk]|bzr):*' branchformat '%b|%F{cyan}%r%f'
  zstyle ':vcs_info:git*+set-message:*' hooks git_status

  # Define prompts.
  PROMPT='%2~${vcs_info_msg_0_} » '
  RPROMPT=''
}

prompt_minimal_setup "$@"
