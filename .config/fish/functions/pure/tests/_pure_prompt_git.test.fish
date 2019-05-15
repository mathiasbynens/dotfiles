source $current_dirname/../functions/_pure_prompt_git.fish
source $current_dirname/../functions/_pure_prompt_git_branch.fish
source $current_dirname/../functions/_pure_parse_git_branch.fish
source $current_dirname/../functions/_pure_string_width.fish

set --local succeed 0
set --local empty ''

function setup
    mkdir --parents /tmp/test_pure_prompt_git  # prevent conflict between parallel test files
    cd /tmp/test_pure_prompt_git
end

function teardown
    rm --force --recursive /tmp/test_pure_prompt_git
end

@test "_pure_prompt_git: ignores directory that are not git repository" (
    function _pure_prompt_git_dirty; echo $empty; end
    function _pure_prompt_git_pending_commits; echo $empty; end

    _pure_prompt_git
) $status -eq $succeed

@test "_pure_prompt_git: activates on git repository" (
    git init --quiet
    function _pure_prompt_git_dirty; echo $empty; end
    function _pure_prompt_git_pending_commits; echo $empty; end

    set pure_color_git_branch $empty
    set pure_color_git_dirty $empty
    set pure_color_git_pending_commits $empty

    _pure_prompt_git
) = 'master'

@test "_pure_prompt_git: activates on dirty repository" (
    git init --quiet
    function _pure_prompt_git_dirty; echo '*'; end
    function _pure_prompt_git_pending_commits; echo $empty; end

    set pure_color_git_branch $empty
    set pure_color_git_dirty $empty
    set pure_color_git_pending_commits $empty

    _pure_prompt_git
) = 'master*'

@test "_pure_prompt_git: activates on repository with upstream changes" (
    git init --quiet
    function _pure_prompt_git_dirty; echo $empty; end
    function _pure_prompt_git_pending_commits; echo 'v'; end

    set pure_color_git_branch $empty
    set pure_color_git_dirty $empty
    set pure_color_git_pending_commits $empty

    _pure_prompt_git
) = 'master v'