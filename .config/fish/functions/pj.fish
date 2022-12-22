function pj --wraps=git\ commit\ -a\ -m\ \'\(date\ +\%F\)\ -\ personal\ journal\ update\' --description alias\ pj=git\ commit\ -a\ -m\ \'\(date\ +\%F\)\ -\ personal\ journal\ update\'
    git commit -a -m (date +%F)\ \-\ personal\ journal\ update $argv
end
