runtime syntax/diff.vim
setlocal filetype=

syntax match gitStatusComment   +^#.*+ contains=ALL

syntax match gitStatusBranch    +On branch .\++

syntax match gitStatusUndracked +\t\zs.\++
syntax match gitStatusNewFile   +\t\zsnew file: .\++
syntax match gitStatusModified  +\t\zsmodified: .\++

highlight link gitStatusComment     Comment

highlight link gitStatusBranch      Title

highlight link gitStatusUndracked   diffOnly
highlight link gitStatusNewFile     diffAdded
highlight link gitStatusModified    diffChanged

