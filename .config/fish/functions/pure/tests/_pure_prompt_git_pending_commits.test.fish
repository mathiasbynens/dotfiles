source $current_dirname/../functions/_pure_prompt_git_pending_commits.fish

set --local empty ''
set fake_git_repo /tmp/pure
set fake_git_bare /tmp/pure.git

function setup
    rm -r -f $fake_git_repo

    git init --bare --quiet /tmp/pure.git
    mkdir --parents $fake_git_repo
    cd $fake_git_repo
    git init --quiet
    git config --local user.email "you@example.com"
    git config --local user.name "Your Name"
    git remote add origin ../pure.git/
    touch file.txt
    git add file.txt
    git commit --quiet --message='init'
end

function teardown
    rm -r -f \
        $fake_git_repo \
        $fake_git_bare
end

@test "_pure_prompt_git_pending_commits: print nothing when no upstream repo" (
    cd $fake_git_repo

    _pure_prompt_git_pending_commits
) = $empty

@test "_pure_prompt_git_pending_commits: show arrow UP when branch is AHEAD of upstream (need git push)" (
    git push --set-upstream --quiet origin master > /dev/null
    touch missing-on-upstream.txt
    git add missing-on-upstream.txt
    git commit --quiet --message='missing on upstream'

    set pure_symbol_git_unpushed_commits '^'
    set pure_color_git_unpushed_commits (set_color cyan)

    _pure_prompt_git_pending_commits

) = (set_color cyan)'^'

@test "_pure_prompt_git_pending_commits: show arrow DOWN when branch is BEHIND upstream (need git pull)" (
    touch another-file.txt
    git add another-file.txt
    git commit --quiet --message='another'
    git push --set-upstream --quiet origin master > /dev/null

    git reset --hard --quiet HEAD~1

    set pure_symbol_git_unpulled_commits 'v'
    set pure_color_git_unpulled_commits (set_color cyan)

    _pure_prompt_git_pending_commits
) = (set_color cyan)'v'

