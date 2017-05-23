" Check PHP and other files to see if they belong to Drupal.

if exists("did_load_filetypes")
  finish
endif

augroup filetypedetect
  " Use :execute in order to use the drupaldetect#php_ext variable.
  execute 'autocmd BufRead,BufNewFile *.{' . drupaldetect#php_ext . '}'
        \ 'if drupaldetect#Check() | setf php | endif'
  autocmd BufRead,BufNewFile *.{info,info.yml,make,build}
        \ if drupaldetect#Check() | setf drini | endif
augroup END
