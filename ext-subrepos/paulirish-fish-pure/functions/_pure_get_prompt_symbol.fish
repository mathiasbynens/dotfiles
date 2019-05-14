function _pure_get_prompt_symbol \
    --description 'Print prompt symbol' \
    --argument-names exit_code

    set --local prompt_symbol $pure_symbol_prompt
    set --local is_vi_mode (string match -r "fish_(vi|hybrid)_key_bindings" $fish_key_bindings)
    if test -n "$is_vi_mode" \
            -a "$pure_reverse_prompt_symbol_in_vimode" = true \
            -a "$fish_bind_mode" != "insert"
        set prompt_symbol $pure_symbol_reverse_prompt
    end

    echo "$prompt_symbol"
end
