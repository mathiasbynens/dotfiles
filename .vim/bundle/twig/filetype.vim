if exists("did_load_filetypes")
  finish
endif
augroup filetypedetect
  au BufRead,BufNewFile *.twig call s:Setf(expand('<amatch>'))
augroup END

function! s:Setf(filename)
  " Check verbose as in autoload/gzip.vim .
  let prefix = (&verbose < 8) ? 'silent!' : ''

  " Use the base filename to set the filetype, but save autocommands for
  " later, so that we do not execute them twice.
  let ei_save = &eventignore
  set eventignore=FileType
  try
    let basefile = fnamemodify(a:filename, ':r')
    execute prefix 'doau BufRead' basefile
  finally
    let &eventignore = ei_save
  endtry

  if !strlen(&ft)
    " Default to HTML twig template.
    let ft = 'html.twig'
  else
    let ft = &ft . (&ft =~ '\<twig\>' ? '' : '.twig')
  endif
  execute prefix 'set filetype=' . ft
endfun
