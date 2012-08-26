import sublime, sublime_plugin
from functools import partial

class DetectIndentationCommand(sublime_plugin.TextCommand):
    """Examines the contents of the buffer to determine the indentation
    settings."""

    def run(self, edit, show_message = True, threshold = 10):
        sample = self.view.substr(sublime.Region(0, min(self.view.size(), 2**14)))

        starts_with_tab = 0
        spaces_list = []
        indented_lines = 0

        for line in sample.split("\n"):
            if not line: continue
            if line[0] == "\t":
                starts_with_tab += 1
                indented_lines += 1
            elif line.startswith(' '):
                spaces = 0
                for ch in line:
                    if ch == ' ': spaces += 1
                    else: break
                if spaces > 1 and spaces != len(line):
                    indented_lines += 1
                    spaces_list.append(spaces)

        evidence = [1.0, 1.0, 0.8, 0.9, 0.8, 0.9, 0.9, 0.95, 1.0]

        if indented_lines >= threshold:
            if len(spaces_list) > starts_with_tab:
                for indent in xrange(8, 1, -1):
                    same_indent = filter(lambda x: x % indent == 0, spaces_list)
                    if len(same_indent) >= evidence[indent] * len(spaces_list):
                        if show_message:
                            sublime.status_message("Detect Indentation: Setting indentation to "
                                + str(indent) + " spaces")
                        self.view.settings().set('translate_tabs_to_spaces', True)
                        self.view.settings().set('tab_size', indent)
                        return

                for indent in xrange(8, 1, -2):
                    same_indent = filter(lambda x: x % indent == 0 or x % indent == 1, spaces_list)
                    if len(same_indent) >= evidence[indent] * len(spaces_list):
                        if show_message:
                            sublime.status_message("Detect Indentation: Setting indentation to "
                                + str(indent) + " spaces")
                        self.view.settings().set('translate_tabs_to_spaces', True)
                        self.view.settings().set('tab_size', indent)
                        return

            elif starts_with_tab >= 0.8 * indented_lines:
                if show_message:
                    sublime.status_message("Detect Indentation: Setting indentation to tabs")
                self.view.settings().set('translate_tabs_to_spaces', False)

class DetectIndentationEventListener(sublime_plugin.EventListener):
    def on_load(self, view):
        if view.settings().get('detect_indentation'):
            is_at_front = view.window() != None
            view.run_command('detect_indentation', {'show_message': is_at_front})
