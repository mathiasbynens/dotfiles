function _pure_prompt_git_dirty
    set --local git_dirty_symbol
    set --local git_dirty_color

    set --local is_git_dirty (command git status --porcelain --untracked=no --ignore-submodules 2>/dev/null)
    if test -n "$is_git_dirty"  # un-commited files
        set git_dirty_symbol "$pure_symbol_git_dirty"
        set git_dirty_color "$pure_color_git_dirty"
    end

    echo "$git_dirty_color$git_dirty_symbol"
end
