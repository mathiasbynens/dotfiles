import re
import os
import textwrap
import sublime
import sublime_plugin

def get_tab_size(view):
    return int(view.settings().get('tab_size', 8))

def normed_indentation_pt(view, sel, non_space=False):
    """
        Calculates tab normed `visual` position of sel.begin() relative "
        to start of line

        \n\t\t\t    => normed_indentation_pt => 12
        \n  \t\t\t  => normed_indentation_pt => 12

        Different amount of characters, same visual indentation.
    """

    tab_size = get_tab_size(view)
    pos = 0
    ln = view.line(sel)

    for pt in xrange(ln.begin(), ln.end() if non_space else sel.begin()):
        ch = view.substr(pt)

        if ch == '\t':
            pos += tab_size - (pos % tab_size)

        elif ch.isspace():
            pos += 1

        elif non_space:
            break
        else:
            pos+=1

    return pos

def compress_column(column):
    # "SS\T"
    if all(c.isspace() for c in column):
        column = '\t'

    # "CCSS"
    elif column[-1] == ' ':
        while column and column[-1] == ' ':
            column.pop()
        column.append('\t')

    # "CC\T"
    return column

def line_and_normed_pt(view, pt):
    return ( view.rowcol(pt)[0],
            normed_indentation_pt(view, sublime.Region(pt)) )

def pt_from_line_and_normed_pt(view, (ln, pt)):
    i = start_pt = view.text_point(ln, 0)
    tab_size = get_tab_size(view)

    pos = 0

    for i in xrange(start_pt, start_pt + pt):
        ch = view.substr(i)

        if ch == '\t':
            pos += tab_size - (pos % tab_size)
        else:
            pos += 1

        i += 1
        if pos == pt: break

    return i

def save_selections(view, selections=None):
    return [ [line_and_normed_pt(view, p) for p in (sel.a, sel.b)]
            for sel in selections or view.sel() ]

def region_from_stored_selection(view, stored):
    return sublime.Region(*[pt_from_line_and_normed_pt(view, p) for p in stored])

def restore_selections(view, lines_and_pts):
    view.sel().clear()

    for stored in lines_and_pts:
        view.sel().add(region_from_stored_selection(view, stored))

def unexpand(the_string, tab_size, first_line_offset = 0, only_leading=True):
    lines = the_string.split('\n')
    compressed = []

    for li, line in enumerate(lines):
        pos                =      0

        if not li: pos += first_line_offset

        rebuilt_line       =     []
        column             =     []

        for i, char in enumerate(line):
            if only_leading and not char.isspace():
                column.extend(list(line[i:]))
                break

            column.append(char)
            pos += 1

            if char == '\t':
                pos += tab_size - (pos % tab_size)

            if pos % tab_size == 0:
                rebuilt_line.extend(compress_column(column))
                column = []

        rebuilt_line.extend(column)
        compressed.append(''.join(rebuilt_line))

    return '\n'.join(compressed)

class TabCommand(sublime_plugin.TextCommand):
    translate = False

    def run(self, edit, set_translate_tabs=False, whole_buffer=True, **kw):
        view = self.view

        if set_translate_tabs or not self.translate:
            view.settings().set('translate_tabs_to_spaces', self.translate)

        if whole_buffer or not view.has_non_empty_selection_region():
            self.operation_regions = [sublime.Region(0, view.size())]
        else:
            self.operation_regions = view.sel()

        sels = save_selections(view)
        visible,  = save_selections(view, [view.visible_region()])
        self.do(edit, **kw)
        restore_selections(view, sels)
        visible = region_from_stored_selection(view, visible)
        view.show(visible, False)
        view.run_command("scroll_lines", {"amount": 1.0 })

class ExpandTabs(TabCommand):
    translate = True

    def do(self, edit, **kw):
        view = self.view
        tab_size = get_tab_size(view)

        for sel in self.operation_regions:
            sel = view.line(sel) # TODO: expand tabs with non regular offsets
            view.replace(edit, sel, view.substr(sel).expandtabs(tab_size))

class UnexpandTabs(TabCommand):
    def do(self, edit, only_leading = True, **kw):
        view = self.view
        tab_size = get_tab_size(view)

        for sel in self.operation_regions:
            the_string = view.substr(sel)
            first_line_off_set = normed_indentation_pt( view, sel ) % tab_size

            compressed = unexpand( the_string, tab_size, first_line_off_set,
                                only_leading = only_leading )

            view.replace(edit, sel, compressed)
