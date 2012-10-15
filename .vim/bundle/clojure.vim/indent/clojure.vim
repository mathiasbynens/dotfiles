" Vim indent file
" Language:      Clojure
" Maintainer:    Meikel Brandmeyer <mb@kotka.de>
" URL:           http://kotka.de/projects/clojure/vimclojure.html

" Only load this indent file when no other was loaded.
if exists("b:did_indent")
	finish
endif
let b:did_indent = 1

let s:save_cpo = &cpo
set cpo&vim

let b:undo_indent = "setlocal ai< si< lw< et< sts< sw< inde< indk<"

setlocal noautoindent expandtab nosmartindent

setlocal softtabstop=2
setlocal shiftwidth=2

setlocal indentkeys=!,o,O

if exists("*searchpairpos")

function! s:MatchPairs(open, close, stopat)
	" Stop only on vector and map [ resp. {. Ignore the ones in strings and
	" comments.
	return searchpairpos(a:open, '', a:close, 'bWn',
				\ 'vimclojure#util#SynIdName() !~ "clojureParen\\d"',
				\ a:stopat)
endfunction

function! ClojureCheckForStringWorker() dict
	" Check whether there is the last character of the previous line is
	" highlighted as a string. If so, we check whether it's a ". In this
	" case we have to check also the previous character. The " might be the
	" closing one. In case the we are still in the string, we search for the
	" opening ". If this is not found we take the indent of the line.
	let nb = prevnonblank(v:lnum - 1)

	if nb == 0
		return -1
	endif

	call cursor(nb, 0)
	call cursor(0, col("$") - 1)
	if vimclojure#util#SynIdName() != "clojureString"
		return -1
	endif

	" This will not work for a " in the first column...
	if vimclojure#util#Yank('l', 'normal! "lyl') == '"'
		call cursor(0, col("$") - 2)
		if vimclojure#util#SynIdName() != "clojureString"
			return -1
		endif
		if vimclojure#util#Yank('l', 'normal! "lyl') != '\\'
			return -1
		endif
		call cursor(0, col("$") - 1)
	endif

	let p = searchpos('\(^\|[^\\]\)\zs"', 'bW')

	if p != [0, 0]
		return p[1] - 1
	endif

	return indent(".")
endfunction

function! s:CheckForString()
	return vimclojure#util#WithSavedPosition({
				\ 'f' : function("ClojureCheckForStringWorker")
				\ })
endfunction

function! ClojureIsMethodSpecialCaseWorker() dict
	" Find the next enclosing form.
	call vimclojure#util#MoveBackward()

	" Special case: we are at a '(('.
	if vimclojure#util#Yank('l', 'normal! "lyl') == '('
		return 0
	endif
	call cursor(self.pos)

	let nextParen = s:MatchPairs('(', ')', 0)

	" Special case: we are now at toplevel.
	if nextParen == [0, 0]
		return 0
	endif
	call cursor(nextParen)

	call vimclojure#util#MoveForward()
	let keyword = vimclojure#util#Yank('l', 'normal! "lye')
	if index([ 'deftype', 'defrecord', 'reify', 'proxy',
				\ 'extend', 'extend-type', 'extend-protocol',
				\ 'letfn' ], keyword) >= 0
		return 1
	endif

	return 0
endfunction

function! s:IsMethodSpecialCase(position)
	let closure = {
				\ 'pos': a:position,
				\ 'f' : function("ClojureIsMethodSpecialCaseWorker")
				\ }

	return vimclojure#util#WithSavedPosition(closure)
endfunction

function! GetClojureIndent()
	" Get rid of special case.
	if line(".") == 1
		return 0
	endif

	" We have to apply some heuristics here to figure out, whether to use
	" normal lisp indenting or not.
	let i = s:CheckForString()
	if i > -1
		return i
	endif

	call cursor(0, 1)

	" Find the next enclosing [ or {. We can limit the second search
	" to the line, where the [ was found. If no [ was there this is
	" zero and we search for an enclosing {.
	let paren = s:MatchPairs('(', ')', 0)
	let bracket = s:MatchPairs('\[', '\]', paren[0])
	let curly = s:MatchPairs('{', '}', bracket[0])

	" In case the curly brace is on a line later then the [ or - in
	" case they are on the same line - in a higher column, we take the
	" curly indent.
	if curly[0] > bracket[0] || curly[1] > bracket[1]
		if curly[0] > paren[0] || curly[1] > paren[1]
			return curly[1]
		endif
	endif

	" If the curly was not chosen, we take the bracket indent - if
	" there was one.
	if bracket[0] > paren[0] || bracket[1] > paren[1]
		return bracket[1]
	endif

	" There are neither { nor [ nor (, ie. we are at the toplevel.
	if paren == [0, 0]
		return 0
	endif

	" Now we have to reimplement lispindent. This is surprisingly easy, as
	" soon as one has access to syntax items.
	"
	" - Check whether we are in a special position after deftype, defrecord,
	"   reify, proxy or letfn. These are special cases.
	" - Get the next keyword after the (.
	" - If its first character is also a (, we have another sexp and align
	"   one column to the right of the unmatched (.
	" - In case it is in lispwords, we indent the next line to the column of
	"   the ( + sw.
	" - If not, we check whether it is last word in the line. In that case
	"   we again use ( + sw for indent.
	" - In any other case we use the column of the end of the word + 2.
	call cursor(paren)

	if s:IsMethodSpecialCase(paren)
		return paren[1] + &shiftwidth - 1
	endif

	" In case we are at the last character, we use the paren position.
	if col("$") - 1 == paren[1]
		return paren[1]
	endif

	" In case after the paren is a whitespace, we search for the next word.
	normal! l
	if vimclojure#util#Yank('l', 'normal! "lyl') == ' '
		normal! w
	endif

	" If we moved to another line, there is no word after the (. We
	" use the ( position for indent.
	if line(".") > paren[0]
		return paren[1]
	endif

	" We still have to check, whether the keyword starts with a (, [ or {.
	" In that case we use the ( position for indent.
	let w = vimclojure#util#Yank('l', 'normal! "lye')
	if stridx('([{', w[0]) > 0
		return paren[1]
	endif

	if &lispwords =~ '\<' . w . '\>'
		return paren[1] + &shiftwidth - 1
	endif

	" XXX: Slight glitch here with special cases. However it's only
	" a heureustic. Offline we can't do more.
	if g:vimclojure#FuzzyIndent
				\ && w != 'with-meta'
				\ && w != 'clojure.core/with-meta'
				\ && w =~ '\(^\|/\)\(def\|with\)'
				\ && w !~ '\(^\|/\)\(def\|with\).*\*$'
				\ && w !~ '\(^\|/\)\(def\|with\).*-fn$'
		return paren[1] + &shiftwidth - 1
	endif

	normal! w
	if paren[0] < line(".")
		return paren[1] + &shiftwidth - 1
	endif

	normal! ge
	return col(".") + 1
endfunction

setlocal indentexpr=GetClojureIndent()

else

	" In case we have searchpairpos not available we fall back to
	" normal lisp indenting.
	setlocal indentexpr=
	setlocal lisp
	let b:undo_indent .= " lisp<"

endif

" Defintions:
setlocal lispwords=def,def-,defn,defn-,defmacro,defmacro-,defmethod,defmulti
setlocal lispwords+=defonce,defvar,defvar-,defunbound,let,fn,letfn,binding,proxy
setlocal lispwords+=defnk,definterface,defprotocol,deftype,defrecord,reify
setlocal lispwords+=extend,extend-protocol,extend-type,bound-fn

" Conditionals and Loops:
setlocal lispwords+=if,if-not,if-let,when,when-not,when-let,when-first
setlocal lispwords+=condp,case,loop,dotimes,for,while

" Blocks:
setlocal lispwords+=do,doto,try,catch,locking,with-in-str,with-out-str,with-open
setlocal lispwords+=dosync,with-local-vars,doseq,dorun,doall,->,->>,future
setlocal lispwords+=with-bindings

" Namespaces:
setlocal lispwords+=ns,clojure.core/ns

" Java Classes:
setlocal lispwords+=gen-class,gen-interface

let &cpo = s:save_cpo
