#!/usr/bin/env python
#coding: utf8
#################################### IMPORTS ###################################

# Std Libs
import re

try:
    from itertools import izip
except ImportError: # Python 3 coming Feb?
    from itertools import zip as izip

# Sublime Libs
import sublime
import sublime_plugin

#################################### HELPERS ###################################

def notify_nothing():
    sublime.status_message('Nothing to transpose')

def full_region(region):
    return ( sublime.Region(region.begin(), region.begin() + 1)
            if region.empty() else region )

def perform_transposition(edit, view, trans, init_sel):
    " assumes trans is already reverse sorted sequence of regions"
    view.sel().subtract(init_sel)
    
    for i, (sel, substr) in enumerate(izip(trans, 
                            reversed([view.substr(s) for s in trans])) ):
        view.replace(edit, sel, substr)
        if not i: view.sel().add(init_sel)

def transpose_selections(edit, view):
    for sel in view.sel():
        word_sel = view.word(sel) 
        word_extents = (wb, we) = (word_sel.begin(), word_sel.end())
        transpose_words = sel.end() in word_extents

        #" wora! arst"
        if transpose_words:
            if sel.end() == we:
                next = view.find('\w', word_sel.end())
                if next is None: continue
                trans = [ view.word(next), word_sel ]
            else:
                if wb == 0: continue
                for pt in xrange(wb-1, -1, -1):
                    if re.match('\w', view.substr(pt)): break
                trans = [ word_sel, view.word(pt) ]
        else:
            p1 = max(0,  sel.begin() -1)
            character_behind_region = sublime.Region(p1)
            #" a!a"
            trans = [ full_region(sel), full_region(character_behind_region)]

        perform_transposition(edit, view, trans, sel)

def rotate_selections(edit, view):
    # TODO: ???
    for sel in view.sel():
        if sel.empty(): view.sel().add(view.word(sel))

    sels     = list(reversed(view.sel()))

    strings  = [ view.substr(s) for s in sels ]
    strings.append(strings.pop(0))

    for sel, substr in izip(sels, strings):
        view.replace(edit, sel, substr)

################################### COMMANDS ###################################

class Transpose(sublime_plugin.TextCommand):
    """
    - empty selection, cursor within a word: transpose characters
    - empty selection, cursor at the end of a word: transpose words
    - multiple selections, all empty: as above

    - multiple selections, at least one non-empty: rotate contents of selections
    (i.e., each selection takes on the contents of the selection before it)

    - single non-empty selection: do nothing

    """

    def run(self, edit, **kw):
        if not self.enabled(): return notify_nothing()
    
        view  = self.view
        sels  = view.sel()
        nsels = len(sels)

        if nsels > 1 and view.has_non_empty_selection_region():
            rotate_selections(edit, view)
        else:
            transpose_selections(edit, view)

    def enabled(self):
        sels = self.view.sel()
        return not (len(sels) == 1 and not sels[0].empty())