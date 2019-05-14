
function __maybe_toggle_dirtystate -d "Ignore dirty state if we're in the huge Chromium repo"
    # check if we're in a git repo. 
    if not git rev-parse ^ /dev/null
      return
    end
    # check if an origin remote exists
    if not git remote get-url origin > /dev/null ^&1
      return
    end
    set -l actualurl (git remote get-url origin)
    switch $actualurl
      case "*chromium.googlesource.com*"
        git config bash.showDirtyState false
    end
end
