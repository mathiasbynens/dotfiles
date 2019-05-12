"      _               _                 _  __
"     | |__   __ _  __| | __      _____ | |/ _|
"     | '_ \ / _` |/ _` | \ \ /\ / / _ \| | |_
"     | |_) | (_| | (_| |  \ V  V / (_) | |  _|
"     |_.__/ \__,_|\__,_|   \_/\_/ \___/|_|_|
"
"      I am the Bad Wolf. I create myself.
"       I take the words. I scatter them in time and space.
"        A message to lead myself here.
"
" A Vim colorscheme pieced together by Steve Losh.
" Available at http://stevelosh.com/projects/badwolf/
"
" Why? {{{
"
" After using Molokai for quite a long time, I started longing for
" a replacement.
"
" I love Molokai's high contrast and gooey, saturated tones, but it can be
" a little inconsistent at times.
"
" Also it's winter here in Rochester, so I wanted a color scheme that's a bit
" warmer.  A little less blue and a bit more red.
"
" And so Bad Wolf was born.  I'm no designer, but designers have been scattering
" beautiful colors through time and space long before I came along.  I took
" advantage of that and reused some of my favorites to lead me to this scheme.
"
" }}}

" Supporting code -------------------------------------------------------------
" Preamble {{{

set background=dark

if exists("syntax_on")
    syntax reset
endif

let colors_name = "badwolf"

" }}}
" Palette {{{

let s:bwc = {}

" The most basic of all our colors is a slightly tweaked version of the Molokai
" Normal text.
let s:bwc.plain = ['f8f6f2', 15]

" Pure and simple.
let s:bwc.snow = ['ffffff', 15]
let s:bwc.coal = ['000000', 0]

" All of the Gravel colors are based on a brown from Clouds Midnight.
let s:bwc.brightgravel   = ['d9cec3', 252]
let s:bwc.lightgravel    = ['998f84', 245]
let s:bwc.gravel         = ['857f78', 243]
let s:bwc.mediumgravel   = ['666462', 241]
let s:bwc.deepgravel     = ['45413b', 238]
let s:bwc.deepergravel   = ['35322d', 236]
let s:bwc.darkgravel     = ['242321', 235]
let s:bwc.blackgravel    = ['1c1b1a', 233]
let s:bwc.blackestgravel = ['141413', 232]

" A color sampled from a highlight in a photo of a glass of Dale's Pale Ale on
" my desk.
let s:bwc.dalespale = ['fade3e', 221]

" A beautiful tan from Tomorrow Night.
let s:bwc.dirtyblonde = ['f4cf86', 222]

" Delicious, chewy red from Made of Code for the poppiest highlights.
let s:bwc.taffy = ['ff2c4b', 197]

" The star of the show comes straight from Made of Code.
let s:bwc.tardis = ['0a9dff', 39]

" This one's from Mustang, not Florida!
let s:bwc.orange = ['ffa724', 214]

" A limier green from Getafe.
let s:bwc.lime = ['aeee00', 148]

" Rose's dress in The Idiot's Lantern.
let s:bwc.dress = ['ff9eb8', 211]

" Another play on the brown from Clouds Midnight.  I love that color.
let s:bwc.toffee = ['b88853', 137]

" Also based on that Clouds Midnight brown.
let s:bwc.coffee    = ['c7915b', 173]
let s:bwc.darkroast = ['88633f', 95]

" }}}
" Highlighting Function {{{
function! HL(group, fg, ...)
    " Arguments: group, guifg, guibg, gui, guisp

    let histring = 'hi ' . a:group . ' '

    if strlen(a:fg)
        if a:fg == 'fg'
            let histring .= 'guifg=fg ctermfg=fg '
        else
            let c = get(s:bwc, a:fg)
            let histring .= 'guifg=#' . c[0] . ' ctermfg=' . c[1] . ' '
        endif
    endif

    if a:0 >= 1 && strlen(a:1)
        if a:1 == 'bg'
            let histring .= 'guibg=bg ctermbg=bg '
        else
            let c = get(s:bwc, a:1)
            let histring .= 'guibg=#' . c[0] . ' ctermbg=' . c[1] . ' '
        endif
    endif

    if a:0 >= 2 && strlen(a:2)
        let histring .= 'gui=' . a:2 . ' cterm=' . a:2 . ' '
    endif

    if a:0 >= 3 && strlen(a:3)
        let c = get(s:bwc, a:3)
        let histring .= 'guisp=#' . c[0] . ' '
    endif

    " echom histring

    execute histring
endfunction
" }}}
" Configuration Options {{{

if exists('g:badwolf_darkgutter') && g:badwolf_darkgutter
    let s:gutter = 'blackestgravel'
else
    let s:gutter = 'blackgravel'
endif

" }}}

" Actual colorscheme ----------------------------------------------------------
" Vanilla Vim {{{

" General/UI {{{

call HL('Normal', 'plain', 'blackgravel')

call HL('Folded', 'mediumgravel', 'bg', 'none')

call HL('VertSplit', 'lightgravel', 'bg', 'none')

call HL('CursorLine',   '', 'darkgravel', 'none')
call HL('CursorColumn', '', 'darkgravel')
call HL('ColorColumn',  '', 'darkgravel')

call HL('MatchParen', 'dalespale', 'darkgravel', 'bold')

call HL('NonText',    'deepgravel', 'bg')
call HL('SpecialKey', 'deepgravel', 'bg')

call HL('Visual',    '',  'deepgravel')
call HL('VisualNOS', '',  'deepgravel')

call HL('Search',    'coal', 'dalespale', 'bold')
call HL('IncSearch', 'coal', 'tardis',    'bold')

call HL('Underlined', 'fg', '', 'underline')

call HL('StatusLine',   'coal', 'tardis',     'bold')
call HL('StatusLineNC', 'snow', 'deepgravel', 'bold')

call HL('Directory', 'dirtyblonde', '', 'bold')

call HL('Title', 'lime')

call HL('ErrorMsg',   'taffy',       'bg', 'bold')
call HL('MoreMsg',    'dalespale',   '',   'bold')
call HL('ModeMsg',    'dirtyblonde', '',   'bold')
call HL('Question',   'dirtyblonde', '',   'bold')
call HL('WarningMsg', 'dress',       '',   'bold')

" This is a ctags tag, not an HTML one.  'Something you can use c-] on'.
call HL('Tag', '', '', 'bold')

" hi IndentGuides                  guibg=#373737
" hi WildMenu        guifg=#66D9EF guibg=#000000

" }}}
" Gutter {{{

call HL('LineNr',     'mediumgravel', s:gutter)
call HL('SignColumn', '',             s:gutter)
call HL('FoldColumn', 'mediumgravel', s:gutter)

" }}}
" Cursor {{{

call HL('Cursor',  'coal', 'tardis', 'bold')
call HL('vCursor', 'coal', 'tardis', 'bold')
call HL('iCursor', 'coal', 'tardis', 'none')

" }}}
" Syntax highlighting {{{

" Start with a simple base.
call HL('Special', 'plain')

" Comments are slightly brighter than folds, to make 'headers' easier to see.
call HL('Comment',        'gravel')
call HL('Todo',           'snow', 'bg', 'bold')
call HL('SpecialComment', 'snow', 'bg', 'bold')

" Strings are a nice, pale straw color.  Nothing too fancy.
call HL('String', 'dirtyblonde')

" Control flow stuff is taffy.
call HL('Statement',   'taffy', '', 'bold')
call HL('Keyword',     'taffy', '', 'bold')
call HL('Conditional', 'taffy', '', 'bold')
call HL('Operator',    'taffy', '', 'none')
call HL('Label',       'taffy', '', 'none')
call HL('Repeat',      'taffy', '', 'none')

" Functions and variable declarations are orange, because plain looks weird.
call HL('Identifier', 'orange', '', 'none')
call HL('Function',   'orange', '', 'none')

" Preprocessor stuff is lime, to make it pop.
"
" This includes imports in any given language, because they should usually be
" grouped together at the beginning of a file.  If they're in the middle of some
" other code they should stand out, because something tricky is
" probably going on.
call HL('PreProc',   'lime', '', 'none')
call HL('Macro',     'lime', '', 'none')
call HL('Define',    'lime', '', 'none')
call HL('PreCondit', 'lime', '', 'bold')

" Constants of all kinds are colored together.
" I'm not really happy with the color yet...
call HL('Constant',  'toffee', '', 'bold')
call HL('Character', 'toffee', '', 'bold')
call HL('Boolean',   'toffee', '', 'bold')

call HL('Number', 'toffee', '', 'bold')
call HL('Float',  'toffee', '', 'bold')

" Not sure what 'special character in a constant' means, but let's make it pop.
call HL('SpecialChar', 'dress', '', 'bold')

call HL('Type', 'dress', '', 'none')
call HL('StorageClass', 'taffy', '', 'none')
call HL('Structure', 'taffy', '', 'none')
call HL('Typedef', 'taffy', '', 'bold')

" Make try/catch blocks stand out.
call HL('Exception', 'lime', '', 'bold')

" Misc
call HL('Error',  'snow',   'taffy', 'bold')
call HL('Debug',  'snow',   '',      'bold')
call HL('Ignore', 'gravel', '',      '')

" }}}
" Completion Menu {{{

call HL('Pmenu', 'plain', 'deepergravel')
call HL('PmenuSel', 'coal', 'tardis', 'bold')
call HL('PmenuSbar', '', 'deepergravel')
call HL('PmenuThumb', 'brightgravel')

" }}}
" Diffs {{{

call HL('DiffDelete', 'coal', 'coal')
call HL('DiffAdd',    '',     'deepergravel')
call HL('DiffChange', '',     'darkgravel')
call HL('DiffText',   'snow', 'deepergravel', 'bold')

" }}}
" Spelling {{{

if has("spell")
    call HL('SpellCap', 'dalespale', '', 'undercurl,bold', 'dalespale')
    call HL('SpellBad', '', '', 'undercurl', 'dalespale')
    call HL('SpellLocal', '', '', 'undercurl', 'dalespale')
    call HL('SpellRare', '', '', 'undercurl', 'dalespale')
endif

" }}}

" }}}
" Plugins {{{

" CtrlP {{{

    " the message when no match is found
    call HL('CtrlPNoEntries', 'snow', 'taffy', 'bold')

    " the matched pattern
    call HL('CtrlPMatch', 'orange', 'bg', 'none')

    " the line prefix '>' in the match window
    call HL('CtrlPLinePre', 'deepgravel', 'bg', 'none')

    " the prompt’s base
    call HL('CtrlPPrtBase', 'deepgravel', 'bg', 'none')

    " the prompt’s text
    call HL('CtrlPPrtText', 'plain', 'bg', 'none')

    " the prompt’s cursor when moving over the text
    call HL('CtrlPPrtCursor', 'coal', 'tardis', 'bold')

    " 'prt' or 'win', also for 'regex'
    call HL('CtrlPMode1', 'coal', 'tardis', 'bold')

    " 'file' or 'path', also for the local working dir
    call HL('CtrlPMode2', 'coal', 'tardis', 'bold')

    " the scanning status
    call HL('CtrlPStats', 'coal', 'tardis', 'bold')

    " TODO: CtrlP extensions.
    " CtrlPTabExtra  : the part of each line that’s not matched against (Comment)
    " CtrlPqfLineCol : the line and column numbers in quickfix mode (|hl-Search|)
    " CtrlPUndoT     : the elapsed time in undo mode (|hl-Directory|)
    " CtrlPUndoBr    : the square brackets [] in undo mode (Comment)
    " CtrlPUndoNr    : the undo number inside [] in undo mode (String)

" }}}
" EasyMotion {{{

call HL('EasyMotionTarget', 'tardis',     'bg', 'bold')
call HL('EasyMotionShade',  'deepgravel', 'bg')

" }}}
" Interesting Words {{{

" These are only used if you're me or have copied the <leader>hNUM mappings
" from my Vimrc.
call HL('InterestingWord1', 'coal', 'orange')
call HL('InterestingWord2', 'coal', 'lime')
call HL('InterestingWord3', 'coal', 'taffy')

" }}}
" Makegreen {{{

" hi GreenBar term=reverse ctermfg=white ctermbg=green guifg=coal guibg=#9edf1c
" hi RedBar   term=reverse ctermfg=white ctermbg=red guifg=white guibg=#C50048

" }}}
" ShowMarks {{{

call HL('ShowMarksHLl', 'tardis', 'blackgravel')
call HL('ShowMarksHLu', 'tardis', 'blackgravel')
call HL('ShowMarksHLo', 'tardis', 'blackgravel')
call HL('ShowMarksHLm', 'tardis', 'blackgravel')

" }}}

" }}}
" Filetype-specific {{{

" Clojure {{{

call HL('clojureSpecial',  'taffy', '', '')
call HL('clojureDefn',     'taffy', '', '')
call HL('clojureDefMacro', 'taffy', '', '')
call HL('clojureDefine',   'taffy', '', '')
call HL('clojureMacro',    'taffy', '', '')
call HL('clojureCond',     'taffy', '', '')

call HL('clojureKeyword', 'orange', '', 'none')

call HL('clojureFunc',   'dress', '', 'none')
call HL('clojureRepeat', 'dress', '', 'none')

call HL('clojureParen0', 'lightgravel', '', 'none')

call HL('clojureAnonArg', 'snow', '', 'bold')

" }}}
" CSS {{{

call HL('cssColorProp', 'fg', '', 'none')
call HL('cssBoxProp', 'fg', '', 'none')
call HL('cssTextProp', 'fg', '', 'none')
call HL('cssRenderProp', 'fg', '', 'none')
call HL('cssGeneratedContentProp', 'fg', '', 'none')

call HL('cssValueLength', 'toffee', '', 'bold')
call HL('cssColor', 'toffee', '', 'bold')
call HL('cssBraces', 'lightgravel', '', 'none')
call HL('cssIdentifier', 'orange', '', 'bold')
call HL('cssClassName', 'orange', '', 'none')

" }}}
" Django Templates {{{

call HL('djangoArgument', 'dirtyblonde', '',)
call HL('djangoTagBlock', 'orange', '')
call HL('djangoVarBlock', 'orange', '')
" hi djangoStatement guifg=#ff3853 gui=bold
" hi djangoVarBlock guifg=#f4cf86

" }}}
" HTML {{{

" Punctuation
call HL('htmlTag',    'darkroast', 'bg', 'none')
call HL('htmlEndTag', 'darkroast', 'bg', 'none')

" Tag names
call HL('htmlTagName',        'coffee', '', 'bold')
call HL('htmlSpecialTagName', 'coffee', '', 'bold')

" Attributes
call HL('htmlArg', 'coffee', '', 'none')

" Stuff inside an <a> tag
call HL('htmlLink', 'lightgravel', '', 'underline')

" }}}
" Java {{{

call HL('javaClassDecl', 'taffy', '', 'bold')
call HL('javaScopeDecl', 'taffy', '', 'bold')
call HL('javaCommentTitle', 'gravel', '')
call HL('javaDocTags', 'snow', '', 'none')
call HL('javaDocParam', 'dalespale', '', '')

" }}}
" LessCSS {{{

call HL('lessVariable', 'lime', '', 'none')

" }}}
" Mail {{{

call HL('mailSubject', 'orange', '', 'bold')
call HL('mailHeader', 'lightgravel', '', '')
call HL('mailHeaderKey', 'lightgravel', '', '')
call HL('mailHeaderEmail', 'snow', '', '')
call HL('mailURL', 'toffee', '', 'underline')
call HL('mailSignature', 'gravel', '', 'none')

call HL('mailQuoted1', 'gravel', '', 'none')
call HL('mailQuoted2', 'dress', '', 'none')
call HL('mailQuoted3', 'dirtyblonde', '', 'none')
call HL('mailQuoted4', 'orange', '', 'none')
call HL('mailQuoted5', 'lime', '', 'none')

" }}}
" Markdown {{{

call HL('markdownHeadingRule', 'lightgravel', '', 'bold')
call HL('markdownHeadingDelimiter', 'lightgravel', '', 'bold')
call HL('markdownOrderedListMarker', 'lightgravel', '', 'bold')
call HL('markdownListMarker', 'lightgravel', '', 'bold')
call HL('markdownH1', 'orange', '', 'bold')
call HL('markdownH2', 'lime', '', 'bold')
call HL('markdownH3', 'lime', '', 'none')
call HL('markdownH4', 'lime', '', 'none')
call HL('markdownH5', 'lime', '', 'none')
call HL('markdownH6', 'lime', '', 'none')
call HL('markdownLinkText', 'toffee', '', 'underline')
call HL('markdownIdDeclaration', 'toffee')
call HL('markdownAutomaticLink', 'toffee', '', 'bold')
call HL('markdownUrl', 'toffee', '', 'bold')
call HL('markdownUrldelimiter', 'lightgravel', '', 'bold')
call HL('markdownLinkDelimiter', 'lightgravel', '', 'bold')
call HL('markdownLinkTextDelimiter', 'lightgravel', '', 'bold')
call HL('markdownCodeDelimiter', 'dirtyblonde', '', 'bold')
call HL('markdownCode', 'dirtyblonde', '', 'none')
call HL('markdownCodeBlock', 'dirtyblonde', '', 'none')

" }}}
" Python {{{

hi def link pythonOperator Operator
call HL('pythonBuiltin',    'dress')
call HL('pythonEscape',     'dress')
call HL('pythonException',  'lime', '', 'bold')
call HL('pythonExceptions', 'lime', '', 'none')
call HL('pythonDecorator',  'taffy', '', 'none')

" }}}
" Vim {{{

call HL('VimCommentTitle', 'lightgravel', '', 'bold')

call HL('VimMapMod',    'dress', '', 'none')
call HL('VimMapModKey', 'dress', '', 'none')
call HL('VimNotation', 'dress', '', 'none')
call HL('VimBracket', 'dress', '', 'none')

" }}}

" }}}

