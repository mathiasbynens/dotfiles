#!/usr/bin/env python

import sublime
import sublime_plugin

from htmlentitydefs import codepoint2name as cp2n

class EncodeHtmlEntities(sublime_plugin.TextCommand):
    def run(self, edit, **args):
        view = self.view

        for sel in view.sel():
            buf = []

            for pt in xrange(sel.begin(), sel.end()):
                ch = view.substr(pt)
                ch_ord = ord(ch)

                if (not view.match_selector(pt, ('meta.tag - string, constant.character.entity'))
                        and ch_ord in cp2n
                        and not (ch in ('"', "'")
                        and view.match_selector(pt, 'string'))):
                    ch = '&%s;' % cp2n[ch_ord]

                buf.append(ch)

            view.replace(edit, sel, ''.join(buf))
