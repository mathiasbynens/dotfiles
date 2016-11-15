#
# Exposes Git repository information via the $git_info associative array.
#
# Authors:
#   Sorin Ionescu <sorin.ionescu@gmail.com>
#

# Gets the Git special action (am, bisect, cherry, merge, rebase).
# Borrowed from vcs_info and edited.
function _git-action {
  local action_dir
  local git_dir="$(git-dir)"
  local apply_formatted
  local bisect_formatted
  local cherry_pick_formatted
  local cherry_pick_sequence_formatted
  local merge_formatted
  local rebase_formatted
  local rebase_interactive_formatted
  local rebase_merge_formatted

  for action_dir in \
    "${git_dir}/rebase-apply" \
    "${git_dir}/rebase" \
    "${git_dir}/../.dotest"
  do
    if [[ -d "$action_dir" ]] ; then
      zstyle -s ':prezto:module:git:info:action:apply' format 'apply_formatted' || apply_formatted='apply'
      zstyle -s ':prezto:module:git:info:action:rebase' format 'rebase_formatted' || rebase_formatted='rebase'

      if [[ -f "${action_dir}/rebasing" ]] ; then
        print "$rebase_formatted"
      elif [[ -f "${action_dir}/applying" ]] ; then
        print "$apply_formatted"
      else
        print "${rebase_formatted}/${apply_formatted}"
      fi

      return 0
    fi
  done

  for action_dir in \
    "${git_dir}/rebase-merge/interactive" \
    "${git_dir}/.dotest-merge/interactive"
  do
    if [[ -f "$action_dir" ]]; then
      zstyle -s ':prezto:module:git:info:action:rebase-interactive' format 'rebase_interactive_formatted' || rebase_interactive_formatted='rebase-interactive'
      print "$rebase_interactive_formatted"
      return 0
    fi
  done

  for action_dir in \
    "${git_dir}/rebase-merge" \
    "${git_dir}/.dotest-merge"
  do
    if [[ -d "$action_dir" ]]; then
      zstyle -s ':prezto:module:git:info:action:rebase-merge' format 'rebase_merge_formatted' || rebase_merge_formatted='rebase-merge'
      print "$rebase_merge_formatted"
      return 0
    fi
  done

  if [[ -f "${git_dir}/MERGE_HEAD" ]]; then
    zstyle -s ':prezto:module:git:info:action:merge' format 'merge_formatted' || merge_formatted='merge'
    print "$merge_formatted"
    return 0
  fi

  if [[ -f "${git_dir}/CHERRY_PICK_HEAD" ]]; then
    if [[ -d "${git_dir}/sequencer" ]] ; then
      zstyle -s ':prezto:module:git:info:action:cherry-pick-sequence' format 'cherry_pick_sequence_formatted' || cherry_pick_sequence_formatted='cherry-pick-sequence'
      print "$cherry_pick_sequence_formatted"
    else
      zstyle -s ':prezto:module:git:info:action:cherry-pick' format 'cherry_pick_formatted' || cherry_pick_formatted='cherry-pick'
      print "$cherry_pick_formatted"
    fi

    return 0
  fi

  if [[ -f "${git_dir}/BISECT_LOG" ]]; then
    zstyle -s ':prezto:module:git:info:action:bisect' format 'bisect_formatted' || bisect_formatted='bisect'
    print "$bisect_formatted"
    return 0
  fi

  return 1
}

# Gets the Git status information.
function git-info {
  # Extended globbing is needed to parse repository status.
  setopt LOCAL_OPTIONS
  setopt EXTENDED_GLOB

  local action
  local action_format
  local action_formatted
  local added=0
  local added_format
  local added_formatted
  local ahead=0
  local ahead_and_behind
  local ahead_and_behind_cmd
  local ahead_format
  local ahead_formatted
  local ahead_or_behind
  local behind=0
  local behind_format
  local behind_formatted
  local branch
  local branch_format
  local branch_formatted
  local branch_info
  local clean
  local clean_formatted
  local commit
  local commit_format
  local commit_formatted
  local deleted=0
  local deleted_format
  local deleted_formatted
  local dirty=0
  local dirty_format
  local dirty_formatted
  local ignore_submodules
  local indexed=0
  local indexed_format
  local indexed_formatted
  local -A info_formats
  local info_format
  local modified=0
  local modified_format
  local modified_formatted
  local position
  local position_format
  local position_formatted
  local remote
  local remote_cmd
  local remote_format
  local remote_formatted
  local renamed=0
  local renamed_format
  local renamed_formatted
  local stashed=0
  local stashed_format
  local stashed_formatted
  local status_cmd
  local status_mode
  local unindexed=0
  local unindexed_format
  local unindexed_formatted
  local unmerged=0
  local unmerged_format
  local unmerged_formatted
  local untracked=0
  local untracked_format
  local untracked_formatted

  # Clean up previous $git_info.
  unset git_info
  typeset -gA git_info

  # Return if not inside a Git repository work tree.
  if ! is-true "$(git rev-parse --is-inside-work-tree 2> /dev/null)"; then
    return 1
  fi

  if (( $# > 0 )); then
    if [[ "$1" == [Oo][Nn] ]]; then
      git config --bool prompt.showinfo true
    elif [[ "$1" == [Oo][Ff][Ff] ]]; then
      git config --bool prompt.showinfo false
    else
      print "usage: $0 [ on | off ]" >&2
    fi
    return 0
  fi

  # Return if git-info is disabled.
  if ! is-true "${$(git config --bool prompt.showinfo):-true}"; then
    return 1
  fi

  # Ignore submodule status.
  zstyle -s ':prezto:module:git:status:ignore' submodules 'ignore_submodules'

  # Format commit.
  zstyle -s ':prezto:module:git:info:commit' format 'commit_format'
  if [[ -n "$commit_format" ]]; then
    commit="$(git rev-parse HEAD 2> /dev/null)"
    if [[ -n "$commit" ]]; then
      zformat -f commit_formatted "$commit_format" "c:$commit"
    fi
  fi

  # Format stashed.
  zstyle -s ':prezto:module:git:info:stashed' format 'stashed_format'
  if [[ -n "$stashed_format" && -f "$(git-dir)/refs/stash" ]]; then
    stashed="$(git stash list 2> /dev/null | wc -l | awk '{print $1}')"
    if [[ -n "$stashed" ]]; then
      zformat -f stashed_formatted "$stashed_format" "S:$stashed"
    fi
  fi

  # Format action.
  zstyle -s ':prezto:module:git:info:action' format 'action_format'
  if [[ -n "$action_format" ]]; then
    action="$(_git-action)"
    if [[ -n "$action" ]]; then
      zformat -f action_formatted "$action_format" "s:$action"
    fi
  fi

  # Get the branch.
  branch="${$(git symbolic-ref HEAD 2> /dev/null)#refs/heads/}"

  # Format branch.
  zstyle -s ':prezto:module:git:info:branch' format 'branch_format'
  if [[ -n "$branch" && -n "$branch_format" ]]; then
    zformat -f branch_formatted "$branch_format" "b:$branch"
  fi

  # Format position.
  zstyle -s ':prezto:module:git:info:position' format 'position_format'
  if [[ -z "$branch" && -n "$position_format" ]]; then
    position="$(git describe --contains --all HEAD 2> /dev/null)"
    if [[ -n "$position" ]]; then
      zformat -f position_formatted "$position_format" "p:$position"
    fi
  fi

  # Format remote.
  zstyle -s ':prezto:module:git:info:remote' format 'remote_format'
  if [[ -n "$branch" && -n "$remote_format" ]]; then
    # Gets the remote name.
    remote_cmd='git rev-parse --symbolic-full-name --verify HEAD@{upstream}'
    remote="${$(${(z)remote_cmd} 2> /dev/null)##refs/remotes/}"
    if [[ -n "$remote" ]]; then
      zformat -f remote_formatted "$remote_format" "R:$remote"
    fi
  fi

  zstyle -s ':prezto:module:git:info:ahead' format 'ahead_format'
  zstyle -s ':prezto:module:git:info:behind' format 'behind_format'
  if [[ -n "$branch" && ( -n "$ahead_format" || -n "$behind_format" ) ]]; then
    # Gets the commit difference counts between local and remote.
    ahead_and_behind_cmd='git rev-list --count --left-right HEAD...@{upstream}'

    # Get ahead and behind counts.
    ahead_and_behind="$(${(z)ahead_and_behind_cmd} 2> /dev/null)"

    # Format ahead.
    if [[ -n "$ahead_format" ]]; then
      ahead="$ahead_and_behind[(w)1]"
      if (( ahead > 0 )); then
        zformat -f ahead_formatted "$ahead_format" "A:$ahead"
      fi
    fi

    # Format behind.
    if [[ -n "$behind_format" ]]; then
      behind="$ahead_and_behind[(w)2]"
      if (( behind > 0 )); then
        zformat -f behind_formatted "$behind_format" "B:$behind"
      fi
    fi
  fi

  # Get status type.
  if ! zstyle -t ':prezto:module:git:info' verbose; then
    # Format indexed.
    zstyle -s ':prezto:module:git:info:indexed' format 'indexed_format'
    if [[ -n "$indexed_format" ]]; then
      ((
        indexed+=$(
          git diff-index \
            --no-ext-diff \
            --name-only \
            --cached \
            --ignore-submodules=${ignore_submodules:-none} \
            HEAD \
            2> /dev/null \
          | wc -l
        )
      ))
      if (( indexed > 0 )); then
        zformat -f indexed_formatted "$indexed_format" "i:$indexed"
      fi
    fi

    # Format unindexed.
    zstyle -s ':prezto:module:git:info:unindexed' format 'unindexed_format'
    if [[ -n "$unindexed_format" ]]; then
      ((
        unindexed+=$(
          git diff-files \
            --no-ext-diff \
            --name-only \
            --ignore-submodules=${ignore_submodules:-none} \
            2> /dev/null \
          | wc -l
        )
      ))
      if (( unindexed > 0 )); then
        zformat -f unindexed_formatted "$unindexed_format" "I:$unindexed"
      fi
    fi

    # Format untracked.
    zstyle -s ':prezto:module:git:info:untracked' format 'untracked_format'
    if [[ -n "$untracked_format" ]]; then
      ((
        untracked+=$(
          git ls-files \
            --other \
            --exclude-standard \
            2> /dev/null \
          | wc -l
        )
      ))
      if (( untracked > 0 )); then
        zformat -f untracked_formatted "$untracked_format" "u:$untracked"
      fi
    fi

    (( dirty = indexed + unindexed + untracked ))
  else
    # Use porcelain status for easy parsing.
    status_cmd="git status --porcelain --ignore-submodules=${ignore_submodules:-none}"

    # Get current status.
    while IFS=$'\n' read line; do
      # Count added, deleted, modified, renamed, unmerged, untracked, dirty.
      # T (type change) is undocumented, see http://git.io/FnpMGw.
      # For a table of scenarii, see http://i.imgur.com/2YLu1.png.
      [[ "$line" == ([ACDMT][\ MT]|[ACMT]D)\ * ]] && (( added++ ))
      [[ "$line" == [\ ACMRT]D\ * ]] && (( deleted++ ))
      [[ "$line" == ?[MT]\ * ]] && (( modified++ ))
      [[ "$line" == R?\ * ]] && (( renamed++ ))
      [[ "$line" == (AA|DD|U?|?U)\ * ]] && (( unmerged++ ))
      [[ "$line" == \?\?\ * ]] && (( untracked++ ))
      (( dirty++ ))
    done < <(${(z)status_cmd} 2> /dev/null)

    # Format added.
    if (( added > 0 )); then
      zstyle -s ':prezto:module:git:info:added' format 'added_format'
      zformat -f added_formatted "$added_format" "a:$added"
    fi

    # Format deleted.
    if (( deleted > 0 )); then
      zstyle -s ':prezto:module:git:info:deleted' format 'deleted_format'
      zformat -f deleted_formatted "$deleted_format" "d:$deleted"
    fi

    # Format modified.
    if (( modified > 0 )); then
      zstyle -s ':prezto:module:git:info:modified' format 'modified_format'
      zformat -f modified_formatted "$modified_format" "m:$modified"
    fi

    # Format renamed.
    if (( renamed > 0 )); then
      zstyle -s ':prezto:module:git:info:renamed' format 'renamed_format'
      zformat -f renamed_formatted "$renamed_format" "r:$renamed"
    fi

    # Format unmerged.
    if (( unmerged > 0 )); then
      zstyle -s ':prezto:module:git:info:unmerged' format 'unmerged_format'
      zformat -f unmerged_formatted "$unmerged_format" "U:$unmerged"
    fi

    # Format untracked.
    if (( untracked > 0 )); then
      zstyle -s ':prezto:module:git:info:untracked' format 'untracked_format'
      zformat -f untracked_formatted "$untracked_format" "u:$untracked"
    fi
  fi

  # Format dirty and clean.
  if (( dirty > 0 )); then
    zstyle -s ':prezto:module:git:info:dirty' format 'dirty_format'
    zformat -f dirty_formatted "$dirty_format" "D:$dirty"
  else
    zstyle -s ':prezto:module:git:info:clean' format 'clean_formatted'
  fi

  # Format info.
  zstyle -a ':prezto:module:git:info:keys' format 'info_formats'
  for info_format in ${(k)info_formats}; do
    zformat -f REPLY "$info_formats[$info_format]" \
      "a:$added_formatted" \
      "A:$ahead_formatted" \
      "B:$behind_formatted" \
      "b:$branch_formatted" \
      "C:$clean_formatted" \
      "c:$commit_formatted" \
      "d:$deleted_formatted" \
      "D:$dirty_formatted" \
      "i:$indexed_formatted" \
      "I:$unindexed_formatted" \
      "m:$modified_formatted" \
      "p:$position_formatted" \
      "R:$remote_formatted" \
      "r:$renamed_formatted" \
      "s:$action_formatted" \
      "S:$stashed_formatted" \
      "U:$unmerged_formatted" \
      "u:$untracked_formatted"
    git_info[$info_format]="$REPLY"
  done

  unset REPLY

  return 0
}

git-info "$@"
