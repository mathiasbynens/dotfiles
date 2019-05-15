source $current_dirname/../fish_right_prompt.fish

set --local empty ''

@test "fish_right_prompt: succeed" (
    fish_right_prompt 2>&1 >/dev/null
) $status -eq 0

@test "fish_right_prompt: prints $pure_color_right_prompt" (
    set pure_right_prompt "🐙"  # U+1F419 OCTOPUS
    set pure_color_right_prompt $empty
    set pure_color_normal $empty

    fish_right_prompt
) = '🐙'

@test "fish_right_prompt: prints colorful right_prompt" (
    set pure_right_prompt "🐬"  # U+1F42C DOLPHIN
    set pure_color_right_prompt (set_color blue)
    set pure_color_normal (set_color normal)

    fish_right_prompt
) = (set_color blue)'🐬'(set_color normal)
