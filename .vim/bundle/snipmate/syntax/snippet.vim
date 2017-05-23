" Syntax highlighting for snippet files (used for snipMate.vim)
" Hopefully this should make snippets a bit nicer to write!
syn match snipComment '^#.*'
syn match placeHolder '\${\d\+\(:.\{-}\)\=}' contains=snipCommand
syn match tabStop '\$\d\+'
syn match snipCommand '[^\\]`.\{-}`'
syn match snippet '^snippet.*' transparent contains=multiSnipText,snipKeyword
syn match multiSnipText '\S\+ \zs.*' contained
syn match snipKeyword '^snippet'me=s+8 contained
syn match snipError "^[^#s\t].*$"

hi link snipComment   Comment
hi link multiSnipText String
hi link snipKeyword   Keyword
hi link snipComment   Comment
hi link placeHolder   Special
hi link tabStop       Special
hi link snipCommand   String
hi link snipError     Error
