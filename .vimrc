set background=dark

"set the runtime path to include Vundle and initialize
set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()
	Plugin 'VundleVim/Vundle.vim'
	Plugin 'kien/ctrlp.vim'
	Plugin 'rking/ag.vim'
	Plugin 'mileszs/ack.vim'
	Plugin 'ncm2/ncm2'
	
	Plugin 'Xuyuanp/nerdtree-git-plugin' " improv: show a little star if dirty
	Plugin 'Raimondi/delimitMate'       " auto adds/removes closing brackets
	Plugin 'compnerd/arm64asm-vim'      " syntax: arm64 assembly
	Plugin 'ycm-core/YouCompleteMe'
	Plugin 'airblade/vim-gitgutter'
	Plugin 'editorconfig/editorconfig-vim'

	" color schemes
	Plugin 'morhetz/gruvbox'
	Plugin 'flazz/vim-colorschemes'
	Plugin 'preservim/tagbar'           " tagbar: list of tags
	Plugin 'preservim/nerdtree'
	Plugin 'arcticicestudio/nord-vim'
	Plugin 'whatyouhide/vim-gotham'
call vundle#end()

colorscheme Benokai 

filetype plugin indent on    " c
" alternatively, pass a path where Vundle should install plugins
"call vundle#begin('~/some/path/here')
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
" Don’t add empty newlines at the end of files
set binary
" Centralize backups, swapfiles and undo history
set backupdir=~/.vim/backups
set directory=~/.vim/swaps
if exists("&undodir")
set undodir=~/.vim/undo
endif

" Don’t create backups when editing files in certain directories
set backupskip=/tmp/*,/private/tmp/*

" Respect modeline in files
set modeline
set modelines=4
" Enable per-directory .vimrc files and disable unsafe commands in them
set exrc
set secure
" Enable line numbers
set number
" Enable syntax highlighting
syntax on
" Highlight current line
set cursorline
" Set the maximum textwidth to 80 characters
set textwidth=80
" Make tabs as wide as four spaces
" set tabstop=4
" Show “invisible” characters
set lcs=tab:▸\ ,trail:·,eol:¬,nbsp:_
set list
" Highlight searches
set hlsearch
" Ignore case of searches
set ignorecase
" Highlight dynamically as pattern is typed
set incsearch
" Always show status line
set laststatus=2
" Enable mouse in all modes
set mouse=a
" Disable error bells
set noerrorbells
" Don’t reset cursor to start of line when moving around.
set nostartofline
" Show the cursor position
set ruler
" Don’t show the intro message when starting Vim
set shortmess=aTI
" Show the current mode
set showmode
" Show the filename in the window titlebar
set title
" Show the (partial) command as it’s being typed
set showcmd
" Use relative line numbers
if exists("&relativenumber")
set relativenumber
au BufReadPost * set relativenumber
endif
" Start scrolling three lines before the horizontal window border
set scrolloff=3

" Strip trailing whitespace (,ss)
function! StripWhitespace()
let save_cursor = getpos(".")
let old_query = getreg('/')
:%s/\s\+$//e
call setpos('.', save_cursor)
call setreg('/', old_query)
endfunction

noremap <leader>ss :call StripWhitespace()<CR>
" Save a file as root (,W)
noremap <leader>W :w !sudo tee % > /dev/null<CR>

" Tab switching keymaps
noremap L :tabnext<CR>
noremap H :tabprev<CR>

" Automatic commands
if has("autocmd")
" Enable file type detection
filetype on
" Treat .json files as .js
autocmd BufNewFile,BufRead *.json setfiletype json syntax=javascript
" Treat .md files as Markdown
autocmd BufNewFile,BufRead *.md setlocal filetype=markdown
endif

set splitbelow
set splitright

digraph gy 127947
digraph gc 9989
digraph rx 10060
digraph cb 129395
digraph rn 127939
