import HTMLGenerator
import Lexer
from DispatchHandler import DispatchHandler
import Keywords
from _SilverCity import find_lexer_module_by_id, PropertySet, WordList
from ScintillaConstants import SCLEX_NULL
import LanguageInfo

class NULLLexer(Lexer.Lexer):
    def __init__(self, properties = PropertySet()):
        self._properties = properties
        self._lexer = find_lexer_module_by_id(SCLEX_NULL)
        self._keyword_lists = []

class NULLHandler(DispatchHandler):
    def __init__(self):
        DispatchHandler.__init__(self, None)

class NULLHTMLGenerator(HTMLGenerator.HTMLGenerator, NULLHandler):
    name = 'null'
    description = 'No styling'
    
    def __init__(self):
        NULLHandler.__init__(self)
            
    def generate_html(self, file, buffer, lexer = NULLLexer()):
        self._file = file
        
        lexer.tokenize_by_style(buffer, self.event_handler)

    def handle_other(self, style, text, **ignored):
        self._file.write(self.markup(text))
        
null_language_info = LanguageInfo.LanguageInfo(
                'null',
                 ['text', 'txt'],
                 [],
                 [NULLHTMLGenerator]
            )

LanguageInfo.register_language(null_language_info) 
