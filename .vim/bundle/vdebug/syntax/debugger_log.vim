" Vim syntax file
" Language: Vim Debugger Watch
" Maintainer: Jon Cairns
" Latest Revision: 2 August 2012

if exists("b:current_syntax")
  finish
endif

syn match debuggerLogMarker '^-'
syn match debuggerLogDebug '\zs\[Debug\]\ze' 
syn match debuggerLogInfo '\zs\[Info\]\ze' 
syn match debuggerLogError '\zs\[ERROR\]\ze' 
syn match debuggerLogDate '\s{.*}\s' 

hi def link debuggerLogMarker Type
hi def link debuggerLogInfo Special
hi def link debuggerLogDebug Comment
hi def link debuggerLogError Error
hi def link debuggerLogDate Comment
