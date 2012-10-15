" histwin.vim - Vim global plugin for browsing the undo tree
" -------------------------------------------------------------
" Last Change: Tue, 04 May 2010 22:42:22 +0200
" Maintainer:  Christian Brabandt <cb@256bit.org>
" Version:     0.12
" Copyright:   (c) 2009 by Christian Brabandt
"              The VIM LICENSE applies to histwin.vim 
"              (see |copyright|) except use "histwin.vim" 
"              instead of "Vim".
"              No warranty, express or implied.
"    *** ***   Use At-Your-Own-Risk!   *** ***
"
" GetLatestVimScripts: 2932 6 :AutoInstall: histwin.vim
" TODO: - write documentation
"       - don't use matchadd for syntax highlighting but use
"         appropriate syntax highlighting rules

" Init:
if exists("g:loaded_undo_browse") || &cp || &ul == -1
  finish
endif

let g:loaded_undo_browse = 0.11
let s:cpo                = &cpo
set cpo&vim

" User_Command:
if exists(":UB") != 2
	com -nargs=0 UB :call histwin#UndoBrowse()
else
	echoerr "histwin: UB is already defined. May be by another Plugin?"
endif

" ChangeLog:
" see :h histwin-history

" Restore:
let &cpo=s:cpo
unlet s:cpo
" vim: ts=4 sts=4 fdm=marker com+=l\:\" fdm=syntax
