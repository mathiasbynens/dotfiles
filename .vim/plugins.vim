call plug#begin()

" General Utility Plugins {{{

" Matchit: Improves '%' match pairs
packadd! matchit

" Localvimrc: Provides project specific vimrc files
Plug 'https://github.com/embear/vim-localvimrc'
let localvimrc_sandbox = 0
let localvimrc_persistent = 1

" VimPager: Using for convenient installer, but don't enable plugin
Plug 'rkitover/vimpager', { 'on': 'Page' }

" Repeat: Let "." repeat more things
Plug 'tpope/vim-repeat'

" Airline: lightweight powerline plugin
Plug 'vim-airline/vim-airline'
Plug 'vim-airline/vim-airline-themes'
let g:airline_powerline_fonts = 1
let g:airline_inactive_collapse = 1
let g:airline_theme = 'solarized'
let g:airline_solarized_bg='dark'
let g:airline#extensions#branch#enabled = 1
let g:airline#extensions#tabline#enabled = 1
let g:airline#extensions#tagbar#enabled = 1
let g:airline_skip_empty_sections = 1

if !exists('g:airline_symbols')
  let g:airline_symbols = {}
endif

if !exists('g:airline_powerline_fonts')
  let g:airline#extensions#tabline#left_sep = ' '
  let g:airline#extensions#tabline#left_alt_sep = '|'
  let g:airline_left_sep          = '▶'
  let g:airline_left_alt_sep      = '»'
  let g:airline_right_sep         = '◀'
  let g:airline_right_alt_sep     = '«'
  let g:airline#extensions#branch#prefix     = '⤴' "➔, ➥, ⎇
  let g:airline#extensions#readonly#symbol   = '⊘'
  let g:airline#extensions#linecolumn#prefix = '¶'
  let g:airline#extensions#paste#symbol      = 'ρ'
  let g:airline_symbols.linenr    = '␊'
  let g:airline_symbols.branch    = '⎇'
  let g:airline_symbols.paste     = 'ρ'
  let g:airline_symbols.paste     = 'Þ'
  let g:airline_symbols.paste     = '∥'
  let g:airline_symbols.whitespace = 'Ξ'
else
  let g:airline#extensions#tabline#left_sep = ''
  let g:airline#extensions#tabline#left_alt_sep = ''

  " powerline symbols
  let g:airline_left_sep = ''
  let g:airline_left_alt_sep = ''
  let g:airline_right_sep = ''
  let g:airline_right_alt_sep = ''
  let g:airline_symbols.branch = ''
  let g:airline_symbols.readonly = ''
  let g:airline_symbols.linenr = ''
endif

" BracketedPaste: automatically turn off and on paste mode
Plug 'ConradIrwin/vim-bracketed-paste'

" Dispatch: kick off jobs based on actions (Installed for Omnisharp)
Plug 'tpope/vim-dispatch'

" EditorConfig: Allow projects to override local config settings
Plug 'editorconfig/editorconfig-vim'
let g:EditorConfig_exclude_patterns = ['fugitive://.*']
"}}}

" Navigation Plugins {{{

" Ack: Integration with ack/rg searching (see g:ackprg in .vimrc)
Plug 'https://github.com/mileszs/ack.vim', { 'on': 'Ack' }
cnoreabbrev Ack Ack!
nnoremap <Leader>a :Ack!<Space>

" Tagbar: ctag file navigation
Plug 'majutsushi/tagbar'
" Set some defaults for tagbar
let g:tagbar_autoclose = 1
let g:tagbar_left = 1
" Set a mapping for the tagbar.vim plugin.  Toggles the tagbar window.
nmap <leader>t :TagbarToggle<cr>

" FastFold: Fixed a bug where vim tries to refold and causes severe slow down
Plug 'https://github.com/Konfekt/FastFold'

" EasyMotion: Provides easy short range navigation shortcuts
Plug 'https://github.com/easymotion/vim-easymotion'

" CtrlP: Fuzzy file finder
Plug 'https://github.com/kien/ctrlp.vim'

" NerdTree: File Browser
Plug 'scrooloose/nerdtree', { 'on': 'NERDTreeToggle' }
let g:NERDTreeChDirMode=2
let g:NERDTreeIgnore=['node_modules','\.rbc$', '\~$', '\.pyc$', '\.db$', '\.sqlite$', '__pycache__']
let g:NERDTreeSortOrder=['^__\.py$', '\/$', '*', '\.swp$', '\.bak$', '\~$']
let g:NERDTreeShowBookmarks=1
let g:nerdtree_tabs_focus_on_files=1
let g:NERDTreeMapOpenInTabSilent = '<RightMouse>'
let g:NERDTreeWinSize = 50
nnoremap <leader>N :NERDTreeToggle<CR>

" Gundo: Undo tree visualizer
Plug 'sjl/gundo.vim', { 'on': 'GundoToggle' }
nnoremap <leader>u :GundoToggle<CR>

" Incsearch : Include incsearch.vim for vim < 81208 otherwise use is.vim
Plug 'https://github.com/haya14busa/is.vim'
" }}}

" Lazy Typing Plugins {{{

" Supertab: autocompletion with Tab
Plug 'https://github.com/ervandew/supertab'

" AutoPairs: Auto close pairs of things Eg: ""''{} etc
Plug 'https://github.com/jiangmiao/auto-pairs'
let g:AutoPairsFlyMode = 1
let g:AutoPairsShortcutBackInsert = '<Leader>b'
let g:AutoPairsShortcutJump= '<Leader>n'
let g:AutoPairsShortcutFastWrap= '<Leader>e'

" DelimitMate: Auto closer pairs.  I'm trying auto-pairs at the moment
" Plug 'Raimondi/delimitMate'
" Set some defaults for delimitMate
" let delimitMate_expand_cr = 2
" let delimitMate_expand_space = 1
" let delimitMate_expand_inside_quotes = 1
" let delimitMate_jump_expansion = 1

" CloseTag: Try to close matching <p> tags
Plug 'https://github.com/alvan/vim-closetag'

" ExpandRegion: allows easy expansion of visual selections
Plug 'https://github.com/terryma/vim-expand-region'
vmap v <Plug>(expand_region_expand)
vmap <C-v> <Plug>(expand_region_shrink)

" Templates: Provide boilerplate templates
Plug 'https://github.com/aperezdc/vim-template'
let g:templates_directory = [$HOME."/.vim/templates"]

" Commentary: easily comment out code
Plug 'https://github.com/tpope/vim-commentary'

" EasyAlign: Align all sorts of things
Plug 'junegunn/vim-easy-align'
" Start interactive EasyAlign in visual mode (e.g. vipga)
xmap ga <Plug>(EasyAlign)
" Start interactive EasyAlign for a motion/text object (e.g. gaip)
nmap ga <Plug>(EasyAlign)
" Quick map for aligning code in a {} block
nmap <silent> - gavi}
vmap <silent> - ga
" Same thing, but assume alignment on equal sign
nmap <silent> -- gavi}=<CR>
vmap <silent> -- ga=<CR>

" Surround: easily manage surround areas with '")({})"' etc
Plug 'https://github.com/tpope/vim-surround'

" Exchange: easily exchange selected elements
Plug 'tommcdo/vim-exchange'

" SplitJoin: split or join code into one-liners vs verbose layouts
Plug 'AndrewRadev/splitjoin.vim'

" Ultisnips: Snippets
Plug 'sirver/ultisnips'

" VimSnippets: Various snippets for lots of languages
Plug 'honza/vim-snippets'

" }}}

" Version Control Plugins {{{

" GitGutter: Shows inline git symbols for changed/added/removed lines
Plug 'https://github.com/airblade/vim-gitgutter', executable('git') ? {} : { 'on': [] }

" Fugitive: Git wrapper
Plug 'https://github.com/tpope/vim-fugitive'

" VCSCommand: VCS (cvs,svn,git,hg) managment
Plug 'vim-scripts/vcscommand.vim'
" }}}

" Language Plugins {{{

" ALE: Asynchronous Lint Engine
Plug 'dense-analysis/ale'
let g:airline#extensions#ale#enabled = 1

" Perl: yup
Plug 'neybar/vim-perl', { 'for': 'perl', 'do': 'make clean carp dancer highlight-all-pragmas moose test-more try-tiny'  }

" IndentLine: Provides visual indent levels
" Plug 'Yggdroot/indentLine', { 'for': 'python' }
Plug 'Yggdroot/indentLine'
let g:indentLine_enabled = 1
let g:indentLine_concealcursor = ''
let g:indentLine_char = '┆'
let g:indentLine_faster = 1

" Go: Go functionality
Plug 'fatih/vim-go', { 'do': ':GoInstallBinaries' }
" }}}

" Syntax Plugins {{{

" JSON: syntax highlighter
Plug 'elzr/vim-json'
" Turn off the auto conceal feature (It hides the quote characters until you
" move your cursor over the line)
let g:vim_json_syntax_conceal = 0

" Ansible: Provide some coloring and syntax for ansible files
Plug 'pearofducks/ansible-vim'

" SCSS: for sassy css
Plug 'cakebaker/scss-syntax.vim'

" HashiCorp: (Syntax and other tools for Vagrant,Terraform,Packer, etc)
Plug 'hashivim/vim-hashicorp-tools'

" Groovy: syntax files
Plug 'modille/groovy.vim'

" Jenkinsfile: helper that loads up Groovy and a few other keywords
Plug 'martinda/Jenkinsfile-vim-syntax'

" Typescript: Add some typescript syntax and linting
Plug 'leafgarland/typescript-vim'
Plug 'HerringtonDarkholme/yats.vim'
let g:yats_host_keyword = 1
" }}}

" Color Plugins {{{
Plug 'altercation/vim-colors-solarized'
" color settings are after plug#end because vim can't find the colorscheme at
" this point in time.
" }}}

call plug#end()

colorscheme solarized
let g:solarized_diffmode="high"
if &diff
    " override the colorscheme for vimdiff.  This is the best colorscheme for
    " diff operations that I've found by far
    colorscheme solarized
endif

" UltiSnips has built-in SuperTab support: pressing <Tab> will first try to
" expand/jump a snippet, then fall back to SuperTab completion automatically.
let g:SuperTabDefaultCompletionType = '<c-p>'
let g:UltiSnipsExpandTrigger = "<tab>"
" Use Ctrl-j and Ctrl-b to navigate between snippet tabstops
let g:UltiSnipsJumpForwardTrigger = "<c-j>"
let g:UltiSnipsJumpBackwardTrigger = "<c-b>"

" vim:foldmethod=marker:foldlevel=0
