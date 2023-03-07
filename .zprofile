# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/bin" ] ; then
    export PATH="$HOME/bin:$PATH"
fi

# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/.local/bin" ] ; then
    PATH="$HOME/.local/bin:$PATH"
fi

# config pyenv if available
if [ -d "$HOME/.pyenv" ] ; then
	export PYENV_ROOT="$HOME/.pyenv"
	export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
fi

# config jenv if available
if [ -d "$HOME/.jenv" ] ; then
	export JENV_ROOT="$HOME/.jenv"
	export PATH="$JENV_ROOT/bin:$PATH"
fi

# set get-opt from gnu / Apache Airflow
if [ -d "$HOME/projects/airflow" ] ; then
	export PATH="/usr/local/opt/gnu-getopt/bin:$PATH"
fi

# config chruby if available
if [ -d "/usr/local/opt/chruby/share/chruby" ] ; then
	source /usr/local/opt/chruby/share/chruby/chruby.sh
	source /usr/local/opt/chruby/share/chruby/auto.sh
	eval "$(jenv init -)"
fi

# Load the shell dotfiles, and then some:
# * ~/.path can be used to extend `$PATH`.
# * ~/.extra can be used for other settings you don’t want to commit.
for file in ~/.{path,exports,aliases,functions,extra,variables}; do
	[ -r "$file" ] && [ -f "$file" ] && source "$file";
done;
unset file;

# Add tab completion for many Bash commands
if which brew &> /dev/null && [ -r "$(brew --prefix)/etc/profile.d/bash_completion.sh" ]; then
	# Ensure existing Homebrew v1 completions continue to work
	export BASH_COMPLETION_COMPAT_DIR="$(brew --prefix)/etc/bash_completion.d";
	source "$(brew --prefix)/etc/profile.d/bash_completion.sh";
elif [ -f /etc/bash_completion ]; then
	source /etc/bash_completion;
fi;
