function chpwd --on-variable PWD --description 'handler of changing $PWD'
  if not status --is-command-substitution ; and status --is-interactive

    set cur_cwd (echo $PWD | sed -e "s|^$HOME|~|" -e 's|^/private||')

    # set_color -o black
    # printf (printf "%*s" (tput cols)) | sed -e "s/ /\─/g";
    echo ""
    printf "%s⇢ %sEntering %s%s%s …\n" (set_color $fish_color_cwd) (set_color normal) (set_color $fish_color_cwd) $cur_cwd (set_color normal)
    ls

  end
end
