import bracket_plugin
import sublime
import sublime_plugin


class swap_brackets_transform(bracket_plugin.BracketPluginCommand):
    def run(self, bracket, content, selection, bracket_type="square"):
        brackets = {
            "square": ["[", "]"],
            "round": ["(", ")"],
            "angle": ["<", ">"],
            "curly": ["{", "}"]
        }
        edit = self.view.begin_edit()
        self.view.replace(edit, sublime.Region(bracket.begin(), bracket.begin() + 1), brackets[bracket_type][0])
        self.view.replace(edit, sublime.Region(bracket.end() - 1, bracket.end()), brackets[bracket_type][1])
        self.view.end_edit(edit)


class SwapBracketsCommand(sublime_plugin.WindowCommand):
    def swap_brackets(self, value):
        brackets = [
            "square",
            "round",
            "angle",
            "curly"
        ]
        self.window.run_command(
            "bracket_highlighter_key", {
                "plugin": {
                    "type": ["bracket"],
                    "command": "bracket_plugins.swap_brackets_transform",
                    "args": {"bracket_type": brackets[value]}
                }
            }
        )

    def run(self):
        self.window.show_quick_panel(
            [
                "[] square", "() round",
                "<> angle", "{} curly"
            ],
            self.swap_brackets
        )
