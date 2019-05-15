function _pure_prompt_command_duration
    set --local command_duration

    # Get command execution duration
    if test -n "$CMD_DURATION"
        set command_duration (_pure_format_time $CMD_DURATION $pure_threshold_command_duration)
    end
    set --local command_duration_color "$pure_color_command_duration"

    echo "$command_duration_color$command_duration"
end
