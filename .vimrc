""""""""""""""""""""""""""
" => General
"""""""""""""""""""""""""
" Set to auto read when file is changed from outside
set autoread
 
" Sets how many lines of history VIM has to remember
set history=700
 
" Enable filetype plugins
filetype plugin on
filetype indent on
 
" Fast saving
nmap <leader>w :w!<cr>
 
"""""""""""""""""""""""""
" => VIM user interface
"""""""""""""""""""""""""
" Set 10 lines to cursor 
set so=7
 
" Enable mouse
set mouse=a
 
" Turn on wild menu
set wildmenu
 
" Ignore compiled files
set wildignore=*.o,*~,*.pyc
 
" Always show current position
set ruler
set columns=95
set colorcolumn=80
set number
 
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
 
"""""""""""""""""""""""""
" => Syntax
"""""""""""""""""""""""""
filetype on
syntax enable
autocmd BufRead,BufNewFile *.py let python_highlight_all=1
let g:html5_event_handler_attributes_complete = 1 
 
""""""""""""""""""""""""""""
" => Text, tab, and indent related
""""""""""""""""""""""""""""
" use spaces instead of tabs
set expandtab
 
" 1 tab == 4 spaces
set shiftwidth=4
set tabstop=4
set softtabstop=4
 
" indenting
set autoindent
set copyindent
 
" Auto indent
set ai
 
" Smart indent
set si
 
" Wrap lines
set wrap
 
""""""""""""""""""""""""""""""
" => Status line
"""""""""""""""""""""""""""""
" Always show the status line
set laststatus=2
 
"""""""""""""""""""""""""""""
" => Moving around
"""""""""""""""""""""""""""""
" Disable highlight when <leader><cr> is pressed
map <silent> <leader><cr> :noh<cr>
 
" Useful mappings for managing tabs
map <leader>tn :tabnew<cr>
map <leader>to :tabonly<cr>
map <leader>tc :tabclose<cr>
map <leader>tm :tabmove
