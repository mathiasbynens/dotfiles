" Vim syntax file
" Language:     Configuration File (ini file) for Drupal, Drush
" Author:       Benji Fisher <http://drupal.org/user/683300>
" Last Change: Wed Nov 09 05:00 PM 2011 EST

" References:
" - modules (7.x):  http://drupal.org/node/542202
" - modules (6.x):  http://drupal.org/node/231036
" - themes (6.x, 7.x):  http://drupal.org/node/171205
"   and http://drupal.org/node/1243144
" - format (7.x):
"   http://api.drupal.org/api/drupal/includes--common.inc/function/drupal_parse_info_format/7
" - format (6.x):
"   http://api.drupal.org/api/drupal/includes--common.inc/function/drupal_parse_info_file/6
" - Profiler:
"   http://drupalcode.org/project/profiler_example.git/blob_plain/HEAD:/profiler_example.info

" For version 5.x: Clear all syntax items
" For version 6.x or higher: Quit when a syntax file was already loaded
if version < 600
  syntax clear
elseif exists("b:current_syntax")
  finish
endif

syn case match

" What is the core version?
" Is this a theme, a module, or a Drush make file?
" TODO:  How do we recognize a Profiler ini file?  For now, Profiler includes
" all syntax items, which may be the right thing to do anyway.
function! s:IniType()
  " Find the Drupal core version.
  let save_cursor = getpos(".")
  call cursor(1, 1)
  let core_re = '^\s*core\s*=\s*\zs\d\+\ze\.x\s*$'
  let core_line = search(core_re, 'cn', 500)
  let core = matchstr(getline(core_line), core_re)
  call setpos('.', save_cursor)

  let ext = expand('%:e')
  if ext == 'make' || ext == 'build'
    let type = 'make'
  else
    " If the extension is not 'info' at this point, I do not know how we got
    " here.
    let path = expand('%:p')
    let m_index = strridx(path, '/modules/')
    let t_index = strridx(path, '/themes/')
    if m_index == -1 && t_index == -1
      let m_index = strridx(path, '/modules/')
      let t_index = strridx(path, '/themes/')
    endif
    if m_index > t_index
      let type = 'module'
    elseif m_index < t_index
      let type = 'theme'
    else        " We are not inside a themes/ directory, nor a mudules/ directory.  Do not guess.
      let type = ''
    endif
  endif
  return [core, type]
endfun

" Unless there is a more specific match, the entire line will be given Normal
" highlighting.
syn match driniNormal     "\S.*"
syn match driniComment    "^\s*\zs;.*$"
syn match driniOverLength "\%81v.*" containedin=driniComment contained

" Here is the basic pattern.  Note the use of nextgroup and contained.
" Later patterns and keywords take priority, so start with the generic key.
" After the =, either Value or "Value" or 'Value'.  Strings may span lines.
syn match    driniCustom    nextgroup=driniIndex,driniEquals skipwhite skipempty
      \ "[^ \t=;\[\]][^=;\[\]]*"
syn keyword  driniKey       nextgroup=driniEquals skipwhite skipempty datestamp project version
syn region driniIndex       contained oneline skipwhite skipempty
      \ nextgroup=driniIndex,driniEquals matchgroup=driniBracket start="\[" end="]"
syn match    driniEquals    contained skipwhite skipempty nextgroup=@driniValue "="
syn cluster  driniValue     contains=driniString,driniRHS
syn region   driniString    contained skipwhite nextgroup=driniNormal
      \ start=/\z(["']\)/ skip=/\\\z1/ end=/\z1/
syn match    driniRHS       contained /[^\t "';].*/

" These variants on the pattern let us restrict the syntax of the values.

" The name should start with an uppercase letter and the rest should be
" lowercase letters and spaces.
syn keyword  driniKey        nextgroup=driniNameEquals skipwhite skipempty name
syn match    driniNameEquals contained skipwhite skipempty
      \ nextgroup=driniNameValue,driniNameString "="
syn match    driniNameValue  contained nextgroup=driniNormal "\u[a-z ]*"
syn region   driniNameString contained oneline contains=driniNameValue
      \ skipwhite nextgroup=driniNormal start=/\z(["']\)/ skip=/\\\z1/ end=/\z1/

" The description should start with an uppercase letter, end with a period,
" and be no more than 255 characters in total.
syn keyword  driniKey        nextgroup=driniDescEquals skipwhite skipempty description
syn match    driniDescEquals contained skipwhite skipempty
      \ nextgroup=driniDescValue,driniDescString "="
syn match    driniDescValue  contained "\u.\{,253}\."
syn match    driniDescLong   contained nextgroup=driniDescLong skipwhite "\u\_.\{-,253}\."
syn region   driniDescString contained contains=driniDescLong keepend
      \ skipwhite nextgroup=driniNormal start=/\z(["']\)/ skip=/\\\z1/ end=/\z1/

syn keyword  driniKey        nextgroup=driniCoreEquals skipwhite skipempty core
syn match    driniCoreEquals contained skipwhite skipempty nextgroup=driniCoreValue "="
syn match    driniCoreValue  contained /\(['"]\)\=\d\+\.x\1/

" The optional version can be as simple as (2.1) or as complicated as
" (>1.0, <=3.2, !=3.0,)
syn keyword  driniKey        nextgroup=driniDepIndex skipwhite skipempty dependencies
syn region   driniDepIndex   contained oneline skipwhite skipempty
      \ nextgroup=driniDepIndex,driniDepEquals matchgroup=driniBracket start="\[" end="]"
syn match    driniDepEquals  contained skipwhite skipempty
      \ nextgroup=driniDepValue,driniDepString "="
syn match    driniDepValue   contained skipwhite
      \ nextgroup=driniDepVersion,driniNormal "[a-z_.]\+"
syn region   driniDepVersion contained oneline contains=driniDepVerNo
      \ skipwhite nextgroup=driniNormal matchgroup=driniDepParen start="(" end=")"
syn match    driniDepVerNo   contained
      \ "\(\([=><!]\?=\|[=><]\)\s*\)\=\d\+\.\(x\|\d\+\)"
syn region   driniDepString  contained oneline contains=driniDepValue,driniDepVersion
      \ skipwhite nextgroup=driniNormal start=/\z(["']\)/ skip=/\\\z1/ end=/\z1/

let [s:core, s:initype] = s:IniType()

if s:initype == 'module' || s:initype == ''
  if !s:core || s:core >= 6
    syn keyword driniKey nextgroup=driniEquals skipwhite skipempty hidden package php
  endif

  if !s:core || s:core >= 7
    syn keyword driniKey nextgroup=driniEquals skipwhite skipempty configure required
    syn keyword driniKey nextgroup=driniIndex skipwhite skipempty files scripts stylesheets
  endif
endif

if s:initype == 'theme' || s:initype == ''
  syn keyword driniKey   nextgroup=driniEquals skipwhite skipempty engine package php screenshot
  " The keyword "base" should be followed by "theme".
  syn keyword driniKey   nextgroup=driniTheme skipwhite skipempty base
  syn keyword driniTheme contained nextgroup=driniEquals skipwhite skipempty theme
  syn keyword driniKey   nextgroup=driniIndex skipwhite skipempty features regions scripts settings stylesheets
  if !s:core || s:core >= 7
    syn keyword driniKey nextgroup=driniEquals skipwhite skipempty hidden required
    syn keyword driniKey nextgroup=driniIndex skipwhite skipempty regions_hidden
  endif
endif

if s:initype == 'make' || s:initype == ''
  syn keyword driniKey nextgroup=driniEquals skipwhite skipempty api
  syn keyword driniKey nextgroup=driniIndex skipwhite skipempty includes libraries projects
endif

if s:initype == ''
  " Keywords for the Profiler module.
  syn keyword driniKey nextgroup=driniEquals skipwhite skipempty base
  syn keyword driniKey nextgroup=driniIndex skipwhite skipempty nodes terms users variables theme
endif

" Define the default highlighting.  The 'default' keyword requires vim 5.8+.

" Link all groups to the cluster that contains them.
highlight default link  driniNormal     Normal

highlight default link  driniTheme      driniKey
highlight default link  driniKey        Keyword
highlight default link  driniCustom     Identifier

highlight default link  driniBracket    Delimeter
highlight default link  driniDepIndex   driniIndex
highlight default link  driniIndex      String
highlight default link  driniCoreEquals driniEquals
highlight default link  driniDepEquals  driniEquals
highlight default link  driniDescEquals driniEquals
highlight default link  driniNameEquals driniEquals
highlight default link  driniEquals     Operator
highlight default link  driniCoreValue  driniRHS
highlight default link  driniDepValue   driniRHS
highlight default link  driniDescLong   driniRHS
highlight default link  driniDescValue  driniRHS
highlight default link  driniNameValue  driniRHS
highlight default link  driniDepVersion Normal
highlight default link  driniDepVerNo   WarningMsg
highlight default link  driniDepParen   Delimeter
highlight default link  driniRHS        String
highlight default link  driniCoreString driniString
highlight default link  driniDepString  Normal
highlight default link  driniDescString Normal
highlight default link  driniNameString Normal
highlight default link  driniString     String

highlight default link  driniComment    Comment
highlight default link  driniOverLength Error

let b:current_syntax = "drini"

" vim:ts=8
