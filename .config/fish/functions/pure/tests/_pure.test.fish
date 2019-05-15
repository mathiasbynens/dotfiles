source $current_dirname/../functions/_pure_set_default.fish

set --local empty ''

@test "configure: pure_version"  (
    set --erase pure_version
    source $current_dirname/../conf.d/pure.fish
    echo $pure_version
) != $empty

@test "configure: _pure_fresh_session"  (
    set --erase _pure_fresh_session
    source $current_dirname/../conf.d/pure.fish
    echo $_pure_fresh_session
) = true

@test "configure: VIRTUAL_ENV_DISABLE_PROMPT"  (
    set --erase VIRTUAL_ENV_DISABLE_PROMPT
    source $current_dirname/../conf.d/pure.fish
    echo $VIRTUAL_ENV_DISABLE_PROMPT
) = 1

@test "configure: pure_symbol_prompt"  (
    set --erase pure_symbol_prompt
    source $current_dirname/../conf.d/pure.fish
    echo $pure_symbol_prompt
) = "❯"

@test "configure: pure_symbol_reverse_prompt"  (
    set --erase pure_symbol_reverse_prompt
    source $current_dirname/../conf.d/pure.fish
    echo $pure_symbol_reverse_prompt
) = "❮"

@test "configure: pure_reverse_prompt_symbol_in_vimode" (
        set --erase pure_reverse_prompt_symbol_in_vimode
        source $current_dirname/../conf.d/pure.fish
        echo $pure_reverse_prompt_symbol_in_vimode
    ) = true

@test "configure: pure_symbol_git_unpulled_commits"  (
    set --erase pure_symbol_git_unpulled_commits
    source $current_dirname/../conf.d/pure.fish
    echo $pure_symbol_git_unpulled_commits
) = "⇣"

@test "configure: pure_symbol_git_unpushed_commits"  (
    set --erase pure_symbol_git_unpushed_commits
    source $current_dirname/../conf.d/pure.fish
    echo $pure_symbol_git_unpushed_commits
) = "⇡"

@test "configure: pure_symbol_git_dirty"  (
    set --erase pure_symbol_git_dirty
    source $current_dirname/../conf.d/pure.fish
    echo $pure_symbol_git_dirty
) = "*"

@test "configure: pure_symbol_title_bar_separator"  (
    set --erase pure_symbol_title_bar_separator
    source $current_dirname/../conf.d/pure.fish
    echo $pure_symbol_title_bar_separator
) = "—"

@test "configure: pure_color_primary"  (
    set --erase pure_color_primary
    source $current_dirname/../conf.d/pure.fish
    echo $pure_color_primary
) = (set_color blue)

@test "configure: pure_color_info"  (
    set --erase pure_color_info
    source $current_dirname/../conf.d/pure.fish
    echo $pure_color_info
) = (set_color cyan)

@test "configure: pure_color_mute"  (
    set --erase pure_color_mute
    source $current_dirname/../conf.d/pure.fish
    echo $pure_color_mute
) = (set_color brblack)

@test "configure: pure_color_success"  (
    set --erase pure_color_success
    source $current_dirname/../conf.d/pure.fish
    echo $pure_color_success
) = (set_color magenta)

@test "configure: pure_color_normal"  (
    set --erase pure_color_normal
    source $current_dirname/../conf.d/pure.fish
    echo $pure_color_normal
) = (set_color normal)

@test "configure: pure_color_danger"  (
    set --erase pure_color_danger
    source $current_dirname/../conf.d/pure.fish
    echo $pure_color_danger
) = (set_color red)

@test "configure: pure_color_light"  (
    set --erase pure_color_light
    source $current_dirname/../conf.d/pure.fish
    echo $pure_color_light
) = (set_color white)

@test "configure: pure_color_warning"  (
    set --erase pure_color_warning
    source $current_dirname/../conf.d/pure.fish
    echo $pure_color_warning
) = (set_color yellow)

@test "configure: pure_color_command_duration"  (
    set --erase pure_color_command_duration
    source $current_dirname/../conf.d/pure.fish
    echo $pure_color_command_duration
) = (set_color yellow)

@test "configure: pure_color_current_directory"  (
    set --erase pure_color_current_directory
    source $current_dirname/../conf.d/pure.fish
    echo $pure_color_current_directory
) = (set_color blue)

@test "configure: pure_color_git_unpushed_commits"  (
    set --erase pure_color_git_unpushed_commits
    source $current_dirname/../conf.d/pure.fish
    echo $pure_color_git_unpushed_commits
) = (set_color cyan)

@test "configure: pure_color_git_unpulled_commits"  (
    set --erase pure_color_git_unpulled_commits
    source $current_dirname/../conf.d/pure.fish
    echo $pure_color_git_unpulled_commits
) = (set_color cyan)

@test "configure: pure_color_git_branch"  (
    set --erase pure_color_git_branch
    source $current_dirname/../conf.d/pure.fish
    echo $pure_color_git_branch
) = (set_color brblack)

@test "configure: pure_color_git_dirty"  (
    set --erase pure_color_git_dirty
    source $current_dirname/../conf.d/pure.fish
    echo $pure_color_git_dirty
) = (set_color brblack)

@test "configure: pure_color_ssh_hostname"  (
    set --erase pure_color_ssh_hostname
    source $current_dirname/../conf.d/pure.fish
    echo $pure_color_ssh_hostname
) = (set_color brblack)

@test "configure: pure_color_ssh_separator"  (
    set --erase pure_color_ssh_separator
    source $current_dirname/../conf.d/pure.fish
    echo $pure_color_ssh_separator
) = (set_color brblack)

@test "configure: pure_color_ssh_user_normal"  (
    set --erase pure_color_ssh_user_normal
    source $current_dirname/../conf.d/pure.fish
    echo $pure_color_ssh_user_normal
) = (set_color brblack)

@test "configure: pure_color_ssh_user_root"  (
    set --erase pure_color_ssh_user_root
    source $current_dirname/../conf.d/pure.fish
    echo $pure_color_ssh_user_root
) = (set_color white)

@test "configure: pure_color_prompt_on_error"  (
    set --erase pure_color_prompt_on_error
    source $current_dirname/../conf.d/pure.fish
    echo $pure_color_prompt_on_error
) = (set_color red)

@test "configure: pure_color_prompt_on_success"  (
    set --erase pure_color_prompt_on_success
    source $current_dirname/../conf.d/pure.fish
    echo $pure_color_prompt_on_success
) = (set_color magenta)

@test "configure: pure_color_virtualenv"  (
    set --erase pure_color_virtualenv
    source $current_dirname/../conf.d/pure.fish
    echo $pure_color_virtualenv
) = (set_color brblack)

@test "configure: pure_begin_prompt_with_current_directory"  (
    set --erase pure_begin_prompt_with_current_directory
    source $current_dirname/../conf.d/pure.fish
    echo $pure_begin_prompt_with_current_directory
) = true

@test "configure: pure_separate_prompt_on_error"  (
    set --erase pure_separate_prompt_on_error
    source $current_dirname/../conf.d/pure.fish
    echo $pure_separate_prompt_on_error
) = false

@test "configure: pure_threshold_command_duration"  (
    set --erase pure_threshold_command_duration
    source $current_dirname/../conf.d/pure.fish
    echo $pure_threshold_command_duration
) = 5

@test "configure: pure_right_prompt"  (
    set --erase pure_right_prompt
    source $current_dirname/../conf.d/pure.fish
    echo $pure_right_prompt
) = ""

@test "configure: pure_color_right_prompt"  (
    set --erase pure_color_right_prompt
    source $current_dirname/../conf.d/pure.fish
    echo $pure_color_right_prompt
) = (set_color normal)

