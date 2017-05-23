" Vim syntax file
" Language:	Twig template
" Maintainer:	Gabriel Gosselin <gabrielNOSPAM@evidens.ca>
" Last Change:	2014 December 15
" Version:	1.1
"
" Based Jinja syntax by:	Armin Ronacher <armin.ronacher@active-4.com>
" With modifications by Benji Fisher, Ph.D.
"
" Known Bugs:
"   because of odd limitations dicts and the modulo operator
"   appear wrong in the template.
"
" Changes:
"
"     2008 May 9:     Added support for Jinja2 changes (new keyword rules)
"     2011 July 27:   Changed all references of jinja tp twig
"     2014 December 4:   Do not assume that the base filetype is HTML.

if exists('b:main_syntax')
  finish
endif
if exists('b:current_syntax')
  let b:main_syntax = b:current_syntax
else
  let b:main_syntax = 'twig'
endif

syntax case match

" Twig template built-in tags and parameters (without filter, macro, is and
" raw, they have special treatment)
syn keyword twigStatement containedin=twigVarBlock,twigTagBlock,twigNested contained and if else in not or recursive as import

syn keyword twigStatement containedin=twigVarBlock,twigTagBlock,twigNested contained is filter skipwhite nextgroup=twigFilter
syn keyword twigStatement containedin=twigTagBlock contained macro skipwhite nextgroup=twigFunction
syn keyword twigStatement containedin=twigTagBlock contained block skipwhite nextgroup=twigBlockName

" Variable Names
syn match twigVariable containedin=twigVarBlock,twigTagBlock,twigNested contained skipwhite /[a-zA-Z_][a-zA-Z0-9_]*/
syn keyword twigSpecial containedin=twigVarBlock,twigTagBlock,twigNested contained false true none loop super caller varargs kwargs

" Filters
syn match twigOperator "|" containedin=twigVarBlock,twigTagBlock,twigNested contained nextgroup=twigFilter
syn match twigFilter contained skipwhite /[a-zA-Z_][a-zA-Z0-9_]*/
syn match twigFunction contained skipwhite /[a-zA-Z_][a-zA-Z0-9_]*/
syn match twigBlockName contained skipwhite /[a-zA-Z_][a-zA-Z0-9_]*/

" Twig template constants
syn region twigString containedin=twigVarBlock,twigTagBlock,twigNested contained start=/"/ skip=/\\"/ end=/"/
syn region twigString containedin=twigVarBlock,twigTagBlock,twigNested contained start=/'/ skip=/\\'/ end=/'/
syn match twigNumber containedin=twigVarBlock,twigTagBlock,twigNested contained /[0-9]\+\(\.[0-9]\+\)\?/

" Operators
syn match twigOperator containedin=twigVarBlock,twigTagBlock,twigNested contained /[+\-*\/<>=!,:]/
syn match twigPunctuation containedin=twigVarBlock,twigTagBlock,twigNested contained /[()\[\]]/
syn match twigOperator containedin=twigVarBlock,twigTagBlock,twigNested contained /\./ nextgroup=twigAttribute
syn match twigAttribute contained /[a-zA-Z_][a-zA-Z0-9_]*/

" Twig template tag and variable blocks
syn region twigNested matchgroup=twigOperator start="(" end=")" transparent display containedin=twigVarBlock,twigTagBlock,twigNested contained
syn region twigNested matchgroup=twigOperator start="\[" end="\]" transparent display containedin=twigVarBlock,twigTagBlock,twigNested contained
syn region twigNested matchgroup=twigOperator start="{" end="}" transparent display containedin=twigVarBlock,twigTagBlock,twigNested contained
syn region twigTagBlock matchgroup=twigTagDelim start=/{%-\?/ end=/-\?%}/ skipwhite containedin=ALLBUT,twigTagBlock,twigVarBlock,twigRaw,twigString,twigNested,twigComment

syn region twigVarBlock matchgroup=twigVarDelim start=/{{-\?/ end=/-\?}}/ containedin=ALLBUT,twigTagBlock,twigVarBlock,twigRaw,twigString,twigNested,twigComment

" Twig template 'raw' tag
syn region twigRaw matchgroup=twigRawDelim start="{%\s*raw\s*%}" end="{%\s*endraw\s*%}" containedin=ALLBUT,twigTagBlock,twigVarBlock,twigString,twigComment

" Twig comments
syn region twigComment matchgroup=twigCommentDelim start="{#" end="#}" containedin=ALLBUT,twigTagBlock,twigVarBlock,twigString

" Block start keywords.  A bit tricker.  We only highlight at the start of a
" tag block and only if the name is not followed by a comma or equals sign
" which usually means that we have to deal with an assignment.
syn match twigStatement containedin=twigTagBlock contained skipwhite /\({%-\?\s*\)\@<=\<[a-zA-Z_][a-zA-Z0-9_]*\>\(\s*[,=]\)\@!/

" and context modifiers
syn match twigStatement containedin=twigTagBlock contained /\<with\(out\)\?\s\+context\>/ skipwhite


" Define the default highlighting.
" For version 5.7 and earlier: only when not done already
" For version 5.8 and later: only when an item doesn't have highlighting yet
if version >= 508 || !exists("did_twig_syn_inits")
  if version < 508
    let did_twig_syn_inits = 1
    command -nargs=+ HiLink hi link <args>
  else
    command -nargs=+ HiLink hi def link <args>
  endif

  HiLink twigPunctuation twigOperator
  HiLink twigAttribute twigVariable
  HiLink twigFunction twigFilter

  HiLink twigTagDelim twigTagBlock
  HiLink twigVarDelim twigVarBlock
  HiLink twigCommentDelim twigComment
  HiLink twigRawDelim twig

  HiLink twigSpecial Special
  HiLink twigOperator Normal
  HiLink twigRaw Normal
  HiLink twigTagBlock PreProc
  HiLink twigVarBlock PreProc
  HiLink twigStatement Statement
  HiLink twigFilter Function
  HiLink twigBlockName Function
  HiLink twigVariable Identifier
  HiLink twigString Constant
  HiLink twigNumber Constant
  HiLink twigComment Comment

  delcommand HiLink
endif
