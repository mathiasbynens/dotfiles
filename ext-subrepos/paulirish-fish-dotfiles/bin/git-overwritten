#!/bin/bash
# Usage: git overwritten [--[no-]color] [<head=HEAD>] [<base=origin>]
#
# Aggregates git blame information about original owners of lines changed or
# removed in the '<base>...<head>' diff.
#
# Each line of output represents a past commit, and consists of:
# - number of lines from the commit that this diff affects
# - commit date
# - commit sha
# - author name
# - commit subject message
#
# The commits are listed in the reverse chronological order.
#
# Author: Mislav Marohnić

set -e

unset colorize
unset head
unset base

abort() {
  "$0" --help | head -1 >&2
  exit 1
}

while [ "$#" -gt 0 ]; do
  case "$1" in
  --color ) colorize=1 ;;
  --no-color ) colorize= ;;
  -h | --help )
    sed -ne '/^#/!q;s/.\{1,2\}//;1d;p' < "$0"
    exit 0
    ;;
  -* | "") abort ;;
  * )
    if [ -z "$head" ]; then head="$1"
    elif [ -z "$base" ]; then base="$1"
    else abort
    fi
    ;;
  esac
  shift 1
done

head="${head:-HEAD}"
base="${base:-origin}"

[ -t 1 ] && colorize="${colorize-1}"

color() {
  if [ -n "$colorize" ]; then
    printf "\e[0;%dm%s\e[m" "$1" "$2"
  else
    echo -n "$2"
  fi
}

git diff "${base}...${head}" --diff-filter=DM --no-prefix -w -U0 | grep -v '^+' | awk '
  function print_range() {
    printf "-L %d,%d -- %s\n", start, stop, file
  }
  /^--- / {
    sub(/^--- /, "")
    file = $0
    next
  }
  /^-/ {
    if (!start) start = stop = diffstart
    else stop += 1
    next
  }
  start {
    print_range()
    start = 0
  }
  /^@@ / {
    sub(/^-/, "", $2)
    diffstart = int($2)
    start = 0
  }
  END {
    if (start) print_range()
  }
' | xargs -L1 git blame --line-porcelain "$base" | awk -v OFS=$'\t' '
  BEGIN { num_lines = name_length = 0 }
  function val() { sub(/^[a-z-]+ /, ""); return $0 }
  /^[0-9a-f]{40} / { sha = $1 }
  /^author / {
    author = val()
    len = length(author)
    if (len > name_length) name_length = len
  }
  /^committer-time / { time = val() }
  /^summary / { msg = val() }
  /^\t/ {
    print time, sha, author, msg
    num_lines += 1
  }
  END { print num_lines, name_length }
' | sort -n | {
  read num_lines name_length
  if [ "$num_lines" -eq 0 ]; then
    color 31 "Warning: " >&2
    echo "no changed/removed lines found in the $base...$head diff" >&2
  fi

  while IFS=$'\t' read time sha author msg; do
    date -r $time "+%Y-%m-%d" | tr -d $'\n'
    printf ' '
    color 33 "${sha:0:7}"
    printf '  '
    color 32 "$(printf "%${name_length}s" "$author")"
    printf ': '
    echo "$msg"
  done
} | sort -r | uniq -c
