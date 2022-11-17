#zmodload zsh/zprof

### Added by Zinit's installer
if [[ ! -f $HOME/.local/share/zinit/zinit.git/zinit.zsh ]]; then
    print -P "%F{33} %F{220}Installing %F{33}ZDHARMA-CONTINUUM%F{220} Initiative Plugin Manager (%F{33}zdharma-continuum/zinit%F{220})…%f"
    command mkdir -p "$HOME/.local/share/zinit" && command chmod g-rwX "$HOME/.local/share/zinit"
    command git clone https://github.com/zdharma-continuum/zinit "$HOME/.local/share/zinit/zinit.git" && \
        print -P "%F{33} %F{34}Installation successful.%f%b" || \
        print -P "%F{160} The clone has failed.%f%b"
fi

source "$HOME/.local/share/zinit/zinit.git/zinit.zsh"
autoload -Uz _zinit
(( ${+_comps} )) && _comps[zinit]=_zinit
 
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

export PATH="$HOME/go/bin:$PATH"
export PATH="$HOME/.cargo/bin:$PATH"

_fzf_compgen_path() {
  fd --hidden --follow --exclude ".git" . "$1"
}

# Use fd to generate the list for directory completion
_fzf_compgen_dir() {
  fd --type d --hidden --follow --exclude ".git" . "$1"
}

zplugin ice "rupa/z" pick"z.sh"; zplugin light rupa/z

zplugin ice wait as"program" pick"bin/git-dsf"; zplugin light zdharma-continuum/zsh-diff-so-fancy
zplugin ice wait lucid; zplugin light zsh-users/zsh-autosuggestions
zplugin ice wait lucid; zplugin light zdharma-continuum/fast-syntax-highlighting
zplugin ice wait lucid; zplugin snippet OMZ::lib/history.zsh
zplugin ice wait lucid; zplugin snippet OMZ::lib/key-bindings.zsh 
zplugin ice wait lucid; zplugin snippet OMZ::plugins/sudo/sudo.plugin.zsh
zplugin ice wait lucid; zplugin snippet OMZ::plugins/kubectl/kubectl.plugin.zsh
zplugin ice wait lucid; zplugin snippet OMZ::plugins/git/git.plugin.zsh
zplugin ice wait lucid; zplugin snippet OMZ::plugins/vscode/vscode.plugin.zsh

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
