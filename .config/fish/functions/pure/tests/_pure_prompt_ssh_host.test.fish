source $current_dirname/../functions/_pure_prompt_ssh_host.fish
source $current_dirname/../tools/versions-compare.fish

if fish_version_below '3.0.0'
    @mesg (print_fish_version_below '3.0.0')
    @test "_pure_prompt_ssh_host: colorize hostname (using reserved variable)" (
        set pure_color_ssh_hostname (set_color grey)
        set hostname 'hostname-variable'

        _pure_prompt_ssh_host
    ) = (set_color grey)'hostname-variable'
end

if fish_version_below '3.0.0'
    @mesg (print_fish_version_below '3.0.0')
    @test "_pure_prompt_ssh_host: colorize hostname (using hostname executable)" (
        set --erase hostname
        function hostname  # mock
            echo 'hostname-executable'
        end

        set pure_color_ssh_hostname (set_color grey)

        _pure_prompt_ssh_host

        functions --erase hostname
    ) = (set_color grey)'hostname-executable'
end

if fish_version_at_least '3.0.0'
    @mesg (print_fish_version_at_least '3.0.0')
    @test "_pure_prompt_ssh_host: use native \$hostname" (
        set pure_color_ssh_hostname (set_color grey)

        _pure_prompt_ssh_host > /dev/null
    ) $status -eq 0
end
