# https://github.com/roryokane/z-fish/blob/master/z.fish

# maintains a jump-list of the directories you actually use
#
# INSTALL:
#   * put something like this in your config.fish:
#     source /path/to/z.fish
#   * cd around for a while to build up the db
#   * PROFIT!!
#
# USE:
#   * z foo     # cd to most frecent dir matching foo
#   * z foo bar # cd to most frecent dir matching foo and bar
#   * z -r foo  # cd to highest ranked dir matching foo
#   * z -t foo  # cd to most recently accessed dir matching foo
#   * z -l foo  # list matches instead of cd
#   * z -c foo  # restrict matches to subdirs of $PWD

complete -x -c z -a '(z --complete (commandline -t))'

function addzhist --on-variable PWD
  z --add "$PWD"
end

function z -d "Jump to a recent directory."
    if not set -q z_datafile
        set -g z_datafile "$HOME/.z"
    end

    # add entries
    if [ "$argv[1]" = "--add" ]
        set -e argv[1]

        # $HOME isn't worth matching
        [ "$argv" = "$HOME" ]; and return

        set -l tempfile (command mktemp $z_datafile.XXXXXX)
        test -f $tempfile; or return

        # maintain the file
        command awk -v path="$argv" -v now=(date +%s) -F"|" '
            BEGIN {
                rank[path] = 1
                time[path] = now
            }
            $2 >= 1 {
                if( $1 == path ) {
                    rank[$1] = $2 + 1
                    time[$1] = now
                } else {
                    rank[$1] = $2
                    time[$1] = $3
                }
                count += $2
            }
            END {
                if( count > 6000 ) {
                    for( i in rank ) print i "|" 0.9*rank[i] "|" time[i] # aging
                } else for( i in rank ) print i "|" rank[i] "|" time[i]
            }
        ' $z_datafile ^/dev/null > $tempfile
        if [ $status -ne 0 -a -f $z_datafile ]
            command rm -f "$tempfile"
        else
            command mv -f "$tempfile" "$z_datafile"
        end

    # tab completion
    else
        if [ "$argv[1]" = "--complete" ]
            command awk -v q="$argv[2]" -F"|" '
                BEGIN {
                    if( q == tolower(q) ) nocase = 1
                    split(q,fnd," ")
                }
                {
                    if( system("test -d \"" $1 "\"") ) next
                    if( nocase ) {
                        for( i in fnd ) tolower($1) !~ tolower(fnd[i]) && $1 = ""
                        if( $1 ) print $1
                    } else {
                        for( i in fnd ) $1 !~ fnd[i] && $1 = ""
                        if( $1 ) print $1
                    }
                }
            ' "$z_datafile" 2>/dev/null

        else
            # list/go
            set -l last ''
            set -l list 0
            set -l typ ''
            set -l fnd ''

            while [ (count $argv) -gt 0 ]
                switch "$argv[1]"
                    case -- '--'
                        while [ "$argv[1]" ]
                            set -e argv[1]
                            set fnd "$fnd $argv[1]"
                        end
                    case -- '-*'
                        set -l opt (echo $argv[1] | cut -b2-)
                        while [ "$opt" ]
                            switch (echo $opt | cut -b1)
                                case -- 'c'
                                    set fnd "^$PWD $fnd"
                                case -- 'h'
                                    echo "z [-chlrt] args" >&2
                                    return
                                case -- 'l'
                                    set list 1
                                case -- 'r'
                                    set typ "rank"
                                case -- 't'
                                    set typ "recent"
                            end
                            set -l opt (echo $opt | cut -b2-)
                        end
                    case '*'
                        set fnd "$fnd $argv[1]"
                end
                set last $argv[1]
                set -e argv[1]
            end

            [ "$fnd" -a "$fnd" != "^$PWD " ]; or set list 1

            # if we hit enter on a completion just go there
            switch "$last"
                # completions will always start with /
                case -- '/*'
                    [ -z "$list" -a -d "$last" ]; and cd "$last"; and return
            end

            # no file yet
            [ -f "$z_datafile" ]; or return

            set -l cd (command awk -v t=(date +%s) -v list="$list" -v typ="$typ" -v q="$fnd" -v z_datafile="$z_datafile" -F"|" '
            function notdir(path, tmp) {
                n = gsub("/+", "/", path)
                for( i = 0; i < n; i++ ) path = path "/.."
                path = path z_datafile
                if( ( getline tmp < path ) >= 0 ) {
                    close(path)
                    return 0
                }
                return 1
            }
            function frecent(rank, time) {
                dx = t-time
                if( dx < 3600 ) return rank*4
                if( dx < 86400 ) return rank*2
                if( dx < 604800 ) return rank/2
                return rank/4
            }
            function output(files, toopen, override) {
                if( list ) {
                    cmd = "sort -n >&2"
                    for( i in files ) if( files[i] ) printf "%-10s %s\n", files[i], i | cmd
                    if( override ) printf "%-10s %s\n", "common:", override > "/dev/stderr"
                } else {
                    if( override ) toopen = override
                    print toopen
                }
            }
            function common(matches) {
                # shortest match
                for( i in matches ) {
                    if( matches[i] && (!short || length(i) < length(short)) ) short = i
                }
                if( short == "/" ) return
                # shortest match must be common to each match. escape special characters in
                # a copy when testing, so we can return the original.
                clean_short = short
                gsub(/[\(\)\[\]\|]/, "\\\\&", clean_short)
                for( i in matches ) if( matches[i] && i !~ clean_short ) return
                return short
            }
            BEGIN { split(q, a, " "); oldf = noldf = -9999999999 }
            {
                if( notdir($1) ) {next}
                if( typ == "rank" ) {
                    f = $2
                } else if( typ == "recent" ) {
                    f = $3-t
                } else f = frecent($2, $3)
                    wcase[$1] = nocase[$1] = f
                for( i in a ) {
                    if( $1 !~ a[i] ) delete wcase[$1]
                    if( tolower($1) !~ tolower(a[i]) ) delete nocase[$1]
                }
                if( wcase[$1] && wcase[$1] > oldf ) {
                    cx = $1
                    oldf = wcase[$1]
                } else if( nocase[$1] && nocase[$1] > noldf ) {
                    ncx = $1
                    noldf = nocase[$1]
                }
            }
            END {
                if( cx ) {
                    output(wcase, cx, common(wcase))
                } else if( ncx ) output(nocase, ncx, common(nocase))
            }' $z_datafile)

            [ $status -gt 0 ]; and return
            [ "$cd" ]; and cd "$cd"
        end
    end
end