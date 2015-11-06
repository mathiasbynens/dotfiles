set nocompatible

" set the runtime path to include Vundle and initialize
set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()
Plugin 'gmarik/vundle'

" Essentials
Plugin 'kien/ctrlp.vim'
Plugin 'tpope/vim-fugitive'
Plugin 'scrooloose/nerdtree'
Plugin 'Xuyuanp/nerdtree-git-plugin'
Plugin 'tpope/vim-surround'
Plugin 'benmills/vimux'
Plugin 'scrooloose/syntastic'
Plugin 'scrooloose/NERDCommenter'
Plugin 'bling/vim-airline'
Plugin 'ervandew/supertab'
Plugin 'majutsushi/tagbar'
Plugin 'airblade/vim-gitgutter'
"Plugin 'Valloric/YouCompleteMe'
"
" Python
"Plugin 'davidhalter/jedi-vim'
Plugin 'klen/python-mode'

" utilities
Plugin 'mileszs/ack.vim'
Plugin 'chrisbra/csv.vim'
Plugin 'jceb/vim-orgmode'
Plugin 'google/yapf'
Plugin 'elzr/vim-json'

" Plugin 'Raimondi/delimitMate'
" Plugin 'tpope/vim-commentary'
" Plugin 'tpope/vim-unimpaired'
" Plugin 'tpope/vim-endwise'
" Plugin 'tpope/vim-ragtag'
" Plugin 'tpope/vim-repeat'
" Plugin 'garbas/vim-snipmate'
" Plugin 'mattn/emmet-vim'
" Plugin 'editorconfig/editorconfig-vim'
" Plugin 'MarcWeber/vim-addon-mw-utils'
" Plugin 'tomtom/tlib_vim'
" Plugin 'sotte/presenting.vim'
" Plugin 'tpope/vim-dispatch'
" Plugin 'mtth/scratch.vim'
" Plugin 'itspriddle/vim-marked'
" Plugin 'tpope/vim-vinegar'
" Plugin 'ap/vim-css-color'
" Plugin 'davidoc/taskpaper.vim'
" Plugin 'tpope/vim-abolish'
" Plugin 'AndrewRadev/splitjoin.vim'
" Plugin 'godlygeek/tabular'
" Plugin 'gbigwood/Clippo'
" Plugin 'vim-scripts/matchit.zip'
" Plugin 'gregsexton/MatchTag'
" Plugin 'tpope/vim-sleuth' " detect indent style (tabs vs. spaces)
" Plugin 'sickill/vim-pasta'
" Plugin 'junegunn/goyo.vim'
"
" " colorschemes
Plugin 'altercation/vim-colors-solarized'
" Plugin 'chriskempson/base16-vim'
"
" " JavaScript
" Plugin 'hail2u/vim-css3-syntax'
" Plugin 'othree/html5.vim'
" Plugin 'pangloss/vim-javascript'
" Plugin 'jelera/vim-javascript-syntax'
" " Plugin 'jason0x43/vim-js-syntax'
" " Plugin 'jason0x43/vim-js-indent'
" Plugin 'wavded/vim-stylus'
" Plugin 'groenewege/vim-less'
" Plugin 'digitaltoad/vim-jade'
" Plugin 'juvenn/mustache.vim'
" Plugin 'moll/vim-node'
" Plugin 'leafgarland/typescript-vim'
" Plugin 'mxw/vim-jsx'
" Plugin 'cakebaker/scss-syntax.vim'
" " Plugin 'dart-lang/dart-vim-plugin'
" " Plugin 'kchmck/vim-coffee-script'
" " Plugin 'marijnh/tern_for_vim'
"
" " languages
" Plugin 'tpope/vim-markdown'
" Plugin 'fatih/vim-go'
" " Plugin 'tclem/vim-arduino'
" Plugin 'timcharper/textile.vim'

" Misc
" Plugin 'mhinz/vim-startify'


call vundle#end()
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" => General
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Sets how many lines of history VIM has to remember
set history=700

" Enable filetype plugins
filetype plugin on
filetype indent on

" Set to auto read when a file is changed from the outside
set autoread

" Fast saving
nmap <leader>w :w!<cr>

" switch between panels
noremap <LEFT> <C-W>h
noremap <C-h> <C-W>h
inoremap <LEFT> <ESC><C-W>h
inoremap <C-h> <ESC><C-W>h

noremap <RIGHT> <C-W>l
noremap <C-l> <C-W>l
inoremap <RIGHT> <ESC><C-W>l
inoremap <C-l> <ESC><C-W>l

noremap <TOP> <C-W>k
noremap <C-k> <C-W>k
inoremap <TOP> <ESC><C-W>k
inoremap <C-k> <ESC><C-W>k

noremap <BOTTOM> <C-W>j
noremap <C-j> <C-W>j
inoremap <BOTTOM> <ESC><C-W>j
inoremap <C-j> <ESC><C-W>j

" F1 - Toggle
noremap <F1> :e#<cr>
inoremap <F1> <ESC>:e#<cr>

" F2 - next buffer
noremap <F2> :bnext<cr>
inoremap <F2> <ESC>:bnext<cr>

" F3 - NERDTreeFind
noremap <F3> :NERDTreeFind<CR>
inoremap <F3> <ESC>:NERDTreeFind<CR>

" F4 - Tagbar 
nmap <F4> :TagbarToggle<CR>

" F5 - Tagbar
noremap <F5> :noautocmd vimgrep 
inoremap <F5> <ESC>:noautocmd vimgrep 

" Printing filename and linenumber
noremap <leader>p :echo "In file"expand("%:t")"at line"<CR>


" Switch between panels / resize panels
"noremap <F1> <C-W>h:vertical resize 120<cr>
"inoremap <F1> <ESC><C-W>h:vertical resize 120<cr>

"noremap <F2> <C-W>l:vertical resize 120<cr>
"inoremap <F2> <ESC><C-W>l:vertical resize 120<cr>

"noremap <F3> <C-W>=
"inoremap <F3> <ESC><C-W>=i

" Switch buffers
"noremap <F4> :e#<cr>
"inoremap <F4> <ESC>:e#<cr>

" - search command (grep equivalent)
"noremap <F5> :noautocmd vimgrep 
"inoremap <F5> <ESC>:noautocmd vimgrep 



"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" => VIM user interface
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Set 7 lines to the cursor - when moving vertically using j/k
set so=7

" Ignore compiled files
set wildignore=*.o,*~,*.pyc

"Always show current position
set ruler

" Height of the command bar
set cmdheight=2

" A buffer becomes hidden when it is abandoned
set hid

" Configure backspace so it acts as it should act
set backspace=eol,start,indent
set whichwrap+=<,>,h,l

" Ignore case when searching
set ignorecase

" When searching try to be smart about cases 
set smartcase

" Highlight search results
set hlsearch

" Makes search act like search in modern browsers
set incsearch

" Don't redraw while executing macros (good performance config)
set lazyredraw

" For regular expressions turn magic on
set magic

" Show matching brackets when text indicator is over them
set showmatch
" How many tenths of a second to blink when matching brackets
set mat=2

" No annoying sound on errors
set noerrorbells
set novisualbell
set t_vb=
set tm=500

" Vim Indent guides
let g:indent_guides_enable_on_vim_startup = 0

" No beeps
set noerrorbells visualbell t_vb=
autocmd GUIEnter * set visualbell t_vb=


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" => Colors and Fonts
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Enable syntax highlighting
syntax enable
set background=dark
colorscheme solarized
let g:solarized_termcolors=256

" Set extra options when running in GUI mode
if has("gui_running")
    set guioptions-=T
    set guioptions+=e
    set t_Co=256
    set guitablabel=%M\ %t
endif

" Set utf8 as standard encoding and en_US as the standard language
set encoding=utf8

" Use Unix as the standard file type
set ffs=unix,dos,mac


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"=> Files, backups and undo
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Turn backup off, since most stuff is in SVN, git et.c anyway...
set nobackup
set nowb
set noswapfile


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" => Text, tab and indent related
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Use spaces instead of tabs
set expandtab

" Be smart when using tabs ;)
set smarttab

" 1 tab == 4 spaces
set shiftwidth=2
set tabstop=2
set sw=2
set sts=2

" Linebreak on 500 characters
set lbr
set tw=500

set ai "Auto indent
set si "Smart indent
set wrap "Wrap lines

" Show wich line is selected
set cursorline

" Show line number
set number
"autocmd InsertEnter * :set number
"autocmd InsertLeave * :set relativenumber

" Use the OS clipboard by default (on versions compiled with `+clipboard`)
set clipboard=unnamed
" Enhance command-line completion
set wildmenu
" Allow cursor keys in insert mode
set esckeys
" Allow backspace in insert mode
set backspace=indent,eol,start
" Optimize for fast terminal connections
set ttyfast
" Add the g flag to search/replace by default
set gdefault
" Use UTF-8 without BOM
set encoding=utf-8 nobomb
" Change mapleader
let mapleader=","
" Auto run NERDTree
let g:NERDTreeWinPos = "right"
let g:NERDTreeQuitOnOpen = 1
let NERDTreeIgnore = ['\.pyc$']

" Tagbar
let g:tagbar_autofocus = 1
let g:tagbar_autoclose = 1
let g:tagbar_sort = 0

"Orgmode
let g:org_todo_keywords = ['TODO', 'CURRENT', 'WAITING', 'DONE']   

" Airline
set laststatus=2

" Python-mode
let g:pymode_rope = 1

" Don't lint on write
let g:pymode_lint_on_write = 1

" Don't autocomplete please (so slow)
let g:pymode_rope_completion = 1

" Disabling rope auto import
let g:pymode_rope_autoimport = 0 

" Documentation
let g:pymode_doc = 1
let g:pymode_doc_key = 'K'

"Linting
let g:pymode_lint = 1
let g:pymode_lint_checker = "pyflakes,pep8"
" Auto check on save
let g:pymode_lint_write = 1

" Support virtualenv
let g:pymode_virtualenv = 1

" Enable breakpoints plugin
let g:pymode_breakpoint = 1
let g:pymode_breakpoint_bind = '<leader>b'

" syntax highlighting
let g:pymode_syntax = 1
let g:pymode_syntax_all = 1
let g:pymode_syntax_indent_errors = g:pymode_syntax_all
let g:pymode_syntax_space_errors = g:pymode_syntax_all

" Don't autofold code
let g:pymode_folding = 0

syntax enable
set background=dark
colorscheme solarized

