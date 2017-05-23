" Vdebug: Powerful, fast, multi-language debugger client for Vim.
"
" Script Info  {{{
"=============================================================================
"    Copyright: Copyright (C) 2012 Jon Cairns
"      Licence:	The MIT Licence (see LICENCE file)
" Name Of File: vdebug.vim
"  Description: Multi-language debugger client for Vim (PHP, Ruby, Python,
"               Perl, NodeJS)
"   Maintainer: Jon Cairns <jon at joncairns.com>
"      Version: 1.4.1
"               Inspired by the Xdebug plugin, which was originally written by 
"               Seung Woo Shin <segv <at> sayclub.com> and extended by many
"               others.
"        Usage: Use :help Vdebug for information on how to configure and use
"               this script, or visit the Github page http://github.com/joonty/vdebug.
"
"=============================================================================
" }}}

" Do not source this script when python is not compiled in.
if !has("python")
    finish
endif

silent doautocmd User VdebugPre

" Load start_vdebug.py either from the runtime directory (usually
" /usr/local/share/vim/vim71/plugin/ if you're running Vim 7.1) or from the
" home vim directory (usually ~/.vim/plugin/).
if filereadable($VIMRUNTIME."/plugin/python/start_vdebug.py")
  pyfile $VIMRUNTIME/plugin/start_vdebug.py
elseif filereadable($HOME."/.vim/plugin/python/start_vdebug.py")
  pyfile $HOME/.vim/plugin/python/start_vdebug.py
else
  " when we use pathogen for instance
  let $CUR_DIRECTORY=expand("<sfile>:p:h")

  if filereadable($CUR_DIRECTORY."/python/start_vdebug.py")
    pyfile $CUR_DIRECTORY/python/start_vdebug.py
  else
    call confirm('vdebug.vim: Unable to find start_vdebug.py. Place it in either your home vim directory or in the Vim runtime directory.', 'OK')
  endif
endif

" Nice characters get screwed up on windows
if has('win32') || has('win64')
    let g:vdebug_force_ascii = 1
elseif has('multi_byte') == 0
    let g:vdebug_force_ascii = 1
else
    let g:vdebug_force_ascii = 0
end

if !exists("g:vdebug_options")
    let g:vdebug_options = {}
endif

if !exists("g:vdebug_keymap")
    let g:vdebug_keymap = {}
endif

if !exists("g:vdebug_features")
    let g:vdebug_features = {}
endif

if !exists("g:vdebug_leader_key")
    let g:vdebug_leader_key = ""
endif

let g:vdebug_keymap_defaults = {
\    "run" : "<F5>",
\    "run_to_cursor" : "<F9>",
\    "step_over" : "<F2>",
\    "step_into" : "<F3>",
\    "step_out" : "<F4>",
\    "close" : "<F6>",
\    "detach" : "<F7>",
\    "set_breakpoint" : "<F10>",
\    "get_context" : "<F11>",
\    "eval_under_cursor" : "<F12>",
\    "eval_visual" : "<Leader>e"
\}

let g:vdebug_options_defaults = {
\    "port" : 9000,
\    "timeout" : 20,
\    "server" : '',
\    "on_close" : 'stop',
\    "break_on_open" : 1,
\    "ide_key" : '',
\    "debug_window_level" : 0,
\    "debug_file_level" : 0,
\    "debug_file" : "",
\    "path_maps" : {},
\    "watch_window_style" : 'expanded',
\    "marker_default" : '⬦',
\    "marker_closed_tree" : '▸',
\    "marker_open_tree" : '▾',
\    "continuous_mode"  : 0
\}

" Different symbols for non unicode Vims
if g:vdebug_force_ascii == 1
    let g:vdebug_options_defaults["marker_default"] = '*'
    let g:vdebug_options_defaults["marker_closed_tree"] = '+'
    let g:vdebug_options_defaults["marker_open_tree"] = '-'
endif

" Create the top dog
python debugger = DebuggerInterface()

" Commands
command! -nargs=? -complete=customlist,s:BreakpointTypes Breakpoint python debugger.set_breakpoint(<q-args>)
command! VdebugStart python debugger.run()
command! -nargs=? BreakpointRemove python debugger.remove_breakpoint(<q-args>)
command! BreakpointWindow python debugger.toggle_breakpoint_window()
command! -nargs=? -bang VdebugEval call s:HandleEval('<bang>', <q-args>)
command! -nargs=+ -complete=customlist,s:OptionNames VdebugOpt python debugger.handle_opt(<f-args>)
command! -nargs=? VdebugTrace python debugger.handle_trace(<q-args>)

if hlexists("DbgCurrentLine") == 0
    hi default DbgCurrentLine term=reverse ctermfg=White ctermbg=Red guifg=#ffffff guibg=#ff0000
end
if hlexists("DbgCurrentSign") == 0
    hi default DbgCurrentSign term=reverse ctermfg=White ctermbg=Red guifg=#ffffff guibg=#ff0000
end
if hlexists("DbgBreakptLine") == 0
    hi default DbgBreakptLine term=reverse ctermfg=White ctermbg=Green guifg=#ffffff guibg=#00ff00
end
if hlexists("DbgBreakptSign") == 0
    hi default DbgBreakptSign term=reverse ctermfg=White ctermbg=Green guifg=#ffffff guibg=#00ff00
end

" Signs and highlighted lines for breakpoints, etc.
sign define current text=-> texthl=DbgCurrentSign linehl=DbgCurrentLine
sign define breakpt text=B> texthl=DbgBreakptSign linehl=DbgBreakptLine

function! s:BreakpointTypes(A,L,P)
    let arg_to_cursor = strpart(a:L,11,a:P)
    let space_idx = stridx(arg_to_cursor,' ')
    if space_idx == -1
        return filter(['conditional ','exception ','return ','call ','watch '],'v:val =~ "^".a:A.".*"')
    else
        return []
    endif
endfunction

function! s:HandleEval(bang,code)
    let code = escape(a:code,'"')
    if strlen(a:bang)
        execute 'python debugger.save_eval("'.code.'")'
    endif
    if strlen(a:code)
        execute 'python debugger.handle_eval("'.code.'")'
    endif
endfunction

" Reload options dictionary, by merging with default options.
"
" This should be called if you want to update the options after vdebug has
" been loaded.
function! Vdebug_load_options(options)
    " Merge options with defaults
    let g:vdebug_options = extend(g:vdebug_options_defaults, a:options)
endfunction

" Assign keymappings, and merge with defaults.
"
" This should be called if you want to update the keymappings after vdebug has
" been loaded.
function! Vdebug_load_keymaps(keymaps)
    " Unmap existing keys, if applicable
    if has_key(g:vdebug_keymap, "run")
        exe "silent! nunmap ".g:vdebug_keymap["run"]
    endif
    if has_key(g:vdebug_keymap, "set_breakpoint")
        exe "silent! nunmap ".g:vdebug_keymap["set_breakpoint"]
    endif
    if has_key(g:vdebug_keymap, "eval_visual")
        exe "silent! vunmap ".g:vdebug_keymap["eval_visual"]
    endif

    " Merge keymaps with defaults
    let g:vdebug_keymap = extend(g:vdebug_keymap_defaults, a:keymaps)

    " Mappings allowed in non-debug mode
    exe "noremap ".g:vdebug_keymap["run"]." :python debugger.run()<cr>"
    exe "noremap ".g:vdebug_keymap["set_breakpoint"]." :python debugger.set_breakpoint()<cr>"

    " Exceptional case for visual evaluation
    exe "vnoremap ".g:vdebug_keymap["eval_visual"]." :python debugger.handle_visual_eval()<cr>"
endfunction

function! s:OptionNames(A,L,P)
    let arg_to_cursor = strpart(a:L,10,a:P)
    let space_idx = stridx(arg_to_cursor,' ')
    if space_idx == -1
        return filter(keys(g:vdebug_options_defaults),'v:val =~ a:A')
    else
        let opt_name = strpart(arg_to_cursor,0,space_idx)
        if has_key(g:vdebug_options,opt_name)
            return [g:vdebug_options[opt_name]]
        else
            return []
        endif
    endif
endfunction

function! Vdebug_get_visual_selection()
  let [lnum1, col1] = getpos("'<")[1:2]
  let [lnum2, col2] = getpos("'>")[1:2]
  let lines = getline(lnum1, lnum2)
  let lines[-1] = lines[-1][: col2 - 1]
  let lines[0] = lines[0][col1 - 1:]
  return join(lines, "\n")
endfunction

function! Vdebug_edit(filename)
    try
        execute 'buffer' fnameescape(a:filename)
    catch /^Vim\%((\a\+)\)\=:E94/
        execute 'silent edit' fnameescape(a:filename)
    endtry
endfunction

silent doautocmd User VdebugPost
call Vdebug_load_options(g:vdebug_options)
call Vdebug_load_keymaps(g:vdebug_keymap)
