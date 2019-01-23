# Path to your oh-my-zsh installation.
export ZSH=$HOME/.oh-my-zsh

ZSH_THEME=""

plugins=(git z osx vscode alias-tips kubectl)

fpath=(/usr/local/share/zsh-completions $fpath)

#autoload -U compinit && compinit

export ZSH_PLUGINS_ALIAS_TIPS_TEXT='💡 '
export NVM_AUTO_USE=true

source $ZSH/oh-my-zsh.sh

export PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/bin:/usr/sbin:/sbin:/usr/X11/bin

test -e ${HOME}/.iterm2_shell_integration.zsh && source ${HOME}/.iterm2_shell_integration.zsh

for file in ~/.{exports,aliases,functions,extra}; do
    [ -r "$file" ] && source "$file"
done
unset file

#ZPLUG_SUDO_PASSWORD=""
#zplug "jhawthorn/fzy", as:command, rename-to:fzy, hook-build:"make && sudo make install"
#zplug "b4b4r07/enhancd", use:init.sh

#zplug "zsh-users/zsh-history-substring-search"


#if zplug check b4b4r07/enhancd; then
#    export ENHANCD_FILTER=fzy:fzf-tmux:peco
#fi

autoload -U promptinit; promptinit
prompt pure

if [ /usr/local/bin/kubectl ]; then source <(kubectl completion zsh); fi

KUBE_PS1_PREFIX=""
KUBE_PS1_SUFFIX=""
KUBE_PS1_SEPARATOR=""
source "/usr/local/opt/kube-ps1/share/kube-ps1.sh"
PS1='$(kube_ps1) '$PS1

ZSH_AUTOSUGGEST_STRATEGY=(match_prev_cmd history)
source /usr/local/share/zsh-autosuggestions/zsh-autosuggestions.zsh
bindkey '^[end' autosuggest-accept

ZSH_HIGHLIGHT_HIGHLIGHTERS=(main brackets pattern cursor root)
#ZSH_HIGHLIGHT_STYLES[root]='bg=red'
source /usr/local/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

