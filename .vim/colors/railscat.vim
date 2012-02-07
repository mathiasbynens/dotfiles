" Vim color scheme
"
" Name:        railscat.vim
" Maintainer:  Jeff Kreeftmeijer
" License:     public domain
" URL:         https://gist.github.com/1523432
"
" A GUI only extended version of the Railscasts+ theme, that comes with
" Janus [1] and is, in turn, an extension to the original Railscasts theme
" [2], which is a port of the RailsCasts TextMate theme [3] to Vim.
"
" [1] https://github.com/carlhuda/janus
" [2] http://www.vim.org/scripts/script.php?script_id=2175
" [3] http://railscasts.com/about

set background=dark
hi clear
if exists("syntax_on")
	syntax reset
endif
let g:colors_name = "railscat"

" Colors
" Brown        #BC9458
" Dark Blue    #6D9CBE
" Dark Green   #519F50
" Dark Orange  #CC7833
" Light Blue   #D0D0FF
" Light Green  #A5C261
" Tan          #FFC66D

hi Normal                    guifg=#E6E1DC guibg=#2B2B2B
hi Cursor                    guibg=#FFFFFF
hi Search                    guibg=#5A647E
hi Visual                    guibg=#5A647E

" Folds
" -----
" line used for closed folds
hi Folded                    guifg=#F6F3E8 guibg=#444444 gui=NONE

" Misc
" ----
" directory names and other special names in listings
hi Directory                 guifg=#A5C261 gui=NONE

" Popup Menu
" ----------
" normal item in popup
hi Pmenu                     guifg=#F6F3E8 guibg=#444444 gui=NONE
" selected item in popup
hi PmenuSel                  guifg=#000000 guibg=#A5C261 gui=NONE
" scrollbar in popup
hi PMenuSbar                 guibg=#5A647E gui=NONE
" thumb of the scrollbar in the popup
hi PMenuThumb                guibg=#AAAAAA gui=NONE

"rubyComment
hi Comment                   guifg=#BC9458 gui=italic
hi Todo                      guifg=#BC9458 guibg=NONE gui=italic

"rubyPseudoVariable
"nil, self, symbols, etc
hi Constant                  guifg=#6D9CBE

"rubyClass, rubyModule, rubyDefine
"def, end, include, etc
hi Define                    guifg=#CC7833

"rubyInterpolation
hi Delimiter                 guifg=#519F50

"rubyError, rubyInvalidVariable
hi Error                     guifg=#FFFFFF guibg=#990000

"rubyFunction
hi Function                  guifg=#FFC66D gui=NONE

"rubyIdentifier
"@var, @@var, $var, etc
hi Identifier                guifg=#D0D0FF gui=NONE

"rubyInclude
"include, autoload, extend, load, require
hi Include                   guifg=#CC7833 gui=NONE

"rubyKeyword, rubyKeywordAsMethod
"alias, undef, super, yield, callcc, caller, lambda, proc
hi Keyword                   guifg=#CC7833

" same as define
hi Macro                     guifg=#CC7833 gui=NONE

"rubyInteger
hi Number                    guifg=#A5C261

" #if, #else, #endif
hi PreCondit                 guifg=#CC7833 gui=NONE

" generic preprocessor
hi PreProc                   guifg=#CC7833 gui=NONE

"rubyControl, rubyAccess, rubyEval
"case, begin, do, for, if unless, while, until else, etc.
hi Statement                 guifg=#CC7833 gui=NONE

"rubyString
hi String                    guifg=#A5C261

hi Title                     guifg=#FFFFFF

"rubyConstant
hi Type                      guifg=#DA4939 gui=NONE

hi DiffAdd                   guifg=#E6E1DC guibg=#144212
hi DiffDelete                guifg=#E6E1DC guibg=#660000

hi link htmlTag              xmlTag
hi link htmlTagName          xmlTagName
hi link htmlEndTag           xmlEndTag

hi xmlTag                    guifg=#E8BF6A
hi xmlTagName                guifg=#E8BF6A
hi xmlEndTag                 guifg=#E8BF6A

hi StatusLine   guibg=#cccccc guifg=#000000
hi StatusLineNC guibg=#666666 guifg=#333333
hi CursorLine   guibg=#262626
hi VertSplit    guifg=#262626
hi ColorColumn  guibg=#262626
hi LineNr       guifg=#666666 guibg=#333333
hi NonText      guifg=#666666
hi SignColumn   guibg=#666666