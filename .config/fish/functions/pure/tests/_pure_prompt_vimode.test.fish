source $current_dirname/../functions/_pure_prompt_vimode.fish

set --local empty ''

@test "_pure_prompt_vimode: hides vimode prompt by default" (
    _pure_prompt_vimode
) = $empty

@test "_pure_prompt_vimode: shows default vimode prompt" (
    set fish_key_bindings fish_vi_key_bindings

    _pure_prompt_vimode
    set fish_key_bindings fish_default_key_bindings
) = (set_color --bold --background red white)'[N] '(set_color normal)' '

