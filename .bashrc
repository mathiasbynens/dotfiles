[ -n "$PS1" ] && source ~/.bash_profile

# To set trap to intercept the non-zero return code of last program
EC() { echo -e '\e[1;33m'code $?'\e[m\n'; }
trap EC ERR

# This will change your title to the last command run, and make sure your history file is always up-to-date
export HISTCONTROL=ignoreboth
export HISTIGNORE='history*'
export PROMPT_COMMAND='history -a;echo -en "\e]2;";history 1|sed "s/^[ \t]*[0-9]\{1,\}  //g";echo -en "\e\\";'

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize

# Auto "cd" when entering just a path
shopt -s autocd