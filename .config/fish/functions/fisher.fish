set -g fisher_version 3.2.9

function fisher -a cmd -d "fish package manager"
    set -q XDG_CACHE_HOME; or set XDG_CACHE_HOME ~/.cache
    set -q XDG_CONFIG_HOME; or set XDG_CONFIG_HOME ~/.config

    set -g fish_config $XDG_CONFIG_HOME/fish
    set -g fisher_cache $XDG_CACHE_HOME/fisher
    set -g fisher_config $XDG_CONFIG_HOME/fisher

    set -q fisher_path; or set -g fisher_path $fish_config

    for path in {$fish_config,$fisher_path}/{functions,completions,conf.d} $fisher_cache
        if test ! -d $path
            command mkdir -p $path
        end
    end

    if test ! -e $fisher_path/completions/fisher.fish
        echo "fisher complete" >$fisher_path/completions/fisher.fish
        _fisher_complete
    end

    if test -e $fisher_path/conf.d/fisher.fish
        switch "$version"
            case \*-\*
                command rm -f $fisher_path/conf.d/fisher.fish
            case 2\*
            case \*
                command rm -f $fisher_path/conf.d/fisher.fish
        end
    else
        switch "$version"
            case \*-\*
            case 2\*
                echo "fisher copy-user-key-bindings" >$fisher_path/conf.d/fisher.fish
        end
    end

    switch "$cmd"
        case {,self-}complete
            _fisher_complete
        case copy-user-key-bindings
            _fisher_copy_user_key_bindings
        case ls
            set -e argv[1]
            if test -s "$fisher_path/fishfile"
                set -l file (_fisher_fmt <$fisher_path/fishfile | _fisher_parse -R | command sed "s|@.*||")
                _fisher_ls | _fisher_fmt | command awk -v FILE="$file" "
                    BEGIN { for (n = split(FILE, f); ++i <= n;) file[f[i]] } \$0 in file && /$argv[1]/
                " | command sed "s|^$HOME|~|"
            end
        case self-update
            _fisher_self_update (status -f)
        case self-uninstall
            _fisher_self_uninstall
        case {,-}-v{ersion,}
            echo "fisher version $fisher_version" (status -f | command sed "s|^$HOME|~|")
        case {,-}-h{elp,}
            _fisher_help
        case ""
            _fisher_commit --
        case add rm
            if not isatty
                while read -l arg
                    set argv $argv $arg
                end
            end

            if test (count $argv) = 1
                echo "fisher: invalid number of arguments" >&2
                _fisher_help >&2
                return 1
            end

            _fisher_commit $argv
        case \*
            echo "fisher: unknown flag or command \"$cmd\"" >&2
            _fisher_help >&2
            return 1
    end
end

function _fisher_complete
    complete -ec fisher
    complete -xc fisher -n __fish_use_subcommand -a add -d "Add packages"
    complete -xc fisher -n __fish_use_subcommand -a rm -d "Remove packages"
    complete -xc fisher -n __fish_use_subcommand -a ls -d "List installed packages matching REGEX"
    complete -xc fisher -n __fish_use_subcommand -a --help -d "Show usage help"
    complete -xc fisher -n __fish_use_subcommand -a --version -d "$fisher_version"
    complete -xc fisher -n __fish_use_subcommand -a self-update -d "Update to the latest version"
    for pkg in (fisher ls)
        complete -xc fisher -n "__fish_seen_subcommand_from rm" -a $pkg
    end
end

function _fisher_copy_user_key_bindings
    if functions -q fish_user_key_bindings
        functions -c fish_user_key_bindings fish_user_key_bindings_copy
    end
    function fish_user_key_bindings
        for file in $fisher_path/conf.d/*_key_bindings.fish
            source $file >/dev/null 2>/dev/null
        end
        if functions -q fish_user_key_bindings_copy
            fish_user_key_bindings_copy
        end
    end
end

function _fisher_ls
    for pkg in $fisher_config/*/*/*
        command readlink $pkg; or echo $pkg
    end
end

function _fisher_fmt
    command sed "s|^[[:space:]]*||;s|^$fisher_config/||;s|^~|$HOME|;s|^\.\/*|$PWD/|;s|^https*:/*||;s|^github\.com/||;s|/*\$||"
end

function _fisher_help
    echo "usage: fisher add <package...>     Add packages"
    echo "       fisher rm  <package...>     Remove packages"
    echo "       fisher                      Update all packages"
    echo "       fisher ls  [<regex>]        List installed packages matching <regex>"
    echo "       fisher --help               Show this help"
    echo "       fisher --version            Show the current version"
    echo "       fisher self-update          Update to the latest version"
    echo "       fisher self-uninstall       Uninstall from your system"
    echo "examples:"
    echo "       fisher add jethrokuan/z rafaelrinaldi/pure"
    echo "       fisher add gitlab.com/foo/bar@v2"
    echo "       fisher add ~/path/to/local/pkg"
    echo "       fisher add <file"
    echo "       fisher rm rafaelrinaldi/pure"
    echo "       fisher ls | fisher rm"
    echo "       fisher ls fish-\*"
end

function _fisher_self_update -a file
    set -l url "https://raw.githubusercontent.com/jorgebucaran/fisher/master/fisher.fish"
    echo "fetching $url" >&2
    command curl -s "$url?nocache" >$file.

    set -l next_version (command awk '{ print $4 } { exit }' <$file.)
    switch "$next_version"
        case "" $fisher_version
            command rm -f $file.
            if test -z "$next_version"
                echo "fisher: cannot update fisher -- are you offline?" >&2
                return 1
            end
            echo "fisher is already up-to-date" >&2
        case \*
            echo "linking $file" | command sed "s|$HOME|~|" >&2
            command mv -f $file. $file
            source $file
            echo "updated to fisher $fisher_version -- hooray!" >&2
            _fisher_complete
    end
end

function _fisher_self_uninstall
    for pkg in (_fisher_ls)
        _fisher_rm $pkg
    end

    for file in $fisher_cache $fisher_config $fisher_path/{functions,completions,conf.d}/fisher.fish $fisher_path/fishfile
        echo "removing $file"
        command rm -Rf $file 2>/dev/null
    end | command sed "s|$HOME|~|" >&2

    for name in (set -n | command awk '/^fisher_/')
        set -e "$name"
    end

    functions -e (functions -a | command awk '/^_fisher/') fisher
    complete -c fisher --erase
end

function _fisher_commit -a cmd
    set -e argv[1]
    set -l elapsed (_fisher_now)
    set -l fishfile $fisher_path/fishfile

    if test ! -e "$fishfile"
        command touch $fishfile
        echo "created new fishfile in $fishfile" | command sed "s|$HOME|~|" >&2
    end

    set -l old_pkgs (_fisher_ls | _fisher_fmt)
    for pkg in (_fisher_ls)
        _fisher_rm $pkg
    end
    command rm -Rf $fisher_config
    command mkdir -p $fisher_config

    set -l next_pkgs (_fisher_fmt <$fishfile | _fisher_parse -R $cmd (printf "%s\n" $argv | _fisher_fmt))
    set -l actual_pkgs (_fisher_fetch $next_pkgs)
    set -l updated_pkgs
    for pkg in $old_pkgs
        if contains -- $pkg $actual_pkgs
            set updated_pkgs $updated_pkgs $pkg
        end
    end

    if test -z "$actual_pkgs$updated_pkgs$old_pkgs$next_pkgs"
        echo "fisher: nothing to commit -- try adding some packages" >&2
        return 1
    end

    set -l out_pkgs
    if test "$cmd" = "rm"
        set out_pkgs $next_pkgs
    else
        for pkg in $next_pkgs
            if contains -- (echo $pkg | command sed "s|@.*||") $actual_pkgs
                set out_pkgs $out_pkgs $pkg
            end
        end
    end

    printf "%s\n" (_fisher_fmt <$fishfile | _fisher_parse -W $cmd $out_pkgs | command sed "s|^$HOME|~|") >$fishfile

    _fisher_complete

    command awk -v A=(count $actual_pkgs) -v U=(count $updated_pkgs) -v O=(count $old_pkgs) -v E=(_fisher_now $elapsed) '
        BEGIN {
            res = fmt("removed", O - U, fmt("updated", U, fmt("added", A - U)))
            printf((res ? res : "done") " in %.2fs\n", E / 1000)
        }
        function fmt(action, n, s) {
            return n ? (s ? s ", " : s) action " " n " package" (n > 1 ? "s" : "") : s
        }
    ' >&2
end

function _fisher_parse -a mode cmd
    set -e argv[1..2]
    command awk -v FS="[[:space:]]*#+" -v MODE="$mode" -v CMD="$cmd" -v ARGSTR="$argv" '
        BEGIN {
            for (n = split(ARGSTR, a, " "); i++ < n;) pkgs[getkey(a[i])] = a[i]
        }
        !NF { next } { k = getkey($1) }
        MODE == "-R" && !(k in pkgs) && $0 = $1
        MODE == "-W" && (/^#/ || k in pkgs || CMD != "rm") { print pkgs[k] (sub($1, "") ? $0 : "") }
        MODE == "-W" || CMD == "rm" { delete pkgs[k] }
        END {
            for (k in pkgs) {
                if (CMD != "rm" || MODE == "-W") print pkgs[k]
                else print "fisher: cannot remove \""k"\" -- package is not in fishfile" > "/dev/stderr"
            }
        }
        function getkey(s,  a) {
            return (split(s, a, /@+|:/) > 2) ? a[2]"/"a[1]"/"a[3] : a[1]
        }
    '
end

function _fisher_fetch
    set -l pkg_jobs
    set -l out_pkgs
    set -l next_pkgs
    set -l local_pkgs
    set -q fisher_user_api_token; and set -l curl_opts -u $fisher_user_api_token

    for pkg in $argv
        switch $pkg
            case \~\* /\*
                set -l path (echo "$pkg" | command sed "s|^~|$HOME|")
                if test -e "$path"
                    set local_pkgs $local_pkgs $path
                else
                    echo "fisher: cannot add \"$pkg\" -- is this a valid file?" >&2
                end
                continue
        end

        command awk -v PKG="$pkg" -v FS=/ '
            BEGIN {
                if (split(PKG, tmp, /@+|:/) > 2) {
                    if (tmp[4]) sub("@"tmp[4], "", PKG)
                    print PKG "\t" tmp[2]"/"tmp[1]"/"tmp[3] "\t" (tmp[4] ? tmp[4] : "master")
                } else {
                    pkg = split(PKG, _, "/") <= 2 ? "github.com/"tmp[1] : tmp[1]
                    tag = tmp[2] ? tmp[2] : "master"
                    print (\
                        pkg ~ /^github/ ? "https://codeload."pkg"/tar.gz/"tag : \
                        pkg ~ /^gitlab/ ? "https://"pkg"/-/archive/"tag"/"tmp[split(pkg, tmp, "/")]"-"tag".tar.gz" : \
                        pkg ~ /^bitbucket/ ? "https://"pkg"/get/"tag".tar.gz" : pkg \
                    ) "\t" pkg
                }
            }
        ' | read -l url pkg branch

        if test ! -d "$fisher_config/$pkg"
            fish -c "
                echo fetching $url >&2
                command mkdir -p $fisher_config/$pkg $fisher_cache/(command dirname $pkg)
                if test ! -z \"$branch\"
                     command git clone $url $fisher_config/$pkg --branch $branch --depth 1 2>/dev/null
                     or echo fisher: cannot clone \"$url\" -- is this a valid url\? >&2
                else if command curl $curl_opts -Ss -w \"\" $url 2>&1 | command tar -xzf- -C $fisher_config/$pkg 2>/dev/null
                    command rm -Rf $fisher_cache/$pkg
                    command mv -f $fisher_config/$pkg/* $fisher_cache/$pkg
                    command rm -Rf $fisher_config/$pkg
                    command cp -Rf {$fisher_cache,$fisher_config}/$pkg
                else if test -d \"$fisher_cache/$pkg\"
                    echo fisher: cannot connect to server -- looking in \"$fisher_cache/$pkg\" | command sed 's|$HOME|~|' >&2
                    command cp -Rf $fisher_cache/$pkg $fisher_config/$pkg/..
                else
                    command rm -Rf $fisher_config/$pkg
                    echo fisher: cannot add \"$pkg\" -- is this a valid package\? >&2
                end
            " >/dev/null &
            set pkg_jobs $pkg_jobs (_fisher_jobs --last)
            set next_pkgs $next_pkgs "$fisher_config/$pkg"
        end
    end

    if set -q pkg_jobs[1]
        while for job in $pkg_jobs
                contains -- $job (_fisher_jobs); and break
            end
        end
        for pkg in $next_pkgs
            if test -d "$pkg"
                set out_pkgs $out_pkgs $pkg
                _fisher_add $pkg
            end
        end
    end

    set -l local_prefix $fisher_config/local/$USER
    if test ! -d "$local_prefix"
        command mkdir -p $local_prefix
    end
    for pkg in $local_pkgs
        set -l target $local_prefix/(command basename $pkg)
        if test ! -L "$target"
            command ln -sf $pkg $target
            set out_pkgs $out_pkgs $pkg
            _fisher_add $pkg --link
        end
    end

    if set -q out_pkgs[1]
        _fisher_fetch (
            for pkg in $out_pkgs
                if test -s "$pkg/fishfile"
                    _fisher_fmt <$pkg/fishfile | _fisher_parse -R
                end
            end)
        printf "%s\n" $out_pkgs | _fisher_fmt
    end
end

function _fisher_add -a pkg opts
    for src in $pkg/{functions,completions,conf.d}/**.* $pkg/*.fish
        set -l target (command basename $src)
        switch $src
            case $pkg/conf.d\*
                set target $fisher_path/conf.d/$target
            case $pkg/completions\*
                set target $fisher_path/completions/$target
            case $pkg/{functions,}\*
                switch $target
                    case uninstall.fish
                        continue
                    case {init,key_bindings}.fish
                        set target $fisher_path/conf.d/(command basename $pkg)\_$target
                    case \*
                        set target $fisher_path/functions/$target
                end
        end
        echo "linking $target" | command sed "s|$HOME|~|" >&2
        if set -q opts[1]
            command ln -sf $src $target
        else
            command cp -f $src $target
        end
        switch $target
            case \*.fish
                source $target >/dev/null 2>/dev/null
        end
    end
end

function _fisher_rm -a pkg
    for src in $pkg/{conf.d,completions,functions}/**.* $pkg/*.fish
        set -l target (command basename $src)
        set -l filename (command basename $target .fish)
        switch $src
            case $pkg/conf.d\*
                test "$filename.fish" = "$target"; and emit "$filename"_uninstall
                set target conf.d/$target
            case $pkg/completions\*
                test "$filename.fish" = "$target"; and complete -ec $filename
                set target completions/$target
            case $pkg/{,functions}\*
                test "$filename.fish" = "$target"; and functions -e $filename
                switch $target
                    case uninstall.fish
                        source $src
                        continue
                    case {init,key_bindings}.fish
                        set target conf.d/(command basename $pkg)\_$target
                    case \*
                        set target functions/$target
                end
        end
        command rm -f $fisher_path/$target
    end
    if not functions -q fish_prompt
        source "$__fish_datadir$__fish_data_dir/functions/fish_prompt.fish"
    end
end

function _fisher_jobs
    jobs $argv | command awk '/^[0-9]+\t/ { print $1 }'
end

function _fisher_now -a elapsed
    switch (command uname)
        case Darwin \*BSD
            command perl -MTime::HiRes -e 'printf("%.0f\n", (Time::HiRes::time() * 1000) - $ARGV[0])' $elapsed
        case \*
            math (command date "+%s%3N") - "0$elapsed"
    end
end
