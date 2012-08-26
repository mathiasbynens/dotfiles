import string
import sublime
import sublime_plugin

class Transformer(sublime_plugin.TextCommand):
    def run(self, edit):
        self.transform(self.transformer[0], self.view, edit)

    def transform(self, f, view, edit):
        for s in view.sel():
            if s.empty():
                s = view.word(s)

            txt = f(view.substr(s))
            view.replace(edit, s, txt)

class SwapCaseCommand(Transformer):
    transformer = string.swapcase,

class UpperCaseCommand(Transformer):
    transformer = string.upper,

class LowerCaseCommand(Transformer):
    transformer = string.lower,

class TitleCaseCommand(Transformer):
    transformer = lambda s: string.capwords(s, " "),

def rot13(ch):
    o = ord(ch)
    if o >= ord('a') and o <= ord('z'):
        return unichr((o - ord('a') + 13) % 26 + ord('a'))
    if o >= ord('A') and o <= ord('Z'):
        return unichr((o - ord('A') + 13) % 26 + ord('A'))
    return ch

class Rot13Command(Transformer):
    transformer = lambda s: "".join([rot13(ch) for ch in s]),
