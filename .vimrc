"colors and fonts {{{
syntax enable
" desert is only a fallback for when solarized (see plugins.vim) isn't installed
if empty(glob('~/.vim/plugged/vim-colors-solarized'))
    colors desert
endif
set background=dark

if has("gui_running")
    set guioptions-=T
    set t_Co=256
    set nu
endif
" }}}
" general settings {{{

set nocompatible
set history=300		           " keep 300 lines of command line history
set backspace=indent,eol,start "backspace config
" viminfo remembers the state of vim from session to session
"           +--Disable hlsearch while loading viminfo
"           | +--Remember marks for last 500 files
"           | |    +--Remember up to 10000 lines in each register
"           | |    |      +--Remember up to 1MB in each register
"           | |    |      |     +--Remember last 1000 search patterns
"           | |    |      |     |     +---Remember last 1000 commands
"           | |    |      |     |     |
"           v v    v      v     v     v
set viminfo=h,'500,<10000,s1000,/1000,:1000
set modelines=5
set virtualedit=block
set fileformats=unix,dos,mac "Default file types (in particular what line endings to use)
" }}}
" text, tab and indent {{{
set expandtab             "turn tabs into spaces
set shiftwidth=4
set tabstop=4
set smarttab              "might need to remove this
set ai                    "Auto indent
set shiftround
set wrap                  " Wrap lines
filetype plugin indent on " Enable file type detection.
" }}}
" user interface {{{
set showcmd	    	" display incomplete commands
set cursorline      " underline the current line
set wildmenu        " Turn on wild menu
set wildmode=list:longest,full
set showmatch       " show matching brackets when text indicator is over them
set ruler	    	" show the cursor position all the time
set whichwrap+=<,>,h,l
set statusline=%F%m%r%h%w\ [FORMAT=%{&ff}]\ [TYPE=%Y]\ [ASCII=\%03.3b]\ [HEX=\%02.2B]\ [POS=%04l,%04v][%p%%]\ [LEN=%L]
set laststatus=2    " always show statusline
set noerrorbells    " No sound on errors
set novisualbell
set t_vb=
set scrolloff=3     " Start scrolling three lines before bottom of window
set splitright      " make new vertical splits go to the right
" }}}
" search {{{
set ignorecase      " ignore case when searching
set infercase       " allow insert mode completion to be smart about matching
set smartcase       " don't ignore case when looking for Caps
set hlsearch        " highlight search terms
set incsearch       " show partial search matches
set magic           " set magic on for regex
set mat=2           " how long to blink the brackets
" Search down into subfolders
" Provides tab-completion for all file-related tasks
set path+=**
" }}}
" backup, swap files {{{
if has("vms")
  set nobackup		" do not keep a backup file, use versions instead
else
  set backup		" keep a backup file
endif
set backupdir=~/.vim/backups
set directory=~/.vim/swaps
set updatecount=10 "save file every 10 keystrokes?
set autowrite
if has('persistent_undo')
    set undodir=$HOME/.vim/undo
    set undofile
endif
" }}}
" leader Shortcuts {{{
" With a map leader it's possible to do extra key combinations
" like <leader>w saves the current file
let mapleader = ","
let g:mapleader = ","

" Fast saving
nmap <leader>w :w!<cr>

map <leader>hl :nohlsearch<CR>
map <leader>ma :make<cr>

" emulate pastetoggle with a normal mode mapping
nmap <leader>pp :setlocal paste! paste?<CR>

"Allow searching in visual block
"select block then hit <leader>/ to search.  Using <leader>/ again will search
"in the same block
map <leader>/ /\%V
vmap <leader>/ <Esc>/\%V

map <leader>t2 :setlocal shiftwidth = 2<cr>
map <leader>t4 :setlocal shiftwidth = 4<cr>
map <leader>t8 :setlocal shiftwidth = 8<cr>

"Save a file as root (,W)
noremap <leader>W :w !sudo tee % > /dev/null<CR>

"Cope
" Do :help cope if you are unsure what cope is. It's super useful!
map <leader>bc :botright cope<cr>
map <leader>cn :cn<cr>
map <leader>cp :cp<cr>


"Spell checking
"Pressing ,ss will toggle and untoggle spell checking
map <leader>ss :setlocal spell!<cr>

"Spelling Shortcuts using <leader>
map <leader>sn ]s
map <leader>sp [s
map <leader>sa zg
map <leader>s? z=

" Remove the Windows ^M - when the encodings gets messed up
noremap <Leader>m mmHmt:%s/<C-V><cr>//ge<cr>'tzt'm

" Open an terminal window
map <leader>z :botright terminal ++rows=10<cr>


" }}}
" mappings {{{
imap jk <Esc>
" }}}
" folding {{{
set foldmethod=indent " fold based on indent level
set foldnestmax=10    " max 10 depth
set foldenable        " don't fold files by default on open
set foldlevelstart=1  " start with fold level of 1
" }}}
" custom functions {{{
function! TrimTrailingWS ()
    if search('\s\+$', 'cnw')
        :%s/\s\+$//g
    endif
endfunction
"Double-delete to remove trailing whitespace...
map <silent> <BS><BS>  mz:call TrimTrailingWS()<CR>`z
" }}}
" autogroup {{{
" Only do this part when compiled with support for autocommands.
if has("autocmd")

  augroup vimrc_autocmd
    autocmd!

    " When editing a file, always jump to the last known cursor position.
    " Don't do it when the position is invalid or when inside an event handler
    " (happens when dropping a file on gvim).
    autocmd BufReadPost *
      \ if line("'\"") > 0 && line("'\"") <= line("$") |
      \   exe "normal g`\"" |
      \ endif

    " Automatically open the quickfix window when running :make
    " http://vim.wikia.com/wiki/Automatically_open_the_quickfix_window_on_:make
    autocmd QuickFixCmdPost [^l]* nested cwindow
    autocmd QuickFixCmdPost    l* nested lwindow
  augroup END

  if exists("+omnifunc")
      augroup vimrc_autocmd_omnifunc
        autocmd!
        autocmd Filetype *
                    \	if &omnifunc == "" |
                    \		setlocal omnifunc=syntaxcomplete#Complete |
                    \	endif
      augroup END
  endif

endif " has("autocmd")
" }}}
" plugins {{{
" Use ripgrep (installed via the Brewfile) over grep
" --smart-case: case-insensitive unless the pattern has an uppercase letter
set grepprg=rg\ --vimgrep\ --smart-case\ $*
set grepformat=%f:%l:%c:%m
let g:ackprg = 'rg --vimgrep --smart-case'
" Use rg in CtrlP for listing files. Fast and respects .gitignore
let g:ctrlp_user_command = 'rg %s --files --color=never --hidden --glob "!.git" --glob "!.DS_Store"'

runtime plugins.vim
" }}}

" vim:foldmethod=marker:foldlevel=0
