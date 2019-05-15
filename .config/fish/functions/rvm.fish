function rvm --description='Ruby enVironment Manager'
  # run RVM and capture the resulting environment
  set --local env_file (mktemp -t rvm.fish.XXXXXXXXXX)
  bash -c 'source ~/.rvm/scripts/rvm; rvm "$@"; status=$?; env > "$0"; exit $status' $env_file $argv

  # apply rvm_* and *PATH variables from the captured environment
  and eval (grep '^rvm\|^[^=]*PATH\|^GEM_HOME' $env_file | grep -v '_clr=' | sed '/^[^=]*PATH/s/:/" "/g; s/^/set -xg /; s/=/ "/; s/$/" ;/; s/(//; s/)//')
  # needed under fish >= 2.2.0
  and set -xg GEM_PATH (echo $GEM_PATH | sed 's/ /:/g')

  # clean up
  rm -f $env_file
end

function __handle_rvmrc_stuff --on-variable PWD
  # Source a .rvmrc file in a directory after changing to it, if it exists.
  # To disable this fature, set rvm_project_rvmrc=0 in $HOME/.rvmrc
  if test "$rvm_project_rvmrc" != 0
    set -l cwd $PWD
    while true
      if contains $cwd "" $HOME "/"
        if test "$rvm_project_rvmrc_default" = 1
          rvm default 1>/dev/null 2>&1
        end
        break
      else
        if test -e .rvmrc -o -e .ruby-version -o -e .ruby-gemset
          eval "rvm reload" > /dev/null
          eval "rvm rvmrc load" >/dev/null
          break
        else
          set cwd (dirname "$cwd")
        end
      end
    end

    set -e cwd
  end
end
