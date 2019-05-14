set --global DIRNAME $current_dirname

function setup
    cp $current_dirname/fixtures/{config.mock.fish,config.fish}
end

function teardown
    rm $current_dirname/fixtures/config.fish
end

@test "migrate all variables" (
    set file_to_migrate $current_dirname/fixtures/config.fish  # created during 'setup'

    fish $current_dirname/../tools/migration-to-2.0.0.fish $file_to_migrate 2>&1 >/dev/null
    
    diff -U 0 $current_dirname/fixtures/config.expected.fish $file_to_migrate
) $status -eq 0

