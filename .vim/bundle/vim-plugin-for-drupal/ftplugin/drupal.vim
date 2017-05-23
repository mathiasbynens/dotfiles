" We never :set ft=drupal.  This filetype is always added to another, as in
" :set ft=php.drupal or :set ft=css.drupal.

" Just in case someone is still using Vim in 'compatible' mode.
let s:keepcpo= &cpo
set cpo&vim

" @var b:Drupal_info
" drupal#DrupalInfo() will return a Dictionary containing useful information.
let b:Drupal_info = drupal#DrupalInfo()

" The tags file can be used for PHP omnicompletion even if $DRUPAL_ROOT == ''.
" If $DRUPAL_ROOT is set correctly, then the tags file can also be used for
" tag searches. Look for tags files in the project (module, theme, etc.)
" directory, the Drupal root directory, and in ../tagfiles/.
" TODO:  If we do not know which version of Drupal core, add no tags file or
" all?
let tags = []
if strlen(b:Drupal_info.INFO_FILE)
  let tags += [fnamemodify(b:Drupal_info.INFO_FILE, ':p:h') . '/tags']
endif
if strlen(b:Drupal_info.DRUPAL_ROOT)
  let tags += [fnamemodify(b:Drupal_info.DRUPAL_ROOT, ':p:h') . '/tags']
endif
if strlen(b:Drupal_info.CORE)
  let tagfile = 'drupal' . b:Drupal_info.CORE . '.tags'
  " <sfile>:p = .../vimrc/bundle/vim-plugin-for-drupal/ftplugin/drupal.vim
  let tags += [expand('<sfile>:p:h:h') . '/tagfiles/' . tagfile]
endif
for tagfile in tags
  " Bail out if the tags file has already been added.
  if stridx(&l:tags, tagfile) == -1
    " This is like :setlocal tags += ... but without having to escape special
    " characters.
    " :help :let-option
    let &l:tags .= ',' . tagfile
  endif
endfor

" Maybe someday 'tags' will be made |global-local|. Until then, including this
" is a no-op.
let s:undo_ftplugin = 'setlocal tags<'

" {{{ PHP specific settings.
" In ftdetect/drupal.vim we set ft=php.drupal.  This means that the settings
" here will come after those set by the PHP ftplugins.  In particular, we can
" override the 'comments' setting.

if &ft =~ '\<php\>'
  " In principle, PHP is case-insensitive, but Drupal coding standards pay
  " attention to case. This option affects searching in files and also tag
  " searches and code completion. If you want a case-insensitive search, start
  " the pattern with '\c'.
  setl noignorecase
  " Format comment blocks.  Just type / on a new line to close.
  " Recognize // (but not #) style comments.
  setl comments=sr:/**,m:*\ ,ex:*/,://

  " Syntastic settings, adapted from
  " echodittolabs.org/drupal-coding-standards-vim-code-sniffer-syntastic-regex
  if exists('loaded_syntastic_plugin') && strlen(drupal#phpcs_exec)
    let g:syntastic_php_phpcs_exec = drupal#phpcs_exec
    let g:syntastic_php_phpcs_args = drupal#phpcs_args
  endif

  " Cf. comment on 'tags':  'ignorecase' is global.
  let s:undo_ftplugin .= ' ignorecase< comments<'
endif
" }}} PHP specific settings.

" {{{ Javascript specific settings.
" This plugins does 'set ft=javascript.drupal'.  This means that the
" settings here will come after those set by the javascript ftplugins.
if &ft =~ '\<javascript\>'
  " Add eslint to the checkers array. There is no need to check for the binary
  " as in phpcs, syntastic will handle it.
  if exists('loaded_syntastic_plugin')
    if !exists('b:syntastic_javascript_checkers')
      let b:syntastic_checkers = ['eslint']
    elseif index(b:syntastic_checkers, 'eslint') == -1
      call add(b:syntastic_checkers, 'eslint')
    endif
  endif
endif
" }}} Javascript specific settings.

" Vdebug settings. {{{
if !exists('g:vdebug_features')
  let g:vdebug_features = {}
endif
" Useful for Drupal's deeply nested arrays.
if !exists('g:vdebug_features.max_children') || g:vdebug_features.max_children < 128
  let g:vdebug_features.max_children = 128
endif
" }}} Vdebug settings.

setl autoindent              "Auto indent based on previous line
setl expandtab               "Tab key inserts spaces
setl nojoinspaces            "No second space when joining lines that end in "."
setl shiftwidth=2            "Use two spaces for auto-indent
setl smartindent             "Smart autoindenting on new line
setl smarttab                "Respect space/tab settings
setl tabstop=2               "Use two spaces for tabs
setl textwidth=80            "Limit comment lines to 80 characters.
"  -t:  Do not apply 'textwidth' to code.
"  +c:  Apply 'textwidth' to comments.
"  +r:  Continue comments after hitting <Enter> in Insert mode.
"  +o:  Continue comments after when using 'O' or 'o' to open a new line.
"  +q:  Format comments using q<motion>.
"  +l:  Do not break a comment line if it is long before you start.
setl formatoptions-=t
setl formatoptions+=croql

" Cf. comment on 'tags':  'joinspaces' and 'smarttab' are global.
let s:undo_ftplugin .= ' autoindent< expandtab< joinspaces< shiftwidth<
      \ smartindent< smarttab< tabstop< textwidth<'

" Done setting options, and the next line may finish the script.
if exists("b:undo_ftplugin")
  let b:undo_ftplugin = s:undo_ftplugin . ' | ' . b:undo_ftplugin
else
  let b:undo_ftplugin = s:undo_ftplugin
endif

" Some options will be set by other ftplugin files, and some will be reset to
" their global values when ftplugin.vim executes b:undo_ftplugin, so do not
" :finish before setting all options as above. The commands below do not have
" to be repeated when re-entering a buffer.
"
" The usual variable, b:did_ftplugin, is already set by the ftplugin for the
" primary filetype, so use a custom variable.
if exists("b:did_drupal_ftplugin")  && exists("b:did_ftplugin") | let &cpo = s:keepcpo | finish | endif
let b:did_drupal_ftplugin = 1

augroup Drupal
  autocmd! BufEnter <buffer> call drupal#BufEnter()
augroup END

" {{{ Menu items

let s:options = {'root': 'Drupal', 'special': '<buffer>'}
if strlen(b:Drupal_info.OPEN_COMMAND) " {{{

  " Lookup the API docs for a drupal function under cursor.
  nmap <Plug>DrupalAPI :silent call drupal#OpenURL('api.d.o')<CR><C-L>
  call drupal#CreateMaps('n', 'Drupal API', '<LocalLeader>da',
	\ '<Plug>DrupalAPI', s:options)

  " Lookup the API docs for a drupal hook under cursor.
  nmap <Plug>DrupalHook :silent call drupal#OpenURL('hook')<CR><C-L>
  call drupal#CreateMaps('n', 'Drupal Hook', '<LocalLeader>dh',
	\ '<Plug>DrupalHook', s:options)

  " Lookup the API docs for a contrib function under cursor.
  nmap <Plug>DrupalContribAPI :silent call drupal#OpenURL('drupalcontrib')<CR><C-L>
  call drupal#CreateMaps('n', 'Drupal contrib', '<LocalLeader>dc',
	\ '<Plug>DrupalContribAPI', s:options)

  " Lookup the API docs for a drush function under cursor.
  nmap <Plug>DrushAPI :silent call drupal#OpenURL("http://api.drush.ws/api/function/")<CR><C-L>
  call drupal#CreateMaps('n', 'Drush API', '<LocalLeader>dda',
	\ '<Plug>DrushAPI', s:options)
endif " }}}

" Get the value of the drupal variable under cursor.
nnoremap <buffer> <LocalLeader>dv :execute "!drush vget ".shellescape(expand("<cword>"), 1)<CR>
  call drupal#CreateMaps('n', 'variable_get', '<LocalLeader>dv',
	\ ':execute "!drush vget ".shellescape(expand("<cword>"), 1)<CR>',
	\ s:options)

" Tag commands.
let s:options = {'root': 'Drupal.Tags', 'shortcut': '<C-]>', 'weight': '100.'}
let s:descriptions = [
      \ ['<C-]>', 'Tag under cursor'],
      \ ['<C-W>]', 'Ditto, split window'],
      \ [':tag ', 'Go to a tag.'],
      \ [':stag ', 'Ditto, split window'],
      \ [':tag /', 'Search for tag.'],
      \ [':stag /', 'Ditto, split window'],
      \ [':tag /', 'Search for tag.'],
      \ [':stag /', 'Ditto, split window'],
      \ [':ts<CR>', 'Choose one match.'],
      \ ]
for [s:key, s:text] in s:descriptions
  let s:options.shortcut = s:key
  call drupal#CreateMaps('n', s:text, '', s:key, s:options)
endfor
unlet s:options.shortcut

if strlen(drupal#CtagsPath())
  call drupal#CreateMaps('n', '-Drupal.Tags Sep-', '', ':', s:options)
  call drupal#CreateMaps('n', 'tag-gen options', '',
        \ ':Drush help vimrc-tag-gen<CR>', s:options)
  nmap <Plug>DrupalTagGenProject :call drupal#TagGen('project')<CR>
  call drupal#CreateMaps('n', 'tag-gen current project', '',
        \ '<Plug>DrupalTagGenProject', s:options)
  nmap <Plug>DrupalTagGenRoot :call drupal#TagGen('drupal')<CR>
  call drupal#CreateMaps('n', 'tag-gen Drupal root', '',
        \ '<Plug>DrupalTagGenRoot', s:options)
endif

" Drupal.Configure menu.
nmap <Plug>DrupalSetRoot :call drupal#SetDrupalRoot()<CR>
let s:options = {'root': 'Drupal.Configure', 'weight': '900.'}
call drupal#CreateMaps('n', 'Set Drupal root', '', '<Plug>DrupalSetRoot', s:options)
call drupal#CreateMaps('n', 'Show Drupal info', '', ':echo b:Drupal_info<CR>', s:options)

" End of menu items. }}}

" Restore the saved compatibility options.
let &cpo = s:keepcpo
