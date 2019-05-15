function bass
  set __bash_args $argv
  if test "$__bash_args[1]_" = '-d_'
    set __bass_debug
    set -e __bash_args[1]
  end

  set -l __script (python (dirname (status -f))/__bass.py $__bash_args)
  if test $__script = '__usage'
    echo "Usage: bass [-d] <bash-command>"
  else if test $__script = '__error'
    echo "Bass encountered an error!"
  else
    source $__script
    if set -q __bass_debug
      cat $__script
    end
    rm -f $__script
  end
end
