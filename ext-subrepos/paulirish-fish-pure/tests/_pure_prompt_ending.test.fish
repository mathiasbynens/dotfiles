source $current_dirname/../functions/_pure_prompt_ending.fish

@test "_pure_prompt_ending: reset color to normal" (
    set pure_color_normal (set_color normal)
    
    _pure_prompt_ending
) = (set_color normal)' '

