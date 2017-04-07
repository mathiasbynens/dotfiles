#compdef ag
# ------------------------------------------------------------------------------
# Copyright (c) 2015 Github zsh-users - http://github.com/zsh-users
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the zsh-users nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL ZSH-USERS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ------------------------------------------------------------------------------
# Description
# -----------
#
#  Completion script for ag (https://github.com/ggreer/the_silver_searcher)
#
# ------------------------------------------------------------------------------
# Authors
# -------
#
#  * Akira Maeda <https://github.com/glidenote>
#
# ------------------------------------------------------------------------------
# -*- mode: zsh; sh-indentation: 2; indent-tabs-mode: nil; sh-basic-offset: 2; -*-
# vim: ft=zsh sw=2 ts=2 et
# ------------------------------------------------------------------------------
_ag_version() {
  local version
  version=( $($words[1] --version) )
  version=${version[@]:2:1}
  version=( "${(@s/./)version}" )
  echo "${version[2]}"
}

# Dynamically build the file type completion
# Modifies the global $AG_OPTS array
_ag_add_file_types() {
  local typ exts
  for i in $($words[1] --list-file-types); do
    if [[ "${i:0:2}" = '--' ]]; then
      if [[ "${typ}x" != "x" ]]; then
        AG_OPTS+="${typ}[${exts}]"
      fi
      typ=$i
      exts=
    else
      exts+=$i
    fi
  done
  AG_OPTS+="${typ}[${exts}]"
}

# Add version appropriate options above base
# Modifies the global $AG_OPTS array
_ag_add_version_opts() {
  local minor=$(_ag_version)

  if [[ $minor -gt 21 ]];then
    _ag_add_file_types
    AG_OPTS+=(
      '(- 1 *)--list-file-types[list supported filetypes to search]'
      '--silent[suppress all log messages, including errors]'
    )
  fi

  if [[ $minor -gt 22 ]];then
    AG_OPTS+=(
      '(-z --search-zip)'{-z,--search-zip}'[search contents of compressed files]'
    )
  fi

  if [[ $minor -le 24 ]];then
    AG_OPTS+=(
      '(-s --case-sensitive)'{-s,--case-sensitive}'[match case sensitively]'
      '(--noheading --heading)'{--noheading,--heading}'[print file names above matching contents]'
    )
  fi
  if [[ $minor -gt 24 ]];then
    AG_OPTS+=(
      '(-s --case-sensitive)'{-s,--case-sensitive}'[Match case sensitively. Default on.]'
      '(-H --noheading --heading)'{-H,--noheading,--heading}'[print file names above matching contents]'
      '--vimgrep[output results like vim''s, :vimgrep /pattern/g would (report every match on the line)]'
    )
  fi

  if [[ $minor -gt 26 ]];then
    AG_OPTS+=(
      '(-0 --null --print0)'{-0,--null,--print0}'[separate the filenames with \\0, rather than \\n]'
    )
  fi

  if [[ $minor -le 27 ]];then
    AG_OPTS+=(
      '--depth[Search up to NUM directories deep. Default is 25.]:number'
    )
  fi
  if [[ $minor -gt 27 ]];then
    AG_OPTS+=(
      '(-c --count)'{-c,--count}'[only print the number of matches in each file]'
      '--depth[Search up to NUM directories deep, -1 for unlimited. Default is 25.]:number'
      '(-F --fixed-strings)'{-F,--fixed-strings}'[alias for --literal for compatibility with grep]'
    )
  fi

  if [[ $minor -le 28 ]];then
    AG_OPTS+=(
      '(--no-numbers)--no-numbers[don´t show line numbers]'
    )
  fi
  if [[ $minor -gt 28 ]];then
    AG_OPTS+=(
      '(--nofilename --filename)'{--nofilename,--filename}'[Print file names. Default on, except when searching a single file.]'
      '(--nonumbers --numbers)'{--nonumbers,--numbers}'[Print line numbers. Default is to omit line numbers when searching streams]'
      '(-o --only-matching)'{-o,--only-matching}'[print only the matching part of the lines]'
    )
  fi
}

_ag() {
  local curcontext="$curcontext" state line cmds update_policy ret=1

  zstyle -s ":completion:${curcontext}:" cache-policy update_policy
  [[ -z "$update_policy" ]] && zstyle ":completion:${curcontext}:" cache-policy _ag_types_caching_policy

  # Don't complete if command doesn't exist
  [[ ${+commands[${words[1]}]} -eq 0 ]] && return 0

  if ( [[ ${+AG_OPTS} -eq 0 ]] || _cache_invalid "_AG_OPTS" ) && ! _retrieve_cache "_AG_OPTS"; then
    # Base opts starts at ag version 0.20
    AG_OPTS=(
      '(- 1 *)--help[print a short help statement]'
      '(- 1 *)--man[print the manual page]'
      '(- 1 *)--version[display version and copyright information]'
      '--ackmate[output results in a format parseable by AckMate]'
      '(-A --after)'{-A,--after}'[Print NUM lines before match. Default is 2]:number'
      '(-t --all-text -a --all-types -u --unrestricted)'{-t,--all-text}"[search all text files, excluding hidden ones]"
      '(-a --all-types -t --all-text -u --unrestricted)'{-a,--all-types}"[search all text files, excluding hidden ones and not obeying ignore files (.agignore, .gitignore...)]"
      '(-B --before)'{-B,--before}'[Print NUM lines after match. Defaults is 2]:number'
      '(--nobreak --break)'{--nobreak,--break}'[Print a newline between matches in different files. Default on.]'
      '(--color --nocolor)--color[Print color codes in results. Default on.]'
      '(--nocolor --color --color-line-number --color-match --color-path)--nocolor[Do not print color codes in results. Default on.]'
      '(--nocolor)--color-line-number[Color codes for line numbers. Default is 1;33.]'
      '(--nocolor)--color-match[Color codes for result match numbers. Default is 30;43.]'
      '(--nocolor)--color-path[Color codes for path names. Default is 1;32.]'
      '--column[print column numbers in results]'
      '(-C --context)'{-C,--context}'[Print NUM lines before and after matches. Default is 2.]:number'
      '(-D --debug)'{-D,--debug}'[enable debug logging]'
      '(-G --file-search-regex)'{-G,--file-search-regex}'[only search file names matching PATTERN]:pattern'
      '(-l --files-with-matches)'{-l,--files-with-matches}'[only print filenames containing matches, not matching lines]'
      '(-L --files-without-matches)'{-L,--files-without-matches}"[only print filenames that don't contain matches]"
      '(-f --follow)'{-f,--follow}'[follow symlinks]'
      '(-g)-g[print filenames that match PATTERN]:pattern'
      '(--nogroup --group)'{--nogroup,--group}'[same as --\[no\]break --\[no\]heading]'
      '--hidden[search hidden files, still obeys ignore files.]'
      '*--ignore[Ignore files/directories matching this pattern. Literal file and directory names are also allowed.]:files:_files'
      '(-i --ignore-case)'{-i,--ignore-case}'[match case insensitively]:pattern'
      '*--ignore-dir[alias for --ignore for compatibility with ack]:files:_files'
      '(-v --invert-match)'{-v,--invert-match}'[invert match]'
      '(-Q --literal)'{-Q,--literal}'[match PATTERN literally, no regular expression]'
      '(-m --max-count)'{-m,--max-count}'[Skip the rest of a file after NUM matches. Default is 10,000.]:number'
      '(--pager --nopager)'{--pager,--nopager}'[Display results with PAGER. Disabled by default.]:pager program:_command_names'
      '(--passthrough)--passthrough[when searching a stream, print all lines even if they don''t match]'
      '(-p --path-to-agignore)'{-p,--path-to-agignore}'[provide a path to a specific .agignore file]:files:_files'
      '--print-long-lines[print matches on very long lines, > 2k characters by default]'
      '--search-binary[search binary files]'
      '(-U --skip-vcs-ignores)'{-U,--skip-vcs-ignores}'[ignore VCS ignore files (.gitigore, .hgignore, svn:ignore), but still use .agignore]'
      '(-S --smart-case)'{-S,--smart-case}'[match case sensitively if PATTERN contains any uppercase letters, else match case insensitively]'
      '--stats[print stats (files scanned, time taken, etc)]'
      '(-u --unrestricted -t --all-text -a --all-types)'{-u,--unrestricted}'[search ALL files, includes: hidden, binary & ignored files (.agignore, .gitignore...)]'
      '(-w --word-regexp)'{-w,--word-regexp}'[only match whole words]'
    )
    _ag_add_version_opts
    AG_OPTS+=(
      '*: :_files'
    )
    [[ $#AG_OPTS -gt 0 ]] && _store_cache '_AG_OPTS' AG_OPTS
  fi

  _arguments -C -s -S ${AG_OPTS} && ret=0
  unset AG_OPTS

  case $state in
    # placeholder
  esac

  return ret
}

_ag_types_caching_policy() {
  # Rebuild if .agignore more recent than cache.
  [[ -f $HOME/.agignore && $$HOME/.agignore -nt "$1" ]] && return 0

  # Rebuild if cache is older than one week.
  local -a oldp
  oldp=( "$1"(Nmw+1) )
  (( $#oldp )) && return 0

  return 1
}

_ag "$@"
