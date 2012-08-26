import sublime, sublime_plugin
import string
import textwrap
import re
import comment

def previous_line(view, sr):
    """sr should be a Region covering the entire hard line"""
    if sr.begin() == 0:
        return None
    else:
        return view.full_line(sr.begin() - 1)

def next_line(view, sr):
    """sr should be a Region covering the entire hard line, including
    the newline"""
    if sr.end() == view.size():
        return None
    else:
        return view.full_line(sr.end())


separating_line_pattern = re.compile("^[\\t ]*\\n?$")

def is_paragraph_separating_line(view, sr):
    return separating_line_pattern.match(view.substr(sr)) != None

def has_prefix(view, line, prefix):
    if not prefix:
        return True

    line_start = view.substr(sublime.Region(line.begin(),
        line.begin() + len(prefix)))

    return line_start == prefix

def expand_to_paragraph(view, tp):
    sr = view.full_line(tp)
    if is_paragraph_separating_line(view, sr):
        return sublime.Region(tp, tp)

    required_prefix = None

    # If the current line starts with a comment, only select lines that are also
    # commented
    (line_comments, block_comments) = comment.build_comment_data(view, tp)
    dataStart = comment.advance_to_first_non_white_space_on_line(view, sr.begin())
    for c in line_comments:
        (start, disable_indent) = c
        comment_region = sublime.Region(dataStart,
            dataStart + len(start))
        if view.substr(comment_region) == start:
            required_prefix = view.substr(sublime.Region(sr.begin(), comment_region.end()))
            break

    first = sr.begin()
    prev = sr
    while True:
        prev = previous_line(view, prev)
        if (prev == None or is_paragraph_separating_line(view, prev) or
                not has_prefix(view, prev, required_prefix)):
            break
        else:
            first = prev.begin()

    last = sr.end()
    next = sr
    while True:
        next = next_line(view, next)
        if (next == None or is_paragraph_separating_line(view, next) or
                not has_prefix(view, next, required_prefix)):
            break
        else:
            last = next.end()

    return sublime.Region(first, last)

def all_paragraphs_intersecting_selection(view, sr):
    paragraphs = []

    para = expand_to_paragraph(view, sr.begin())
    if not para.empty():
        paragraphs.append(para)

    while True:
        line = next_line(view, para)
        if line == None or line.begin() >= sr.end():
            break;

        if not is_paragraph_separating_line(view, line):
            para = expand_to_paragraph(view, line.begin())
            paragraphs.append(para)
        else:
            para = line

    return paragraphs


class ExpandSelectionToParagraphCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        regions = []

        for s in self.view.sel():
            regions.append(sublime.Region(
                expand_to_paragraph(self.view, s.begin()).begin(),
                expand_to_paragraph(self.view, s.end()).end()))

        for r in regions:
            self.view.sel().add(r)


class WrapLinesCommand(sublime_plugin.TextCommand):
    line_prefix_pattern = re.compile("^\W+")

    def extract_prefix(self, sr):
        lines = self.view.split_by_newlines(sr)
        if len(lines) == 0:
            return None

        initial_prefix_match = self.line_prefix_pattern.match(self.view.substr(
            lines[0]))
        if not initial_prefix_match:
            return None

        prefix = self.view.substr(sublime.Region(lines[0].begin(),
            lines[0].begin() + initial_prefix_match.end()))

        for line in lines[1:]:
            if self.view.substr(sublime.Region(line.begin(),
                    line.begin() + len(prefix))) != prefix:
                return None

        return prefix

    def width_in_spaces(self, str, tab_width):
        sum = 0;
        for c in str:
            if c == '\t':
                sum += tab_width - 1
        return sum

    def run(self, edit, width=0):
        if width == 0 and self.view.settings().get("wrap_width"):
            try:
                width = int(self.view.settings().get("wrap_width"))
            except TypeError:
                pass

        if width == 0 and self.view.settings().get("rulers"):
            # try and guess the wrap width from the ruler, if any
            try:
                width = int(self.view.settings().get("rulers")[0])
            except ValueError:
                pass
            except TypeError:
                pass

        if width == 0:
            width = 78

        # Make sure tabs are handled as per the current buffer
        tab_width = 8
        if self.view.settings().get("tab_size"):
            try:
                tab_width = int(self.view.settings().get("tab_size"))
            except TypeError:
                pass

        if tab_width == 0:
            tab_width == 8

        paragraphs = []
        for s in self.view.sel():
            paragraphs.extend(all_paragraphs_intersecting_selection(self.view, s))

        if len(paragraphs) > 0:
            self.view.sel().clear()
            for p in paragraphs:
                self.view.sel().add(p)

            # This isn't an ideal way to do it, as we loose the position of the
            # cursor within the paragraph: hence why the paragraph is selected
            # at the end.
            for s in self.view.sel():
                wrapper = textwrap.TextWrapper()
                wrapper.expand_tabs = False
                wrapper.width = width
                prefix = self.extract_prefix(s)
                if prefix:
                    wrapper.initial_indent = prefix
                    wrapper.subsequent_indent = prefix
                    wrapper.width -= self.width_in_spaces(prefix, tab_width)

                if wrapper.width < 0:
                    continue

                txt = self.view.substr(s)
                if prefix:
                    txt = txt.replace(prefix, u"")

                txt = string.expandtabs(txt, tab_width)

                txt = wrapper.fill(txt) + u"\n"
                self.view.replace(edit, s, txt)

            # It's unhelpful to have the entire paragraph selected, just leave the
            # selection at the end
            ends = [s.end() - 1 for s in self.view.sel()]
            self.view.sel().clear()
            for pt in ends:
                self.view.sel().add(sublime.Region(pt))
