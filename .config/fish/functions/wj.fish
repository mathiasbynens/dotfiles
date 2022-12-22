function wj --wraps=git\ commit\ -a\ -m\ \'\(date\ +\%F\)\ -\ work\ journal\ update\' --wraps='git commit -a -m "(date +%F) - work journal update"' --description 'alias wj=git commit -a -m "(date +%F) - work journal update"'
    git commit -a -m (date +%F)\ \-\ work\ journal\ update $argv
end
