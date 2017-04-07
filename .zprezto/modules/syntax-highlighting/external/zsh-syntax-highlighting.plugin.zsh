# -------------------------------------------------------------------------------------------------
# Copyright (c) 2010-2015 zsh-syntax-highlighting contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted
# provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright notice, this list of conditions
#    and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright notice, this list of
#    conditions and the following disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of the zsh-syntax-highlighting contributors nor the names of its contributors
#    may be used to endorse or promote products derived from this software without specific prior
#    written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# -------------------------------------------------------------------------------------------------
# -*- mode: zsh; sh-indentation: 2; indent-tabs-mode: nil; sh-basic-offset: 2; -*-
# vim: ft=zsh sw=2 ts=2 et
# -------------------------------------------------------------------------------------------------


if [[ -o function_argzero ]]; then
  # $0 is reliable
  ZSH_HIGHLIGHT_VERSION=$(<"${0:A:h}"/.version)
  ZSH_HIGHLIGHT_REVISION=$(<"${0:A:h}"/.revision-hash)
  if [[ $ZSH_HIGHLIGHT_REVISION == \$Format:* ]]; then
    # When running from a source tree without 'make install', $ZSH_HIGHLIGHT_REVISION
    # would be set to '$Format:%H$' literally.  That's an invalid value, and obtaining
    # the valid value (via `git rev-parse HEAD`, as Makefile does) might be costly, so:
    ZSH_HIGHLIGHT_REVISION=HEAD
  fi
else
  # $0 is unreliable, so the call to _zsh_highlight_load_highlighters will fail.
  # TODO: If 'zmodload zsh/parameter' is available, ${funcsourcetrace[1]%:*} might serve as a substitute?
  # TODO: also check POSIX_ARGZERO, but not it's not available in older zsh
  echo "zsh-syntax-highlighting: error: not compatible with NO_FUNCTION_ARGZERO" >&2
  return 1
fi

# -------------------------------------------------------------------------------------------------
# Core highlighting update system
# -------------------------------------------------------------------------------------------------

# Array declaring active highlighters names.
typeset -ga ZSH_HIGHLIGHT_HIGHLIGHTERS

# Update ZLE buffer syntax highlighting.
#
# Invokes each highlighter that needs updating.
# This function is supposed to be called whenever the ZLE state changes.
_zsh_highlight()
{
  # Store the previous command return code to restore it whatever happens.
  local ret=$?

  setopt localoptions warncreateglobal
  setopt localoptions noksharrays
  local REPLY # don't leak $REPLY into global scope

  # Do not highlight if there are more than 300 chars in the buffer. It's most
  # likely a pasted command or a huge list of files in that case..
  [[ -n ${ZSH_HIGHLIGHT_MAXLENGTH:-} ]] && [[ $#BUFFER -gt $ZSH_HIGHLIGHT_MAXLENGTH ]] && return $ret

  # Do not highlight if there are pending inputs (copy/paste).
  [[ $PENDING -gt 0 ]] && return $ret

  # Reset region highlight to build it from scratch
  typeset -ga region_highlight
  region_highlight=();

  {
    local cache_place
    local -a region_highlight_copy

    # Select which highlighters in ZSH_HIGHLIGHT_HIGHLIGHTERS need to be invoked.
    local highlighter; for highlighter in $ZSH_HIGHLIGHT_HIGHLIGHTERS; do

      # eval cache place for current highlighter and prepare it
      cache_place="_zsh_highlight_${highlighter}_highlighter_cache"
      typeset -ga ${cache_place}

      # If highlighter needs to be invoked
      if "_zsh_highlight_${highlighter}_highlighter_predicate"; then

        # save a copy, and cleanup region_highlight
        region_highlight_copy=("${region_highlight[@]}")
        region_highlight=()

        # Execute highlighter and save result
        {
          "_zsh_highlight_${highlighter}_highlighter"
        } always {
          eval "${cache_place}=(\"\${region_highlight[@]}\")"
        }

        # Restore saved region_highlight
        region_highlight=("${region_highlight_copy[@]}")

      fi

      # Use value form cache if any cached
      eval "region_highlight+=(\"\${${cache_place}[@]}\")"

    done

    # Re-apply zle_highlight settings
    () {
      if (( REGION_ACTIVE )) ; then
        # zle_highlight[region] defaults to 'standout' if unspecified
        local region="${${zle_highlight[(r)region:*]#region:}:-standout}"
        integer start end
        if (( MARK > CURSOR )) ; then
          start=$CURSOR end=$MARK
        else
          start=$MARK end=$CURSOR
        fi
        region_highlight+=("$start $end $region")
      fi
    }
    # YANK_ACTIVE is only available in zsh-5.1.1 and newer
    (( $+YANK_ACTIVE )) && () {
      if (( YANK_ACTIVE )) ; then
        # zle_highlight[paste] defaults to 'standout' if unspecified
        local paste="${${zle_highlight[(r)paste:*]#paste:}:-standout}"
        integer start end
        if (( YANK_END > YANK_START )) ; then
          start=$YANK_START end=$YANK_END
        else
          start=$YANK_END end=$YANK_START
        fi
        region_highlight+=("$start $end $paste")
      fi
    }

    return $ret


  } always {
    typeset -g _ZSH_HIGHLIGHT_PRIOR_BUFFER="$BUFFER"
    typeset -gi _ZSH_HIGHLIGHT_PRIOR_CURSOR=$CURSOR
  }
}


# -------------------------------------------------------------------------------------------------
# API/utility functions for highlighters
# -------------------------------------------------------------------------------------------------

# Array used by highlighters to declare user overridable styles.
typeset -gA ZSH_HIGHLIGHT_STYLES

# Whether the command line buffer has been modified or not.
#
# Returns 0 if the buffer has changed since _zsh_highlight was last called.
_zsh_highlight_buffer_modified()
{
  [[ "${_ZSH_HIGHLIGHT_PRIOR_BUFFER:-}" != "$BUFFER" ]]
}

# Whether the cursor has moved or not.
#
# Returns 0 if the cursor has moved since _zsh_highlight was last called.
_zsh_highlight_cursor_moved()
{
  [[ -n $CURSOR ]] && [[ -n ${_ZSH_HIGHLIGHT_PRIOR_CURSOR-} ]] && (($_ZSH_HIGHLIGHT_PRIOR_CURSOR != $CURSOR))
}


# -------------------------------------------------------------------------------------------------
# Setup functions
# -------------------------------------------------------------------------------------------------

# Helper for _zsh_highlight_bind_widgets
# $1 is name of widget to call
_zsh_highlight_call_widget()
{
  builtin zle "$@" && 
  _zsh_highlight
}

# Rebind all ZLE widgets to make them invoke _zsh_highlights.
_zsh_highlight_bind_widgets()
{
  setopt localoptions noksharrays

  # Load ZSH module zsh/zleparameter, needed to override user defined widgets.
  zmodload zsh/zleparameter 2>/dev/null || {
    echo 'zsh-syntax-highlighting: failed loading zsh/zleparameter.' >&2
    return 1
  }

  # Override ZLE widgets to make them invoke _zsh_highlight.
  local cur_widget
  for cur_widget in ${${(f)"$(builtin zle -la)"}:#(.*|_*|orig-*|run-help|which-command|beep|set-local-history|yank)}; do
    case $widgets[$cur_widget] in

      # Already rebound event: do nothing.
      user:$cur_widget|user:_zsh_highlight_widget_*);;

      # User defined widget: override and rebind old one with prefix "orig-".
      user:*) eval "zle -N orig-$cur_widget ${widgets[$cur_widget]#*:}; \
                    _zsh_highlight_widget_$cur_widget() { _zsh_highlight_call_widget orig-$cur_widget -- \"\$@\" }; \
                    zle -N $cur_widget _zsh_highlight_widget_$cur_widget";;

      # Completion widget: override and rebind old one with prefix "orig-".
      completion:*) eval "zle -C orig-$cur_widget ${${widgets[$cur_widget]#*:}/:/ }; \
                          _zsh_highlight_widget_$cur_widget() { _zsh_highlight_call_widget orig-$cur_widget -- \"\$@\" }; \
                          zle -N $cur_widget _zsh_highlight_widget_$cur_widget";;

      # Builtin widget: override and make it call the builtin ".widget".
      builtin) eval "_zsh_highlight_widget_$cur_widget() { _zsh_highlight_call_widget .$cur_widget -- \"\$@\" }; \
                     zle -N $cur_widget _zsh_highlight_widget_$cur_widget";;

      # Default: unhandled case.
      *) echo "zsh-syntax-highlighting: unhandled ZLE widget '$cur_widget'" >&2 ;;
    esac
  done
}

# Load highlighters from directory.
#
# Arguments:
#   1) Path to the highlighters directory.
_zsh_highlight_load_highlighters()
{
  setopt localoptions noksharrays

  # Check the directory exists.
  [[ -d "$1" ]] || {
    echo "zsh-syntax-highlighting: highlighters directory '$1' not found." >&2
    return 1
  }

  # Load highlighters from highlighters directory and check they define required functions.
  local highlighter highlighter_dir
  for highlighter_dir ($1/*/); do
    highlighter="${highlighter_dir:t}"
    [[ -f "$highlighter_dir/${highlighter}-highlighter.zsh" ]] && {
      . "$highlighter_dir/${highlighter}-highlighter.zsh"
      type "_zsh_highlight_${highlighter}_highlighter" &> /dev/null &&
      type "_zsh_highlight_${highlighter}_highlighter_predicate" &> /dev/null || {
        echo "zsh-syntax-highlighting: '${highlighter}' highlighter should define both required functions '_zsh_highlight_${highlighter}_highlighter' and '_zsh_highlight_${highlighter}_highlighter_predicate' in '${highlighter_dir}/${highlighter}-highlighter.zsh'." >&2
      }
    }
  done
}


# -------------------------------------------------------------------------------------------------
# Setup
# -------------------------------------------------------------------------------------------------

# Try binding widgets.
_zsh_highlight_bind_widgets || {
  echo 'zsh-syntax-highlighting: failed binding ZLE widgets, exiting.' >&2
  return 1
}

# Resolve highlighters directory location.
_zsh_highlight_load_highlighters "${ZSH_HIGHLIGHT_HIGHLIGHTERS_DIR:-${${0:A}:h}/highlighters}" || {
  echo 'zsh-syntax-highlighting: failed loading highlighters, exiting.' >&2
  return 1
}

# Reset scratch variables when commandline is done.
_zsh_highlight_preexec_hook()
{
  typeset -g _ZSH_HIGHLIGHT_PRIOR_BUFFER=
  typeset -gi _ZSH_HIGHLIGHT_PRIOR_CURSOR=
}
autoload -U add-zsh-hook
add-zsh-hook preexec _zsh_highlight_preexec_hook 2>/dev/null || {
    echo 'zsh-syntax-highlighting: failed loading add-zsh-hook.' >&2
  }

# Initialize the array of active highlighters if needed.
[[ $#ZSH_HIGHLIGHT_HIGHLIGHTERS -eq 0 ]] && ZSH_HIGHLIGHT_HIGHLIGHTERS=(main) || true
