# oh-my-zsh Theme
# Default robbyrussell theme with node version info.
# Installation: place this file in .oh-my-zsh/custom/themes/robbyrussell.zsh_theme

function node_version {
	local v=$(node -v | sed 's/\..*//' | sed 's/v//');
	echo $v
}

function node_prompt_version {
    if which node &> /dev/null; then
        echo "%{$fg_bold[green]%}node$(node_version) %{$reset_color%}"
    fi
}

local ret_status="%(?:%{$fg_bold[green]%}➜ :%{$fg_bold[red]%}➜ )"
PROMPT='${ret_status} %{$fg[cyan]%}%c%{$reset_color%} $(node_prompt_version)$(git_prompt_info)'

ZSH_THEME_GIT_PROMPT_PREFIX="%{$fg_bold[blue]%}git:(%{$fg[red]%}"
ZSH_THEME_GIT_PROMPT_SUFFIX="%{$reset_color%} "
ZSH_THEME_GIT_PROMPT_DIRTY="%{$fg[blue]%}) %{$fg[yellow]%}✗"
ZSH_THEME_GIT_PROMPT_CLEAN="%{$fg[blue]%})"
