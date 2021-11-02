# Only source ~/.bash_profile if interactive shell
# Provide some extra PATH locations for things using a non-interactive shell
# such as git-annex, mosh, and rsync via homebrew.

if [[ -n "$PS1" ]] ; then
	source ~/.bash_profile
elif
	PATH=$HOME/bin:/usr/local/bin:/opt/homebrew/bin:$PATH
	return
fi
