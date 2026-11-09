set makeprg=$HOME/.vim/makeprg/vimparse.pl\ %\ $*
"set makeprg=$HOME/.vim/makeprg/vimparse.pl\ -c\ %\ $*
"set tags+=$HOME/.vim/tags/perl.ctags
set tags=./tags;/,tags;/
set errorformat=%f:%l:%m
let g:perl_fold=1
let perl_fold=1
let g:perl_cuddle_indent=1
set keywordprg=perldoc\ -T\ -f "let K call perldoc instead of man
"set define=^\\s*sub This was set by vim-perl

" Tidy selected lines (or entire file) with _t:
nnoremap <silent> <leader>ti :%!perltidy -q<Enter>
vnoremap <silent> <leader>ti :!perltidy -q<Enter>

" Deparse obfuscated code
nnoremap <silent> <leader>d :.!perl -MO=Deparse 2>/dev/null<cr>
vnoremap <silent> <leader>d :!perl -MO=Deparse 2>/dev/null<cr>

" Run the current program
nmap <leader>r :!perl %<cr>

" Tame <c-p> and <c-n> for ins-complete a bit.  This will prevent keyword completion from
" scanning all included perl modules which can slow things down a bit
set complete-=i

" Allow <c-p> and <c-n> to recognize ':' as significant.  Enables ins-complete
" on module names
set iskeyword+=:
