source $current_dirname/../functions/_pure_prompt.fish
source $current_dirname/../functions/_pure_prompt_virtualenv.fish
source $current_dirname/../functions/_pure_prompt_vimode.fish
source $current_dirname/../functions/_pure_prompt_symbol.fish
source $current_dirname/../functions/_pure_get_prompt_symbol.fish
source $current_dirname/../functions/_pure_print_prompt.fish
source $current_dirname/../functions/_pure_string_width.fish

set --local failed 1
set --local succeed 0

@test "_pure_prompt: print prompt after succeeding command" (
    set pure_color_prompt_on_success (set_color magenta)
    set pure_symbol_prompt '>'  # using default ❯ break following tests
    set --local last_command $succeed

    _pure_prompt $last_command
) = (set_color magenta)'>'

@test "_pure_prompt: print prompt after failing command" (
    set pure_color_prompt_on_error (set_color red)
    set pure_symbol_prompt '>'  # using default ❯ break following tests
    set --local last_command $failed

    _pure_prompt $last_command
) = (set_color red)'>'

