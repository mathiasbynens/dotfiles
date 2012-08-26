import sublime, sublime_plugin

class IncreaseFontSizeCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        s = sublime.load_settings("Preferences.sublime-settings")
        current = s.get("font_size", 10)

        if current >= 36:
            current += 4
        elif current >= 24:
            current += 2
        else:
            current += 1

        if current > 128:
            current = 128
        s.set("font_size", current)

        sublime.save_settings("Preferences.sublime-settings")

class DecreaseFontSizeCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        s = sublime.load_settings("Preferences.sublime-settings")
        current = s.get("font_size", 10)
        # current -= 1

        if current >= 40:
            current -= 4
        elif current >= 26:
            current -= 2
        else:
            current -= 1

        if current < 8:
            current = 8
        s.set("font_size", current)

        sublime.save_settings("Preferences.sublime-settings")

class ResetFontSizeCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        s = sublime.load_settings("Preferences.sublime-settings")
        s.erase("font_size")

        sublime.save_settings("Preferences.sublime-settings")
