import sublime, sublime_plugin
import os

class NewBuildSystemCommand(sublime_plugin.WindowCommand):
    def run(self):
        v = self.window.new_file()
        v.settings().set('default_dir',
            os.path.join(sublime.packages_path(), 'User'))
        v.set_syntax_file('Packages/JavaScript/JSON.tmLanguage')
        v.set_name('untitled.sublime-build')

        template = """{
	"cmd": ["${0:make}"]
}
"""
        v.run_command("insert_snippet", {"contents": template})


class NewPluginCommand(sublime_plugin.WindowCommand):
    def run(self):
        v = self.window.new_file()
        v.settings().set('default_dir',
            os.path.join(sublime.packages_path(), 'User'))
        v.set_syntax_file('Packages/Python/Python.tmLanguage')

        template = """import sublime, sublime_plugin

class ExampleCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		$0self.view.insert(edit, 0, "Hello, World!")
"""
        v.run_command("insert_snippet", {"contents": template})


class NewSnippetCommand(sublime_plugin.WindowCommand):
    def run(self):
        v = self.window.new_file()
        v.settings().set('default_dir',
            os.path.join(sublime.packages_path(), 'User'))
        v.settings().set('default_extension', 'sublime-snippet')
        v.set_syntax_file('Packages/XML/XML.tmLanguage')

        template = """<snippet>
	<content><![CDATA[
Hello, \${1:this} is a \${2:snippet}.
]]></content>
	<!-- Optional: Set a tabTrigger to define how to trigger the snippet -->
	<!-- <tabTrigger>hello</tabTrigger> -->
	<!-- Optional: Set a scope to limit where the snippet will trigger -->
	<!-- <scope>source.python</scope> -->
</snippet>
"""
        v.run_command("insert_snippet", {"contents": template})
