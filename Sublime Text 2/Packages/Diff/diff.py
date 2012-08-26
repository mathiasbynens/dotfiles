import sublime, sublime_plugin
import difflib
import time
import os.path
import codecs

class DiffFilesCommand(sublime_plugin.WindowCommand):
    def run(self, files):
        if len(files) != 2:
            return

        try:
            a = codecs.open(files[1], "r", "utf-8").readlines()
            b = codecs.open(files[0], "r", "utf-8").readlines()
        except UnicodeDecodeError:
            sublime.status_message("Diff only works with UTF-8 files")
            return

        adate = time.ctime(os.stat(files[1]).st_mtime)
        bdate = time.ctime(os.stat(files[0]).st_mtime)

        diff = difflib.unified_diff(a, b, files[1], files[0], adate, bdate)

        difftxt = u"".join(line for line in diff)

        if difftxt == "":
            sublime.status_message("Files are identical")
        else:
            v = self.window.new_file()
            v.set_name(os.path.basename(files[1]) + " -> " + os.path.basename(files[0]))
            v.set_scratch(True)
            v.set_syntax_file('Packages/Diff/Diff.tmLanguage')
            edit = v.begin_edit()
            v.insert(edit, 0, difftxt)
            v.end_edit(edit)

    def is_visible(self, files):
        return len(files) == 2

class DiffChangesCommand(sublime_plugin.TextCommand):
    def run(self, edit):

        fname = self.view.file_name();

        try:
            a = codecs.open(fname, "r", "utf-8").read().splitlines()
            b = self.view.substr(sublime.Region(0, self.view.size())).splitlines()
        except UnicodeDecodeError:
            sublime.status_message("Diff only works with UTF-8 files")
            return

        adate = time.ctime(os.stat(fname).st_mtime)
        bdate = time.ctime()

        diff = difflib.unified_diff(a, b, fname, fname, adate, bdate,lineterm='')
        difftxt = u"\n".join(line for line in diff)

        if difftxt == "":
            sublime.status_message("No changes")
            return

        use_buffer = self.view.settings().get('diff_changes_to_buffer')

        if use_buffer:
            v = self.view.window().new_file()
            v.set_name("Unsaved Changes: " + os.path.basename(self.view.file_name()))
            v.set_scratch(True)
            v.set_syntax_file('Packages/Diff/Diff.tmLanguage')
        else:
            win = self.view.window()
            v = win.get_output_panel('unsaved_changes')
            v.set_syntax_file('Packages/Diff/Diff.tmLanguage')
            v.settings().set('word_wrap', self.view.settings().get('word_wrap'))

        edit = v.begin_edit()
        v.insert(edit, 0, difftxt)
        v.end_edit(edit)

        if not use_buffer:
            win.run_command("show_panel", {"panel": "output.unsaved_changes"})

    def is_enabled(self):
        return self.view.is_dirty() and self.view.file_name()
