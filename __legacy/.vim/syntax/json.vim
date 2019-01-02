" Vim syntax file
" Language:     JSON
" Maintainer:   Jeroen Ruigrok van der Werven <asmodai@in-nomine.org>
" Last Change:  2009-06-16
" Version:      0.4
" {{{1

" Syntax setup {{{2
" For version 5.x: Clear all syntax items
" For version 6.x: Quit when a syntax file was already loaded

if !exists("main_syntax")
	if version < 600
		syntax clear
	elseif exists("b:current_syntax")
		finish
	endif
	let main_syntax = 'json'
endif

" Syntax: Strings {{{2
syn region  jsonString    start=+"+  skip=+\\\\\|\\"+  end=+"+  contains=jsonEscape
" Syntax: JSON does not allow strings with single quotes, unlike JavaScript.
syn region  jsonStringSQ  start=+'+  skip=+\\\\\|\\"+  end=+'+

" Syntax: Escape sequences {{{3
syn match   jsonEscape    "\\["\\/bfnrt]" contained
syn match   jsonEscape    "\\u\x\{4}" contained

" Syntax: Strings should always be enclosed with quotes.
syn match   jsonNoQuotes  "\<\a\+\>"

" Syntax: Numbers {{{2
syn match   jsonNumber    "-\=\<\%(0\|[1-9]\d*\)\%(\.\d\+\)\=\%([eE][-+]\=\d\+\)\=\>"

" Syntax: An integer part of 0 followed by other digits is not allowed.
syn match   jsonNumError  "-\=\<0\d\.\d*\>"

" Syntax: Boolean {{{2
syn keyword jsonBoolean   true false

" Syntax: Null {{{2
syn keyword jsonNull      null

" Syntax: Braces {{{2
syn match   jsonBraces   "[{}\[\]]"

" Define the default highlighting. {{{1
" For version 5.7 and earlier: only when not done already
" For version 5.8 and later: only when an item doesn't have highlighting yet
if version >= 508 || !exists("did_json_syn_inits")
  if version < 508
    let did_json_syn_inits = 1
    command -nargs=+ HiLink hi link <args>
  else
    command -nargs=+ HiLink hi def link <args>
  endif
  HiLink jsonString      String
  HiLink jsonEscape      Special
  HiLink jsonNumber      Number
  HiLink jsonBraces      Operator
  HiLink jsonNull        Function
  HiLink jsonBoolean     Boolean

  HiLink jsonNumError    Error
  HiLink jsonStringSQ    Error
  HiLink jsonNoQuotes    Error
  delcommand HiLink
endif

let b:current_syntax = "json"
if main_syntax == 'json'
	unlet main_syntax
endif