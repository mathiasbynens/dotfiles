" Vim syntax file
" Language: Vim Debugger Watch
" Maintainer: Jon Cairns
" Latest Revision: 2 August 2012

if exists("b:current_syntax")
  finish
endif

syn match debuggerStatusIdentifier '^Status:'
syn match debuggerStatusBreak '\s\zsbreak\ze'
syn match debuggerStatusStart '\s\zsrunning\ze'
syn match debuggerStatusStop '\s\zs\(stopped\|stopping\)\ze'
syn match debuggerStatusInfo '^\(Not\|Connected\|Listening\).*$'
syn region debuggerStatusHelp start='Press' end='information.'

hi def link debuggerStatusIdentifier Title
hi def link debuggerStatusStop Error
hi def link debuggerStatusBreak Special
hi def link debuggerStatusStart Constant
hi def link debuggerStatusInfo Type
hi def link debuggerStatusHelp Comment
