source $current_dirname/../functions/_pure_prompt_ssh_separator.fish

@test "_pure_prompt_ssh_separator: display at symbol" (
    set pure_color_ssh_separator ""

    _pure_prompt_ssh_separator
) = '@'

@test "_pure_prompt_ssh_separator: display colored at symbol" (
    set pure_color_ssh_separator (set_color grey)

    _pure_prompt_ssh_separator
) = (set_color grey)'@'

