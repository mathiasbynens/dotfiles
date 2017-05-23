" Recognize '; ' at the start of a line as a comment and recognize one level
" of lists with '; - '.  Not smart enough to require ';' in first column.
setl comments=b:;\ -,b:;
" Complete keywords using <C-O>.  :help ft-syntax-omni
setl omnifunc=syntaxcomplete#Complete
