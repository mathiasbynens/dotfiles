# `which` plus symlink resolving
# requires: brew install coreutils
function whichlink --description "Use `which` along with symlink resolving"
    greadlink -f (which $argv)
end
