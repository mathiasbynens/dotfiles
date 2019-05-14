function _pure_prompt_virtualenv --description "Display virtualenv directory"
    if test -n "$VIRTUAL_ENV"
        set --local virtualenv (basename "$VIRTUAL_ENV")
        set --local virtualenv_color "$pure_color_virtualenv"

        echo "$virtualenv_color$virtualenv"
    end
end
