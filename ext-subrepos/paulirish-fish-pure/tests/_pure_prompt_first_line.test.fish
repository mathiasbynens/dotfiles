source $current_dirname/../functions/_pure_prompt_first_line.fish

set --local empty ''

function setup
    set pure_color_current_directory $pure_color_primary
    set pure_color_git_branch $pure_color_mute
    set pure_color_git_dirty $pure_color_mute
    set pure_color_command_duration $pure_color_warning

    mkdir --parents /tmp/test
    cd /tmp/test
    git init --quiet
    set SSH_CONNECTION 127.0.0.1 56422 127.0.0.1 22

    function _pure_print_prompt; string join ' ' $argv; end
    function _pure_prompt_ssh; echo 'user@hostname'; end
    function _pure_prompt_git; echo 'master'; end
    function _pure_prompt_command_duration; echo '1s'; end
    function _pure_string_width; echo 15; end
    function _pure_prompt_current_folder; pwd; end
end

function teardown
    functions --erase _pure_print_prompt
    functions --erase _pure_prompt_ssh
    functions --erase _pure_prompt_git
    functions --erase _pure_prompt_command_duration
    functions --erase _pure_string_width
    functions --erase _pure_prompt_current_folder
end

@test "_pure_prompt_first_line: fails when git is missing" (
    functions --copy type builtin_type
    function type  # mock, see https://github.com/fish-shell/fish-shell/issues/5444
        if test "x$argv" = "x-fq git"
            return 1
        end

        builtin_type $argv
    end

    _pure_prompt_first_line
    set --local exit_code $status

    functions --erase type  # remove mock
    functions --copy builtin_type type  # restore built-in behavior for following test cases
    echo $exit_code
) = 1

@test "_pure_prompt_first_line: print current directory, git, user@hostname (ssh-only), command duration" (
    set pure_begin_prompt_with_current_directory true
    _pure_prompt_first_line

    rm -r -f /tmp/test
) = '/tmp/test master user@hostname 1s'

@test "_pure_prompt_first_line: print user@hostname (ssh-only), current directory, git, command duration" (
    set pure_begin_prompt_with_current_directory false
    _pure_prompt_first_line

    rm -r -f /tmp/test
) = 'user@hostname /tmp/test master 1s'

