# Add `~/bin` and brew folders to the `$PATH`
# and python's path: https://github.com/mxcl/homebrew/wiki/Homebrew-and-Python
export PATH="$HOME/.rvm/bin:/usr/local/bin:/usr/local/share/python:$HOME/Projects/myStash/bin:$HOME/npm-global/bin:$HOME/bin/node-tools:/usr/local/sbin:$(brew --prefix josegonzalez/php/php54)/bin:$HOME/Projects/libs/depot_tools:$HOME//Projects/libs/AWS-ElasticBeanstalk-CLI-2.5.1/eb/macosx/python2.7:$PATH"

export D8_PATH="$HOME/bin/node-tools"

# Python env
source /usr/local/bin/virtualenvwrapper.sh

# Run rvm
[[ -s "$HOME/.rvm/scripts/rvm" ]] && source "$HOME/.rvm/scripts/rvm"

# Run nvm node manager
# source ~/.nvm/nvm.sh
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" # This loads nvm

# Use 0.10
# nvm use 0.10

# Raise the limit of open files
ulimit -n 5000

# Load the shell dotfiles, and then some:
# * ~/.path can be used to extend `$PATH`.
# * ~/.extra can be used for other settings you don’t want to commit.
for file in ~/.{path,bash_prompt,exports,aliases,functions,extra}; do
	[ -r "$file" ] && source "$file"
done
unset file

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

# Prefer US English and use UTF-8
export LC_ALL="en_US.UTF-8"
export LANG="en_US"

# Add tab completion for SSH hostnames based on ~/.ssh/config, ignoring wildcards
[ -e "$HOME/.ssh/config" ] && complete -o "default" -o "nospace" -W "$(grep "^Host" ~/.ssh/config | grep -v "[?*]" | cut -d " " -f2)" scp sftp ssh

# Add tab completion for `defaults read|write NSGlobalDomain`
# You could just use `-g` instead, but I like being explicit
complete -W "NSGlobalDomain" defaults

# Add `killall` tab completion for common apps
complete -o "nospace" -W "Contacts Calendar Dock Finder Mail Safari iTunes SystemUIServer Terminal Twitter" killall

# If possible, add tab completion for many more commands
[ -f /etc/bash_completion ] && source /etc/bash_completion

# Run Z
. ~/Projects/libs/z/z.sh

# Git autocomplete
source ~/.git-completion.bash
