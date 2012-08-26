import sublime, sublime_plugin
import os.path

class SaveOnFocusLost(sublime_plugin.EventListener):
    def on_deactivated(self, view):
        # The check for os.path.exists ensures that deleted files won't be resurrected
        if (view.file_name() and view.is_dirty() and
                view.settings().get('save_on_focus_lost') == True and
                os.path.exists(view.file_name())):
            view.run_command('save');
