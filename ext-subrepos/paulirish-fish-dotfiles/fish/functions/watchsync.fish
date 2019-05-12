function watchsync
  #
  # Keep local path in sync with remote path
  # Ignore .git metadata if present
  #

  set -l local $argv[1]
  set -l remote $argv[2]

  if test -z "$local" -o -z "$remote"; and test -f .watchsync
    set -l config (cat .watchsync)
    set local $config[1]
    set remote $config[2]
  end

  if not test -d "$local" -a -d "$remote"
    echo ""
    echo "Missing valid path arguments; watchsync expects either of the following:"
    echo ""
    echo "  - sync paths passed as arguments: watchsync <from-path> <to-path>"
    echo "  - a .watchsync file in the current dir, containing the arguments"
    echo ""
    return 1
  end

  set -l excludeGit ""
  if test -d "$local/.git"
    set excludeGit "--exclude .git"
  end

  set -l excludeFromGitignore ""
  if test -f "$local/.gitignore"
    set excludeFromGitignore "--exclude-from=.gitignore"
  end

  echo ""
  echo "# Start watching '$local', syncing changes to '$remote'..."
  echo ""

  cd "$local"
  fswatch . "date +%H:%M:%S && rsync -iru --size-only $excludeGit $excludeFromGitignore --delete . \"$remote\""
end
