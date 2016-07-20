pace.vim -- An intergalactically friendly Vim theme.
" Maintainer: Brandon Siders <tyrannicaltoucan@gmail.com>
" License: MIT
" Modifed: 13 July 2016
" -----------------------------------------------------------

highlight clear

if exists("syntax_on")
    syntax reset
endif

set background=dark

let t_Co = 256
let colors_name = "deep-space"

" Italics (not compatible with all terminals!)
if !exists("g:deepspace_italics")
    let g:deepspace_italics = 0
endif

" Color Definitions
let s:black         = ["#1b202a", 234]
let s:visual_gray   = ["#2a3341", 236]
let s:dark_gray     = ["#323c4d", 237]
let s:mid_gray      = ["#51617d", 243]
let s:light_gray    = ["#9aa7bd", 248]
let s:white         = ["#c9d0dc", 252]

let s:red           = ["#b15e7c", 132]
let s:green         = ["#709d6c", 65]
let s:yellow        = ["#b5a262", 143]
let s:blue          = ["#608cc3", 67]
let s:purple        = ["#8f72bf", 97]
let s:cyan          = ["#56adb7", 73]
let s:pink          = ["#ca8bba", 175]
let s:orange        = ["#b3785d", 137]
let s:cursor_blue   = ["#599dff", 75]

let s:none          = ["NONE", "NONE"]

" Highlight function
function! s:HL(group, fg, bg, ...)
    execute 'hi!' a:group
                \ 'ctermfg=' .a:fg[1] 'ctermbg='.a:bg[1]
                \ 'guifg='   .a:fg[0] 'guibg='.a:bg[0]
                \ 'cterm='   .(a:0 > 0 ? get(a:1, 'cterm', 'NONE'): 'NONE')
                \ 'gui='     .(a:0 > 0 ? get(a:1, 'gui', 'NONE'): 'NONE')
                \ 'guisp='   .(a:0 > 0 ? get(a:1, 'guisp', 'NONE'): 'NONE')
endfun

" General syntax
if g:deepspace_italics == 1
    call s:HL("Comment",                s:mid_gray,     s:none,             {'cterm': 'italic',     'gui': 'italic'})
    call s:HL("Todo",                   s:pink,         s:none,             {'cterm': 'bolditalic', 'gui': 'bolditalic'})
else
    call s:HL("Comment",                s:mid_gray,     s:none,             {'gui': 'italic'})
    call s:HL("Todo",                   s:pink,         s:none,             {'cterm': 'bold',       'gui': 'bolditalic'})
endif

call s:HL("Constant",                   s:red,          s:none)
call s:HL("String",                     s:green,        s:none)
call s:HL("Character",                  s:red,          s:none)
call s:HL("Number",                     s:red,          s:none)
call s:HL("Boolean",                    s:red,          s:none)
call s:HL("Float",                      s:red,          s:none)
call s:HL("Identifier",                 s:purple,       s:none)
call s:HL("Function",                   s:yellow,       s:none)
call s:HL("Statement",                  s:blue,         s:none)
call s:HL("Conditional",                s:blue,         s:none)
call s:HL("Repeat",                     s:blue,         s:none)
call s:HL("Label",                      s:blue,         s:none)
call s:HL("Operator",                   s:cyan,         s:none)
call s:HL("Keyword",                    s:cyan,         s:none)
call s:HL("Exception",                  s:blue,         s:none)
call s:HL("PreProc",                    s:cyan,         s:none)
call s:HL("Include",                    s:purple,       s:none)
call s:HL("Define",                     s:blue,         s:none)
call s:HL("Macro",                      s:blue,         s:none)
call s:HL("PreCondit",                  s:purple,       s:none)
call s:HL("Type",                       s:orange,       s:none)
call s:HL("StorageClass",               s:orange,       s:none)
call s:HL("Structure",                  s:orange,       s:none)
call s:HL("Typedef",                    s:blue,         s:none)
call s:HL("Special",                    s:red,          s:none)
call s:HL("SpecialChar",                s:red,          s:none)
call s:HL("Tag",                        s:blue,         s:none)
call s:HL("Delimiter",                  s:cyan,         s:none)
call s:HL("SpecialComment",             s:light_gray,   s:none)
call s:HL("Underlined",                 s:blue,         s:none,             {'cterm': 'underline',  'gui': 'underline'})
call s:HL("Ignore",                     s:light_gray,   s:none)
call s:HL("Error",                      s:red,          s:none,             {'cterm': 'bold',       'gui': 'bold'})

" Editor
call s:HL("ColorColumn",                s:none,         s:visual_gray)
call s:HL("Cursor",                     s:black,        s:cursor_blue)
call s:HL("CursorColumn",               s:light_gray,   s:visual_gray)
call s:HL("CursorLine",                 s:none,         s:visual_gray)
call s:HL("CursorLineNr",               s:white,        s:visual_gray)
call s:HL("DiffAdd",                    s:black,        s:green)
call s:HL("DiffChange",                 s:black,        s:yellow)
call s:HL("DiffDelete",                 s:black,        s:red)
call s:HL("DiffText",                   s:black,        s:blue)
call s:HL("Directory",                  s:blue,         s:none)
call s:HL("Error",                      s:red,          s:none,             {'cterm': 'underline',  'gui': 'underline'})
call s:HL("ErrorMsg",                   s:red,          s:none,             {'cterm': 'bold',       'gui': 'bold'})
call s:HL("Folded",                     s:mid_gray,     s:black)
call s:HL("FoldColumn",                 s:light_gray,   s:none)
call s:HL("IncSearch",                  s:black,        s:light_gray)
call s:HL("LineNr",                     s:dark_gray,    s:none)
call s:HL("MatchParen",                 s:black,        s:pink,             {'cterm': 'bold',       'gui': 'bold'})
call s:HL("ModeMsg",                    s:green,        s:none)
call s:HL("MoreMsg",                    s:green,        s:none)
call s:HL("NonText",                    s:mid_gray,     s:none)
call s:HL("Normal",                     s:light_gray,   s:black)
call s:HL("Pmenu",                      s:light_gray,   s:dark_gray)
call s:HL("PmenuSbar",                  s:mid_gray,     s:light_gray)
call s:HL("PmenuSel",                   s:black,        s:cursor_blue)
call s:HL("PmenuThumb",                 s:light_gray,   s:white)
call s:HL("Question",                   s:yellow,       s:black)
call s:HL("Search",                     s:black,        s:yellow)
call s:HL("SpecialKey",                 s:mid_gray,     s:none)
call s:HL("SpellBad",                   s:red,          s:none,             {'cterm': 'underline',  'gui': 'boldundercurl'})
call s:HL("SpellCap",                   s:blue,         s:none,             {'cterm': 'underline',  'gui': 'boldundercurl'})
call s:HL("SpellLocal",                 s:cyan,         s:none,             {'cterm': 'underline',  'gui': 'boldundercurl'})
call s:HL("SpellRare",                  s:purple,       s:none,             {'cterm': 'underline',  'gui': 'boldundercurl'})
call s:HL("StatusLine",                 s:light_gray,   s:visual_gray)
call s:HL("StatusLineNC",               s:black,        s:dark_gray)
call s:HL("TabLine",                    s:black,        s:light_gray)
call s:HL("TabLineSel",                 s:light_gray,   s:cursor_blue,      {'cterm': 'bold',       'gui': 'bold'})
call s:HL("Title",                      s:green,        s:none,             {'cterm': 'bold',       'gui': 'bold'})
call s:HL("VertSplit",                  s:mid_gray,     s:none)
call s:HL("Visual",                     s:mid_gray,     s:dark_gray)
call s:HL("VisualNOS",                  s:white,        s:none,             {'cterm': 'boldunderline', 'gui': 'boldunderline'})
call s:HL("WarningMsg",                 s:red,          s:none)
call s:HL("WildMenu",                   s:black,        s:cursor_blue)

" Vim-Signify
call s:HL("SignifySignAdd",             s:green,        s:none)
call s:HL("SignifySignChange",          s:yellow,       s:none)
call s:HL("SignifySignDelete",          s:red,          s:none)

" Vim-Gitgutter
hi link GitGutterAdd    SignifySignAdd
hi link GitGutterChange SignifySignChange
hi link GitGutterDelete SignifySignDelete
call s:HL("GitGutterChangeDelete",      s:orange,       s:none)

" Vim-Fugitive
call s:HL("diffAdded",                  s:green,        s:none)
call s:HL("diffRemoved",                s:red,          s:none)

" Javascript
call s:HL("javaScriptBraces",           s:light_gray,   s:none)
call s:HL("javaScriptFunction",         s:blue,         s:none)
call s:HL("javaScriptIdentifier",       s:purple,       s:none)
call s:HL("javaScriptNull",             s:red,          s:none)
call s:HL("javaScriptNumber",           s:red,          s:none)
call s:HL("javaScriptRequire",          s:cyan,         s:none)
call s:HL("javaScriptReserved",         s:blue,         s:none)

" CSS
call s:HL("cssAttrComma",               s:blue,         s:none)
call s:HL("cssAttributeSelector",       s:green,        s:none)
call s:HL("cssBraces",                  s:light_gray,   s:none)
call s:HL("cssClassName",               s:yellow,       s:none)
call s:HL("cssClassNameDot",            s:yellow,       s:none)
call s:HL("cssDefinition",              s:blue,         s:none)
call s:HL("cssFontAttr",                s:cyan,         s:none)
call s:HL("cssFontDescriptor",          s:blue,         s:none)
call s:HL("cssFunctionName",            s:blue,         s:none)
call s:HL("cssIdentifier",              s:orange,       s:none)
call s:HL("cssImportant",               s:blue,         s:none)
call s:HL("cssInclude",                 s:light_gray,   s:none)
call s:HL("cssIncludeKeyword",          s:purple,       s:none)
call s:HL("cssMediaType",               s:cyan,         s:none)
call s:HL("cssProp",                    s:light_gray,   s:none)
call s:HL("cssPseudoClassId",           s:red,          s:none)
call s:HL("cssSelectorOp",              s:blue,         s:none)
call s:HL("cssSelectorOp2",             s:blue,         s:none)
call s:HL("cssTagName",                 s:blue,         s:none)

" Sass
call s:HL("sassAmpersand",              s:red,          s:none)
call s:HL("sassClass",                  s:orange,       s:none)
call s:HL("sassControl",                s:purple,       s:none)
call s:HL("sassExtend",                 s:purple,       s:none)
call s:HL("sassFor",                    s:blue,         s:none)
call s:HL("sassFunction",               s:cyan,         s:none)
call s:HL("sassId",                     s:orange,       s:none)
call s:HL("sassInclude",                s:blue,         s:none)
call s:HL("sassMedia",                  s:purple,       s:none)
call s:HL("sassMediaOperators",         s:light_gray,   s:none)
call s:HL("sassMixin",                  s:purple,       s:none)
call s:HL("sassMixinName",              s:blue,         s:none)
call s:HL("sassMixing",                 s:purple,       s:none)

" HTML
call s:HL("Title",                      s:yellow,       s:none,             {'cterm': 'bold',        'gui': 'bold'})
call s:HL("htmlArg",                    s:red,          s:none)
call s:HL("htmlEndTag",                 s:blue,         s:none)
call s:HL("htmlH1",                     s:light_gray,   s:none)
call s:HL("htmlLink",                   s:cyan,         s:none)
call s:HL("htmlSpecialChar",            s:orange,       s:none)
call s:HL("htmlSpecialTagName",         s:purple,       s:none)
call s:HL("htmlTag",                    s:blue,         s:none)
call s:HL("htmlTagName",                s:purple,       s:none)

" Ruby
call s:HL("rubyBlockParameter",         s:purple,      s:none)
call s:HL("rubyBlockParameterList",     s:purple,      s:none)
call s:HL("rubyClass",                  s:blue,        s:none)
call s:HL("rubyConstant",               s:orange,      s:none)
call s:HL("rubyControl",                s:blue,        s:none)
call s:HL("rubyEscape",                 s:red,         s:none)
call s:HL("rubyFunction",               s:yellow,      s:none)
call s:HL("rubyInterpolation",          s:green,       s:none)
call s:HL("rubyInterpolationDelimiter", s:pink,        s:none)
call s:HL("rubyRegexpSpecial",          s:yellow,      s:none)
call s:HL("rubyRegexp",                 s:cyan,        s:none)
call s:HL("rubyRegexpDelimiter",        s:cyan,        s:none)
call s:HL("rubyStringDelimiter",        s:green,       s:none)
call s:HL("rubySymbol",                 s:red,         s:none)

" Git
call s:HL("gitcommitUnmerged",          s:green,       s:none)
call s:HL("gitcommitBranch",            s:orange,      s:none)
call s:HL("gitcommitDiscardedType",     s:red,         s:none)
call s:HL("gitcommitSelectedType",      s:green,       s:none)
call s:HL("gitcommitHeader",            s:purple,      s:none)
call s:HL("gitcommitUntrackedFile",     s:blue,        s:none)
call s:HL("gitcommitDiscardedFile",     s:red,         s:none)
call s:HL("gitcommitSelectedFile",      s:green,       s:none)
call s:HL("gitcommitUnmergedFile",      s:yellow,      s:none)
call s:HL("gitcommitFile",              s:cyan,        s:none)
hi link gitcommitComment comment
hi link gitcommitOnBranch comment
hi link gitcommitNoBranch gitcommitBranch
hi link gitcommitUntracked gitcommitComment
hi link gitcommitDiscarded gitcommitComment
hi link gitcommitSelected gitcommitComment
hi link gitcommitDiscardedArrow gitcommitDiscardedFile
hi link gitcommitSelectedArrow gitcommitSelectedFile
hi link gitcommitUnmergedArrow gitcommitUnmergedFile
Host mtm-jupiter
HostName mtm-jupiter
user mtm-jupiter
IdentityFile ~/.ssh/mtm_rsa
