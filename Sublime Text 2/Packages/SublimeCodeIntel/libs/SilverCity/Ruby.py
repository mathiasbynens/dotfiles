import HTMLGenerator
import Lexer
import Keywords
from _SilverCity import find_lexer_module_by_id, PropertySet, WordList
from DispatchHandler import DispatchHandler
from ScintillaConstants import SCLEX_RUBY
import LanguageInfo
import Python

class RubyLexer(Lexer.Lexer):
    def __init__(self, properties = PropertySet()):
        self._properties = properties
        self._lexer = find_lexer_module_by_id(SCLEX_RUBY)
        self._keyword_lists = [
            WordList(Keywords.ruby_keywords)
                            ]

class RubyHandler(Python.PythonHandler):
    pass

# This is a hack since we now subclass PythonHandler instead of
# RubyHandler
class RubyHTMLGenerator(Python.PythonHTMLGenerator):
    name = 'ruby'
    description = 'Ruby'

    def __init__(self):
        Python.PythonHTMLGenerator.__init__(self)

    def generate_html(self, file, buffer, lexer = RubyLexer()):
        self._file = file
        
        lexer.tokenize_by_style(buffer, self.event_handler)
        
ruby_language_info = LanguageInfo.LanguageInfo(
                'ruby',
                 ['rb', 'cgi'],
                 ['.*?ruby.*?'],
                 [RubyHTMLGenerator]
            )

LanguageInfo.register_language(ruby_language_info)
