function _pure_prompt_vimode
    if test ! $pure_reverse_prompt_symbol_in_vimode
      echo (fish_default_mode_prompt)
    end
end
