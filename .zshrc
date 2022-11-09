#zmodload zsh/zprof

### Added by Zplugin's installer
ZINIT_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}/zinit/zinit.git"
source "${ZINIT_HOME}/zinit.zsh"
autoload -Uz _zinit
(( ${+_comps} )) && _comps[zplugin]=_zplugin
### End of Zplugin installer's chunk
 
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

ZSH_AUTOSUGGEST_STRATEGY=(history completion)
ZSH_AUTOSUGGEST_USE_ASYNC=1
ZSH_AUTOSUGGEST_BUFFER_MAX_SIZE=30

export PATH="/usr/local/opt/go@1.12/bin:$PATH"
export PATH="$HOME/go/bin:$PATH"
export PATH="$HOME/.yarn/bin:$HOME/.config/yarn/global/node_modules/.bin:$PATH"
export PATH="$HOME/.cargo/bin:$PATH"

_fzf_compgen_path() {
  fd --hidden --follow --exclude ".git" . "$1"
}

# Use fd to generate the list for directory completion
_fzf_compgen_dir() {
  fd --type d --hidden --follow --exclude ".git" . "$1"
}

zplugin ice "rupa/z" pick"z.sh"; zplugin light rupa/z

zplugin ice wait as"program" pick"bin/git-dsf"; zplugin light zdharma/zsh-diff-so-fancy
zplugin ice wait lucid; zplugin light zsh-users/zsh-autosuggestions
zplugin ice wait lucid; zplugin light zdharma/fast-syntax-highlighting
zplugin ice wait lucid; zplugin snippet OMZ::lib/history.zsh
zplugin ice wait lucid; zplugin snippet OMZ::lib/key-bindings.zsh 
zplugin ice wait lucid; zplugin snippet OMZ::plugins/sudo/sudo.plugin.zsh
zplugin ice wait lucid; zplugin snippet OMZ::plugins/kubectl/kubectl.plugin.zsh
zplugin ice wait lucid; zplugin snippet OMZ::plugins/git/git.plugin.zsh
zplugin ice wait lucid; zplugin snippet OMZ::plugins/vscode/vscode.plugin.zsh

zplugin ice from"gh-r" as"program"; zplugin load junegunn/fzf-bin
zplugin ice wait lucid multisrc"shell/{completion,key-bindings}.zsh" id-as"junegunn/fzf_completions" pick"/dev/null"; zplugin load junegunn/fzf

# FIXME: drop
zplugin ice wait lucid atinit"zpcompinit; zpcdreplay"; zplugin light jonmosco/kube-ps1

zplugin ice pick"async.zsh" src"pure.zsh"; zplugin light sindresorhus/pure

export WORDCHARS=""

for file in ~/.{exports,aliases,functions,extra}; do
    [ -r "$file" ] && source "$file"
done
unset file

#if [ /usr/local/bin/kubectl ]; then source <(kubectl completion zsh); fi

test -e ${HOME}/.iterm2_shell_integration.zsh && source ${HOME}/.iterm2_shell_integration.zsh

iterm2_print_user_vars() {
  KUBECONTEXT=$(CTX=$(kubectl config current-context) 2> /dev/null;if [ $? -eq 0 ]; then echo $CTX;fi)
  KUBENS=$(kubectl config view --minify --output 'jsonpath={..namespace}')
  iterm2_set_user_var kubeContext "${KUBECONTEXT}[${KUBENS}]"
}

# Load a few important annexes, without Turbo
# (this is currently required for annexes)
zinit light-mode for \
    zdharma-continuum/zinit-annex-as-monitor \
    zdharma-continuum/zinit-annex-bin-gem-node \
    zdharma-continuum/zinit-annex-patch-dl \
    zdharma-continuum/zinit-annex-rust

### End of Zinit's installer chunk
