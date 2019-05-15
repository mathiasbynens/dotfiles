function scmpuff_clear_vars
    set -l scmpuff_env_char "e"
    set -l scmpuff_env_vars (set -x | awk '{print $1}' | grep -E '^'$scmpuff_env_char'\d+')

    for v in $scmpuff_env_vars
        set -e $v
    end
end
