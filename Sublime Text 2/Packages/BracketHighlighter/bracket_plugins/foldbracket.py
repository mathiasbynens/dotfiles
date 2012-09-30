import bracket_plugin


class fold_bracket(bracket_plugin.BracketPluginCommand):
    def run(self, bracket, content, selection):
        new_content = [content]
        if content.size > 0:
            if self.view.fold(content) == False:
                new_content = self.view.unfold(content)
        self.attr.set_selection(new_content)
