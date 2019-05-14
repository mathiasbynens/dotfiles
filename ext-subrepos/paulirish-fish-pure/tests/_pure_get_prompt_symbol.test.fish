source $current_dirname/../functions/_pure_get_prompt_symbol.fish

function setup
    set --global pure_symbol_prompt '❯'
    set --global pure_symbol_reverse_prompt '❮'
end

function teardown
    set fish_key_bindings fish_default_key_bindings
    set fish_bind_mode 'default'
end

@test "_pure_get_prompt_symbol: get default symbol ❯" (
    set pure_reverse_prompt_symbol_in_vimode false

    _pure_get_prompt_symbol
) = '❯'

@test "_pure_get_prompt_symbol: get default symbol ❯ when key binding is default" (
    set pure_reverse_prompt_symbol_in_vimode true
    set fish_bind_mode 'insert'
    set fish_key_bindings 'fish_default_key_bindings'

    _pure_get_prompt_symbol
) = '❯'

@test "_pure_get_prompt_symbol: get default symbol ❯ when bind mode is default" (
    set pure_reverse_prompt_symbol_in_vimode true
    set fish_key_bindings 'fish_default_key_bindings'
    set fish_bind_mode 'default'

    _pure_get_prompt_symbol
) = '❯'

@test "_pure_get_prompt_symbol: get reverse symbol ❮ when VI key binding and not in insert mode" (
    set pure_reverse_prompt_symbol_in_vimode true
    set fish_bind_mode 'default'
    set fish_key_bindings 'fish_vi_key_bindings'

    _pure_get_prompt_symbol
) = '❮'

@test "_pure_get_prompt_symbol: get reverse symbol ❮ when hybrid key binding and not in insert mode" (
    set pure_reverse_prompt_symbol_in_vimode true
    set fish_bind_mode 'default'
    set fish_key_bindings 'fish_hybrid_key_bindings'

    _pure_get_prompt_symbol
) = '❮'
