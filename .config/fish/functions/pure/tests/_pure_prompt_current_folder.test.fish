source $current_dirname/../functions/_pure_prompt_current_folder.fish
source $current_dirname/../functions/_pure_parse_directory.fish

set --local empty ''
set --local fail 1

@test "_pure_prompt_current_folder: fails if no argument given" (
    _pure_prompt_current_folder
) $status -eq $fail

@test "_pure_prompt_current_folder: returns current folder" (
    set pure_color_current_directory $empty
    set COLUMNS 20
    set current_prompt_width 10

    string length (_pure_prompt_current_folder "$current_prompt_width")
) = 8

