" Vim syntax file
" Language:	CSS 3
" Maintainer: Shiao <i@shiao.org>
" Last Change:	2010 Apr 5

syn keyword cssTagName article aside audio bb canvas command datagrid                                                                                                                                                                         
syn keyword cssTagName datalist details dialog embed figure footer
syn keyword cssTagName header hgroup keygen mark meter nav output
syn keyword cssTagName progress time ruby rt rp section time video
syn keyword cssTagName source figcaption

syn keyword cssColorProp contained opacity

syn match cssTextProp contained "\<word-wrap\>"
syn match cssTextProp contained "\<text-overflow\>"

syn match cssBoxProp contained "\<box-shadow\>"
syn match cssBoxProp contained "\<border-radius\>"
syn match cssBoxProp contained "\<border-\(\(top-left\|top-right\|bottom-right\|bottom-left\)-radius\)\>"
" firefox border-radius TODO
syn match cssBoxProp contained "-moz-border-radius\>"
syn match cssBoxProp contained "-moz-border-radius\(-\(bottomleft\|bottomright\|topright\|topleft\)\)\>"

