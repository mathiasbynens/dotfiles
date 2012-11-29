#!/usr/bin/env bash

# search directory defaults to current
dir=.

# case sensitive search
sensitive=

# colors enabled by default in ttys
if [ -t 1 ]; then
  colors=1
else
  colors=
fi

# line numbers shown by default
linenums=1

# ansi colors
cyan=`echo -e '\033[96m'`
reset=`echo -e '\033[39m'`

# usage info
function usage {
  cat <<EOF

  Usage: spot [options] [directory] [term ...]

  Options:

    -s, --sensitive         Force case sensitive search.
    -i, --insensitive       Force case insensitive search.
    -C, --no-colors         Force avoid colors.
    -L, --no-linenums       Hide line numbers.
    -h, --help              This message.

EOF
}

# parse options
while [[ "$1" =~ "-" ]]; do
    case $1 in
        -s | --sensitive )
          sensitive=1
          ;;
        -i | --insensitive )
          sensitive=
          ;;
        -C | --no-colors )
          colors=
          ;;
        -L | --no-linenums )
          linenums=
          ;;
        -h | --help )
          usage
          exit
          ;;
    esac
    shift
done

# check for directory as first parameter
if [[ "$1" =~ / ]]; then
  if [ -d "$1" ]; then
    dir=`echo $1 | sed "s/\/$//"`
    shift
  fi
fi

# check for empty search
if [[ "" = "$@" ]]; then
  echo "(no search term. \`spot -h\` for usage)"
  exit 1
fi

# auto-detect case sensitive based on an uppercase letter
if [[ "$@" =~ [A-Z] ]]; then
  sensitive=1
fi

# grep default params
grepopt="--binary-files=without-match --devices=skip"

# add case insensitive search
if [ ! $sensitive ]; then
  grepopt="$grepopt --ignore-case"
fi

# add line number options
if [ $linenums ]; then
  grepopt="$grepopt -n"
fi

# add force colors
if [ $colors ]; then
  grepopt="$grepopt --color=always"
fi

# run search
if [ $colors ]; then
  find $dir -type f ! -path '*/.git*' ! -path '*/.svn' -print0 \
    | GREP_COLOR="1;33;40" xargs -0 grep $grepopt "`echo $@`" \
    | sed "s/^\([^:]*:\)\(.*\)/  \\
  $cyan\1$reset  \\
  \2 /"
else
  find $dir -type f ! -path '*/.git*' ! -path '*/.svn' -print0 \
    | xargs -0 grep $grepopt "$@" \
    | sed "s/^\([^:]*:\)\(.*\)/  \\
  \1  \\
  \2 /"
fi

echo ""
