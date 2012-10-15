" Vim filetype plugin file
" Language:     Clojure
" Maintainer:   Meikel Brandmeyer <mb@kotka.de>

" Only do this when not done yet for this buffer
if exists("clojure_loaded")
	finish
endif

let clojure_loaded = "2.2.0-SNAPSHOT"

let s:cpo_save = &cpo
set cpo&vim

command! -nargs=0 ClojureRepl call vimclojure#StartRepl()

call vimclojure#MakeProtectedPlug("n", "AddToLispWords", "vimclojure#AddToLispWords", "expand(\"<cword>\")")
call vimclojure#MakeProtectedPlug("n", "ToggleParenRainbow", "vimclojure#ToggleParenRainbow", "")

call vimclojure#MakeCommandPlug("n", "DocLookupWord", "vimclojure#DocLookup", "expand(\"<cword>\")")
call vimclojure#MakeCommandPlug("n", "DocLookupInteractive", "vimclojure#DocLookup", "input(\"Symbol to look up: \")")
call vimclojure#MakeCommandPlug("n", "JavadocLookupWord", "vimclojure#JavadocLookup", "expand(\"<cword>\")")
call vimclojure#MakeCommandPlug("n", "JavadocLookupInteractive", "vimclojure#JavadocLookup", "input(\"Class to lookup: \")")
call vimclojure#MakeCommandPlug("n", "FindDoc", "vimclojure#FindDoc", "")

call vimclojure#MakeCommandPlug("n", "MetaLookupWord", "vimclojure#MetaLookup", "expand(\"<cword>\")")
call vimclojure#MakeCommandPlug("n", "MetaLookupInteractive", "vimclojure#MetaLookup", "input(\"Symbol to look up: \")")

call vimclojure#MakeCommandPlug("n", "SourceLookupWord", "vimclojure#SourceLookup", "expand(\"<cword>\")")
call vimclojure#MakeCommandPlug("n", "SourceLookupInteractive", "vimclojure#SourceLookup", "input(\"Symbol to look up: \")")

call vimclojure#MakeCommandPlug("n", "GotoSourceWord", "vimclojure#GotoSource", "expand(\"<cword>\")")
call vimclojure#MakeCommandPlug("n", "GotoSourceInteractive", "vimclojure#GotoSource", "input(\"Symbol to go to: \")")

call vimclojure#MakeCommandPlug("n", "RequireFile", "vimclojure#RequireFile", "0")
call vimclojure#MakeCommandPlug("n", "RequireFileAll", "vimclojure#RequireFile", "1")

call vimclojure#MakeCommandPlug("n", "RunTests", "vimclojure#RunTests", "0")

call vimclojure#MakeCommandPlug("n", "MacroExpand",  "vimclojure#MacroExpand", "0")
call vimclojure#MakeCommandPlug("n", "MacroExpand1", "vimclojure#MacroExpand", "1")

call vimclojure#MakeCommandPlug("n", "EvalFile",      "vimclojure#EvalFile", "")
call vimclojure#MakeCommandPlug("n", "EvalLine",      "vimclojure#EvalLine", "")
call vimclojure#MakeCommandPlug("v", "EvalBlock",     "vimclojure#EvalBlock", "")
call vimclojure#MakeCommandPlug("n", "EvalToplevel",  "vimclojure#EvalToplevel", "")
call vimclojure#MakeCommandPlug("n", "EvalParagraph", "vimclojure#EvalParagraph", "")

call vimclojure#MakeCommandPlug("n", "StartRepl", "vimclojure#StartRepl", "")
call vimclojure#MakeCommandPlug("n", "StartLocalRepl", "vimclojure#StartRepl", "b:vimclojure_namespace")

inoremap <Plug>ClojureReplEnterHook <Esc>:call b:vimclojure_repl.enterHook()<CR>
inoremap <Plug>ClojureReplEvaluate <Esc>G$:call b:vimclojure_repl.enterHook()<CR>
nnoremap <Plug>ClojureReplHatHook :call b:vimclojure_repl.hatHook()<CR>
inoremap <Plug>ClojureReplUpHistory <C-O>:call b:vimclojure_repl.upHistory()<CR>
inoremap <Plug>ClojureReplDownHistory <C-O>:call b:vimclojure_repl.downHistory()<CR>

nnoremap <Plug>ClojureCloseResultBuffer :call vimclojure#ResultBuffer.CloseBuffer()<CR>

let &cpo = s:cpo_save
