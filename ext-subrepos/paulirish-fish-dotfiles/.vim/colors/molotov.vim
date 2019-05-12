"                             ___           __                     
"             /'\_/`\        /\_ \         /\ \__                  
"            /\      \    ___\//\ \     ___\ \ ,_\   ___   __  __  
"            \ \ \__\ \  / __`\\ \ \   / __`\ \ \/  / __`\/\ \/\ \ 
"             \ \ \_/\ \/\ \L\ \\_\ \_/\ \L\ \ \ \_/\ \L\ \ \ \_/ |
"              \ \_\\ \_\ \____//\____\ \____/\ \__\ \____/\ \___/ 
"               \/_/ \/_/\/___/ \/____/\/___/  \/__/\/___/  \/__/  
"
" Burn, baby, burn! {{{
"
" Author: Gianni Chiappetta <gianni@runlevel6.org>
"
" Note: This theme is basically a fork of Bad Wolf by Steve Losh with less
" settings and different colours.
"
" }}}

" Supporting code -------------------------------------------------------------
" Preamble {{{

if !has("gui_running") && &t_Co != 88 && &t_Co != 256
  finish
endif

hi clear

set background=dark

if exists("syntax_on")
  syntax reset
endif

let colors_name = "molotov"

" }}}
" Palette {{{

" http://designmodo.github.com/Flat-UI/

" Turquoise     → #1ABC9C
" Green Sea     → #16A085

" Emerland      → #2ECC71
" Nephritis     → #27AE60

" Peter River   → #3498DB
" Belize Hole   → #2980B9

" Amethyst      → #9B59B6
" Wisteria      → #8E44AD

" Wet Asphalt   → #34495E
" Midnight Blue → #2C3E50

" Sun Flower    → #F1C40F
" Orange        → #F39C12

" Carrot        → #E67E22
" Pumpkin       → #D35400

" Alizarin      → #E74C3C
" Pomegranate   → #C0392B

" Clouds        → #ECF0F1
" Silver        → #BDC3C7

" Concrete      → #95A5A6
" Asbestos      → #7F8C8D

let s:mlc = {}

let s:mlc.clouds         = ['ECF0F1',  15]

let s:mlc.snow           = ['FFFFFF',  15]
let s:mlc.coal           = ['000000',   0]

let s:mlc.brightgravel   = ['D9CEC3', 252]
let s:mlc.lightgravel    = ['998F84', 245]
let s:mlc.gravel         = ['857F78', 243]
let s:mlc.mediumgravel   = ['666462', 241]
let s:mlc.deepgravel     = ['45413B', 238]
let s:mlc.deepergravel   = ['35322D', 236]
let s:mlc.darkgravel     = ['242321', 235]
let s:mlc.blackgravel    = ['1C1B1A', 233]
let s:mlc.blackestgravel = ['141413', 232]

let s:mlc.sunflower      = ['F1C40F', 220]
let s:mlc.dirtyblonde    = ['F4CF86', 229]
let s:mlc.alizarin       = ['E74C3C', 160]
let s:mlc.emerald        = ['2ECC71',  47]
let s:mlc.peter_river    = ['3498DB',  33]
let s:mlc.orange         = ['F39C12', 208]
let s:mlc.waspyellow     = ['FCB82B', 214]
let s:mlc.turqoise       = ['1ABC9C',  36]
let s:mlc.pumpkin        = ['D35400', 202]
let s:mlc.pomegranate    = ['C0392B', 196]
let s:mlc.greensea       = ['16A085',  29]

" Local colors (NOTE: Enable if you're using Molotov.itermcolors)
" let s:mlc.alizarin       = ['E74C3C',   5]
" let s:mlc.sunflower      = ['F1C40F',   3]
" let s:mlc.dirtyblonde    = ['F4CF86',  11]

" }}}
" Highlighting Function {{{
function! s:HL(group, fg, ...)
  " Arguments: group, guifg, guibg, gui, guisp

  let histring = 'hi ' . a:group . ' '

  if strlen(a:fg)
    if a:fg == 'fg'
      let histring .= 'guifg=fg ctermfg=fg '
    else
      let c = get(s:mlc, a:fg)
      let histring .= 'guifg=#' . c[0] . ' ctermfg=' . c[1] . ' '
    endif
  endif

  if a:0 >= 1 && strlen(a:1)
    if a:1 == 'bg'
      let histring .= 'guibg=bg ctermbg=bg '
    else
      let c = get(s:mlc, a:1)
      let histring .= 'guibg=#' . c[0] . ' ctermbg=' . c[1] . ' '
    endif
  endif

  if a:0 >= 2 && strlen(a:2)
    let histring .= 'gui=' . a:2 . ' cterm=' . a:2 . ' '
  endif

  if a:0 >= 3 && strlen(a:3)
    let c = get(s:mlc, a:3)
    let histring .= 'guisp=#' . c[0] . ' '
  endif

  " echom histring

  execute histring
endfunction
" }}}
" Configuration Options {{{

" None, you bitches!

" }}}

" Actual colorscheme ----------------------------------------------------------
" Vanilla Vim {{{

" General/UI {{{

call s:HL('Normal',       'clouds',        'blackgravel')

call s:HL('Folded',       'mediumgravel', 'bg',          'none')

call s:HL('VertSplit',    'lightgravel',  'bg',          'none')

call s:HL('CursorLine',   '',             'darkgravel',  'none')
call s:HL('CursorColumn', '',             'darkgravel')
call s:HL('ColorColumn',  '',             'darkgravel')

call s:HL('TabLine',      'clouds',        'blackgravel', 'none')
call s:HL('TabLineFill',  'clouds',        'blackgravel', 'none')
call s:HL('TabLineSel',   'coal',         'peter_river',      'none')

call s:HL('MatchParen',   'sunflower',    'darkgravel',  'bold')

call s:HL('NonText',      'deepgravel',   'bg')
call s:HL('SpecialKey',   'deepgravel',   'bg')

call s:HL('Visual',       '',             'deepgravel')
call s:HL('VisualNOS',    '',             'deepgravel')

call s:HL('Search',       'coal',         'sunflower',   'bold')
call s:HL('IncSearch',    'coal',         'peter_river',      'bold')

call s:HL('Underlined',   'fg',           '',            'underline')

call s:HL('StatusLine',   'coal',         'peter_river',      'bold')
call s:HL('StatusLineNC', 'snow',         'deepgravel',  'bold')

call s:HL('Directory',    'dirtyblonde',  '',            'bold')

call s:HL('Title',        'waspyellow')

call s:HL('ErrorMsg',     'alizarin',        'bg',          'bold')
call s:HL('MoreMsg',      'sunflower',    '',            'bold')
call s:HL('ModeMsg',      'dirtyblonde',  '',            'bold')
call s:HL('Question',     'dirtyblonde',  '',            'bold')
call s:HL('WarningMsg',   'turqoise',        '',            'bold')

" This is a ctags tag, not an HTML one.  'Something you can use c-] on'.
call s:HL('Tag', '', '', 'bold')

" hi IndentGuides                  guibg=#373737
" hi WildMenu        guifg=#66D9EF guibg=#000000

" }}}
" Gutter {{{

call s:HL('LineNr',     'mediumgravel', 'blackgravel')
call s:HL('SignColumn', '',             'blackgravel')
call s:HL('FoldColumn', 'mediumgravel', 'blackgravel')

" }}}
" Cursor {{{

call s:HL('Cursor',  'coal', 'peter_river', 'bold')
call s:HL('vCursor', 'coal', 'peter_river', 'bold')
call s:HL('iCursor', 'coal', 'peter_river', 'none')

" }}}
" Syntax highlighting {{{

" Start with a simple base.
call s:HL('Special', 'clouds')

" Comments are slightly brighter than folds, to make 'headers' easier to see.
call s:HL('Comment',        'gravel')
call s:HL('Todo',           'snow', 'bg', 'bold')
call s:HL('SpecialComment', 'snow', 'bg', 'bold')

" Strings are a nice, pale straw color.  Nothing too fancy.
call s:HL('String', 'dirtyblonde')

" Control flow stuff is alizarin.
call s:HL('Statement',   'alizarin', '', 'bold')
call s:HL('Keyword',     'alizarin', '', 'bold')
call s:HL('Conditional', 'alizarin', '', 'bold')
call s:HL('Operator',    'alizarin', '', 'none')
call s:HL('Label',       'alizarin', '', 'none')
call s:HL('Repeat',      'alizarin', '', 'none')

" Functions and variable declarations are orange, because clouds looks weird.
call s:HL('Identifier', 'orange', '', 'none')
call s:HL('Function',   'orange', '', 'none')

" Preprocessor stuff is waspyellow, to make it pop.
"
" This includes imports in any given language, because they should usually be
" grouped together at the beginning of a file.  If they're in the middle of some
" other code they should stand out, because something tricky is
" probably going on.
call s:HL('PreProc',   'waspyellow', '', 'none')
call s:HL('Macro',     'waspyellow', '', 'none')
call s:HL('Define',    'waspyellow', '', 'none')
call s:HL('PreCondit', 'waspyellow', '', 'bold')

" Constants of all kinds are colored together.
" I'm not really happy with the color yet...
call s:HL('Constant',  'pumpkin', '', 'bold')
call s:HL('Character', 'pumpkin', '', 'bold')
call s:HL('Boolean',   'pumpkin', '', 'bold')

call s:HL('Number',    'pumpkin', '', 'bold')
call s:HL('Float',     'pumpkin', '', 'bold')

" Not sure what 'special character in a constant' means, but let's make it pop.
call s:HL('SpecialChar', 'turqoise', '', 'bold')

call s:HL('Type',         'turqoise', '', 'none')
call s:HL('StorageClass', 'alizarin', '', 'none')
call s:HL('Structure',    'alizarin', '', 'none')
call s:HL('Typedef',      'alizarin', '', 'bold')

" Make try/catch blocks stand out.
call s:HL('Exception', 'waspyellow', '', 'bold')

" Misc
call s:HL('Error',  'snow',   'alizarin', 'bold')
call s:HL('Debug',  'snow',   '',      'bold')
call s:HL('Ignore', 'gravel', '',      '')

" }}}
" Completion Menu {{{

call s:HL('Pmenu',      'clouds',        'deepergravel')
call s:HL('PmenuSel',   'coal',         'peter_river',       'bold')
call s:HL('PmenuSbar',  '',             'deepergravel')
call s:HL('PmenuThumb', 'brightgravel')

" }}}
" Diffs {{{

call s:HL('DiffDelete', 'coal', 'coal')
call s:HL('DiffAdd',    '',     'deepergravel')
call s:HL('DiffChange', '',     'darkgravel')
call s:HL('DiffText',   'snow', 'deepergravel', 'bold')

" }}}
" Spelling {{{

if has("spell")
    call s:HL('SpellCap',   'sunflower', 'bg', 'undercurl,bold', 'sunflower')
    call s:HL('SpellBad',   '',          'bg', 'undercurl',      'sunflower')
    call s:HL('SpellLocal', '',          '',   'undercurl',      'sunflower')
    call s:HL('SpellRare',  '',          '',   'undercurl',      'sunflower')
endif

" }}}

" }}}
" Plugins {{{

" CtrlP {{{

  " the message when no match is found
  call s:HL('CtrlPNoEntries', 'snow', 'alizarin', 'bold')

  " the matched pattern
  call s:HL('CtrlPMatch', 'orange', 'bg', 'none')

  " the line prefix '>' in the match window
  call s:HL('CtrlPLinePre', 'deepgravel', 'bg', 'none')

  " the prompt’s base
  call s:HL('CtrlPPrtBase', 'deepgravel', 'bg', 'none')

  " the prompt’s text
  call s:HL('CtrlPPrtText', 'clouds', 'bg', 'none')

  " the prompt’s cursor when moving over the text
  call s:HL('CtrlPPrtCursor', 'coal', 'peter_river', 'bold')

  " 'prt' or 'win', also for 'regex'
  call s:HL('CtrlPMode1', 'coal', 'peter_river', 'bold')

  " 'file' or 'path', also for the local working dir
  call s:HL('CtrlPMode2', 'coal', 'peter_river', 'bold')

  " the scanning status
  call s:HL('CtrlPStats', 'coal', 'peter_river', 'bold')

  " TODO: CtrlP extensions.
  " CtrlPTabExtra  : the part of each line that’s not matched against (Comment)
  " CtrlPqfLineCol : the line and column numbers in quickfix mode (|s:HL-Search|)
  " CtrlPUndoT     : the elapsed time in undo mode (|s:HL-Directory|)
  " CtrlPUndoBr    : the square brackets [] in undo mode (Comment)
  " CtrlPUndoNr    : the undo number inside [] in undo mode (String)

" }}}
" EasyMotion {{{

call s:HL('EasyMotionTarget', 'peter_river',     'bg', 'bold')
call s:HL('EasyMotionShade',  'deepgravel', 'bg')

" }}}
" Interesting Words {{{

" These are only used if you're me or have copied the <leader>hNUM mappings
" from my Vimrc.
call s:HL('InterestingWord1', 'coal', 'orange')
call s:HL('InterestingWord2', 'coal', 'waspyellow')
call s:HL('InterestingWord3', 'coal', 'emerald')
call s:HL('InterestingWord4', 'coal', 'pumpkin')
call s:HL('InterestingWord5', 'coal', 'turqoise')
call s:HL('InterestingWord6', 'coal', 'alizarin')


" }}}
" Makegreen {{{

" hi GreenBar term=reverse ctermfg=white ctermbg=green guifg=coal guibg=#9edf1c
" hi RedBar   term=reverse ctermfg=white ctermbg=red guifg=white guibg=#C50048

" }}}
" ShowMarks {{{

call s:HL('ShowMarksHLl', 'peter_river', 'blackgravel')
call s:HL('ShowMarksHLu', 'peter_river', 'blackgravel')
call s:HL('ShowMarksHLo', 'peter_river', 'blackgravel')
call s:HL('ShowMarksHLm', 'peter_river', 'blackgravel')

" }}}

" }}}
" Filetype-specific {{{

" Clojure {{{

call s:HL('clojureSpecial',  'alizarin',       '', '')
call s:HL('clojureDefn',     'alizarin',       '', '')
call s:HL('clojureDefMacro', 'alizarin',       '', '')
call s:HL('clojureDefine',   'alizarin',       '', '')
call s:HL('clojureMacro',    'alizarin',       '', '')
call s:HL('clojureCond',     'alizarin',       '', '')

call s:HL('clojureKeyword',  'orange',      '', 'none')

call s:HL('clojureFunc',     'turqoise',       '', 'none')
call s:HL('clojureRepeat',   'turqoise',       '', 'none')

call s:HL('clojureParen0',   'lightgravel', '', 'none')

call s:HL('clojureAnonArg',  'snow',        '', 'bold')

" }}}
" CSS {{{

call s:HL('cssColorProp',            'dirtyblonde', '', 'none')
call s:HL('cssBoxProp',              'dirtyblonde', '', 'none')
call s:HL('cssTextProp',             'dirtyblonde', '', 'none')
call s:HL('cssRenderProp',           'dirtyblonde', '', 'none')
call s:HL('cssGeneratedContentProp', 'dirtyblonde', '', 'none')

call s:HL('cssValueLength',          'pumpkin',      '', 'bold')
call s:HL('cssColor',                'pumpkin',      '', 'bold')
call s:HL('cssBraces',               'lightgravel', '', 'none')
call s:HL('cssIdentifier',           'orange',      '', 'bold')
call s:HL('cssClassName',            'orange',      '', 'none')

" }}}
" Diff {{{

call s:HL('gitDiff',     'lightgravel', '',)

call s:HL('diffRemoved', 'turqoise',       '',)
call s:HL('diffAdded',   'waspyellow',        '',)
call s:HL('diffFile',    'coal',        'alizarin',  'bold')
call s:HL('diffNewFile', 'coal',        'alizarin',  'bold')

call s:HL('diffLine',    'coal',        'orange', 'bold')
call s:HL('diffSubname', 'orange',      '',       'none')

" }}}
" Django Templates {{{

call s:HL('djangoArgument', 'dirtyblonde', '',)
call s:HL('djangoTagBlock', 'orange',      '')
call s:HL('djangoVarBlock', 'orange',      '')
" hi djangoStatement guifg=#ff3853 gui=bold
" hi djangoVarBlock guifg=#f4cf86

" }}}
" HTML {{{

" Punctuation
call s:HL('htmlTag',    'greensea', 'bg', 'none')
call s:HL('htmlEndTag', 'greensea', 'bg', 'none')

" Tag names
call s:HL('htmlTagName',        'pomegranate', '', 'bold')
call s:HL('htmlSpecialTagName', 'pomegranate', '', 'bold')
call s:HL('htmlSpecialChar',    'waspyellow',   '', 'none')

" Attributes
call s:HL('htmlArg', 'pomegranate', '', 'none')

" Stuff inside an <a> tag

call s:HL('htmlLink', 'lightgravel', '', 'underline')

" }}}
" Java {{{

call s:HL('javaClassDecl',    'alizarin',     '', 'bold')
call s:HL('javaScopeDecl',    'alizarin',     '', 'bold')
call s:HL('javaCommentTitle', 'gravel',    '')
call s:HL('javaDocTags',      'snow',      '', 'none')
call s:HL('javaDocParam',     'sunflower', '', '')

" }}}
" LaTeX {{{

call s:HL('texStatement',   'peter_river',       '', 'none')
call s:HL('texMathZoneX',   'orange',       '', 'none')
call s:HL('texMathZoneA',   'orange',       '', 'none')
call s:HL('texMathZoneB',   'orange',       '', 'none')
call s:HL('texMathZoneC',   'orange',       '', 'none')
call s:HL('texMathZoneD',   'orange',       '', 'none')
call s:HL('texMathZoneE',   'orange',       '', 'none')
call s:HL('texMathZoneV',   'orange',       '', 'none')
call s:HL('texMathZoneX',   'orange',       '', 'none')
call s:HL('texMath',        'orange',       '', 'none')
call s:HL('texMathMatcher', 'orange',       '', 'none')
call s:HL('texRefLabel',    'dirtyblonde',  '', 'none')
call s:HL('texRefZone',     'waspyellow',         '', 'none')
call s:HL('texComment',     'greensea',    '', 'none')
call s:HL('texDelimiter',   'orange',       '', 'none')
call s:HL('texZone',        'brightgravel', '', 'none')

augroup badwolf_tex
  au!

  au BufRead,BufNewFile *.tex syn region texMathZoneV start="\\(" end="\\)\|%stopzone\>" keepend contains=@texMathZoneGroup
  au BufRead,BufNewFile *.tex syn region texMathZoneX start="\$" skip="\\\\\|\\\$" end="\$\|%stopzone\>" keepend contains=@texMathZoneGroup
augroup END

" }}}
" LessCSS {{{

call s:HL('lessVariable', 'waspyellow', '', 'none')

" }}}
" Lispyscript {{{

call s:HL('lispyscriptDefMacro', 'waspyellow',  '', '')
call s:HL('lispyscriptRepeat',   'turqoise', '', 'none')

" }}}
" Mail {{{

call s:HL('mailSubject',     'orange',      '', 'bold')
call s:HL('mailHeader',      'lightgravel', '', '')
call s:HL('mailHeaderKey',   'lightgravel', '', '')
call s:HL('mailHeaderEmail', 'snow',        '', '')
call s:HL('mailURL',         'pumpkin',      '', 'underline')
call s:HL('mailSignature',   'gravel',      '', 'none')

call s:HL('mailQuoted1',     'gravel',      '', 'none')
call s:HL('mailQuoted2',     'turqoise',       '', 'none')
call s:HL('mailQuoted3',     'dirtyblonde', '', 'none')
call s:HL('mailQuoted4',     'orange',      '', 'none')
call s:HL('mailQuoted5',     'waspyellow',        '', 'none')

" }}}
" Markdown {{{

call s:HL('markdownHeadingRule',       'lightgravel', '', 'bold')
call s:HL('markdownHeadingDelimiter',  'lightgravel', '', 'bold')
call s:HL('markdownOrderedListMarker', 'lightgravel', '', 'bold')
call s:HL('markdownListMarker',        'lightgravel', '', 'bold')
call s:HL('markdownItalic',            'snow',        '', 'bold')
call s:HL('markdownBold',              'snow',        '', 'bold')
call s:HL('markdownH1',                'orange',      '', 'bold')
call s:HL('markdownH2',                'waspyellow',        '', 'bold')
call s:HL('markdownH3',                'waspyellow',        '', 'none')
call s:HL('markdownH4',                'waspyellow',        '', 'none')
call s:HL('markdownH5',                'waspyellow',        '', 'none')
call s:HL('markdownH6',                'waspyellow',        '', 'none')
call s:HL('markdownLinkText',          'pumpkin',      '', 'underline')
call s:HL('markdownIdDeclaration',     'pumpkin')
call s:HL('markdownAutomaticLink',     'pumpkin',      '', 'bold')
call s:HL('markdownUrl',               'pumpkin',      '', 'bold')
call s:HL('markdownUrldelimiter',      'lightgravel', '', 'bold')
call s:HL('markdownLinkDelimiter',     'lightgravel', '', 'bold')
call s:HL('markdownLinkTextDelimiter', 'lightgravel', '', 'bold')
call s:HL('markdownCodeDelimiter',     'dirtyblonde', '', 'bold')
call s:HL('markdownCode',              'dirtyblonde', '', 'none')
call s:HL('markdownCodeBlock',         'dirtyblonde', '', 'none')

" }}}
" MySQL {{{

call s:HL('mysqlSpecial', 'turqoise', '', 'bold')

" }}}
" Python {{{

hi def link pythonOperator Operator
call s:HL('pythonBuiltin',     'turqoise')
call s:HL('pythonBuiltinObj',  'turqoise')
call s:HL('pythonBuiltinFunc', 'turqoise')
call s:HL('pythonEscape',      'turqoise')
call s:HL('pythonException',   'waspyellow',   '', 'bold')
call s:HL('pythonExceptions',  'waspyellow',   '', 'none')
call s:HL('pythonPrecondit',   'waspyellow',   '', 'none')
call s:HL('pythonDecorator',   'alizarin',  '', 'none')
call s:HL('pythonRun',         'gravel', '', 'bold')
call s:HL('pythonCoding',      'gravel', '', 'bold')

" }}}
" SLIMV {{{

" Rainbow parentheses
call s:HL('hlLevel0', 'gravel')
call s:HL('hlLevel1', 'orange')
call s:HL('hlLevel2', 'emerald')
call s:HL('hlLevel3', 'turqoise')
call s:HL('hlLevel4', 'pomegranate')
call s:HL('hlLevel5', 'dirtyblonde')
call s:HL('hlLevel6', 'orange')
call s:HL('hlLevel7', 'emerald')
call s:HL('hlLevel8', 'turqoise')
call s:HL('hlLevel9', 'pomegranate')

" }}}
" Vim {{{

call s:HL('VimCommentTitle', 'lightgravel', '', 'bold')

call s:HL('VimMapMod',       'turqoise',       '', 'none')
call s:HL('VimMapModKey',    'turqoise',       '', 'none')
call s:HL('VimNotation',     'turqoise',       '', 'none')
call s:HL('VimBracket',      'turqoise',       '', 'none')

" }}}

" }}}

