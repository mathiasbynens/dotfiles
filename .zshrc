# Path to your oh-my-zsh configuration.
export ZSH=$HOME/.oh-my-zsh
ZSH_THEME="my"

plugins=(git z osx zsh-autosuggestions vscode alias-tips zsh-completions kubectl)

export ZSH_PLUGINS_ALIAS_TIPS_TEXT='💡 '
export NVM_AUTO_USE=true

source $ZSH/oh-my-zsh.sh

export PATH=~/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/bin:/usr/sbin:/sbin:/usr/X11/bin:/usr/local/git/bin

test -e ${HOME}/.iterm2_shell_integration.zsh && source ${HOME}/.iterm2_shell_integration.zsh

for file in ~/.{exports,aliases,functions,extra}; do
    [ -r "$file" ] && source "$file"
done
unset file

autoload -U promptinit; promptinit
prompt pure

if [ /usr/local/bin/kubectl ]; then source <(kubectl completion zsh); fi

KUBE_PS1_PREFIX=""
KUBE_PS1_SUFFIX=""
KUBE_PS1_SEPARATOR=""
source "/usr/local/opt/kube-ps1/share/kube-ps1.sh"
PS1='$(kube_ps1) '$PS1

ZSH_HIGHLIGHT_HIGHLIGHTERS=(main brackets pattern cursor root)
ZSH_HIGHLIGHT_STYLES[root]='bg=red'
source /usr/local/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
