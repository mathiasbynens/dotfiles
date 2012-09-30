import bracket_plugin
import sublime


class select_bracket(bracket_plugin.BracketPluginCommand):
    def run(self, bracket, content, selection, select=''):
        (first, last) = (content.a, content.b)
        bh_type = self.attr.get_type()
        if select == 'left':
            if bh_type == "tag":
                first, last = (bracket.begin() + 1, bracket.begin() + 1)
            else:
                last = content.a
        elif select == 'right':
            if bh_type == "tag":
                first, last = (content.end() + 1, content.end() + 1)
            else:
                first = content.b
        self.attr.set_selection([sublime.Region(first, last)])
