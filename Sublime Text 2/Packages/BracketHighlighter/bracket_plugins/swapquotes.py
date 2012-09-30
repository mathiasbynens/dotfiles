import bracket_plugin
import sublime


class swap_quotes(bracket_plugin.BracketPluginCommand):
    def escaped(self, idx):
        view = self.view
        escaped = False
        while idx >= 0 and view.substr(idx) == '\\':
            escaped = ~escaped
            idx -= 1
        return escaped

    def run(self, bracket, content, selection):
        view = self.view
        quote = view.substr(bracket.a)
        if quote != "'" and quote != '"':
            return
        new = "'" if (quote == '"') else '"'
        old = quote
        begin = bracket.a + 1
        end = bracket.b
        edit = view.begin_edit()
        content_end = content.b
        while begin < end:
            char = view.substr(begin)
            if char == old and self.escaped(begin - 1):
                view.replace(edit, sublime.Region(begin - 1, begin), '')
                end -= 1
                content_end -= 1
            elif char == new and not self.escaped(begin - 1):
                view.insert(edit, begin, '\\')
                end += 1
                content_end += 1
            begin += 1
        view.replace(edit, sublime.Region(bracket.a, bracket.a + 1), new)
        view.replace(edit, sublime.Region(end - 1, end), new)
        view.end_edit(edit)
        self.attr.set_bracket(sublime.Region(bracket.a, end))
        self.attr.set_content(sublime.Region(content.a, content_end))
        self.attr.set_selection([sublime.Region(content_end, content_end)])
