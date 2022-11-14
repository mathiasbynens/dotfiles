# Defined in - @ line 1
function c --wraps=tr\ -d\ \'\\n\'\ \|\ xclip\ -sel\ clip --description alias\ c=tr\ -d\ \'\\n\'\ \|\ xclip\ -sel\ clip
  tr -d '\n' | xclip -sel clip $argv;
end
