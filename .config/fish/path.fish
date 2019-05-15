
# Grab my $PATHs from ~/.extra
set -l PATH_DIRS (cat "$HOME/.extra" | grep "^PATH" | \
    # clean up bash PATH setting pattern
    sed "s/PATH=//" | sed "s/\\\$PATH://" | \
    # rewrite ~/ to use {$HOME}
    sed "s/~\//{\$HOME}\//")


set -l PA ""

for entry in (string split \n $PATH_DIRS)
    # resolve the {$HOME} substitutions
    set -l resolved_path (eval echo $entry)
    if test -d "$resolved_path"; # and not contains $resolved_path $PATH
        set PA $PA "$resolved_path"
    end
end

# # rvm
# if which -s rvm;
# 	set PA $PA $HOME/.rvm/gems/ruby-2.2.1/bin
# end


set -l paths "
# yarn binary
$HOME/.yarn/bin
$GOPATH/bin

# yarn global modules (hack for me)
$HOME/.config/yarn/global/node_modules/.bin
"

for entry in (string split \n $paths)
    # resolve the {$HOME} substitutions
    set -l resolved_path (eval echo $entry)
    if test -d "$resolved_path";
        set PA $PA "$resolved_path"
    end
end

# GO
set PA $PA "$HOME/.go/bin"

# Google Cloud SDK.
if test -f "$HOME/google-cloud-sdk/path.fish.inc"
    source "$HOME/google-cloud-sdk/path.fish.inc"
end

set --export PATH $PA $PATH
