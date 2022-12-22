function gwip --wraps=git\ commit\ -a\ -m\ \'work\ in\ progress\ -\ fixup\' --description alias\ gwip=git\ commit\ -a\ -m\ \'work\ in\ progress\ -\ fixup\'
    git commit -an -m 'work in progress - fixup' $argv
end
