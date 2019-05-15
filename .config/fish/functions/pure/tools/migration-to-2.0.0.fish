# Migrate variable to 2.0.0
# Usage:
#     ❯ tools/migration-to-2.0.0.fish
#     ❯ tools/migration-to-2.0.0.fish /path/to/my/config.fish

set fish_user_config $HOME/.config/fish/config.fish
if set --query argv[1]
    set fish_user_config $argv[1]
end
printf "%sMigrating configuration: $fish_user_config\n"

printf (set_color cyan)"Renaming color variables\n"(set_color normal)
sed -i 's/pure_color_blue/pure_color_primary/g' $fish_user_config #; grep -c 'pure_color_blue' $fish_user_config
sed -i 's/pure_color_current_folder/pure_color_current_directory/g' $fish_user_config #; grep -c 'pure_color_current_folder' $fish_user_config
sed -i 's/pure_color_cyan/pure_color_info/g' $fish_user_config #; grep -c 'pure_color_cyan' $fish_user_config
sed -i 's/pure_color_folder/pure_color_current_directory/g' $fish_user_config #; grep -c 'pure_color_folder' $fish_user_config
sed -i 's/pure_color_gray/pure_color_mute/g' $fish_user_config #; grep -c 'pure_color_gray' $fish_user_config
sed -i 's/pure_color_green/pure_color_success/g' $fish_user_config #; grep -c 'pure_color_magenta' $fish_user_config
sed -i 's/pure_color_magenta/pure_color_success/g' $fish_user_config #; grep -c 'pure_color_magenta' $fish_user_config
sed -i 's/pure_color_red/pure_color_danger/g' $fish_user_config #; grep -c 'pure_color_red' $fish_user_config
sed -i 's/pure_color_symbol_error/pure_color_prompt_on_error/g' $fish_user_config #; grep -c 'pure_color_symbol_error' $fish_user_config
sed -i 's/pure_color_symbol_success/pure_color_prompt_on_success/g' $fish_user_config #; grep -c 'pure_color_symbol_success' $fish_user_config
sed -i 's/pure_color_white/pure_color_light/g' $fish_user_config #; grep -c 'pure_color_white' $fish_user_config
sed -i 's/pure_color_yellow/pure_color_warning/g' $fish_user_config #; grep -c 'pure_color_yellow' $fish_user_config

printf (set_color cyan)"Renaming git variables\n"(set_color normal)
sed -i 's/pure_symbol_git_arrow_down/pure_symbol_git_unpulled_commits/g' $fish_user_config #; grep -c 'pure_symbol_git_arrow_down' $fish_user_config
sed -i 's/pure_symbol_git_arrow_up/pure_symbol_git_unpushed_commits/g' $fish_user_config #; grep -c 'pure_symbol_git_arrow_up' $fish_user_config
sed -i 's/pure_symbol_git_down_arrow/pure_symbol_git_unpulled_commits/g' $fish_user_config #; grep -c 'pure_symbol_git_arrow_down' $fish_user_config
sed -i 's/pure_symbol_git_up_arrow/pure_symbol_git_unpushed_commits/g' $fish_user_config #; grep -c 'pure_symbol_git_arrow_up' $fish_user_config

printf (set_color cyan)"Renaming SSH variables\n"(set_color normal)
sed -i 's/pure_color_ssh_host/pure_color_ssh_hostname/g' $fish_user_config #; grep -c 'pure_color_ssh_host' $fish_user_config
sed -i 's/pure_color_ssh_root/pure_color_ssh_user_root/g' $fish_user_config #; grep -c 'pure_color_ssh_root' $fish_user_config
sed -i 's/pure_color_ssh_separator/pure_color_ssh_separator/g' $fish_user_config #; grep -c 'pure_color_ssh_separator' $fish_user_config
sed -i 's/pure_color_ssh_username/pure_color_ssh_user_normal/g' $fish_user_config #; grep -c 'pure_color_ssh_username' $fish_user_config
sed -i 's/pure_host_color/pure_color_ssh_hostname/g' $fish_user_config #; grep -c 'pure_host_color' $fish_user_config
sed -i 's/pure_root_color/pure_color_ssh_user_root/g' $fish_user_config #; grep -c 'pure_root_color' $fish_user_config
sed -i 's/pure_username_color/pure_color_ssh_user_normal/g' $fish_user_config #; grep -c 'pure_username_color' $fish_user_config

printf (set_color cyan)"Renaming Misc variables\n"(set_color normal)
sed -i 's/pure_command_max_exec_time/pure_threshold_command_duration/g' $fish_user_config #; grep -c 'pure_command_max_exec_time' $fish_user_config
sed -i 's/pure_symbol_horizontal_bar/pure_symbol_title_bar_separator/g' $fish_user_config #; grep -c 'pure_symbol_horizontal_bar' $fish_user_config

printf (set_color cyan)"Change variables type\n"(set_color normal)
sed -i 's/_pure_fresh_session 0/_pure_fresh_session false/g' $fish_user_config #; grep -c '_pure_fresh_session 1' $fish_user_config
sed -i 's/_pure_fresh_session 1/_pure_fresh_session true/g' $fish_user_config #; grep -c '_pure_fresh_session 1' $fish_user_config
sed -i 's/pure_separate_prompt_on_error 0/pure_separate_prompt_on_error false/g' $fish_user_config #; grep -c 'pure_separate_prompt_on_error' $fish_user_config
sed -i 's/pure_separate_prompt_on_error 1/pure_separate_prompt_on_error true/g' $fish_user_config #; grep -c 'pure_separate_prompt_on_error' $fish_user_config
sed -i 's/pure_prompt_begin_with_current_directory 0/pure_begin_prompt_with_current_directory true/g' $fish_user_config #; grep -c 'pure_prompt_begin_with_current_directory' $fish_user_config
sed -i 's/pure_prompt_begin_with_current_directory 1/pure_begin_prompt_with_current_directory false/g' $fish_user_config #; grep -c 'pure_prompt_begin_with_current_directory' $fish_user_config
sed -i 's/pure_user_host_location 0/pure_begin_prompt_with_current_directory true/g' $fish_user_config #; grep -c 'pure_prompt_begin_with_current_directory' $fish_user_config
sed -i 's/pure_user_host_location 1/pure_begin_prompt_with_current_directory false/g' $fish_user_config #; grep -c 'pure_prompt_begin_with_current_directory' $fish_user_config

if test (grep 'pure_color_git_pending_commits' $fish_user_config)
    printf (set_color yellow)'Manual edit required!'(set_color normal)
    printf 'Variable "%s" has been split in two:\n' \
        (set_color green)"$pure_color_git_pending_commits"(set_color normal)
    printf "\t%s\n\t%s" \
        (set_color green)"pure_color_git_unpushed_commits"(set_color normal) \
        (set_color green)"pure_color_git_unpulled_commits"(set_color normal)
end
