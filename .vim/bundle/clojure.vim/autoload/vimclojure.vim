" Part of Vim filetype plugin for Clojure
" Language:     Clojure
" Maintainer:   Meikel Brandmeyer <mb@kotka.de>

let s:save_cpo = &cpo
set cpo&vim

function! vimclojure#WarnDeprecated(old, new)
	echohl WarningMsg
	echomsg a:old . " is deprecated! Use " . a:new . "!"
	echomsg "eg. let " . a:new . " = <desired value here>"
	echohl None
endfunction

" Configuration
if !exists("g:vimclojure#FuzzyIndent")
	let vimclojure#FuzzyIndent = 0
endif

if !exists("g:vimclojure#HighlightBuiltins")
	if exists("g:clj_highlight_builtins")
		call vimclojure#WarnDeprecated("g:clj_highlight_builtins",
					\ "vimclojure#HighlightBuiltins")
		let vimclojure#HighlightBuiltins = g:clj_highlight_builtins
	else
		let vimclojure#HighlightBuiltins = 1
	endif
endif

if exists("g:clj_highlight_contrib")
	echohl WarningMsg
	echomsg "clj_highlight_contrib is deprecated! It's removed without replacement!"
	echohl None
endif

if !exists("g:vimclojure#DynamicHighlighting")
	if exists("g:clj_dynamic_highlighting")
		call vimclojure#WarnDeprecated("g:clj_dynamic_highlighting",
					\ "vimclojure#DynamicHighlighting")
		let vimclojure#DynamicHighlighting = g:clj_dynamic_highlighting
	else
		let vimclojure#DynamicHighlighting = 0
	endif
endif

if !exists("g:vimclojure#ParenRainbow")
	if exists("g:clj_paren_rainbow")
		call vimclojure#WarnDeprecated("g:clj_paren_rainbow",
					\ "vimclojure#ParenRainbow")
		let vimclojure#ParenRainbow = g:clj_paren_rainbow
	else
		let vimclojure#ParenRainbow = 0
	endif
endif

if !exists("g:vimclojure#WantNailgun")
	if exists("g:clj_want_gorilla")
		call vimclojure#WarnDeprecated("g:clj_want_gorilla",
					\ "vimclojure#WantNailgun")
		let vimclojure#WantNailgun = g:clj_want_gorilla
	else
		let vimclojure#WantNailgun = 0
	endif
endif

if !exists("g:vimclojure#NailgunServer")
	let vimclojure#NailgunServer = "127.0.0.1"
endif

if !exists("g:vimclojure#NailgunPort")
	let vimclojure#NailgunPort = "2113"
endif

if !exists("g:vimclojure#UseErrorBuffer")
	let vimclojure#UseErrorBuffer = 1
endif

function! vimclojure#ReportError(msg)
	if g:vimclojure#UseErrorBuffer
		let buf = g:vimclojure#ResultBuffer.New()
		call buf.showText(a:msg)
		wincmd p
	else
		echoerr substitute(a:msg, '\n\(\t\?\)', ' ', 'g')
	endif
endfunction

function! vimclojure#EscapePathForOption(path)
	let path = fnameescape(a:path)

	" Hardcore escapeing of whitespace...
	let path = substitute(path, '\', '\\\\', 'g')
	let path = substitute(path, '\ ', '\\ ', 'g')

	return path
endfunction

function! vimclojure#AddPathToOption(path, option)
	let path = vimclojure#EscapePathForOption(a:path)
	execute "setlocal " . a:option . "+=" . path
endfunction

function! vimclojure#AddCompletions(ns)
	let completions = split(globpath(&rtp, "ftplugin/clojure/completions-" . a:ns . ".txt"), '\n')
	if completions != []
		call vimclojure#AddPathToOption('k' . completions[0], 'complete')
	endif
endfunction

function! ClojureExtractSexprWorker() dict
	let pos = [0, 0]
	let start = getpos(".")

	if getline(start[1])[start[2] - 1] == "("
				\ && vimclojure#util#SynIdName() =~ 'clojureParen' . self.level
		let pos = [start[1], start[2]]
	endif

	if pos == [0, 0]
		let pos = searchpairpos('(', '', ')', 'bW' . self.flag,
					\ 'vimclojure#util#SynIdName() !~ "clojureParen\\d"')
	endif

	if pos == [0, 0]
		throw "Error: Not in a s-expression!"
	endif

	return [pos, vimclojure#util#Yank('l', 'normal! "ly%')]
endfunction

" Nailgun part:
function! vimclojure#ExtractSexpr(toplevel)
	let closure = {
				\ "flag"  : (a:toplevel ? "r" : ""),
				\ "level" : (a:toplevel ? "0" : '\d'),
				\ "f"     : function("ClojureExtractSexprWorker")
				\ }

	return vimclojure#util#WithSavedPosition(closure)
endfunction

function! vimclojure#BufferName()
	let file = expand("%")
	if file == ""
		let file = "UNNAMED"
	endif
	return file
endfunction

" Key mappings and Plugs
function! vimclojure#MakePlug(mode, plug, f, args)
	if a:mode == "i"
		let esc = "<ESC>"
	else
		let esc = ""
	endif

	execute a:mode . "noremap <Plug>Clojure" . a:plug
				\ . " " . esc . ":call " . a:f . "(" . a:args . ")<CR>"
endfunction

function! vimclojure#MakeProtectedPlug(mode, plug, f, args)
	execute a:mode . "noremap <Plug>Clojure" . a:plug
				\ . " :call vimclojure#ProtectedPlug(function(\""
				\ . a:f . "\"), [ " . a:args . " ])<CR>"
endfunction

function! vimclojure#MakeCommandPlug(mode, plug, f, args)
	execute a:mode . "noremap <Plug>Clojure" . a:plug
				\ . " :call vimclojure#ProtectedPlug("
				\ . " function(\"vimclojure#CommandPlug\"),"
				\ . " [ function(\"" . a:f . "\"), [ " . a:args . " ]])<CR>"
endfunction

function! vimclojure#MapPlug(mode, keys, plug)
	if !hasmapto("<Plug>Clojure" . a:plug, a:mode)
		execute a:mode . "map <buffer> <unique> <silent> <LocalLeader>" . a:keys
					\ . " <Plug>Clojure" . a:plug
	endif
endfunction

if !exists("*vimclojure#CommandPlug")
	function vimclojure#CommandPlug(f, args)
		if exists("b:vimclojure_loaded")
					\ && !exists("b:vimclojure_namespace")
					\ && g:vimclojure#WantNailgun == 1
			unlet b:vimclojure_loaded
			call vimclojure#InitBuffer("silent")
		endif

		if exists("b:vimclojure_namespace")
			call call(a:f, a:args)
		elseif g:vimclojure#WantNailgun == 1
			let msg = "VimClojure could not initialise the server connection.\n"
						\ . "That means you will not be able to use the interactive features.\n"
						\ . "Reasons might be that the server is not running or that there is\n"
						\ . "some trouble with the classpath.\n\n"
						\ . "VimClojure will *not* start the server for you or handle the classpath.\n"
						\ . "There is a plethora of tools like ivy, maven, gradle and leiningen,\n"
						\ . "which do this better than VimClojure could ever do it."
			throw msg
		endif
	endfunction
endif

if !exists("*vimclojure#ProtectedPlug")
	function vimclojure#ProtectedPlug(f, args)
		try
			return call(a:f, a:args)
		catch /.*/
			call vimclojure#ReportError(v:exception)
		endtry
	endfunction
endif

" A Buffer...
if !exists("g:vimclojure#SplitPos")
	let vimclojure#SplitPos = "top"
endif

if !exists("g:vimclojure#SplitSize")
	let vimclojure#SplitSize = ""
endif

let vimclojure#Object = {}

function! vimclojure#Object.New(...) dict
	let instance = copy(self)
	let instance.prototype = self

	call call(instance.Init, a:000, instance)

	return instance
endfunction

function! vimclojure#Object.Init() dict
endfunction

let vimclojure#Buffer = copy(vimclojure#Object)
let vimclojure#Buffer["__superObjectNew"] = vimclojure#Buffer["New"]

function! vimclojure#Buffer.New(...) dict
	if g:vimclojure#SplitPos == "left" || g:vimclojure#SplitPos == "right"
		let o_sr = &splitright
		if g:vimclojure#SplitPos == "left"
			set nosplitright
		else
			set splitright
		end
		execute printf("%svnew", g:vimclojure#SplitSize)
		let &splitright = o_sr
	else
		let o_sb = &splitbelow
		if g:vimclojure#SplitPos == "bottom"
			set splitbelow
		else
			set nosplitbelow
		end
		execute printf("%snew", g:vimclojure#SplitSize)
		let &splitbelow = o_sb
	endif

	return call(self.__superObjectNew, a:000, self)
endfunction

function! vimclojure#Buffer.Init() dict
	let self._buffer = bufnr("%")
endfunction

function! vimclojure#Buffer.goHere() dict
	execute "buffer! " . self._buffer
endfunction

function! vimclojure#Buffer.goHereWindow() dict
	execute "sbuffer! " . self._buffer
endfunction

function! vimclojure#Buffer.resize() dict
	call self.goHere()
	let size = line("$")
	if size < 3
		let size = 3
	endif
	execute "resize " . size
endfunction

function! vimclojure#Buffer.showText(text) dict
	call self.goHere()
	if type(a:text) == type("")
		let text = split(a:text, '\n')
	else
		let text = a:text
	endif
	call append(line("$"), text)
endfunction

function! vimclojure#Buffer.showOutput(output) dict
	call self.goHere()
	if a:output.value == 0
		if a:output.stdout != ""
			call self.showText(a:output.stdout)
		endif
		if a:output.stderr != ""
			call self.showText(a:output.stderr)
		endif
	else
		call self.showText(a:output.value)
	endif
endfunction

function! vimclojure#Buffer.clear() dict
	1
	normal! "_dG
endfunction

function! vimclojure#Buffer.close() dict
	execute "bdelete! " . self._buffer
endfunction

" The transient buffer, used to display results.
let vimclojure#ResultBuffer = copy(vimclojure#Buffer)
let vimclojure#ResultBuffer["__superBufferNew"] = vimclojure#ResultBuffer["New"]
let vimclojure#ResultBuffer["__superBufferInit"] = vimclojure#ResultBuffer["Init"]
let vimclojure#ResultBuffer.__instance = []

function! ClojureResultBufferNewWorker() dict
	set switchbuf=useopen
	call self.instance.goHereWindow()
	call call(self.instance.Init, self.args, self.instance)

	return self.instance
endfunction

function! vimclojure#ResultBuffer.New(...) dict
	if g:vimclojure#ResultBuffer.__instance != []
		let oldInstance = g:vimclojure#ResultBuffer.__instance[0]

		if oldInstance.prototype is self
			let closure = {
						\ 'instance' : oldInstance,
						\ 'args'     : a:000,
						\ 'f'        : function("ClojureResultBufferNewWorker")
						\ }

			return vimclojure#util#WithSavedOption('switchbuf', closure)
		else
			call oldInstance.close()
		endif
	endif

	let b:vimclojure_result_buffer = 1
	let instance = call(self.__superBufferNew, a:000, self)
	let g:vimclojure#ResultBuffer.__instance = [ instance ]

	return instance
endfunction

function! vimclojure#ResultBuffer.Init() dict
	call self.__superBufferInit()

	setlocal noswapfile
	setlocal buftype=nofile
	setlocal bufhidden=wipe

	call vimclojure#MapPlug("n", "p", "CloseResultBuffer")

	call self.clear()
	let leader = exists("g:maplocalleader") ? g:maplocalleader : "\\"
	call append(0, "; Use " . leader . "p to close this buffer!")
endfunction

function! vimclojure#ResultBuffer.CloseBuffer() dict
	if g:vimclojure#ResultBuffer.__instance != []
		let instance = g:vimclojure#ResultBuffer.__instance[0]
		let g:vimclojure#ResultBuffer.__instance = []
		call instance.close()
	endif
endfunction

function! s:InvalidateResultBufferIfNecessary(buf)
	if g:vimclojure#ResultBuffer.__instance != []
				\ && g:vimclojure#ResultBuffer.__instance[0]._buffer == a:buf
		let g:vimclojure#ResultBuffer.__instance = []
	endif
endfunction

augroup VimClojureResultBuffer
	au BufDelete * call s:InvalidateResultBufferIfNecessary(expand("<abuf>"))
augroup END

" A special result buffer for clojure output.
let vimclojure#ClojureResultBuffer = copy(vimclojure#ResultBuffer)
let vimclojure#ClojureResultBuffer["__superResultBufferInit"] =
			\ vimclojure#ResultBuffer["Init"]
let vimclojure#ClojureResultBuffer["__superResultBufferShowOutput"] =
			\ vimclojure#ResultBuffer["showOutput"]

function! vimclojure#ClojureResultBuffer.Init(ns) dict
	call self.__superResultBufferInit()
	set filetype=clojure
	let b:vimclojure_namespace = a:ns
endfunction

function! vimclojure#ClojureResultBuffer.showOutput(text) dict
	call self.__superResultBufferShowOutput(a:text)
	normal G
endfunction

" Nails
if !exists("vimclojure#NailgunClient")
	let vimclojure#NailgunClient = "ng"
endif

function! ClojureShellEscapeArgumentsWorker() dict
	set noshellslash
	return map(copy(self.vals), 'shellescape(v:val)')
endfunction

function! vimclojure#ShellEscapeArguments(vals)
	let closure = {
				\ 'vals': a:vals,
				\ 'f'   : function("ClojureShellEscapeArgumentsWorker")
				\ }

	return vimclojure#util#WithSavedOption('shellslash', closure)
endfunction

function! vimclojure#ExecuteNailWithInput(nail, input, ...)
	if type(a:input) == type("")
		let input = split(a:input, '\n', 1)
	else
		let input = a:input
	endif

	let inputfile = tempname()
	try
		call writefile(input, inputfile)

		let cmdline = vimclojure#ShellEscapeArguments(
					\ [g:vimclojure#NailgunClient,
					\   '--nailgun-server', g:vimclojure#NailgunServer,
					\   '--nailgun-port', g:vimclojure#NailgunPort,
					\   'vimclojure.Nail', a:nail]
					\ + a:000)
		let cmd = join(cmdline, " ") . " <" . inputfile
		" Add hardcore quoting for Windows
		if has("win32") || has("win64")
			let cmd = '"' . cmd . '"'
		endif

		let output = system(cmd)

		if v:shell_error
			throw "Error executing Nail! (" . v:shell_error . ")\n" . output
		endif
	finally
		call delete(inputfile)
	endtry

	execute "let result = " . substitute(output, '\n$', '', '')
	return result
endfunction

function! vimclojure#ExecuteNail(nail, ...)
	return call(function("vimclojure#ExecuteNailWithInput"), [a:nail, ""] + a:000)
endfunction

function! vimclojure#DocLookup(word)
	if a:word == ""
		return
	endif

	let doc = vimclojure#ExecuteNailWithInput("DocLookup", a:word,
				\ "-n", b:vimclojure_namespace)
	let buf = g:vimclojure#ResultBuffer.New()
	call buf.showOutput(doc)
	wincmd p
endfunction

function! vimclojure#FindDoc()
	let pattern = input("Pattern to look for: ")
	let doc = vimclojure#ExecuteNailWithInput("FindDoc", pattern)
	let buf = g:vimclojure#ResultBuffer.New()
	call buf.showOutput(doc)
	wincmd p
endfunction

let s:DefaultJavadocPaths = {
			\ "java" : "http://java.sun.com/javase/6/docs/api/",
			\ "org/apache/commons/beanutils" : "http://commons.apache.org/beanutils/api/",
			\ "org/apache/commons/chain" : "http://commons.apache.org/chain/api-release/",
			\ "org/apache/commons/cli" : "http://commons.apache.org/cli/api-release/",
			\ "org/apache/commons/codec" : "http://commons.apache.org/codec/api-release/",
			\ "org/apache/commons/collections" : "http://commons.apache.org/collections/api-release/",
			\ "org/apache/commons/logging" : "http://commons.apache.org/logging/apidocs/",
			\ "org/apache/commons/mail" : "http://commons.apache.org/email/api-release/",
			\ "org/apache/commons/io" : "http://commons.apache.org/io/api-release/"
			\ }

if !exists("vimclojure#JavadocPathMap")
	let vimclojure#JavadocPathMap = {}
endif

for k in keys(s:DefaultJavadocPaths)
	if !has_key(vimclojure#JavadocPathMap, k)
		let vimclojure#JavadocPathMap[k] = s:DefaultJavadocPaths[k]
	endif
endfor

if !exists("vimclojure#Browser")
	if has("win32") || has("win64")
		let vimclojure#Browser = "start"
	elseif has("mac")
		let vimclojure#Browser = "open"
	else
		" some freedesktop thing, whatever, issue #67
		let vimclojure#Browser = "xdg-open"
	endif
endif

function! vimclojure#JavadocLookup(word)
	let word = substitute(a:word, "\\.$", "", "")
	let path = vimclojure#ExecuteNailWithInput("JavadocPath", word,
				\ "-n", b:vimclojure_namespace)

	if path.stderr != ""
		let buf = g:vimclojure#ResultBuffer.New()
		call buf.showOutput(path)
		wincmd p
		return
	endif

	let match = ""
	for pattern in keys(g:vimclojure#JavadocPathMap)
		if path.value =~ "^" . pattern && len(match) < len(pattern)
			let match = pattern
		endif
	endfor

	if match == ""
		echoerr "No matching Javadoc URL found for " . path.value
	endif

	let url = g:vimclojure#JavadocPathMap[match] . path.value
	call system(join([g:vimclojure#Browser, url], " "))
endfunction

function! vimclojure#SourceLookup(word)
	let source = vimclojure#ExecuteNailWithInput("SourceLookup", a:word,
				\ "-n", b:vimclojure_namespace)
	let buf = g:vimclojure#ClojureResultBuffer.New(b:vimclojure_namespace)
	call buf.showOutput(source)
	wincmd p
endfunction

function! vimclojure#MetaLookup(word)
	let meta = vimclojure#ExecuteNailWithInput("MetaLookup", a:word,
				\ "-n", b:vimclojure_namespace)
	let buf = g:vimclojure#ClojureResultBuffer.New(b:vimclojure_namespace)
	call buf.showOutput(meta)
	wincmd p
endfunction

function! vimclojure#GotoSource(word)
	let pos = vimclojure#ExecuteNailWithInput("SourceLocation", a:word,
				\ "-n", b:vimclojure_namespace)

	if pos.stderr != ""
		let buf = g:vimclojure#ResultBuffer.New()
		call buf.showOutput(pos)
		wincmd p
		return
	endif

	if !filereadable(pos.value.file)
		let file = findfile(pos.value.file)
		if file == ""
			echoerr pos.value.file . " not found in 'path'"
			return
		endif
		let pos.value.file = file
	endif

	execute "edit " . pos.value.file
	execute pos.value.line
endfunction

" Evaluators
function! vimclojure#MacroExpand(firstOnly)
	let [unused, sexp] = vimclojure#ExtractSexpr(0)
	let ns = b:vimclojure_namespace

	let cmd = ["MacroExpand", sexp, "-n", ns]
	if a:firstOnly
		let cmd = cmd + [ "-o" ]
	endif

	let expanded = call(function("vimclojure#ExecuteNailWithInput"), cmd)

	let buf = g:vimclojure#ClojureResultBuffer.New(ns)
	call buf.showOutput(expanded)
	wincmd p
endfunction

function! vimclojure#RequireFile(all)
	let ns = b:vimclojure_namespace
	let all = a:all ? "-all" : ""

	let require = "(require :reload" . all . " :verbose '". ns. ")"
	let result = vimclojure#ExecuteNailWithInput("Repl", require, "-r")

	let resultBuffer = g:vimclojure#ClojureResultBuffer.New(ns)
	call resultBuffer.showOutput(result)
	wincmd p
endfunction

function! vimclojure#RunTests(all)
	let ns = b:vimclojure_namespace

	let result = call(function("vimclojure#ExecuteNailWithInput"),
				\ [ "RunTests", "", "-n", ns ] + (a:all ? [ "-a" ] : []))
	let resultBuffer = g:vimclojure#ClojureResultBuffer.New(ns)
	call resultBuffer.showOutput(result)
	wincmd p
endfunction

function! vimclojure#EvalFile()
	let content = getbufline(bufnr("%"), 1, line("$"))
	let file = vimclojure#BufferName()
	let ns = b:vimclojure_namespace

	let result = vimclojure#ExecuteNailWithInput("Repl", content,
				\ "-r", "-n", ns, "-f", file)

	let resultBuffer = g:vimclojure#ClojureResultBuffer.New(ns)
	call resultBuffer.showOutput(result)
	wincmd p
endfunction

function! vimclojure#EvalLine()
	let theLine = line(".")
	let content = getline(theLine)
	let file = vimclojure#BufferName()
	let ns = b:vimclojure_namespace

	let result = vimclojure#ExecuteNailWithInput("Repl", content,
				\ "-r", "-n", ns, "-f", file, "-l", theLine)

	let resultBuffer = g:vimclojure#ClojureResultBuffer.New(ns)
	call resultBuffer.showOutput(result)
	wincmd p
endfunction

function! vimclojure#EvalBlock()
	let file = vimclojure#BufferName()
	let ns = b:vimclojure_namespace

	let content = getbufline(bufnr("%"), line("'<"), line("'>"))
	let result = vimclojure#ExecuteNailWithInput("Repl", content,
				\ "-r", "-n", ns, "-f", file, "-l", line("'<") - 1)

	let resultBuffer = g:vimclojure#ClojureResultBuffer.New(ns)
	call resultBuffer.showOutput(result)
	wincmd p
endfunction

function! vimclojure#EvalToplevel()
	let file = vimclojure#BufferName()
	let ns = b:vimclojure_namespace
	let [pos, expr] = vimclojure#ExtractSexpr(1)

	let result = vimclojure#ExecuteNailWithInput("Repl", expr,
				\ "-r", "-n", ns, "-f", file, "-l", pos[0] - 1)

	let resultBuffer = g:vimclojure#ClojureResultBuffer.New(ns)
	call resultBuffer.showOutput(result)
	wincmd p
endfunction

function! ClojureEvalParagraphWorker() dict
	normal! }
	return line(".")
endfunction

function! vimclojure#EvalParagraph()
	let file = vimclojure#BufferName()
	let ns = b:vimclojure_namespace
	let startPosition = line(".")

	let closure = { 'f' : function("ClojureEvalParagraphWorker") }

	let endPosition = vimclojure#util#WithSavedPosition(closure)

	let content = getbufline(bufnr("%"), startPosition, endPosition)
	let result = vimclojure#ExecuteNailWithInput("Repl", content,
				\ "-r", "-n", ns, "-f", file, "-l", startPosition - 1)

	let resultBuffer = g:vimclojure#ClojureResultBuffer.New(ns)
	call resultBuffer.showOutput(result)
	wincmd p
endfunction

" The Repl
let vimclojure#Repl = copy(vimclojure#Buffer)
let vimclojure#Repl.__superBufferNew = vimclojure#Repl.New
let vimclojure#Repl.__superBufferInit = vimclojure#Repl.Init

let vimclojure#Repl._history = []
let vimclojure#Repl._historyDepth = 0
let vimclojure#Repl._replCommands = [ ",close", ",st", ",ct", ",toggle-pprint" ]

" Simple wrapper to allow on demand load of autoload/vimclojure.vim.
function! vimclojure#StartRepl(...)
	let ns = a:0 > 0 ? a:1 : "user"
	call g:vimclojure#Repl.New(ns)
endfunction

" FIXME: Ugly hack. But easier than cleaning up the buffer
" mess in case something goes wrong with repl start.
function! vimclojure#Repl.New(namespace) dict
	let replStart = vimclojure#ExecuteNail("Repl", "-s",
				\ "-n", a:namespace)
	if replStart.stderr != ""
		call vimclojure#ReportError(replStart.stderr)
		return
	endif

	let instance = call(self.__superBufferNew, [a:namespace], self)
	let instance._id = replStart.value.id
	call vimclojure#ExecuteNailWithInput("Repl",
				\ "(require 'clojure.stacktrace)",
				\ "-r", "-i", instance._id)

	return instance
endfunction

function! vimclojure#Repl.Init(namespace) dict
	call self.__superBufferInit()

	let self._prompt = a:namespace . "=>"

	setlocal buftype=nofile
	setlocal noswapfile

	call append(line("$"), ["Clojure", self._prompt . " "])

	let b:vimclojure_repl = self

	set filetype=clojure
	let b:vimclojure_namespace = a:namespace

	if !hasmapto("<Plug>ClojureReplEnterHook", "i")
		imap <buffer> <silent> <CR> <Plug>ClojureReplEnterHook
	endif
	if !hasmapto("<Plug>ClojureReplEvaluate", "i")
		imap <buffer> <silent> <C-CR> <Plug>ClojureReplEvaluate
	endif
	if !hasmapto("<Plug>ClojureReplHatHook", "n")
		nmap <buffer> <silent> ^ <Plug>ClojureReplHatHook
	endif
	if !hasmapto("<Plug>ClojureReplUpHistory", "i")
		imap <buffer> <silent> <C-Up> <Plug>ClojureReplUpHistory
	endif
	if !hasmapto("<Plug>ClojureReplDownHistory", "i")
		imap <buffer> <silent> <C-Down> <Plug>ClojureReplDownHistory
	endif

	normal! G
	startinsert!
endfunction

function! vimclojure#Repl.isReplCommand(cmd) dict
	for candidate in self._replCommands
		if candidate == a:cmd
			return 1
		endif
	endfor
	return 0
endfunction

function! vimclojure#Repl.doReplCommand(cmd) dict
	if a:cmd == ",close"
		call vimclojure#ExecuteNail("Repl", "-S", "-i", self._id)
		call self.close()
		stopinsert
	elseif a:cmd == ",st"
		let result = vimclojure#ExecuteNailWithInput("Repl",
					\ "(vimclojure.util/pretty-print-stacktrace *e)", "-r",
					\ "-i", self._id)
		call self.showOutput(result)
		call self.showPrompt()
	elseif a:cmd == ",ct"
		let result = vimclojure#ExecuteNailWithInput("Repl",
					\ "(vimclojure.util/pretty-print-causetrace *e)", "-r",
					\ "-i", self._id)
		call self.showOutput(result)
		call self.showPrompt()
	elseif a:cmd == ",toggle-pprint"
		let result = vimclojure#ExecuteNailWithInput("Repl",
					\ "(set! vimclojure.repl/*print-pretty* (not vimclojure.repl/*print-pretty*))", "-r",
					\ "-i", self._id)
		call self.showOutput(result)
		call self.showPrompt()
	endif
endfunction

function! vimclojure#Repl.showPrompt() dict
	call self.showText(self._prompt . " ")
	normal! G
	startinsert!
endfunction

function! vimclojure#Repl.getCommand() dict
	let ln = line("$")

	while getline(ln) !~ "^" . self._prompt && ln > 0
		let ln = ln - 1
	endwhile

	" Special Case: User deleted Prompt by accident. Insert a new one.
	if ln == 0
		call self.showPrompt()
		return ""
	endif

	let cmd = vimclojure#util#Yank("l", ln . "," . line("$") . "yank l")

	let cmd = substitute(cmd, "^" . self._prompt . "\\s*", "", "")
	let cmd = substitute(cmd, "\n$", "", "")
	return cmd
endfunction

function! vimclojure#ReplDoEnter()
	execute "normal! a\<CR>x"
	normal! ==x
	if getline(".") =~ '^\s*$'
		startinsert!
	else
		startinsert
	endif
endfunction

function! vimclojure#Repl.enterHook() dict
	let lastCol = {}

	function lastCol.f() dict
		normal! g_
		return col(".")
	endfunction

	if line(".") < line("$") || col(".") < vimclojure#util#WithSavedPosition(lastCol)
		call vimclojure#ReplDoEnter()
		return
	endif

	let cmd = self.getCommand()

	" Special Case: Showed prompt (or user just hit enter).
	if cmd =~ '^\(\s\|\n\)*$'
		execute "normal! a\<CR>"
		startinsert!
		return
	endif

	if self.isReplCommand(cmd)
		call self.doReplCommand(cmd)
		return
	endif

	let result = vimclojure#ExecuteNailWithInput("CheckSyntax", cmd,
				\ "-n", b:vimclojure_namespace)
	if result.value == 0 && result.stderr == ""
		call vimclojure#ReplDoEnter()
	elseif result.stderr != ""
		let buf = g:vimclojure#ResultBuffer.New()
		call buf.showOutput(result)
	else
		let result = vimclojure#ExecuteNailWithInput("Repl", cmd,
					\ "-r", "-i", self._id)
		call self.showOutput(result)

		let self._historyDepth = 0
		let self._history = [cmd] + self._history

		let namespace = vimclojure#ExecuteNailWithInput("ReplNamespace", "",
					\ "-i", self._id)
		let b:vimclojure_namespace = namespace.value
		let self._prompt = namespace.value . "=>"

		call self.showPrompt()
	endif
endfunction

function! vimclojure#Repl.hatHook() dict
	let l = getline(".")

	if l =~ "^" . self._prompt
		let [buf, line, col, off] = getpos(".")
		call setpos(".", [buf, line, len(self._prompt) + 2, off])
	else
		normal! ^
	endif
endfunction

function! vimclojure#Repl.upHistory() dict
	let histLen = len(self._history)
	let histDepth = self._historyDepth

	if histLen > 0 && histLen > histDepth
		let cmd = self._history[histDepth]
		let self._historyDepth = histDepth + 1

		call self.deleteLast()

		call self.showText(self._prompt . " " . cmd)
	endif

	normal! G$
endfunction

function! vimclojure#Repl.downHistory() dict
	let histLen = len(self._history)
	let histDepth = self._historyDepth

	if histDepth > 0 && histLen > 0
		let self._historyDepth = histDepth - 1
		let cmd = self._history[self._historyDepth]

		call self.deleteLast()

		call self.showText(self._prompt . " " . cmd)
	elseif histDepth == 0
		call self.deleteLast()
		call self.showText(self._prompt . " ")
	endif

	normal! G$
endfunction

function! vimclojure#Repl.deleteLast() dict
	normal! G

	while getline("$") !~ self._prompt
		normal! dd
	endwhile

	normal! dd
endfunction

" Highlighting
function! vimclojure#ColorNamespace(highlights)
	for [category, words] in items(a:highlights)
		if words != []
			execute "syntax keyword clojure" . category . " " . join(words, " ")
		endif
	endfor
endfunction

" Omni Completion
function! vimclojure#OmniCompletion(findstart, base)
	if a:findstart == 1
		let line = getline(".")
		let start = col(".") - 1

		while start > 0 && line[start - 1] =~ '\w\|-\|\.\|+\|*\|/'
			let start -= 1
		endwhile

		return start
	else
		let slash = stridx(a:base, '/')
		if slash > -1
			let prefix = strpart(a:base, 0, slash)
			let base = strpart(a:base, slash + 1)
		else
			let prefix = ""
			let base = a:base
		endif

		if prefix == "" && base == ""
			return []
		endif

		let completions = vimclojure#ExecuteNail("Complete",
					\ "-n", b:vimclojure_namespace,
					\ "-p", prefix, "-b", base)
		return completions.value
	endif
endfunction

function! vimclojure#InitBuffer(...)
	if exists("b:vimclojure_loaded")
		return
	endif
	let b:vimclojure_loaded = 1

	if g:vimclojure#WantNailgun == 1
		if !exists("b:vimclojure_namespace")
			" Get the namespace of the buffer.
			if &previewwindow
				let b:vimclojure_namespace = "user"
			else
				try
					let content = getbufline(bufnr("%"), 1, line("$"))
					let namespace =
								\ vimclojure#ExecuteNailWithInput(
								\   "NamespaceOfFile", content)
					if namespace.stderr != ""
						throw namespace.stderr
					endif
					let b:vimclojure_namespace = namespace.value
				catch /.*/
					if a:000 == []
						call vimclojure#ReportError(
									\ "Could not determine the Namespace of the file.\n\n"
									\ . "This might have different reasons. Please check, that the ng server\n"
									\ . "is running with the correct classpath and that the file does not contain\n"
									\ . "syntax errors. The interactive features will not be enabled, ie. the\n"
									\ . "keybindings will not be mapped.\n\nReason:\n" . v:exception)
					endif
				endtry
			endif
		endif
	endif
endfunction

function! vimclojure#AddToLispWords(word)
	execute "setlocal lw+=" . a:word
endfunction

function! vimclojure#ToggleParenRainbow()
	highlight clear clojureParen1
	highlight clear clojureParen2
	highlight clear clojureParen3
	highlight clear clojureParen4
	highlight clear clojureParen5
	highlight clear clojureParen6
	highlight clear clojureParen7
	highlight clear clojureParen8
	highlight clear clojureParen9

	let g:vimclojure#ParenRainbow = !g:vimclojure#ParenRainbow

	if g:vimclojure#ParenRainbow != 0
		if &background == "dark"
			highlight clojureParen1 ctermfg=yellow      guifg=orange1
			highlight clojureParen2 ctermfg=green       guifg=yellow1
			highlight clojureParen3 ctermfg=cyan        guifg=greenyellow
			highlight clojureParen4 ctermfg=magenta     guifg=green1
			highlight clojureParen5 ctermfg=red         guifg=springgreen1
			highlight clojureParen6 ctermfg=yellow      guifg=cyan1
			highlight clojureParen7 ctermfg=green       guifg=slateblue1
			highlight clojureParen8 ctermfg=cyan        guifg=magenta1
			highlight clojureParen9 ctermfg=magenta     guifg=purple1
		else
			highlight clojureParen1 ctermfg=darkyellow  guifg=orangered3
			highlight clojureParen2 ctermfg=darkgreen   guifg=orange2
			highlight clojureParen3 ctermfg=blue        guifg=yellow3
			highlight clojureParen4 ctermfg=darkmagenta guifg=olivedrab4
			highlight clojureParen5 ctermfg=red         guifg=green4
			highlight clojureParen6 ctermfg=darkyellow  guifg=paleturquoise3
			highlight clojureParen7 ctermfg=darkgreen   guifg=deepskyblue4
			highlight clojureParen8 ctermfg=blue        guifg=darkslateblue
			highlight clojureParen9 ctermfg=darkmagenta guifg=darkviolet
		endif
	else
		highlight link clojureParen1 clojureParen0
		highlight link clojureParen2 clojureParen0
		highlight link clojureParen3 clojureParen0
		highlight link clojureParen4 clojureParen0
		highlight link clojureParen5 clojureParen0
		highlight link clojureParen6 clojureParen0
		highlight link clojureParen7 clojureParen0
		highlight link clojureParen8 clojureParen0
		highlight link clojureParen9 clojureParen0
	endif
endfunction

" Epilog
let &cpo = s:save_cpo
