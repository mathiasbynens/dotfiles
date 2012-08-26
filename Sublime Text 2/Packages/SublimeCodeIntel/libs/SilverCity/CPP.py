import HTMLGenerator
import Keywords
import Lexer
from DispatchHandler import DispatchHandler
from _SilverCity import find_lexer_module_by_id, PropertySet, WordList
from ScintillaConstants import SCLEX_CPP
import LanguageInfo

class CPPLexer(Lexer.Lexer):
    def __init__(self, properties = PropertySet()):
        self._properties = properties
        self._lexer = find_lexer_module_by_id(SCLEX_CPP)
        self._keyword_lists = [
            WordList(Keywords.cpp_keywords),
            WordList(), # User defined (important functions, constants, etc.)
            WordList(Keywords.doxygen_keywords),
            WordList(), # "Fold header keywords" - whatever that is
            WordList(), # Global classes and typedefs
                               ]
            
class CPPHandler(DispatchHandler):
    def __init__(self):
        DispatchHandler.__init__(self, 'SCE_C')

class CPPHTMLGenerator(HTMLGenerator.SimpleHTMLGenerator, CPPHandler):
    name = 'cpp'
    description = 'C and C++'

    def __init__(self):
        CPPHandler.__init__(self)
        HTMLGenerator.SimpleHTMLGenerator.__init__(self, 'SCE_C')
            
    def generate_html(self, file, buffer, lexer = CPPLexer()):
        self._file = file
        
        lexer.tokenize_by_style(buffer, self.event_handler)


cpp_language_info = LanguageInfo.LanguageInfo(
                'C++',
                 ['c', 'c+', 'c++', 'cpp', 'cxx', 'h', 'hpp'],
                 [],
                 [CPPHTMLGenerator]
            ) 

LanguageInfo.register_language(cpp_language_info)
