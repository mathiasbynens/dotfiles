set ts=4		"Tabs to 4
set shiftwidth=4	"shift width equals tabs
set ignorecase		"ignore case for search opeartions
set number		"activate linenumbers
set autoindent		"set automatic shifting - zeileneinrücken
set paste           	"do not reformat when pasting stuff
set smartindent		"intelligent shifting - intelligentes einrücken
set showmatch		"show matching brackets
set langmenu=en_US.UTF-8 "set language to english
set background=dark	"set dark background color
colorscheme koehler

"customize gui
if has("gui_running")
	set guioptions-=T 				"no toolbar
	set guifont=Consolas:h11:cANSI	"set font to Consolas with size h11
endif

" enable syntax highlghting for shader files
filetype on
au BufNewFile,BufRead *.vert set filetype=c
au BufNewFile,BufRead *.frag set filetype=c
au BufNewFile,BufRead *.geom set filetype=c
"use arrow keys for window changing
nmap <silent> <A-Up> :wincmd k<CR>
nmap <silent> <A-Down> :wincmd j<CR>
nmap <silent> <A-Left> :wincmd h<CR>
nmap <silent> <A-Right> :wincmd l<CR>

" Colorizer Settings
:let g:colorizer_auto_filetype='css,html'
:let g:colorizer_skip_comments = 1

" Ideas from http://amix.dk/vim/vimrc.html

" Options for tabs
map tn :tabnew
map to :tabonly
map tc :tabclose
map tm :tabmove
map te :tabedit
nmap <silent> <S-tab> :tabnext<CR>
nmap <silent> <C-tab> :tabprevious<CR>

" return to last edit position when opening files
autocmd BufReadPost *
	\ if line("'\"") > 0 && line("'\"") <= line("$") |
	\	exe "normal! g`\"" |
 	\ endif

" Remember info about open buffers on close
set viminfo^=%
" use 'ss' to toggle spellchecking
map<leader>ss :setlocal spell!<cr>
"map :f to / and :fback to ?
map :f /
map :fback ?
"map :r to :%s/ for fast substitution
map :r :%s/
syntax on		"activate syntax highlighting

set diffexpr=MyDiff()
function MyDiff()
  let opt = '-a --binary '
  if &diffopt =~ 'icase' | let opt = opt . '-i ' | endif
  if &diffopt =~ 'iwhite' | let opt = opt . '-b ' | endif
  let arg1 = v:fname_in
  if arg1 =~ ' ' | let arg1 = '"' . arg1 . '"' | endif
  let arg2 = v:fname_new
  if arg2 =~ ' ' | let arg2 = '"' . arg2 . '"' | endif
  let arg3 = v:fname_out
  if arg3 =~ ' ' | let arg3 = '"' . arg3 . '"' | endif
  let eq = ''
  if $VIMRUNTIME =~ ' '
    if &sh =~ '\<cmd'
      let cmd = '""' . $VIMRUNTIME . '\diff"'
      let eq = '"'
    else
      let cmd = substitute($VIMRUNTIME, ' ', '" ', '') . '\diff"'
    endif
  else
    let cmd = $VIMRUNTIME . '\diff'
  endif
  silent execute '!' . cmd . ' ' . opt . arg1 . ' ' . arg2 . ' > ' . arg3 . eq
endfunction

"adjust status bar
"" Mode Indication -Prominent!
function! InsertStatuslineColor(mode)
  if a:mode == 'i'
    hi statusline guibg=red
    set cursorcolumn
  elseif a:mode == 'r'
    hi statusline guibg=blue
  else
    hi statusline guibg= magenta
  endif
endfunction

function! InsertLeaveActions()
  hi statusline guibg=green
  set nocursorcolumn
endfunction

au InsertEnter * call InsertStatuslineColor(v:insertmode)
au InsertLeave * call InsertLeaveActions()

" to handle exiting insert mode via a control-C
inoremap <c-c> <c-o>:call InsertLeaveActions()<cr><c-c>
" default the statusline to green when entering Vim
hi statusline guibg=green

" have a permanent statusline to color
"set laststatus=2
