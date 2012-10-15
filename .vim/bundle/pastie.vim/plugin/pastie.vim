" pastie.vim - Interface for pastie.org
" Maintainer:   Tim Pope <vimNOSPAM@tpope.org>
" URL:          http://www.vim.org/scripts/script.php?script_id=1624
" GetLatestVimScripts: 1624 1 :AutoInstall: pastie.vim

if exists("g:loaded_pastie") || &cp
    finish
endif
let g:loaded_pastie = 1

augroup pastie
    autocmd!
    autocmd BufReadPre  http://pastie.org/*[0-9]?key=*           call s:extractcookies(expand("<amatch>"))
    autocmd BufReadPost http://pastie.org/*[0-9]?key=*           call s:PastieSwapout(expand("<amatch>"))
    autocmd BufReadPost http://pastie.org/*[0-9]                 call s:PastieSwapout(expand("<amatch>"))
    autocmd BufReadPost http://pastie.org/pastes/*[0-9]/download call s:PastieRead(expand("<amatch>"))
    autocmd BufReadPost http://pastie.org/*[0-9].*               call s:PastieRead(expand("<amatch>"))
    autocmd BufWriteCmd http://pastie.org/pastes/*[0-9]/download call s:PastieWrite(expand("<amatch>"))
    autocmd BufWriteCmd http://pastie.org/*[0-9].*               call s:PastieWrite(expand("<amatch>"))
    autocmd BufWriteCmd http://pastie.org/pastes/                call s:PastieWrite(expand("<amatch>"))

    autocmd BufReadPre  http://pastie.caboo.se/*[0-9]?key=*           call s:extractcookies(expand("<amatch>"))
    autocmd BufReadPost http://pastie.caboo.se/*[0-9]?key=*           call s:PastieSwapout(expand("<amatch>"))
    autocmd BufReadPost http://pastie.caboo.se/*[0-9]                 call s:PastieSwapout(expand("<amatch>"))
    autocmd BufReadPost http://pastie.caboo.se/pastes/*[0-9]/download call s:PastieRead(expand("<amatch>"))
    autocmd BufReadPost http://pastie.caboo.se/*[0-9].*               call s:PastieRead(expand("<amatch>"))
    autocmd BufWriteCmd http://pastie.caboo.se/pastes/*[0-9]/download call s:PastieWrite(expand("<amatch>"))
    autocmd BufWriteCmd http://pastie.caboo.se/*[0-9].*               call s:PastieWrite(expand("<amatch>"))
    autocmd BufWriteCmd http://pastie.caboo.se/pastes/                call s:PastieWrite(expand("<amatch>"))
augroup END

let s:domain = "pastie.org"

let s:dl_suffix = ".txt" " Used only for :file

if !exists("g:pastie_destination")
    if version >= 700
        let g:pastie_destination = 'tab'
    else
        let g:pastie_destination = 'window'
    endif
    "let g:pastie_destination = 'buffer'
endif

command! -bar -bang -nargs=* -range=0 -complete=file Pastie :call s:Pastie(<bang>0,<line1>,<line2>,<count>,<f-args>)

function! s:Pastie(bang,line1,line2,count,...)
    if exists(":tab")
        let tabnr = tabpagenr()
    endif
    let newfile = "http://".s:domain."/pastes/"
    let loggedin = 0
    let ft = &ft
    let num = 0
    if a:0 == 0 && a:count == a:line1 && a:count > line('$')
        let num = a:count
    elseif a:0 == 0 && a:line1 == 0 && a:line2 == 0
        let num = s:latestid()
        if num == 0
            return s:error("Could not determine latest paste")
        endif
    elseif !a:count && a:0 == 1
        if a:1 == '*'
            let numcheck = @*
        elseif a:1 == '+'
            let numcheck = @+
        elseif a:1 == '@'
            let numcheck = @@
        else
            let numcheck = a:1
        endif
        let numcheck = substitute(numcheck,'\n\+$','','')
        let numcheck = substitute(numcheck,'^\n\+','','g')
        if numcheck =~ '\n'
            let numcheck = ''
        endif
        if numcheck =~ '^\d\d+$'
            let num = numcheck
        elseif numcheck =~ '\%(^\|/\)\d\+?key=\x\{8,\}'
            if exists("b:pastie_fake_login")
                unlet b:pastie_fake_login
            else
                call s:extractcookies('/'.matchstr(numcheck,'\%(^\|/\)\zs\d\+?.*'))
            endif
            if exists("g:pastie_account")
                let loggedin = 1
            endif
            let num = matchstr(numcheck,'\%(^\|/\)\zs\d\+\ze?')
        elseif numcheck =~ '\%(^\|^/\|^http://.*\)\d\+\%([/?]\|$\)'
            let num = matchstr(numcheck,'\%(^\|/\)\zs\d\+')
        endif
    endif
    if num
        call s:newwindow()
        let file = "http://".s:domain."/".num.s:dl_suffix
        silent exe 'doautocmd BufReadPre '.file
        silent exe 'read !ruby -rnet/http -e "r = Net::HTTP.get_response(\%{'.s:domain.'}, \%{/pastes/'.num.'/download}); if r.code == \%{200} then print r.body else exit 10+r.code.to_i/100 end"'
        if v:shell_error && v:shell_error != 14 && v:shell_error !=15
            return s:error("Something went wrong: shell returned ".v:shell_error)
        else
            let err = v:shell_error
            silent exe "file ".file
            1d_
            set nomodified
            call s:dobufreadpost()
            if err
                if loggedin
                    let b:pastie_update = 1
                else
                    echohl WarningMsg
                    echo "Warning: Failed to retrieve existing paste"
                    echohl None
                endif
            endif
            "call s:PastieRead(file)
            if a:bang
                " Instead of saving an identical paste, take ! to mean "do not
                " create a new paste on first save"
                let b:pastie_update = 1
            endif
            return
        endif
    elseif a:0 == 0 && !a:count && a:bang && expand("%") =~ '^http://'.s:domain.'/\d\+'
        " If the :Pastie! form is used in an existing paste, switch to
        " updating instead of creating.
        "echohl Question
        echo "Will update, not create"
        echohl None
        let b:pastie_update = 1
        return
    elseif a:0 == 1 && !a:count && a:1 =~ '^[&?]\x\{32,\}'
        " Set session id with :Pastie&deadbeefcafebabe
        let g:pastie_session_id = strpart(a:1,1)
    elseif a:0 == 1 && !a:count && (a:1 == '&' || a:1 == '?')
        " Extract session id with :Pastie&
        call s:cookies()
        if exists("g:pastie_session_id")
            echo g:pastie_session_id
            "silent! let @* = g:pastie_session_id
        endif
    elseif a:0 == 0 && !a:count && a:line1
        let ft = 'conf'
        let sum = ""
        let cnt = 0
        let keep = @"
        windo let tmp = s:grabwin() | if tmp != "" | let cnt = cnt + 1 | let sum = sum . tmp | end
        let sum = substitute(sum,'\n\+$',"\n",'')
        if cnt == 1
            let ft = matchstr(sum,'^##.\{-\} \[\zs\w*\ze\]')
            if ft != ""
                let sum = substitute(sum,'^##.\{-\} \[\w*\]\n','','')
            endif
        endif
        call s:newwindow()
        silent exe "file ".newfile
        "silent exe "doautocmd BufReadPre ".newfile
        if sum != ""
            let @" = sum
            silent $put
            1d _
        endif
        if ft == 'plaintext' || ft == 'plain_text'
            "set ft=conf
        elseif ft != '' && sum != ""
            let &ft = ft
        endif
        let @" = keep
        call s:dobufreadpost()
    else
        let keep = @"
        let args = ""
        if a:0 > 0 && a:1 =~ '^[-"@0-9a-zA-Z:.%#*+~_/]$'
            let i = 1
            let register = a:1
        else
            let i = 0
            let register = ""
        endif
        while i < a:0
            let i = i+1
            if strlen(a:{i})
                let file = fnamemodify(expand(a:{i}),':~:.')
                let args = args . file . "\n"
            endif
        endwhile
        let range = ""
        if a:count
            silent exe a:line1.",".a:line2."yank"
            let range = @"
            let @" = keep
        endif
        call s:newwindow()
        silent exe "file ".newfile
        "silent exe "doautocmd BufReadPre ".newfile
        if range != ""
            let &ft = ft
            let @" = range
            silent $put
        endif
        if register != '' && register != '_'
            "exe "let regvalue = @".register
            silent exe "$put ".(register =~ '^[@"]$' ? '' : register)
        endif
        while args != ''
            let file = matchstr(args,'^.\{-\}\ze\n')
            let args = substitute(args,'^.\{-\}\n','','')
            let @" = "## ".file." [".s:parser(file)."]\n"
            if a:0 != 1 || a:count
                silent $put
            else
                let &ft = s:filetype(file)
            endif
            silent exe "$read ".substitute(file,' ','\ ','g')
        endwhile
        let @" = keep
        1d_
        call s:dobufreadpost()
        if (a:0 + (a:count > 0)) > 1
            set ft=conf
        endif
    endif
    1
    call s:afterload()
    if a:bang
        write
        let name = bufname('%')
        " TODO: re-echo the URL in a way that doesn't disappear. Stupid Vim.
        silent! bdel
        if exists("tabnr")
            silent exe "norm! ".tabnr."gt"
        endif
    endif
endfunction

function! s:dobufreadpost()
    if expand("%") =~ '/\d\+\.\@!'
        silent exe "doautocmd BufReadPost ".expand("%")
    else
        silent exe "doautocmd BufNewFile ".expand("%")
    endif
endfunction

function! s:PastieSwapout(file)
    if a:file =~ '?key='
        let b:pastie_fake_login = 1
    endif
    exe "Pastie ".a:file
endfunction

function! s:PastieRead(file)
    let lnum = line(".")
    silent %s/^!!\(.*\)/\1 #!!/e
    exe lnum
    set nomodified
    let num = matchstr(a:file,'/\@<!/\zs\d\+')
    let url = "http://".s:domain."/pastes/".num
    "let url = substitute(a:file,'\c/\%(download/\=\|text/\=\)\=$','','')
    let url = url."/download"
    let result = system('ruby -rnet/http -e "puts Net::HTTP.get_response(URI.parse(%{'.url.'}))[%{Content-Disposition}]"')
    let fn = matchstr(result,'filename="\zs.*\ze"')
    let &ft = s:filetype(fn)
    if &ft =~ '^\%(html\|ruby\)$' && getline(1).getline(2).getline(3) =~ '<%'
        set ft=eruby
    endif
    call s:afterload()
endfunction

function! s:afterload()
    set commentstring=%s\ #!! "
    hi def link pastieIgnore    Ignore
    hi def link pastieNonText   NonText
    if exists(":match")
        hi def link pastieHighlight MatchParen
        if version >= 700
            2match pastieHighlight /^!!\s*.*\|^.\{-\}\ze\s*#!!\s*$/
        else
            match  pastieHighlight /^!!\s*.*\|^.\{-\}\ze\s*#!!\s*$/
        endif
    else
        hi def link pastieHighlight Search
        syn match pastieHighlight '^.\{-\}\ze\s*#!!\s*$' nextgroup=pastieIgnore skipwhite
        syn region pastieHighlight start='^!!\s*' end='$' contains=pastieNonText
    endif
    syn match pastieIgnore '#!!\ze\s*$' containedin=rubyComment,rubyString
    syn match pastieNonText '^!!' containedin=rubyString
endfunction

function! s:PastieWrite(file)
    let parser = s:parser(&ft)
    let tmp = tempname()
    let num = matchstr(a:file,'/\@<!/\zs\d\+')
    if num == ''
        let num = 'pastes'
    endif
    if exists("b:pastie_update") && s:cookies() != '' && num != ""
        let url = "/pastes/".num
        let method = "_method=put&"
    else
        let url = "/pastes"
        let method = ""
    endif
    if exists("b:pastie_display_name")
        let pdn = "&paste[display_name]=".s:urlencode(b:pastie_display_name)
    elseif exists("g:pastie_display_name")
        let pdn = "&paste[display_name]=".s:urlencode(g:pastie_display_name)
    else
        let pdn = ""
    endif
    silent exe "write ".tmp
    let result = ""
    let rubycmd = 'obj = Net::HTTP.start(%{'.s:domain.'}){|h|h.post(%{'.url.'}, %q{'.method.'paste[parser]='.parser.pdn.'&paste[authorization]=burger&paste[key]=&paste[body]=} + File.read(%q{'.tmp.'}).gsub(/^(.*?) *#\!\! *#{36.chr}/,%{!\!}+92.chr+%{1}).gsub(/[^a-zA-Z0-9_.-]/n) {|s| %{%%%02x} % s[0]},{%{Cookie} => %{'.s:cookies().'}})}; print obj[%{Location}].to_s+%{ }+obj[%{Set-Cookie}].to_s'
    let result = system('ruby -rnet/http -e "'.rubycmd.'"')
    let redirect = matchstr(result,'^[^ ]*')
    let cookies  = matchstr(result,'^[^ ]* \zs.*')
    call s:extractcookiesfromheader(cookies)
    call delete(tmp)
    if redirect =~ '^\w\+://'
        set nomodified
        let b:pastie_update = 1
        "silent! let @+ = result
        silent! let @* = redirect
        silent exe "file ".redirect.s:dl_suffix
        " TODO: make a proper status message
        echo '"'.redirect.'" written'
        silent exe "doautocmd BufWritePost ".redirect.s:dl_suffix
    else
        if redirect == ''
            let redirect = "Could not post to ".url
        endif
        let redirect = substitute(redirect,'^-e:1:\s*','','')
        call s:error(redirect)
    endif
endfunction

function! s:error(msg)
    echohl Error
    echo a:msg
    echohl NONE
    let v:errmsg = a:msg
endfunction

function! s:filetype(type)
    " Accepts a filename, extension, pastie parser, or vim filetype
    let type = tolower(substitute(a:type,'.*\.','',''))
    if type =~ '^\%(x\=html\|asp\w*\)$'
        return 'html'
    elseif type =~ '^\%(eruby\|erb\|rhtml\)$'
        return 'eruby'
    elseif type =~ '^\%(ruby\|ruby_on_rails\|rb\|rake\|builder\|rjs\|irbrc\)'
        return 'ruby'
    elseif type == 'js' || type == 'javascript'
        return 'javascript'
    elseif type == 'c' || type == 'cpp' || type == 'c++'
        return 'cpp'
    elseif type =~ '^\%(css\|diff\|java\|php\|python\|sql\|sh\|shell-unix-generic\)$'
        return type
    else
        return ''
    endif
endfunction

function! s:parser(type)
    let type = s:filetype(a:type)
    if type == 'text' || type == ''
        return 'plain_text'
    elseif type == 'eruby'
        return 'html_rails'
    elseif type == 'ruby'
        return 'ruby_on_rails'
    elseif type == 'sh'
        return 'shell-unix-generic'
    elseif type == 'cpp'
        return 'c++'
    else
        return type
    endif
endfunction

function! s:grabwin()
    let ft = (&ft == '' ? expand("%:e") : &ft)
    let top = "## ".expand("%:~:.")." [".s:parser(ft)."]\n"
    let keep = @"
    silent %yank
    let file = @"
    let @" = keep
    if file == "" || file == "\n"
        return ""
    else
        return top.file."\n"
    endif
endfunction

function! s:cookies()
    if exists("g:pastie_session_id")
        let cookies = "_pastie_session_id=".g:pastie_session_id
    else
        call s:extractcookies('/')
        if !exists("g:pastie_session_id")
            if !exists("s:session_warning")
                echohl WarningMsg
                echo "Warning: could not extract session id"
                let s:session_warning = 1
                echohl NONE
            endif
            let cookies = ""
        else
            let cookies = "_pastie_session_id=".g:pastie_session_id
        endif
    endif
    if !exists("g:pastie_account")
        let rubycmd = '%w(~/.mozilla/firefox ~/.firefox/default ~/.phoenix/default ~/Application\ Data/Mozilla/Firefox/Profiles ~/Library/Application\ Support/Firefox/Profiles)'
        let rubycmd = rubycmd . '.each {|dir| Dir[File.join(File.expand_path(dir),%{*})].select {|p| File.exists?(File.join(p,%{cookies.txt}))}.each {|p| File.open(File.join(p,%{cookies.txt})).each_line { |l| a=l.split(9.chr); puts [a[4],a[6]].join(%{ }) if a[0] =~ /pastie\.caboo\.se#{36.chr}/ && Time.now.to_i < a[4].to_i && a[5] == %{account} }}}'
        let output = ''
        let output = system('ruby -e "'.rubycmd.'"')
        if output =~ '\n' && output !~ '-e:'
            let output = substitute(output,'\n.*','','')
            let g:pastie_account = matchstr(output,' \zs.*')
            let g:pastie_account_expires = matchstr(output,'.\{-\}\ze ')
        else
            let g:pastie_account = ''
        endif
    endif
    if exists("g:pastie_account") && g:pastie_account != ""
        " You cannot set this arbitrarily, it must be a valid cookie
        let cookies = cookies . (cookies == "" ? "" : "; ")
        let cookies = cookies . 'account='.substitute(g:pastie_account,':','%3A','g')
    endif
    return cookies
endfunction

function! s:extractcookies(path)
    let path = substitute(a:path,'\c^http://'.s:domain,'','')
    if path !~ '^/'
        let path = '/'.path
    endif
    let cookie = system('ruby -rnet/http -e "print Net::HTTP.get_response(%{'.s:domain.'},%{'.path.'})[%{Set-Cookie}]"')
    if exists("g:pastie_debug")
        let g:pastie_cookies_path = path
        let g:pastie_cookies = cookie
    endif
    return s:extractcookiesfromheader(cookie)
endfunction

function! s:extractcookiesfromheader(cookie)
    let cookie = a:cookie
    if cookie !~ '-e:'
        let session_id = matchstr(cookie,'\<_pastie_session_id=\zs.\{-\}\ze\%([;,]\|$\)')
        let account    = matchstr(cookie,'\<account=\zs.\{-\}\ze\%([;,]\|$\)')
        if session_id != ""
            let g:pastie_session_id = session_id
        endif
        if account != ""
            let g:pastie_account = account
            let time = matchstr(cookie,'\<[Ee]xpires=\zs\w\w\w,.\{-\}\ze\%([;,]\|$\)')
            if time != ""
                let g:pastie_account_expires = system('ruby -e "print Time.parse(%{'.time.'}).to_i"')
            endif
        endif
    endif
endfunction

function! s:latestid()
    return system('ruby -rnet/http -e "print Net::HTTP.get_response(URI.parse(%{http://'.s:domain.'/all})).body.match(%r{<a href=.http://'.s:domain.'/(\d+).>View})[1]"')
endfunction

function! s:urlencode(str)
    " Vim 6.2, how did we ever live with you?
    return substitute(substitute(a:str,"[\001-\037%&?=\\\\]",'\="%".printf("%02X",char2nr(submatch(0)))','g'),' ','%20','g')
endfunction

function! s:newwindow()
    if !(&modified) && (expand("%") == '' || (version >= 700 && winnr("$") == 1 && tabpagenr("$") == 1))
        enew
    else
        if g:pastie_destination == 'tab'
            tabnew
        elseif g:pastie_destination == 'window'
            new
        else
            enew
        endif
    endif
    setlocal noswapfile
endfunction

" vim:set sw=4 sts=4 et:
