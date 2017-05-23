" ============================================================================
" File:        NERD_commenter.vim
" Description: vim global plugin that provides easy code commenting
" Author:      Martin Grenfell <martin.grenfell at gmail dot com>
" Maintainer:  Caleb Maclennan <caleb@alerque.com>
" Version:     2.4.0
" Last Change: Tue May 24 14:03:29 EEST 2016
" License:     This program is free software. It comes without any warranty,
"              to the extent permitted by applicable law. You can redistribute
"              it and/or modify it under the terms of the Do What The Fuck You
"              Want To Public License, Version 2, as published by Sam Hocevar.
"              See http://sam.zoy.org/wtfpl/COPYING for more details.
"
" ============================================================================

" Section: script init stuff {{{1
if exists("loaded_nerd_comments")
    finish
endif
if v:version < 700
    echoerr "NERDCommenter: this plugin requires vim >= 7. DOWNLOAD IT! You'll thank me later!"
    finish
endif
let loaded_nerd_comments = 1

" Function: s:InitVariable() function {{{2
" This function is used to initialise a given variable to a given value. The
" variable is only initialised if it does not exist prior
"
" Args:
"   -var: the name of the var to be initialised
"   -value: the value to initialise var to
"
" Returns:
"   1 if the var is set, 0 otherwise
function s:InitVariable(var, value)
    if !exists(a:var)
        execute 'let ' . a:var . ' = ' . "'" . a:value . "'"
        return 1
    endif
    return 0
endfunction

" Section: space string init{{{2
" When putting spaces after the left delimiter and before the right we use
" s:spaceStr for the space char. This way we can make it add anything after
" the left and before the right by modifying this variable
let s:spaceStr = ' '
let s:lenSpaceStr = strlen(s:spaceStr)

" Section: variable initialization {{{2
call s:InitVariable("g:NERDAllowAnyVisualDelims", 1)
call s:InitVariable("g:NERDBlockComIgnoreEmpty", 0)
call s:InitVariable("g:NERDCommentWholeLinesInVMode", 0)
call s:InitVariable("g:NERDCommentEmptyLines", 0)
call s:InitVariable("g:NERDCompactSexyComs", 0)
call s:InitVariable("g:NERDCreateDefaultMappings", 1)
call s:InitVariable("g:NERDDefaultNesting", 1)
call s:InitVariable("g:NERDMenuMode", 3)
call s:InitVariable("g:NERDLPlace", "[>")
call s:InitVariable("g:NERDUsePlaceHolders", 1)
call s:InitVariable("g:NERDRemoveAltComs", 1)
call s:InitVariable("g:NERDRemoveExtraSpaces", 0)
call s:InitVariable("g:NERDRPlace", "<]")
call s:InitVariable("g:NERDSpaceDelims", 0)
call s:InitVariable("g:NERDDefaultAlign", "none")
call s:InitVariable("g:NERDTrimTrailingWhitespace", 0)

let s:NERDFileNameEscape="[]#*$%'\" ?`!&();<>\\"

let s:delimiterMap = {
    \ 'aap': { 'left': '#' },
    \ 'abc': { 'left': '%' },
    \ 'acedb': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'actionscript': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'ada': { 'left': '--', 'leftAlt': '--  ' },
    \ 'ahdl': { 'left': '--' },
    \ 'ahk': { 'left': ';', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'amiga': { 'left': ';' },
    \ 'aml': { 'left': '/*' },
    \ 'ampl': { 'left': '#' },
    \ 'ansible': { 'left': '#' },
    \ 'apache': { 'left': '#' },
    \ 'apachestyle': { 'left': '#' },
    \ 'applescript': { 'left': '--', 'leftAlt': '(*', 'rightAlt': '*)' },
    \ 'armasm': { 'left': ';' },
    \ 'asciidoc': { 'left': '//' },
    \ 'asm': { 'left': ';', 'leftAlt': '#' },
    \ 'asm68k': { 'left': ';' },
    \ 'asn': { 'left': '--' },
    \ 'asp': { 'left': '%', 'leftAlt': '%*', 'rightAlt': '*%' },
    \ 'aspvbs': { 'left': '''', 'leftAlt': '<!--', 'rightAlt': '-->' },
    \ 'asterisk': { 'left': ';' },
    \ 'asy': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'atlas': { 'left': 'C', 'right': '$' },
    \ 'augeas': { 'left': '(*', 'right': '*)' },
    \ 'autohotkey': { 'left': ';', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'autoit': { 'left': ';' },
    \ 'ave': { 'left': "'" },
    \ 'awk': { 'left': '#' },
    \ 'basic': { 'left': "'", 'leftAlt': 'REM ' },
    \ 'bbx': { 'left': '%' },
    \ 'bc': { 'left': '#' },
    \ 'bib': { 'left': '//' },
    \ 'bindzone': { 'left': ';' },
    \ 'blade': { 'left': '{{--', 'right': '--}}' },
    \ 'bst': { 'left': '%' },
    \ 'btm': { 'left': '::' },
    \ 'c': { 'left': '/*', 'right': '*/', 'leftAlt': '//' },
    \ 'cabal': { 'left': '--' },
    \ 'calibre': { 'left': '//' },
    \ 'caos': { 'left': '*' },
    \ 'catalog': { 'left': '--', 'right': '--' },
    \ 'cf': { 'left': '<!---', 'right': '--->' },
    \ 'cfg': { 'left': '#' },
    \ 'cg': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'ch': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'cl': { 'left': '#' },
    \ 'clean': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'clipper': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'clojure': { 'left': ';' },
    \ 'cmake': { 'left': '#' },
    \ 'coffee': { 'left': '#', 'leftAlt': '###', 'rightAlt': '###' },
    \ 'conkyrc': { 'left': '#' },
    \ 'context': { 'left': '%', 'leftAlt': '--' },
    \ 'coq': { 'left': '(*', 'right': '*)' },
    \ 'cpp': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'crontab': { 'left': '#' },
    \ 'cs': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'csp': { 'left': '--' },
    \ 'cterm': { 'left': '*' },
    \ 'cucumber': { 'left': '#' },
    \ 'cuda': { 'left': '/*', 'right': '*/', 'leftAlt': '//' },
    \ 'cvs': { 'left': 'CVS:' },
    \ 'cython': { 'left': '# ', 'leftAlt': '#' },
    \ 'd': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'dakota': { 'left': '#' },
    \ 'dcl': { 'left': '$!' },
    \ 'debcontrol': { 'left': '#' },
    \ 'debsources': { 'left': '#' },
    \ 'def': { 'left': ';' },
    \ 'desktop': { 'left': '#' },
    \ 'dhcpd': { 'left': '#' },
    \ 'diff': { 'left': '#' },
    \ 'django': { 'left': '<!--', 'right': '-->', 'leftAlt': '{#', 'rightAlt': '#}' },
    \ 'dns': { 'left': ';' },
    \ 'docbk': { 'left': '<!--', 'right': '-->' },
    \ 'dockerfile': { 'left': '#' },
    \ 'dosbatch': { 'left': 'REM ', 'leftAlt': '::' },
    \ 'dosini': { 'left': ';' },
    \ 'dot': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'dracula': { 'left': ';' },
    \ 'dsl': { 'left': ';' },
    \ 'dtml': { 'left': '<dtml-comment>', 'right': '</dtml-comment>' },
    \ 'dylan': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'ebuild': { 'left': '#' },
    \ 'ecd': { 'left': '#' },
    \ 'eclass': { 'left': '#' },
    \ 'eiffel': { 'left': '--' },
    \ 'elf': { 'left': "'" },
    \ 'elixir': { 'left': '#' },
    \ 'elm': { 'left': '--', 'leftAlt': '{--', 'rightAlt': '--}' },
    \ 'elmfilt': { 'left': '#' },
    \ 'ember-script': { 'left': '#' },
    \ 'emblem': { 'left': '/' },
    \ 'erlang': { 'left': '%', 'leftAlt': '%%' },
    \ 'eruby': { 'left': '<%#', 'right': '%>', 'leftAlt': '<!--', 'rightAlt': '-->' },
    \ 'esmtprc': { 'left': '#' },
    \ 'expect': { 'left': '#' },
    \ 'exports': { 'left': '#' },
    \ 'factor': { 'left': '! ', 'leftAlt': '!# ' },
    \ 'fancy': { 'left': '#' },
    \ 'fgl': { 'left': '#' },
    \ 'focexec': { 'left': '-*' },
    \ 'form': { 'left': '*' },
    \ 'fortran': { 'left': '!' },
    \ 'foxpro': { 'left': '*' },
    \ 'fsharp': { 'left': '(*', 'right': '*)', 'leftAlt': '//' },
    \ 'fstab': { 'left': '#' },
    \ 'fvwm': { 'left': '#' },
    \ 'fx': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'gams': { 'left': '*' },
    \ 'gdb': { 'left': '#' },
    \ 'gdmo': { 'left': '--' },
    \ 'geek': { 'left': 'GEEK_COMMENT:' },
    \ 'genshi': { 'left': '<!--', 'right': '-->', 'leftAlt': '{#', 'rightAlt': '#}' },
    \ 'gentoo-conf-d': { 'left': '#' },
    \ 'gentoo-env-d': { 'left': '#' },
    \ 'gentoo-init-d': { 'left': '#' },
    \ 'gentoo-make-conf': { 'left': '#' },
    \ 'gentoo-package-keywords': { 'left': '#' },
    \ 'gentoo-package-mask': { 'left': '#' },
    \ 'gentoo-package-use': { 'left': '#' },
    \ 'gitcommit': { 'left': '#' },
    \ 'gitconfig': { 'left': ';' },
    \ 'gitignore': { 'left': '#' },
    \ 'gitrebase': { 'left': '#' },
    \ 'glsl': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'gnuplot': { 'left': '#' },
    \ 'go': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'groovy': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'gsp': { 'left': '<%--', 'right': '--%>', 'leftAlt': '<!--', 'rightAlt': '-->' },
    \ 'gtkrc': { 'left': '#' },
    \ 'h': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'haml': { 'left': '-#', 'leftAlt': '/' },
    \ 'handlebars': { 'left': '{{!-- ', 'right': ' --}}' },
    \ 'haskell': { 'left': '{-', 'right': '-}', 'nested': 1, 'leftAlt': '--', 'nestedAlt': 1 },
    \ 'haxe': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'hb': { 'left': '#' },
    \ 'hbs': { 'left': '{{!-- ', 'right': ' --}}' },
    \ 'hercules': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'hive': { 'left': '-- ' },
    \ 'hog': { 'left': '#' },
    \ 'hostsaccess': { 'left': '#' },
    \ 'htmlcheetah': { 'left': '##' },
    \ 'htmldjango': { 'left': '<!--', 'right': '-->', 'leftAlt': '{#', 'rightAlt': '#}' },
    \ 'htmlos': { 'left': '#', 'right': '/#' },
    \ 'hxml': { 'left': '#' },
    \ 'hyphy': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'ia64': { 'left': '#' },
    \ 'icon': { 'left': '#' },
    \ 'idl': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'idlang': { 'left': ';' },
    \ 'idris': { 'leftAlt': '--', 'left': '{-', 'right': '-}' },
    \ 'incar': { 'left': '!' },
    \ 'inform': { 'left': '!' },
    \ 'inittab': { 'left': '#' },
    \ 'ishd': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'iss': { 'left': ';' },
    \ 'ist': { 'left': '%' },
    \ 'jade': { 'left': '//-', 'leftAlt': '//' },
    \ 'java': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'javacc': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'javascript': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'javascript.jquery': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'jess': { 'left': ';' },
    \ 'jgraph': { 'left': '(*', 'right': '*)' },
    \ 'jinja': { 'left': '<!--', 'right': '-->', 'leftAlt': '{#', 'rightAlt': '#}' },
    \ 'jproperties': { 'left': '#' },
    \ 'jsp': { 'left': '<%--', 'right': '--%>' },
    \ 'julia': { 'left': '#' },
    \ 'kix': { 'left': ';' },
    \ 'kscript': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'lace': { 'left': '--' },
    \ 'laravel': { 'left': '{{--', 'right': '--}}' },
    \ 'ldif': { 'left': '#' },
    \ 'less': { 'left': '/*', 'right': '*/' },
    \ 'lhaskell': { 'left': '>{-', 'right': '-}', 'leftAlt': '>-- ' },
    \ 'lilo': { 'left': '#' },
    \ 'lilypond': { 'left': '%' },
    \ 'liquid': { 'left': '{% comment %}', 'right': '{% endcomment %}' },
    \ 'lisp': { 'left': ';', 'nested': 1, 'leftAlt': '#|', 'rightAlt': '|#', 'nestedAlt': 1 },
    \ 'llvm': { 'left': ';' },
    \ 'lotos': { 'left': '(*', 'right': '*)' },
    \ 'lout': { 'left': '#' },
    \ 'lpc': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'lprolog': { 'left': '%' },
    \ 'lscript': { 'left': "'" },
    \ 'lss': { 'left': '#' },
    \ 'lua': { 'left': '--', 'leftAlt': '--[[', 'rightAlt': ']]' },
    \ 'lynx': { 'left': '#' },
    \ 'lytex': { 'left': '%' },
    \ 'm4': { 'left': 'dnl ' },
    \ 'mail': { 'left': '> ' },
    \ 'mako': { 'left': '##' },
    \ 'man': { 'left': '."' },
    \ 'map': { 'left': '%' },
    \ 'maple': { 'left': '#' },
    \ 'markdown': { 'left': '<!--', 'right': '-->' },
    \ 'masm': { 'left': ';' },
    \ 'mason': { 'left': '<% #', 'right': '%>' },
    \ 'master': { 'left': '$' },
    \ 'matlab': { 'left': '%', 'leftAlt': '%{', 'rightAlt': '%}' },
    \ 'mel': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'meson': { 'left': '#' },
    \ 'mib': { 'left': '--' },
    \ 'mips': { 'left': '#' },
    \ 'mirah': {'left': '#' },
    \ 'mkd': { 'left': '<!---', 'right': '-->' },
    \ 'mma': { 'left': '(*', 'right': '*)' },
    \ 'model': { 'left': '$', 'right': '$' },
    \ 'moduala.': { 'left': '(*', 'right': '*)' },
    \ 'modula2': { 'left': '(*', 'right': '*)' },
    \ 'modula3': { 'left': '(*', 'right': '*)' },
    \ 'molpro': { 'left': '!' },
    \ 'monk': { 'left': ';' },
    \ 'mush': { 'left': '#' },
    \ 'mustache': { 'left': '{{!', 'right': '}}' },
    \ 'nagios': { 'left': ';' },
    \ 'named': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'nasm': { 'left': ';' },
    \ 'nastran': { 'left': '$' },
    \ 'natural': { 'left': '/*' },
    \ 'ncf': { 'left': ';' },
    \ 'newlisp': { 'left': ';' },
    \ 'nginx': { 'left': '#' },
    \ 'nimrod': { 'left': '#' },
    \ 'nroff': { 'left': '\"' },
    \ 'nsis': { 'left': '#' },
    \ 'ntp': { 'left': '#' },
    \ 'objc': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'objcpp': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'objj': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'ocaml': { 'left': '(*', 'right': '*)', 'nested': 1 },
    \ 'occam': { 'left': '--' },
    \ 'octave': { 'left': '%', 'leftAlt': '#' },
    \ 'omlet': { 'left': '(*', 'right': '*)' },
    \ 'omnimark': { 'left': ';' },
    \ 'ooc': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'openroad': { 'left': '//' },
    \ 'opl': { 'left': "REM" },
    \ 'ora': { 'left': '#' },
    \ 'ox': { 'left': '//' },
    \ 'paludis-use-conf': { 'left': '#' },
    \ 'pandoc': { 'left': '<!--', 'right': '-->' },
    \ 'pascal': { 'left': '{', 'right': '}', 'leftAlt': '(*', 'rightAlt': '*)' },
    \ 'patran': { 'left': '$', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'pcap': { 'left': '#' },
    \ 'pccts': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'pdf': { 'left': '%' },
    \ 'perl': { 'left': '#' },
    \ 'pfmain': { 'left': '//' },
    \ 'php': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'pic': { 'left': ';' },
    \ 'pike': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'pilrc': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'pine': { 'left': '#' },
    \ 'plm': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'plsql': { 'left': '-- ', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'po': { 'left': '#' },
    \ 'poscar': { 'left': '!' },
    \ 'postscr': { 'left': '%' },
    \ 'pov': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'povini': { 'left': ';' },
    \ 'ppd': { 'left': '%' },
    \ 'ppwiz': { 'left': ';;' },
    \ 'privoxy': { 'left': '#' },
    \ 'processing': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'prolog': { 'left': '%', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'ps1': { 'left': '#' },
    \ 'psf': { 'left': '#' },
    \ 'ptcap': { 'left': '#' },
    \ 'pug': { 'left': '//-', 'leftAlt': '//' },
    \ 'puppet': { 'left': '#' },
    \ 'pyrex': { 'left': '# ', 'leftAlt': '#' },
    \ 'python': { 'left': '# ', 'leftAlt': '#' },
    \ 'r': { 'left': '#', 'leftAlt': '#''' },
    \ 'racket': { 'left': ';', 'nested': 1, 'leftAlt': '#|', 'rightAlt': '|#', 'nestedAlt': 1 },
    \ 'radiance': { 'left': '#' },
    \ 'ratpoison': { 'left': '#' },
    \ 'rc': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'rebol': { 'left': ';' },
    \ 'registry': { 'left': ';' },
    \ 'remind': { 'left': '#' },
    \ 'resolv': { 'left': '#' },
    \ 'rgb': { 'left': '!' },
    \ 'rib': { 'left': '#' },
    \ 'rmd': { 'left': '#' },
    \ 'robots': { 'left': '#' },
    \ 'rspec': { 'left': '#' },
    \ 'ruby': { 'left': '#', 'leftAlt': '=begin', 'rightAlt': '=end' },
    \ 'rust': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'sa': { 'left': '--' },
    \ 'samba': { 'left': ';', 'leftAlt': '#' },
    \ 'sass': { 'left': '//', 'leftAlt': '/*' },
    \ 'sather': { 'left': '--' },
    \ 'scala': { 'left': '//', 'nested': 1, 'leftAlt': '/*', 'rightAlt': '*/', 'nestedAlt': 1 },
    \ 'scheme': { 'left': ';', 'nested': 1, 'leftAlt': '#|', 'rightAlt': '|#', 'nestedAlt': 1 },
    \ 'scilab': { 'left': '//' },
    \ 'scons': { 'left': '#' },
    \ 'scsh': { 'left': ';' },
    \ 'scss': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'sed': { 'left': '#' },
    \ 'sgmldecl': { 'left': '--', 'right': '--' },
    \ 'sgmllnx': { 'left': '<!--', 'right': '-->' },
    \ 'sh': { 'left': '#' },
    \ 'shader_test': { 'left': '#' },
    \ 'sicad': { 'left': '*' },
    \ 'sile': { 'left': '%' },
    \ 'simula': { 'left': '%', 'leftAlt': '--' },
    \ 'sinda': { 'left': '$' },
    \ 'skill': { 'left': ';' },
    \ 'slang': { 'left': '%' },
    \ 'slice': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'slim': { 'left': '/', 'leftAlt': '/!' },
    \ 'slrnrc': { 'left': '%' },
    \ 'sls': { 'left': '#' },
    \ 'sm': { 'left': '#' },
    \ 'smarty': { 'left': '{*', 'right': '*}' },
    \ 'smil': { 'left': '<!', 'right': '>' },
    \ 'smith': { 'left': ';' },
    \ 'sml': { 'left': '(*', 'right': '*)', 'nested': 1 },
    \ 'snippets': { 'left': '#' },
    \ 'snnsnet': { 'left': '#' },
    \ 'snnspat': { 'left': '#' },
    \ 'snnsres': { 'left': '#' },
    \ 'snobol4': { 'left': '*' },
    \ 'spec': { 'left': '#' },
    \ 'specman': { 'left': '//' },
    \ 'spectre': { 'left': '//', 'leftAlt': '*' },
    \ 'spice': { 'left': '$' },
    \ 'spin': { 'left': '''', 'leftAlt': '{', 'rightAlt': '}' },
    \ 'sql': { 'left': '-- ' },
    \ 'sqlforms': { 'left': '-- ' },
    \ 'sqlj': { 'left': '-- ' },
    \ 'sqr': { 'left': '!' },
    \ 'squid': { 'left': '#' },
    \ 'ss': { 'left': ';', 'leftAlt': '#|', 'rightAlt': '|#' },
    \ 'sshdconfig': { 'left': '#' },
    \ 'st': { 'left': '"' },
    \ 'stan': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'stp': { 'left': '/*', 'right': '*/', 'leftAlt': '//' },
    \ 'supercollider': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'swift': { 'left': '/*', 'right': '*/', 'leftAlt': '//' },
    \ 'systemverilog': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'tads': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'tags': { 'left': ';' },
    \ 'tak': { 'left': '$' },
    \ 'tasm': { 'left': ';' },
    \ 'tcl': { 'left': '#' },
    \ 'teak': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'terraform': { 'left': '#', 'leftAlt': '/*', 'rightAlt': '*/'  },
    \ 'tex': { 'left': '%' },
    \ 'texinfo': { 'left': "@c " },
    \ 'texmf': { 'left': '%' },
    \ 'tf': { 'left': ';' },
    \ 'tidy': { 'left': '#' },
    \ 'tli': { 'left': '#' },
    \ 'tmux': { 'left': '#' },
    \ 'toml': { 'left': '#' },
    \ 'trasys': { 'left': "$" },
    \ 'tsalt': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'tsscl': { 'left': '#' },
    \ 'tssgm': { 'left': "comment = '", 'right': "'" },
    \ 'tup': { 'left': '#' },
    \ 'twig': { 'left': '{#', 'right': '#}' },
    \ 'txt2tags': { 'left': '%' },
    \ 'typescript': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'uc': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'uil': { 'left': '!' },
    \ 'upstart': { 'left': '#' },
    \ 'vala': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'vasp': { 'left': '!' },
    \ 'vb': { 'left': "'" },
    \ 'velocity': { 'left': "##", 'right': "", 'leftAlt': '#*', 'rightAlt': '*#' },
    \ 'vera': { 'left': '/*', 'right': '*/', 'leftAlt': '//' },
    \ 'verilog': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'verilog_systemverilog': { 'left': '//', 'leftAlt': '/*', 'rightAlt': '*/' },
    \ 'vgrindefs': { 'left': '#' },
    \ 'vhdl': { 'left': '--' },
    \ 'vimperator': { 'left': '"' },
    \ 'virata': { 'left': '%' },
    \ 'vrml': { 'left': '#' },
    \ 'vsejcl': { 'left': '/*' },
    \ 'webmacro': { 'left': '##' },
    \ 'wget': { 'left': '#' },
    \ 'wikipedia': { 'left': '<!--', 'right': '-->' },
    \ 'winbatch': { 'left': ';' },
    \ 'wml': { 'left': '#' },
    \ 'wvdial': { 'left': ';' },
    \ 'xdefaults': { 'left': '!' },
    \ 'xkb': { 'left': '//' },
    \ 'xmath': { 'left': '#' },
    \ 'xpm2': { 'left': '!' },
    \ 'xquery': { 'left': '(:', 'right': ':)' },
    \ 'yaml': { 'left': '#' },
    \ 'z8a': { 'left': ';' }
    \ }

let g:NERDDelimiterMap = s:delimiterMap

if exists("g:NERDCustomDelimiters")
    call extend(s:delimiterMap, g:NERDCustomDelimiters)
endif

" Section: Comment mapping functions, autocommands and commands {{{1
" ============================================================================
" Section: Comment enabler autocommands {{{2
" ============================================================================

augroup NERDCommenter

    "if the user enters a buffer or reads a buffer then we gotta set up
    "the comment delimiters for that new filetype
    autocmd BufEnter,BufRead * :call s:SetUpForNewFiletype(&filetype, 0)

    "if the filetype of a buffer changes, force the script to reset the
    "delimiters for the buffer
    autocmd Filetype * :call s:SetUpForNewFiletype(&filetype, 1)
augroup END


" Function: s:SetUpForNewFiletype(filetype) function {{{2
" This function is responsible for setting up buffer scoped variables for the
" given filetype.
"
" Args:
"   -filetype: the filetype to set delimiters for
"   -forceReset: 1 if the delimiters should be reset if they have already be
"    set for this buffer.
"
function s:SetUpForNewFiletype(filetype, forceReset)
    let ft = a:filetype

    "for compound filetypes, if we don't know how to handle the full filetype
    "then break it down and use the first part that we know how to handle
    if ft =~ '\.' && !has_key(s:delimiterMap, ft)
        let filetypes = split(a:filetype, '\.')
        for i in filetypes
            if has_key(s:delimiterMap, i)
                let ft = i
                break
            endif
        endfor
    endif

    let b:NERDSexyComMarker = ''

    if has_key(s:delimiterMap, ft)
        let b:NERDCommenterDelims = s:delimiterMap[ft]
        for i in ['left', 'leftAlt', 'right', 'rightAlt']
            if !has_key(b:NERDCommenterDelims, i)
                let b:NERDCommenterDelims[i] = ''
            endif
        endfor
        for i in ['nested', 'nestedAlt']
            if !has_key(b:NERDCommenterDelims, i)
                let b:NERDCommenterDelims[i] = 0
            endif
        endfor
        " if g:NERD_<filetype>_alt_style is defined, use the alternate style
        let b:NERDCommenterFirstInit = getbufvar(1,"NERDCommenterFirstInit")
        if exists('g:NERDAltDelims_'.ft) && eval('g:NERDAltDelims_'.ft) && !b:NERDCommenterFirstInit
            call s:SwitchToAlternativeDelimiters(0)
            let b:NERDCommenterFirstInit = 1
        endif
    else
        let b:NERDCommenterDelims = s:CreateDelimMapFromCms()
    endif

endfunction

function s:CreateDelimMapFromCms()
    if &ft == '' && exists('g:NERDDefaultDelims')
        let delims = g:NERDDefaultDelims
        for i in ['left', 'leftAlt', 'right', 'rightAlt']
            if !has_key(delims, i)
                let delims[i] = ''
            endif
        endfor
        return delims
    endif
    return {
        \ 'left': substitute(&commentstring, '\([^ \t]*\)\s*%s.*', '\1', ''),
        \ 'right': substitute(&commentstring, '.*%s\s*\(.*\)', '\1', 'g'),
        \ 'nested': 0,
        \ 'leftAlt': '',
        \ 'rightAlt': '',
        \ 'nestedAlt': 0}
endfunction

" Function: s:SwitchToAlternativeDelimiters(printMsgs) function {{{2
" This function is used to swap the delimiters that are being used to the
" alternative delimiters for that filetype. For example, if a c++ file is
" being edited and // comments are being used, after this function is called
" /**/ comments will be used.
"
" Args:
"   -printMsgs: if this is 1 then a message is echoed to the user telling them
"    if this function changed the delimiters or not
function s:SwitchToAlternativeDelimiters(printMsgs)
    if exists('*NERDCommenter_before')
        exe "call NERDCommenter_before()"
    endif
    "if both of the alternative delimiters are empty then there is no
    "alternative comment style so bail out
    if b:NERDCommenterDelims['leftAlt'] == '' && b:NERDCommenterDelims['rightAlt'] == ''
        if a:printMsgs
            call s:NerdEcho("Cannot use alternative delimiters, none are specified", 0)
        endif
        return 0
    endif

    "save the current delimiters
    let tempLeft = s:Left()
    let tempRight = s:Right()
    let tempNested = s:Nested()

    "swap current delimiters for alternative
    let b:NERDCommenterDelims['left'] = b:NERDCommenterDelims['leftAlt']
    let b:NERDCommenterDelims['right'] = b:NERDCommenterDelims['rightAlt']
    "set information on whether these are nested
    let b:NERDCommenterDelims['nested'] = b:NERDCommenterDelims['nestedAlt']

    "set the previously current delimiters to be the new alternative ones
    let b:NERDCommenterDelims['leftAlt'] = tempLeft
    let b:NERDCommenterDelims['rightAlt'] = tempRight
    let b:NERDCommenterDelims['nestedAlt'] = tempNested

    "tell the user what comment delimiters they are now using
    if a:printMsgs
        call s:NerdEcho("Now using " . s:Left() . " " . s:Right() . " to delimit comments", 1)
    endif

    if exists('*NERDCommenter_after')
        exe "call NERDCommenter_after()"
    endif

    return 1
endfunction

" Section: Comment delimiter add/removal functions {{{1
" ============================================================================
" Function: s:AppendCommentToLine(){{{2
" This function appends comment delimiters at the EOL and places the cursor in
" position to start typing the comment
function s:AppendCommentToLine()
    let left = s:Left({'space': 1})
    let right = s:Right({'space': 1})

    " get the length of the right delimiter
    let lenRight = strlen(right)

    let isLineEmpty = strlen(getline(".")) == 0
    let insOrApp = (isLineEmpty==1 ? 'i' : 'A')

    "stick the delimiters down at the end of the line. We have to format the
    "comment with spaces as appropriate
    execute ":normal! " . insOrApp . (isLineEmpty ? '' : ' ') . left . right

    " if there is a right delimiter then we gotta move the cursor left
    " by the length of the right delimiter so we insert between the delimiters
    if lenRight > 0
        let leftMoveAmount = lenRight - 1
        execute ":normal! " . leftMoveAmount . "h"
        startinsert
    else
        startinsert!
    endif
endfunction

" Function: s:CommentBlock(top, bottom, lSide, rSide, forceNested ) {{{2
" This function is used to comment out a region of code. This region is
" specified as a bounding box by arguments to the function.
"
" Args:
"   -top: the line number for the top line of code in the region
"   -bottom: the line number for the bottom line of code in the region
"   -lSide: the column number for the left most column in the region
"   -rSide: the column number for the right most column in the region
"   -forceNested: a flag indicating whether comments should be nested
function s:CommentBlock(top, bottom, lSide, rSide, forceNested )
    " we need to create local copies of these arguments so we can modify them
    let top = a:top
    let bottom = a:bottom
    let lSide = a:lSide
    let rSide = a:rSide

    "if the top or bottom line starts with tabs we have to adjust the left and
    "right boundaries so that they are set as though the tabs were spaces
    let topline = getline(top)
    let bottomline = getline(bottom)
    if s:HasLeadingTabs(topline, bottomline)

        "find out how many tabs are in the top line and adjust the left
        "boundary accordingly
        let numTabs = s:NumberOfLeadingTabs(topline)
        if lSide < numTabs
            let lSide = &ts * lSide
        else
            let lSide = (lSide - numTabs) + (&ts * numTabs)
        endif

        "find out how many tabs are in the bottom line and adjust the right
        "boundary accordingly
        let numTabs = s:NumberOfLeadingTabs(bottomline)
        let rSide = (rSide - numTabs) + (&ts * numTabs)
    endif

    "we must check that bottom IS actually below top, if it is not then we
    "swap top and bottom. Similarly for left and right.
    if bottom < top
        let temp = top
        let top = bottom
        let bottom = top
    endif
    if rSide < lSide
        let temp = lSide
        let lSide = rSide
        let rSide = temp
    endif

    "if the current delimiters aren't multipart then we will switch to the
    "alternative delimiters (if THEY are) as the comment will be better and more
    "accurate with multipart delimiters
    let switchedDelims = 0
    if !s:Multipart() && g:NERDAllowAnyVisualDelims && s:AltMultipart()
        let switchedDelims = 1
        call s:SwitchToAlternativeDelimiters(0)
    endif

    "start the commenting from the top and keep commenting till we reach the
    "bottom
    let currentLine=top
    while currentLine <= bottom

        "check if we are allowed to comment this line
        if s:CanCommentLine(a:forceNested, currentLine)

            "convert the leading tabs into spaces
            let theLine = getline(currentLine)
            let lineHasLeadTabs = s:HasLeadingTabs(theLine)
            if lineHasLeadTabs
                let theLine = s:ConvertLeadingTabsToSpaces(theLine)
            endif

            "don't comment lines that begin after the right boundary of the
            "block unless the user has specified to do so
            if theLine !~ '^ \{' . rSide . '\}' || !g:NERDBlockComIgnoreEmpty

                "attempt to place the cursor in on the left of the boundary box,
                "then check if we were successful, if not then we cant comment this
                "line
                call setline(currentLine, theLine)
                if s:CanPlaceCursor(currentLine, lSide)

                    let leftSpaced = s:Left({'space': 1})
                    let rightSpaced = s:Right({'space': 1})

                    "stick the left delimiter down
                    let theLine = strpart(theLine, 0, lSide-1) . leftSpaced . strpart(theLine, lSide-1)

                    if s:Multipart()
                        "stick the right delimiter down
                        let theLine = strpart(theLine, 0, rSide+strlen(leftSpaced)) . rightSpaced . strpart(theLine, rSide+strlen(leftSpaced))

                        let firstLeftDelim = s:FindDelimiterIndex(s:Left(), theLine)
                        let lastRightDelim = s:LastIndexOfDelim(s:Right(), theLine)

                        if firstLeftDelim != -1 && lastRightDelim != -1
                            let searchStr = strpart(theLine, 0, lastRightDelim)
                            let searchStr = strpart(searchStr, firstLeftDelim+strlen(s:Left()))

                            "replace the outer most delimiters in searchStr with
                            "place-holders
                            let theLineWithPlaceHolders = s:ReplaceDelims(s:Left(), s:Right(), g:NERDLPlace, g:NERDRPlace, searchStr)

                            "add the right delimiter onto the line
                            let theLine = strpart(theLine, 0, firstLeftDelim+strlen(s:Left())) . theLineWithPlaceHolders . strpart(theLine, lastRightDelim)
                        endif
                    endif
                endif
            endif

            "restore tabs if needed
            if lineHasLeadTabs
                let theLine = s:ConvertLeadingSpacesToTabs(theLine)
            endif

            if g:NERDTrimTrailingWhitespace == 1
              let theLine = s:TrimTrailingWhitespace(theLine)
            endif

            call setline(currentLine, theLine)
        endif

        let currentLine = currentLine + 1
    endwhile

    "if we switched delimiterss then we gotta go back to what they were before
    if switchedDelims == 1
        call s:SwitchToAlternativeDelimiters(0)
    endif
endfunction

" Function: s:CommentLines(forceNested, alignLeft, alignRight, firstLine, lastLine) {{{2
" This function comments a range of lines.
"
" Args:
"   -forceNested: a flag indicating whether the called is requesting the comment
"    to be nested if need be
"   -align: should be "left", "start", "both" or "none"
"   -firstLine/lastLine: the top and bottom lines to comment
function s:CommentLines(forceNested, align, firstLine, lastLine)
    " we need to get the left and right indexes of the leftmost char in the
    " block of of lines and the right most char so that we can do alignment of
    " the delimiters if the user has specified
    let leftAlignIndx = a:align == "start" ? 0 : s:LeftMostIndx(a:forceNested, 0, a:firstLine, a:lastLine)
    let rightAlignIndx = s:RightMostIndx(a:forceNested, 0, a:firstLine, a:lastLine)

    " gotta add the length of the left delimiter onto the rightAlignIndx cos
    " we'll be adding a left delimiter to the line
    let rightAlignIndx = rightAlignIndx + strlen(s:Left({'space': 1}))

    " now we actually comment the lines. Do it line by line
    let currentLine = a:firstLine
    while currentLine <= a:lastLine

        " get the next line, check commentability and convert spaces to tabs
        let theLine = getline(currentLine)
        let lineHasLeadingTabs = s:HasLeadingTabs(theLine)
        let theLine = s:ConvertLeadingTabsToSpaces(theLine)
        if s:CanCommentLine(a:forceNested, currentLine)
            "if the user has specified forceNesting then we check to see if we
            "need to switch delimiters for place-holders
            if a:forceNested && g:NERDUsePlaceHolders && !s:Nested()
                let theLine = s:SwapOuterMultiPartDelimsForPlaceHolders(theLine)
            endif

            " find out if the line is commented using normal delimiters and/or
            " alternate ones
            let isCommented = s:IsCommented(s:Left(), s:Right(), theLine) || s:IsCommented(s:Left({'alt': 1}), s:Right({'alt': 1}), theLine)

            " check if we can comment this line
            if !isCommented || g:NERDUsePlaceHolders || s:Multipart()
                if a:align == "left" || a:align == "start" || a:align == "both"
                    let theLine = s:AddLeftDelimAligned(s:Left({'space': 1}), theLine, leftAlignIndx)
                else
                    let theLine = s:AddLeftDelim(s:Left({'space': 1}), theLine)
                endif
                if a:align == "both"
                    let theLine = s:AddRightDelimAligned(s:Right({'space': 1}), theLine, rightAlignIndx)
                else
                    let theLine = s:AddRightDelim(s:Right({'space': 1}), theLine)
                endif
            endif
        endif

        " restore leading tabs if appropriate
        if lineHasLeadingTabs
            let theLine = s:ConvertLeadingSpacesToTabs(theLine)
        endif

        if g:NERDTrimTrailingWhitespace == 1
            let theLine = s:TrimTrailingWhitespace(theLine)
        endif

        " we are done with this line
        call setline(currentLine, theLine)
        let currentLine = currentLine + 1
    endwhile

endfunction

" Function: s:CommentLinesMinimal(firstLine, lastLine) {{{2
" This function comments a range of lines in a minimal style. I
"
" Args:
"   -firstLine/lastLine: the top and bottom lines to comment
function s:CommentLinesMinimal(firstLine, lastLine)
    "check that minimal comments can be done on this filetype
    if !s:HasMultipartDelims()
        throw 'NERDCommenter.Delimiters exception: Minimal comments can only be used for filetypes that have multipart delimiters'
    endif

    let sexyNested = s:SexyNested()

    "if we need to use place holders for the comment, make sure they are
    "enabled for this filetype, or the delimiterss allow nesting
    if !g:NERDUsePlaceHolders && !sexyNested && s:DoesBlockHaveMultipartDelim(a:firstLine, a:lastLine)
        throw 'NERDCommenter.Settings exception: Place holders are required but disabled.'
    endif

    "get the left and right delimiters to smack on
    let left = s:GetSexyComLeft(g:NERDSpaceDelims,0)
    let right = s:GetSexyComRight(g:NERDSpaceDelims,0)

    "make sure all multipart delimiters on the lines are replaced with
    "placeholders to prevent illegal syntax
    if !sexyNested
        let currentLine = a:firstLine
        while(currentLine <= a:lastLine)
            let theLine = getline(currentLine)
            let theLine = s:ReplaceDelims(left, right, g:NERDLPlace, g:NERDRPlace, theLine)
            call setline(currentLine, theLine)
            let currentLine = currentLine + 1
        endwhile
    endif

    "add the delimiter to the top line
    let theLine = getline(a:firstLine)
    let lineHasLeadingTabs = s:HasLeadingTabs(theLine)
    let theLine = s:ConvertLeadingTabsToSpaces(theLine)
    let theLine = s:AddLeftDelim(left, theLine)
    if lineHasLeadingTabs
        let theLine = s:ConvertLeadingSpacesToTabs(theLine)
    endif
    call setline(a:firstLine, theLine)

    "add the delimiter to the bottom line
    let theLine = getline(a:lastLine)
    let lineHasLeadingTabs = s:HasLeadingTabs(theLine)
    let theLine = s:ConvertLeadingTabsToSpaces(theLine)
    let theLine = s:AddRightDelim(right, theLine)
    if lineHasLeadingTabs
        let theLine = s:ConvertLeadingSpacesToTabs(theLine)
    endif

    if g:NERDTrimTrailingWhitespace == 1
        let theLine = s:TrimTrailingWhitespace(theLine)
    endif

    call setline(a:lastLine, theLine)
endfunction

" Function: s:CommentLinesSexy(topline, bottomline) function {{{2
" This function is used to comment lines in the 'Sexy' style. E.g., in c:
" /*
"  * This is a sexy comment
"  */
" Args:
"   -topline: the line number of the top line in the sexy comment
"   -bottomline: the line number of the bottom line in the sexy comment
function s:CommentLinesSexy(topline, bottomline)
    let left = s:GetSexyComLeft(0, 0)
    let right = s:GetSexyComRight(0, 0)

    "check if we can do a sexy comment with the available delimiters
    if left == -1 || right == -1
        throw 'NERDCommenter.Delimiters exception: cannot perform sexy comments with available delimiters.'
    endif

    "make sure the lines aren't already commented sexually or we can nest
    if !s:CanSexyCommentLines(a:topline, a:bottomline)
        throw 'NERDCommenter.Nesting exception: cannot nest sexy comments'
    endif


    let sexyComMarker = s:GetSexyComMarker(0,0)
    let sexyComMarkerSpaced = s:GetSexyComMarker(1,0)


    " we jam the comment as far to the right as possible
    let leftAlignIndx = s:LeftMostIndx(1, 1, a:topline, a:bottomline)

    "check if we should use the compact style i.e that the left/right
    "delimiters should appear on the first and last lines of the code and not
    "on separate lines above/below the first/last lines of code
    if g:NERDCompactSexyComs
        let spaceString = (g:NERDSpaceDelims ? s:spaceStr : '')

        "comment the top line
        let theLine = getline(a:topline)
        let lineHasTabs = s:HasLeadingTabs(theLine)
        if lineHasTabs
            let theLine = s:ConvertLeadingTabsToSpaces(theLine)
        endif
        if !s:SexyNested()
            let theLine = s:SwapOuterMultiPartDelimsForPlaceHolders(theLine)
        endif
        let theLine = s:AddLeftDelimAligned(left . spaceString, theLine, leftAlignIndx)
        if lineHasTabs
            let theLine = s:ConvertLeadingSpacesToTabs(theLine)
        endif
        call setline(a:topline, theLine)

        "comment the bottom line
        if a:bottomline != a:topline
            let theLine = getline(a:bottomline)
            let lineHasTabs = s:HasLeadingTabs(theLine)
            if lineHasTabs
                let theLine = s:ConvertLeadingTabsToSpaces(theLine)
            endif
            if !s:SexyNested()
                let theLine = s:SwapOuterMultiPartDelimsForPlaceHolders(theLine)
            endif
        endif
        let theLine = s:AddRightDelim(spaceString . right, theLine)
        if lineHasTabs
            let theLine = s:ConvertLeadingSpacesToTabs(theLine)
        endif
        call setline(a:bottomline, theLine)
    else

        " add the left delimiter one line above the lines that are to be commented
        call cursor(a:topline, 1)
        execute 'normal! O'
        let theLine = repeat(' ', leftAlignIndx) . left

        " Make sure tabs are respected
        if !&expandtab
           let theLine = s:ConvertLeadingSpacesToTabs(theLine)
        endif
        call setline(a:topline, theLine)

        " add the right delimiter after bottom line (we have to add 1 cos we moved
        " the lines down when we added the left delimiter
        call cursor(a:bottomline+1, 1)
        execute 'normal! o'
        let theLine = repeat(' ', leftAlignIndx) . repeat(' ', strlen(left)-strlen(sexyComMarker)) . right

        " Make sure tabs are respected
        if !&expandtab
           let theLine = s:ConvertLeadingSpacesToTabs(theLine)
        endif
        call setline(a:bottomline+2, theLine)

    endif

    " go thru each line adding the sexyComMarker marker to the start of each
    " line in the appropriate place to align them with the comment delimiters
    let currentLine = a:topline+1
    while currentLine <= a:bottomline + !g:NERDCompactSexyComs
        " get the line and convert the tabs to spaces
        let theLine = getline(currentLine)
        let lineHasTabs = s:HasLeadingTabs(theLine)
        if lineHasTabs
            let theLine = s:ConvertLeadingTabsToSpaces(theLine)
        endif

        if !s:SexyNested()
            let theLine = s:SwapOuterMultiPartDelimsForPlaceHolders(theLine)
        endif

        " add the sexyComMarker
        let theLine = repeat(' ', leftAlignIndx) . repeat(' ', strlen(left)-strlen(sexyComMarker)) . sexyComMarkerSpaced . strpart(theLine, leftAlignIndx)

        if lineHasTabs
            let theLine = s:ConvertLeadingSpacesToTabs(theLine)
        endif

        if g:NERDTrimTrailingWhitespace == 1
            let theLine = s:TrimTrailingWhitespace(theLine)
        endif

        " set the line and move onto the next one
        call setline(currentLine, theLine)
        let currentLine = currentLine + 1
    endwhile

endfunction

" Function: s:CommentLinesToggle(forceNested, firstLine, lastLine) {{{2
" Applies "toggle" commenting to the given range of lines
"
" Args:
"   -forceNested: a flag indicating whether the called is requesting the comment
"    to be nested if need be
"   -firstLine/lastLine: the top and bottom lines to comment
function s:CommentLinesToggle(forceNested, firstLine, lastLine)
    let currentLine = a:firstLine

    let align = g:NERDDefaultAlign
    let leftAlignIndx = align == "start" ? 0 : s:LeftMostIndx(a:forceNested, 0, a:firstLine, a:lastLine)
    let rightAlignIndx = s:RightMostIndx(a:forceNested, 0, a:firstLine, a:lastLine)
    let rightAlignIndx = rightAlignIndx + strlen(s:Left({'space': 1}))

    while currentLine <= a:lastLine

        " get the next line, check commentability and convert spaces to tabs
        let theLine = getline(currentLine)
        let lineHasLeadingTabs = s:HasLeadingTabs(theLine)
        let theLine = s:ConvertLeadingTabsToSpaces(theLine)
        if s:CanToggleCommentLine(a:forceNested, currentLine)

            "if the user has specified forceNesting then we check to see if we
            "need to switch delimiters for place-holders
            if g:NERDUsePlaceHolders && !s:Nested()
                let theLine = s:SwapOuterMultiPartDelimsForPlaceHolders(theLine)
            endif

            if align == 'left' || align == 'start' || align == 'both'
                let theLine = s:AddLeftDelimAligned(s:Left({'space': 1}), theLine, leftAlignIndx)
            else
                let theLine = s:AddLeftDelim(s:Left({'space': 1}), theLine)
            endif
            if align == "both"
                let theLine = s:AddRightDelimAligned(s:Right({'space': 1}), theLine, rightAlignIndx)
            else
                let theLine = s:AddRightDelim(s:Right({'space': 1}), theLine)
            endif
        endif

        " restore leading tabs if appropriate
        if lineHasLeadingTabs
            let theLine = s:ConvertLeadingSpacesToTabs(theLine)
        endif

        if g:NERDTrimTrailingWhitespace == 1
            let theLine = s:TrimTrailingWhitespace(theLine)
        endif

        " we are done with this line
        call setline(currentLine, theLine)
        let currentLine = currentLine + 1
    endwhile

endfunction

" Function: s:CommentRegion(topline, topCol, bottomLine, bottomCol) function {{{2
" This function comments chunks of text selected in visual mode.
" It will comment exactly the text that they have selected.
" Args:
"   -topLine: the line number of the top line in the sexy comment
"   -topCol: top left column for this comment
"   -bottomline: the line number of the bottom line in the sexy comment
"   -bottomCol: the bottom right column for this comment
"   -forceNested: whether the caller wants comments to be nested if the
"    line(s) are already commented
function s:CommentRegion(topLine, topCol, bottomLine, bottomCol, forceNested)

    "switch delimiters (if we can) if the current set isn't multipart
    let switchedDelims = 0
    if !s:Multipart() && s:AltMultipart() && !g:NERDAllowAnyVisualDelims
        let switchedDelims = 1
        call s:SwitchToAlternativeDelimiters(0)
    endif

    "if there is only one line in the comment then just do it
    if a:topLine == a:bottomLine
        call s:CommentBlock(a:topLine, a:bottomLine, a:topCol, a:bottomCol, a:forceNested)

    "there are multiple lines in the comment
    else
        "comment the top line
        call s:CommentBlock(a:topLine, a:topLine, a:topCol, strlen(getline(a:topLine)), a:forceNested)

        "comment out all the lines in the middle of the comment
        let topOfRange = a:topLine+1
        let bottomOfRange = a:bottomLine-1
        if topOfRange <= bottomOfRange
            call s:CommentLines(a:forceNested, g:NERDDefaultAlign, topOfRange, bottomOfRange)
        endif

        "comment the bottom line
        let bottom = getline(a:bottomLine)
        let numLeadingSpacesTabs = strlen(substitute(bottom, '^\([ \t]*\).*$', '\1', ''))
        call s:CommentBlock(a:bottomLine, a:bottomLine, numLeadingSpacesTabs+1, a:bottomCol, a:forceNested)

    endif

    "stick the cursor back on the char it was on before the comment
    call cursor(a:topLine, a:topCol + strlen(s:Left()) + g:NERDSpaceDelims)

    "if we switched delimiters then we gotta go back to what they were before
    if switchedDelims == 1
        call s:SwitchToAlternativeDelimiters(0)
    endif

endfunction

" Function: s:InvertComment(firstLine, lastLine) function {{{2
" Inverts the comments on the lines between and including the given line
" numbers i.e all commented lines are uncommented and vice versa
" Args:
"   -firstLine: the top of the range of lines to be inverted
"   -lastLine: the bottom of the range of lines to be inverted
function s:InvertComment(firstLine, lastLine)

    " go thru all lines in the given range
    let currentLine = a:firstLine
    while currentLine <= a:lastLine
        let theLine = getline(currentLine)

        let sexyComBounds = s:FindBoundingLinesOfSexyCom(currentLine)

        " if the line is commented normally, uncomment it
        if s:IsCommentedFromStartOfLine(s:Left(), theLine) || s:IsCommentedFromStartOfLine(s:Left({'alt': 1}), theLine)
            call s:UncommentLines(currentLine, currentLine)
            let currentLine = currentLine + 1

        " check if the line is commented sexually
        elseif !empty(sexyComBounds)
            let numLinesBeforeSexyComRemoved = s:NumLinesInBuf()
            call s:UncommentLinesSexy(sexyComBounds[0], sexyComBounds[1])

            "move to the line after last line of the sexy comment
            let numLinesAfterSexyComRemoved = s:NumLinesInBuf()
            let currentLine = sexyComBounds[1] - (numLinesBeforeSexyComRemoved - numLinesAfterSexyComRemoved) + 1

        " the line isn't commented
        else
            call s:CommentLinesToggle(1, currentLine, currentLine)
            let currentLine = currentLine + 1
        endif

    endwhile
endfunction

function! NERDCommentIsLineCommented(lineNo)
    let theLine = getline(a:lineNo)
    return s:IsInSexyComment(a:lineNo) || s:IsCommentedFromStartOfLine(s:Left(), theLine) || s:IsCommentedFromStartOfLine(s:Left({'alt': 1}), theLine)
endfunction

" Function: NERDComment(mode, type) function {{{2
" This function is a Wrapper for the main commenting functions
"
" Args:
"   -mode: a character indicating the mode in which the comment is requested:
"   'n' for Normal mode, 'x' for Visual mode
"   -type: the type of commenting requested. Can be 'Sexy', 'Invert',
"    'Minimal', 'Toggle', 'AlignLeft', 'AlignBoth', 'Comment',
"    'Nested', 'ToEOL', 'Append', 'Insert', 'Uncomment', 'Yank'
function! NERDComment(mode, type) range
    if exists('*NERDCommenter_before')
        exe "call NERDCommenter_before()"
    endif

    let isVisual = a:mode =~ '[vsx]'

    if !exists("g:did_load_ftplugin") || g:did_load_ftplugin != 1
        call s:NerdEcho("filetype plugins should be enabled. See :help NERDComInstallation and :help :filetype-plugin-on", 0)
    endif

    if isVisual
        let firstLine = line("'<")
        let lastLine = line("'>")
        let firstCol = col("'<")
        let lastCol = col("'>") - (&selection == 'exclusive' ? 1 : 0)
    else
        let firstLine = a:firstline
        let lastLine = a:lastline
    endif
    "
    " Save options we need to change so we can recover them later
    let state = s:SetupStateBeforeLineComment(firstLine, lastLine)

    let countWasGiven = (!isVisual && firstLine != lastLine)

    let forceNested = (a:type ==? 'Nested' || g:NERDDefaultNesting)

    if a:type ==? 'Comment' || a:type ==? 'Nested'
        if isVisual && visualmode() == "\<C-V>"
            call s:CommentBlock(firstLine, lastLine, firstCol, lastCol, forceNested)
        elseif isVisual && visualmode() == "v" && (g:NERDCommentWholeLinesInVMode==0 || (g:NERDCommentWholeLinesInVMode==2 && s:HasMultipartDelims()))
            call s:CommentRegion(firstLine, firstCol, lastLine, lastCol, forceNested)
        else
            call s:CommentLines(forceNested, g:NERDDefaultAlign, firstLine, lastLine)
        endif

    elseif a:type ==? 'AlignLeft' || a:type ==? 'AlignBoth'
        let align = "none"
        if a:type ==? "AlignLeft"
            let align = "left"
        elseif a:type ==? "AlignBoth"
            let align = "both"
        endif
        call s:CommentLines(forceNested, align, firstLine, lastLine)

    elseif a:type ==? 'Invert'
        call s:InvertComment(firstLine, lastLine)

    elseif a:type ==? 'Sexy'
        try
            call s:CommentLinesSexy(firstLine, lastLine)
        catch /NERDCommenter.Delimiters/
            call s:CommentLines(forceNested, g:NERDDefaultAlign, firstLine, lastLine)
        catch /NERDCommenter.Nesting/
            call s:NerdEcho("Sexy comment aborted. Nested sexy cannot be nested", 0)
        endtry

    elseif a:type ==? 'Toggle'
        let theLine = getline(firstLine)

        if s:IsInSexyComment(firstLine) || s:IsCommentedFromStartOfLine(s:Left(), theLine) || s:IsCommentedFromStartOfLine(s:Left({'alt': 1}), theLine)
            call s:UncommentLines(firstLine, lastLine)
        else
            call s:CommentLinesToggle(forceNested, firstLine, lastLine)
        endif

    elseif a:type ==? 'Minimal'
        try
            call s:CommentLinesMinimal(firstLine, lastLine)
        catch /NERDCommenter.Delimiters/
            call s:NerdEcho("Minimal comments can only be used for filetypes that have multipart delimiters.", 0)
        catch /NERDCommenter.Settings/
            call s:NerdEcho("Place holders are required but disabled.", 0)
        endtry

    elseif a:type ==? 'ToEOL'
        call s:SaveScreenState()
        call s:CommentBlock(firstLine, firstLine, col("."), col("$")-1, 1)
        call s:RestoreScreenState()

    elseif a:type ==? 'Append'
        call s:AppendCommentToLine()

    elseif a:type ==? 'Insert'
        call s:PlaceDelimitersAndInsBetween()

    elseif a:type ==? 'Uncomment'
        call s:UncommentLines(firstLine, lastLine)

    elseif a:type ==? 'Yank'
        if isVisual
            normal! gvy
        elseif countWasGiven
            execute firstLine .','. lastLine .'yank'
        else
            normal! yy
        endif
        execute firstLine .','. lastLine .'call NERDComment("'. a:mode .'", "Comment")'
    endif

    call s:RecoverStateAfterLineComment(state)

    if isVisual
        let nlines = lastLine - firstLine
        silent! call repeat#set("V" . nlines . "jo" . "\<Plug>NERDCommenter". a:type)
    else
        silent! call repeat#set("\<Plug>NERDCommenter". a:type)
    endif

    if exists('*NERDCommenter_after')
        exe "call NERDCommenter_after()"
    endif

endfunction

" Function: s:PlaceDelimitersAndInsBetween() function {{{2
" This is function is called to place comment delimiters down and place the
" cursor between them
function s:PlaceDelimitersAndInsBetween()
    " get the left and right delimiters without any escape chars in them
    let left = s:Left({'space': 1})
    let right = s:Right({'space': 1})

    let theLine = getline(".")
    let lineHasLeadTabs = s:HasLeadingTabs(theLine) || (theLine =~ '^ *$' && !&expandtab)

    "convert tabs to spaces and adjust the cursors column to take this into
    "account
    let untabbedCol = s:UntabbedCol(theLine, col("."))
    call setline(line("."), s:ConvertLeadingTabsToSpaces(theLine))
    call cursor(line("."), untabbedCol)

    " get the length of the right delimiter
    let lenRight = strlen(right)

    let isDelimOnEOL = col(".") >= strlen(getline("."))

    " if the cursor is in the first col then we gotta insert rather than
    " append the comment delimiters here
    let insOrApp = (col(".")==1 ? 'i' : 'a')

    " place the delimiters down. We do it differently depending on whether
    " there is a left AND right delimiter
    if lenRight > 0
        execute ":normal! " . insOrApp . left . right
        execute ":normal! " . lenRight . "h"
    else
        execute ":normal! " . insOrApp . left
    endif
    silent! normal! l

    "if needed convert spaces back to tabs and adjust the cursors col
    "accordingly
    if lineHasLeadTabs
        let tabbedCol = s:TabbedCol(getline("."), col("."))
        call setline(line("."), s:ConvertLeadingSpacesToTabs(getline(".")))
        call cursor(line("."), tabbedCol)
    endif

    if isDelimOnEOL && lenRight == 0
        startinsert!
    else
        startinsert
    endif
endfunction

" Function: s:RemoveDelimiters(left, right, line) {{{2
" this function is called to remove the first left comment delimiter and the
" last right delimiter of the given line.
"
" The arguments left and right must be strings. If there is no right delimiter (as
" is the case for e.g vim file comments) them the argument right should be ""
"
" Args:
"   -left: the left comment delimiter
"   -right: the right comment delimiter
"   -line: the line to remove the delimiters from
function s:RemoveDelimiters(left, right, line)

    let l:left = a:left
    let l:right = a:right
    let lenLeft = strlen(left)
    let lenRight = strlen(right)

    let delimsSpaced = (g:NERDSpaceDelims || g:NERDRemoveExtraSpaces)

    let line = a:line

    "look for the left delimiter, if we find it, remove it.
    let leftIndx = s:FindDelimiterIndex(a:left, line)
    if leftIndx != -1
        let line = strpart(line, 0, leftIndx) . strpart(line, leftIndx+lenLeft)

        "if the user has specified that there is a space after the left delimiter
        "then check for the space and remove it if it is there
        if delimsSpaced && strpart(line, leftIndx, s:lenSpaceStr) == s:spaceStr
            let line = strpart(line, 0, leftIndx) . strpart(line, leftIndx+s:lenSpaceStr)
        endif
    endif

    "look for the right delimiter, if we find it, remove it
    let rightIndx = s:LastIndexOfDelim(a:right, line)
    if rightIndx != -1
        let line = strpart(line, 0, rightIndx) . strpart(line, rightIndx+lenRight)

        "if the user has specified that there is a space before the right delimiter
        "then check for the space and remove it if it is there
        if delimsSpaced && strpart(line, rightIndx-s:lenSpaceStr, s:lenSpaceStr) == s:spaceStr && (s:Multipart() || s:AltMultipart())
            let line = strpart(line, 0, rightIndx-s:lenSpaceStr) . strpart(line, rightIndx)
        endif
    endif

    return line
endfunction

" Function: s:SetupStateBeforeLineComment(topLine, bottomLine) {{{2
" Changes ignorecase and foldmethod options before commenting lines and saves
" their original values in a dict, which is returned as a result
"
" Args:
" topLine: the top line of the visual selection to uncomment
" bottomLine: the bottom line of the visual selection to uncomment
"
" Return: a dict with the state prior to configuration changes
"
function s:SetupStateBeforeLineComment(topLine, bottomLine)
    let state = {'foldmethod' : &foldmethod,
                \'ignorecase' : &ignorecase}

    " Vim's foldmethods are evaluated every time we use 'setline', which can
    " make commenting wide ranges of lines VERY slow. We'll change it to
    " manual, do the commenting stuff and recover it later. To avoid slowing
    " down commenting few lines, we avoid doing this for ranges smaller than
    " 10 lines
    if a:bottomLine - a:topLine >= 10 && &foldmethod != "manual"
        set foldmethod=manual
    endif

    " we want case sensitivity when commenting
    set noignorecase

    return state
endfunction

" Function: s:RecoverStateAfterLineComment(state) {{{2
" Receives the state returned by s:SetupStateBeforeLineComment and restores
" the state accordingly
"
" Args:
" state: the top line of the visual selection to uncomment
" bottomLine: the bottom line of the visual selection to uncomment
function s:RecoverStateAfterLineComment(state)
    if a:state['foldmethod'] != &foldmethod
        let &foldmethod = a:state['foldmethod']
    endif
    if a:state['ignorecase'] != &ignorecase
        let &ignorecase = a:state['ignorecase']
    endif
endfunction

" Function: s:TrimTrailingWhitespace(line) {{{2
" This function removes all the trailing whitespace
" Args:
"   -line: the target line
function s:TrimTrailingWhitespace(line)
    let toReturn = substitute(a:line, '\s\+$', '', 'g')
    return toReturn
endfunction

" Function: s:UncommentLines(topLine, bottomLine) {{{2
" This function uncomments the given lines
"
" Args:
" topLine: the top line of the visual selection to uncomment
" bottomLine: the bottom line of the visual selection to uncomment
function s:UncommentLines(topLine, bottomLine)
    "make local copies of a:firstline and a:lastline and, if need be, swap
    "them around if the top line is below the bottom
    let l:firstline = a:topLine
    let l:lastline = a:bottomLine
    if firstline > lastline
        let firstline = lastline
        let lastline = a:topLine
    endif

    "go thru each line uncommenting each line removing sexy comments
    let currentLine = firstline
    while currentLine <= lastline

        "check the current line to see if it is part of a sexy comment
        let sexyComBounds = s:FindBoundingLinesOfSexyCom(currentLine)
        if !empty(sexyComBounds)

            "we need to store the number of lines in the buffer before the comment is
            "removed so we know how many lines were removed when the sexy comment
            "was removed
            let numLinesBeforeSexyComRemoved = s:NumLinesInBuf()

            call s:UncommentLinesSexy(sexyComBounds[0], sexyComBounds[1])

            "move to the line after last line of the sexy comment
            let numLinesAfterSexyComRemoved = s:NumLinesInBuf()
            let numLinesRemoved = numLinesBeforeSexyComRemoved - numLinesAfterSexyComRemoved
            let currentLine = sexyComBounds[1] - numLinesRemoved + 1
            let lastline = lastline - numLinesRemoved

        "no sexy com was detected so uncomment the line as normal
        else
            call s:UncommentLinesNormal(currentLine, currentLine)
            let currentLine = currentLine + 1
        endif
    endwhile

endfunction

" Function: s:UncommentLinesSexy(topline, bottomline) {{{2
" This function removes all the comment characters associated with the sexy
" comment spanning the given lines
" Args:
"   -topline/bottomline: the top/bottom lines of the sexy comment
function s:UncommentLinesSexy(topline, bottomline)
    let left = s:GetSexyComLeft(0,1)
    let right = s:GetSexyComRight(0,1)


    "check if it is even possible for sexy comments to exist with the
    "available delimiters
    if left == -1 || right == -1
        throw 'NERDCommenter.Delimiters exception: cannot uncomment sexy comments with available delimiters.'
    endif

    let leftUnEsc = s:GetSexyComLeft(0,0)
    let rightUnEsc = s:GetSexyComRight(0,0)

    let sexyComMarker = s:GetSexyComMarker(0, 1)
    let sexyComMarkerUnEsc = s:GetSexyComMarker(0, 0)

    "the markerOffset is how far right we need to move the sexyComMarker to
    "line it up with the end of the left delimiter
    let markerOffset = strlen(leftUnEsc)-strlen(sexyComMarkerUnEsc)

    " go thru the intermediate lines of the sexy comment and remove the
    " sexy comment markers (e.g., the '*'s on the start of line in a c sexy
    " comment)
    let currentLine = a:topline+1
    while currentLine < a:bottomline
        let theLine = getline(currentLine)

        " remove the sexy comment marker from the line. We also remove the
        " space after it if there is one and if appropriate options are set
        let sexyComMarkerIndx = stridx(theLine, sexyComMarkerUnEsc)
        if strpart(theLine, sexyComMarkerIndx+strlen(sexyComMarkerUnEsc), s:lenSpaceStr) == s:spaceStr  && g:NERDSpaceDelims
            let theLine = strpart(theLine, 0, sexyComMarkerIndx - markerOffset) . strpart(theLine, sexyComMarkerIndx+strlen(sexyComMarkerUnEsc)+s:lenSpaceStr)
        else
            let theLine = strpart(theLine, 0, sexyComMarkerIndx - markerOffset) . strpart(theLine, sexyComMarkerIndx+strlen(sexyComMarkerUnEsc))
        endif

        let theLine = s:SwapOuterPlaceHoldersForMultiPartDelims(theLine)

        let theLine = s:ConvertLeadingWhiteSpace(theLine)

        if g:NERDTrimTrailingWhitespace == 1
            let theLine = s:TrimTrailingWhitespace(theLine)
        endif

        " move onto the next line
        call setline(currentLine, theLine)
        let currentLine = currentLine + 1
    endwhile

    " gotta make a copy of a:bottomline cos we modify the position of the
    " last line  it if we remove the topline
    let bottomline = a:bottomline

    " get the first line so we can remove the left delimiter from it
    let theLine = getline(a:topline)

    " if the first line contains only the left delimiter then just delete it
    if theLine =~ '^[ \t]*' . left . '[ \t]*$' && !g:NERDCompactSexyComs
        call cursor(a:topline, 1)
        normal! dd
        let bottomline = bottomline - 1

    " topline contains more than just the left delimiter
    else

        " remove the delimiter. If there is a space after it
        " then remove this too if appropriate
        let delimIndx = stridx(theLine, leftUnEsc)
        if strpart(theLine, delimIndx+strlen(leftUnEsc), s:lenSpaceStr) == s:spaceStr && g:NERDSpaceDelims
            let theLine = strpart(theLine, 0, delimIndx) . strpart(theLine, delimIndx+strlen(leftUnEsc)+s:lenSpaceStr)
        else
            let theLine = strpart(theLine, 0, delimIndx) . strpart(theLine, delimIndx+strlen(leftUnEsc))
        endif
        let theLine = s:SwapOuterPlaceHoldersForMultiPartDelims(theLine)
        call setline(a:topline, theLine)
    endif

    " get the last line so we can remove the right delimiter
    let theLine = getline(bottomline)

    " if the bottomline contains only the right delimiter then just delete it
    if theLine =~ '^[ \t]*' . right . '[ \t]*$'
        call cursor(bottomline, 1)
        normal! dd

    " the last line contains more than the right delimiter
    else
        " remove the right delimiter. If there is a space after it and
        " if the appropriate options are set then remove this too.
        let delimIndx = s:LastIndexOfDelim(rightUnEsc, theLine)
        if strpart(theLine, delimIndx+strlen(leftUnEsc), s:lenSpaceStr) == s:spaceStr  && g:NERDSpaceDelims
            let theLine = strpart(theLine, 0, delimIndx) . strpart(theLine, delimIndx+strlen(rightUnEsc)+s:lenSpaceStr)
        else
            let theLine = strpart(theLine, 0, delimIndx) . strpart(theLine, delimIndx+strlen(rightUnEsc))
        endif

        " if the last line also starts with a sexy comment marker then we
        " remove this as well
        if theLine =~ '^[ \t]*' . sexyComMarker

            " remove the sexyComMarker. If there is a space after it then
            " remove that too
            let sexyComMarkerIndx = stridx(theLine, sexyComMarkerUnEsc)
            if strpart(theLine, sexyComMarkerIndx+strlen(sexyComMarkerUnEsc), s:lenSpaceStr) == s:spaceStr  && g:NERDSpaceDelims
                let theLine = strpart(theLine, 0, sexyComMarkerIndx - markerOffset ) . strpart(theLine, sexyComMarkerIndx+strlen(sexyComMarkerUnEsc)+s:lenSpaceStr)
            else
                let theLine = strpart(theLine, 0, sexyComMarkerIndx - markerOffset ) . strpart(theLine, sexyComMarkerIndx+strlen(sexyComMarkerUnEsc))
            endif
        endif

        let theLine = s:SwapOuterPlaceHoldersForMultiPartDelims(theLine)
        call setline(bottomline, theLine)
    endif

    " remove trailing whitespaces for first and last line
    if g:NERDTrimTrailingWhitespace == 1
        let theLine = getline(a:bottomline)
        let theLine = s:TrimTrailingWhitespace(theLine)
        call setline(a:bottomline, theLine)
        let theLine = getline(a:topline)
        let theLine = s:TrimTrailingWhitespace(theLine)
        call setline(a:topline, theLine)
    endif
endfunction

" Function: s:UncommentLineNormal(line) {{{2
" uncomments the given line and returns the result
" Args:
"   -line: the line to uncomment
function s:UncommentLineNormal(line)
    let line = a:line

    "get the positions of all delimiter types on the line
    let indxLeft = s:FindDelimiterIndex(s:Left(), line)
    let indxLeftAlt = s:FindDelimiterIndex(s:Left({'alt': 1}), line)
    let indxRight = s:LastIndexOfDelim(s:Right(), line)
    let indxRightAlt = s:LastIndexOfDelim(s:Right({'alt': 1}), line)

    "get the comment status on the line so we know how it is commented
    let lineCommentStatus =  s:IsCommentedOutermost(s:Left(), s:Right(), s:Left({'alt': 1}), s:Right({'alt': 1}), line)

    "it is commented with s:Left() and s:Right() so remove these delimiters
    if lineCommentStatus == 1
        let line = s:RemoveDelimiters(s:Left(), s:Right(), line)

    "it is commented with s:Left({'alt': 1}) and s:Right({'alt': 1}) so remove these delimiters
    elseif lineCommentStatus == 2 && g:NERDRemoveAltComs
        let line = s:RemoveDelimiters(s:Left({'alt': 1}), s:Right({'alt': 1}), line)

    "it is not properly commented with any delimiters so we check if it has
    "any random left or right delimiters on it and remove the outermost ones
    else
        "remove the outer most left comment delimiter
        if indxLeft != -1 && (indxLeft < indxLeftAlt || indxLeftAlt == -1)
            let line = s:RemoveDelimiters(s:Left(), '', line)
        elseif indxLeftAlt != -1 && g:NERDRemoveAltComs
            let line = s:RemoveDelimiters(s:Left({'alt': 1}), '', line)
        endif

        "remove the outer most right comment delimiter
        if indxRight != -1 && (indxRight < indxRightAlt || indxRightAlt == -1)
            let line = s:RemoveDelimiters('', s:Right(), line)
        elseif indxRightAlt != -1 && g:NERDRemoveAltComs
            let line = s:RemoveDelimiters('', s:Right({'alt': 1}), line)
        endif
    endif


    let indxLeftPlace = s:FindDelimiterIndex(g:NERDLPlace, line)
    let indxRightPlace = s:FindDelimiterIndex(g:NERDRPlace, line)

    let right = s:Right()
    let left = s:Left()
    if !s:Multipart()
        let right = s:Right({'alt': 1})
        let left = s:Left({'alt': 1})
    endif


    "if there are place-holders on the line then we check to see if they are
    "the outermost delimiters on the line. If so then we replace them with
    "real delimiters
    if indxLeftPlace != -1
        if (indxLeftPlace < indxLeft || indxLeft==-1) && (indxLeftPlace < indxLeftAlt || indxLeftAlt==-1)
            let line = s:ReplaceDelims(g:NERDLPlace, g:NERDRPlace, left, right, line)
        endif
    elseif indxRightPlace != -1
        if (indxRightPlace < indxLeft || indxLeft==-1) && (indxLeftPlace < indxLeftAlt || indxLeftAlt==-1)
            let line = s:ReplaceDelims(g:NERDLPlace, g:NERDRPlace, left, right, line)
        endif

    endif

    let line = s:ConvertLeadingWhiteSpace(line)

    if g:NERDTrimTrailingWhitespace == 1
        let line = s:TrimTrailingWhitespace(line)
    endif

    return line
endfunction

" Function: s:UncommentLinesNormal(topline, bottomline) {{{2
" This function is called to uncomment lines that aren't a sexy comment
" Args:
"   -topline/bottomline: the top/bottom line numbers of the comment
function s:UncommentLinesNormal(topline, bottomline)
    let currentLine = a:topline
    while currentLine <= a:bottomline
        let line = getline(currentLine)
        call setline(currentLine, s:UncommentLineNormal(line))
        let currentLine = currentLine + 1
    endwhile
endfunction


" Section: Other helper functions {{{1
" ============================================================================

" Function: s:AddLeftDelim(delim, theLine) {{{2
" Args:
function s:AddLeftDelim(delim, theLine)
    return substitute(a:theLine, '^\([ \t]*\)', '\1' . a:delim, '')
endfunction

" Function: s:AddLeftDelimAligned(delim, theLine) {{{2
" Args:
function s:AddLeftDelimAligned(delim, theLine, alignIndx)

    "if the line is not long enough then bung some extra spaces on the front
    "so we can align the delimiter properly
    let theLine = a:theLine
    if strlen(theLine) < a:alignIndx
        let theLine = repeat(' ', a:alignIndx - strlen(theLine))
    endif

    return strpart(theLine, 0, a:alignIndx) . a:delim . strpart(theLine, a:alignIndx)
endfunction

" Function: s:AddRightDelim(delim, theLine) {{{2
" Args:
function s:AddRightDelim(delim, theLine)
    if a:delim == ''
        return a:theLine
    else
        return substitute(a:theLine, '$', a:delim, '')
    endif
endfunction

" Function: s:AddRightDelimAligned(delim, theLine, alignIndx) {{{2
" Args:
function s:AddRightDelimAligned(delim, theLine, alignIndx)
    if a:delim == ""
        return a:theLine
    else

        " when we align the right delimiter we are just adding spaces
        " so we get a string containing the needed spaces (it
        " could be empty)
        let extraSpaces = ''
        let extraSpaces = repeat(' ', a:alignIndx-strlen(a:theLine))

        " add the right delimiter
        return substitute(a:theLine, '$', extraSpaces . a:delim, '')
    endif
endfunction

" Function: s:AltMultipart() {{{2
" returns 1 if the alternative delimiters are multipart
function s:AltMultipart()
    return b:NERDCommenterDelims['rightAlt'] != ''
endfunction

" Function: s:AltNested() {{{2
" returns 1 if the alternate multipart (if any) delimiters allow nesting
function s:AltNested()
    return b:NERDCommenterDelims['nestedAlt']
endfunction

" Function: s:CanCommentLine(forceNested, line) {{{2
"This function is used to determine whether the given line can be commented.
"It returns 1 if it can be and 0 otherwise
"
" Args:
"   -forceNested: a flag indicating whether the caller wants comments to be nested
"    if the current line is already commented
"   -lineNum: the line number of the line to check for commentability
function s:CanCommentLine(forceNested, lineNum)
    let theLine = getline(a:lineNum)

    " make sure we don't comment lines that are just spaces or tabs or empty,
    " unless configured otherwise
    if g:NERDCommentEmptyLines == 0 && theLine =~ "^[ \t]*$"
        return 0
    endif

    "if the line is part of a sexy comment then just flag it...
    if s:IsInSexyComment(a:lineNum)
        return 0
    endif

    let isCommented = s:IsCommentedNormOrSexy(a:lineNum)

    "if the line isn't commented return true
    if !isCommented
        return 1
    endif

    "if the line is commented but nesting is allowed then return true
    if s:Nested() || (a:forceNested && (!s:Multipart() || g:NERDUsePlaceHolders))
        return 1
    endif

    return 0
endfunction

" Function: s:CanPlaceCursor(line, col) {{{2
" returns 1 if the cursor can be placed exactly in the given position
function s:CanPlaceCursor(line, col)
    let c = col(".")
    let l = line(".")
    call cursor(a:line, a:col)
    let success = (line(".") == a:line && col(".") == a:col)
    call cursor(l,c)
    return success
endfunction

" Function: s:CanSexyCommentLines(topline, bottomline) {{{2
" Return: 1 if the given lines can be commented sexually, 0 otherwise
function s:CanSexyCommentLines(topline, bottomline)
    " see if the selected regions have any sexy comments
    " however, if the language allows nested comments,
    " we allow nested sexy comments
    if s:SexyNested()
        return 1
    endif
    let currentLine = a:topline
    while(currentLine <= a:bottomline)
        if s:IsInSexyComment(currentLine)
            return 0
        endif
        let currentLine = currentLine + 1
    endwhile
    return 1
endfunction
" Function: s:CanToggleCommentLine(forceNested, line) {{{2
"This function is used to determine whether the given line can be toggle commented.
"It returns 1 if it can be and 0 otherwise
"
" Args:
"   -lineNum: the line number of the line to check for commentability
function s:CanToggleCommentLine(forceNested, lineNum)
    let theLine = getline(a:lineNum)
    if (s:IsCommentedFromStartOfLine(s:Left(), theLine) || s:IsCommentedFromStartOfLine(s:Left({'alt': 1}), theLine)) && !a:forceNested
        return 0
    endif

    " make sure we don't comment lines that are just spaces or tabs or empty,
    " unless configured otherwise
    if g:NERDCommentEmptyLines == 0 && theLine =~ "^[ \t]*$"
        return 0
    endif

    "if the line is part of a sexy comment then just flag it...
    if s:IsInSexyComment(a:lineNum)
        return 0
    endif

    return 1
endfunction

" Function: s:ConvertLeadingSpacesToTabs(line) {{{2
" This function takes a line and converts all leading tabs on that line into
" spaces
"
" Args:
"   -line: the line whose leading tabs will be converted
function s:ConvertLeadingSpacesToTabs(line)
    let toReturn  = a:line
    while toReturn =~ '^\t*' . s:TabSpace() . '\(.*\)$'
        let toReturn = substitute(toReturn, '^\(\t*\)' . s:TabSpace() . '\(.*\)$'  ,  '\1\t\2' , "")
    endwhile

    return toReturn
endfunction


" Function: s:ConvertLeadingTabsToSpaces(line) {{{2
" This function takes a line and converts all leading spaces on that line into
" tabs
"
" Args:
"   -line: the line whose leading spaces will be converted
function s:ConvertLeadingTabsToSpaces(line)
    let toReturn  = a:line
    while toReturn =~ '^\( *\)\t'
        let toReturn = substitute(toReturn, '^\( *\)\t',  '\1' . s:TabSpace() , "")
    endwhile

    return toReturn
endfunction

" Function: s:ConvertLeadingWhiteSpace(line) {{{2
" Converts the leading white space to tabs/spaces depending on &ts
"
" Args:
"   -line: the line to convert
function s:ConvertLeadingWhiteSpace(line)
    let toReturn = a:line
    while toReturn =~ '^ *\t'
        let toReturn = substitute(toReturn, '^ *\zs\t\ze', s:TabSpace(), "g")
    endwhile

    if !&expandtab
        let toReturn = s:ConvertLeadingSpacesToTabs(toReturn)
    endif

    return toReturn
endfunction


" Function: s:CountNonESCedOccurances(str, searchstr, escChar) {{{2
" This function counts the number of substrings contained in another string.
" These substrings are only counted if they are not escaped with escChar
" Args:
"   -str: the string to look for searchstr in
"   -searchstr: the substring to search for in str
"   -escChar: the escape character which, when preceding an instance of
"    searchstr, will cause it not to be counted
function s:CountNonESCedOccurances(str, searchstr, escChar)
    "get the index of the first occurrence of searchstr
    let indx = stridx(a:str, a:searchstr)

    "if there is an instance of searchstr in str process it
    if indx != -1
        "get the remainder of str after this instance of searchstr is removed
        let lensearchstr = strlen(a:searchstr)
        let strLeft = strpart(a:str, indx+lensearchstr)

        "if this instance of searchstr is not escaped, add one to the count
        "and recurse. If it is escaped, just recurse
        if !s:IsEscaped(a:str, indx, a:escChar)
            return 1 + s:CountNonESCedOccurances(strLeft, a:searchstr, a:escChar)
        else
            return s:CountNonESCedOccurances(strLeft, a:searchstr, a:escChar)
        endif
    endif
endfunction
" Function: s:DoesBlockHaveDelim(delim, top, bottom) {{{2
" Returns 1 if the given block of lines has a delimiter (a:delim) in it
" Args:
"   -delim: the comment delimiter to check the block for
"   -top: the top line number of the block
"   -bottom: the bottom line number of the block
function s:DoesBlockHaveDelim(delim, top, bottom)
    let currentLine = a:top
    while currentLine < a:bottom
        let theline = getline(currentLine)
        if s:FindDelimiterIndex(a:delim, theline) != -1
            return 1
        endif
        let currentLine = currentLine + 1
    endwhile
    return 0
endfunction

" Function: s:DoesBlockHaveMultipartDelim(top, bottom) {{{2
" Returns 1 if the given block has a >= 1 multipart delimiter in it
" Args:
"   -top: the top line number of the block
"   -bottom: the bottom line number of the block
function s:DoesBlockHaveMultipartDelim(top, bottom)
    if s:HasMultipartDelims()
        if s:Multipart()
            return s:DoesBlockHaveDelim(s:Left(), a:top, a:bottom) || s:DoesBlockHaveDelim(s:Right(), a:top, a:bottom)
        else
            return s:DoesBlockHaveDelim(s:Left({'alt': 1}), a:top, a:bottom) || s:DoesBlockHaveDelim(s:Right({'alt': 1}), a:top, a:bottom)
        endif
    endif
    return 0
endfunction


" Function: s:Esc(str) {{{2
" Escapes all the tricky chars in the given string
function s:Esc(str)
    let charsToEsc = '*/\."&$+'
    return escape(a:str, charsToEsc)
endfunction

" Function: s:FindDelimiterIndex(delimiter, line) {{{2
" This function is used to get the string index of the input comment delimiter
" on the input line. If no valid comment delimiter is found in the line then
" -1 is returned
" Args:
"   -delimiter: the delimiter we are looking to find the index of
"   -line: the line we are looking for delimiter on
function s:FindDelimiterIndex(delimiter, line)

    "make sure the delimiter isn't empty otherwise we go into an infinite loop.
    if a:delimiter == ""
        return -1
    endif


    let l:delimiter = a:delimiter
    let lenDel = strlen(l:delimiter)

    "get the index of the first occurrence of the delimiter
    let delIndx = stridx(a:line, l:delimiter)

    "keep looping thru the line till we either find a real comment delimiter
    "or run off the EOL
    while delIndx != -1

        "if we are not off the EOL get the str before the possible delimiter
        "in question and check if it really is a delimiter. If it is, return
        "its position
        if delIndx != -1
            if s:IsDelimValid(l:delimiter, delIndx, a:line)
                return delIndx
            endif
        endif

        "we have not yet found a real comment delimiter so move past the
        "current one we are looking at
        let restOfLine = strpart(a:line, delIndx + lenDel)
        let distToNextDelim = stridx(restOfLine , l:delimiter)

        "if distToNextDelim is -1 then there is no more potential delimiters
        "on the line so set delIndx to -1. Otherwise, move along the line by
        "distToNextDelim
        if distToNextDelim == -1
            let delIndx = -1
        else
            let delIndx = delIndx + lenDel + distToNextDelim
        endif
    endwhile

    "there is no comment delimiter on this line
    return -1
endfunction

" Function: s:FindBoundingLinesOfSexyCom(lineNum) {{{2
" This function takes in a line number and tests whether this line number is
" the top/bottom/middle line of a sexy comment. If it is then the top/bottom
" lines of the sexy comment are returned
" Args:
"   -lineNum: the line number that is to be tested whether it is the
"    top/bottom/middle line of a sexy com
" Returns:
"   A string that has the top/bottom lines of the sexy comment encoded in it.
"   The format is 'topline,bottomline'. If a:lineNum turns out not to be the
"   top/bottom/middle of a sexy comment then -1 is returned
function s:FindBoundingLinesOfSexyCom(lineNum)

    "find which delimiters to look for as the start/end delimiters of the comment
    let left = ''
    let right = ''
    if s:Multipart()
        let left = s:Left({'esc': 1})
        let right = s:Right({'esc': 1})
    elseif s:AltMultipart()
        let left = s:Left({'alt': 1, 'esc': 1})
        let right = s:Right({'alt': 1, 'esc': 1})
    else
        return []
    endif

    let sexyComMarker = s:GetSexyComMarker(0, 1)

    "initialise the top/bottom line numbers of the sexy comment to -1
    let top = -1
    let bottom = -1

    let currentLine = a:lineNum
    while top == -1 || bottom == -1
        let theLine = getline(currentLine)

        "check if the current line is the top of the sexy comment
        if currentLine <= a:lineNum && theLine =~ '^[ \t]*' . left && theLine !~ '.*' . right && currentLine < s:NumLinesInBuf()
            let top = currentLine
            let currentLine = a:lineNum

        "check if the current line is the bottom of the sexy comment
        elseif theLine =~ '^[ \t]*' . right && theLine !~ '.*' . left && currentLine > 1
            let bottom = currentLine

        "the right delimiter is on the same line as the last sexyComMarker
        elseif theLine =~ '^[ \t]*' . sexyComMarker . '.*' . right
            let bottom = currentLine

        "we have not found the top or bottom line so we assume currentLine is an
        "intermediate line and look to prove otherwise
        else

            "if the line doesn't start with a sexyComMarker then it is not a sexy
            "comment
            if theLine !~ '^[ \t]*' . sexyComMarker
                return []
            endif

        endif

        "if top is -1 then we haven't found the top yet so keep looking up
        if top == -1
            let currentLine = currentLine - 1
        "if we have found the top line then go down looking for the bottom
        else
            let currentLine = currentLine + 1
        endif

    endwhile

    return [top, bottom]
endfunction


" Function: s:GetSexyComMarker() {{{2
" Returns the sexy comment marker for the current filetype.
"
" C style sexy comments are assumed if possible. If not then the sexy comment
" marker is the last char of the delimiter pair that has both left and right
" delimiters and has the longest left delimiter
"
" Args:
"   -space: specifies whether the marker is to have a space string after it
"    (the space string will only be added if NERDSpaceDelims is set)
"   -esc: specifies whether the tricky chars in the marker are to be ESCed
function s:GetSexyComMarker(space, esc)
    let sexyComMarker = b:NERDSexyComMarker

    "if there is no hardcoded marker then we find one
    if sexyComMarker == ''

        "if the filetype has c style comments then use standard c sexy
        "comments
        if s:HasCStyleComments()
            let sexyComMarker = '*'
        else
            "find a comment marker by getting the longest available left delimiter
            "(that has a corresponding right delimiter) and taking the last char
            let lenLeft = strlen(s:Left())
            let lenLeftAlt = strlen(s:Left({'alt': 1}))
            let left = ''
            let right = ''
            if s:Multipart() && lenLeft >= lenLeftAlt
                let left = s:Left()
            elseif s:AltMultipart()
                let left = s:Left({'alt': 1})
            else
                return -1
            endif

            "get the last char of left
            let sexyComMarker = strpart(left, strlen(left)-1)
        endif
    endif

    if a:space && g:NERDSpaceDelims
        let sexyComMarker = sexyComMarker . s:spaceStr
    endif

    if a:esc
        let sexyComMarker = s:Esc(sexyComMarker)
    endif

    return sexyComMarker
endfunction

" Function: s:SexyNested() {{{2
" Returns 1 if the sexy delimeters allow nesting
" TODO this is ugly copy&paste from the GetSexyComLeft/Right functions,
" these could all be cleaned up
function s:SexyNested()
    let lenLeft = strlen(s:Left())
    let lenLeftAlt = strlen(s:Left({'alt': 1}))

    "assume c style sexy comments if possible
    if s:HasCStyleComments()
        return (s:Left() == '/*' && s:Nested()) || (s:Left({'alt': 1}) == '/*' && s:AltNested())
    else
        "grab the longest left delim that has a right
        if s:Multipart() && lenLeft >= lenLeftAlt
            return s:Nested()
        elseif s:AltMultipart()
            return s:AltNested()
        else
            return 0
        endif
    endif
endfunction

" Function: s:GetSexyComLeft(space, esc) {{{2
" Returns the left delimiter for sexy comments for this filetype or -1 if
" there is none. C style sexy comments are used if possible
" Args:
"   -space: specifies if the delimiter has a space string on the end
"   (the space string will only be added if NERDSpaceDelims is set)
"   -esc: specifies whether the tricky chars in the string are ESCed
function s:GetSexyComLeft(space, esc)
    let lenLeft = strlen(s:Left())
    let lenLeftAlt = strlen(s:Left({'alt': 1}))
    let left = ''

    "assume c style sexy comments if possible
    if s:HasCStyleComments()
        let left = '/*'
    else
        "grab the longest left delimiter that has a right
        if s:Multipart() && lenLeft >= lenLeftAlt
            let left = s:Left()
        elseif s:AltMultipart()
            let left = s:Left({'alt': 1})
        else
            return -1
        endif
    endif

    if a:space && g:NERDSpaceDelims
        let left = left . s:spaceStr
    endif

    if a:esc
        let left = s:Esc(left)
    endif

    return left
endfunction

" Function: s:GetSexyComRight(space, esc) {{{2
" Returns the right delimiter for sexy comments for this filetype or -1 if
" there is none. C style sexy comments are used if possible.
" Args:
"   -space: specifies if the delimiter has a space string on the start
"   (the space string will only be added if NERDSpaceDelims
"   is specified for the current filetype)
"   -esc: specifies whether the tricky chars in the string are ESCed
function s:GetSexyComRight(space, esc)
    let lenLeft = strlen(s:Left())
    let lenLeftAlt = strlen(s:Left({'alt': 1}))
    let right = ''

    "assume c style sexy comments if possible
    if s:HasCStyleComments()
        let right = '*/'
    else
        "grab the right delimiter that pairs with the longest left delimiter
        if s:Multipart() && lenLeft >= lenLeftAlt
            let right = s:Right()
        elseif s:AltMultipart()
            let right = s:Right({'alt': 1})
        else
            return -1
        endif
    endif

    if a:space && g:NERDSpaceDelims
        let right = s:spaceStr . right
    endif

    if a:esc
        let right = s:Esc(right)
    endif

    return right
endfunction

" Function: s:HasMultipartDelims() {{{2
" Returns 1 if the current filetype has at least one set of multipart delimiters
function s:HasMultipartDelims()
    return s:Multipart() || s:AltMultipart()
endfunction

" Function: s:HasLeadingTabs(...) {{{2
" Returns 1 if any of the given strings have leading tabs
function s:HasLeadingTabs(...)
    for s in a:000
        if s =~ '^\t.*'
            return 1
        end
    endfor
    return 0
endfunction
" Function: s:HasCStyleComments() {{{2
" Returns 1 if the current filetype has c style comment delimiters
function s:HasCStyleComments()
    return (s:Left() == '/*' && s:Right() == '*/') || (s:Left({'alt': 1}) == '/*' && s:Right({'alt': 1}) == '*/')
endfunction

" Function: s:IsCommentedNormOrSexy(lineNum) {{{2
"This function is used to determine whether the given line is commented with
"either set of delimiters or if it is part of a sexy comment
"
" Args:
"   -lineNum: the line number of the line to check
function s:IsCommentedNormOrSexy(lineNum)
    let theLine = getline(a:lineNum)

    "if the line is commented normally return 1
    if s:IsCommented(s:Left(), s:Right(), theLine) || s:IsCommented(s:Left({'alt': 1}), s:Right({'alt': 1}), theLine)
        return 1
    endif

    "if the line is part of a sexy comment return 1
    if s:IsInSexyComment(a:lineNum)
        return 1
    endif
    return 0
endfunction

" Function: s:IsCommented(left, right, line) {{{2
"This function is used to determine whether the given line is commented with
"the given delimiters
"
" Args:
"   -line: the line that to check if commented
"   -left/right: the left and right delimiters to check for
function s:IsCommented(left, right, line)
    "if the line isn't commented return true
    if s:FindDelimiterIndex(a:left, a:line) != -1 && (s:LastIndexOfDelim(a:right, a:line) != -1 || !s:Multipart())
        return 1
    endif
    return 0
endfunction

" Function: s:IsCommentedFromStartOfLine(left, line) {{{2
"This function is used to determine whether the given line is commented with
"the given delimiters at the start of the line i.e the left delimiter is the
"first thing on the line (apart from spaces\tabs)
"
" Args:
"   -line: the line that to check if commented
"   -left: the left delimiter to check for
function s:IsCommentedFromStartOfLine(left, line)
    let theLine = s:ConvertLeadingTabsToSpaces(a:line)
    let numSpaces = strlen(substitute(theLine, '^\( *\).*$', '\1', ''))
    let delimIndx = s:FindDelimiterIndex(a:left, theLine)
    return delimIndx == numSpaces
endfunction

" Function: s:IsCommentedOutermost(left, right, leftAlt, rightAlt, line) {{{2
" Finds the type of the outermost delimiters on the line
"
" Args:
"   -line: the line that to check if the outermost comments on it are
"    left/right
"   -left/right: the left and right delimiters to check for
"   -leftAlt/rightAlt: the left and right alternative delimiters to check for
"
" Returns:
"   0 if the line is not commented with either set of delimiters
"   1 if the line is commented with the left/right delimiter set
"   2 if the line is commented with the leftAlt/rightAlt delim set
function s:IsCommentedOutermost(left, right, leftAlt, rightAlt, line)
    "get the first positions of the left delimiters and the last positions of the
    "right delimiters
    let indxLeft = s:FindDelimiterIndex(a:left, a:line)
    let indxLeftAlt = s:FindDelimiterIndex(a:leftAlt, a:line)
    let indxRight = s:LastIndexOfDelim(a:right, a:line)
    let indxRightAlt = s:LastIndexOfDelim(a:rightAlt, a:line)

    "check if the line has a left delimiter before a leftAlt delimiter
    if (indxLeft <= indxLeftAlt || indxLeftAlt == -1) && indxLeft != -1
        "check if the line has a right delimiter after any rightAlt delimiter
        if (indxRight > indxRightAlt && indxRight > indxLeft) || !s:Multipart()
            return 1
        endif

        "check if the line has a leftAlt delimiter before a left delimiter
    elseif (indxLeftAlt <= indxLeft || indxLeft == -1) && indxLeftAlt != -1
        "check if the line has a rightAlt delimiter after any right delimiter
        if (indxRightAlt > indxRight && indxRightAlt > indxLeftAlt) || !s:AltMultipart()
            return 2
        endif
    else
        return 0
    endif

    return 0

endfunction


" Function: s:IsDelimValid(delimiter, delIndx, line) {{{2
" This function is responsible for determining whether a given instance of a
" comment delimiter is a real delimiter or not. For example, in java the
" // string is a comment delimiter but in the line:
"               System.out.println("//");
" it does not count as a comment delimiter. This function is responsible for
" distinguishing between such cases. It does so by applying a set of
" heuristics that are not fool proof but should work most of the time.
"
" Args:
"   -delimiter: the delimiter we are validating
"   -delIndx: the position of delimiter in line
"   -line: the line that delimiter occurs in
"
" Returns:
" 0 if the given delimiter is not a real delimiter (as far as we can tell) ,
" 1 otherwise
function s:IsDelimValid(delimiter, delIndx, line)
    "get the delimiter without the escchars
    let l:delimiter = a:delimiter

    "get the strings before and after the delimiter
    let preComStr = strpart(a:line, 0, a:delIndx)
    let postComStr = strpart(a:line, a:delIndx+strlen(delimiter))

    "to check if the delimiter is real, make sure it isn't preceded by
    "an odd number of quotes and followed by the same (which would indicate
    "that it is part of a string and therefore is not a comment)
    if !s:IsNumEven(s:CountNonESCedOccurances(preComStr, '"', "\\")) && !s:IsNumEven(s:CountNonESCedOccurances(postComStr, '"', "\\"))
        return 0
    endif
    if !s:IsNumEven(s:CountNonESCedOccurances(preComStr, "'", "\\")) && !s:IsNumEven(s:CountNonESCedOccurances(postComStr, "'", "\\"))
        return 0
    endif
    if !s:IsNumEven(s:CountNonESCedOccurances(preComStr, "`", "\\")) && !s:IsNumEven(s:CountNonESCedOccurances(postComStr, "`", "\\"))
        return 0
    endif


    "if the comment delimiter is escaped, assume it isn't a real delimiter
    if s:IsEscaped(a:line, a:delIndx, "\\")
        return 0
    endif

    "vim comments are so fucking stupid!! Why the hell do they have comment
    "delimiters that are used elsewhere in the syntax?!?! We need to check
    "some conditions especially for vim
    if &filetype == "vim"
        if !s:IsNumEven(s:CountNonESCedOccurances(preComStr, '"', "\\"))
            return 0
        endif

        "if the delimiter is on the very first char of the line or is the
        "first non-tab/space char on the line then it is a valid comment delimiter
        if a:delIndx == 0 || a:line =~ "^[ \t]\\{" . a:delIndx . "\\}\".*$"
            return 1
        endif

        let numLeftParen =s:CountNonESCedOccurances(preComStr, "(", "\\")
        let numRightParen =s:CountNonESCedOccurances(preComStr, ")", "\\")

        "if the quote is inside brackets then assume it isn't a comment
        if numLeftParen > numRightParen
            return 0
        endif

        "if the line has an even num of unescaped "'s then we can assume that
        "any given " is not a comment delimiter
        if s:IsNumEven(s:CountNonESCedOccurances(a:line, "\"", "\\"))
            return 0
        endif
    endif

    return 1

endfunction

" Function: s:IsNumEven(num) {{{2
" A small function the returns 1 if the input number is even and 0 otherwise
" Args:
"   -num: the number to check
function s:IsNumEven(num)
    return (a:num % 2) == 0
endfunction

" Function: s:IsEscaped(str, indx, escChar) {{{2
" This function takes a string, an index into that string and an esc char and
" returns 1 if the char at the index is escaped (i.e if it is preceded by an
" odd number of esc chars)
" Args:
"   -str: the string to check
"   -indx: the index into str that we want to check
"   -escChar: the escape char the char at indx may be ESCed with
function s:IsEscaped(str, indx, escChar)
    "initialise numEscChars to 0 and look at the char before indx
    let numEscChars = 0
    let curIndx = a:indx-1

    "keep going back thru str until we either reach the start of the str or
    "run out of esc chars
    while curIndx >= 0 && strpart(a:str, curIndx, 1) == a:escChar

        "we have found another esc char so add one to the count and move left
        "one char
        let numEscChars  = numEscChars + 1
        let curIndx = curIndx - 1

    endwhile

    "if there is an odd num of esc chars directly before the char at indx then
    "the char at indx is escaped
    return !s:IsNumEven(numEscChars)
endfunction

" Function: s:IsInSexyComment(line) {{{2
" returns 1 if the given line number is part of a sexy comment
function s:IsInSexyComment(line)
    return !empty(s:FindBoundingLinesOfSexyCom(a:line))
endfunction

" Function: s:IsSexyComment(topline, bottomline) {{{2
" This function takes in 2 line numbers and returns 1 if the lines between and
" including the given line numbers are a sexy comment. It returns 0 otherwise.
" Args:
"   -topline: the line that the possible sexy comment starts on
"   -bottomline: the line that the possible sexy comment stops on
function s:IsSexyComment(topline, bottomline)

    "get the delimiter set that would be used for a sexy comment
    let left = ''
    let right = ''
    if s:Multipart()
        let left = s:Left()
        let right = s:Right()
    elseif s:AltMultipart()
        let left = s:Left({'alt': 1})
        let right = s:Right({'alt': 1})
    else
        return 0
    endif

    "swap the top and bottom line numbers around if need be
    let topline = a:topline
    let bottomline = a:bottomline
    if bottomline < topline
        topline = bottomline
        bottomline = a:topline
    endif

    "if there is < 2 lines in the comment it cannot be sexy
    if (bottomline - topline) <= 0
        return 0
    endif

    "if the top line doesn't begin with a left delimiter then the comment isn't sexy
    if getline(a:topline) !~ '^[ \t]*' . left
        return 0
    endif

    "if there is a right delimiter on the top line then this isn't a sexy comment
    if s:LastIndexOfDelim(right, getline(a:topline)) != -1
        return 0
    endif

    "if there is a left delimiter on the bottom line then this isn't a sexy comment
    if s:FindDelimiterIndex(left, getline(a:bottomline)) != -1
        return 0
    endif

    "if the bottom line doesn't begin with a right delimiter then the comment isn't
    "sexy
    if getline(a:bottomline) !~ '^.*' . right . '$'
        return 0
    endif

    let sexyComMarker = s:GetSexyComMarker(0, 1)

    "check each of the intermediate lines to make sure they start with a
    "sexyComMarker
    let currentLine = a:topline+1
    while currentLine < a:bottomline
        let theLine = getline(currentLine)

        if theLine !~ '^[ \t]*' . sexyComMarker
            return 0
        endif

        "if there is a right delimiter in an intermediate line then the block isn't
        "a sexy comment
        if s:LastIndexOfDelim(right, theLine) != -1
            return 0
        endif

        let currentLine = currentLine + 1
    endwhile

    "we have not found anything to suggest that this isn't a sexy comment so
    return 1

endfunction

" Function: s:LastIndexOfDelim(delim, str) {{{2
" This function takes a string and a delimiter and returns the last index of
" that delimiter in string
" Args:
"   -delim: the delimiter to look for
"   -str: the string to look for delimiter in
function s:LastIndexOfDelim(delim, str)
    let delim = a:delim
    let lenDelim = strlen(delim)

    "set index to the first occurrence of delimiter. If there is no occurrence then
    "bail
    let indx = s:FindDelimiterIndex(delim, a:str)
    if indx == -1
        return -1
    endif

    "keep moving to the next instance of delimiter in str till there is none left
    while 1

        "search for the next delimiter after the previous one
        let searchStr = strpart(a:str, indx+lenDelim)
        let indx2 = s:FindDelimiterIndex(delim, searchStr)

        "if we find a delimiter update indx to record the position of it, if we
        "don't find another delimiter then indx is the last one so break out of
        "this loop
        if indx2 != -1
            let indx = indx + indx2 + lenDelim
        else
            break
        endif
    endwhile

    return indx

endfunction

" Function: s:Left(...) {{{2
" returns left delimiter data
function s:Left(...)
    let params = a:0 ? a:1 : {}

    let delim = has_key(params, 'alt') ? b:NERDCommenterDelims['leftAlt'] : b:NERDCommenterDelims['left']

    if delim == ''
        return ''
    endif

    if has_key(params, 'space') && g:NERDSpaceDelims
        let delim = delim . s:spaceStr
    endif

    if has_key(params, 'esc')
        let delim = s:Esc(delim)
    endif

    return delim
endfunction

" Function: s:LeftMostIndx(countCommentedLines, countEmptyLines, topline, bottomline) {{{2
" This function takes in 2 line numbers and returns the index of the left most
" char (that is not a space or a tab) on all of these lines.
" Args:
"   -countCommentedLines: 1 if lines that are commented are to be checked as
"    well. 0 otherwise
"   -countEmptyLines: 1 if empty lines are to be counted in the search
"   -topline: the top line to be checked
"   -bottomline: the bottom line to be checked
function s:LeftMostIndx(countCommentedLines, countEmptyLines, topline, bottomline)

    " declare the left most index as an extreme value
    let leftMostIndx = 1000

    " go thru the block line by line updating leftMostIndx
    let currentLine = a:topline
    while currentLine <= a:bottomline

        " get the next line and if it is allowed to be commented, or is not
        " commented, check it
        let theLine = getline(currentLine)
        if a:countEmptyLines || theLine !~ '^[ \t]*$'
            if a:countCommentedLines || (!s:IsCommented(s:Left(), s:Right(), theLine) && !s:IsCommented(s:Left({'alt': 1}), s:Right({'alt': 1}), theLine))
                " convert spaces to tabs and get the number of leading spaces for
                " this line and update leftMostIndx if need be
                let theLine = s:ConvertLeadingTabsToSpaces(theLine)
                let leadSpaceOfLine = strlen( substitute(theLine, '\(^[ \t]*\).*$','\1','') )
                if leadSpaceOfLine < leftMostIndx
                    let leftMostIndx = leadSpaceOfLine
                endif
            endif
        endif

        " move on to the next line
        let currentLine = currentLine + 1
    endwhile

    if leftMostIndx == 1000
        return 0
    else
        return leftMostIndx
    endif
endfunction

" Function: s:Multipart() {{{2
" returns 1 if the current delimiters are multipart
function s:Multipart()
    return s:Right() != ''
endfunction

" Function: s:NerdEcho(msg, typeOfMsg) {{{2
" Args:
"   -msg: the message to echo
"   -typeOfMsg: 0 = warning message
"               1 = normal message
function s:NerdEcho(msg, typeOfMsg)
    if a:typeOfMsg == 0
        echohl WarningMsg
        echom 'NERDCommenter:' . a:msg
        echohl None
    elseif a:typeOfMsg == 1
        echom 'NERDCommenter:' . a:msg
    endif
endfunction

" Function: s:Nested() {{{2
" returns 1 if the current multipart (if any) delimiters allow nesting
function s:Nested()
    return b:NERDCommenterDelims['nested']
endfunction

" Function: s:NumberOfLeadingTabs(s) {{{2
" returns the number of leading tabs in the given string
function s:NumberOfLeadingTabs(s)
    return strlen(substitute(a:s, '^\(\t*\).*$', '\1', ""))
endfunction

" Function: s:NumLinesInBuf() {{{2
" Returns the number of lines in the current buffer
function s:NumLinesInBuf()
    return line('$')
endfunction

" Function: s:ReplaceDelims(toReplace1, toReplace2, replacor1, replacor2, str) {{{2
" This function takes in a string, 2 delimiters in that string and 2 strings
" to replace these delimiters with.
"
" Args:
"   -toReplace1: the first delimiter to replace
"   -toReplace2: the second delimiter to replace
"   -replacor1: the string to replace toReplace1 with
"   -replacor2: the string to replace toReplace2 with
"   -str: the string that the delimiters to be replaced are in
function s:ReplaceDelims(toReplace1, toReplace2, replacor1, replacor2, str)
    let line = s:ReplaceLeftMostDelim(a:toReplace1, a:replacor1, a:str)
    let line = s:ReplaceRightMostDelim(a:toReplace2, a:replacor2, line)
    return line
endfunction

" Function: s:ReplaceLeftMostDelim(toReplace, replacor, str) {{{2
" This function takes a string and a delimiter and replaces the left most
" occurrence of this delimiter in the string with a given string
"
" Args:
"   -toReplace: the delimiter in str that is to be replaced
"   -replacor: the string to replace toReplace with
"   -str: the string that contains toReplace
function s:ReplaceLeftMostDelim(toReplace, replacor, str)
    let toReplace = a:toReplace
    let replacor = a:replacor
    "get the left most occurrence of toReplace
    let indxToReplace = s:FindDelimiterIndex(toReplace, a:str)

    "if there IS an occurrence of toReplace in str then replace it and return
    "the resulting string
    if indxToReplace != -1
        let line = strpart(a:str, 0, indxToReplace) . replacor . strpart(a:str, indxToReplace+strlen(toReplace))
        return line
    endif

    return a:str
endfunction

" Function: s:ReplaceRightMostDelim(toReplace, replacor, str) {{{2
" This function takes a string and a delimiter and replaces the right most
" occurrence of this delimiter in the string with a given string
"
" Args:
"   -toReplace: the delimiter in str that is to be replaced
"   -replacor: the string to replace toReplace with
"   -str: the string that contains toReplace
"
function s:ReplaceRightMostDelim(toReplace, replacor, str)
    let toReplace = a:toReplace
    let replacor = a:replacor
    let lenToReplace = strlen(toReplace)

    "get the index of the last delimiter in str
    let indxToReplace = s:LastIndexOfDelim(toReplace, a:str)

    "if there IS a delimiter in str, replace it and return the result
    let line = a:str
    if indxToReplace != -1
        let line = strpart(a:str, 0, indxToReplace) . replacor . strpart(a:str, indxToReplace+strlen(toReplace))
    endif
    return line
endfunction

"FUNCTION: s:RestoreScreenState() {{{2
"
"Sets the screen state back to what it was when s:SaveScreenState was last
"called.
"
function s:RestoreScreenState()
    if !exists("t:NERDComOldTopLine") || !exists("t:NERDComOldPos")
        throw 'NERDCommenter exception: cannot restore screen'
    endif

    call cursor(t:NERDComOldTopLine, 0)
    normal! zt
    call setpos(".", t:NERDComOldPos)
endfunction

" Function: s:Right(...) {{{2
" returns right delimiter data
function s:Right(...)
    let params = a:0 ? a:1 : {}

    let delim = has_key(params, 'alt') ? b:NERDCommenterDelims['rightAlt'] : b:NERDCommenterDelims['right']

    if delim == ''
        return ''
    endif

    if has_key(params, 'space') && g:NERDSpaceDelims
        let delim = s:spaceStr . delim
    endif

    if has_key(params, 'esc')
        let delim = s:Esc(delim)
    endif

    return delim
endfunction

" Function: s:RightMostIndx(countCommentedLines, countEmptyLines, topline, bottomline) {{{2
" This function takes in 2 line numbers and returns the index of the right most
" char on all of these lines.
" Args:
"   -countCommentedLines: 1 if lines that are commented are to be checked as
"    well. 0 otherwise
"   -countEmptyLines: 1 if empty lines are to be counted in the search
"   -topline: the top line to be checked
"   -bottomline: the bottom line to be checked
function s:RightMostIndx(countCommentedLines, countEmptyLines, topline, bottomline)
    let rightMostIndx = -1

    " go thru the block line by line updating rightMostIndx
    let currentLine = a:topline
    while currentLine <= a:bottomline

        " get the next line and see if it is commentable, otherwise it doesn't
        " count
        let theLine = getline(currentLine)
        if a:countEmptyLines || theLine !~ '^[ \t]*$'

            if a:countCommentedLines || (!s:IsCommented(s:Left(), s:Right(), theLine) && !s:IsCommented(s:Left({'alt': 1}), s:Right({'alt': 1}), theLine))

                " update rightMostIndx if need be
                let theLine = s:ConvertLeadingTabsToSpaces(theLine)
                let lineLen = strlen(theLine)
                if lineLen > rightMostIndx
                    let rightMostIndx = lineLen
                endif
            endif
        endif

        " move on to the next line
        let currentLine = currentLine + 1
    endwhile

    return rightMostIndx
endfunction

"FUNCTION: s:SaveScreenState() {{{2
"Saves the current cursor position in the current buffer and the window
"scroll position
function s:SaveScreenState()
    let t:NERDComOldPos = getpos(".")
    let t:NERDComOldTopLine = line("w0")
endfunction

" Function: s:SwapOuterMultiPartDelimsForPlaceHolders(line) {{{2
" This function takes a line and swaps the outer most multi-part delimiters for
" place holders
" Args:
"   -line: the line to swap the delimiters in
"
function s:SwapOuterMultiPartDelimsForPlaceHolders(line)
    " find out if the line is commented using normal delimiters and/or
    " alternate ones
    let isCommented = s:IsCommented(s:Left(), s:Right(), a:line)
    let isCommentedAlt = s:IsCommented(s:Left({'alt': 1}), s:Right({'alt': 1}), a:line)

    let line2 = a:line

    "if the line is commented and there is a right delimiter, replace
    "the delimiters with place-holders
    if isCommented && s:Multipart()
        let line2 = s:ReplaceDelims(s:Left(), s:Right(), g:NERDLPlace, g:NERDRPlace, a:line)

    "similarly if the line is commented with the alternative
    "delimiters
    elseif isCommentedAlt && s:AltMultipart()
        let line2 = s:ReplaceDelims(s:Left({'alt': 1}), s:Right({'alt': 1}), g:NERDLPlace, g:NERDRPlace, a:line)
    endif

    return line2
endfunction

" Function: s:SwapOuterPlaceHoldersForMultiPartDelims(line) {{{2
" This function takes a line and swaps the outermost place holders for
" multi-part delimiters
" Args:
"   -line: the line to swap the delimiters in
"
function s:SwapOuterPlaceHoldersForMultiPartDelims(line)
    let left = ''
    let right = ''
    if s:Multipart()
        let left = s:Left()
        let right = s:Right()
    elseif s:AltMultipart()
        let left = s:Left({'alt': 1})
        let right = s:Right({'alt': 1})
    endif

    let line = s:ReplaceDelims(g:NERDLPlace, g:NERDRPlace, left, right, a:line)
    return line
endfunction
" Function: s:TabbedCol(line, col) {{{2
" Gets the col number for given line and existing col number. The new col
" number is the col number when all leading spaces are converted to tabs
" Args:
"   -line:the line to get the rel col for
"   -col: the abs col
function s:TabbedCol(line, col)
    let lineTruncated = strpart(a:line, 0, a:col)
    let lineSpacesToTabs = substitute(lineTruncated, s:TabSpace(), '\t', 'g')
    return strlen(lineSpacesToTabs)
endfunction
"FUNCTION: s:TabSpace() {{{2
"returns a string of spaces equal in length to &tabstop
function s:TabSpace()
    let tabSpace = ""
    let spacesPerTab = &tabstop
    while spacesPerTab > 0
        let tabSpace = tabSpace . " "
        let spacesPerTab = spacesPerTab - 1
    endwhile
    return tabSpace
endfunction

" Function: s:UnEsc(str, escChar) {{{2
" This function removes all the escape chars from a string
" Args:
"   -str: the string to remove esc chars from
"   -escChar: the escape char to be removed
function s:UnEsc(str, escChar)
    return substitute(a:str, a:escChar, "", "g")
endfunction

" Function: s:UntabbedCol(line, col) {{{2
" Takes a line and a col and returns the absolute column of col taking into
" account that a tab is worth 3 or 4 (or whatever) spaces.
" Args:
"   -line:the line to get the abs col for
"   -col: the col that doesn't take into account tabs
function s:UntabbedCol(line, col)
    let lineTruncated = strpart(a:line, 0, a:col)
    let lineTabsToSpaces = substitute(lineTruncated, '\t', s:TabSpace(), 'g')
    return strlen(lineTabsToSpaces)
endfunction
" Section: Comment mapping and menu item setup {{{1
" ===========================================================================

" Create menu items for the specified modes.  If a:combo is not empty, then
" also define mappings and show a:combo in the menu items.
function! s:CreateMaps(modes, target, desc, combo)
    " Build up a map command like
    " 'noremap <silent> <plug>NERDCommenterComment :call NERDComment("n", "Comment")'
    let plug = '<plug>NERDCommenter' . a:target
    let plug_start = 'noremap <silent> ' . plug . ' :call NERDComment("'
    let plug_end = '", "' . a:target . '")<cr>'
    " Build up a menu command like
    " 'menu <silent> comment.Comment<Tab>\\cc <plug>NERDCommenterComment'
    let menuRoot = get(['', 'comment', '&comment', '&Plugin.&comment'],
                \ g:NERDMenuMode, '')
    let menu_command = 'menu <silent> ' . menuRoot . '.' . escape(a:desc, ' ')
    if strlen(a:combo)
        let leader = exists('g:mapleader') ? g:mapleader : '\'
        let menu_command .= '<Tab>' . escape(leader, '\') . a:combo
    endif
    let menu_command .= ' ' . (strlen(a:combo) ? plug : a:target)
    " Execute the commands built above for each requested mode.
    for mode in (a:modes == '') ? [''] : split(a:modes, '\zs')
        if strlen(a:combo)
            execute mode . plug_start . mode . plug_end
            if g:NERDCreateDefaultMappings && !hasmapto(plug, mode)
                execute mode . 'map <leader>' . a:combo . ' ' . plug
            endif
        endif
        " Check if the user wants the menu to be displayed.
        if g:NERDMenuMode != 0
            execute mode . menu_command
        endif
    endfor
endfunction
call s:CreateMaps('nx', 'Comment',    'Comment', 'cc')
call s:CreateMaps('nx', 'Toggle',     'Toggle', 'c<space>')
call s:CreateMaps('nx', 'Minimal',    'Minimal', 'cm')
call s:CreateMaps('nx', 'Nested',     'Nested', 'cn')
call s:CreateMaps('n',  'ToEOL',      'To EOL', 'c$')
call s:CreateMaps('nx', 'Invert',     'Invert', 'ci')
call s:CreateMaps('nx', 'Sexy',       'Sexy', 'cs')
call s:CreateMaps('nx', 'Yank',       'Yank then comment', 'cy')
call s:CreateMaps('n',  'Append',     'Append', 'cA')
call s:CreateMaps('',   ':',          '-Sep-', '')
call s:CreateMaps('nx', 'AlignLeft',  'Left aligned', 'cl')
call s:CreateMaps('nx', 'AlignBoth',  'Left and right aligned', 'cb')
call s:CreateMaps('',   ':',          '-Sep2-', '')
call s:CreateMaps('nx', 'Uncomment',  'Uncomment', 'cu')
call s:CreateMaps('n',  'AltDelims',  'Switch Delimiters', 'ca')
call s:CreateMaps('i',  'Insert',     'Insert Comment Here', '')
call s:CreateMaps('',   ':',          '-Sep3-', '')
call s:CreateMaps('',   ':help NERDCommenterContents<CR>', 'Help', '')

inoremap <silent> <plug>NERDCommenterInsert <SPACE><BS><ESC>:call NERDComment('i', "insert")<CR>

" switch to/from alternative delimiters (does not use wrapper function)
nnoremap <plug>NERDCommenterAltDelims :call <SID>SwitchToAlternativeDelimiters(1)<cr>

" This is a workaround to enable lazy-loading from supported plugin managers:
" See https://github.com/scrooloose/nerdcommenter/issues/176
call s:SetUpForNewFiletype(&filetype, 1)

" vim: set foldmethod=marker :
