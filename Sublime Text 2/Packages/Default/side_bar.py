import sublime, sublime_plugin
import os
import functools
import send2trash

class NewFileAtCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        v = self.window.new_file()

        if len(dirs) == 1:
            v.settings().set('default_dir', dirs[0])

    def is_visible(self, dirs):
        return len(dirs) == 1

class DeleteFileCommand(sublime_plugin.WindowCommand):
    def run(self, files):
        for f in files:
            send2trash.send2trash(f)

    def is_visible(self, files):
        return len(files) > 0

class NewFolderCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.show_input_panel("Folder Name:", "", functools.partial(self.on_done, dirs[0]), None, None)

    def on_done(self, dir, name):
        os.makedirs(os.path.join(dir, name))

    def is_visible(self, dirs):
        return len(dirs) == 1

class DeleteFolderCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        if sublime.ok_cancel_dialog("Delete Folder?", "Delete"):
            try:
                for d in dirs:
                    send2trash.send2trash(d)
            except:
                sublime.status_message("Unable to delete folder")

    def is_visible(self, dirs):
        return len(dirs) > 0

class RenamePathCommand(sublime_plugin.WindowCommand):
    def run(self, paths):
        branch, leaf = os.path.split(paths[0])
        v = self.window.show_input_panel("New Name:", leaf, functools.partial(self.on_done, paths[0], branch), None, None)
        name, ext = os.path.splitext(leaf)

        v.sel().clear()
        v.sel().add(sublime.Region(0, len(name)))

    def on_done(self, old, branch, leaf):
        new = os.path.join(branch, leaf)

        try:
            os.rename(old, new)

            v = self.window.find_open_file(old)
            if v:
                v.retarget(new)
        except:
            sublime.status_message("Unable to rename")

    def is_visible(self, paths):
        return len(paths) == 1

class OpenContainingFolderCommand(sublime_plugin.WindowCommand):
    def run(self, files):
        branch,leaf = os.path.split(files[0])
        self.window.run_command("open_dir", {"dir": branch, "file": leaf})

    def is_visible(self, files):
        return len(files) > 0

class FindInFolderCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.run_command("show_panel", {"panel": "find_in_files",
            "where": ",".join(dirs)})

    def is_visible(self, dirs):
        return len(dirs) > 0
