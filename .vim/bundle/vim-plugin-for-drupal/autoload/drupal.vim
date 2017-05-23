" @file autoload/drupal.vim
" Define functions called from ftplugin/drupal.vim.
"
" This file will be loaded as soon as a buffer's file type is set to 'drupal'.

" @function drupal#CreateMaps(modes, menu, key, target, options) {{{
" Create maps and menu items, where the menu items display the mapped keys.
" @param
"   String modes:  the modes for which the map/menu item will be defined, such
"     as 'nv'.
"   String menu:  the menu item. Periods (.) will be escaped:  see also
"     a:options.root.
"   String key:  the key sequence to be mapped.
"   String target:  the result of the map or menu item.
"   Dictionary options:  the keys are all optional.
"     'root':  menu root, prepended to a:menu.
"     'shortcut':  displayed in menu, defaults to a:key.
"     'weight':  weight of the menu item (:help sub-menu-priority).
"     'special':  extra arguments to :map command, one or more of <buffer>,
"       <silent>, <special>, <script>, <expr>, <unique>, separated by
"       spaces. Only <silent>, <special>, <script> apply to the :menu
"       command as well.
" If a:modes == '', then use plain :menu and :map commands.
" If a:menu == '' or a:key == '', then do not define a menu or map, resp.
" Do not escape spaces in a:menu nor a:options.root:  the function will.
function drupal#CreateMaps(modes, menu, key, target, options) " {{{
  let special = ' ' . get(a:options, 'special', '') . ' '
  let map_command = 'map' . special . a:key . ' ' . a:target
  if has_key(a:options, 'root')
    let item = a:options.root . '.' . escape(a:menu, '.')
  else
    let item = escape(a:menu, '.')
  endif
  let specials = filter(split(special), "v:val =~? '^<s'")
  let menu_command = 'menu ' . join(specials)
  if has_key(a:options, 'weight')
    " Prepend one dot for each parent menu.
    let dots = strpart(s:Dots(item), strlen(s:Dots(a:options.weight)))
    let menu_command .= ' ' . dots . a:options.weight
  endif
  let menu_command .= ' ' . escape(item, ' ')
  let shortcut = get(a:options, 'shortcut', a:key)
  if strlen(shortcut)
    let leader = exists('mapleader') ? mapleader : '\'
    let shortcut = substitute(shortcut, '\c<leader>', escape(leader, '\'), 'g')
    let lleader = exists('maplocalleader') ? maplocalleader : '\'
    let shortcut = substitute(shortcut, '\c<localleader>', escape(lleader, '\'), 'g')
    if !has('macunix')
      let menu_command .= '<Tab>'
    else
      " Menu shortcuts work differently on the Mac, so use escaped spaces.
      let len = strlen(a:menu . shortcut)
      let menu_command .= repeat('\ ', max([1, 20 - len]))
    endif
    let menu_command .= escape(shortcut, ' \')
  endif
  let menu_command .= ' ' . a:target
  " Execute the commands built above for each requested mode.
  for mode in (a:modes == '') ? [''] : split(a:modes, '\zs')
    if strlen(a:key)
      execute mode . map_command
    endif
    if strlen(a:menu)
      execute mode . menu_command
    endif
  endfor
endfunction " }}} }}}

" @function s:Dots(menuPath) {{{
" Remove everything but unescaped dots.
" @param
"   String menuPath:  any string, such as 'Foo.bar.item'.
" @return
"   String:  in the example, '..'.
" {{{
function! s:Dots(menuPath)
  let dots = substitute(a:menuPath, '\\\\', '', 'g')
  let dots = substitute(dots, '\\\.', '', 'g')
  let dots = substitute(dots, '[^.]', '', 'g')
  return dots
endfunction " }}} }}}

" @function drupal#BufEnter() {{{
" There are some things that we *wish* were local to the buffer.  We stuff
" them into this function and call them from a BufEnter <buffer> autocommand.
" - @var $DRUPAL_ROOT
"   Set this environment variable from b:Drupal_info.DRUPAL_ROOT.
" - SnipMate settings
let s:snip_path = expand('<sfile>:p:h:h') . '/snippets/drupal'
function! drupal#BufEnter() " {{{
  if strlen(b:Drupal_info.DRUPAL_ROOT)
    let $DRUPAL_ROOT = b:Drupal_info.DRUPAL_ROOT
  endif
  " Garbas' snipmate is already aware of version-indepedent snippets
  " so we load the scope for the version-dependent snippets.
  if strlen(b:Drupal_info.CORE) && exists(':SnipMateLoadScope')
    exec 'SnipMateLoadScope drupal' . b:Drupal_info.CORE
  endif
  " Load snippets for the snipmate version on vimscripts.
  if exists('*ExtractSnips')
    call ResetSnippets('drupal')
    " Load the version-independent snippets.
    let snip_path = s:snip_path . '/'
    for ft in split(&ft, '\.')
      call ExtractSnips(snip_path . ft, 'drupal')
      call ExtractSnipsFile(snip_path . ft . '.snippets', 'drupal')
    endfor
    " If we know the version of Drupal, add the coresponding snippets.
    if strlen(b:Drupal_info.CORE)
      let snip_path = s:snip_path . b:Drupal_info.CORE . '/'
      for ft in split(&ft, '\.')
        call ExtractSnips(snip_path . ft, 'drupal')
        call ExtractSnipsFile(snip_path . ft . '.snippets', 'drupal')
      endfor
    endif " strlen(b:Drupal_info.CORE)
  endif " exists('*ExtractSnips')
endfun " }}}

" @function drupal#OpenURL(base) " {{{
function drupal#OpenURL(base) " {{{
  let open = b:Drupal_info.OPEN_COMMAND
  if open == ''
    return
  endif
  " Get the word under the cursor.
  let func = expand('<cword>')
  " Some API sites let you specify which Drupal version you want.
  let core = strlen(b:Drupal_info.CORE) ? b:Drupal_info.CORE . '/' : ''
  " Custom processing for several API sites.
  if a:base == 'api.d.o'
    let url = 'http://api.drupal.org/api/search/' . core
  elseif a:base == 'hook'
    let url = 'http://api.drupal.org/api/search/' . core
    " Find the module or theme name and replace it with 'hook'.
    let root = expand('%:t:r')
    let func = substitute(func, '^' . root, 'hook', '')
  elseif a:base == 'drupalcontrib'
    let url = 'http://drupalcontrib.org/api/search/' . core
  else
    let url = a:base
    execute '!' . open . ' ' . a:base . func
  endif
  call system(open . ' ' . url . shellescape(func))
endfun " }}} }}}

" function! s:FindPath(dirs, subpath, condition) " {{{
" Utility function:  find a path satisfying a condition
" @param
"   List dirs: each entry is a String representing a directory, ending in '/'
"   String subpath: a subpath to look for inside each directory
"   String condition: a condition to be evaluated on path = directory . subpath
" @return String
"   The path satisfying the condition, '' if none is found.
function! s:FindPath(dirs, subpath, condition) " {{{
  for dir in a:dirs
    let path = dir . a:subpath
    execute 'let success =' a:condition
    if success
      return path
    endif
  endfor
  return ''
endfun  " }}} }}}

" @function! drupal#CtagsPath() " {{{
" Return path to exuberant ctags, or '' if not found.
function! drupal#CtagsPath() " {{{
  let dirs = ['', '/usr/bin/', '/usr/local/bin/']
  let condition = 'executable(path) && system(path . "--version") =~ "Exuberant Ctags"'
  return s:FindPath(dirs, 'ctags', condition)
endfun
" }}} }}}

" @function! drupal#PhpcsPath() " {{{
" Return path to phpcs (PHP CodeSniffer), or '' if not found.
function! drupal#PhpcsPath() " {{{
  let dirs = ['', $HOME . '/.composer/vendor/bin/', '/usr/local/bin/']
  return s:FindPath(dirs, 'phpcs', 'executable(path)')
endfun
" }}} }}}
let drupal#phpcs_exec = drupal#PhpcsPath()

" @function! drupal#CodeSnifferPath() " {{{
" Return path to Drupal standards for PHP CodeSniffer, or '' if not found.
function! drupal#CodeSnifferPath() " {{{
  " First check whether phpcs already knows about Drupal. If so, then return
  " 'Drupal' instead of a complete path.
  let standard = matchstr(system(g:drupal#phpcs_exec . ' -i'), '\c\<Drupal\>')
  if strlen(standard)
    return standard
  endif
  " Next, look for the Drupal standards in the locations corresponding to the
  " instructions for installing the Coder module:
  " https://www.drupal.org/node/1419988
  let dirs = [$HOME . '/.composer/vendor/drupal/', $HOME . '/.drush/']
  return s:FindPath(dirs, 'coder/coder_sniffer/Drupal', 'isdirectory(path)')
endfun
" }}} }}}
let drupal#codesniffer_standard = drupal#CodeSnifferPath()

" @function! drupal#PhpcsArgs() " {{{
" Return the arguments that should be added to phpcs.
function! drupal#PhpcsArgs() " {{{
  let args = {
	\ 'standard': g:drupal#codesniffer_standard,
	\ 'report': 'csv',
	\ 'extensions': g:drupaldetect#php_ext
	\ }
  call filter(args, 'strlen(v:val)')
  return join(map(items(args), '"--" . v:val[0] . "=" . v:val[1]'))
endfun
" }}} }}}
let drupal#phpcs_args = drupal#PhpcsArgs()

" @function! drupal#TagGen(type)" {{{
" Invoke ctags via drush, either for the current project or for the Drupal
" root.
"
" @param type
"   Either 'project' or 'drupal'.
function! drupal#TagGen(type) " {{{
  let ctags = drupal#CtagsPath()
  if strlen(ctags) == 0
    return
  endif
  let options = ' --ctags=' . ctags
  if a:type == 'project' && b:Drupal_info.INFO_FILE != ''
    let tagdir = fnamemodify(b:Drupal_info.INFO_FILE, ':h')
  elseif a:type == 'drupal' && b:Drupal_info.DRUPAL_ROOT != ''
    let tagdir = b:Drupal_info.DRUPAL_ROOT
    " let options .= ' --make-portable=yes'
  else
    return
  endif
  let options .= ' --tag-file=' . tagdir . '/tags'
  execute 'Drush vimrc-tag-gen ' . options . ' ' . tagdir
endfun
" }}} }}}

" @function drupal#DrupalInfo() {{{
"
" @return Dictionary
" Some information for use by ftplugin and syntax scripts.  The keys are
" - DRUPAL_ROOT
"   path to the Drupal root
" - INFO_FILE
"   path to the .info file of the containing module, theme, etc.
" - TYPE
"   'module' or 'theme' or 'make'
" - OPEN_COMMAND
"   'open' or 'xdg-open' or 'cmd /c start', depending on the OS
" In all cases, the values will be '' if we cannot make a reasonable guess.
function! drupal#DrupalInfo() " {{{
  " Expect something like /var/www/drupal-7.9/sites/all/modules/ctools
  let path = expand('%:p')
  let directory = fnamemodify(path, ':h')
  let info = {'DRUPAL_ROOT': drupaldetect#DrupalRoot(directory),
	\ 'INFO_FILE': drupaldetect#InfoPath(directory)}
  let info.OPEN_COMMAND = drupal#OpenCommand()
  let info.TYPE = drupal#IniType(info.INFO_FILE)
  let info.CORE = drupaldetect#CoreVersion(info.INFO_FILE)
  " If we found only one of CORE and DRUPAL_ROOT, use it to get the other.
  if info.CORE == '' && info.DRUPAL_ROOT != ''
    let INFO_FILE = info.DRUPAL_ROOT . '/modules/system/system.info'
    if filereadable(INFO_FILE)
      " Looks like we are dealing with Drupal 6/7.
      let info.CORE = drupaldetect#CoreVersion(INFO_FILE)
    else
      let INFO_FILE = info.DRUPAL_ROOT . '/core/modules/system/system.info.yml'
      if filereadable(INFO_FILE)
        " Looks like we are dealing with Drupal 8.
        let info.CORE = drupaldetect#CoreVersion(INFO_FILE)
      endif
    endif
  elseif info.DRUPAL_ROOT == '' && info.CORE != ''  && exists('g:Drupal_dirs')
    let info.DRUPAL_ROOT = get(g:Drupal_dirs, info.CORE, '')
  endif

  return info
endfun " }}} }}}

" @function drupal#OpenCommand() {{{
" Return a string that can be used to open URL's (and other things).
" Usage:
" let open = drupal#OpenCommand()
" if strlen(open) | execute '!' . open . ' http://example.com' | endif
" @see http://www.dwheeler.com/essays/open-files-urls.html
function! drupal#OpenCommand() " {{{
if has('win32unix') && executable('cygstart')
  return 'cygstart'
elseif has('unix') && executable('xdg-open')
  return 'xdg-open'
elseif (has('win32') || has('win64')) && executable('cmd')
  return 'cmd /c start'
elseif (has('macunix') || has('unix') && system('uname') =~ 'Darwin')
      \ && executable('open')
  return 'open'
else
  return ''
endif
endfun " }}} }}}

" @function drupal#IniType(info_path) {{{
" Find the type (module, theme, make) by parsing the path. For D8, first try
" parsing the .info.yml file.
"
" @param info_path
"   A string representing the path to the .info file.
"
" @return
"   A string:  module, theme, make
"
" @todo:  How do we recognize a Profiler .info file?
function! drupal#IniType(info_path) " {{{
  " Determine make files by their extensions. Parse .yml files.
  let ext = fnamemodify(a:info_path, ':e')
  if ext == 'make' || ext == 'build'
    return 'make'
  elseif ext == 'yml'
    let type = drupaldetect#ParseInfo(a:info_path, 'type', 'yml')
    if strlen(type)
      return type
    endif
  endif

  " If we are not done yet, then parse the path.
  " Borrowed from autoload/pathogen.vim:
  let slash = !exists("+shellslash") || &shellslash ? '/' : '\'
  " If the extension is not 'info' at this point, I do not know how we got
  " here.
  let m_index = strridx(a:info_path, slash . 'modules' . slash)
  let t_index = strridx(a:info_path, slash . 'themes' . slash)
  " If neither matches, try a case-insensitive search.
  if m_index == -1 && t_index == -1
    let m_index = matchend(a:info_path, '\c.*\' . slash . 'modules\' . slash)
    let t_index = matchend(a:info_path, '\c.*\' . slash . 'themes\' . slash)
  endif
  if m_index > t_index
    return 'module'
  elseif m_index < t_index
    return 'theme'
  endif
  " We are not inside a themes/ directory, nor a modules/ directory.  Do not
  " guess.
  return ''
endfun " }}} }}}

" @function! drupal#SetDrupalRoot() " {{{
function! drupal#SetDrupalRoot() " {{{
  let dir = input('Drupal root directory: ', b:Drupal_info.DRUPAL_ROOT, 'file')
  let b:Drupal_info.DRUPAL_ROOT = expand(substitute(dir, '[/\\]$', '', ''))
  if strlen(dir)
    let INFO_FILE = b:Drupal_info.DRUPAL_ROOT . '/modules/system/system.info'
    if filereadable(INFO_FILE)
      let b:Drupal_info.CORE = drupaldetect#CoreVersion(INFO_FILE)
    endif
  endif
endfun " }}} }}}
