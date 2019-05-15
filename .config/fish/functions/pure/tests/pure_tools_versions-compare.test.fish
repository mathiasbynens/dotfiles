source $current_dirname/../tools/versions-compare.fish

set --local fail 1
set --local success 0

@test "fish_version_below: fails on itself" (
    set mock_fish_version '3.0.0'
    fish_version_below '3.0.0' $mock_fish_version >/dev/null
) $status -eq $fail

@test "fish_version_below: succeed when FISH_VERSION is lower" (
    set mock_fish_version '3.0.0'
    fish_version_below '4.0.0' $mock_fish_version >/dev/null
) $status -eq $success

@test "fish_version_below: fails when FISH_VERSION is higher" (
    set mock_fish_version '4.0.0'
    fish_version_below '3.0.0' $mock_fish_version >/dev/null
) $status -eq $fail

@test "fish_version_at_least: succeed on itself" (
    set mock_fish_version '3.0.0'
    fish_version_at_least '3.0.0' $mock_fish_version >/dev/null
) $status -eq $success

@test "fish_version_at_least: fails when FISH_VERSION is lower" (
    set mock_fish_version '3.0.0'
    fish_version_at_least '4.0.0' $mock_fish_version >/dev/null
) $status -eq $fail

@test "fish_version_at_least: succeed when FISH_VERSION is higher" (
    set mock_fish_version '4.0.0'
    fish_version_at_least '3.0.0' $mock_fish_version >/dev/null
) $status -eq $success

