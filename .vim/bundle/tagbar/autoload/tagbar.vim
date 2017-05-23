" ============================================================================
" File:        tagbar.vim
" Description: List the current file's tags in a sidebar, ordered by class etc
" Author:      Jan Larres <jan@majutsushi.net>
" Licence:     Vim licence
" Website:     http://majutsushi.github.com/tagbar/
" Version:     2.7
" Note:        This plugin was heavily inspired by the 'Taglist' plugin by
"              Yegappan Lakshmanan and uses a small amount of code from it.
"
" Original taglist copyright notice:
"              Permission is hereby granted to use and distribute this code,
"              with or without modifications, provided that this copyright
"              notice is copied with it. Like anything else that's free,
"              taglist.vim is provided *as is* and comes with no warranty of
"              any kind, either expressed or implied. In no event will the
"              copyright holder be liable for any damamges resulting from the
"              use of this software.
" ============================================================================

scriptencoding utf-8

" Initialization {{{1

" If another plugin calls an autoloaded Tagbar function on startup before the
" plugin/tagbar.vim file got loaded, load it explicitly
if exists(':Tagbar') == 0
    runtime plugin/tagbar.vim
endif

if exists(':Tagbar') == 0
    echomsg 'Tagbar: Could not load plugin code, check your runtimepath!'
    finish
endif

" Basic init {{{2

redir => s:ftype_out
silent filetype
redir END
if s:ftype_out !~# 'detection:ON'
    echomsg 'Tagbar: Filetype detection is turned off, skipping plugin'
    unlet s:ftype_out
    finish
endif
unlet s:ftype_out

let s:icon_closed = g:tagbar_iconchars[0]
let s:icon_open   = g:tagbar_iconchars[1]

let s:type_init_done    = 0
let s:autocommands_done = 0
let s:statusline_in_use = 0

" 0: not checked yet; 1: checked and found; 2: checked and not found
let s:checked_ctags       = 0
let s:checked_ctags_types = 0
let s:ctags_is_uctags     = 0
let s:ctags_types         = {}

let s:new_window      = 1
let s:is_maximized    = 0
let s:winrestcmd      = ''
let s:short_help      = 1
let s:nearby_disabled = 0
let s:paused = 0
let s:pwin_by_tagbar = 0
let s:buffer_seqno = 0
let s:vim_quitting = 0
let s:last_alt_bufnr = -1

let s:window_expanded   = 0
let s:expand_bufnr = -1
let s:window_pos = {
    \ 'pre'  : { 'x' : 0, 'y' : 0 },
    \ 'post' : { 'x' : 0, 'y' : 0 }
\}

let s:delayed_update_files = []

" Script-local variable needed since compare functions can't
" take extra arguments
let s:compare_typeinfo = {}

let s:visibility_symbols = {
    \ 'public'    : '+',
    \ 'protected' : '#',
    \ 'private'   : '-'
\ }

let g:loaded_tagbar = 1

let s:last_highlight_tline = 0
let s:debug = 0
let s:debug_file = ''

let s:warnings = {
    \ 'type': [],
    \ 'encoding': 0
\ }

" s:Init() {{{2
function! s:Init(silent) abort
    if s:checked_ctags == 2 && a:silent
        return 0
    elseif s:checked_ctags != 1
        if !s:CheckForExCtags(a:silent)
            return 0
        endif
    endif

    if !s:checked_ctags_types
        call s:GetSupportedFiletypes()
    endif

    if !s:type_init_done
        call s:InitTypes()
    endif

    if !s:autocommands_done
        call s:CreateAutocommands()
        call s:AutoUpdate(fnamemodify(expand('%'), ':p'), 0)
    endif

    return 1
endfunction

" s:InitTypes() {{{2
function! s:InitTypes() abort
    call s:debug('Initializing types')

    let s:known_types = {}

    " Ant {{{3
    let type_ant = s:TypeInfo.New()
    let type_ant.ctagstype = 'ant'
    let type_ant.kinds     = [
        \ {'short' : 'p', 'long' : 'projects', 'fold' : 0, 'stl' : 1},
        \ {'short' : 't', 'long' : 'targets',  'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.ant = type_ant
    " Asm {{{3
    let type_asm = s:TypeInfo.New()
    let type_asm.ctagstype = 'asm'
    let type_asm.kinds     = [
        \ {'short' : 'm', 'long' : 'macros',  'fold' : 0, 'stl' : 1},
        \ {'short' : 't', 'long' : 'types',   'fold' : 0, 'stl' : 1},
        \ {'short' : 'd', 'long' : 'defines', 'fold' : 0, 'stl' : 1},
        \ {'short' : 'l', 'long' : 'labels',  'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.asm = type_asm
    " ASP {{{3
    let type_aspvbs = s:TypeInfo.New()
    let type_aspvbs.ctagstype = 'asp'
    let type_aspvbs.kinds     = [
        \ {'short' : 'd', 'long' : 'constants',   'fold' : 0, 'stl' : 1},
        \ {'short' : 'c', 'long' : 'classes',     'fold' : 0, 'stl' : 1},
        \ {'short' : 'f', 'long' : 'functions',   'fold' : 0, 'stl' : 1},
        \ {'short' : 's', 'long' : 'subroutines', 'fold' : 0, 'stl' : 1},
        \ {'short' : 'v', 'long' : 'variables',   'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.aspvbs = type_aspvbs
    " Asymptote {{{3
    " Asymptote gets parsed well using filetype = c
    let type_asy = s:TypeInfo.New()
    let type_asy.ctagstype = 'c'
    let type_asy.kinds     = [
        \ {'short' : 'd', 'long' : 'macros',      'fold' : 1, 'stl' : 0},
        \ {'short' : 'p', 'long' : 'prototypes',  'fold' : 1, 'stl' : 0},
        \ {'short' : 'g', 'long' : 'enums',       'fold' : 0, 'stl' : 1},
        \ {'short' : 'e', 'long' : 'enumerators', 'fold' : 0, 'stl' : 0},
        \ {'short' : 't', 'long' : 'typedefs',    'fold' : 0, 'stl' : 0},
        \ {'short' : 's', 'long' : 'structs',     'fold' : 0, 'stl' : 1},
        \ {'short' : 'u', 'long' : 'unions',      'fold' : 0, 'stl' : 1},
        \ {'short' : 'm', 'long' : 'members',     'fold' : 0, 'stl' : 0},
        \ {'short' : 'v', 'long' : 'variables',   'fold' : 0, 'stl' : 0},
        \ {'short' : 'f', 'long' : 'functions',   'fold' : 0, 'stl' : 1}
    \ ]
    let type_asy.sro        = '::'
    let type_asy.kind2scope = {
        \ 'g' : 'enum',
        \ 's' : 'struct',
        \ 'u' : 'union'
    \ }
    let type_asy.scope2kind = {
        \ 'enum'   : 'g',
        \ 'struct' : 's',
        \ 'union'  : 'u'
    \ }
    let s:known_types.asy = type_asy
    " Awk {{{3
    let type_awk = s:TypeInfo.New()
    let type_awk.ctagstype = 'awk'
    let type_awk.kinds     = [
        \ {'short' : 'f', 'long' : 'functions', 'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.awk = type_awk
    " Basic {{{3
    let type_basic = s:TypeInfo.New()
    let type_basic.ctagstype = 'basic'
    let type_basic.kinds     = [
        \ {'short' : 'c', 'long' : 'constants',    'fold' : 0, 'stl' : 1},
        \ {'short' : 'g', 'long' : 'enumerations', 'fold' : 0, 'stl' : 1},
        \ {'short' : 'f', 'long' : 'functions',    'fold' : 0, 'stl' : 1},
        \ {'short' : 'l', 'long' : 'labels',       'fold' : 0, 'stl' : 1},
        \ {'short' : 't', 'long' : 'types',        'fold' : 0, 'stl' : 1},
        \ {'short' : 'v', 'long' : 'variables',    'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.basic = type_basic
    " BETA {{{3
    let type_beta = s:TypeInfo.New()
    let type_beta.ctagstype = 'beta'
    let type_beta.kinds     = [
        \ {'short' : 'f', 'long' : 'fragments', 'fold' : 0, 'stl' : 1},
        \ {'short' : 's', 'long' : 'slots',     'fold' : 0, 'stl' : 1},
        \ {'short' : 'v', 'long' : 'patterns',  'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.beta = type_beta
    " C {{{3
    let type_c = s:TypeInfo.New()
    let type_c.ctagstype = 'c'
    let type_c.kinds     = [
        \ {'short' : 'd', 'long' : 'macros',      'fold' : 1, 'stl' : 0},
        \ {'short' : 'p', 'long' : 'prototypes',  'fold' : 1, 'stl' : 0},
        \ {'short' : 'g', 'long' : 'enums',       'fold' : 0, 'stl' : 1},
        \ {'short' : 'e', 'long' : 'enumerators', 'fold' : 0, 'stl' : 0},
        \ {'short' : 't', 'long' : 'typedefs',    'fold' : 0, 'stl' : 0},
        \ {'short' : 's', 'long' : 'structs',     'fold' : 0, 'stl' : 1},
        \ {'short' : 'u', 'long' : 'unions',      'fold' : 0, 'stl' : 1},
        \ {'short' : 'm', 'long' : 'members',     'fold' : 0, 'stl' : 0},
        \ {'short' : 'v', 'long' : 'variables',   'fold' : 0, 'stl' : 0},
        \ {'short' : 'f', 'long' : 'functions',   'fold' : 0, 'stl' : 1}
    \ ]
    let type_c.sro        = '::'
    let type_c.kind2scope = {
        \ 'g' : 'enum',
        \ 's' : 'struct',
        \ 'u' : 'union'
    \ }
    let type_c.scope2kind = {
        \ 'enum'   : 'g',
        \ 'struct' : 's',
        \ 'union'  : 'u'
    \ }
    let s:known_types.c = type_c
    " C++ {{{3
    let type_cpp = s:TypeInfo.New()
    let type_cpp.ctagstype = 'c++'
    let type_cpp.kinds     = [
        \ {'short' : 'd', 'long' : 'macros',      'fold' : 1, 'stl' : 0},
        \ {'short' : 'p', 'long' : 'prototypes',  'fold' : 1, 'stl' : 0},
        \ {'short' : 'g', 'long' : 'enums',       'fold' : 0, 'stl' : 1},
        \ {'short' : 'e', 'long' : 'enumerators', 'fold' : 0, 'stl' : 0},
        \ {'short' : 't', 'long' : 'typedefs',    'fold' : 0, 'stl' : 0},
        \ {'short' : 'n', 'long' : 'namespaces',  'fold' : 0, 'stl' : 1},
        \ {'short' : 'c', 'long' : 'classes',     'fold' : 0, 'stl' : 1},
        \ {'short' : 's', 'long' : 'structs',     'fold' : 0, 'stl' : 1},
        \ {'short' : 'u', 'long' : 'unions',      'fold' : 0, 'stl' : 1},
        \ {'short' : 'f', 'long' : 'functions',   'fold' : 0, 'stl' : 1},
        \ {'short' : 'm', 'long' : 'members',     'fold' : 0, 'stl' : 0},
        \ {'short' : 'v', 'long' : 'variables',   'fold' : 0, 'stl' : 0}
    \ ]
    let type_cpp.sro        = '::'
    let type_cpp.kind2scope = {
        \ 'g' : 'enum',
        \ 'n' : 'namespace',
        \ 'c' : 'class',
        \ 's' : 'struct',
        \ 'u' : 'union'
    \ }
    let type_cpp.scope2kind = {
        \ 'enum'      : 'g',
        \ 'namespace' : 'n',
        \ 'class'     : 'c',
        \ 'struct'    : 's',
        \ 'union'     : 'u'
    \ }
    let s:known_types.cpp = type_cpp
    let s:known_types.cuda = type_cpp
    " C# {{{3
    let type_cs = s:TypeInfo.New()
    let type_cs.ctagstype = 'c#'
    let type_cs.kinds     = [
        \ {'short' : 'd', 'long' : 'macros',      'fold' : 1, 'stl' : 0},
        \ {'short' : 'f', 'long' : 'fields',      'fold' : 0, 'stl' : 1},
        \ {'short' : 'g', 'long' : 'enums',       'fold' : 0, 'stl' : 1},
        \ {'short' : 'e', 'long' : 'enumerators', 'fold' : 0, 'stl' : 0},
        \ {'short' : 't', 'long' : 'typedefs',    'fold' : 0, 'stl' : 1},
        \ {'short' : 'n', 'long' : 'namespaces',  'fold' : 0, 'stl' : 1},
        \ {'short' : 'i', 'long' : 'interfaces',  'fold' : 0, 'stl' : 1},
        \ {'short' : 'c', 'long' : 'classes',     'fold' : 0, 'stl' : 1},
        \ {'short' : 's', 'long' : 'structs',     'fold' : 0, 'stl' : 1},
        \ {'short' : 'E', 'long' : 'events',      'fold' : 0, 'stl' : 1},
        \ {'short' : 'm', 'long' : 'methods',     'fold' : 0, 'stl' : 1},
        \ {'short' : 'p', 'long' : 'properties',  'fold' : 0, 'stl' : 1}
    \ ]
    let type_cs.sro        = '.'
    let type_cs.kind2scope = {
        \ 'n' : 'namespace',
        \ 'i' : 'interface',
        \ 'c' : 'class',
        \ 's' : 'struct',
        \ 'g' : 'enum'
    \ }
    let type_cs.scope2kind = {
        \ 'namespace' : 'n',
        \ 'interface' : 'i',
        \ 'class'     : 'c',
        \ 'struct'    : 's',
        \ 'enum'      : 'g'
    \ }
    let s:known_types.cs = type_cs
    " COBOL {{{3
    let type_cobol = s:TypeInfo.New()
    let type_cobol.ctagstype = 'cobol'
    let type_cobol.kinds     = [
        \ {'short' : 'd', 'long' : 'data items',        'fold' : 0, 'stl' : 1},
        \ {'short' : 'f', 'long' : 'file descriptions', 'fold' : 0, 'stl' : 1},
        \ {'short' : 'g', 'long' : 'group items',       'fold' : 0, 'stl' : 1},
        \ {'short' : 'p', 'long' : 'paragraphs',        'fold' : 0, 'stl' : 1},
        \ {'short' : 'P', 'long' : 'program ids',       'fold' : 0, 'stl' : 1},
        \ {'short' : 's', 'long' : 'sections',          'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.cobol = type_cobol
    " DOS Batch {{{3
    let type_dosbatch = s:TypeInfo.New()
    let type_dosbatch.ctagstype = 'dosbatch'
    let type_dosbatch.kinds     = [
        \ {'short' : 'l', 'long' : 'labels',    'fold' : 0, 'stl' : 1},
        \ {'short' : 'v', 'long' : 'variables', 'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.dosbatch = type_dosbatch
    " Eiffel {{{3
    let type_eiffel = s:TypeInfo.New()
    let type_eiffel.ctagstype = 'eiffel'
    let type_eiffel.kinds     = [
        \ {'short' : 'c', 'long' : 'classes',  'fold' : 0, 'stl' : 1},
        \ {'short' : 'f', 'long' : 'features', 'fold' : 0, 'stl' : 1}
    \ ]
    let type_eiffel.sro        = '.' " Not sure, is nesting even possible?
    let type_eiffel.kind2scope = {
        \ 'c' : 'class',
        \ 'f' : 'feature'
    \ }
    let type_eiffel.scope2kind = {
        \ 'class'   : 'c',
        \ 'feature' : 'f'
    \ }
    let s:known_types.eiffel = type_eiffel
    " Erlang {{{3
    let type_erlang = s:TypeInfo.New()
    let type_erlang.ctagstype = 'erlang'
    let type_erlang.kinds     = [
        \ {'short' : 'm', 'long' : 'modules',            'fold' : 0, 'stl' : 1},
        \ {'short' : 'd', 'long' : 'macro definitions',  'fold' : 0, 'stl' : 1},
        \ {'short' : 'f', 'long' : 'functions',          'fold' : 0, 'stl' : 1},
        \ {'short' : 'r', 'long' : 'record definitions', 'fold' : 0, 'stl' : 1}
    \ ]
    let type_erlang.sro        = '.' " Not sure, is nesting even possible?
    let type_erlang.kind2scope = {
        \ 'm' : 'module'
    \ }
    let type_erlang.scope2kind = {
        \ 'module' : 'm'
    \ }
    let s:known_types.erlang = type_erlang
    " Flex {{{3
    " Vim doesn't support Flex out of the box, this is based on rough
    " guesses and probably requires
    " http://www.vim.org/scripts/script.php?script_id=2909
    " Improvements welcome!
    let type_as = s:TypeInfo.New()
    let type_as.ctagstype = 'flex'
    let type_as.kinds     = [
        \ {'short' : 'v', 'long' : 'global variables', 'fold' : 0, 'stl' : 0},
        \ {'short' : 'c', 'long' : 'classes',          'fold' : 0, 'stl' : 1},
        \ {'short' : 'm', 'long' : 'methods',          'fold' : 0, 'stl' : 1},
        \ {'short' : 'p', 'long' : 'properties',       'fold' : 0, 'stl' : 1},
        \ {'short' : 'f', 'long' : 'functions',        'fold' : 0, 'stl' : 1},
        \ {'short' : 'x', 'long' : 'mxtags',           'fold' : 0, 'stl' : 0}
    \ ]
    let type_as.sro        = '.'
    let type_as.kind2scope = {
        \ 'c' : 'class'
    \ }
    let type_as.scope2kind = {
        \ 'class' : 'c'
    \ }
    let s:known_types.mxml = type_as
    let s:known_types.actionscript = type_as
    " Fortran {{{3
    let type_fortran = s:TypeInfo.New()
    let type_fortran.ctagstype = 'fortran'
    let type_fortran.kinds     = [
        \ {'short' : 'm', 'long' : 'modules',    'fold' : 0, 'stl' : 1},
        \ {'short' : 'p', 'long' : 'programs',   'fold' : 0, 'stl' : 1},
        \ {'short' : 'k', 'long' : 'components', 'fold' : 0, 'stl' : 1},
        \ {'short' : 't', 'long' : 'derived types and structures', 'fold' : 0,
         \ 'stl' : 1},
        \ {'short' : 'c', 'long' : 'common blocks', 'fold' : 0, 'stl' : 1},
        \ {'short' : 'b', 'long' : 'block data',    'fold' : 0, 'stl' : 0},
        \ {'short' : 'e', 'long' : 'entry points',  'fold' : 0, 'stl' : 1},
        \ {'short' : 'f', 'long' : 'functions',     'fold' : 0, 'stl' : 1},
        \ {'short' : 's', 'long' : 'subroutines',   'fold' : 0, 'stl' : 1},
        \ {'short' : 'l', 'long' : 'labels',        'fold' : 0, 'stl' : 1},
        \ {'short' : 'n', 'long' : 'namelists',     'fold' : 0, 'stl' : 1},
        \ {'short' : 'v', 'long' : 'variables',     'fold' : 0, 'stl' : 0}
    \ ]
    let type_fortran.sro        = '.' " Not sure, is nesting even possible?
    let type_fortran.kind2scope = {
        \ 'm' : 'module',
        \ 'p' : 'program',
        \ 'f' : 'function',
        \ 's' : 'subroutine'
    \ }
    let type_fortran.scope2kind = {
        \ 'module'     : 'm',
        \ 'program'    : 'p',
        \ 'function'   : 'f',
        \ 'subroutine' : 's'
    \ }
    let s:known_types.fortran = type_fortran
    " HTML {{{3
    let type_html = s:TypeInfo.New()
    let type_html.ctagstype = 'html'
    if s:ctags_is_uctags
        let type_html.kinds = [
            \ {'short' : 'a', 'long' : 'named anchors', 'fold' : 0, 'stl' : 1},
            \ {'short' : 'h', 'long' : 'H1 headings',   'fold' : 0, 'stl' : 1},
            \ {'short' : 'i', 'long' : 'H2 headings',   'fold' : 0, 'stl' : 1},
            \ {'short' : 'j', 'long' : 'H3 headings',   'fold' : 0, 'stl' : 1},
        \ ]
    else
        let type_html.kinds = [
            \ {'short' : 'f', 'long' : 'JavaScript functions', 'fold' : 0, 'stl' : 1},
            \ {'short' : 'a', 'long' : 'named anchors',        'fold' : 0, 'stl' : 1}
        \ ]
    endif
    let s:known_types.html = type_html
    " Java {{{3
    let type_java = s:TypeInfo.New()
    let type_java.ctagstype = 'java'
    let type_java.kinds     = [
        \ {'short' : 'p', 'long' : 'packages',       'fold' : 1, 'stl' : 0},
        \ {'short' : 'f', 'long' : 'fields',         'fold' : 0, 'stl' : 0},
        \ {'short' : 'g', 'long' : 'enum types',     'fold' : 0, 'stl' : 1},
        \ {'short' : 'e', 'long' : 'enum constants', 'fold' : 0, 'stl' : 0},
        \ {'short' : 'i', 'long' : 'interfaces',     'fold' : 0, 'stl' : 1},
        \ {'short' : 'c', 'long' : 'classes',        'fold' : 0, 'stl' : 1},
        \ {'short' : 'm', 'long' : 'methods',        'fold' : 0, 'stl' : 1}
    \ ]
    let type_java.sro        = '.'
    let type_java.kind2scope = {
        \ 'g' : 'enum',
        \ 'i' : 'interface',
        \ 'c' : 'class'
    \ }
    let type_java.scope2kind = {
        \ 'enum'      : 'g',
        \ 'interface' : 'i',
        \ 'class'     : 'c'
    \ }
    let s:known_types.java = type_java
    " JavaScript {{{3
    " jsctags/doctorjs will be used if available.
    let type_javascript = s:TypeInfo.New()
    let type_javascript.ctagstype = 'javascript'
    let jsctags = s:CheckFTCtags('jsctags', 'javascript')
    if jsctags != ''
        let type_javascript.kinds = [
            \ {'short' : 'v', 'long' : 'variables', 'fold' : 0, 'stl' : 0},
            \ {'short' : 'f', 'long' : 'functions', 'fold' : 0, 'stl' : 1}
        \ ]
        let type_javascript.sro        = '.'
        let type_javascript.kind2scope = {
            \ 'v' : 'namespace',
            \ 'f' : 'namespace'
        \ }
        let type_javascript.scope2kind = {
            \ 'namespace' : 'v'
        \ }
        let type_javascript.ctagsbin   = jsctags
        let type_javascript.ctagsargs  = '-f -'
    else
        let type_javascript.kinds = [
            \ {'short': 'v', 'long': 'global variables', 'fold': 0, 'stl': 0},
            \ {'short': 'c', 'long': 'classes',          'fold': 0, 'stl': 1},
            \ {'short': 'p', 'long': 'properties',       'fold': 0, 'stl': 0},
            \ {'short': 'm', 'long': 'methods',          'fold': 0, 'stl': 1},
            \ {'short': 'f', 'long': 'functions',        'fold': 0, 'stl': 1},
        \ ]
        let type_javascript.sro        = '.'
        let type_javascript.kind2scope = {
            \ 'c' : 'class',
            \ 'f' : 'function',
            \ 'm' : 'method',
            \ 'p' : 'property',
        \ }
        let type_javascript.scope2kind = {
            \ 'class'    : 'c',
            \ 'function' : 'f',
        \ }
    endif
    let s:known_types.javascript = type_javascript
    " Lisp {{{3
    let type_lisp = s:TypeInfo.New()
    let type_lisp.ctagstype = 'lisp'
    let type_lisp.kinds     = [
        \ {'short' : 'f', 'long' : 'functions', 'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.lisp = type_lisp
    let s:known_types.clojure = type_lisp
    " Lua {{{3
    let type_lua = s:TypeInfo.New()
    let type_lua.ctagstype = 'lua'
    let type_lua.kinds     = [
        \ {'short' : 'f', 'long' : 'functions', 'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.lua = type_lua
    " Make {{{3
    let type_make = s:TypeInfo.New()
    let type_make.ctagstype = 'make'
    let type_make.kinds     = [
        \ {'short' : 'm', 'long' : 'macros', 'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.make = type_make
    " Matlab {{{3
    let type_matlab = s:TypeInfo.New()
    let type_matlab.ctagstype = 'matlab'
    let type_matlab.kinds     = [
        \ {'short' : 'f', 'long' : 'functions', 'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.matlab = type_matlab
    " Ocaml {{{3
    let type_ocaml = s:TypeInfo.New()
    let type_ocaml.ctagstype = 'ocaml'
    let type_ocaml.kinds     = [
        \ {'short' : 'M', 'long' : 'modules or functors', 'fold' : 0, 'stl' : 1},
        \ {'short' : 'v', 'long' : 'global variables',    'fold' : 0, 'stl' : 0},
        \ {'short' : 'c', 'long' : 'classes',             'fold' : 0, 'stl' : 1},
        \ {'short' : 'C', 'long' : 'constructors',        'fold' : 0, 'stl' : 1},
        \ {'short' : 'm', 'long' : 'methods',             'fold' : 0, 'stl' : 1},
        \ {'short' : 'e', 'long' : 'exceptions',          'fold' : 0, 'stl' : 1},
        \ {'short' : 't', 'long' : 'type names',          'fold' : 0, 'stl' : 1},
        \ {'short' : 'f', 'long' : 'functions',           'fold' : 0, 'stl' : 1},
        \ {'short' : 'r', 'long' : 'structure fields',    'fold' : 0, 'stl' : 0}
    \ ]
    let type_ocaml.sro        = '.' " Not sure, is nesting even possible?
    let type_ocaml.kind2scope = {
        \ 'M' : 'Module',
        \ 'c' : 'class',
        \ 't' : 'type'
    \ }
    let type_ocaml.scope2kind = {
        \ 'Module' : 'M',
        \ 'class'  : 'c',
        \ 'type'   : 't'
    \ }
    let s:known_types.ocaml = type_ocaml
    " Pascal {{{3
    let type_pascal = s:TypeInfo.New()
    let type_pascal.ctagstype = 'pascal'
    let type_pascal.kinds     = [
        \ {'short' : 'f', 'long' : 'functions',  'fold' : 0, 'stl' : 1},
        \ {'short' : 'p', 'long' : 'procedures', 'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.pascal = type_pascal
    " Perl {{{3
    let type_perl = s:TypeInfo.New()
    let type_perl.ctagstype = 'perl'
    let type_perl.kinds     = [
        \ {'short' : 'p', 'long' : 'packages',    'fold' : 1, 'stl' : 0},
        \ {'short' : 'c', 'long' : 'constants',   'fold' : 0, 'stl' : 0},
        \ {'short' : 'f', 'long' : 'formats',     'fold' : 0, 'stl' : 0},
        \ {'short' : 'l', 'long' : 'labels',      'fold' : 0, 'stl' : 1},
        \ {'short' : 's', 'long' : 'subroutines', 'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.perl = type_perl
    " PHP {{{3
    let type_php = s:TypeInfo.New()
    let type_php.ctagstype = 'php'
    let type_php.kinds     = [
        \ {'short' : 'i', 'long' : 'interfaces',           'fold' : 0, 'stl' : 1},
        \ {'short' : 'c', 'long' : 'classes',              'fold' : 0, 'stl' : 1},
        \ {'short' : 'd', 'long' : 'constant definitions', 'fold' : 0, 'stl' : 0},
        \ {'short' : 'f', 'long' : 'functions',            'fold' : 0, 'stl' : 1},
        \ {'short' : 'v', 'long' : 'variables',            'fold' : 0, 'stl' : 0},
        \ {'short' : 'j', 'long' : 'javascript functions', 'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.php = type_php
    " Python {{{3
    let type_python = s:TypeInfo.New()
    let type_python.ctagstype = 'python'
    let type_python.kinds     = [
        \ {'short' : 'i', 'long' : 'imports',   'fold' : 1, 'stl' : 0},
        \ {'short' : 'c', 'long' : 'classes',   'fold' : 0, 'stl' : 1},
        \ {'short' : 'f', 'long' : 'functions', 'fold' : 0, 'stl' : 1},
        \ {'short' : 'm', 'long' : 'members',   'fold' : 0, 'stl' : 1},
        \ {'short' : 'v', 'long' : 'variables', 'fold' : 0, 'stl' : 0}
    \ ]
    let type_python.sro        = '.'
    let type_python.kind2scope = {
        \ 'c' : 'class',
        \ 'f' : 'function',
        \ 'm' : 'function'
    \ }
    let type_python.scope2kind = {
        \ 'class'    : 'c',
        \ 'function' : 'f'
    \ }
    if s:ctags_is_uctags
        " Universal Ctags treats member functions differently from normal
        " functions
        let type_python.kind2scope.m = 'member'
        let type_python.scope2kind.member = 'm'
    endif
    let s:known_types.python = type_python
    let s:known_types.pyrex  = type_python
    let s:known_types.cython = type_python
    " REXX {{{3
    let type_rexx = s:TypeInfo.New()
    let type_rexx.ctagstype = 'rexx'
    let type_rexx.kinds     = [
        \ {'short' : 's', 'long' : 'subroutines', 'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.rexx = type_rexx
    " Ruby {{{3
    let type_ruby = s:TypeInfo.New()
    let type_ruby.ctagstype = 'ruby'
    let type_ruby.kinds     = [
        \ {'short' : 'm', 'long' : 'modules',           'fold' : 0, 'stl' : 1},
        \ {'short' : 'c', 'long' : 'classes',           'fold' : 0, 'stl' : 1},
        \ {'short' : 'f', 'long' : 'methods',           'fold' : 0, 'stl' : 1},
        \ {'short' : 'F', 'long' : 'singleton methods', 'fold' : 0, 'stl' : 1}
    \ ]
    let type_ruby.sro        = '.'
    let type_ruby.kind2scope = {
        \ 'c' : 'class',
        \ 'm' : 'class',
        \ 'f' : 'class'
    \ }
    let type_ruby.scope2kind = {
        \ 'class' : 'c'
    \ }
    let s:known_types.ruby = type_ruby
    " Scheme {{{3
    let type_scheme = s:TypeInfo.New()
    let type_scheme.ctagstype = 'scheme'
    let type_scheme.kinds     = [
        \ {'short' : 'f', 'long' : 'functions', 'fold' : 0, 'stl' : 1},
        \ {'short' : 's', 'long' : 'sets',      'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.scheme = type_scheme
    let s:known_types.racket = type_scheme
    " Shell script {{{3
    let type_sh = s:TypeInfo.New()
    let type_sh.ctagstype = 'sh'
    let type_sh.kinds     = [
        \ {'short' : 'f', 'long' : 'functions', 'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.sh = type_sh
    let s:known_types.csh = type_sh
    let s:known_types.zsh = type_sh
    " SLang {{{3
    let type_slang = s:TypeInfo.New()
    let type_slang.ctagstype = 'slang'
    let type_slang.kinds     = [
        \ {'short' : 'n', 'long' : 'namespaces', 'fold' : 0, 'stl' : 1},
        \ {'short' : 'f', 'long' : 'functions',  'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.slang = type_slang
    " SML {{{3
    let type_sml = s:TypeInfo.New()
    let type_sml.ctagstype = 'sml'
    let type_sml.kinds     = [
        \ {'short' : 'e', 'long' : 'exception declarations', 'fold' : 0, 'stl' : 0},
        \ {'short' : 'f', 'long' : 'function definitions',   'fold' : 0, 'stl' : 1},
        \ {'short' : 'c', 'long' : 'functor definitions',    'fold' : 0, 'stl' : 1},
        \ {'short' : 's', 'long' : 'signature declarations', 'fold' : 0, 'stl' : 0},
        \ {'short' : 'r', 'long' : 'structure declarations', 'fold' : 0, 'stl' : 0},
        \ {'short' : 't', 'long' : 'type definitions',       'fold' : 0, 'stl' : 1},
        \ {'short' : 'v', 'long' : 'value bindings',         'fold' : 0, 'stl' : 0}
    \ ]
    let s:known_types.sml = type_sml
    " SQL {{{3
    " The SQL ctags parser seems to be buggy for me, so this just uses the
    " normal kinds even though scopes should be available. Improvements
    " welcome!
    let type_sql = s:TypeInfo.New()
    let type_sql.ctagstype = 'sql'
    let type_sql.kinds     = [
        \ {'short' : 'P', 'long' : 'packages',               'fold' : 1, 'stl' : 1},
        \ {'short' : 'd', 'long' : 'prototypes',             'fold' : 0, 'stl' : 1},
        \ {'short' : 'c', 'long' : 'cursors',                'fold' : 0, 'stl' : 1},
        \ {'short' : 'f', 'long' : 'functions',              'fold' : 0, 'stl' : 1},
        \ {'short' : 'F', 'long' : 'record fields',          'fold' : 0, 'stl' : 1},
        \ {'short' : 'L', 'long' : 'block label',            'fold' : 0, 'stl' : 1},
        \ {'short' : 'p', 'long' : 'procedures',             'fold' : 0, 'stl' : 1},
        \ {'short' : 's', 'long' : 'subtypes',               'fold' : 0, 'stl' : 1},
        \ {'short' : 't', 'long' : 'tables',                 'fold' : 0, 'stl' : 1},
        \ {'short' : 'T', 'long' : 'triggers',               'fold' : 0, 'stl' : 1},
        \ {'short' : 'v', 'long' : 'variables',              'fold' : 0, 'stl' : 1},
        \ {'short' : 'i', 'long' : 'indexes',                'fold' : 0, 'stl' : 1},
        \ {'short' : 'e', 'long' : 'events',                 'fold' : 0, 'stl' : 1},
        \ {'short' : 'U', 'long' : 'publications',           'fold' : 0, 'stl' : 1},
        \ {'short' : 'R', 'long' : 'services',               'fold' : 0, 'stl' : 1},
        \ {'short' : 'D', 'long' : 'domains',                'fold' : 0, 'stl' : 1},
        \ {'short' : 'V', 'long' : 'views',                  'fold' : 0, 'stl' : 1},
        \ {'short' : 'n', 'long' : 'synonyms',               'fold' : 0, 'stl' : 1},
        \ {'short' : 'x', 'long' : 'MobiLink Table Scripts', 'fold' : 0, 'stl' : 1},
        \ {'short' : 'y', 'long' : 'MobiLink Conn Scripts',  'fold' : 0, 'stl' : 1},
        \ {'short' : 'z', 'long' : 'MobiLink Properties',    'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.sql = type_sql
    " Tcl {{{3
    let type_tcl = s:TypeInfo.New()
    let type_tcl.ctagstype = 'tcl'
    let type_tcl.kinds     = [
        \ {'short' : 'c', 'long' : 'classes',    'fold' : 0, 'stl' : 1},
        \ {'short' : 'm', 'long' : 'methods',    'fold' : 0, 'stl' : 1},
        \ {'short' : 'p', 'long' : 'procedures', 'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.tcl = type_tcl
    " LaTeX {{{3
    let type_tex = s:TypeInfo.New()
    let type_tex.ctagstype = 'tex'
    let type_tex.kinds     = [
        \ {'short' : 'i', 'long' : 'includes',       'fold' : 1, 'stl' : 0},
        \ {'short' : 'p', 'long' : 'parts',          'fold' : 0, 'stl' : 1},
        \ {'short' : 'c', 'long' : 'chapters',       'fold' : 0, 'stl' : 1},
        \ {'short' : 's', 'long' : 'sections',       'fold' : 0, 'stl' : 1},
        \ {'short' : 'u', 'long' : 'subsections',    'fold' : 0, 'stl' : 1},
        \ {'short' : 'b', 'long' : 'subsubsections', 'fold' : 0, 'stl' : 1},
        \ {'short' : 'P', 'long' : 'paragraphs',     'fold' : 0, 'stl' : 0},
        \ {'short' : 'G', 'long' : 'subparagraphs',  'fold' : 0, 'stl' : 0},
        \ {'short' : 'l', 'long' : 'labels',         'fold' : 0, 'stl' : 0}
    \ ]
    let type_tex.sro        = '""'
    let type_tex.kind2scope = {
        \ 'p' : 'part',
        \ 'c' : 'chapter',
        \ 's' : 'section',
        \ 'u' : 'subsection',
        \ 'b' : 'subsubsection'
    \ }
    let type_tex.scope2kind = {
        \ 'part'          : 'p',
        \ 'chapter'       : 'c',
        \ 'section'       : 's',
        \ 'subsection'    : 'u',
        \ 'subsubsection' : 'b'
    \ }
    let type_tex.sort = 0
    let s:known_types.tex = type_tex
    " Vala {{{3
    " Vala is supported by the ctags fork provided by Anjuta, so only add the
    " type if the fork is used to prevent error messages otherwise
    if has_key(s:ctags_types, 'vala') || executable('anjuta-tags')
        let type_vala = s:TypeInfo.New()
        let type_vala.ctagstype = 'vala'
        let type_vala.kinds     = [
            \ {'short' : 'e', 'long' : 'Enumerations',       'fold' : 0, 'stl' : 1},
            \ {'short' : 'v', 'long' : 'Enumeration values', 'fold' : 0, 'stl' : 0},
            \ {'short' : 's', 'long' : 'Structures',         'fold' : 0, 'stl' : 1},
            \ {'short' : 'i', 'long' : 'Interfaces',         'fold' : 0, 'stl' : 1},
            \ {'short' : 'd', 'long' : 'Delegates',          'fold' : 0, 'stl' : 1},
            \ {'short' : 'c', 'long' : 'Classes',            'fold' : 0, 'stl' : 1},
            \ {'short' : 'p', 'long' : 'Properties',         'fold' : 0, 'stl' : 0},
            \ {'short' : 'f', 'long' : 'Fields',             'fold' : 0, 'stl' : 0},
            \ {'short' : 'm', 'long' : 'Methods',            'fold' : 0, 'stl' : 1},
            \ {'short' : 'E', 'long' : 'Error domains',      'fold' : 0, 'stl' : 1},
            \ {'short' : 'r', 'long' : 'Error codes',        'fold' : 0, 'stl' : 1},
            \ {'short' : 'S', 'long' : 'Signals',            'fold' : 0, 'stl' : 1}
        \ ]
        let type_vala.sro = '.'
        " 'enum' doesn't seem to be used as a scope, but it can't hurt to have
        " it here
        let type_vala.kind2scope = {
            \ 's' : 'struct',
            \ 'i' : 'interface',
            \ 'c' : 'class',
            \ 'e' : 'enum'
        \ }
        let type_vala.scope2kind = {
            \ 'struct'    : 's',
            \ 'interface' : 'i',
            \ 'class'     : 'c',
            \ 'enum'      : 'e'
        \ }
        let s:known_types.vala = type_vala
    endif
    if !has_key(s:ctags_types, 'vala') && executable('anjuta-tags')
        let s:known_types.vala.ctagsbin = 'anjuta-tags'
    endif
    " Vera {{{3
    " Why are variables 'virtual'?
    let type_vera = s:TypeInfo.New()
    let type_vera.ctagstype = 'vera'
    let type_vera.kinds     = [
        \ {'short' : 'd', 'long' : 'macros',      'fold' : 1, 'stl' : 0},
        \ {'short' : 'g', 'long' : 'enums',       'fold' : 0, 'stl' : 1},
        \ {'short' : 'T', 'long' : 'typedefs',    'fold' : 0, 'stl' : 0},
        \ {'short' : 'c', 'long' : 'classes',     'fold' : 0, 'stl' : 1},
        \ {'short' : 'e', 'long' : 'enumerators', 'fold' : 0, 'stl' : 0},
        \ {'short' : 'm', 'long' : 'members',     'fold' : 0, 'stl' : 1},
        \ {'short' : 'f', 'long' : 'functions',   'fold' : 0, 'stl' : 1},
        \ {'short' : 't', 'long' : 'tasks',       'fold' : 0, 'stl' : 1},
        \ {'short' : 'v', 'long' : 'variables',   'fold' : 0, 'stl' : 0},
        \ {'short' : 'p', 'long' : 'programs',    'fold' : 0, 'stl' : 1}
    \ ]
    let type_vera.sro        = '.' " Nesting doesn't seem to be possible
    let type_vera.kind2scope = {
        \ 'g' : 'enum',
        \ 'c' : 'class',
        \ 'v' : 'virtual'
    \ }
    let type_vera.scope2kind = {
        \ 'enum'      : 'g',
        \ 'class'     : 'c',
        \ 'virtual'   : 'v'
    \ }
    let s:known_types.vera = type_vera
    " Verilog {{{3
    let type_verilog = s:TypeInfo.New()
    let type_verilog.ctagstype = 'verilog'
    let type_verilog.kinds     = [
        \ {'short' : 'c', 'long' : 'constants',           'fold' : 0, 'stl' : 0},
        \ {'short' : 'e', 'long' : 'events',              'fold' : 0, 'stl' : 1},
        \ {'short' : 'f', 'long' : 'functions',           'fold' : 0, 'stl' : 1},
        \ {'short' : 'm', 'long' : 'modules',             'fold' : 0, 'stl' : 1},
        \ {'short' : 'n', 'long' : 'net data types',      'fold' : 0, 'stl' : 1},
        \ {'short' : 'p', 'long' : 'ports',               'fold' : 0, 'stl' : 1},
        \ {'short' : 'r', 'long' : 'register data types', 'fold' : 0, 'stl' : 1},
        \ {'short' : 't', 'long' : 'tasks',               'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.verilog = type_verilog
    " VHDL {{{3
    " The VHDL ctags parser unfortunately doesn't generate proper scopes
    let type_vhdl = s:TypeInfo.New()
    let type_vhdl.ctagstype = 'vhdl'
    let type_vhdl.kinds     = [
        \ {'short' : 'P', 'long' : 'packages',   'fold' : 1, 'stl' : 0},
        \ {'short' : 'c', 'long' : 'constants',  'fold' : 0, 'stl' : 0},
        \ {'short' : 't', 'long' : 'types',      'fold' : 0, 'stl' : 1},
        \ {'short' : 'T', 'long' : 'subtypes',   'fold' : 0, 'stl' : 1},
        \ {'short' : 'r', 'long' : 'records',    'fold' : 0, 'stl' : 1},
        \ {'short' : 'e', 'long' : 'entities',   'fold' : 0, 'stl' : 1},
        \ {'short' : 'f', 'long' : 'functions',  'fold' : 0, 'stl' : 1},
        \ {'short' : 'p', 'long' : 'procedures', 'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.vhdl = type_vhdl
    " Vim {{{3
    let type_vim = s:TypeInfo.New()
    let type_vim.ctagstype = 'vim'
    let type_vim.kinds     = [
        \ {'short' : 'n', 'long' : 'vimball filenames',  'fold' : 0, 'stl' : 1},
        \ {'short' : 'v', 'long' : 'variables',          'fold' : 1, 'stl' : 0},
        \ {'short' : 'f', 'long' : 'functions',          'fold' : 0, 'stl' : 1},
        \ {'short' : 'a', 'long' : 'autocommand groups', 'fold' : 1, 'stl' : 1},
        \ {'short' : 'c', 'long' : 'commands',           'fold' : 0, 'stl' : 0},
        \ {'short' : 'm', 'long' : 'maps',               'fold' : 1, 'stl' : 0}
    \ ]
    let s:known_types.vim = type_vim
    " YACC {{{3
    let type_yacc = s:TypeInfo.New()
    let type_yacc.ctagstype = 'yacc'
    let type_yacc.kinds     = [
        \ {'short' : 'l', 'long' : 'labels', 'fold' : 0, 'stl' : 1}
    \ ]
    let s:known_types.yacc = type_yacc
    " }}}3

    for [type, typeinfo] in items(s:known_types)
        let typeinfo.ftype = type
    endfor

    for typeinfo in values(s:known_types)
        call typeinfo.createKinddict()
    endfor

    call s:LoadUserTypeDefs()

    " Add an 'unknown' kind to the types for pseudotags that we can't
    " determine the correct kind for since they don't have any children that
    " are not pseudotags and that therefore don't provide scope information
    for typeinfo in values(s:known_types)
        if has_key(typeinfo, 'kind2scope')
            let unknown_kind =
                \ {'short' : '?', 'long' : 'unknown',  'fold' : 0, 'stl' : 1}
            " Check for existence first since some types exist under more than
            " one name
            if index(typeinfo.kinds, unknown_kind) == -1
                call add(typeinfo.kinds, unknown_kind)
            endif
            let typeinfo.kind2scope['?'] = 'unknown'
        endif
    endfor

    let s:type_init_done = 1
endfunction

" s:LoadUserTypeDefs() {{{2
function! s:LoadUserTypeDefs(...) abort
    if a:0 > 0
        let type = a:1

        call s:debug("Initializing user type '" . type . "'")

        let defdict = {}
        let defdict[type] = g:tagbar_type_{type}
    else
        call s:debug('Initializing user types')

        let defdict = tagbar#getusertypes()
    endif

    let transformed = {}
    for [type, def] in items(defdict)
        let transformed[type] = s:TransformUserTypeDef(def)
        let transformed[type].ftype = type
    endfor

    for [key, value] in items(transformed)
        if !has_key(s:known_types, key) || get(value, 'replace', 0)
            let s:known_types[key] = s:TypeInfo.New(value)
        else
            call extend(s:known_types[key], value)
        endif
        call s:known_types[key].createKinddict()
    endfor
endfunction

" s:TransformUserTypeDef() {{{2
" Transform the user definitions into the internal format
function! s:TransformUserTypeDef(def) abort
    let newdef = copy(a:def)

    if has_key(a:def, 'kinds')
        let newdef.kinds = []
        let kinds = a:def.kinds
        for kind in kinds
            let kindlist = split(kind, ':')
            let kinddict = {'short' : kindlist[0], 'long' : kindlist[1]}
            let kinddict.fold = get(kindlist, 2, 0)
            let kinddict.stl  = get(kindlist, 3, 1)
            call add(newdef.kinds, kinddict)
        endfor
    endif

    " If the user only specified one of kind2scope and scope2kind then use it
    " to generate the respective other
    if has_key(a:def, 'kind2scope') && !has_key(a:def, 'scope2kind')
        let newdef.scope2kind = {}
        for [key, value] in items(a:def.kind2scope)
            let newdef.scope2kind[value] = key
        endfor
    elseif has_key(a:def, 'scope2kind') && !has_key(a:def, 'kind2scope')
        let newdef.kind2scope = {}
        for [key, value] in items(a:def.scope2kind)
            let newdef.kind2scope[value] = key
        endfor
    endif

    return newdef
endfunction

" s:RestoreSession() {{{2
" Properly restore Tagbar after a session got loaded
function! s:RestoreSession() abort
    call s:debug('Restoring session')

    let curfile = fnamemodify(bufname('%'), ':p')

    let tagbarwinnr = bufwinnr(s:TagbarBufName())
    if tagbarwinnr == -1
        " Tagbar wasn't open in the saved session, nothing to do
        return
    else
        let in_tagbar = 1
        if winnr() != tagbarwinnr
            call s:goto_win(tagbarwinnr)
            let in_tagbar = 0
        endif
    endif

    let s:last_autofocus = 0

    call s:Init(0)

    call s:InitWindow(g:tagbar_autoclose)

    call s:AutoUpdate(curfile, 0)

    if !in_tagbar
        call s:goto_win('p')
    endif
endfunction

" s:MapKeys() {{{2
function! s:MapKeys() abort
    call s:debug('Mapping keys')

    nnoremap <script> <silent> <buffer> <2-LeftMouse>
                                              \ :call <SID>JumpToTag(0)<CR>
    nnoremap <script> <silent> <buffer> <LeftRelease>
                                 \ <LeftRelease>:call <SID>CheckMouseClick()<CR>

    inoremap <script> <silent> <buffer> <2-LeftMouse>
                                              \ <C-o>:call <SID>JumpToTag(0)<CR>
    inoremap <script> <silent> <buffer> <LeftRelease>
                            \ <LeftRelease><C-o>:call <SID>CheckMouseClick()<CR>

    let maps = [
        \ ['jump',          'JumpToTag(0)'],
        \ ['preview',       'JumpToTag(1)'],
        \ ['previewwin',    'ShowInPreviewWin()'],
        \ ['nexttag',       'GotoNextToplevelTag(1)'],
        \ ['prevtag',       'GotoNextToplevelTag(-1)'],
        \ ['showproto',     'ShowPrototype(0)'],
        \ ['hidenonpublic', 'ToggleHideNonPublicTags()'],
        \
        \ ['openfold',      'OpenFold()'],
        \ ['closefold',     'CloseFold()'],
        \ ['togglefold',    'ToggleFold()'],
        \ ['openallfolds',  'SetFoldLevel(99, 1)'],
        \ ['closeallfolds', 'SetFoldLevel(0, 1)'],
        \ ['nextfold',      'GotoNextFold()'],
        \ ['prevfold',      'GotoPrevFold()'],
        \
        \ ['togglesort',            'ToggleSort()'],
        \ ['togglecaseinsensitive', 'ToggleCaseInsensitive()'],
        \ ['toggleautoclose',       'ToggleAutoclose()'],
        \ ['zoomwin',               'ZoomWindow()'],
        \ ['close',                 'CloseWindow()'],
        \ ['help',                  'ToggleHelp()'],
    \ ]

    let map_options = ' <script> <silent> <buffer> '
    if v:version > 703 || (v:version == 703 && has('patch1261'))
        let map_options .= ' <nowait> '
    endif

    for [map, func] in maps
        let def = get(g:, 'tagbar_map_' . map)
        if type(def) == type("")
            let keys = [def]
        else
            let keys = def
        endif
        for key in keys
            execute 'nnoremap' . map_options . key .
                        \ ' :call <SID>' . func . '<CR>'
        endfor
        unlet def
    endfor

    let b:tagbar_mapped_keys = 1
endfunction

" s:CreateAutocommands() {{{2
function! s:CreateAutocommands() abort
    call s:debug('Creating autocommands')

    augroup TagbarAutoCmds
        autocmd!

        if !g:tagbar_silent
            autocmd CursorHold __Tagbar__.* call s:ShowPrototype(1)
        endif
        autocmd WinEnter   __Tagbar__.* call s:SetStatusLine()
        autocmd WinLeave   __Tagbar__.* call s:SetStatusLine()

        if g:tagbar_autopreview
            autocmd CursorMoved __Tagbar__.* nested call s:ShowInPreviewWin()
        endif

        autocmd BufEnter * if expand('<amatch>') !~ '__Tagbar__.*' |
                         \     let s:last_alt_bufnr = bufnr('#') |
                         \ endif
        if exists('##QuitPre')
            autocmd QuitPre * let s:vim_quitting = 1
        endif
        autocmd WinEnter * nested call s:HandleOnlyWindow()
        autocmd WinEnter * if bufwinnr(s:TagbarBufName()) == -1 |
                         \     call s:ShrinkIfExpanded() |
                         \ endif

        autocmd BufWritePost *
                    \ call s:HandleBufWrite(fnamemodify(expand('<afile>'), ':p'))
        autocmd CursorHold,CursorHoldI * call s:do_delayed_update()
        " BufReadPost is needed for reloading the current buffer if the file
        " was changed by an external command; see commit 17d199f
        autocmd BufReadPost,BufEnter,CursorHold,FileType * call
                    \ s:AutoUpdate(fnamemodify(expand('<afile>'), ':p'), 0)
        autocmd BufDelete,BufWipeout *
                    \ nested call s:HandleBufDelete(expand('<afile>'), expand('<abuf>'))

        " Suspend Tagbar while grep commands are running, since we don't want
        " to process files that only get loaded temporarily to search them
        autocmd QuickFixCmdPre  *grep* let s:tagbar_qf_active = 1
        autocmd QuickFixCmdPost *grep* if exists('s:tagbar_qf_active') |
                                     \     unlet s:tagbar_qf_active |
                                     \ endif

        autocmd VimEnter * call s:CorrectFocusOnStartup()
    augroup END

    let s:autocommands_done = 1
endfunction

" s:CheckForExCtags() {{{2
" Test whether the ctags binary is actually Exuberant Ctags and not BSD ctags
" (or something else)
function! s:CheckForExCtags(silent) abort
    call s:debug('Checking for Exuberant Ctags')

    if !exists('g:tagbar_ctags_bin')
        let ctagsbins  = []
        let ctagsbins += ['ctags-exuberant'] " Debian
        let ctagsbins += ['exuberant-ctags']
        let ctagsbins += ['exctags'] " FreeBSD, NetBSD
        let ctagsbins += ['/usr/local/bin/ctags'] " Homebrew
        let ctagsbins += ['/opt/local/bin/ctags'] " Macports
        let ctagsbins += ['ectags'] " OpenBSD
        let ctagsbins += ['ctags']
        let ctagsbins += ['ctags.exe']
        let ctagsbins += ['tags']
        for ctags in ctagsbins
            if executable(ctags)
                let g:tagbar_ctags_bin = ctags
                break
            endif
        endfor
        if !exists('g:tagbar_ctags_bin')
            let errmsg = 'Tagbar: Exuberant ctags not found!'
            let infomsg = 'Please download Exuberant Ctags from' .
                        \ ' ctags.sourceforge.net and install it in a' .
                        \ ' directory in your $PATH or set g:tagbar_ctags_bin.'
            call s:CtagsErrMsg(errmsg, infomsg, a:silent)
            let s:checked_ctags = 2
            return 0
        endif
    else
        " reset 'wildignore' temporarily in case *.exe is included in it
        let wildignore_save = &wildignore
        set wildignore&

        let g:tagbar_ctags_bin = expand(g:tagbar_ctags_bin)

        let &wildignore = wildignore_save

        if !executable(g:tagbar_ctags_bin)
            let errmsg = "Tagbar: Exuberant ctags not found at " .
                       \ "'" . g:tagbar_ctags_bin . "'!"
            let infomsg = 'Please check your g:tagbar_ctags_bin setting.'
            call s:CtagsErrMsg(errmsg, infomsg, a:silent)
            let s:checked_ctags = 2
            return 0
        endif
    endif

    let ctags_cmd = s:EscapeCtagsCmd(g:tagbar_ctags_bin, '--version')
    if ctags_cmd == ''
        let s:checked_ctags = 2
        return 0
    endif

    let ctags_output = s:ExecuteCtags(ctags_cmd)

    call s:debug("Command output:\n" . ctags_output)
    call s:debug("Exit code: " . v:shell_error)

    if v:shell_error || ctags_output !~# '\(Exuberant\|Universal\) Ctags'
        let errmsg = 'Tagbar: Ctags doesn''t seem to be Exuberant Ctags!'
        let infomsg = 'BSD ctags will NOT WORK.' .
            \ ' Please download Exuberant Ctags from ctags.sourceforge.net' .
            \ ' and install it in a directory in your $PATH' .
            \ ' or set g:tagbar_ctags_bin.'
        call s:CtagsErrMsg(errmsg, infomsg, a:silent,
                         \ ctags_cmd, ctags_output, v:shell_error)
        let s:checked_ctags = 2
        return 0
    elseif !s:CheckExCtagsVersion(ctags_output)
        let errmsg = 'Tagbar: Exuberant Ctags is too old!'
        let infomsg = 'You need at least version 5.5 for Tagbar to work.' .
            \ ' Please download a newer version from ctags.sourceforge.net.'
        call s:CtagsErrMsg(errmsg, infomsg, a:silent, ctags_cmd, ctags_output)
        let s:checked_ctags = 2
        return 0
    else
        let s:checked_ctags = 1
        return 1
    endif
endfunction

" s:CtagsErrMsg() {{{2
function! s:CtagsErrMsg(errmsg, infomsg, silent, ...) abort
    call s:debug(a:errmsg)
    let ctags_cmd    = a:0 > 0 ? a:1 : ''
    let ctags_output = a:0 > 1 ? a:2 : ''

    let exit_code_set = a:0 > 2
    if exit_code_set
        let exit_code = a:3
    endif

    if !a:silent
        call s:warning(a:errmsg)
        echomsg a:infomsg

        if ctags_cmd == ''
            return
        endif

        echomsg 'Executed command: "' . ctags_cmd . '"'
        if ctags_output != ''
            echomsg 'Command output:'
            for line in split(ctags_output, '\n')
                echomsg line
            endfor
        else
            echomsg 'Command output is empty.'
        endif
        if exit_code_set
            echomsg 'Exit code: ' . exit_code
        endif
    endif
endfunction


" s:CheckExCtagsVersion() {{{2
function! s:CheckExCtagsVersion(output) abort
    call s:debug('Checking Exuberant Ctags version')

    if a:output =~ 'Universal Ctags'
        call s:debug("Found Universal Ctags, assuming compatibility")
        let s:ctags_is_uctags = 1
        return 1
    endif

    if a:output =~ 'Exuberant Ctags Development'
        call s:debug("Found development version, assuming compatibility")
        return 1
    endif

    let matchlist = matchlist(a:output, '\vExuberant Ctags (\d+)\.(\d+)')
    let major     = matchlist[1]
    let minor     = matchlist[2]

    call s:debug("Ctags version: major='" . major . "', minor='" . minor . "'")

    return major >= 6 || (major == 5 && minor >= 5)
endfunction

" s:CheckFTCtags() {{{2
function! s:CheckFTCtags(bin, ftype) abort
    if executable(a:bin)
        return a:bin
    endif

    if exists('g:tagbar_type_' . a:ftype)
        let userdef = g:tagbar_type_{a:ftype}
        if has_key(userdef, 'ctagsbin')
            return userdef.ctagsbin
        else
            return ''
        endif
    endif

    return ''
endfunction

" s:GetSupportedFiletypes() {{{2
function! s:GetSupportedFiletypes() abort
    call s:debug('Getting filetypes supported by Exuberant Ctags')

    let ctags_cmd = s:EscapeCtagsCmd(g:tagbar_ctags_bin, '--list-languages')
    if ctags_cmd == ''
        return
    endif

    let ctags_output = s:ExecuteCtags(ctags_cmd)

    if v:shell_error
        " this shouldn't happen as potential problems would have already been
        " caught by the previous ctags checking
        return
    endif

    let types = split(ctags_output, '\n\+')

    for type in types
        if match(type, '\[disabled\]') == -1
            let s:ctags_types[tolower(type)] = 1
        endif
    endfor

    let s:checked_ctags_types = 1
endfunction

" Prototypes {{{1
" Base tag {{{2
let s:BaseTag = {}

" s:BaseTag.New() {{{3
function! s:BaseTag.New(name) abort dict
    let newobj = copy(self)

    call newobj._init(a:name)

    return newobj
endfunction

" s:BaseTag._init() {{{3
function! s:BaseTag._init(name) abort dict
    let self.name          = a:name
    let self.fields        = {}
    let self.fields.line   = 0
    let self.fields.column = 0
    let self.prototype     = ''
    let self.path          = ''
    let self.fullpath      = a:name
    let self.depth         = 0
    let self.parent        = {}
    let self.tline         = -1
    let self.fileinfo      = {}
    let self.typeinfo      = {}
    let self._childlist    = []
    let self._childdict    = {}
endfunction

" s:BaseTag.isNormalTag() {{{3
function! s:BaseTag.isNormalTag() abort dict
    return 0
endfunction

" s:BaseTag.isPseudoTag() {{{3
function! s:BaseTag.isPseudoTag() abort dict
    return 0
endfunction

" s:BaseTag.isKindheader() {{{3
function! s:BaseTag.isKindheader() abort dict
    return 0
endfunction

" s:BaseTag.getPrototype() {{{3
function! s:BaseTag.getPrototype(short) abort dict
    return self.prototype
endfunction

" s:BaseTag._getPrefix() {{{3
function! s:BaseTag._getPrefix() abort dict
    let fileinfo = self.fileinfo

    if !empty(self._childlist)
        if fileinfo.tagfolds[self.fields.kind][self.fullpath]
            let prefix = s:icon_closed
        else
            let prefix = s:icon_open
        endif
    else
        let prefix = ' '
    endif
    " Visibility is called 'access' in the ctags output
    if g:tagbar_show_visibility
        if has_key(self.fields, 'access')
            let prefix .= get(s:visibility_symbols, self.fields.access, ' ')
        elseif has_key(self.fields, 'file')
            let prefix .= s:visibility_symbols.private
        else
            let prefix .= ' '
        endif
    endif

    return prefix
endfunction

" s:BaseTag.initFoldState() {{{3
function! s:BaseTag.initFoldState() abort dict
    let fileinfo = self.fileinfo

    if s:known_files.has(fileinfo.fpath) &&
     \ has_key(fileinfo, '_tagfolds_old') &&
     \ has_key(fileinfo._tagfolds_old[self.fields.kind], self.fullpath)
        " The file has been updated and the tag was there before, so copy its
        " old fold state
        let fileinfo.tagfolds[self.fields.kind][self.fullpath] =
                    \ fileinfo._tagfolds_old[self.fields.kind][self.fullpath]
    elseif self.depth >= fileinfo.foldlevel
        let fileinfo.tagfolds[self.fields.kind][self.fullpath] = 1
    else
        let fileinfo.tagfolds[self.fields.kind][self.fullpath] =
                    \ fileinfo.kindfolds[self.fields.kind]
    endif
endfunction

" s:BaseTag.getClosedParentTline() {{{3
function! s:BaseTag.getClosedParentTline() abort dict
    let tagline  = self.tline

    " Find the first closed parent, starting from the top of the hierarchy.
    let parents   = []
    let curparent = self.parent
    while !empty(curparent)
        call add(parents, curparent)
        let curparent = curparent.parent
    endwhile
    for parent in reverse(parents)
        if parent.isFolded()
            let tagline = parent.tline
            break
        endif
    endfor

    return tagline
endfunction

" s:BaseTag.isFoldable() {{{3
function! s:BaseTag.isFoldable() abort dict
    return !empty(self._childlist)
endfunction

" s:BaseTag.isFolded() {{{3
function! s:BaseTag.isFolded() abort dict
    return self.fileinfo.tagfolds[self.fields.kind][self.fullpath]
endfunction

" s:BaseTag.openFold() {{{3
function! s:BaseTag.openFold() abort dict
    if self.isFoldable()
        let self.fileinfo.tagfolds[self.fields.kind][self.fullpath] = 0
    endif
endfunction

" s:BaseTag.closeFold() {{{3
function! s:BaseTag.closeFold() abort dict
    let newline = line('.')

    if !empty(self.parent) && self.parent.isKindheader()
        " Tag is child of generic 'kind'
        call self.parent.closeFold()
        let newline = self.parent.tline
    elseif self.isFoldable() && !self.isFolded()
        " Tag is parent of a scope and is not folded
        let self.fileinfo.tagfolds[self.fields.kind][self.fullpath] = 1
        let newline = self.tline
    elseif !empty(self.parent)
        " Tag is normal child, so close parent
        let parent = self.parent
        let self.fileinfo.tagfolds[parent.fields.kind][parent.fullpath] = 1
        let newline = parent.tline
    endif

    return newline
endfunction

" s:BaseTag.setFolded() {{{3
function! s:BaseTag.setFolded(folded) abort dict
    let self.fileinfo.tagfolds[self.fields.kind][self.fullpath] = a:folded
endfunction

" s:BaseTag.openParents() {{{3
function! s:BaseTag.openParents() abort dict
    let parent = self.parent

    while !empty(parent)
        call parent.openFold()
        let parent = parent.parent
    endwhile
endfunction

" s:BaseTag.addChild() {{{3
function! s:BaseTag.addChild(tag) abort dict
    call add(self._childlist, a:tag)

    if has_key(self._childdict, a:tag.name)
        call add(self._childdict[a:tag.name], a:tag)
    else
        let self._childdict[a:tag.name] = [a:tag]
    endif
endfunction

" s:BaseTag.getChildren() {{{3
function! s:BaseTag.getChildren() dict abort
    return self._childlist
endfunction

" s:BaseTag.getChildrenByName() {{{3
function! s:BaseTag.getChildrenByName(tagname) dict abort
    return get(self._childdict, a:tagname, [])
endfunction

" s:BaseTag.removeChild() {{{3
function! s:BaseTag.removeChild(tag) dict abort
    let idx = index(self._childlist, a:tag)
    if idx >= 0
        call remove(self._childlist, idx)
    endif

    let namelist = get(self._childdict, a:tag.name, [])
    let idx = index(namelist, a:tag)
    if idx >= 0
        call remove(namelist, idx)
    endif
endfunction

" Normal tag {{{2
let s:NormalTag = copy(s:BaseTag)

" s:NormalTag.isNormalTag() {{{3
function! s:NormalTag.isNormalTag() abort dict
    return 1
endfunction

" s:NormalTag.strfmt() {{{3
function! s:NormalTag.strfmt() abort dict
    let typeinfo = self.typeinfo

    let suffix = get(self.fields, 'signature', '')
    if has_key(self.fields, 'type')
        let suffix .= ' : ' . self.fields.type
    elseif has_key(get(typeinfo, 'kind2scope', {}), self.fields.kind)
        let suffix .= ' : ' . typeinfo.kind2scope[self.fields.kind]
    endif

    return self._getPrefix() . self.name . suffix
endfunction

" s:NormalTag.str() {{{3
function! s:NormalTag.str(longsig, full) abort dict
    if a:full && self.path != ''
        let str = self.path . self.typeinfo.sro . self.name
    else
        let str = self.name
    endif

    if has_key(self.fields, 'signature')
        if a:longsig
            let str .= self.fields.signature
        else
            let str .= '()'
        endif
    endif

    return str
endfunction

" s:NormalTag.getPrototype() {{{3
function! s:NormalTag.getPrototype(short) abort dict
    if self.prototype != ''
        let prototype = self.prototype
    else
        let bufnr = self.fileinfo.bufnr

        if self.fields.line == 0 || !bufloaded(bufnr)
            " No linenumber available or buffer not loaded (probably due to
            " 'nohidden'), try the pattern instead
            return substitute(self.pattern, '^\\V\\^\\C\s*\(.*\)\\$$', '\1', '')
        endif

        let line = getbufline(bufnr, self.fields.line)[0]
        let list = split(line, '\zs')

        let start = index(list, '(')
        if start == -1
            return substitute(line, '^\s\+', '', '')
        endif

        let opening = count(list, '(', 0, start)
        let closing = count(list, ')', 0, start)
        if closing >= opening
            return substitute(line, '^\s\+', '', '')
        endif

        let balance = opening - closing

        let prototype = line
        let curlinenr = self.fields.line + 1
        while balance > 0
            let curline = getbufline(bufnr, curlinenr)[0]
            let curlist = split(curline, '\zs')
            let balance += count(curlist, '(')
            let balance -= count(curlist, ')')
            let prototype .= "\n" . curline
            let curlinenr += 1
        endwhile

        let self.prototype = prototype
    endif

    if a:short
        " join all lines and remove superfluous spaces
        let prototype = substitute(prototype, '^\s\+', '', '')
        let prototype = substitute(prototype, '\_s\+', ' ', 'g')
        let prototype = substitute(prototype, '(\s\+', '(', 'g')
        let prototype = substitute(prototype, '\s\+)', ')', 'g')
        " Avoid hit-enter prompts
        let maxlen = &columns - 12
        if len(prototype) > maxlen
            let prototype = prototype[:maxlen - 1 - 3]
            let prototype .= '...'
        endif
    endif

    return prototype
endfunction

" Pseudo tag {{{2
let s:PseudoTag = copy(s:BaseTag)

" s:PseudoTag.isPseudoTag() {{{3
function! s:PseudoTag.isPseudoTag() abort dict
    return 1
endfunction

" s:PseudoTag.strfmt() {{{3
function! s:PseudoTag.strfmt() abort dict
    let typeinfo = self.typeinfo

    let suffix = get(self.fields, 'signature', '')
    if has_key(typeinfo.kind2scope, self.fields.kind)
        let suffix .= ' : ' . typeinfo.kind2scope[self.fields.kind]
    endif

    return self._getPrefix() . self.name . '*' . suffix
endfunction

" Kind header {{{2
let s:KindheaderTag = copy(s:BaseTag)

" s:KindheaderTag.isKindheader() {{{3
function! s:KindheaderTag.isKindheader() abort dict
    return 1
endfunction

" s:KindheaderTag.getPrototype() {{{3
function! s:KindheaderTag.getPrototype(short) abort dict
    return self.name . ': ' .
         \ self.numtags . ' ' . (self.numtags > 1 ? 'tags' : 'tag')
endfunction

" s:KindheaderTag.isFoldable() {{{3
function! s:KindheaderTag.isFoldable() abort dict
    return 1
endfunction

" s:KindheaderTag.isFolded() {{{3
function! s:KindheaderTag.isFolded() abort dict
    return self.fileinfo.kindfolds[self.short]
endfunction

" s:KindheaderTag.openFold() {{{3
function! s:KindheaderTag.openFold() abort dict
    let self.fileinfo.kindfolds[self.short] = 0
endfunction

" s:KindheaderTag.closeFold() {{{3
function! s:KindheaderTag.closeFold() abort dict
    let self.fileinfo.kindfolds[self.short] = 1
    return line('.')
endfunction

" s:KindheaderTag.toggleFold() {{{3
function! s:KindheaderTag.toggleFold() abort dict
    let fileinfo = s:TagbarState().getCurrent(0)

    let fileinfo.kindfolds[self.short] = !fileinfo.kindfolds[self.short]
endfunction

" Type info {{{2
let s:TypeInfo = {}

" s:TypeInfo.New() {{{3
function! s:TypeInfo.New(...) abort dict
    let newobj = copy(self)

    let newobj.kinddict = {}

    if a:0 > 0
        call extend(newobj, a:1)
    endif

    return newobj
endfunction

" s:TypeInfo.getKind() {{{3
function! s:TypeInfo.getKind(kind) abort dict
    let idx = self.kinddict[a:kind]
    return self.kinds[idx]
endfunction

" s:TypeInfo.createKinddict() {{{3
" Create a dictionary of the kind order for fast access in sorting functions
function! s:TypeInfo.createKinddict() abort dict
    let i = 0
    for kind in self.kinds
        let self.kinddict[kind.short] = i
        let i += 1
    endfor
    let self.kinddict['?'] = i
endfunction

" File info {{{2
let s:FileInfo = {}

" s:FileInfo.New() {{{3
function! s:FileInfo.New(fname, ftype, typeinfo) abort dict
    let newobj = copy(self)

    " The complete file path
    let newobj.fpath = a:fname

    let newobj.bufnr = bufnr(a:fname)

    " File modification time
    let newobj.mtime = getftime(a:fname)

    " The vim file type
    let newobj.ftype = a:ftype

    " List of the tags that are present in the file, sorted according to the
    " value of 'g:tagbar_sort'
    let newobj._taglist = []
    let newobj._tagdict = {}

    " Dictionary of the tags, indexed by line number in the file
    let newobj.fline = {}

    " Dictionary of the tags, indexed by line number in the tagbar
    let newobj.tline = {}

    " Dictionary of the folding state of 'kind's, indexed by short name
    let newobj.kindfolds = {}
    let newobj.typeinfo = a:typeinfo
    " copy the default fold state from the type info
    for kind in a:typeinfo.kinds
        let newobj.kindfolds[kind.short] =
                    \ g:tagbar_foldlevel == 0 ? 1 : kind.fold
    endfor

    " Dictionary of dictionaries of the folding state of individual tags,
    " indexed by kind and full path
    let newobj.tagfolds = {}
    for kind in a:typeinfo.kinds
        let newobj.tagfolds[kind.short] = {}
    endfor

    " The current foldlevel of the file
    let newobj.foldlevel = g:tagbar_foldlevel

    return newobj
endfunction

" s:FileInfo.addTag() {{{3
function! s:FileInfo.addTag(tag) abort dict
    call add(self._taglist, a:tag)

    if has_key(self._tagdict, a:tag.name)
        call add(self._tagdict[a:tag.name], a:tag)
    else
        let self._tagdict[a:tag.name] = [a:tag]
    endif
endfunction

" s:FileInfo.getTags() {{{3
function! s:FileInfo.getTags() dict abort
    return self._taglist
endfunction

" s:FileInfo.getTagsByName() {{{3
function! s:FileInfo.getTagsByName(tagname) dict abort
    return get(self._tagdict, a:tagname, [])
endfunction

" s:FileInfo.removeTag() {{{3
function! s:FileInfo.removeTag(tag) dict abort
    let idx = index(self._taglist, a:tag)
    if idx >= 0
        call remove(self._taglist, idx)
    endif

    let namelist = get(self._tagdict, a:tag.name, [])
    let idx = index(namelist, a:tag)
    if idx >= 0
        call remove(namelist, idx)
    endif
endfunction

" s:FileInfo.reset() {{{3
" Reset stuff that gets regenerated while processing a file and save the old
" tag folds
function! s:FileInfo.reset() abort dict
    let self.mtime = getftime(self.fpath)
    let self._taglist = []
    let self._tagdict = {}
    let self.fline = {}
    let self.tline = {}

    let self._tagfolds_old = self.tagfolds
    let self.tagfolds = {}

    for kind in self.typeinfo.kinds
        let self.tagfolds[kind.short] = {}
    endfor
endfunction

" s:FileInfo.clearOldFolds() {{{3
function! s:FileInfo.clearOldFolds() abort dict
    if exists('self._tagfolds_old')
        unlet self._tagfolds_old
    endif
endfunction

" s:FileInfo.sortTags() {{{3
function! s:FileInfo.sortTags() abort dict
    if get(s:compare_typeinfo, 'sort', g:tagbar_sort)
        call s:SortTags(self._taglist, 's:CompareByKind')
    else
        call s:SortTags(self._taglist, 's:CompareByLine')
    endif
endfunction

" s:FileInfo.openKindFold() {{{3
function! s:FileInfo.openKindFold(kind) abort dict
    let self.kindfolds[a:kind.short] = 0
endfunction

" s:FileInfo.closeKindFold() {{{3
function! s:FileInfo.closeKindFold(kind) abort dict
    let self.kindfolds[a:kind.short] = 1
endfunction

" Per-tagbar instance state prototype {{{2
let s:state = {
    \ '_current' : {},
    \ '_paused'  : {},
\ }

" s:state.New() {{{3
function! s:state.New() abort dict
    return deepcopy(self)
endfunction

" s:state.getCurrent() {{{3
function! s:state.getCurrent(forcecurrent) abort dict
    if !s:paused || a:forcecurrent
        return self._current
    else
        return self._paused
    endif
endfunction

" s:state.setCurrent() {{{3
function! s:state.setCurrent(fileinfo) abort dict
    let self._current = a:fileinfo
endfunction

" s:state.setPaused() {{{3
function! s:state.setPaused() abort dict
    let self._paused = self._current
endfunction

" Known files {{{2
let s:known_files = {
    \ '_files'   : {}
\ }

" s:known_files.get() {{{3
function! s:known_files.get(fname) abort dict
    return get(self._files, a:fname, {})
endfunction

" s:known_files.put() {{{3
" Optional second argument is the filename
function! s:known_files.put(fileinfo, ...) abort dict
    if a:0 == 1
        let self._files[a:1] = a:fileinfo
    else
        let fname = a:fileinfo.fpath
        let self._files[fname] = a:fileinfo
    endif
endfunction

" s:known_files.has() {{{3
function! s:known_files.has(fname) abort dict
    return has_key(self._files, a:fname)
endfunction

" s:known_files.rm() {{{3
function! s:known_files.rm(fname) abort dict
    if s:known_files.has(a:fname)
        call s:debug('Removing fileinfo for [' . a:fname . ']')
        call remove(self._files, a:fname)
    endif
endfunction

" Window management {{{1
" s:ToggleWindow() {{{2
function! s:ToggleWindow(flags) abort
    call s:debug('ToggleWindow called')

    let tagbarwinnr = bufwinnr(s:TagbarBufName())
    if tagbarwinnr != -1
        call s:CloseWindow()
        return
    endif

    call s:OpenWindow(a:flags)

    call s:debug('ToggleWindow finished')
endfunction

" s:OpenWindow() {{{2
function! s:OpenWindow(flags) abort
    call s:debug("OpenWindow called with flags: '" . a:flags . "'")

    let autofocus = a:flags =~# 'f'
    let jump      = a:flags =~# 'j'
    let autoclose = a:flags =~# 'c'

    let curfile = fnamemodify(bufname('%'), ':p')
    let curline = line('.')

    " If the tagbar window is already open check jump flag
    " Also set the autoclose flag if requested
    let tagbarwinnr = bufwinnr(s:TagbarBufName())
    if tagbarwinnr != -1
        if winnr() != tagbarwinnr && jump
            call s:goto_win(tagbarwinnr)
            call s:HighlightTag(g:tagbar_autoshowtag != 2, 1, curline)
        endif
        call s:debug("OpenWindow finished, Tagbar already open")
        return
    endif

    " Use the window ID if the functionality exists, this is more reliable
    " since the window number can change due to the Tagbar window opening
    if exists('*win_getid')
        let prevwinid = win_getid()
        if winnr('$') > 1
            call s:goto_win('p', 1)
            let pprevwinid = win_getid()
            call s:goto_win('p', 1)
        endif
    else
        let prevwinnr = winnr()
        if winnr('$') > 1
            call s:goto_win('p', 1)
            let pprevwinnr = winnr()
            call s:goto_win('p', 1)
        endif
    endif

    " This is only needed for the CorrectFocusOnStartup() function
    let s:last_autofocus = autofocus

    if !s:Init(0)
        return 0
    endif

    " Expand the Vim window to accomodate for the Tagbar window if requested
    " and save the window positions to be able to restore them later.
    if g:tagbar_expand >= 1 && !s:window_expanded &&
     \ (has('gui_running') || g:tagbar_expand == 2)
        let s:window_pos.pre.x = getwinposx()
        let s:window_pos.pre.y = getwinposy()
        let &columns += g:tagbar_width + 1
        let s:window_pos.post.x = getwinposx()
        let s:window_pos.post.y = getwinposy()
        let s:window_expanded = 1
    endif

    let s:window_opening = 1
    if g:tagbar_vertical == 0
        let mode = 'vertical '
        let openpos = g:tagbar_left ? 'topleft ' : 'botright '
        let width = g:tagbar_width
    else
        let mode = ''
        let openpos = g:tagbar_left ? 'leftabove ' : 'rightbelow '
        let width = g:tagbar_vertical
    endif
    exe 'silent keepalt ' . openpos . mode . width . 'split ' . s:TagbarBufName()
    exe 'silent ' . mode . 'resize ' . width
    unlet s:window_opening

    call s:InitWindow(autoclose)

    " If the current file exists, but is empty, it means that it had a
    " processing error before opening the window, most likely due to a call to
    " currenttag() in the statusline. Remove the entry so an error message
    " will be shown if the processing still fails.
    if empty(s:known_files.get(curfile))
        call s:known_files.rm(curfile)
    endif

    call s:AutoUpdate(curfile, 0)
    call s:HighlightTag(g:tagbar_autoshowtag != 2, 1, curline)

    if !(g:tagbar_autoclose || autofocus || g:tagbar_autofocus)
        if exists('*win_getid')
            if exists('pprevwinid')
                noautocmd call win_gotoid(pprevwinid)
            endif
            call win_gotoid(prevwinid)
        else
            " If the Tagbar winnr is identical to one of the saved values
            " then that means that the window numbers have changed.
            " Just jump back to the previous window since we won't be able to
            " restore the window history.
            if winnr() == prevwinnr
             \ || (exists('pprevwinnr') && winnr() == pprevwinnr)
                call s:goto_win('p')
            else
                if exists('pprevwinnr')
                    call s:goto_win(pprevwinnr, 1)
                endif
                call s:goto_win(prevwinnr)
            endif
        endif
    endif

    call s:debug('OpenWindow finished')
endfunction

" s:InitWindow() {{{2
function! s:InitWindow(autoclose) abort
    call s:debug('InitWindow called with autoclose: ' . a:autoclose)

    " Buffer-local options

    setlocal filetype=tagbar

    setlocal noreadonly " in case the "view" mode is used
    setlocal buftype=nofile
    setlocal bufhidden=hide
    setlocal noswapfile
    setlocal nobuflisted
    setlocal nomodifiable
    setlocal textwidth=0

    if has('balloon_eval')
        setlocal balloonexpr=TagbarBalloonExpr()
        set ballooneval
    endif


    " Window-local options

    setlocal nolist
    setlocal nowrap
    setlocal winfixwidth
    setlocal nospell

    if g:tagbar_show_linenumbers == 0
        setlocal nonumber
        if exists('+relativenumber')
            setlocal norelativenumber
        endif
    elseif g:tagbar_show_linenumbers == 1
        setlocal number
    elseif g:tagbar_show_linenumbers == 2
        setlocal relativenumber
    else
        set number<
        if exists('+relativenumber')
            set relativenumber<
        endif
    endif

    setlocal nofoldenable
    setlocal foldcolumn=0
    " Reset fold settings in case a plugin set them globally to something
    " expensive. Apparently 'foldexpr' gets executed even if 'foldenable' is
    " off, and then for every appended line (like with :put).
    setlocal foldmethod&
    setlocal foldexpr&


    let w:autoclose = a:autoclose

    call s:SetStatusLine()

    let s:new_window = 1

    let cpoptions_save = &cpoptions
    set cpoptions&vim

    if !exists('b:tagbar_mapped_keys')
        call s:MapKeys()
    endif

    let &cpoptions = cpoptions_save

    if g:tagbar_expand
        let s:expand_bufnr = bufnr('%')
    endif

    call s:debug('InitWindow finished')
endfunction

" s:CloseWindow() {{{2
function! s:CloseWindow() abort
    call s:debug('CloseWindow called')

    let tagbarwinnr = bufwinnr(s:TagbarBufName())
    if tagbarwinnr == -1
        return
    endif

    " Close the preview window if it was opened by us
    if s:pwin_by_tagbar
        pclose
        let tagbarwinnr = bufwinnr(s:TagbarBufName())
    endif

    if winnr() == tagbarwinnr
        if winbufnr(2) != -1
            " Other windows are open, only close the tagbar one

            let curfile = s:TagbarState().getCurrent(0)

            close

            " Try to jump to the correct window after closing
            call s:goto_win('p')

            if !empty(curfile)
                let filebufnr = bufnr(curfile.fpath)

                if bufnr('%') != filebufnr
                    let filewinnr = bufwinnr(filebufnr)
                    if filewinnr != -1
                        call s:goto_win(filewinnr)
                    endif
                endif
            endif
        endif
    else
        " Go to the tagbar window, close it and then come back to the original
        " window. Save a win-local variable in the original window so we can
        " jump back to it even if the window number changed.
        call s:mark_window()
        call s:goto_win(tagbarwinnr)
        close

        call s:goto_markedwin()
    endif

    call s:ShrinkIfExpanded()

    " The window sizes may have changed due to the shrinking happening after
    " the window closing, so equalize them again.
    if &equalalways
        wincmd =
    endif

    if s:autocommands_done && !s:statusline_in_use
        autocmd! TagbarAutoCmds
        let s:autocommands_done = 0
    endif

    call s:debug('CloseWindow finished')
endfunction

" s:ShrinkIfExpanded() {{{2
" If the Vim window has been expanded, and Tagbar is not open in any other
" tabpages, shrink the window again
function! s:ShrinkIfExpanded() abort
    if !s:window_expanded || &filetype == 'tagbar' || s:expand_bufnr == -1
        return
    endif

    let tablist = []
    for i in range(tabpagenr('$'))
        call extend(tablist, tabpagebuflist(i + 1))
    endfor

    if index(tablist, s:expand_bufnr) == -1
        let &columns -= g:tagbar_width + 1
        let s:window_expanded = 0
        let s:expand_bufnr = -1
        " Only restore window position if it is available and if the
        " window hasn't been moved manually after the expanding
        if getwinposx() != -1 &&
         \ getwinposx() == s:window_pos.post.x &&
         \ getwinposy() == s:window_pos.post.y
           execute 'winpos ' . s:window_pos.pre.x .
                       \ ' ' . s:window_pos.pre.y
        endif
    endif
endfunction

" s:ZoomWindow() {{{2
function! s:ZoomWindow() abort
    if s:is_maximized
        execute 'vertical resize ' . g:tagbar_width
        execute s:winrestcmd
        let s:is_maximized = 0
    else
        let s:winrestcmd = winrestcmd()
        if g:tagbar_zoomwidth == 1
            vertical resize
        elseif g:tagbar_zoomwidth == 0
            let func = exists('*strdisplaywidth') ? 'strdisplaywidth' : 'strlen'
            let maxline = max(map(getline(line('w0'), line('w$')),
                                \ func . '(v:val)'))
            execute 'vertical resize ' . maxline
        elseif g:tagbar_zoomwidth > 1
            execute 'vertical resize ' . g:tagbar_zoomwidth
        endif
        let s:is_maximized = 1
    endif
endfunction

" s:CorrectFocusOnStartup() {{{2
" For whatever reason the focus will be on the Tagbar window if
" tagbar#autoopen is used with a FileType autocommand on startup and
" g:tagbar_left is set. This should work around it by jumping to the window of
" the current file after startup.
function! s:CorrectFocusOnStartup() abort
    if bufwinnr(s:TagbarBufName()) != -1 && !g:tagbar_autofocus && !s:last_autofocus
        let curfile = s:TagbarState().getCurrent(1)
        if !empty(curfile) && curfile.fpath != fnamemodify(bufname('%'), ':p')
            let winnr = bufwinnr(curfile.fpath)
            if winnr != -1
                call s:goto_win(winnr)
            endif
        endif
    endif
endfunction

" Tag processing {{{1
" s:ProcessFile() {{{2
" Execute ctags and put the information into a 'FileInfo' object
function! s:ProcessFile(fname, ftype) abort
    call s:debug('ProcessFile called [' . a:fname . ']')

    if !s:IsValidFile(a:fname, a:ftype)
        call s:debug('Not a valid file, returning')
        return
    endif

    let typeinfo = s:known_types[a:ftype]

    " If the file has only been updated preserve the fold states, otherwise
    " create a new entry
    if s:known_files.has(a:fname) && !empty(s:known_files.get(a:fname)) &&
     \ s:known_files.get(a:fname).ftype == a:ftype
        let fileinfo = s:known_files.get(a:fname)
        let typeinfo = fileinfo.typeinfo
        call fileinfo.reset()
    else
        if exists('#TagbarProjects#User')
            execute 'doautocmd <nomodeline> TagbarProjects User ' . a:fname
            if exists('b:tagbar_type')
                let typeinfo = extend(copy(typeinfo),
                                    \ s:TransformUserTypeDef(b:tagbar_type))
                call typeinfo.createKinddict()
            endif
        endif
        let fileinfo = s:FileInfo.New(a:fname, a:ftype, typeinfo)
    endif

    call s:debug('typeinfo for file to process: ' . string(typeinfo))

    " Use a temporary files for ctags processing instead of the original one.
    " This allows using Tagbar for files accessed with netrw, and also doesn't
    " slow down Tagbar for files that sit on slow network drives.
    let tempfile = tempname()
    let ext = fnamemodify(fileinfo.fpath, ':e')
    if ext != ''
        let tempfile .= '.' . ext
    endif

    call writefile(getbufline(fileinfo.bufnr, 1, '$'), tempfile)
    let fileinfo.mtime = getftime(tempfile)

    let ctags_output = s:ExecuteCtagsOnFile(tempfile, a:fname, typeinfo)

    call delete(tempfile)

    if ctags_output == -1
        call s:debug('Ctags error when processing file')
        " Put an empty entry into known_files so the error message is only
        " shown once
        call s:known_files.put({}, a:fname)
        return
    elseif ctags_output == ''
        call s:debug('Ctags output empty')
        " No need to go through the tag processing if there are no tags, and
        " preserving the old fold state isn't necessary either
        call s:known_files.put(s:FileInfo.New(a:fname, a:ftype,
                                            \ s:known_types[a:ftype]), a:fname)
        return
    endif

    call s:debug('Filetype tag kinds: ' . string(keys(typeinfo.kinddict)))

    " Parse the ctags output lines
    call s:debug('Parsing ctags output')
    let rawtaglist = split(ctags_output, '\n\+')
    for line in rawtaglist
        " skip comments
        if line =~# '^!_TAG_'
            continue
        endif

        let parts = split(line, ';"')
        if len(parts) == 2 " Is a valid tag line
            call s:ParseTagline(parts[0], parts[1], typeinfo, fileinfo)
        endif
    endfor

    " Create a placeholder tag for the 'kind' header for folding purposes, but
    " only for non-scoped tags
    for kind in typeinfo.kinds
        if has_key(get(typeinfo, 'kind2scope', {}), kind.short)
            continue
        endif

        let curtags = filter(copy(fileinfo.getTags()),
                           \ 'v:val.fields.kind ==# kind.short && ' .
                           \ '!has_key(v:val, "scope")')
        call s:debug('Processing kind: ' . kind.short .
                   \ ', number of tags: ' . len(curtags))

        if empty(curtags)
            continue
        endif

        let kindtag          = s:KindheaderTag.New(kind.long)
        let kindtag.short    = kind.short
        let kindtag.numtags  = len(curtags)
        let kindtag.fileinfo = fileinfo

        for tag in curtags
            let tag.parent = kindtag
        endfor
    endfor

    " Clear old folding information from previous file version to prevent leaks
    call fileinfo.clearOldFolds()

    " Sort the tags
    let s:compare_typeinfo = typeinfo
    call fileinfo.sortTags()

    call s:known_files.put(fileinfo)
endfunction

" s:ExecuteCtagsOnFile() {{{2
function! s:ExecuteCtagsOnFile(fname, realfname, typeinfo) abort
    call s:debug('ExecuteCtagsOnFile called [' . a:fname . ']')

    if has_key(a:typeinfo, 'ctagsargs') && type(a:typeinfo.ctagsargs) == type('')
        " if ctagsargs is a string, prepend and append space separators
        let ctags_args = ' ' . a:typeinfo.ctagsargs . ' '
    elseif has_key(a:typeinfo, 'ctagsargs') && type(a:typeinfo.ctagsargs) == type([])
        let ctags_args = a:typeinfo.ctagsargs
    " otherwise ctagsargs is not defined or not defined as a valid type
    else
        "Prefer constructing ctags_args as a list rather than a string
        "See s:EscapeCtagsCmd() - It's a best practice to shellescape()
        "each arg separately because in special cases where space is
        "intended to be in an argument, spaces in a single ctag_args
        "string would be ambiguous. Is the space an argument separator
        "or to be included in the argument
        let ctags_args  = [ '-f',
                          \ '-',
                          \ '--format=2',
                          \ '--excmd=pattern',
                          \ '--fields=nksSaf',
                          \ '--extra=',
                          \ '--file-scope=yes',
                          \ '--sort=no',
                          \ '--append=no'
                          \ ]

        " Include extra type definitions
        if has_key(a:typeinfo, 'deffile')
            let ctags_args += ['--options=' . expand(a:typeinfo.deffile)]
        endif

        " Third-party programs may not necessarily make use of this
        if has_key(a:typeinfo, 'ctagstype')
            let ctags_type = a:typeinfo.ctagstype

            let ctags_kinds = ''
            for kind in a:typeinfo.kinds
                if kind.short !=# '?'
                    let ctags_kinds .= kind.short
                endif
            endfor

            let ctags_args += ['--language-force=' . ctags_type]
            let ctags_args += ['--' . ctags_type . '-kinds=' . ctags_kinds]
        endif
    endif

    if has_key(a:typeinfo, 'ctagsbin')
        " reset 'wildignore' temporarily in case *.exe is included in it
        let wildignore_save = &wildignore
        set wildignore&
        let ctags_bin = expand(a:typeinfo.ctagsbin)
        let &wildignore = wildignore_save
    else
        let ctags_bin = g:tagbar_ctags_bin
    endif

    let ctags_cmd = s:EscapeCtagsCmd(ctags_bin, ctags_args, a:fname)
    if ctags_cmd == ''
        return ''
    endif

    let ctags_output = s:ExecuteCtags(ctags_cmd)

    if v:shell_error || ctags_output =~ 'Warning: cannot open source file'
        call s:debug('Command output:')
        call s:debug(ctags_output)
        call s:debug('Exit code: ' . v:shell_error)
        " Only display an error message if the Tagbar window is open and we
        " haven't seen the error before.
        if bufwinnr(s:TagbarBufName()) != -1 &&
         \ (!s:known_files.has(a:realfname) ||
         \ !empty(s:known_files.get(a:realfname)))
            call s:warning('Tagbar: Could not execute ctags for ' . a:realfname . '!')
            echomsg 'Executed command: "' . ctags_cmd . '"'
            if !empty(ctags_output)
                echomsg 'Command output:'
                for line in split(ctags_output, '\n')
                    echomsg line
                endfor
            endif
            echomsg 'Exit code: ' . v:shell_error
        endif
        return -1
    endif

    call s:debug('Ctags executed successfully')
    if s:debug
        exe 'redir! > ' . s:debug_file . '.ctags_out'
        silent echon ctags_output
        redir END
    endif

    return ctags_output
endfunction

" s:ParseTagline() {{{2
" Structure of a tag line:
" tagname<TAB>filename<TAB>expattern;"fields
" fields: <TAB>name:value
" fields that are always present: kind, line
function! s:ParseTagline(part1, part2, typeinfo, fileinfo) abort
    let basic_info  = split(a:part1, '\t')

    let taginfo      = s:NormalTag.New(basic_info[0])
    let taginfo.file = basic_info[1]

    " the pattern can contain tabs and thus may have been split up, so join
    " the rest of the items together again
    let pattern = join(basic_info[2:], "\t")
    let start   = 2 " skip the slash and the ^
    let end     = strlen(pattern) - 1
    if pattern[end - 1] ==# '$'
        let end -= 1
        let dollar = '\$'
    else
        let dollar = ''
    endif
    let pattern         = strpart(pattern, start, end - start)
    let taginfo.pattern = '\V\^\C' . pattern . dollar

    " When splitting fields make sure not to create empty keys or values in
    " case a value illegally contains tabs
    let fields = split(a:part2, '^\t\|\t\ze\w\+:')
    if fields[0] !~# ':'
        let taginfo.fields.kind = remove(fields, 0)
    endif
    for field in fields
        " can't use split() since the value can contain ':'
        let delimit = stridx(field, ':')
        let key = strpart(field, 0, delimit)
        " Remove all tabs that may illegally be in the value
        let val = substitute(strpart(field, delimit + 1), '\t', '', 'g')
        " File-restricted scoping
        if key == "file"
            let taginfo.fields[key] = 'yes'
        endif
        if len(val) > 0
            if key == 'line' || key == 'column'
                let taginfo.fields[key] = str2nr(val)
            else
                let taginfo.fields[key] = val
            endif
        endif
    endfor
    " Needed for jsctags
    if has_key(taginfo.fields, 'lineno')
        let taginfo.fields.line = str2nr(taginfo.fields.lineno)
    endif
    " Do some sanity checking in case ctags reports invalid line numbers
    if taginfo.fields.line < 0
        let taginfo.fields.line = 0
    endif

    if !has_key(taginfo.fields, 'kind')
        call s:debug("Warning: No 'kind' field found for tag " . basic_info[0] . "!")
        if index(s:warnings.type, a:typeinfo.ftype) == -1
            call s:warning("No 'kind' field found for tag " . basic_info[0] . "!" .
                         \ " Please read the last section of ':help tagbar-extend'.")
            call add(s:warnings.type, a:typeinfo.ftype)
        endif
        return
    endif

    let taginfo.fileinfo = a:fileinfo
    let taginfo.typeinfo = a:typeinfo

    let a:fileinfo.fline[taginfo.fields.line] = taginfo

    " If this filetype doesn't have any scope information then we can stop
    " here after adding the tag to the list
    if !has_key(a:typeinfo, 'scope2kind')
        call a:fileinfo.addTag(taginfo)
        return
    endif


    " Make some information easier accessible
    for scope in keys(a:typeinfo.scope2kind)
        if has_key(taginfo.fields, scope)
            let taginfo.scope = scope
            let taginfo.path  = taginfo.fields[scope]

            let taginfo.fullpath = taginfo.path . a:typeinfo.sro .
                                 \ taginfo.name
            break
        endif
    endfor
    let pathlist = split(taginfo.path, '\V' . a:typeinfo.sro)
    let taginfo.depth = len(pathlist)

    " Needed for folding
    try
        call taginfo.initFoldState()
    catch /^Vim(\a\+):E716:/ " 'Key not present in Dictionary'
        " The tag has a 'kind' that doesn't exist in the type definition
        call s:debug('Warning: Unknown tag kind: ' . taginfo.fields.kind)
        if index(s:warnings.type, a:typeinfo.ftype) == -1
            call s:warning('Unknown tag kind encountered: ' .
                \ '"' . taginfo.fields.kind . '".' .
                \ ' Your ctags and Tagbar configurations are out of sync!' .
                \ ' Please read '':help tagbar-extend''.')
            call add(s:warnings.type, a:typeinfo.ftype)
        endif
        return
    endtry

    call s:add_tag_recursive({}, taginfo, pathlist)
endfunction

" s:add_tag_recursive() {{{2
" Add a tag recursively as a child of its parent, or if there is no parent, to
" the root tag list in the fileinfo object.
function! s:add_tag_recursive(parent, taginfo, pathlist) abort
    " If the pathlist is empty we are at the correct scope for the current tag
    if empty(a:pathlist)
        " If a child tag got processed before a parent tag then there will
        " be a pseudotag here as a placeholder. Copy the children over and
        " then replace the pseudotag with the real one.
        let pseudotags = []
        if empty(a:parent)
            let name_siblings = a:taginfo.fileinfo.getTagsByName(a:taginfo.name)
        else
            let name_siblings = a:parent.getChildrenByName(a:taginfo.name)
        endif

        for tag in name_siblings
            if (tag.fields.kind ==# '?'
              \ || tag.fields.kind ==# a:taginfo.fields.kind)
             \ && tag.isPseudoTag()
                call add(pseudotags, tag)
            endif
        endfor

        if len(pseudotags) == 1
            let pseudotag = pseudotags[0]
            for child in pseudotag.getChildren()
                call a:taginfo.addChild(child)
                let child.parent = a:taginfo
            endfor
            if empty(a:parent)
                call a:taginfo.fileinfo.removeTag(pseudotag)
            else
                call a:parent.removeChild(pseudotag)
            endif
        elseif len(pseudotags) > 1
            echoerr 'Tagbar: Found duplicate pseudotag; this should never happen!'
                  \ 'Please contact the script maintainer with an example.'
                  \ 'Pseudotag name:' pseudotag.name
        endif

        if empty(a:parent)
            call a:taginfo.fileinfo.addTag(a:taginfo)
        else
            call a:parent.addChild(a:taginfo)
            let a:taginfo.parent = a:parent
        endif
        return
    endif


    " There is still at least one more scope between the current one and the
    " one of the current tag, so we have to either find or create the
    " intermediate tags

    let grandparent = a:parent
    let parentname = remove(a:pathlist, 0)

    if empty(grandparent)
        let name_siblings = a:taginfo.fileinfo.getTagsByName(parentname)
    else
        let name_siblings = grandparent.getChildrenByName(parentname)
    endif
    if empty(a:pathlist)
        " If the current tag is a direct child of the parent we're looking for
        " then we can also filter the parents based on the scope information
        let parents = []
        for tag in name_siblings
            if tag.fields.kind ==# '?'
             \ || get(a:taginfo.typeinfo.kind2scope, tag.fields.kind, "") == a:taginfo.scope
                call add(parents, tag)
            endif
        endfor
    else
        let parents = name_siblings
    endif

    if empty(parents)
        " No parents found, so either the parent is a pseudotag or it hasn't
        " been processed yet. Create a pseudotag as a placeholder; if the
        " actual parent gets processed later it will get replaced.
        if empty(a:pathlist)
            let pseudokind = a:taginfo.typeinfo.scope2kind[a:taginfo.scope]
        else
            let pseudokind = '?'
        endif
        let parent = s:create_pseudotag(parentname, grandparent,
                    \ pseudokind, a:taginfo.typeinfo, a:taginfo.fileinfo)
        if empty(grandparent)
            call a:taginfo.fileinfo.addTag(parent)
        else
            call grandparent.addChild(parent)
        endif
    elseif len(parents) == 1
        let parent = parents[0]
    else
        " If there are multiple possible parents (c.f. issue #139, or tags
        " with the same name but a different kind) then we will pick the one
        " that is closest above the current tag as a heuristic.

        " Start at line 0 so that pseudotags get included
        let minline = 0
        for candidate in parents
            if candidate.fields.line <= a:taginfo.fields.line &&
             \ candidate.fields.line >= minline
                let parent = candidate
                let minline = candidate.fields.line
            endif
        endfor

        if !exists('parent')
            " If we still haven't found a parent it must be below the current
            " tag, so find the closest parent below the tag. This can happen
            " for example in Go.
            let maxline = line('$')
            for candidate in parents
                if candidate.fields.line >= a:taginfo.fields.line &&
                 \ candidate.fields.line <= maxline
                    let parent = candidate
                    let maxline = candidate.fields.line
                endif
            endfor
        endif
    endif

    " If the parent is a pseudotag it may have gotten created as an in-between
    " tag without proper information about its kind because all if its
    " children are also pseudotags, so it may be incorrect. If the current tag
    " is a direct child of a pseudotag then we can derive the correct kind, so
    " replace it if necessary.
    if parent.isPseudoTag() && empty(a:pathlist)
        let parentkind = a:taginfo.typeinfo.scope2kind[a:taginfo.scope]
        if parent.fields.kind ==# '?' || parentkind !=# parent.fields.kind
            let parent.fields.kind = parentkind
            call parent.initFoldState()
        endif
    endif

    call s:add_tag_recursive(parent, a:taginfo, a:pathlist)
endfunction

" s:create_pseudotag() {{{2
function! s:create_pseudotag(name, parent, kind, typeinfo, fileinfo) abort
    if !empty(a:parent)
        let curpath = a:parent.fullpath
        " If the kind is not present in the kind2scope dictionary, return an
        " empty scope. This can happen due to incorrect ctags output as in #397.
        let pscope  = get(a:typeinfo.kind2scope, a:parent.fields.kind, '')
    else
        let curpath = ''
        let pscope  = ''
    endif

    let pseudotag             = s:PseudoTag.New(a:name)
    let pseudotag.fields.kind = a:kind

    let parentscope = substitute(curpath, a:name . '$', '', '')
    let parentscope = substitute(parentscope,
                               \ '\V\^' . a:typeinfo.sro . '\$', '', '')

    if pscope != ''
        let pseudotag.fields[pscope] = parentscope
        let pseudotag.scope    = pscope
        let pseudotag.path     = parentscope
        let pseudotag.fullpath =
                    \ pseudotag.path . a:typeinfo.sro . pseudotag.name
    endif
    let pseudotag.depth = len(split(pseudotag.path, '\V' . a:typeinfo.sro))

    let pseudotag.parent = a:parent

    let pseudotag.fileinfo = a:fileinfo
    let pseudotag.typeinfo = a:typeinfo

    call pseudotag.initFoldState()

    return pseudotag
endfunction

" Sorting {{{1
" s:SortTags() {{{2
function! s:SortTags(tags, comparemethod) abort
    call sort(a:tags, a:comparemethod)

    for tag in a:tags
        if !empty(tag.getChildren())
            call s:SortTags(tag.getChildren(), a:comparemethod)
        endif
    endfor
endfunction

" s:CompareByKind() {{{2
function! s:CompareByKind(tag1, tag2) abort
    let typeinfo = s:compare_typeinfo

    if typeinfo.kinddict[a:tag1.fields.kind] <#
     \ typeinfo.kinddict[a:tag2.fields.kind]
        return -1
    elseif typeinfo.kinddict[a:tag1.fields.kind] >#
         \ typeinfo.kinddict[a:tag2.fields.kind]
        return 1
    else
        " Ignore '~' prefix for C++ destructors to sort them directly under
        " the constructors
        if a:tag1.name[0] ==# '~'
            let name1 = a:tag1.name[1:]
        else
            let name1 = a:tag1.name
        endif
        if a:tag2.name[0] ==# '~'
            let name2 = a:tag2.name[1:]
        else
            let name2 = a:tag2.name
        endif

        let ci = g:tagbar_case_insensitive
        if (((!ci) && (name1 <=# name2)) || (ci && (name1 <=? name2)))
            return -1
        else
            return 1
        endif
    endif
endfunction

" s:CompareByLine() {{{2
function! s:CompareByLine(tag1, tag2) abort
    return a:tag1.fields.line - a:tag2.fields.line
endfunction

" s:ToggleSort() {{{2
function! s:ToggleSort() abort
    let fileinfo = s:TagbarState().getCurrent(0)
    if empty(fileinfo)
        return
    endif

    " Save the tag the cursor is currently on
    let curline = line('.')
    let taginfo = s:GetTagInfo(curline, 0)

    match none

    let s:compare_typeinfo = s:known_types[fileinfo.ftype]

    if has_key(s:compare_typeinfo, 'sort')
        let s:compare_typeinfo.sort = !s:compare_typeinfo.sort
    else
        let g:tagbar_sort = !g:tagbar_sort
    endif

    call fileinfo.sortTags()

    call s:RenderContent()
    call s:SetStatusLine()

    " If we were on a tag before sorting then jump to it, otherwise restore
    " the cursor to the current line
    if !empty(taginfo)
        execute taginfo.tline
    else
        execute curline
    endif
endfunction

" Display {{{1
" s:RenderContent() {{{2
function! s:RenderContent(...) abort
    call s:debug('RenderContent called')
    let s:new_window = 0

    if a:0 == 1
        let fileinfo = a:1
    else
        let fileinfo = s:TagbarState().getCurrent(0)
    endif

    if empty(fileinfo)
        call s:debug('Empty fileinfo, returning')
        return
    endif

    let tagbarwinnr = bufwinnr(s:TagbarBufName())

    if &filetype == 'tagbar'
        let in_tagbar = 1
    else
        let in_tagbar = 0
        let prevwinnr = winnr()

        " Get the previous window number, so that we can reproduce
        " the window entering history later. Do not run autocmd on
        " this command, make sure nothing is interfering.
        " let pprevwinnr = winnr('#') " Messes up windows for some reason
        call s:goto_win('p', 1)
        let pprevwinnr = winnr()
        call s:goto_win(tagbarwinnr, 1)
    endif

    if !empty(s:TagbarState().getCurrent(0)) &&
     \ fileinfo.fpath ==# s:TagbarState().getCurrent(0).fpath
        " We're redisplaying the same file, so save the view
        call s:debug('Redisplaying file [' . fileinfo.fpath . ']')
        let saveline = line('.')
        let savecol  = col('.')
        let topline  = line('w0')
    endif

    let lazyredraw_save = &lazyredraw
    set lazyredraw
    let eventignore_save = &eventignore
    set eventignore=all

    setlocal modifiable

    silent %delete _

    call s:PrintHelp()

    let typeinfo = fileinfo.typeinfo

    if !empty(fileinfo.getTags())
        " Print tags
        call s:PrintKinds(typeinfo, fileinfo)
    else
        call s:debug('No tags found, skipping printing.')
        if g:tagbar_compact && s:short_help
            silent 0put ='\" No tags found.'
        else
            silent  put ='\" No tags found.'
        endif
    endif

    " Delete empty lines at the end of the buffer
    for linenr in range(line('$'), 1, -1)
        if getline(linenr) =~ '^$'
            execute 'silent ' . linenr . 'delete _'
        else
            break
        endif
    endfor

    setlocal nomodifiable

    if !empty(s:TagbarState().getCurrent(0)) &&
     \ fileinfo.fpath ==# s:TagbarState().getCurrent(0).fpath
        let scrolloff_save = &scrolloff
        set scrolloff=0

        call cursor(topline, 1)
        normal! zt
        call cursor(saveline, savecol)

        let &scrolloff = scrolloff_save
    else
        " Make sure as much of the Tagbar content as possible is shown in the
        " window by jumping to the top after drawing
        execute 1
        call winline()

        " Invalidate highlight cache from old file
        let s:last_highlight_tline = 0
    endif

    let &lazyredraw  = lazyredraw_save
    let &eventignore = eventignore_save

    if !in_tagbar
        call s:goto_win(pprevwinnr, 1)
        call s:goto_win(prevwinnr, 1)
    endif
endfunction

" s:PrintKinds() {{{2
function! s:PrintKinds(typeinfo, fileinfo) abort
    call s:debug('PrintKinds called')

    " If the short or long help is being displayed then the line numbers don't
    " match up with the length of the output list
    let offset = g:tagbar_compact && s:short_help ? 0 : line('.')
    let output = []

    for kind in a:typeinfo.kinds
        let curtags = filter(copy(a:fileinfo.getTags()),
                           \ 'v:val.fields.kind ==# kind.short')
        call s:debug('Printing kind: ' . kind.short .
                   \ ', number of (top-level) tags: ' . len(curtags))

        if empty(curtags)
            continue
        endif

        if has_key(get(a:typeinfo, 'kind2scope', {}), kind.short)
            " Scoped tags
            for tag in curtags
                call s:PrintTag(tag, 0, output, a:fileinfo, a:typeinfo)

                if !g:tagbar_compact
                    call add(output, "")
                endif
            endfor
        else
            " Non-scoped tags
            let kindtag = curtags[0].parent

            if kindtag.isFolded()
                let foldmarker = s:icon_closed
            else
                let foldmarker = s:icon_open
            endif

            let padding = g:tagbar_show_visibility ? ' ' : ''
            call add(output, foldmarker . padding . kind.long)

            let curline                   = len(output) + offset
            let kindtag.tline             = curline
            let a:fileinfo.tline[curline] = kindtag

            if !kindtag.isFolded()
                for tag in curtags
                    let str = tag.strfmt()
                    call add(output, repeat(' ', g:tagbar_indent) . str)

                    " Save the current tagbar line in the tag for easy
                    " highlighting access
                    let curline                   = len(output) + offset
                    let tag.tline                 = curline
                    let a:fileinfo.tline[curline] = tag
                    let tag.depth                 = 1
                endfor
            endif

            if !g:tagbar_compact
                call add(output, "")
            endif
        endif
    endfor

    let outstr = join(output, "\n")
    if g:tagbar_compact && s:short_help
        silent 0put =outstr
    else
        silent  put =outstr
    endif
endfunction

" s:PrintTag() {{{2
function! s:PrintTag(tag, depth, output, fileinfo, typeinfo) abort
    if g:tagbar_hide_nonpublic &&
     \ get(a:tag.fields, 'access', 'public') !=# 'public'
        let a:tag.tline = -1
        return
    endif

    " Print tag indented according to depth
    let tagstr = repeat(' ', a:depth * g:tagbar_indent) . a:tag.strfmt()
    call add(a:output, tagstr)

    " Save the current tagbar line in the tag for easy highlighting access
    let offset = g:tagbar_compact && s:short_help ? 0 : line('.')
    let curline                   = len(a:output) + offset
    let a:tag.tline               = curline
    let a:fileinfo.tline[curline] = a:tag

    " Recursively print children
    if a:tag.isFoldable() && !a:tag.isFolded()
        for ckind in a:typeinfo.kinds
            let childfilter = 'v:val.fields.kind ==# ckind.short'
            if g:tagbar_hide_nonpublic
                let childfilter .=
                      \ ' && get(v:val.fields, "access", "public") ==# "public"'
            endif
            let childtags = filter(copy(a:tag.getChildren()), childfilter)
            if len(childtags) > 0
                " Print 'kind' header of following children, but only if they
                " are not scope-defining tags (since those already have an
                " identifier)
                if !has_key(a:typeinfo.kind2scope, ckind.short)
                    let indent  = (a:depth + 1) * g:tagbar_indent
                    let indent += g:tagbar_show_visibility
                    let indent += 1 " fold symbol
                    call add(a:output, repeat(' ', indent) . '[' . ckind.long . ']')
                    " Add basic tag to allow folding when on the header line
                    let headertag = s:BaseTag.New(ckind.long)
                    let headertag.parent = a:tag
                    let headertag.fileinfo = a:tag.fileinfo
                    let a:fileinfo.tline[len(a:output) + offset] = headertag
                endif
                for childtag in childtags
                    call s:PrintTag(childtag, a:depth + 1, a:output,
                                  \ a:fileinfo, a:typeinfo)
                endfor
            endif
        endfor
    endif
endfunction

" s:PrintHelp() {{{2
function! s:PrintHelp() abort
    if !g:tagbar_compact && s:short_help
        silent 0put ='\" Press ' . s:get_map_str('help') . ' for help'
        silent  put _
    elseif !s:short_help
        silent 0put ='\" Tagbar keybindings'
        silent  put ='\"'
        silent  put ='\" --------- General ---------'
        silent  put ='\" ' . s:get_map_str('jump') . ': Jump to tag definition'
        silent  put ='\" ' . s:get_map_str('preview') . ': As above, but stay in'
        silent  put ='\"    Tagbar window'
        silent  put ='\" ' . s:get_map_str('previewwin') . ': Show tag in preview window'
        silent  put ='\" ' . s:get_map_str('nexttag') . ': Go to next top-level tag'
        silent  put ='\" ' . s:get_map_str('prevtag') . ': Go to previous top-level tag'
        silent  put ='\" ' . s:get_map_str('showproto') . ': Display tag prototype'
        silent  put ='\" ' . s:get_map_str('hidenonpublic') . ': Hide non-public tags'
        silent  put ='\"'
        silent  put ='\" ---------- Folds ----------'
        silent  put ='\" ' . s:get_map_str('openfold') . ': Open fold'
        silent  put ='\" ' . s:get_map_str('closefold') . ': Close fold'
        silent  put ='\" ' . s:get_map_str('togglefold') . ': Toggle fold'
        silent  put ='\" ' . s:get_map_str('openallfolds') . ': Open all folds'
        silent  put ='\" ' . s:get_map_str('closeallfolds') . ': Close all folds'
        silent  put ='\" ' . s:get_map_str('nextfold') . ': Go to next fold'
        silent  put ='\" ' . s:get_map_str('prevfold') . ': Go to previous fold'
        silent  put ='\"'
        silent  put ='\" ---------- Misc -----------'
        silent  put ='\" ' . s:get_map_str('togglesort') . ': Toggle sort'
        silent  put ='\" ' . s:get_map_str('togglecaseinsensitive') . ': Toggle case insensitive sort option'
        silent  put ='\" ' . s:get_map_str('toggleautoclose') . ': Toggle autoclose option'
        silent  put ='\" ' . s:get_map_str('zoomwin') . ': Zoom window in/out'
        silent  put ='\" ' . s:get_map_str('close') . ': Close window'
        silent  put ='\" ' . s:get_map_str('help') . ': Toggle help'
        silent  put _
    endif
endfunction
function! s:get_map_str(map) abort
    let def = get(g:, 'tagbar_map_' . a:map)
    if type(def) == type("")
        return def
    else
        return join(def, ', ')
    endif
endfunction

" s:RenderKeepView() {{{2
" The gist of this function was taken from NERDTree by Martin Grenfell.
function! s:RenderKeepView(...) abort
    if a:0 == 1
        let line = a:1
    else
        let line = line('.')
    endif

    let curcol  = col('.')
    let topline = line('w0')

    call s:RenderContent()

    let scrolloff_save = &scrolloff
    set scrolloff=0

    call cursor(topline, 1)
    normal! zt
    call cursor(line, curcol)

    let &scrolloff = scrolloff_save

    redraw
endfunction

" User actions {{{1
" s:HighlightTag() {{{2
function! s:HighlightTag(openfolds, ...) abort
    let tagline = 0

    let force = a:0 > 0 ? a:1 : 0

    if a:0 > 1
        let tag = s:GetNearbyTag(1, 0, a:2)
    else
        let tag = s:GetNearbyTag(1, 0)
    endif
    if !empty(tag)
        let tagline = tag.tline
    endif

    " Don't highlight the tag again if it's the same one as last time.
    " This prevents the Tagbar window from jumping back after scrolling with
    " the mouse.
    if !force && tagline == s:last_highlight_tline
        return
    else
        let s:last_highlight_tline = tagline
    endif

    let tagbarwinnr = bufwinnr(s:TagbarBufName())
    if tagbarwinnr == -1
        return
    endif

    if tagbarwinnr == winnr()
        let in_tagbar = 1
    else
        let in_tagbar = 0
        let prevwinnr = winnr()
        call s:goto_win('p', 1)
        let pprevwinnr = winnr()
        call s:goto_win(tagbarwinnr, 1)
    endif

    try
        match none

        " No tag above cursor position so don't do anything
        if tagline == 0
            return
        endif

        if g:tagbar_autoshowtag == 1 || a:openfolds
            call s:OpenParents(tag)
        endif

        " Check whether the tag is inside a closed fold and highlight the parent
        " instead in that case
        let tagline = tag.getClosedParentTline()

        " Parent tag line number is invalid, better don't do anything
        if tagline <= 0
            return
        endif

        " Go to the line containing the tag
        execute tagline

        " Make sure the tag is visible in the window
        call winline()

        let foldpat = '[' . s:icon_open . s:icon_closed . ' ]'
        let pattern = '/^\%' . tagline . 'l\s*' . foldpat . '[-+# ]\zs[^( ]\+\ze/'
        call s:debug("Highlight pattern: '" . pattern . "'")
        if hlexists('TagbarHighlight') " Safeguard in case syntax highlighting is disabled
            execute 'match TagbarHighlight ' . pattern
        else
            execute 'match Search ' . pattern
        endif
    finally
        if !in_tagbar
            call s:goto_win(pprevwinnr, 1)
            call s:goto_win(prevwinnr, 1)
        endif
        redraw
    endtry
endfunction

" s:JumpToTag() {{{2
function! s:JumpToTag(stay_in_tagbar) abort
    let taginfo = s:GetTagInfo(line('.'), 1)

    let autoclose = w:autoclose

    if empty(taginfo) || !taginfo.isNormalTag()
        return
    endif

    let tagbarwinnr = winnr()

    call s:GotoFileWindow(taginfo.fileinfo)

    " Mark current position so it can be jumped back to
    mark '

    " Jump to the line where the tag is defined. Don't use the search pattern
    " since it doesn't take the scope into account and thus can fail if tags
    " with the same name are defined in different scopes (e.g. classes)
    execute taginfo.fields.line

    " If the file has been changed but not saved, the tag may not be on the
    " saved line anymore, so search for it in the vicinity of the saved line
    if match(getline('.'), taginfo.pattern) == -1
        let interval = 1
        let forward  = 1
        while search(taginfo.pattern, 'W' . forward ? '' : 'b') == 0
            if !forward
                if interval > line('$')
                    break
                else
                    let interval = interval * 2
                endif
            endif
            let forward = !forward
        endwhile
    endif

    " If the tag is on a different line after unsaved changes update the tag
    " and file infos/objects
    let curline = line('.')
    if taginfo.fields.line != curline
        let taginfo.fields.line = curline
        let taginfo.fileinfo.fline[curline] = taginfo
    endif

    " Center the tag in the window and jump to the correct column if
    " available, otherwise try to find it in the line
    normal! z.
    if taginfo.fields.column > 0
        call cursor(taginfo.fields.line, taginfo.fields.column)
    else
        call cursor(taginfo.fields.line, 1)
        call search(taginfo.name, 'c', line('.'))
    endif

    normal! zv

    if a:stay_in_tagbar
        call s:HighlightTag(0)
        call s:goto_win(tagbarwinnr)
        redraw
    elseif g:tagbar_autoclose || autoclose
        " Also closes preview window
        call s:CloseWindow()
    else
        " Close the preview window if it was opened by us
        if s:pwin_by_tagbar
            pclose
        endif
        call s:HighlightTag(0)
    endif
endfunction

" s:ShowInPreviewWin() {{{2
function! s:ShowInPreviewWin() abort
    let pos = getpos('.')
    let taginfo = s:GetTagInfo(pos[1], 1)

    if empty(taginfo) || !taginfo.isNormalTag()
        return
    endif

    let pwin_open = 0
    for win in range(1, winnr('$'))
        if getwinvar(win, '&previewwindow')
            let pwin_open = 1
            break
        endif
    endfor

    " We want the preview window to be relative to the file window in normal
    " (horizontal) mode, and relative to the Tagbar window in vertical mode,
    " to make the best use of space.
    if g:tagbar_vertical == 0
        call s:GotoFileWindow(taginfo.fileinfo, 1)
        call s:mark_window()
    endif

    " Open the preview window if it is not already open. This has to be done
    " explicitly before the :psearch below to better control its positioning.
    if !pwin_open
        silent execute
            \ g:tagbar_previewwin_pos . ' pedit ' .
            \ fnameescape(taginfo.fileinfo.fpath)
        if g:tagbar_vertical != 0
            silent execute 'vertical resize ' . g:tagbar_width
        endif
        " Remember that the preview window was opened by Tagbar so we can
        " safely close it by ourselves
        let s:pwin_by_tagbar = 1
    endif

    if g:tagbar_vertical != 0
        call s:GotoFileWindow(taginfo.fileinfo, 1)
        call s:mark_window()
    endif

    " Use psearch instead of pedit since pedit essentially reloads the file
    " and creates an empty undo entry. psearch has to be called from the file
    " window, and since we only want matches in the current file we disable
    " the 'include' option. Also start searching at the correct line number to
    " find the correct tag in case of tags with the same name and to speed up
    " the searching. Unfortunately the /\%l pattern doesn't seem to work with
    " psearch.
    let include_save = &include
    set include=
    silent! execute taginfo.fields.line . ',$psearch! /' . taginfo.pattern . '/'
    let &include = include_save

    call s:goto_win('P', 1)
    normal! zv
    normal! zz
    call s:goto_markedwin(1)
    call s:goto_tagbar(1)
    call cursor(pos[1], pos[2])
endfunction

" s:ShowPrototype() {{{2
function! s:ShowPrototype(short) abort
    let taginfo = s:GetTagInfo(line('.'), 1)

    if empty(taginfo)
        return ''
    endif

    echo taginfo.getPrototype(a:short)
endfunction

" s:ToggleHelp() {{{2
function! s:ToggleHelp() abort
    let s:short_help = !s:short_help

    " Prevent highlighting from being off after adding/removing the help text
    match none

    call s:RenderContent()

    execute 1
    redraw
endfunction

" s:GotoNextToplevelTag() {{{2
function! s:GotoNextToplevelTag(direction) abort
    let curlinenr = line('.')
    let newlinenr = line('.')

    if a:direction == 1
        let range = range(line('.') + 1, line('$'))
    else
        let range = range(line('.') - 1, 1, -1)
    endif

    for tmplinenr in range
        let taginfo = s:GetTagInfo(tmplinenr, 0)

        if empty(taginfo)
            continue
        elseif empty(taginfo.parent)
            let newlinenr = tmplinenr
            break
        endif
    endfor

    if curlinenr != newlinenr
        execute newlinenr
        call winline()
    endif

    redraw
endfunction

" Folding {{{1
" s:OpenFold() {{{2
function! s:OpenFold() abort
    let fileinfo = s:TagbarState().getCurrent(0)
    if empty(fileinfo)
        return
    endif

    let curline = line('.')

    let tag = s:GetTagInfo(curline, 0)
    if empty(tag)
        return
    endif

    call tag.openFold()

    call s:RenderKeepView()
endfunction

" s:CloseFold() {{{2
function! s:CloseFold() abort
    let fileinfo = s:TagbarState().getCurrent(0)
    if empty(fileinfo)
        return
    endif

    match none

    let curline = line('.')

    let curtag = s:GetTagInfo(curline, 0)
    if empty(curtag)
        return
    endif

    let newline = curtag.closeFold()

    call s:RenderKeepView(newline)
endfunction

" s:ToggleFold() {{{2
function! s:ToggleFold() abort
    let fileinfo = s:TagbarState().getCurrent(0)
    if empty(fileinfo)
        return
    endif

    match none

    let curtag = s:GetTagInfo(line('.'), 0)
    if empty(curtag)
        return
    endif

    let newline = line('.')

    if curtag.isKindheader()
        call curtag.toggleFold()
    elseif curtag.isFoldable()
        if curtag.isFolded()
            call curtag.openFold()
        else
            let newline = curtag.closeFold()
        endif
    else
        let newline = curtag.closeFold()
    endif

    call s:RenderKeepView(newline)
endfunction

" s:SetFoldLevel() {{{2
function! s:SetFoldLevel(level, force) abort
    if a:level < 0
        call s:warning('Foldlevel can''t be negative')
        return
    endif

    let fileinfo = s:TagbarState().getCurrent(0)
    if empty(fileinfo)
        return
    endif

    call s:SetFoldLevelRecursive(fileinfo, fileinfo.getTags(), a:level)

    let typeinfo = fileinfo.typeinfo

    " Apply foldlevel to 'kind's
    if a:level == 0
        for kind in typeinfo.kinds
            call fileinfo.closeKindFold(kind)
        endfor
    else
        for kind in typeinfo.kinds
            if a:force || !kind.fold
                call fileinfo.openKindFold(kind)
            endif
        endfor
    endif

    let fileinfo.foldlevel = a:level

    call s:RenderContent()
endfunction

" s:SetFoldLevelRecursive() {{{2
" Apply foldlevel to normal tags
function! s:SetFoldLevelRecursive(fileinfo, tags, level) abort
    for tag in a:tags
        if tag.depth >= a:level
            call tag.setFolded(1)
        else
            call tag.setFolded(0)
        endif

        if !empty(tag.getChildren())
            call s:SetFoldLevelRecursive(a:fileinfo, tag.getChildren(), a:level)
        endif
    endfor
endfunction

" s:OpenParents() {{{2
function! s:OpenParents(...) abort
    if a:0 == 1
        let tag = a:1
    else
        let tag = s:GetNearbyTag(1, 0)
    endif

    if !empty(tag)
        call tag.openParents()
        call s:RenderKeepView()
    endif
endfunction

" s:GotoNextFold() {{{2
function! s:GotoNextFold() abort
    let curlinenr = line('.')
    let newlinenr = line('.')

    let range = range(line('.') + 1, line('$'))

    for linenr in range
        let taginfo = s:GetTagInfo(linenr, 0)

        if empty(taginfo)
            continue
        elseif !empty(taginfo.getChildren()) || taginfo.isKindheader()
            let newlinenr = linenr
            break
        endif
    endfor

    if curlinenr != newlinenr
        execute linenr
        call winline()
    endif

    redraw
endfunction

" s:GotoPrevFold() {{{2
function! s:GotoPrevFold() abort
    let curlinenr = line('.')
    let newlinenr = line('.')
    let curtag = s:GetTagInfo(curlinenr, 0)
    let curparent = get(curtag, 'parent', {})

    let range = range(line('.') - 1, 1, -1)

    for linenr in range
        let taginfo = s:GetTagInfo(linenr, 0)

        if empty(taginfo)
            continue
        " Check for the first tag that is either:
        " - the last tag in an open fold, that is skip all tags that have the
        "   same parent as the current one, or
        " - a closed parent fold.
        elseif (!empty(taginfo.parent) && taginfo.parent != curparent &&
              \ empty(taginfo.getChildren())) ||
             \ ((!empty(taginfo.getChildren()) || taginfo.isKindheader()) &&
              \ taginfo.isFolded())
            let newlinenr = linenr
            break
        endif
    endfor

    if curlinenr != newlinenr
        execute linenr
        call winline()
    endif

    redraw
endfunction

" Helper functions {{{1
" s:AutoUpdate() {{{2
function! s:AutoUpdate(fname, force, ...) abort
    call s:debug('AutoUpdate called [' . a:fname . ']')

    " Whether we want to skip actually displaying the tags in Tagbar and only
    " update the fileinfo
    let no_display = a:0 > 0 ? a:1 : 0

    " This file is being loaded due to a quickfix command like vimgrep, so
    " don't process it
    if exists('s:tagbar_qf_active')
        return
    elseif exists('s:window_opening')
        " This can happen if another plugin causes the active window to change
        " with an autocmd during the initial Tagbar window creation. In that
        " case InitWindow() hasn't had a chance to run yet and things can
        " break. MiniBufExplorer does this, for example. Completely disabling
        " autocmds at that point is also not ideal since for example
        " statusline plugins won't be able to update.
        call s:debug('Still opening window, stopping processing')
        return
    endif

    " Get the filetype of the file we're about to process
    let bufnr = bufnr(a:fname)
    let ftype = getbufvar(bufnr, '&filetype')

    " Don't do anything if we're in the tagbar window
    if ftype == 'tagbar'
        call s:debug('In Tagbar window, stopping processing')
        return
    endif

    " Only consider the main filetype in cases like 'python.django'
    let sftype = get(split(ftype, '\.'), 0, '')
    call s:debug("Vim filetype: '" . ftype . "', " .
               \ "sanitized filetype: '" . sftype . "'")

    " Don't do anything if the file isn't supported
    if !s:IsValidFile(a:fname, sftype)
        call s:debug('Not a valid file, stopping processing')
        let s:nearby_disabled = 1
        return
    endif

    let updated = 0

    " Process the file if it's unknown or the information is outdated.
    " Testing the mtime of the file is necessary in case it got changed
    " outside of Vim, for example by checking out a different version from a
    " VCS.
    if s:known_files.has(a:fname)
        let curfile = s:known_files.get(a:fname)
        " if a:force || getbufvar(curfile.bufnr, '&modified') ||
        if a:force || empty(curfile) || curfile.ftype != sftype ||
         \ (filereadable(a:fname) && getftime(a:fname) > curfile.mtime)
            call s:debug('File data outdated, updating [' . a:fname . ']')
            call s:ProcessFile(a:fname, sftype)
            let updated = 1
        else
            call s:debug('File data seems up to date [' . a:fname . ']')
        endif
    elseif !s:known_files.has(a:fname)
        call s:debug('New file, processing [' . a:fname . ']')
        call s:ProcessFile(a:fname, sftype)
        let updated = 1
    endif

    if no_display
        return
    endif

    let fileinfo = s:known_files.get(a:fname)

    " If we don't have an entry for the file by now something must have gone
    " wrong, so don't change the tagbar content
    if empty(fileinfo)
        call s:debug('fileinfo empty after processing [' . a:fname . ']')
        return
    endif

    " Display the tagbar content if the tags have been updated or a different
    " file is being displayed
    if bufwinnr(s:TagbarBufName()) != -1 && !s:paused &&
     \ (s:new_window || updated ||
      \ (!empty(s:TagbarState().getCurrent(0)) &&
       \ a:fname != s:TagbarState().getCurrent(0).fpath))
        call s:RenderContent(fileinfo)
    endif

    " Call setCurrent after rendering so RenderContent can check whether the
    " same file is being redisplayed
    if !empty(fileinfo)
        call s:debug('Setting current file [' . a:fname . ']')
        call s:TagbarState().setCurrent(fileinfo)
        let s:nearby_disabled = 0
    endif

    call s:HighlightTag(0)
    call s:SetStatusLine()
    call s:debug('AutoUpdate finished successfully')
endfunction

" s:CheckMouseClick() {{{2
function! s:CheckMouseClick() abort
    let line   = getline('.')
    let curcol = col('.')

    if (match(line, s:icon_open . '[-+ ]') + 1) == curcol
        call s:CloseFold()
    elseif (match(line, s:icon_closed . '[-+ ]') + 1) == curcol
        call s:OpenFold()
    elseif g:tagbar_singleclick
        call s:JumpToTag(0)
    endif
endfunction

" s:DetectFiletype() {{{2
function! s:DetectFiletype(bufnr) abort
    " Filetype has already been detected for loaded buffers, but not
    " necessarily for unloaded ones
    let ftype = getbufvar(a:bufnr, '&filetype')

    if bufloaded(a:bufnr)
        return ftype
    endif

    if ftype != ''
        return ftype
    endif

    " Unloaded buffer with non-detected filetype, need to detect filetype
    " manually
    let bufname = bufname(a:bufnr)

    let eventignore_save = &eventignore
    set eventignore=FileType
    let filetype_save = &filetype

    exe 'doautocmd filetypedetect BufRead ' . bufname
    let ftype = &filetype

    let &filetype = filetype_save
    let &eventignore = eventignore_save

    return ftype
endfunction

" s:EscapeCtagsCmd() {{{2
" Assemble the ctags command line in a way that all problematic characters are
" properly escaped and converted to the system's encoding
" Optional third parameter is a file name to run ctags on
" Note: The second parameter (a:args) can be a list of args or
"       a single string of the args.
"       When a:args is a list, each argument in the list will be escaped for the
"       current &shell type.
"       When a:args is a string, all arguments should be escaped appropriately
"       (if required). In most use cases no escaping is required so a string
"       is acceptable. But in cases where arguments may need to be escaped
"       differently for each &shell type, then pass a list of arguments.
function! s:EscapeCtagsCmd(ctags_bin, args, ...) abort
    call s:debug('EscapeCtagsCmd called')
    call s:debug('ctags_bin: ' . a:ctags_bin)
    if type(a:args)==type('')
        call s:debug('ctags_args (is a string): ' . a:args)
    elseif type(a:args)==type([])
        call s:debug('ctags_args (is a list): ' . string(a:args))
    endif

    if exists('+shellslash')
        let shellslash_save = &shellslash
        set noshellslash
    endif

    "Set up 0th argument of ctags_cmd
    "a:ctags_bin may have special characters that require escaping.
    if &shell =~ 'cmd\.exe$' && a:ctags_bin !~ '\s'
        "For windows cmd.exe, escaping the 0th argument can cause
        "problems if it references a batch file and the batch file uses %~dp0.
        "So for windows cmd.exe, only escape the 0th argument iff necessary.
        "Only known necessary case is when ctags_bin executable filename has
        "whitespace character(s).

        "  Example: If 0th argument is wrapped in double quotes AND it is not
        "  an absolute path to ctags_bin, but rather an executable in %PATH%,
        "  then %~dp0 resolves to the current working directory rather than
        "  the batch file's directory. Batch files like this generally exepect
        "  and depend on %~dp0 to resolve the batch file's directory.
        "  Note: Documentation such as `help cmd.exe` and
        "  http://www.microsoft.com/resources/documentation/windows/xp/all/proddocs/en-us/cmd.mspx?mfr=true
        "  suggest other special characters that require escaping for command
        "  line completion.  But tagbar.vim does not use the command line
        "  completion feature of cmd.exe and testing shows that the only special
        "  character that needs to be escaped for tagbar.vim is <space> for
        "  windows cmd.exe.
        let ctags_cmd = a:ctags_bin
    else
        let ctags_cmd = shellescape(a:ctags_bin)
    endif

    "Add additional arguments to ctags_cmd
    if type(a:args)==type('')
        "When a:args is a string, append the arguments
        "Note: In this case, do not attempt to shell escape a:args string.
        "This function expects the string to already be escaped properly for
        "the shell type. Why not escape? Because it could be ambiguous about
        "whether a space is an argument separator or included in the argument.
        "Since escaping rules vary from shell to shell, it is better to pass a
        "list of arguments to a:args. With a list, each argument is clearly
        "separated, so shellescape() can calculate the appropriate escaping
        "for each argument for the current &shell.
        let ctags_cmd .= ' ' . a:args
    elseif type(a:args)==type([])
        "When a:args is a list, shellescape() each argument and append ctags_cmd
        "Note: It's a better practice to shellescape() each argument separately so that
        "spaces used as a separator between arguments can be distinguished with
        "spaces used inside a single argument.
        for arg in a:args
            let ctags_cmd .= ' ' . shellescape(arg)
        endfor
    endif

    "if a filename was specified, add filename as final argument to ctags_cmd.
    if a:0 == 1
        let ctags_cmd .= ' ' . shellescape(a:1)
    endif

    if exists('+shellslash')
        let &shellslash = shellslash_save
    endif

    " Needed for cases where 'encoding' is different from the system's
    " encoding
    if has('multi_byte')
        if g:tagbar_systemenc != &encoding
            let ctags_cmd = iconv(ctags_cmd, &encoding, g:tagbar_systemenc)
        elseif $LANG != ''
            let ctags_cmd = iconv(ctags_cmd, &encoding, $LANG)
        endif
    endif

    call s:debug('Escaped ctags command: ' . ctags_cmd)

    if ctags_cmd == ''
        if !s:warnings.encoding
            call s:warning('Tagbar: Ctags command encoding conversion failed!' .
                \ ' Please read ":h g:tagbar_systemenc".')
            let s:warnings.encoding = 1
        endif
    endif

    return ctags_cmd
endfunction

" s:ExecuteCtags() {{{2
" Execute ctags with necessary shell settings
" Partially based on the discussion at
" http://vim.1045645.n5.nabble.com/bad-default-shellxquote-in-Widows-td1208284.html
function! s:ExecuteCtags(ctags_cmd) abort
    call s:debug('Executing ctags command: ' . a:ctags_cmd)

    if &shell =~# 'fish$'
        " Reset shell since fish isn't really compatible
        let shell_save = &shell
        set shell=sh
    endif

    if exists('+shellslash')
        let shellslash_save = &shellslash
        set noshellslash
    endif

    if &shell =~ 'cmd\.exe'
        let shellxquote_save = &shellxquote
        set shellxquote=\"
        let shellcmdflag_save = &shellcmdflag
        set shellcmdflag=/s\ /c
    endif

    if s:debug
        silent 5verbose let ctags_output = system(a:ctags_cmd)
        call s:debug(v:statusmsg)
        call s:debug('Exit code: ' . v:shell_error)
        redraw!
    else
        silent let ctags_output = system(a:ctags_cmd)
    endif

    if &shell =~ 'cmd\.exe'
        let &shellxquote  = shellxquote_save
        let &shellcmdflag = shellcmdflag_save
    endif

    if exists('+shellslash')
        let &shellslash = shellslash_save
    endif

    if exists('shell_save')
        let &shell = shell_save
    endif

    return ctags_output
endfunction

" s:GetNearbyTag() {{{2
" Get the tag info for a file near the cursor in the current file
function! s:GetNearbyTag(all, forcecurrent, ...) abort
    if s:nearby_disabled
        return {}
    endif

    let fileinfo = s:TagbarState().getCurrent(a:forcecurrent)
    if empty(fileinfo)
        return {}
    endif

    let typeinfo = fileinfo.typeinfo
    if a:0 > 0
        let curline = a:1
    else
        let curline = line('.')
    endif
    let tag = {}

    " If a tag appears in a file more than once (for example namespaces in
    " C++) only one of them has a 'tline' entry and can thus be highlighted.
    " The only way to solve this would be to go over the whole tag list again,
    " making everything slower. Since this should be a rare occurence and
    " highlighting isn't /that/ important ignore it for now.
    for line in range(curline, 1, -1)
        if has_key(fileinfo.fline, line)
            let curtag = fileinfo.fline[line]
            if a:all || typeinfo.getKind(curtag.fields.kind).stl
                let tag = curtag
                break
            endif
        endif
    endfor

    return tag
endfunction

" s:GetTagInfo() {{{2
" Return the info dictionary of the tag on the specified line. If the line
" does not contain a valid tag (for example because it is empty or only
" contains a pseudo-tag) return an empty dictionary.
function! s:GetTagInfo(linenr, ignorepseudo) abort
    let fileinfo = s:TagbarState().getCurrent(0)

    if empty(fileinfo)
        return {}
    endif

    " Don't do anything in empty and comment lines
    let curline = getbufline(bufnr(s:TagbarBufName()), a:linenr)[0]
    if curline =~ '^\s*$' || curline[0] == '"'
        return {}
    endif

    " Check if there is a tag on the current line
    if !has_key(fileinfo.tline, a:linenr)
        return {}
    endif

    let taginfo = fileinfo.tline[a:linenr]

    " Check if the current tag is not a pseudo-tag
    if a:ignorepseudo && taginfo.isPseudoTag()
        return {}
    endif

    return taginfo
endfunction

" s:GetFileWinnr() {{{2
" Get the number of the window that has Tagbar's current file loaded into it,
" or 0 if no window has loaded it. It tries the previous window first, if that
" does not have the correct buffer loaded it will look for the first one with
" the correct buffer in it.
function! s:GetFileWinnr(fileinfo) abort
    let filewinnr = 0
    let prevwinnr = winnr("#")

    if winbufnr(prevwinnr) == a:fileinfo.bufnr &&
     \ !getwinvar(prevwinnr, '&previewwindow')
        let filewinnr = prevwinnr
    else
        " Search for the first real window that has the correct buffer loaded
        " in it. Similar to bufwinnr() but skips the previewwindow.
        for i in range(1, winnr('$'))
            call s:goto_win(i, 1)
            if bufnr('%') == a:fileinfo.bufnr && !&previewwindow
                let filewinnr = winnr()
                break
            endif
        endfor

        call s:goto_tagbar(1)
    endif

    return filewinnr
endfunction

" s:GotoFileWindow() {{{2
" Try to switch to the window that has Tagbar's current file loaded in it, or
" open the file in an existing window otherwise.
function! s:GotoFileWindow(fileinfo, ...) abort
    let noauto = a:0 > 0 ? a:1 : 0

    let filewinnr = s:GetFileWinnr(a:fileinfo)

    " If there is no window with the correct buffer loaded then load it
    " into the first window that has a non-special buffer in it.
    if filewinnr == 0
        for i in range(1, winnr('$'))
            call s:goto_win(i, 1)
            if &buftype == '' && !&previewwindow
                execute 'buffer ' . a:fileinfo.bufnr
                break
            endif
        endfor
    else
        call s:goto_win(filewinnr, 1)
    endif

    " To make ctrl-w_p work we switch between the Tagbar window and the
    " correct window once
    call s:goto_tagbar(noauto)
    call s:goto_win('p', noauto)
endfunction

" s:ToggleHideNonPublicTags() {{{2
function! s:ToggleHideNonPublicTags() abort
    let fileinfo = s:TagbarState().getCurrent(0)
    if empty(fileinfo)
        return
    endif

    " Save the tag the cursor is currently on
    let curline = line('.')
    let taginfo = s:GetTagInfo(curline, 0)

    match none

    let g:tagbar_hide_nonpublic = !g:tagbar_hide_nonpublic
    call s:RenderKeepView()
    call s:SetStatusLine()

    " If we were on a tag before sorting then jump to it, otherwise restore
    " the cursor to the current line
    if !empty(taginfo)
        execute taginfo.tline
    else
        execute curline
    endif
endfunction

" s:ToggleCaseInsensitive() {{{2
function! s:ToggleCaseInsensitive() abort
    let fileinfo = s:TagbarState().getCurrent(0)
    if empty(fileinfo)
        return
    endif

    " Save the tag the cursor is currently on
    let curline = line('.')
    let taginfo = s:GetTagInfo(curline, 0)

    match none

    let g:tagbar_case_insensitive = !g:tagbar_case_insensitive

    call fileinfo.sortTags()

    call s:RenderKeepView()
    call s:SetStatusLine()

    " If we were on a tag before sorting then jump to it, otherwise restore
    " the cursor to the current line
    if !empty(taginfo)
        execute taginfo.tline
    else
        execute curline
    endif
endfunction

" s:ToggleAutoclose() {{{2
function! s:ToggleAutoclose() abort
    let g:tagbar_autoclose = !g:tagbar_autoclose
    call s:SetStatusLine()
endfunction

" s:IsValidFile() {{{2
function! s:IsValidFile(fname, ftype) abort
    call s:debug('Checking if file is valid [' . a:fname . ']')

    if a:fname == '' || a:ftype == ''
        call s:debug('Empty filename or type')
        return 0
    endif

    if !filereadable(a:fname) && getbufvar(a:fname, 'netrw_tmpfile') == ''
        call s:debug('File not readable')
        return 0
    endif

    if getbufvar(a:fname, 'tagbar_ignore') == 1
        call s:debug('File is marked as ignored')
        return 0
    endif

    let winnr = bufwinnr(a:fname)
    if winnr != -1 && getwinvar(winnr, '&diff')
        call s:debug('Window is in diff mode')
        return 0
    endif

    if &previewwindow
        call s:debug('In preview window')
        return 0
    endif

    if !has_key(s:known_types, a:ftype)
        if exists('g:tagbar_type_' . a:ftype)
            " Filetype definition must have been specified in an 'ftplugin'
            " file, so load it now
            call s:LoadUserTypeDefs(a:ftype)
        else
            call s:debug('Unsupported filetype: ' . a:ftype)
            return 0
        endif
    endif

    return 1
endfunction

" s:SetStatusLine() {{{2
function! s:SetStatusLine()
    let tagbarwinnr = bufwinnr(s:TagbarBufName())
    if tagbarwinnr == -1
        return
    endif

    " Make sure we're actually in the Tagbar window
    if tagbarwinnr != winnr()
        let in_tagbar = 0
        let prevwinnr = winnr()
        call s:goto_win('p', 1)
        let pprevwinnr = winnr()
        call s:goto_win(tagbarwinnr, 1)
    else
        let in_tagbar = 1
    endif

    if !empty(s:TagbarState().getCurrent(0))
        let fileinfo = s:TagbarState().getCurrent(0)
        let fname = fnamemodify(fileinfo.fpath, ':t')
        let sorted = get(fileinfo.typeinfo, 'sort', g:tagbar_sort)
    else
        let fname = ''
        let sorted = g:tagbar_sort
    endif
    let sortstr = sorted ? 'Name' : 'Order'

    let flags = []
    let flags += exists('w:autoclose') && w:autoclose ? ['c'] : []
    let flags += g:tagbar_autoclose ? ['C'] : []
    let flags += (sorted && g:tagbar_case_insensitive) ? ['i'] : []
    let flags += g:tagbar_hide_nonpublic ? ['v'] : []

    if exists('g:tagbar_status_func')
        let args = [in_tagbar, sortstr, fname, flags]
        let &l:statusline = call(g:tagbar_status_func, args)
    else
        let colour = in_tagbar ? '%#StatusLine#' : '%#StatusLineNC#'
        let flagstr = join(flags, '')
        if flagstr != ''
            let flagstr = '[' . flagstr . '] '
        endif
        let text = colour . '[' . sortstr . '] ' . flagstr . fname
        let &l:statusline = text
    endif

    if !in_tagbar
        call s:goto_win(pprevwinnr, 1)
        call s:goto_win(prevwinnr, 1)
    endif
endfunction

" s:HandleOnlyWindow() {{{2
function! s:HandleOnlyWindow() abort
    let tagbarwinnr = bufwinnr(s:TagbarBufName())
    if tagbarwinnr == -1
        return
    endif

    let vim_quitting = s:vim_quitting
    let s:vim_quitting = 0

    if vim_quitting && !s:HasOpenFileWindows()
        if winnr('$') >= 1
            call s:goto_win(tagbarwinnr, 1)
        endif

        " Before quitting Vim, delete the tagbar buffer so that the '0 mark is
        " correctly set to the previous buffer.
        if tabpagenr('$') == 1
            noautocmd keepalt bdelete
        endif

        try
            try
                quit
            catch /.*/ " This can be E173 and maybe others
                call s:OpenWindow('')
                echoerr v:exception
            endtry
        catch /.*/
            echohl ErrorMsg
            echo v:exception
            echohl None
        endtry
    endif
endfunction

" s:HandleBufDelete() {{{2
function! s:HandleBufDelete(bufname, bufnr) abort
    " Ignore autocmd events generated for "set nobuflisted",
    let nr = str2nr(a:bufnr)
    if bufexists(nr) && !buflisted(nr)
        return
    endif

    let tagbarwinnr = bufwinnr(s:TagbarBufName())
    if tagbarwinnr == -1 || a:bufname =~ '__Tagbar__.*'
        return
    endif

    call s:known_files.rm(fnamemodify(a:bufname, ':p'))

    if !s:HasOpenFileWindows()
        if tabpagenr('$') == 1 && exists('t:tagbar_buf_name')
            " The last normal window closed due to a :bdelete/:bwipeout.
            " In order to get a normal file window back switch to the last
            " alternative buffer (or a new one if there is no alternative
            " buffer), reset the Tagbar-set window options, and then re-open
            " the Tagbar window.

            " Ignore the buffer to be deleted, just in case
            call setbufvar(a:bufname, 'tagbar_ignore', 1)

            if s:last_alt_bufnr == -1 || s:last_alt_bufnr == expand('<abuf>')
                if argc() > 1 && argidx() < argc() - 1
                    " We don't have an alternative buffer, but there are still
                    " files left in the argument list
                    next
                else
                    enew
                endif
            else
                " Save a local copy as the global value will change
                " during buffer switching
                let last_alt_bufnr = s:last_alt_bufnr

                " Ignore the buffer we're switching to for now, it will get
                " processed due to the OpenWindow() call anyway
                call setbufvar(last_alt_bufnr, 'tagbar_ignore', 1)
                execute 'keepalt buffer' last_alt_bufnr
                call setbufvar(last_alt_bufnr, 'tagbar_ignore', 0)
            endif

            " Reset Tagbar window-local options
            set winfixwidth<

            call s:OpenWindow('')
        elseif exists('t:tagbar_buf_name')
            close
        endif
    endif
endfunction

" s:HandleBufWrite() {{{2
function! s:HandleBufWrite(fname) abort
    if index(s:delayed_update_files, a:fname) == -1
        call add(s:delayed_update_files, a:fname)
    endif
endfunction

" s:do_delayed_update() {{{2
function! s:do_delayed_update() abort
    let curfile = s:TagbarState().getCurrent(0)
    if empty(curfile)
        let curfname = ''
    else
        let curfname = curfile.fpath
    endif

    while !empty(s:delayed_update_files)
        let fname = remove(s:delayed_update_files, 0)
        let no_display = curfname !=# fname
        call s:AutoUpdate(fname, 1, no_display)
    endwhile
endfunction

" s:ReopenWindow() {{{2
function! s:ReopenWindow(delbufname) abort
    if expand('<amatch>') == a:delbufname
        return
    endif

    autocmd! TagbarAutoCmds BufWinEnter
    call s:OpenWindow("")
endfunction

" s:HasOpenFileWindows() {{{2
function! s:HasOpenFileWindows() abort
    for i in range(1, winnr('$'))
        let buf = winbufnr(i)

        " skip unlisted buffers, except for netrw
        if !buflisted(buf) && getbufvar(buf, '&filetype') != 'netrw'
            continue
        endif

        " skip temporary buffers with buftype set
        if getbufvar(buf, '&buftype') != ''
            continue
        endif

        " skip the preview window
        if getwinvar(i, '&previewwindow')
            continue
        endif

        return 1
    endfor

    return 0
endfunction

" s:TagbarBufName() {{{2
function! s:TagbarBufName() abort
    if !exists('t:tagbar_buf_name')
        let s:buffer_seqno += 1
        let t:tagbar_buf_name = '__Tagbar__.' . s:buffer_seqno
    endif

    return t:tagbar_buf_name
endfunction

" s:TagbarState() {{{2
function! s:TagbarState() abort
    if !exists('t:tagbar_state')
        let t:tagbar_state = s:state.New()
    endif

    return t:tagbar_state
endfunction

" s:goto_win() {{{2
function! s:goto_win(winnr, ...) abort
    let cmd = type(a:winnr) == type(0) ? a:winnr . 'wincmd w'
                                     \ : 'wincmd ' . a:winnr
    let noauto = a:0 > 0 ? a:1 : 0

    call s:debug("goto_win(): " . cmd . ", " . noauto)

    if noauto
        noautocmd execute cmd
    else
        execute cmd
    endif
endfunction

" s:goto_tagbar() {{{2
function! s:goto_tagbar(...) abort
    let noauto = a:0 > 0 ? a:1 : 0
    call s:goto_win(bufwinnr(s:TagbarBufName()), noauto)
endfunction

" s:mark_window() {{{2
" Mark window with a window-local variable so we can jump back to it even if
" the window numbers have changed.
function! s:mark_window() abort
    let w:tagbar_mark = 1
endfunction

" s:goto_markedwin() {{{2
" Go to a previously marked window and delete the mark.
function! s:goto_markedwin(...) abort
    let noauto = a:0 > 0 ? a:1 : 0
    for window in range(1, winnr('$'))
        call s:goto_win(window, noauto)
        if exists('w:tagbar_mark')
            unlet w:tagbar_mark
            break
        endif
    endfor
endfunction

" s:warning() {{{2
function! s:warning(msg) abort
    echohl WarningMsg
    echomsg a:msg
    echohl None
endfunction

" TagbarBalloonExpr() {{{2
function! TagbarBalloonExpr() abort
    let taginfo = s:GetTagInfo(v:beval_lnum, 1)

    if empty(taginfo)
        return ''
    endif

    return taginfo.getPrototype(0)
endfunction

" Debugging {{{1
" s:StartDebug() {{{2
function! s:StartDebug(filename) abort
    if empty(a:filename)
        let s:debug_file = 'tagbardebug.log'
    else
        let s:debug_file = a:filename
    endif

    " Empty log file
    exe 'redir! > ' . s:debug_file
    redir END

    " Check whether the log file could be created
    if !filewritable(s:debug_file)
        echomsg 'Tagbar: Unable to create log file ' . s:debug_file
        let s:debug_file = ''
        return
    endif

    let s:debug = 1
endfunction

" s:StopDebug() {{{2
function! s:StopDebug() abort
    let s:debug = 0
    let s:debug_file = ''
endfunction

" s:debug() {{{2
if has('reltime')
    function! s:gettime() abort
        let time = split(reltimestr(reltime()), '\.')
        return strftime('%Y-%m-%d %H:%M:%S.', time[0]) . time[1]
    endfunction
else
    function! s:gettime() abort
        return strftime('%Y-%m-%d %H:%M:%S')
    endfunction
endif
function! s:debug(msg) abort
    if s:debug
        execute 'redir >> ' . s:debug_file
        silent echon s:gettime() . ': ' . a:msg . "\n"
        redir END
    endif
endfunction

" Autoload functions {{{1

" Wrappers {{{2
function! tagbar#ToggleWindow(...) abort
    let flags = a:0 > 0 ? a:1 : ''
    call s:ToggleWindow(flags)
endfunction

function! tagbar#OpenWindow(...) abort
    let flags = a:0 > 0 ? a:1 : ''
    call s:OpenWindow(flags)
endfunction

function! tagbar#CloseWindow() abort
    call s:CloseWindow()
endfunction

function! tagbar#SetFoldLevel(level, force) abort
    call s:SetFoldLevel(a:level, a:force)
endfunction

function! tagbar#highlighttag(openfolds, force) abort
    let tagbarwinnr = bufwinnr(s:TagbarBufName())
    if tagbarwinnr == -1
        echohl WarningMsg
        echomsg "Warning: Can't highlight tag, Tagbar window not open"
        echohl None
        return
    endif
    call s:HighlightTag(a:openfolds, a:force)
endfunction

function! tagbar#StartDebug(...) abort
    let filename = a:0 > 0 ? a:1 : ''
    call s:StartDebug(filename)
endfunction

function! tagbar#StopDebug() abort
    call s:StopDebug()
endfunction

function! tagbar#RestoreSession() abort
    call s:RestoreSession()
endfunction

" }}}2

" tagbar#toggle_pause() {{{2
function! tagbar#toggle_pause() abort
    let s:paused = !s:paused

    if s:paused
        call s:TagbarState().setPaused()
    else
        call s:AutoUpdate(fnamemodify(expand('%'), ':p'), 1)
    endif
endfunction

" tagbar#getusertypes() {{{2
function! tagbar#getusertypes() abort
    let userdefs = filter(copy(g:), 'v:key =~ "^tagbar_type_"')

    let typedict = {}
    for [key, val] in items(userdefs)
        let type = substitute(key, '^tagbar_type_', '', '')
        let typedict[type] = val
    endfor

    return typedict
endfunction

" tagbar#autoopen() {{{2
" Automatically open Tagbar if one of the open buffers contains a supported
" file
function! tagbar#autoopen(...) abort
    call s:debug('tagbar#autoopen called [' . bufname('%') . ']')
    let always = a:0 > 0 ? a:1 : 1

    call s:Init(0)

    for bufnr in range(1, bufnr('$'))
        if buflisted(bufnr) && (always || bufwinnr(bufnr) != -1)
            let ftype = s:DetectFiletype(bufnr)
            if s:IsValidFile(bufname(bufnr), ftype)
                call s:OpenWindow('')
                call s:debug('tagbar#autoopen finished after finding valid ' .
                           \ 'file [' . bufname(bufnr) . ']')
                return
            endif
        endif
    endfor

    call s:debug('tagbar#autoopen finished without finding valid file')
endfunction

" tagbar#currenttag() {{{2
function! tagbar#currenttag(fmt, default, ...) abort
    " Indicate that the statusline functionality is being used. This prevents
    " the CloseWindow() function from removing the autocommands.
    let s:statusline_in_use = 1

    if a:0 > 0
        " also test for non-zero value for backwards compatibility
        let longsig   = a:1 =~# 's' || (type(a:1) == type(0) && a:1 != 0)
        let fullpath  = a:1 =~# 'f'
        let prototype = a:1 =~# 'p'
    else
        let longsig   = 0
        let fullpath  = 0
        let prototype = 0
    endif

    if !s:Init(1)
        return a:default
    endif

    let tag = s:GetNearbyTag(0, 1)

    if !empty(tag)
        if prototype
            return tag.getPrototype(1)
        else
            return printf(a:fmt, tag.str(longsig, fullpath))
        endif
    else
        return a:default
    endif
endfunction

" tagbar#currentfile() {{{2
function! tagbar#currentfile() abort
    let filename = ''

    if !empty(s:TagbarState().getCurrent(1))
        let filename = fnamemodify(s:TagbarState().getCurrent(1).fpath, ':t')
    endif

    return filename
endfunction

" tagbar#gettypeconfig() {{{2
function! tagbar#gettypeconfig(type) abort
    if !s:Init(1)
        return ''
    endif

    let typeinfo = get(s:known_types, a:type, {})

    if empty(typeinfo)
        call s:warning('Unknown type ' . a:type . '!')
        return
    endif

    let output = "let g:tagbar_type_" . a:type . " = {\n"

    let output .= "    \\ 'kinds' : [\n"
    for kind in typeinfo.kinds
        let output .= "        \\ '" . kind.short . ":" . kind.long
        if kind.fold || !kind.stl
            if kind.fold
                let output .= ":1"
            else
                let output .= ":0"
            endif
        endif
        if !kind.stl
            let output .= ":0"
        endif
        let output .= "',\n"
    endfor
    let output .= "    \\ ],\n"

    let output .= "\\ }"

    silent put =output
endfunction

" tagbar#inspect() {{{2
function! tagbar#inspect(var) abort
    return get(s:, a:var)
endfunction

" Modeline {{{1
" vim: ts=8 sw=4 sts=4 et foldenable foldmethod=marker foldcolumn=1
