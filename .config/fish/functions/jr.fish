function jr --wraps=vi\ -Os\ journal/\(date\ --date=\'-1\ day\'\ +\%F\).md\ journal/\(date\ +\%F\).md\ ops-work.md --description 'Open my journal in split mode'
    set journal_path ~/projects/notes/journal

    find $journal_path -type f \( ! -iname template \) -size -200c -delete

    set day_note $journal_path/(date +%F).md
    set look_back 1
    set prev_note $journal_path/(date -v "-"$look_back"d" +%F).md

    if not test -f $day_note
        note
    end

    while not test -f $prev_note
        set look_back (math $look_back+1)
        set prev_note $journal_path/(date -v "-"$look_back"d" +%F).md

        if test $look_back -gt 30
            vi -O ~/projects/notes/ops-work.md $day_note
            return
        end
    end

    vi ~/projects/notes/ops-work.md -c vs\ $prev_note\ \|\ sp\ $day_note $argv
end
