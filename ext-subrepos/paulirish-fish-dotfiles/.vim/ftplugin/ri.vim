" Vim filetype plugin
" Language:	ri / Ruby Information
" Description:	Interface for browsing ri/ruby documentation.
" Maintainer:   Jonas Fonseca <fonseca@diku.dk>
" Last Change:  Nov 26th 2002
" CVS Tag:	$Id: ri.vim,v 1.7 2002/11/27 03:39:26 fonseca Exp $
" License:	This file is placed in the public domain.
" Credits:	Thanks to Bob Hiestand <bob@hiestandfamily.org> for making
"		the cvscommand.vim plugin from which much of the code
"		derives. <URL:http://www.vim.org/script.php?script_id=90>
"
" Section: Documentation {{{1
"
" Below is just a description of the basic installation. For futher
" documentation on usage and configuration take a look at the file doc/ri.txt
"
" Installation: {{{2
"
" The Ri interface consists of 3 files:
"
"	ftplugin/ri.vim
"	syntax/ri.vim
"	doc/ri.txt
"
" With those in you vim directory add something like
"
"	" Load ri interface
"	source path/to/ftplugin/ri.vim
"
" to your ftplugin/ruby.vim to load it when editing ruby files.
"
" Section: Initialization {{{1
" Only do this when not done yet for this buffer

if exists("g:did_ri_interface")
  finish
else
  " Don't load another plugin for this buffer
  let g:did_ri_interface = 1
endif

" Section: Event group setup {{{1
 
augroup Ri
augroup END

" Function: s:RiGetOption(name, default) {{{1 
" Grab a user-specified option to override the default provided.
" Options are searched in the window, buffer, then global spaces.

function! s:RiGetOption(name, default)
  if exists("w:" . a:name)
    execute "return w:".a:name
  elseif exists("b:" . a:name)
    execute "return b:".a:name
  elseif exists("g:" . a:name)
    execute "return g:".a:name
  else
    return a:default
  endif
endfunction

" Function: s:RiGetClassOrModule() {{{1
" Returns the class/module name when in a class/module ri buffer

function! s:RiGetClassOrModule()
  " Try (big) word under cursor
  let text = expand('<cWORD>')
  let class  = substitute(text, '\(\u\+\w*\(::\u\w*\)*\)([.#]|).*', '\1', '')
  if text != class
    return class
  endif
  let class  = substitute(text, '\(\u\+\w*\(::\u\w*\)*\).*', '\1', '')
  if text != class
    return class
  endif

  " Try first line where ri titles the current lookup.
  let text = getline(1)
  let class = substitute(text, '\(^\|.*\s\)\(\u\+\w*\(::\u\w*\)*\)([.#]|).*', '\2', '')
  if text != class
    return class
  endif
  let class = substitute(text, '\(^\|.*\s\)\(\u\+\w*\(::\u\w*\)*\).*', '\2', '')
  if text != class
    return class
  endif

  " Try the line of the cursor
  let text = getline(line('.'))
  let class = substitute(text, '\(^\|.*\s\)\(\u\+\w*\(::\u\w*\)*\)([.#]|).*', '\2', '')
  if text != class
    return class
  endif
  let class = substitute(text, '\(^\|.*\s\)\(\u\+\w*\(::\u\w*\)*\).*', '\2', '')
  if text != class
    return class
  endif

  return ''
endfunction

" Function: s:RiSetupBuffer() {{{1
" Attempts to switch to the LRU Ri buffer else creates a new buffer.

function! s:RiSetupBuffer(name)
  let v:errmsg = ""
  if exists("s:ri_buffer") && bufwinnr(s:ri_buffer) != -1
    " The Ri buffer is still open so switch to it
    let s:switchbuf_save = &switchbuf
    set switchbuf=useopen
    execute 'sbuffer' s:ri_buffer
    let &switchbuf = s:switchbuf_save
    let edit_cmd   = 'edit'
  else
    " Original buffer no longer exists.
    if s:RiGetOption('ri_split_orientation', 'horizontal') == 'horizontal'
      let edit_cmd = 'rightbelow split'
    else
      let edit_cmd = 'vert rightbelow split'
    endif
  end

  silent execute edit_cmd a:name

  if v:errmsg != ""
    if &modified && !&hidden
      echoerr "Unable to open command buffer: 'nohidden' is set and the current buffer is modified (see :help 'hidden')."
    else
      echoerr "Unable to open command buffer:" v:errmsg
    endif
    return -1
  endif

  " Define the environment and execute user-defined hooks.
  silent do Ri User RiBufferCreated
  let s:ri_buffer     = bufnr("%")
  setlocal buftype=nofile
  " Maybe ugly hack but it makes <cword> useful for ruby methodnames
  setlocal iskeyword=42,94,48-57,-,_,A-Z,a-z,,,+,%,<,>,[,],\?,\&,!,~,=,`,|
  setlocal foldmethod=marker	" No syntax folding
  setlocal noswapfile
  setlocal filetype=ri
  setlocal bufhidden=delete	" Delete buffer on hide

  return s:ri_buffer
endfunction

" Function: s:RiExecute(term) {{{1
" Sets up the Ri buffer and executes the Ri lookup 

function! s:RiExecute(term)
  let command    = '0r!ri "' . escape(a:term, '!') . '"'
  let buffername = 'Ri browser [' . escape(a:term, ' |*\') . ']'
  if s:RiSetupBuffer(buffername) == -1
    return -1
  endif
  silent execute command
  1

endfunction
" Function: s:RiAddFoldMarkers() {{{1
" Insert fold markers. Only possible on an unfolded buffer

function! s:RiAddFoldMarkers()
  let last_line = line('.')
  let line = 2
  let cur_ident = ''
  while line <= last_line
    execute line
    let ident = substitute(getline(line), '\s*\(\u\w*\(::\u\w*\)*\).*', '\1', '')
    if ident != cur_ident
      let cur_ident = ident
      let ident = '     ' . ident . ' {' . '{{1'
      call append(line - 1, ident)
      call append(line - 1, '')
      let line = line + 2
    else
      let line = line + 1
    endif
  endwhile
endfunction

" Function: s:RiExpandClass() {{{1
" Handles both expansion for prompt and <cwords>.

function! s:RiExpandClass(term)
  if s:RiGetOption('ri_check_expansion', 'on') == 'on'
    " No expansion when term's first char is uppercase
    if match(a:term, '^[A-Z]') == '0'
      return ''
    endif
  end
  let text = getline(2)
  let class = substitute(text, '^\s\{5}\(class\|module\): \(\u\+\w*\(::\u\w*\)*\).*', '\2', '')
  if text == class " No match
    let class = ''
  endif

  " Try to find a class to complete.
  if s:RiGetOption('ri_prompt_complete', 'off') != 'off'
    if a:term == '' && class == ''
      let class = s:RiGetClassOrModule()
    endif
  endif

  if class != ''
    return class . '#'
  endif
  return class
endfunction

" Function: Ri(term) {{{1
" Handles class/module expansion and initial escaping of search term.
" <expand> is a bool [0|1].
" <term> is a string. Prompting is done when it's empty.

function! Ri(term, expand)
  " Remove trailing bogus characters like punctuation dots.
  let term = substitute(a:term, '\(,[^<>]\?\|[()]\)*\.\?$', '', '')

  let class = ''
  if a:expand == 1
    let class = s:RiExpandClass(term) 
  endif

  if term == ''
    let term = input('Ri search term: ', class)
  elseif a:expand == 1 && class != ''
    let term = class . term
  endif

  " Remove bogus stuff ('.first' from 'Array.new.first' and '#' from '#each')
  let term = substitute(term, '^[.#:]*', '', '')
  let term = substitute(term, '\([^.#:]\+\([.#]\|::\)[^.]*\).*', '\1', '')

  if s:RiGetOption('ri_nonprompt_history', 'add') == 'add'
    call histadd('input', term)
  endif

  " Escape so Vim don't substitute with buffer name.
  call s:RiExecute(escape(term, '"%#`'))

  " Unfold if there more than one match
  if s:RiGetOption('ri_unfold_nonunique', 'off') != 'off'
    if getline(1) =~ 'is not unique'
      2
      " < and > used by module inheritence
      silent %substitute/,[^<>$]/\r     /g
      silent %substitute/,\?$//g
    endif
    if s:RiGetOption('ri_add_foldmarkers', 'on') == 'on'
      call s:RiAddFoldMarkers()
    endif
    1
  endif
endfunction

command! -nargs=1 Ri	   :call Ri('<args>', 0)
command! -nargs=1 RiExpand :call Ri('<args>', 1)

" Section: Setup mappings {{{1
" Prompt for search term

nnoremap <unique> <Plug>Ri :call Ri('', 0)<CR>
if !hasmapto('<Plug>Ri')
  nmap <unique> <Leader>ri <Plug>Ri
endif

if !hasmapto('<M-i>')
  noremap <M-i> :call Ri('', 0)<CR>
endif

" Expand class/module if possible and prompt
nnoremap <unique> <Plug>Rx :call Ri('', 1)<CR>
if !hasmapto('<Plug>Rx')
  nmap <unique> <Leader>rx <Plug>Rx
endif

if !hasmapto('<M-I>')
  noremap <M-I> :call Ri('', 1)<CR>
endif

" Tag-like greedy invoking
if !hasmapto('<M-]>')
  noremap <M-]> :call Ri(expand('<cWORD>'), 0)<cr>
endif

" Not so greedy invoking.
if !hasmapto('<M-[>')
  noremap <M-[> :call Ri(expand('<cword>'), 1)<cr>
endif
