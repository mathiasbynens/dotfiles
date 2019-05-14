source $current_dirname/../functions/_pure_prompt_git_dirty.fish
source $current_dirname/../functions/_pure_parse_git_branch.fish

function setup
    rm -r -f /tmp/pure_pure_prompt_git_dirty

    mkdir --parents /tmp/pure_pure_prompt_git_dirty
    cd /tmp/pure_pure_prompt_git_dirty

    git init --quiet
    git config --local user.email "you@example.com"
    git config --local user.name "Your Name"
end

function teardown
    rm -r -f /tmp/pure_pure_prompt_git_dirty
end

@test "_pure_prompt_git_dirty: untracked files make git repo as dirty" (
    touch file.txt
    set pure_symbol_git_dirty '*'
    set pure_color_git_dirty (set_color brblack)

    _pure_prompt_git_dirty
) = (set_color brblack)'*'

@test "_pure_prompt_git_dirty: staged files mark git repo as dirty" (
    touch file.txt
    git add file.txt
    set pure_symbol_git_dirty '*'
    set pure_color_git_dirty (set_color brblack)

    _pure_prompt_git_dirty
) = (set_color brblack)'*'
