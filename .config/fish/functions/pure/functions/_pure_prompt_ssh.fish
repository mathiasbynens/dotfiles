function _pure_prompt_ssh
    if test "$SSH_CONNECTION" != ""
        echo (_pure_prompt_ssh_user)(_pure_prompt_ssh_separator)(_pure_prompt_ssh_host)
    end
end
