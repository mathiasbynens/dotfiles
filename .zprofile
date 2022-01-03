# export VERBOSE="make some noise"
(( ${+VERBOSE} )) && echo -n ".zprofile ... "

# Load the shell dotfiles, and then some:
# * ~/.path can be used to extend `$PATH`.
# * ~/.extra can be used for other settings you don’t want to commit.
for file in ~/.{path,exports,functions,aliases,extra}; do
	[ -r "$file" ] && [ -f "$file" ] && source "$file";
done;
unset file;
export GPG_TTY=$(tty)

# Homebrew analytics
export HOMEBREW_NO_ANALYTICS=1

# Add pyenv executable to PATH and
# enable shims by adding the following
# to ~/.profile and ~/.zprofile:
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
(( $+commands[pyenv] )) && eval "$(pyenv init --path)"


# Cleanup up PATH, just in case you have added duplicate entries
export PATH=$( echo -n $PATH | awk -v RS=: '!($0 in a) {a[$0]; printf("%s%s", length(a) > 1 ? ":" : "", $0)}' )