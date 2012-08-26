import sublime, sublime_plugin

class CopyPathCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if len(self.view.file_name()) > 0:
            sublime.set_clipboard(self.view.file_name())
            sublime.status_message("Copied file path")

    def is_enabled(self):
        return self.view.file_name() and len(self.view.file_name()) > 0
