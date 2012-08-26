import HTMLGenerator
import Keywords
import Lexer
from DispatchHandler import DispatchHandler
from _SilverCity import find_lexer_module_by_id, PropertySet, WordList
from ScintillaConstants import SCLEX_PS
import LanguageInfo

class PostScriptLexer(Lexer.Lexer):
    def __init__(self, properties = PropertySet()):
        self._properties = properties
        self._lexer = find_lexer_module_by_id(SCLEX_PS)
        self._keyword_lists = [
            WordList(Keywords.postscript_level1_keywords),
            WordList(Keywords.postscript_level2_keywords),
            WordList(Keywords.postscript_level3_keywords),
            WordList(Keywords.postscript_ripspecific_keywords),
            WordList()
                               ]
            
class PostScriptHandler(DispatchHandler):
    def __init__(self):
        DispatchHandler.__init__(self, 'SCE_PS')

class PostScriptHTMLGenerator(HTMLGenerator.SimpleHTMLGenerator, PostScriptHandler):
    name = 'ps'
    description = 'PostScript'
    
    def __init__(self):
        PostScriptHandler.__init__(self)
        HTMLGenerator.SimpleHTMLGenerator.__init__(self, 'SCE_PS')
            
    def generate_html(self, file, buffer, lexer = PostScriptLexer()):
        self._file = file
        
        lexer.tokenize_by_style(buffer, self.event_handler)

postscript_language_info = LanguageInfo.LanguageInfo(
                'PostScript',
                 ['ps', 'eps', 'postscript'],
                 ['.*?PS-.*?'],
                 [PostScriptHTMLGenerator]
            ) 

LanguageInfo.register_language(postscript_language_info)
