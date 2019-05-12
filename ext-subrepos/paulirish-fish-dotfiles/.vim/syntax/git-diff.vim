runtime syntax/diff.vim

syntax match gitDiffStatLine /^ .\{-}\zs[+-]\+$/ contains=gitDiffStatAdd,gitDiffStatDelete
syntax match gitDiffStatAdd    /+/ contained
syntax match gitDiffStatDelete /-/ contained

highlight gitDiffStatAdd    ctermfg=2
highlight gitDiffStatDelete ctermfg=5

