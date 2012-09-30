import bracket_plugin


class select_tag(bracket_plugin.BracketPluginCommand):
    def run(self, bracket, content, selection):
        tag_name = '[\w\:\-]+'
        region1 = self.view.find(tag_name, bracket.a)
        region2 = self.view.find(tag_name, content.b)
        self.attr.set_selection([region1, region2])
