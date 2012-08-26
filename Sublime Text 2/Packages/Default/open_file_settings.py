import sublime, sublime_plugin
import os.path

class OpenFileSettingsCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
        settings_name, _ = os.path.splitext(os.path.basename(view.settings().get('syntax')))
        dir_name = os.path.join(sublime.packages_path(), 'User')
        self.window.open_file(os.path.join(dir_name, settings_name + ".sublime-settings"))

    def is_enabled(self):
        return self.window.active_view() != None
