[ -n "$PS1" ] && source ~/.bash_profile

source "$HOME/.rvm/scripts/rvm"
GIT_PS1_SHOWDIRTYSTATE=1
GIT_PS1_SHOWSTASHSTATE=1
GIT_PS1_SHOWUNTRACKEDFILES=1
PS1='\u@\h:\w$(__git_ps1 "[%s]" | sed "s/ //g")\$ '
