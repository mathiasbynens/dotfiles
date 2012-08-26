import sublime, sublime_plugin
import os.path
import platform

def compare_file_names(x, y):
    if platform.system() == 'Windows' or platform.system() == 'Darwin':
        return x.lower() == y.lower()
    else:
        return x == y

class SwitchFileCommand(sublime_plugin.WindowCommand):
    def run(self, extensions=[]):
        if not self.window.active_view():
            return

        fname = self.window.active_view().file_name()
        if not fname:
            return

        path = os.path.dirname(fname)
        base, ext = os.path.splitext(fname)

        start = 0
        count = len(extensions)

        if ext != "":
            ext = ext[1:]

            for i in xrange(0, len(extensions)):
                if compare_file_names(extensions[i], ext):
                    start = i + 1
                    count -= 1
                    break

        for i in xrange(0, count):
            idx = (start + i) % len(extensions)

            new_path = base + '.' + extensions[idx]

            if os.path.exists(new_path):
                self.window.open_file(new_path)
                break
