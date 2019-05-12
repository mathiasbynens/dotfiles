" Vim syntax file
" Language:	Vim help file
" Maintainer:	Jonas Fonseca <fonseca@diku.dk>
" Last Change:	Nov 24th 2002

" For version 5.x: Clear all syntax items
" For version 6.x: Quit when a syntax file was already loaded
if version < 600
  syntax clear
elseif exists("b:current_syntax")
  finish
endif

syn include @riRuby <sfile>:p:h/ruby.vim

syn region	riNonUniqueTerm	start=+^\w+ end=+^\s\{5}\w.*$+ contains=riTermString,riMethodSpec,riClassFold
syn match	riTermString	contained "`[^']*'"
syn match	riClassFold	contained "^\s\{5}.* {{{" contains=riClassOrModule

syn match	riMethodSpec	contained "\([A-Z]\w*\(\#\|::\|\.\)\)\+[^, ()]\+" contains=riClassOrModule,riComma,riSeparator
syn match	riSeparator 	contained "\(::\|\#\|\.\)"
syn match	riClassOrModule	contained "[A-Z]\w*"

syn region	riSection	start=+^---*+ end=+^---*$+ keepend contains=riMethodSpec,riApiCode,riSectionDelim
syn match	riSectionDelim	contained "---*"

syn region	riApiCode	contained start=+^\s\{5}+ end=+\(->\|$\)+me=s-1 keepend contains=riComma,riBufferType,@riRuby nextgroup=riEvalsto
syn match	riBufferType	contained "^\s\{5}\(class\|module\):"
syn match	riEvalsTo	contained "->.*$"	contains=riOutput
"syn match	riComma		contained ","
syn region	riOutput	contained start=+->+ms=s+3 end=+$+me=s-1 keepend

" Keep below riApiCode but before riExampleCode ;)
syn match	riDescription	"^\s\{5}.*$"	contains=riString,riMethodSpec
syn match	riString	contained "``[^']\+''"

syn region	riExampleCode	start=+^\s\{8}+ end=+\(#=>\|$\)+me=s-1 contains=@riRuby nextgroup=riEvalsTo
syn match	riEvalsTo	"#=>.*$" contains=riRubyOutput
syn region	riRubyOutput	contained start=+#=>+ms=s+3 end=+$+me=s-1 keepend contains=@riRuby

syn region	riProduces	start=+\s\{5}produces:+ skip=+^\s\{8}.*$+ end=+^\(\s\{5}\w.*\)\?$+ contains=riProduct
syn match	riProduct	contained "\s\{8}.*$"

syn sync minlines=40

" Define the default highlighting.
" For version 5.7 and earlier: only when not done already
" For version 5.8 and later: only when an item doesn't have highlighting yet
if version >= 508 || !exists("did_help_syntax_inits")
  if version < 508
    let did_help_syntax_inits = 1
    command -nargs=+ HiLink hi link <args>
  else
    command -nargs=+ HiLink hi def link <args>
  endif

  HiLink riSectionDelim		PreProc
  HiLink riUniqueMethod		Keyword
  HiLink riClassOrModule	Identifier
  HiLink riMethodSpec		Keyword
  HiLink riSeparator		SpecialChar
  HiLink riNonUniqueTerm	Comment
  HiLink riTermString		String
  HiLink riString		String
  HiLink riBufferType		Type
  HiLink riEvalsTo		Delimiter
  HiLink riOutput		Comment
  HiLink riClassFold		Comment
  HiLink riProduces		Comment
  HiLink riProduct		String
  HiLink riDescription		Comment

delcommand HiLink
endif

let b:current_syntax = "ri"

" vim: ts=8 sw=2 fdm=manual
