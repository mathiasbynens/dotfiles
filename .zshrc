#zmodload zsh/zprof

### Added by Zplugin's installer
source '/Users/artem/.zplugin/bin/zplugin.zsh'
autoload -Uz _zplugin
(( ${+_comps} )) && _comps[zplugin]=_zplugin
### End of Zplugin installer's chunk

export ZSH_PLUGINS_ALIAS_TIPS_TEXT='💡 '

export PATH=/usr/local/bin:/usr/local/sbin:/usr/bin:/bin:/usr/sbin:/sbin

# https://github.com/zsh-users/zsh-autosuggestions/issues/303#issuecomment-361814419
#if [[ "${terminfo[kcuu1]}" != "" ]]; then
#  autoload -U up-line-or-beginning-search
#  zle -N up-line-or-beginning-search
#  bindkey "${terminfo[kcuu1]}" up-line-or-beginning-search
#fi

#if [[ "${terminfo[kcud1]}" != "" ]]; then
#  autoload -U down-line-or-beginning-search
#  zle -N down-line-or-beginning-search
#  bindkey "${terminfo[kcud1]}" down-line-or-beginning-search
#fi

KUBE_PS1_PREFIX=""
KUBE_PS1_SUFFIX=""
KUBE_PS1_SEPARATOR=""
PS1='$(kube_ps1) '$PS1

ZSH_AUTOSUGGEST_STRATEGY=(history completion)
ZSH_AUTOSUGGEST_USE_ASYNC=1
ZSH_AUTOSUGGEST_BUFFER_MAX_SIZE=30

export PATH="/usr/local/opt/go@1.12/bin:$PATH"
export PATH="$HOME/go/bin:$PATH"
export PATH="$HOME/.yarn/bin:$HOME/.config/yarn/global/node_modules/.bin:$PATH"

zplugin ice from"gh-r" as"program"; zplugin load junegunn/fzf-bin
zplugin ice multisrc'shell/{completion,key-bindings}.zsh'; zplugin load junegunn/fzf

zplugin ice "rupa/z" pick"z.sh"; zplugin light rupa/z

zplugin ice wait as"program" pick"bin/git-dsf"; zplugin light zdharma/zsh-diff-so-fancy
zplugin ice wait lucid; zplugin light zsh-users/zsh-autosuggestions
zplugin ice wait lucid; zplugin light zdharma/fast-syntax-highlighting
zplugin ice wait lucid; zplugin snippet OMZ::lib/key-bindings.zsh 
zplugin ice wait lucid; zplugin snippet OMZ::plugins/git/git.plugin.zsh
zplugin ice wait lucid; zplugin snippet OMZ::plugins/vscode/vscode.plugin.zsh

zplugin ice wait lucid atinit"zpcompinit; zpcdreplay"; zplugin light jonmosco/kube-ps1

zplugin ice pick"async.zsh" src"pure.zsh"; zplugin light sindresorhus/pure

for file in ~/.{exports,aliases,functions,extra}; do
    [ -r "$file" ] && source "$file"
done
unset file

#if [ /usr/local/bin/kubectl ]; then source <(kubectl completion zsh); fi

#test -e ${HOME}/.iterm2_shell_integration.zsh && source ${HOME}/.iterm2_shell_integration.zsh
