# Load the shell dotfiles, and then some:
# * ~/.path can be used to extend `$PATH`.
for file in ~/.{exports,aliases,functions}.zsh; do
  [ -r "$file" ] && [ -f "$file" ] && source "$file"
done
unset file

## load any env specific files here

# Antibody
source <(antibody init)
antibody bundle mafredri/zsh-async
antibody bundle zsh-users/zsh-completions
antibody bundle zsh-users/zsh-autosuggestions

antibody bundle sindresorhus/pure
antibody bundle zsh-users/zsh-syntax-highlighting
antibody bundle zsh-users/zsh-history-substring-search

# autocomplete
autoload -U compinit && compinit
zstyle ':completion:*' menu select
. <(npm completion)

autoload -U up-line-or-beginning-search
autoload -U down-line-or-beginning-search
zle -N up-line-or-beginning-search
zle -N down-line-or-beginning-search
bindkey "^[[A" up-line-or-beginning-search # Up
bindkey "^[[B" down-line-or-beginning-search # Down

# delete char with backspaces and delete
bindkey '^[[3~' delete-char
bindkey '^?' backward-delete-char
bindkey "^[[H" beginning-of-line
bindkey "^[[F" end-of-line
