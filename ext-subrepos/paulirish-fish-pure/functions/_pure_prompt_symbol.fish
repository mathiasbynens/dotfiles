function _pure_prompt_symbol \
    --description 'Print prompt symbol' \
    --argument-names exit_code

    set --local prompt_symbol (_pure_get_prompt_symbol)
    set --local command_succeed 0
    set --local color_symbol $pure_color_prompt_on_success # default pure symbol color
    if test $exit_code -ne $command_succeed
        set color_symbol $pure_color_prompt_on_error  # different pure symbol color when previous command failed

        if test "$pure_separate_prompt_on_error" = true
            set color_symbol "$pure_color_prompt_on_error$prompt_symbol$exit_code$pure_color_prompt_on_success"
        end
    end

    echo "$color_symbol$prompt_symbol"
end
