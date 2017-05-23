" Vim syntax file
" Language: Vim Debugger Watch Window
" Maintainer: Jon Cairns
" Latest Revision: 2 August 2012

if exists("b:current_syntax")
  finish
endif

syn region debuggerBreakpointHeader start=+^=+ end=+=$+
syn match debuggerBreakpointDivider '|'
syn match debuggerBreakpointTitle '[A-Z]\{2,}'
syn match debuggerBreakpointId '\s\d\{5,}\s'


hi def link debuggerBreakpointHeader Type
hi def link debuggerBreakpointDivider Type
hi def link debuggerBreakpointTitle Title
hi def link debuggerBreakpointId Number
