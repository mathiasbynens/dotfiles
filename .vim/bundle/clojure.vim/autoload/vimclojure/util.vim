" Part of Vim filetype plugin for Clojure
" Language:     Clojure
" Maintainer:   Meikel Brandmeyer <mb@kotka.de>

let s:save_cpo = &cpo
set cpo&vim

function! vimclojure#util#SynIdName()
	return synIDattr(synID(line("."), col("."), 0), "name")
endfunction

function! vimclojure#util#WithSaved(closure)
	let v = a:closure.save()
	try
		let r = a:closure.f()
	finally
		call a:closure.restore(v)
	endtry
	return r
endfunction

function! s:SavePosition() dict
	let [ _b, l, c, _o ] = getpos(".")
	let b = bufnr("%")
	return [b, l, c]
endfunction

function! s:RestorePosition(value) dict
	let [b, l, c] = a:value

	if bufnr("%") != b
		execute b "buffer!"
	endif
	call setpos(".", [0, l, c, 0])
endfunction

function! vimclojure#util#WithSavedPosition(closure)
	let a:closure.save = function("s:SavePosition")
	let a:closure.restore = function("s:RestorePosition")

	return vimclojure#util#WithSaved(a:closure)
endfunction

function! s:SaveRegister(reg)
	return [a:reg, getreg(a:reg, 1), getregtype(a:reg)]
endfunction

function! s:SaveRegisters() dict
	return map([self._register, "", "/", "-",
				\ "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
				\ "s:SaveRegister(v:val)")
endfunction

function! s:RestoreRegisters(registers) dict
	for register in a:registers
		call call(function("setreg"), register)
	endfor
endfunction

function! vimclojure#util#WithSavedRegister(reg, closure)
	let a:closure._register = a:reg
	let a:closure.save = function("s:SaveRegisters")
	let a:closure.restore = function("s:RestoreRegisters")

	return vimclojure#util#WithSaved(a:closure)
endfunction

function! s:SaveOption() dict
	return eval("&" . self._option)
endfunction

function! s:RestoreOption(value) dict
	execute "let &" . self._option . " = a:value"
endfunction

function! vimclojure#util#WithSavedOption(option, closure)
	let a:closure._option = a:option
	let a:closure.save = function("s:SaveOption")
	let a:closure.restore = function("s:RestoreOption")

	return vimclojure#util#WithSaved(a:closure)
endfunction

function! s:DoYank() dict
	silent execute self.yank
	return getreg(self.reg)
endfunction

function! vimclojure#util#Yank(r, how)
	let closure = {
				\ 'reg': a:r,
				\ 'yank': a:how,
				\ 'f': function("s:DoYank")
				\ }

	return vimclojure#util#WithSavedRegister(a:r, closure)
endfunction

function! vimclojure#util#MoveBackward()
	call search('\S', 'Wb')
endfunction

function! vimclojure#util#MoveForward()
	call search('\S', 'W')
endfunction

" Epilog
let &cpo = s:save_cpo
