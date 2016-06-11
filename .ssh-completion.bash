_complete_ssh_hosts ()
{
  COMPREPLY=()
  cur="${COMP_WORDS[COMP_CWORD]}"
  comp_ssh_hosts=`[ -e ~/.ssh/known_hosts ] && \
                  cat ~/.ssh/known_hosts | \
                  cut -f 1 -d ' ' | \
                  sed -e s/,.*//g | \
                  grep -v ^# | \
                  uniq | \
                  grep -v "\[" ;
                  [ -e ~/.ssh/config ] && \
                  grep "^Host" ~/.ssh/config | \
                  grep -v "[?*]" | \
                  cut -d " " -f2- | \
                  tr ' ' '\n'
                 `
        COMPREPLY=( $(compgen -W "${comp_ssh_hosts}" -- $cur))
        return 0
}
complete -F _complete_ssh_hosts ssh sftp scp
