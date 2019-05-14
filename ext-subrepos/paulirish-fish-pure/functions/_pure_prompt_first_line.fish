function _pure_prompt_first_line \
    --description 'Print contextual information before prompt.'

    if not type -fq git  # exit if git is not available
        return 1
    end

    set --local prompt (_pure_print_prompt \
                            (_pure_prompt_ssh) \
                            (_pure_prompt_git) \
                            (_pure_prompt_command_duration)
                        )
    set --local prompt_width (_pure_string_width $prompt)
    set --local current_folder (_pure_prompt_current_folder $prompt_width)

    set --local prompt_components
    if test $pure_begin_prompt_with_current_directory = true
        set prompt_components \
                (_pure_prompt_current_folder $prompt_width) \
                (_pure_prompt_git) \
                (_pure_prompt_ssh) \
                (_pure_prompt_command_duration)
    else
        set prompt_components \
                (_pure_prompt_ssh) \
                (_pure_prompt_current_folder $prompt_width) \
                (_pure_prompt_git) \
                (_pure_prompt_command_duration)
    end

    echo (_pure_print_prompt $prompt_components)
end
