import bracket_plugin


class select_attr(bracket_plugin.BracketPluginCommand):
    def run(self, bracket, content, selection, direction='right'):
        tag_name = '[\w\:\-]+'
        attr_name = '([\w\-:]+)(?:\s*=\s*(?:(?:"((?:\\.|[^"])*)")|(?:\'((?:\\.|[^\'])*)\')|([^>\s]+)))?'
        name = self.view.find(tag_name, bracket.a)
        current = selection[0].b
        region = self.view.find(attr_name, name.b)

        if direction == 'left':
            last = None

            # Keep track of last attr
            if region != None and current <= region.b and region.b < content.a:
                last = region

            while region != None and region.b < content.a:
                # Select attribute until you have closest to the left of selection
                if current > region.b:
                    selection = [region]
                    last = None
                # Update last attr
                elif last != None:
                    last = region
                region = self.view.find(attr_name, region.b)
            # Wrap right
            if last != None:
                selection = [last]
        else:
            first = None
            # Keep track of first attr
            if region != None and region.b < content.a:
                first = region

            while region != None and region.b < content.a:
                # Select closest attr to the right of the selection
                if current < region.b:
                    selection = [region]
                    first = None
                    break
                region = self.view.find(attr_name, region.b)
            # Wrap left
            if first != None:
                selection = [first]
        self.attr.set_selection(selection)
