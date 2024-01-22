function note
    argparse --name=note 'f/file' 'd/date' -- $argv
    or return

    set -q $_flag_file; or set _flag_file (date +%F).md
    set -q _flag_date; or set _flag_date (date +%c)
    set -q path; or set path ~/projects/notes/journal

    cp -n $path/template $path/$_flag_file
    sed -i '' "s/{date}/$_flag_date/" $path/$_flag_file
end
