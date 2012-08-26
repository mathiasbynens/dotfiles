import HTMLGenerator
import Keywords
import Lexer
from DispatchHandler import DispatchHandler
from _SilverCity import find_lexer_module_by_id, PropertySet, WordList
from ScintillaConstants import SCLEX_CPP
import LanguageInfo

class JavaLexer(Lexer.Lexer):
    def __init__(self, properties = PropertySet()):
        self._properties = properties
        self._lexer = find_lexer_module_by_id(SCLEX_CPP)
        self._keyword_lists = [
            WordList(Keywords.java_keywords),
            WordList(), # User defined (important functions, constants, etc.)
            WordList(Keywords.javadoc_keywords),
            WordList(), # "Fold header keywords" - whatever that is
            WordList(), # Global classes and typedefs
                               ]
            
class JavaHandler(DispatchHandler):
    def __init__(self):
        DispatchHandler.__init__(self, 'SCE_C')

class JavaHTMLGenerator(HTMLGenerator.SimpleHTMLGenerator, JavaHandler):
    name = 'java'
    description = 'Java'

    def __init__(self):
        JavaHandler.__init__(self)
        HTMLGenerator.SimpleHTMLGenerator.__init__(self, 'SCE_C')
            
    def generate_html(self, file, buffer, lexer = JavaLexer()):
        self._file = file
        
        lexer.tokenize_by_style(buffer, self.event_handler)


java_language_info = LanguageInfo.LanguageInfo(
                'Java',
                 ['java'],
                 [],
                 [JavaHTMLGenerator]
            ) 

LanguageInfo.register_language(java_language_info)