import sublime, sublime_plugin

def clamp(xmin, x, xmax):
    if x < xmin:
        return xmin
    if x > xmax:
        return xmax
    return x;

class DeleteWordCommand(sublime_plugin.TextCommand):

    def find_by_class(self, pt, classes, forward):
        if forward:
            delta = 1
            end_position = self.view.size()
            if pt > end_position:
                pt = end_position
        else:
            delta = -1
            end_position = 0
            if pt < end_position:
                pt = end_position

        while pt != end_position:
            if self.view.classify(pt) & classes != 0:
                return pt
            pt += delta

        return pt

    def expand_word(self, view, pos, classes, forward):
        if forward:
            delta = 1
        else:
            delta = -1
        ws = ["\t", " "]

        if forward:
            if view.substr(pos) in ws and view.substr(pos + 1) in ws:
                classes = sublime.CLASS_WORD_START | sublime.CLASS_PUNCTUATION_START | sublime.CLASS_LINE_END
        else:
            if view.substr(pos - 1) in ws and view.substr(pos - 2) in ws:
                classes = sublime.CLASS_WORD_END | sublime.CLASS_PUNCTUATION_END | sublime.CLASS_LINE_START

        return sublime.Region(pos, self.find_by_class(pos + delta, classes, forward))

    def run(self, edit, forward = True, sub_words = False):

        if forward:
            classes = sublime.CLASS_WORD_END | sublime.CLASS_PUNCTUATION_END | sublime.CLASS_LINE_START
            if sub_words:
                classes |= sublime.CLASS_SUB_WORD_END
        else:
            classes = sublime.CLASS_WORD_START | sublime.CLASS_PUNCTUATION_START | sublime.CLASS_LINE_END
            if sub_words:
                classes |= sublime.CLASS_SUB_WORD_START

        new_sels = []
        for s in reversed(self.view.sel()):
            if s.empty():
                new_sels.append(self.expand_word(self.view, s.b, classes, forward))

        sz = self.view.size()
        for s in new_sels:
            self.view.sel().add(sublime.Region(clamp(0, s.a, sz),
                clamp(0, s.b, sz)))

        self.view.run_command("add_to_kill_ring", {"forward": forward})

        if forward:
            self.view.run_command('right_delete')
        else:
            self.view.run_command('left_delete')
