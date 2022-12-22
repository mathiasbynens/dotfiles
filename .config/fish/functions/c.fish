# Defined in /home/harmut01/.config/fish/functions/c.fish @ line 2
function c --wraps=tr\ -d\ \'\\n\'\ \|\ xclip\ -sel\ clip --description alias\ c=tr\ -d\ \'\\n\'\ \|\ xclip\ -sel\ clip
  tr -d '\n' | xclip -sel clip $argv;
end
