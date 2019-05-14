function _pure_prompt_git_pending_commits
    set --local git_unpushed_commits
    set --local git_unpulled_commits

    set --local has_upstream (command git rev-parse --abbrev-ref '@{upstream}' 2>/dev/null)
    if test -n "$has_upstream"  # check there is an upstream repo configured
        command git rev-list --left-right --count 'HEAD...@{upstream}' \
        | read --local --array git_status
        set --local commit_to_push $git_status[1]
        set --local commit_to_pull $git_status[2]

        if test $commit_to_push -gt 0  # upstream is behind local repo
            set git_unpushed_commits "$pure_color_git_unpushed_commits$pure_symbol_git_unpushed_commits"
        end

        if test $commit_to_pull -gt 0  # upstream is ahead of local repo
            set git_unpulled_commits "$pure_color_git_unpulled_commits$pure_symbol_git_unpulled_commits"
        end
    end

    echo "$git_unpushed_commits$git_unpulled_commits"
end
