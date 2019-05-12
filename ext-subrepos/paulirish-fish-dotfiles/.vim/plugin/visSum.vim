" vim:filetype=vim foldmethod=marker textwidth=78
" ==========================================================================
" File:         visSum.vim (global plugin)
" Last Changed: 2012-07-17
" Maintainer:   Erik Falor <ewfalor@gmail.com>
" Version:      1.0
" License:      Vim License
"
" A great big thanks to Christian Mauderer for providing a patch for
" floating-point support!
"
"                     ________                __        __
"                    /_  __/ /_  ____ _____  / /_______/ /
"                     / / / __ \/ __ `/ __ \/ //_/ ___/ /
"                    / / / / / / /_/ / / / / ,< (__  )_/
"                   /_/ /_/ /_/\__,_/_/ /_/_/|_/____(_)
"
" This plugin will work whether or not your Vim is compiled with support for
" floating-point numbers.  If your Vim doesn't has('float'), we'll just
" ignore whatever comes after the decimal point.
"
" Due to the way Vim parses floating-point numbers, the only valid separtator
" between the whole and fractional parts of the number is a period.  Vim
" won't accept a comma, even if that's your locale's preference.  This
" plugin follows that convention.
" ==========================================================================

" Exit quickly if the script has already been loaded
let s:this_version = '1.0'
if exists('g:loaded_visSum') && g:loaded_visSum == s:this_version
	finish
endif
let g:loaded_visSum = s:this_version

"Mappings {{{
" clean up existing key mappings upon re-loading of script
if hasmapto('<Plug>SumNum')
	nunmap \su
	vunmap \su
	nunmap <Plug>SumNum
	vunmap <Plug>SumNum
endif

" Key mappings
nmap <silent> <unique> <Leader>su <Plug>SumNum
vmap <silent> <unique> <Leader>su <Plug>SumNum

if has('float')
	" Call the floating-point version of the function
	nmap <silent> <unique> <script> <Plug>SumNum	:call <SID>SumNumbers_Float() <CR>
	vmap <silent> <unique> <script> <Plug>SumNum	:call <SID>SumNumbers_Float() <CR>
	command! -nargs=? -range -register VisSum call <SID>SumNumbers_Float("<reg>")
else
	" Call the integer version of the function
	nmap <silent> <unique> <script> <Plug>SumNum	:call <SID>SumNumbers_Int() <CR>
	vmap <silent> <unique> <script> <Plug>SumNum	:call <SID>SumNumbers_Int() <CR>
	command! -nargs=? -range -register VisSum call <SID>SumNumbers_Int("<reg>")
endif
"}}}

function! <SID>SumNumbers_Float(...) range  "{{{
	let l:sum = 0.0
	let l:cur = ""

	if visualmode() =~ '\cv'
		let y1      = line("'<")
		let y2      = line("'>")
		while y1 <= y2
			let l:cur = matchstr( getline(y1), '-\?\d\+\(\.\d\+\)\?' )
			if l:cur == ""
				let l:cur = "0"
			endif
			let l:sum += eval(l:cur)
			let y1 += 1
		endwhile
	elseif visualmode() == "\<c-v>"
		let y1      = line("'<")
		let y2      = line("'>")
		let x1		= col("'<") - 1
		let len		= col("'>") - x1
		while y1 <= y2
			let line = getline(y1)
			let chunk = strpart(line, x1, len)
			let l:cur = matchstr( strpart(getline(y1), x1, len ), '-\?\d\+\(\.\d\+\)\?' )
			if l:cur == ""
				let l:cur = "0"
			endif
			let l:sum += eval(l:cur)
			let y1 += 1
		endwhile
	else
		echoerr "You must select some text in visual mode first"
		return
	endif

	"Drop the fractional amount if it's zero
	"TODO: When scientific notation is supported, this will need to be changed
	if abs(l:sum) == trunc(abs(l:sum))
		let l:sum = float2nr(l:sum)
	endif

	redraw
	echo "sum = " l:sum
	"save the sum in the variable b:sum, and optionally
	"into the register specified by the user
	let b:sum = l:sum
	if a:0 == 1 && len(a:1) > 0
		execute "let @" . a:1 . " = printf('%g', b:sum)"
	endif
endfunction "}}}

function! <SID>SumNumbers_Int(...) range  "{{{
	let l:sum = 0
	let l:cur = 0

	if visualmode() =~ '\cv'
		let y1      = line("'<")
		let y2      = line("'>")
		while y1 <= y2
			let l:cur = matchstr( getline(y1), '-\{-}\d\+' )
			let l:sum += l:cur
			let y1 += 1
		endwhile
	elseif visualmode() == "\<c-v>"
		let y1      = line("'<")
		let y2      = line("'>")
		let x1		= col("'<") - 1
		let len		= col("'>") - x1
		while y1 <= y2
			let line = getline(y1)
			let chunk = strpart(line, x1, len)
			let l:cur = matchstr( strpart(getline(y1), x1, len ), '-\{-}\d\+' )
			let l:sum += l:cur
			let y1 += 1
		endwhile
	else
		echoerr "You must select some text in visual mode first"
		return
	endif
	redraw
	echo "sum = " l:sum
	"save the sum in the variable b:sum, and optionally
	"into the register specified by the user
	let b:sum = l:sum
	if a:0 == 1 && len(a:1) > 0
		execute "let @" . a:1 . " = b:sum"
	endif
endfunction "}}}

"Test Data "{{{
" <column width=\"24\"> The winter of '49</column>
" <column width=\"18\"> The Summer of '48</column>
" <column width=\"44\"/>123
" <column width=\"14\"/>123
"1.5                    123
"-2                      123.0
"3.1                   123.1
"-4.2                   123.2
"+5.9                    123.3
"-6.0
"7
"8
"8.2
"9.
"10.
"-11.
"+12.
"
"The pedant in me wants to make these numbers work as well;
"but if I've learned anything, it's that the perfect is the
"enemy of the good.
"Avogadro    6.0221415e23
"Planck      6.626068E-34 m^2 kg / s
"Borh Radius 5.2917721092e−11 m
"}}}
