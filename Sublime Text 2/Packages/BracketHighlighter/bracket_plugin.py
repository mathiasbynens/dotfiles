import sublime
import sys
import os

# Pull in built-in plugin directory
built_in_plugins = os.path.join(sublime.packages_path(), 'BracketHighlighter')
if not built_in_plugins in sys.path:
    sys.path.append(built_in_plugins)


class BracketPlugin(object):
    def __init__(self, plugin):
        self.enabled = False
        self.args = plugin['args'] if ("args" in plugin) else {}
        self.plugin = None
        if 'command' in plugin:
            try:
                (module_name, class_name) = plugin['command'].split('.')
                module = __import__(module_name)
                self.plugin = getattr(module, class_name)
                self.enabled = True
            except Exception:
                sublime.error_message('Can not load plugin: ' + plugin['command'])

    def is_enabled(self):
        return self.enabled

    def run_command(self, bracket, content, selection, bracket_type):
        self.args['bracket'] = bracket
        self.args['content'] = content
        self.args['selection'] = selection
        plugin = self.plugin(bracket, content, selection, bracket_type)
        plugin.run(**self.args)
        return plugin.attr.get_attr()


class BracketAttributes(object):
    def __init__(self, bracket, content, selection, bracket_type):
        self.bracket = bracket
        self.content = content
        self.selection = selection
        self.bracket_type = bracket_type

    def set_bracket(self, bracket):
        self.bracket = bracket

    def set_content(self, content):
        self.content = content

    def set_selection(self, selection):
        self.selection = selection

    def get_type(self):
        return self.bracket_type

    def get_attr(self):
        return (self.bracket, self.content, self.selection)


class BracketPluginCommand(object):
    def __init__(self, bracket, content, selection, bracket_type):
        self.view = sublime.active_window().active_view()
        self.attr = BracketAttributes(bracket, content, selection, bracket_type)

    def run(self, bracket, content, selection):
        pass

# Register sublime commands from built-in plugins
from bracket_plugins.sublime_commands import *
