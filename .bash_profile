# Load ~/.bash_prompt, ~/.exports, ~/.aliases, ~/.functions and ~/.extra
# ~/.extra can be used for settings you don’t want to commit
for file in bash_prompt exports aliases functions extra; do
  file="$HOME/.$file"
  [ -e "$file" ] && source "$file"
done

# Case-insensitive globbing (used in pathname expansion)
shopt -s nocaseglob

#  auto complete ssh host names (the crap between ` and ` just has to be a list... you could just make a list of hosts....
complete -W "$(echo `grep ^Host ~/.ssh/config |sed -e 's/Host //g'| grep -v "*"`;)" ssh

