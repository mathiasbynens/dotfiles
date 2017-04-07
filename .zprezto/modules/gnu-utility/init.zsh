#
# Provides for the interactive use of GNU utilities on BSD systems.
#
# Authors:
#   Sorin Ionescu <sorin.ionescu@gmail.com>
#

# Get the prefix or use the default.
zstyle -s ':prezto:module:gnu-utility' prefix '_gnu_utility_p' || _gnu_utility_p='g'

# Return if requirements are not found.
if (( ! ${+commands[${_gnu_utility_p}whoami]} )); then
  return 1
fi

_gnu_utility_cmds=(
  # Coreutils
  '[' 'base64' 'basename' 'cat' 'chcon' 'chgrp' 'chmod' 'chown'
  'chroot' 'cksum' 'comm' 'cp' 'csplit' 'cut' 'date' 'dd' 'df'
  'dir' 'dircolors' 'dirname' 'du' 'echo' 'env' 'expand' 'expr'
  'factor' 'false' 'fmt' 'fold' 'groups' 'head' 'hostid' 'id'
  'install' 'join' 'kill' 'link' 'ln' 'logname' 'ls' 'md5sum'
  'mkdir' 'mkfifo' 'mknod' 'mktemp' 'mv' 'nice' 'nl' 'nohup' 'nproc'
  'od' 'paste' 'pathchk' 'pinee' 'pr' 'printenv' 'printf' 'ptx'
  'pwd' 'readlink' 'realpath' 'rm' 'rmdir' 'runcon' 'seq' 'sha1sum'
  'sha224sum' 'sha256sum' 'sha384sum' 'sha512sum' 'shred' 'shuf'
  'sleep' 'sort' 'split' 'stat' 'stty' 'sum' 'sync' 'tac' 'tail'
  'tee' 'test' 'timeout' 'touch' 'tr' 'true' 'truncate' 'tsort'
  'tty' 'uname' 'unexpand' 'uniq' 'unlink' 'uptime' 'users' 'vdir'
  'wc' 'who' 'whoami' 'yes'

  # The following utilities are not part of Coreutils but installed separately.

  # Binutils
  'addr2line' 'ar' 'c++filt' 'elfedit' 'nm' 'objcopy' 'objdump'
  'ranlib' 'readelf' 'size' 'strings' 'strip'

  # Findutils
  'find' 'locate' 'oldfind' 'updatedb' 'xargs'

  # Libtool
  'libtool' 'libtoolize'

  # Miscellaneous
  'getopt' 'grep' 'indent' 'sed' 'tar' 'time' 'units' 'which'
)

# Wrap GNU utilities in functions.
for _gnu_utility_cmd in "${_gnu_utility_cmds[@]}"; do
  _gnu_utility_pcmd="${_gnu_utility_p}${_gnu_utility_cmd}"
  if (( ${+commands[${_gnu_utility_pcmd}]} )); then
    eval "
      function ${_gnu_utility_cmd} {
        '${commands[${_gnu_utility_pcmd}]}' \"\$@\"
      }
    "
  fi
done

unset _gnu_utility_{p,cmds,cmd,pcmd}
