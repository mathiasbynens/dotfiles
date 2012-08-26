import sublime, sublime_plugin

class TrimTrailingWhiteSpace(sublime_plugin.EventListener):
    def on_pre_save(self, view):
        if view.settings().get("trim_trailing_white_space_on_save") == True:
            trailing_white_space = view.find_all("[\t ]+$")
            trailing_white_space.reverse()
            edit = view.begin_edit()
            for r in trailing_white_space:
                view.erase(edit, r)
            view.end_edit(edit)

class EnsureNewlineAtEof(sublime_plugin.EventListener):
    def on_pre_save(self, view):
        if view.settings().get("ensure_newline_at_eof_on_save") == True:
            if view.size() > 0 and view.substr(view.size() - 1) != '\n':
                edit = view.begin_edit()
                view.insert(edit, view.size(), "\n")
                view.end_edit(edit)
