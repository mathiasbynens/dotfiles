source $current_dirname/../functions/_pure_parse_git_branch.fish

set temporary_test_directory /tmp/pure

function setup
    rm -r -f $temporary_test_directory
    mkdir --parents $temporary_test_directory
    cd $temporary_test_directory
    git init --quiet
end

@test "_pure_parse_git_branch: returns current branch" (
    cd $temporary_test_directory

    _pure_parse_git_branch
) = 'master'

function teardown
    rm -r -f $temporary_test_directory
end