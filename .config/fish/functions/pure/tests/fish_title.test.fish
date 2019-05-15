source $current_dirname/../fish_title.fish
source $current_dirname/../tools/versions-compare.fish

function setup
    mkdir --parents /tmp/current/directory/
    cd /tmp/current/directory/

    function _pure_parse_directory; echo /tmp/current/directory; end
end

if fish_version_below '3.0.0'
    @mesg (print_fish_version_below '3.0.0')
    @test "fish_title: contains current directory and previous command" (
        set pure_symbol_title_bar_separator '—'
        fish_title 'last-command' 
    ) = "directory: last-command — "
end

if fish_version_at_least '3.0.0'
    @mesg (print_fish_version_at_least '3.0.0')
    @test "fish_title: contains current directory and previous command" (
        set pure_symbol_title_bar_separator '—'
        fish_title 'last-command' 
    ) = "directory: last-command — fish"
end

if fish_version_below '3.0.0'
    @mesg (print_fish_version_below '3.0.0')
    @test "fish_title: contains current directory with *empty* a previous command" (
        fish_title '' 
    ) = "/tmp/current/directory — "
end

if fish_version_at_least '3.0.0'
    @mesg (print_fish_version_at_least '3.0.0')
    @test "fish_title: contains current directory with an *empty* previous command" (
        fish_title '' 
    ) = "/tmp/current/directory — fish"
end

if fish_version_below '3.0.0'
    @mesg (print_fish_version_below '3.0.0')
    @test "fish_title: contains current path without a previous command" (
        set pure_symbol_title_bar_separator '—'
        fish_title
    ) = "/tmp/current/directory — "
end

if fish_version_at_least '3.0.0'
    @mesg (print_fish_version_at_least '3.0.0')
    @test "fish_title: contains current path without a previous command" (
        set pure_symbol_title_bar_separator '—'
        fish_title
    ) = "/tmp/current/directory — fish"
end

function teardown
    functions --erase _pure_parse_directory
end
