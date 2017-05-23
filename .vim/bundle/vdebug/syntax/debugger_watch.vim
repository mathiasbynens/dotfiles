" Vim syntax file
" Language: Vim Debugger Watch Window
" Maintainer: Jon Cairns
" Latest Revision: 2 August 2012

if exists("b:current_syntax")
  finish
endif

syn match debuggerWatchTabLine '^\s\[.*$' contains=debuggerWatchTab
syn match debuggerWatchTab '\[\s[^\]]\+\s\]' contains=debuggerWatchTabSel
syn match debuggerWatchTabSel '\*[a-zA-Z\s]\+' contained
syn match debuggerWatchTitle '^\-\s[A-Z].\+'
syn match debuggerWatchMarker '^\s\+[^|\/]'
syn match debuggerWatchJoiner '^\s\+[|\/^]'
syn match debuggerWatchEllipsis '^\s\+\.\.\.'
syn match debuggerWatchNumber '\d\+\.\=\d*'
syn match debuggerWatchVarName '\s\zs.\+\ze\s=' contains=debuggerWatchStringKey,debuggerWatchObjectProperty
syn match debuggerWatchStringKey '\'[^']\+\'' contained
syn match debuggerWatchObjectProperty '\(->\|::\)\zs[^ \-\[:]\+\ze' contained
syn match debuggerWatchTypeContainer '=\s\zs(.*)\ze' contains=debuggerWatchType,debuggerWatchSize
syn match debuggerWatchVarValue ')\zs.*$\ze'
syn match debuggerWatchType '(\zs[^ )]\+)\ze' contained
syn match debuggerWatchSize '\[\zs\d\+\ze\]' contained
syn region debuggerWatchString start=+\s`+ skip=+\\`+ end=+`\s*$+


hi def link debuggerWatchTitle Title
hi def link debuggerWatchMarker Special
hi def link debuggerWatchTab Special
hi def link debuggerWatchTabSel Todo
hi def link debuggerWatchTypeContainer Type
hi def link debuggerWatchType Type
hi def link debuggerWatchString String
hi def link debuggerWatchStringKey String
hi def link debuggerWatchVarName Identifier
hi def link debuggerWatchJoiner Structure
hi def link debuggerWatchEllipsis Structure
hi def link debuggerWatchNumber Number
hi def link debuggerWatchSize Number
