import sublime, sublime_plugin

class ScrollToBof(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.show(0)

class ScrollToEof(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.show(self.view.size())

class ShowAtCenter(sublime_plugin.TextCommand):
	def run(self, edit):
		self.view.show_at_center(self.view.sel()[0])
