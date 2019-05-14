source $current_dirname/../functions/_pure_format_time.fish
source $current_dirname/../functions/_pure_prompt_command_duration.fish

set --local empty ''

@test "_pure_prompt_command_duration: hide command duration when it's zero" (
    set CMD_DURATION $empty
    set pure_color_command_duration $empty

    _pure_prompt_command_duration
) = $empty

@test "_pure_prompt_command_duration: displays command duration when non-zero" (
    set CMD_DURATION 6000 # in milliseconds
    set pure_threshold_command_duration 5 # in seconds
    set pure_color_command_duration $empty

    _pure_prompt_command_duration
) = '6s'

