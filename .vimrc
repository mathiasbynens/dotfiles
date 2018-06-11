set nocompatible              " be iMproved, required
filetype off                  " required

" set the runtime path to include Vundle and initialize
set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()
" alternatively, pass a path where Vundle should install plugins
"call vundle#begin('~/some/path/here')

" let Vundle manage Vundle, required
Plugin 'VundleVim/Vundle.vim'

" The following are examples of different formats supported.
" Keep Plugin commands between vundle#begin/end.

" UI "
Plugin 'flazz/vim-colorschemes'             " color schemes "
Plugin 'mhinz/vim-startify'                 " startup screen "
Plugin 'vim-airline/vim-airline'            " git status bar "
Plugin 'vim-airline/vim-airline-themes'     " git status bar themes "

" TOOLS "
Plugin 'kien/ctrlp.vim'                     " fuzzy search "
Plugin 'airblade/vim-gitgutter'             " git diff next to ruler "
Plugin 'scrooloose/nerdtree'                " sitemap in sidebar "
Plugin 'ternjs/tern_for_vim'                " provides Tern-based JavaScript editing support, for youcompleteme"
Plugin 'valloric/youcompleteme'             " fuzzy-search code completion engine "
Plugin 'ap/vim-css-color'                   " color values as a color in css "
Plugin 'qpkorr/vim-bufkill'                 " nload, delete or wipe a buffer without closing the window or split "

" SYNTAX "
Plugin 'tscout6/syntastic-local-eslint.vim' " local eslint config loading "
Plugin 'scrooloose/syntastic'               " syntax checking "
"Plugin 'leafgarland/typescript-vim'         " Syntax file and other settings for TypeScript "
"Plugin 'mxw/vim-jsx'                        " Syntax highlighting and indenting for JSX "
Plugin 'pangloss/vim-javascript'            " provides syntax highlighting and improved indentation "
Plugin 'posva/vim-vue'                      " .vue support "

" INPUT "
Plugin 'alvan/vim-closetag'                 " Auto-close HTML nodes "
Plugin 'heavenshell/vim-jsdoc'              " javascript function documentation "
Plugin 'yggdroot/indentline'                " indent lines "
Plugin 'mattn/emmet-vim'                    " expanding abbreviations "
Plugin 'Raimondi/delimitMate'               " automatic closing of quotes, parenthesis, brackets, etc "

" All of your Plugins must be added before the following line "
call vundle#end()            " required
filetype plugin indent on    " required
" To ignore plugin indent changes, instead use:
"filetype plugin on
"
" Brief help
" :PluginList       - lists configured plugins
" :PluginInstall    - installs plugins; append `!` to update or just :PluginUpdate
" :PluginSearch foo - searches for foo; append `!` to refresh local cache
" :PluginClean      - confirms removal of unused plugins; append `!` to auto-approve removal
"
" see :h vundle for more details or wiki for FAQ
" Put your non-Plugin stuff after this line
let mapleader=" "

" Appearance "
syntax on
set background=dark
set guifont=SauceCodePro\ Nerd\ Font:h15
"set guifont=Source\ Code\ Pro\ for\ Powerline:h15 "make sure to escape the spaces in the name properly
set guioptions=                     " remove scrollbars in macVim "
set noerrorbells                    " no error bells "
set visualbell                      " use visual bell "
set ruler                           " show the line number on the bar "
set cursorline                      " highlight current line "
set cursorcolumn                    " highlight current column "
set number                          " line numbers "
set cmdheight=1                     " command line two lines high "
set scrolloff=5                     " keep at least 5 lines above/below "
set sidescrolloff=5                 " keep at least 5 lines left/right "
set nocompatible                    " Make Vim more useful "
set clipboard=unnamed               " Use the OS clipboard by default (on versions compiled with `+clipboard`) "
set nowrap                          " do not automatically wrap on load "
set formatoptions-=t                " do not automatically wrap text when typing "
set wildmenu                        " Enhance command-line completion "
set esckeys                         " Allow cursor keys in insert mode "
set linespace=0
set backspace=indent,eol,start      " Allow backspace in insert mode "
set ttyfast                         " Optimize for fast terminal connections "
set gdefault                        " Add the g flag to search/replace by default "
set encoding=utf-8                  " Use UTF-8 "
set binary                          " Don’t add empty newlines at the end of files "
set noeol                           ""
set modeline                        " Respect modeline in files "
set modelines=4
set exrc                            " Enable per-directory .vimrc files and disable unsafe commands in them "
set secure
set lcs=tab:▸\ ,trail:·,eol:¬,nbsp:_ " invisible charachters to show "
set list                            " Show “invisible” characters "
set hlsearch                        " Highlight searches "
set ignorecase                      " Ignore case of searches "
set smartcase                       " when using capital in search then use capital-sentitive search "
set incsearch                       " Highlight dynamically as pattern is typed "
set laststatus=2                    " Always show status line "
set mouse=a                         " Enable mouse in all modes "
set nostartofline                   " Don’t reset cursor to start of line when moving around. "
set shortmess=atI                   " Don’t show the intro message when starting Vim "
set showmode                        " Show the current mode "
set title                           " Show the filename in the window titlebar "
set showcmd                         " Show the (partial) command as it’s being typed "
set scrolloff=3                     " Start scrolling three lines before the horizontal window border "
set autoindent smartindent          " auto/smart indent "
set smarttab                        " tab and backspace are smart "
set softtabstop=4                   " control how many columns vim uses when you hit Tab in insert mode "
set shiftwidth=4                    " control how many columns text is indented with the reindent operations (<< and >>) "
set expandtab                       " When expandtab is set, hitting Tab in insert mode will produce the appropriate number of spaces "
syntax match Tab /\t/
hi Tab gui=underline guifg=blue ctermbg=red

autocmd BufNewFile,BufRead * :e ++ff=dos

if hlID('CarriageReturn')
  match CarriageReturn /\r$/
endif

" HTML auto-complete CTRL+SPACE"
imap <C-Space> <C-X><C-O>

" splits "
set wmh=0                           " current line only in active buffer "

nnoremap <C-J> <C-W><C-J>           " ctrl + [j,k,l,h] to move in plits "
nnoremap <C-K> <C-W><C-K>
nnoremap <C-L> <C-W><C-L>
nnoremap <C-H> <C-W><C-H>

map <leader>j :bnext<CR>            " hotkey to next buffer "
map <leader>k :bprev<CR>            " hotkey to previous buffer "
nnoremap c :bp\|bd #<CR>            " go to the previous buffer, then delete the last buffer "
nnoremap <leader>b :ls<CR>:b<Space>

" line endings "
map <leader><leader>! e ++ff=dos

" This give me a command :B (and a mapping) which calls the function :buffers "
" wait for an input and finally calls :b followed by the input. "
nnoremap ,b :buffer *
set wildmenu
set wildignore+=*.swp,*.bak
set wildignore+=*.pyc,*.class,*.sln,*.Master,*.csproj,*.csproj.user,*.cache,*.dll,*.pdb,*.min.*
set wildignore+=*/.git/**/*,*/.hg/**/*,*/.svn/**/*
set wildignore+=*/min/*,*/vendor/*,*/node_modules/*,*/bower_components/*
set wildignore+=tags,cscope.*
set wildignore+=*.tar.*
set wildignorecase
set wildmode=full

" Strip trailing whitespace (,ss) "
function! StripWhitespace()
    let save_cursor = getpos(".")
    let old_query = getreg('/')
    :%s/\s\+$//e
    call setpos('.', save_cursor)
    call setreg('/', old_query)
endfunction
noremap <leader>ss :call StripWhitespace()<CR>
noremap <leader>W :w !sudo tee % > /dev/null<CR>                            " Save a file as root (,W) "

" Automatic commands "
"if has("autocmd")
    filetype on                                                             " Enable file type detection "
    autocmd BufNewFile,BufRead *.json setfiletype json syntax=JavaScript    " Treat .json files as .js "
    autocmd BufNewFile,BufRead *.md setlocal filetype=markdown              " Treat .md files as Markdown "
    autocmd BufNewFile,BufRead *.ts setlocal filetype=typescript
"endif

" Centralize backups, swapfiles and undo history "
set backupdir=~/.vim/backups
set directory=~/.vim/swaps
if exists("&undodir")
    set undodir=~/.vim/undo
endif

" Don’t create backups when editing files in certain directories "
set backupskip=/tmp/*,/private/tmp/*,/node_modules,/bower_components

" PLUGINS "
" Airline "
let g:airline#extensions#tabline#enabled = 1    " Automatically displays all buffers when there's only one tab open. "
let g:airline_powerline_fonts = 1

" AUTO CLOSE XML/HTML "
" filenames like *.xml, *.html, *.xhtml, ...
" Then after you press <kbd>&gt;</kbd> in these files, this plugin will try to close the current tag.
"
let g:closetag_filenames = '*.html,*.xhtml,*.phtml'

" filenames like *.xml, *.xhtml, ...
" This will make the list of non closing tags self closing in the specified files.
"
let g:closetag_xhtml_filenames = '*.xhtml,*.jsx'

" integer value [0|1]
" This will make the list of non closing tags case sensitive (e.g. `<Link>` will be closed while `<link>` won't.)
"
let g:closetag_emptyTags_caseSensitive = 1

" Shortcut for closing tags, default is '>'
"
let g:closetag_shortcut = '>'

" Add > at current position without closing the current tag, default is ''
"
let g:closetag_close_shortcut = '<leader>>'

" CTRLP "
" Setup some default ignores "
let g:ctrlp_custom_ignore = {
  \ 'dir':  '\v[\/](node_modules|bower_components|dist|build)|(\.(git|hg|svn)|\_site)$',
  \ 'file': '\v\.(exe|so|dll|class|png|jpg|jpeg)$',
\}

" Open with new tab for ctrlp "
"let g:ctrlp_prompt_mappings = {
"    \ 'AcceptSelection("e")': ['<C-e>'],
"    \ 'AcceptSelection("t")': ['<Cr>'],
"\}

" Use the nearest .git directory as the cwd "
" This makes a lot of sense if you are working on a project that is in version "
" control. It also supports works with .svn, .hg, .bzr. "
" let g:ctrlp_working_path_mode = 'r'

" Use NerdTree folder as CTRL search directoryh
let g:NERDTreeChDirMode       = 2
let g:ctrlp_working_path_mode = 'rw'

" Use a leader instead of the actual named binding "
nmap <leader>p :CtrlP<cr>

" Easy bindings for its various modes "
nmap <leader>bb :CtrlPBuffer<cr>
nmap <leader>bm :CtrlPMixed<cr>
nmap <leader>bs :CtrlPMRU<cr>

" GitGutter "
set updatetime=250              " refresh rate for diff makers "

" Javascript libraries syntax "
let g:used_javascript_libs = 'angularjs,backbone,chai,d3,flux,jquery,react,underscore,vue'

" JSX for .js files
let g:jsx_ext_required = 0

" JS doc
nmap <silent> <C-D> <Plug>(jsdoc)
let g:jsdoc_allow_input_prompt = 1  "Allow prompt for interactive input"
let g:jsdoc_input_description = 1   "Prompt for a function description"
let g:jsdoc_return = 1              "Add the @return tag"

" Nerd tree
cd ~/development                  " navigate to development folder "
let NERDTreeShowHidden=1          " show hidden files "
" autocmd VimEnter * NERDTree     " start NERDtree on startup "
" autocmd VimEnter * wincmd p     " dont focus NERDtree on startup "
nmap <leader>n :NERDTreeToggle<cr>

" Colorscheme "
" colorscheme molokaiRDTreeShowHidden=1 " show hidden files "

" Syntastic "
"let g:syntastic_javascript_eslint_exe='$(npm bin)/eslint'   " load eslint from project node_modules"
let g:syntastic_javascript_checkers = ['eslint']
let g:syntastic_typescript_checkers = ['tslint', 'tsc']
set statusline+=%#warningmsg#
set statusline+=%{SyntasticStatuslineFlag()}
set statusline+=%*

let g:syntastic_always_populate_loc_list = 1
let g:syntastic_auto_loc_list = 1
let g:syntastic_check_on_open = 1
let g:syntastic_check_on_wq = 0

" see :h syntastic-loclist-callback
" syntastic height..
function! SyntasticCheckHook(errors)
    if !empty(a:errors)
        let g:syntastic_loc_list_height = min([len(a:errors), 10])
    endif
endfunction

" fix for empty html elements
let g:syntastic_html_tidy_ignore_errors=[" proprietary attribute " ,"trimming empty \<", "inserting implicit ", "unescaped \&" , "lacks \"action", "lacks value", "lacks \"src", "is not recognized!", "discarding unexpected", "replacing obsolete "]

" You complete me "
set shortmess+=c "Removes error 'User defined completion (^U^N^P) Pattern not found'

" Colorscheme "
colorscheme molokai