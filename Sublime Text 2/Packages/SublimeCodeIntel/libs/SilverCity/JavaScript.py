import HTMLGenerator
import Keywords
import Lexer
from DispatchHandler import DispatchHandler
from _SilverCity import find_lexer_module_by_id, PropertySet, WordList
from ScintillaConstants import SCLEX_CPP
import LanguageInfo

class JavaScriptLexer(Lexer.Lexer):
    def __init__(self, properties = PropertySet()):
        self._properties = properties
        self._lexer = find_lexer_module_by_id(SCLEX_CPP)
        self._keyword_lists = [
            WordList(Keywords.js_keywords),
            WordList(),
            WordList(),
            WordList(),
            WordList()
                               ]
            
class JavaScriptHandler(DispatchHandler):
    def __init__(self):
        DispatchHandler.__init__(self, 'SCE_C')

class JavaScriptHTMLGenerator(HTMLGenerator.SimpleHTMLGenerator, JavaScriptHandler):
    name = 'js'
    description = 'JavaScript'
    
    def __init__(self):
        JavaScriptHandler.__init__(self)
        HTMLGenerator.SimpleHTMLGenerator.__init__(self, 'SCE_C')
            
    def generate_html(self, file, buffer, lexer = JavaScriptLexer()):
        self._file = file
        
        lexer.tokenize_by_style(buffer, self.event_handler)

javascript_language_info = LanguageInfo.LanguageInfo(
                'JavaScript',
                 ['js', 'javascript'],
                 [],
                 [JavaScriptHTMLGenerator]
            ) 

LanguageInfo.register_language(javascript_language_info)
