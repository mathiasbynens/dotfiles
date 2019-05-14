# Script to create screenshot context

set coming_from (pwd)
function install_base16_plugin
    fisher ls | grep --quiet smh/base16-shell-fish
    or fisher add smh/base16-shell-fish
end

set --global mock_directory $HOME/dev/
function setup_mock_environment
    git init --bare --quiet /tmp/fake.git
    mkdir --parents $mock_directory/pure/
    cd $mock_directory/pure/
    git init --quiet
    git remote add origin /tmp/fake.git/
    touch mock.file-1; git add mock.file-1; git commit --message='mock.file-1' --quiet
    touch mock.file-2; git add mock.file-2; git commit --message='mock.file-2' --quiet
    git push --set-upstream origin master
end

function revert
    git reset master -q
    cd $HOME
end

function teardown_mock_environment
echo "teardown_mock_environment"
    cd $coming_from
    rm --recursive --force $mock_directory /tmp/fake.git/

    set --erase colorscheme
    functions --erase install_base16_plugin
    functions --erase pure
    functions --erase revert
    functions --erase setup_mock_environment
    functions --erase teardown_mock_environment
    echo 'cleaned'
end


install_base16_plugin
setup_mock_environment
clear
# PLAY ACTION HERE
fish --interactive --init-command="cd $HOME; base16 $colorscheme; clear"
and teardown_mock_environment
