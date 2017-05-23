" Vim compiler file
" Compiler:	Coder module
" Maintainer:	Benji Fisher <http://drupal.org/user/683300>
" URL:		http://drupal.org/project/vimrc
" Last Change:	Mon Dec 19 10:00 AM 2011 EST

if exists("current_compiler")
  finish
endif
let current_compiler = "coder"

if exists(":CompilerSet") != 2		" older Vim always used :setlocal
  command -nargs=* CompilerSet setlocal <args>
endif

let s:cpo_save = &cpo
set cpo-=C

if strlen(b:Drupal_info.DRUPAL_ROOT)
  let coder_format = findfile('coder_format.php', b:Drupal_info.DRUPAL_ROOT . '/**')
  if strlen(coder_format)

    execute 'CompilerSet makeprg=php\ ' . coder_format

    CompilerSet errorformat=%f\ processed.

    augroup Drupal
      au! QuickFixCmdPre,QuickFixCmdPost
    augroup END

  endif
endif

let &cpo = s:cpo_save
unlet s:cpo_save
