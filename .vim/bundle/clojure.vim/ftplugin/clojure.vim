" Vim filetype plugin file
" Language:     Clojure
" Maintainer:   Meikel Brandmeyer <mb@kotka.de>

" Only do this when not done yet for this buffer
if exists("b:did_ftplugin")
	finish
endif

let b:did_ftplugin = 1

let s:cpo_save = &cpo
set cpo&vim

let b:undo_ftplugin = "setlocal fo< com< cms< cpt< isk< def<"

setlocal iskeyword+=?,-,*,!,+,/,=,<,>,.,:

setlocal define=^\\s*(def\\(-\\|n\\|n-\\|macro\\|struct\\|multi\\)?

" Set 'formatoptions' to break comment lines but not other lines,
" and insert the comment leader when hitting <CR> or using "o".
setlocal formatoptions-=t formatoptions+=croql
setlocal commentstring=;%s

" Set 'comments' to format dashed lists in comments.
setlocal comments=sO:;\ -,mO:;\ \ ,n:;

" Take all directories of the CLOJURE_SOURCE_DIRS environment variable
" and add them to the path option.
if has("win32") || has("win64")
	let s:delim = ";"
else
	let s:delim = ":"
endif
for dir in split($CLOJURE_SOURCE_DIRS, s:delim)
	call vimclojure#AddPathToOption(dir . "/**", 'path')
endfor

" When the matchit plugin is loaded, this makes the % command skip parens and
" braces in comments.
let b:match_words = &matchpairs
let b:match_skip = 's:comment\|string\|character'

" Win32 can filter files in the browse dialog
if has("gui_win32") && !exists("b:browsefilter")
	let b:browsefilter = "Clojure Source Files (*.clj)\t*.clj\n" .
				\ "Jave Source Files (*.java)\t*.java\n" .
				\ "All Files (*.*)\t*.*\n"
endif

for ns in [ "clojure.core", "clojure.inspector", "clojure.java.browse",
			\ "clojure.java.io", "clojure.java.javadoc", "clojure.java.shell",
			\ "clojure.main", "clojure.pprint", "clojure.repl", "clojure.set",
			\ "clojure.stacktrace", "clojure.string", "clojure.template",
			\ "clojure.test", "clojure.test.tap", "clojure.test.junit",
			\ "clojure.walk", "clojure.xml", "clojure.zip" ]
	call vimclojure#AddCompletions(ns)
endfor

" Define toplevel folding if desired.
function! ClojureGetFoldingLevelWorker() dict
	execute self.lineno

	if vimclojure#util#SynIdName() =~ 'clojureParen\d' && vimclojure#util#Yank('l', 'normal! "lyl') == '('
		return 1
	endif

	if searchpairpos('(', '', ')', 'bWr', 'vimclojure#util#SynIdName() !~ "clojureParen\\d"') != [0, 0]
		return 1
	endif

	return 0
endfunction

function! ClojureGetFoldingLevel(lineno)
	let closure = {
				\ 'lineno' : a:lineno,
				\ 'f'      : function("ClojureGetFoldingLevelWorker")
				\ }

	return vimclojure#WithSavedPosition(closure)
endfunction

" Disabled for now. Too slow (and naive).
if exists("g:clj_want_folding") && g:clj_want_folding == 1 && 0 == 1
	setlocal foldexpr=ClojureGetFoldingLevel(v:lnum)
	setlocal foldmethod=expr
endif

try
	call vimclojure#InitBuffer()
catch /.*/
	" We swallow a failure here. It means most likely that the
	" server is not running.
	echohl WarningMsg
	echomsg v:exception
	echohl None
endtry

call vimclojure#MapPlug("n", "aw", "AddToLispWords")
call vimclojure#MapPlug("n", "tr", "ToggleParenRainbow")

call vimclojure#MapPlug("n", "lw", "DocLookupWord")
call vimclojure#MapPlug("n", "li", "DocLookupInteractive")
call vimclojure#MapPlug("n", "jw", "JavadocLookupWord")
call vimclojure#MapPlug("n", "ji", "JavadocLookupInteractive")
call vimclojure#MapPlug("n", "fd", "FindDoc")

call vimclojure#MapPlug("n", "mw", "MetaLookupWord")
call vimclojure#MapPlug("n", "mi", "MetaLookupInteractive")

call vimclojure#MapPlug("n", "sw", "SourceLookupWord")
call vimclojure#MapPlug("n", "si", "SourceLookupInteractive")

call vimclojure#MapPlug("n", "gw", "GotoSourceWord")
call vimclojure#MapPlug("n", "gi", "GotoSourceInteractive")

call vimclojure#MapPlug("n", "rf", "RequireFile")
call vimclojure#MapPlug("n", "rF", "RequireFileAll")

call vimclojure#MapPlug("n", "rt", "RunTests")

call vimclojure#MapPlug("n", "me", "MacroExpand")
call vimclojure#MapPlug("n", "m1", "MacroExpand1")

call vimclojure#MapPlug("n", "ef", "EvalFile")
call vimclojure#MapPlug("n", "el", "EvalLine")
call vimclojure#MapPlug("v", "eb", "EvalBlock")
call vimclojure#MapPlug("n", "et", "EvalToplevel")
call vimclojure#MapPlug("n", "ep", "EvalParagraph")

call vimclojure#MapPlug("n", "sr", "StartRepl")
call vimclojure#MapPlug("n", "sR", "StartLocalRepl")

if exists("b:vimclojure_namespace")
	setlocal omnifunc=vimclojure#OmniCompletion

	augroup VimClojure
		autocmd CursorMovedI <buffer> if pumvisible() == 0 | pclose | endif
	augroup END
endif

call vimclojure#MapPlug("n", "p", "CloseResultBuffer")

let &cpo = s:cpo_save
