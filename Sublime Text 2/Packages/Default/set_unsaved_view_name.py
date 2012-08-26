import sublime, sublime_plugin
import os.path
import string
import functools

class SetUnsavedViewName(sublime_plugin.EventListener):
    setting_name = False

    dropped_chars = string.whitespace

    pending = 0

    def on_modified(self, view):
        if view.file_name() or view.is_loading():
            return

        if self.setting_name:
            return

        self.pending += 1
        sublime.set_timeout(functools.partial(self.update_title, view), 20)

    def update_title(self, view):
        self.pending -= 1
        if self.pending != 0:
            return

        if view.settings().get('set_unsaved_view_name') == False:
            return

        cur_name = view.settings().get('auto_name')
        view_name = view.name()

        # Only set the name for plain text files
        syntax = view.settings().get('syntax')
        if syntax != 'Packages/Text/Plain text.tmLanguage':
            if cur_name:
                # Undo any previous name that was set
                view.settings().erase('auto_name')
                if cur_name == view_name:
                    view.set_name("")
            return

        # Name has been explicitly set, don't override it
        if not cur_name and view_name:
            return

        # Name has been explicitly changed, don't override it
        if cur_name and cur_name != view.name():
            view.settings().erase('auto_name')
            return

        # Don't set the names on widgets, it'll just trigger spurious
        # on_modified callbacks
        if view.settings().get('is_widget'):
            return

        line = view.line(0)
        if line.size() > 50:
            line = sublime.Region(0, 50)

        first_line = view.substr(line)

        first_line = first_line.strip(self.dropped_chars)

        self.setting_name = True
        view.set_name(first_line)
        self.setting_name = False

        view.settings().set('auto_name', first_line)
