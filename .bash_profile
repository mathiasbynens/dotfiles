# Add `~/bin` to the `$PATH`
export PATH="$HOME/bin:$PATH"

if [ -x /usr/libexec/path_helper ]; then
	eval `/usr/libexec/path_helper -s`
fi

# Load the shell dotfiles, and then some:
# * ~/.system can be used to ready in a /etc/bashrc or something like that ex:
# if [ -f /etc/bashrc ]; then
#     . /etc/bashrc
# fi

# * ~/.path can be used to extend `$PATH`.
# * ~/.extra can be used for other settings you don’t want to commit.
for file in ~/.{system,path,bash_prompt,exports,aliases,functions,extra}; do
	[ -r "$file" ] && [ -f "$file" ] && source "$file"
done
unset file

# Default file perms
umask 002

#Add some vi mode defaults
set -o vi
bind -m vi-insert '"\e."':insert-last-argument

# Case-insensitive globbing (used in pathname expansion)
shopt -s nocaseglob

# Append to the Bash history file, rather than overwriting it
shopt -s histappend

# Autocorrect typos in path names when using `cd`
shopt -s cdspell

# Enable some Bash 4 features when possible:
# * `autocd`, e.g. `**/qux` will enter `./foo/bar/baz/qux`
# * Recursive globbing, e.g. `echo **/*.txt`
for option in autocd globstar; do
	shopt -s "$option" 2> /dev/null
done

# enable programmable completion features for debian style systems
if [ -f /etc/bash_completion ]; then
  . /etc/bash_completion
fi

# enable plenv if available
if which plenv &> /dev/null; then eval "$(plenv init -)"; fi

# Add tab completion for many Bash commands
if which brew &> /dev/null && [ -f "$(brew --prefix)/etc/bash_completion" ]; then
	source "$(brew --prefix)/etc/bash_completion"
fi

# add updated gnu commands to path on OS X if coreutils is installed
# if which brew &> /dev/null && [ -d "$(brew --prefix coreutils)/libexec/gnubin" ]; then
#     export PATH="$(brew --prefix coreutils)/libexec/gnubin: $PATH"
# fi

# Enable tab completion for `g` by marking it as an alias for `git`
if type _git &> /dev/null && [ -f /usr/local/etc/bash_completion.d/git-completion.bash ]; then
	complete -o default -o nospace -F _git g
fi

# Add tab completion for SSH hostnames based on ~/.ssh/config, ignoring wildcards
[ -e "$HOME/.ssh/config" ] && complete -o "default" -o "nospace" -W "$(grep "^Host" ~/.ssh/config | grep -v "[?*]" | cut -d " " -f2 | tr ' ' '\n')" scp sftp ssh

# Add iTerm integrations if available
test -e "${HOME}/.iterm2_shell_integration.bash" && source "${HOME}/.iterm2_shell_integration.bash"

# Add fzf integration
[ -f ~/.fzf.bash  ] && source ~/.fzf.bash
export FZF_DEFAULT_COMMAND='rg --files --hidden --glob "!.git"'
export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"

# Start tmux on ssh logins (zsh_custom/ssh-agent.zsh sets up the ssh agent)
# export NO_TMUX=1 in ~/.system or ~/.extra if you don't want to automatically start tmux
if [ -z "$NO_TMUX"  ] && [ -z "$TMUX"  ]; then
    # we're not in a tmux session

    if [ ! -z "$SSH_TTY" ]; then
        # We logged in via SSH

        # start tmux (boo, only works this way with tmux 2.0)
        tmux new-session -A -s main
    fi
fi

