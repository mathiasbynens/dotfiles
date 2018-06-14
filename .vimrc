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

" SYNTAX "
Plugin 'mxw/vim-jsx'                        " Syntax highlighting and indenting for JSX "
Plugin 'pangloss/vim-javascript'            " provides syntax highlighting and improved indentation "
Plugin 'posva/vim-vue'                      " .vue support "
Plugin 'w0rp/ale'                           " linter "

" INPUT "
Plugin 'alvan/vim-closetag'                 " Auto-close HTML nodes "
Plugin 'Raimondi/delimitMate'               " automatic closing of quotes, parenthesis, brackets, etc "
Plugin 'prettier/vim-prettier',{ 'do': 'npm install' }" Makes code pretty "

" TOOLS "
Plugin 'kien/ctrlp.vim'                     " fuzzy search "
Plugin 'airblade/vim-gitgutter'             " git diff next to ruler "
Plugin 'scrooloose/nerdtree'                " sitemap in sidebar "
Plugin 'ternjs/tern_for_vim'                " provides Tern-based JavaScript editing support, for youcompleteme"
Plugin 'valloric/youcompleteme'             " fuzzy-search code completion engine "
Plugin 'qpkorr/vim-bufkill'                 " nload, delete or wipe a buffer without closing the window or split "
Plugin 'SirVer/ultisnips'                   " snippets engine."
Plugin 'honza/vim-snippets'                 " snippets preset "

" UI "
Plugin 'ap/vim-css-color'                   " color values as a color in css "
Plugin 'flazz/vim-colorschemes'             " color schemes "
Plugin 'mhinz/vim-startify'                 " startup screen "
Plugin 'nathanaelkane/vim-indent-guides'    " indent liness "
Plugin 'ryanoasis/vim-devicons'             " icons in Nerdtree "
Plugin 'vim-airline/vim-airline'            " git status bar "
Plugin 'vim-airline/vim-airline-themes'     " git status bar themes "



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
filetype plugin on

" Appearance "
syntax on
set background=dark
set guifont=*
set guifont=SauceCodePro\ Nerd\ Font:h25
"set guifont=Source\ Code\ Pro\ for\ Powerline:h15 "make sure to escape the spaces in the name properly
set guioptions=                     " remove scrollbars in macVim "
set noerrorbells                    " no error bells "
set ruler                           " show the line number on the bar "
set belloff=all                     " No sound and flashing
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
set expandtab                       " When expandtab is set, hitting Tab in insert mode will produce the appropriate number of spaces
"
syntax match Tab /\t/
hi Tab gui=underline guifg=blue ctermbg=red

" Performance
let loaded_matchparen=1 " Don't load matchit.vim (paren/bracket matching)
set noshowmatch         " Don't match parentheses/brackets
set nocursorline        " Don't paint cursor line
set nocursorcolumn      " Don't paint cursor column
set lazyredraw          " Wait to redraw
set scrolljump=8        " Scroll 8 lines at a time at bottom/top
let html_no_rendering=1 " Don't render italic, bold, links in HTML

" splits "
nnoremap <C-J> <C-W><C-J>           " ctrl + [j,k,l,h] to move in plits "
nnoremap <C-K> <C-W><C-K>
nnoremap <C-L> <C-W><C-L>
nnoremap <C-H> <C-W><C-H>

" Airline "
let g:airline#extensions#tabline#enabled = 1    " Automatically displays all buffers when there's only one tab open. "
let g:airline_powerline_fonts = 1

" Ale "
let b:ale_fixers = ['prettier', 'eslint']

" AUTO CLOSE XML/HTML "
let g:closetag_filenames = "*.html,*.xhtml,*.phtml,*.erb,*.jsx,*.vue"
let g:closetag_xhtml_filenames = '*.xhtml,*.jsx,*.erb,*.vue'
let g:closetag_emptyTags_caseSensitive = 1
let g:closetag_shortcut = '>'
let g:closetag_close_shortcut = '<leader>>'


" CTRLP "
nmap <leader>p :CtrlP<cr>
" Setup some default ignores "
let g:ctrlp_custom_ignore = {
  \ 'dir':  '\v[\/](node_modules|bower_components|dist|build)|(\.(git|hg|svn)|\_site)$',
  \ 'file': '\v\.(exe|so|dll|class|png|jpg|jpeg)$',
\}

" Use the nearest .git directory as the cwd "
" This makes a lot of sense if you are working on a project that is in version "
" control. It also supports works with .svn, .hg, .bzr. "
" let g:ctrlp_working_path_mode = 'r'

" Use NerdTree folder as CTRL search directoryh
let g:NERDTreeChDirMode       = 2
let g:ctrlp_working_path_mode = 'rw'

" Use a leader instead of the actual named binding "


" GitGutter "
set updatetime=250              " refresh rate for diff makers "

" Indent guides "
let g:indent_guides_enable_on_vim_startup = 1

" JSX for .js files
let g:jsx_ext_required = 0

" Prettier
let g:prettier#autoformat = 0
autocmd BufWritePre *.js,*.jsx,*.mjs,*.ts,*.tsx,*.css,*.less,*.scss,*.json,*.graphql,*.md,*.vue PrettierAsync

" Nerd tree
cd ~/development                  " navigate to development folder "
let NERDTreeShowHidden=1          " show hidden files "
" autocmd VimEnter * NERDTree     " start NERDtree on startup "
" autocmd VimEnter * wincmd p     " dont focus NERDtree on startup "
nmap <leader>n :NERDTreeToggle<cr>

" UtilSnips
" Trigger configuration. Do not use <tab> if you use https://github.com/Valloric/YouCompleteMe.
let g:UltiSnipsExpandTrigger="<tab>"
let g:UltiSnipsJumpForwardTrigger="<c-]>"
let g:UltiSnipsJumpBackwardTrigger="<c-[>"

"see: https://stackoverflow.com/questions/14896327/ultisnips-and-youcompleteme#answer-18685821
function! g:UltiSnips_Complete()
    call UltiSnips#ExpandSnippet()
    if g:ulti_expand_res == 0
        if pumvisible()
            return "\<C-n>"
        else
            call UltiSnips#JumpForwards()
            if g:ulti_jump_forwards_res == 0
               return "\<TAB>"
            endif
        endif
    endif
    return ""
endfunction

au BufEnter * exec "inoremap <silent> " . g:UltiSnipsExpandTrigger . " <C-R>=g:UltiSnips_Complete()<cr>"
let g:UltiSnipsJumpForwardTrigger="<tab>"
let g:UltiSnipsListSnippets="<c-e>"
" this mapping Enter key to <C-y> to chose the current highlight item 
" and close the selection list, same as other IDEs.
" CONFLICT with some plugins like tpope/Endwise
inoremap <expr> <CR> pumvisible() ? "\<C-y>" : "\<C-g>u\<CR>"

" Colorscheme "
colorscheme molokai
