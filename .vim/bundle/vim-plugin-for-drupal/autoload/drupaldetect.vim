" @file {{{
" Functions that determine whether a file is part of a Drupal project.

" These functions are called from BufRead and BufNewFile autocommands, before
" 'filetype' has been set. They are defined here, not in filetype.vim, so that
" they are also available from other scripts. }}}

" @var s:slash
" Borrowed from autoload/pathogen.vim:
let s:slash = !exists("+shellslash") || &shellslash ? '/' : '\'
" @var drupaldetect#php_ext
let drupaldetect#php_ext = 'php,module,install,inc,profile,theme,engine,test,view'

" @function! drupaldetect#Check(...) " {{{
" Decide whether the current file is part of a Drupal project.
"
" @param (optional)
"   a directory to check instead of the current file's project.
"
" @return
"   1 if the current file is part of a Drupal project;
"   0 otherwise.
function! drupaldetect#Check(...) " {{{
  " Expect something like /var/www/drupal-7.9/sites/all/modules/ctools
  let directory = a:0 ? a:1 : expand('%:p:h')
  let drupal_root = drupaldetect#DrupalRoot(directory)
  let info_path = drupaldetect#InfoPath(directory)
  let core = drupaldetect#CoreVersion(info_path)
  return strlen(drupal_root) || strlen(core)
endfun " }}} }}}

" @function drupaldetect#DrupalRoot(path, ...) {{{
" Try to guess which part of the path is the Drupal root directory.
"
" @param path
"   A string representing a system path.
" @param ... (optional)
"   If present and non-zero, then clear the cached value.
"
" @return
"   A string representing the Drupal root, '' if not found.
let s:drupal_root_cache = {}
function drupaldetect#DrupalRoot(path, ...) " {{{
  " If there is a non-zero optional value, then clear the cache.
  if a:0 && a:1 && has_key(s:drupal_root_cache, a:path)
    unlet s:drupal_root_cache[a:path]
  endif
  " If we have a cached answer, then return it.
  if has_key(s:drupal_root_cache, a:path)
    return s:drupal_root_cache[a:path]
  endif

  " If all the markers are found, assume the directory is the Drupal root.
  " See update_verify_update_archive() for official markers. Define them as
  " lists of path components, then join them with the correct path separator.
  let markers = {7 : [
        \   ['index.php'],
        \   ['update.php'],
        \   ['includes', 'bootstrap.inc'],
        \   ['modules', 'node', 'node.module'],
        \   ['modules', 'system', 'system.module'],
        \ ],
        \ 8 : [
        \   ['index.php'],
        \   ['core', 'install.php'],
        \   ['core', 'includes', 'bootstrap.inc'],
        \   ['core', 'modules', 'node', 'node.module'],
        \   ['core', 'modules', 'system', 'system.module'],
        \ ], }
  for marker_list in values(markers)
    call map(marker_list, 'join(v:val, s:slash)')
  endfor

  " On *nix, start with '', but on Windows typically start with 'C:'.
  let path_components = split(a:path, s:slash, 1)
  let droot = remove(path_components, 0)

  for part in path_components
    let droot .= s:slash . part
    for marker_list in values(markers)
      let is_drupal_root = 1
      for marker in marker_list
        " Since globpath() is built in to vim, this should be fast.
        if globpath(droot, marker) == ''
          let is_drupal_root = 0
          break
        endif
      endfor " marker
      " If all the markers are there, then this looks like a Drupal root.
      if is_drupal_root
        let s:drupal_root_cache[a:path] = droot
        return droot
      endif
    endfor " marker_list
  endfor " part
  let s:drupal_root_cache[a:path] = ''
  return ''
endfun " }}} }}}

" @function drupaldetect#InfoPath(, ...) {{{
" Try to find the .info file of the module, theme, etc. containing a path.
" Update for D8: look for the extension .info.yml.
"
" @param path
"   A string representing a system path.
" @param ... (optional)
"   If present and non-zero, then clear the cached value.
"
" @return
"   A string representing the path of the .info file, '' if not found.
let s:info_path_cache = {}
function drupaldetect#InfoPath(path, ...) " {{{
  " If there is a non-zero optional value, then clear the cache.
  if a:0 && a:1 && has_key(s:info_path_cache, a:path)
    unlet s:info_path_cache[a:path]
  endif
  " If we have a cached answer, then return it.
  if has_key(s:info_path_cache, a:path)
    return s:info_path_cache[a:path]
  endif

  let dir = a:path
  let tail = strridx(dir, s:slash)
  while tail != -1
    " Unfortunately, some systems do not support
    " glob(path.{info,info.yml,make,build})
    " Look for an info file in the directory tail,
    " then a drush make or profile builder info file.
    for ext in ['info', 'info.yml', 'make', 'build']
      let infopath = glob(dir . s:slash . '*.' . ext)
      if strlen(infopath)
        let files = split(infopath, '\n')
        let s:info_path_cache[a:path] = files[0]
        return files[0]
      endif
    endfor
    " No luck yet, so go up one directory.
    let dir = strpart(dir, 0, tail)
    let tail = strridx(dir, s:slash)
  endwhile
  let s:info_path_cache[a:path] = ''
  return ''
endfun " }}} }}}

" @function drupaldetect#CoreVersion(info_path, ...) {{{
" Find the version of Drupal core by parsing the .info file.
"
" @param info_path
"   A string representing the path to the .info or .info.yml file.
" @param ... (optional)
"   If present and non-zero, then clear the cached value.
"
" @return
"   A numeric string representing the Drupal core version.
" {{{
let s:core_version_cache = {}
function drupaldetect#CoreVersion(info_path, ...)
  " Bail out if the path is empty.
  if a:info_path == ''
    return ''
  endif
  " If there is a non-zero optional value, then clear the cache.
  if a:0 && a:1 && has_key(s:core_version_cache, a:info_path)
    unlet s:core_version_cache[a:info_path]
  endif
  " If we have a cached answer, then return it.
  if has_key(s:core_version_cache, a:info_path)
    return s:core_version_cache[a:info_path]
  endif

  " Find the Drupal core version. Strip '.x' from the end.
  let ext = fnamemodify(a:info_path, ':e')
  let core = drupaldetect#ParseInfo(a:info_path, 'core', ext)
  let s:core_version_cache[a:info_path] = matchstr(core, '^\d\+\ze\.x\s*')
  return s:core_version_cache[a:info_path]
endfun " }}} }}}

" @function drupaldetect#ParseInfo(info_path, key, type) {{{
" Find the value corresponding to a key in an info file.
"
" @param info_path
"   A string representing the path to the .info or .info.yml file.
" @param key
"   A string key
" @param type
"   Either 'info' (pre-D8) or 'yml' (D8 and above).
"
" @return
"   String: the corresponding value, or '' if not found.
function! drupaldetect#ParseInfo(info_path, key, type) " {{{
  if !filereadable(a:info_path)
    return ''
  endif
  let lines = readfile(a:info_path, '', 500)
  let marker = (a:type == 'yml') ? ':' : '='
  let regexp = '^\s*' . escape(a:key, '\') . '\s*' . marker . '\s*\zs.*'
  " Find the first line that matches.
  let core_line = matchstr(lines, regexp)
  " Return the part of the line that matches, '' if no match.
  let value = matchstr(core_line, regexp)
  " Trim the result of quotes and double quotes it might have.
  let value = s:Trim(value, "'")
  let value = s:Trim(value, '"')
  return value
endfun " }}} }}}

"""
" Trims the specified character from the beginning and the end of the
" specified string. Trims all repeats of the specified character.
" Returns the resulting string.
"
" If called without a characters argument, trims whitespace.
"
" @param    string    str     The string to be trimmed.
" @param    string    char    The character to remove from the string.
"
" @return   string            The result.
"""
function! s:Trim(str, ...)
  let l:char = '\s'

  if a:0 ==# 1
    let l:char = a:1
  endif

  " \m   sets Vim's nomagic option for this regex. This ensures portability of the regex.
  " ^    matches the beginning of the string.
  " *    matches as many as possible of the preceding character
  " \(   begins a subexpression
  " .    matches any character
  " \{-} matches the previous character as few times as possible
  " \)   ends a subexpression
  " *    matches as many as possible of the preceding character
  " $    matches the end of the string
  let l:regex = '\m^' . l:char . '*\(.\{-}\)' . l:char . '*$'

  " \1   replaces the string with the first subexpression in the match
  let l:result = substitute(a:str, l:regex, '\1', '')

  return l:result
endfunction

