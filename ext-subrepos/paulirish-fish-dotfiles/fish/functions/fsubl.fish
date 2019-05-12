
function fsubl --description "Fuzzy search to open in sublime"
  if fzf > $TMPDIR/fzf.result
    subl (cat $TMPDIR/fzf.result)
  end
end
