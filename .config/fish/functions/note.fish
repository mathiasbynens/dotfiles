# Defined in - @ line 1
function note --wraps='cp ~/projects/notes/journal/template ~/projects/notes/journal/(date +%F).md' --description 'Make a new journal entry from a template.'
  cp ~/projects/notes/journal/template ~/projects/notes/journal/(date +%F).md;
  sed -i 's+{date}+'(date +%c)'+' ~/projects/notes/journal/(date +%F).md;
end
