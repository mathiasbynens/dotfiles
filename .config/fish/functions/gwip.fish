# Defined in - @ line 1
function gwip --wraps=git\ commit\ -a\ -m\ \'work\ in\ progress\ -\ fixup\' --description alias\ gwip=git\ commit\ -a\ -m\ \'work\ in\ progress\ -\ fixup\'
  git commit -a -m 'work in progress - fixup' $argv;
end
