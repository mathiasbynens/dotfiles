local return_code="%(?..%{$fg[red]%}%? ↵%{$reset_color%})"

ZSH_THEME_GIT_PROMPT_PREFIX="%{$reset_color%}%{$fg[green]%}"
ZSH_THEME_GIT_PROMPT_SUFFIX="%{$reset_color%} "

ZSH_THEME_GIT_PROMPT_DIRTY="%{$fg[yellow]%}⚡%{$reset_color%}"
ZSH_THEME_GIT_PROMPT_CLEAN=""

ZSH_THEME_GIT_PROMPT_AHEAD="%{$fg[cyan]%}▴%{$reset_color%}"
ZSH_THEME_GIT_PROMPT_BEHIND="%{$fg[magenta]%}▾%{$reset_color%}"

ZSH_THEME_GIT_PROMPT_STAGED="%{$fg[green]%}•%{$reset_color%}"
ZSH_THEME_GIT_PROMPT_UNSTAGED="%{$fg[yellow]%}•%{$reset_color%}"
ZSH_THEME_GIT_PROMPT_UNTRACKED="%{$fg[red]%}•%{$reset_color%}"

ZSH_THEME_NVM_PROMPT_PREFIX="%{$FG[208]%}‹⬡ "
ZSH_THEME_NVM_PROMPT_SUFFIX="›%{$reset_color%}"


if [[ $EUID -eq 0 ]]; then
  _USERNAME="%{$fg_bold[red]%}%n"
else
  _USERNAME="%{$fg_bold[magenta]%}%n"
fi
_USERNAME="$_USERNAME%{$reset_color%}"


PROMPT='$_USERNAME%{$fg[cyan]%}@%{$reset_color%}%{$fg[yellow]%}%m%{$reset_color%}%{$fg[red]%}:%{$reset_color%}%{$fg[cyan]%}%0~%{$reset_color%}%{$fg[red]%}|%{$reset_color%}$(nvm_prompt_info)$(git_prompt_info)%{$fg[cyan]%}⇒%{$reset_color%}  '

RPS1="${return_code}"
