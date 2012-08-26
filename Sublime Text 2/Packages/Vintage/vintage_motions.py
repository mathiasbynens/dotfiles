import re
import sublime, sublime_plugin
from vintage import transform_selection
from vintage import transform_selection_regions

class ViSpanCountLines(sublime_plugin.TextCommand):
    def run(self, edit, repeat = 1):
        for i in xrange(repeat - 1):
            self.view.run_command('move', {'by': 'lines',
                                           'extend': True,
                                           'forward': True})

class ViMoveByCharactersInLine(sublime_plugin.TextCommand):
    def run(self, edit, forward = True, extend = False, visual = False):
        delta = 1 if forward else -1

        transform_selection(self.view, lambda pt: pt + delta, extend=extend,
            clip_to_line=(not visual))

class ViMoveByCharacters(sublime_plugin.TextCommand):
    def advance(self, delta, visual, pt):
        pt += delta
        if not visual and self.view.substr(pt) == '\n':
            pt += delta

        return pt

    def run(self, edit, forward = True, extend = False, visual = False):
        delta = 1 if forward else -1
        transform_selection(self.view, lambda pt: self.advance(delta, visual, pt),
            extend=extend)

class ViMoveToHardEol(sublime_plugin.TextCommand):
    def run(self, edit, repeat = 1, extend = False):
        repeat = int(repeat)
        if repeat > 1:
            for i in xrange(repeat - 1):
                self.view.run_command('move',
                    {'by': 'lines', 'extend': extend, 'forward': True})

        transform_selection(self.view, lambda pt: self.view.line(pt).b,
            extend=extend, clip_to_line=False)

class ViMoveToFirstNonWhiteSpaceCharacter(sublime_plugin.TextCommand):
    def first_character(self, pt):
        l = self.view.line(pt)
        lstr = self.view.substr(l)

        offset = 0
        for c in lstr:
            if c == ' ' or c == '\t':
                offset += 1
            else:
                break

        return l.a + offset

    def run(self, edit, repeat = 1, extend = False, register = '"'):
        # According to Vim's help, _ moves count - 1 lines downward.
        for i in xrange(repeat - 1):
            self.view.run_command('move', {'by': 'lines', 'forward': True, 'extend': extend})

        transform_selection(self.view, lambda pt: self.first_character(pt),
            extend=extend)


g_last_move_command = None

class ViMoveToCharacter(sublime_plugin.TextCommand):
    def find_next(self, forward, char, before, pt):
        lr = self.view.line(pt)

        extra = 0 if before else 1

        if forward:
            line = self.view.substr(sublime.Region(pt, lr.b))
            idx = line.find(char, 1)
            if idx >= 0:
                return pt + idx + 1 * extra
        else:
            line = self.view.substr(sublime.Region(lr.a, pt))[::-1]
            idx = line.find(char, 0)
            if idx >= 0:
                return pt - idx - 1 * extra

        return pt

    def run(self, edit, character, extend = False, forward = True, before = False, record = True):
        if record:
            global g_last_move_command
            g_last_move_command = {'character': character, 'extend': extend,
                'forward':forward, 'before':before}

        transform_selection(self.view,
            lambda pt: self.find_next(forward, character, before, pt),
            extend=extend)

class ViExtendToEndOfWhitespaceOrWord(sublime_plugin.TextCommand):
    def run(self, edit, repeat = 1, separators=None):
        repeat = int(repeat)

        # Selections that start on whitespace should extend to the end of the
        # the whitespace.  Other selections can simply be moved to word ends.
        sel = self.view.sel()
        sels_advanced_from_whitespace = []
        sels_to_move_to_word_end = []

        for r in sel:
            b = advance_while_white_space_character(self.view, r.b)
            if b > r.b:
                sels_advanced_from_whitespace.append(sublime.Region(r.a, b))
            else:
                sels_to_move_to_word_end.append(r)

        sel.clear()
        for r in sels_to_move_to_word_end:
            sel.add(r)

        move_args = {"by": "stops", "word_end": True, "punct_end": True,
                     "empty_line": True, "forward": True, "extend": True}
        if separators != None:
            move_args.update(separators=separators)

        self.view.run_command('move', move_args)

        for r in sels_advanced_from_whitespace:
            sel.add(r)

        # Only the first move differs from a normal move to word end.
        for i in xrange(repeat - 1):
            self.view.run_command('move', move_args)

# Helper class used to implement ';'' and ',', which repeat the last f, F, t
# or T command (reversed in the case of ',')
class SetRepeatMoveToCharacterMotion(sublime_plugin.TextCommand):
    def run_(self, args):
        if args:
            return self.run(**args)
        else:
            return self.run()

    def run(self, reverse = False):
        if g_last_move_command:
            cmd = g_last_move_command.copy()
            cmd['record'] = False
            if reverse:
                cmd['forward'] = not cmd['forward']

            self.view.run_command('set_motion', {
                'motion': 'vi_move_to_character',
                'motion_args': cmd,
                'inclusive': True })

class ViMoveToBrackets(sublime_plugin.TextCommand):
    def move_by_percent(self, percent):
        destination = int(self.view.rowcol(self.view.size())[0] * (percent / 100.0))
        destination = self.view.line(self.view.text_point(destination, 0)).a
        destination = advance_while_white_space_character(self.view, destination)

        transform_selection(self.view, lambda pt: destination)

    def run(self, edit, repeat=1):
        repeat = int(repeat)
        if repeat == 1:
            re_brackets = re.compile(r"([(\[{])|([)}\])])")
            def move_to_next_bracket(pt):
                line = self.view.line(pt)
                remaining_line = self.view.substr(sublime.Region(pt, line.b))
                match = re_brackets.search(remaining_line)
                if match:
                    return pt + match.start() + (1 if match.group(2) else 0)
                else:
                    return pt
            transform_selection(self.view, move_to_next_bracket, extend=True)
            self.view.run_command("move_to", {"to": "brackets", "extend": True, "force_outer": True})
        else:
            self.move_by_percent(repeat)

class ViGotoLine(sublime_plugin.TextCommand):
    def run(self, edit, repeat=1, explicit_repeat=True, extend=False,
            ending='eof'):
        # G or gg
        if not explicit_repeat:
            self.view.run_command('move_to', {'to': ending, 'extend':extend})
        # <count>G or <count>gg
        else:
            new_address = int(repeat) - 1
            target_pt = self.view.text_point(new_address, 0)
            transform_selection(self.view, lambda pt: target_pt,
                extend=extend)

def advance_while_white_space_character(view, pt, white_space="\t "):
    while view.substr(pt) in white_space:
        pt += 1

    return pt

class MoveCaretToScreenCenter(sublime_plugin.TextCommand):
    def run(self, edit, extend = True):
        screenful = self.view.visible_region()

        row_a = self.view.rowcol(screenful.a)[0]
        row_b = self.view.rowcol(screenful.b)[0]

        middle_row = (row_a + row_b) / 2
        middle_point = self.view.text_point(middle_row, 0)

        middle_point = advance_while_white_space_character(self.view, middle_point)
        transform_selection(self.view, lambda pt: middle_point, extend=extend)

class MoveCaretToScreenTop(sublime_plugin.TextCommand):
    def run(self, edit, repeat, extend = True):
        # Don't modify offset so not fully visible regions have a lower chance
        # of scrolling the screen.
        # lines_offset = int(repeat) - 1
        lines_offset = int(repeat)
        screenful = self.view.visible_region()

        target = screenful.begin()
        for x in xrange(lines_offset):
            current_line = self.view.line(target)
            target = current_line.b + 1

        target = advance_while_white_space_character(self.view, target)
        transform_selection(self.view, lambda pt: target, extend=extend)

class MoveCaretToScreenBottom(sublime_plugin.TextCommand):
    def run(self, edit, repeat, extend = True):
        # Don't modify offset so not fully visible regions have a lower chance
        # of scrolling the screen.
        # lines_offset = int(repeat) - 1
        lines_offset = int(repeat)
        screenful = self.view.visible_region()

        target = screenful.end()
        for x in xrange(lines_offset):
            current_line = self.view.line(target)
            target = current_line.a - 1
        target = self.view.line(target).a

        target = advance_while_white_space_character(self.view, target)
        transform_selection(self.view, lambda pt: target, extend=extend)

def expand_to_whitespace(view, r):
    a = r.a
    b = r.b
    while view.substr(b) in " \t":
        b += 1

    if b == r.b:
        while view.substr(a - 1) in " \t":
            a -= 1

    return sublime.Region(a, b)

class ViExpandToWords(sublime_plugin.TextCommand):
    def run(self, edit, outer = False, repeat = 1):
        repeat = int(repeat)
        transform_selection_regions(self.view, lambda r: sublime.Region(r.b + 1, r.b + 1))
        self.view.run_command("move", {"by": "stops", "extend":False, "forward":False, "word_begin":True, "punct_begin":True})
        for i in xrange(repeat):
            self.view.run_command("move", {"by": "stops", "extend":True, "forward":True, "word_end":True, "punct_end":True})
        if outer:
            transform_selection_regions(self.view, lambda r: expand_to_whitespace(self.view, r))

class ViExpandToBigWords(sublime_plugin.TextCommand):
    def run(self, edit, outer = False, repeat = 1):
        repeat = int(repeat)
        transform_selection_regions(self.view, lambda r: sublime.Region(r.b + 1, r.b + 1))
        self.view.run_command("move", {"by": "stops", "extend":False, "forward":False, "word_begin":True, "punct_begin":True, "separators": ""})
        for i in xrange(repeat):
            self.view.run_command("move", {"by": "stops", "extend":True, "forward":True, "word_end":True, "punct_end":True, "separators": ""})
        if outer:
            transform_selection_regions(self.view, lambda r: expand_to_whitespace(self.view, r))

class ViExpandToQuotes(sublime_plugin.TextCommand):
    def compare_quote(self, character, p):
        if self.view.substr(p) == character:
            return self.view.score_selector(p, "constant.character.escape") == 0
        else:
            return False

    def expand_to_quote(self, character, r):
        # We'll limit the search to the current line.
        line_begin = self.view.line(r).begin()
        line_end = self.view.line(r).end()

        caret_pos_in_line = r.begin() - line_begin
        # Find out whether there's any quoted text.
        line_text = self.view.substr(self.view.line(r))
        first_quote = line_text.find(character)
        closing_quote = None

        # Look for a closing quote after the first quote.
        if ((line_text[caret_pos_in_line] == character and
             first_quote == caret_pos_in_line) or
             (first_quote > caret_pos_in_line)):
                closing_quote = line_text.find(character, first_quote + 1)
        # The caret may be on a quote character, so don't look past it.
        # This ensures we favor quoted text before the caret over quoted
        # text after it, as Vim does.
        else:
            closing_quote = line_text.find(character, caret_pos_in_line)

        # No quoted text --do nothing (Vim).
        # TODO: Vintage will enter insert mode after this, whereas it should
        # stay in command mode as Vim does.
        if closing_quote == -1:
            return r

        # Quoted text is before the caret --do nothing (Vim).
        if closing_quote < caret_pos_in_line:
            return r

        p = r.b
        if closing_quote == caret_pos_in_line:
            p -= 1

        # Quoted text is after the caret --advance there (Vim).
        if first_quote > caret_pos_in_line:
            p = line_begin + first_quote

        a = p
        while a >= line_begin and not self.compare_quote(character, a):
            a -= 1

        b = a + 1
        while b < line_end and not self.compare_quote(character, b):
            b += 1

        return sublime.Region(a + 1, b)

    def expand_to_outer(self, r):
        a, b = r.a, r.b
        if a > 0:
            a -= 1
        if b < self.view.size():
            b += 1
        return expand_to_whitespace(self.view, sublime.Region(a, b))

    def run(self, edit, character, outer = False):
        transform_selection_regions(self.view, lambda r: self.expand_to_quote(character, r))
        if outer:
            transform_selection_regions(self.view, lambda r: self.expand_to_outer(r))

class ViExpandToTag(sublime_plugin.TextCommand):
    def run(self, edit, outer = False):
        self.view.run_command('expand_selection', {'to': 'tag'})
        if outer:
            self.view.run_command('expand_selection', {'to': 'tag'})

class ViExpandToBrackets(sublime_plugin.TextCommand):
    def run(self, edit, character, outer = False):
        self.view.run_command('expand_selection', {'to': 'brackets', 'brackets': character})
        if outer:
            self.view.run_command('expand_selection', {'to': 'brackets', 'brackets': character})

class ScrollCurrentLineToScreenTop(sublime_plugin.TextCommand):
    def run(self, edit, repeat, extend=False):
        bos = self.view.visible_region().a
        caret = self.view.line(self.view.sel()[0].begin()).a
        offset = self.view.rowcol(caret)[0] - self.view.rowcol(bos)[0]

        caret = advance_while_white_space_character(self.view, caret)
        transform_selection(self.view, lambda pt: caret, extend)
        self.view.run_command('scroll_lines', {'amount': -offset})

class ScrollCurrentLineToScreenCenter(sublime_plugin.TextCommand):
    def run(self, edit, repeat, extend=True):
         line_nr = self.view.rowcol(self.view.sel()[0].a)[0] if \
                                         int(repeat) == 1 else int(repeat) - 1
         point = self.view.line(self.view.text_point(line_nr, 0)).a
         point = advance_while_white_space_character(self.view, point)
         transform_selection(self.view, lambda pt: point, extend)
         self.view.run_command('show_at_center')
