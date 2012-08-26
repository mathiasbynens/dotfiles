import HTMLGenerator
import Keywords
import Lexer
from DispatchHandler import DispatchHandler
from _SilverCity import find_lexer_module_by_id, PropertySet, WordList
from ScintillaConstants import SCLEX_PERL
import LanguageInfo

class PerlLexer(Lexer.Lexer):
    def __init__(self, properties = PropertySet()):
        self._properties = properties
        self._lexer = find_lexer_module_by_id(SCLEX_PERL)
        self._keyword_lists = [
            WordList(Keywords.perl_keywords),
                               ]
            
class PerlHandler(DispatchHandler):
    def __init__(self):
        DispatchHandler.__init__(self, 'SCE_PL')

class PerlHTMLGenerator(HTMLGenerator.SimpleHTMLGenerator, PerlHandler):
    name = 'perl'
    description = 'Perl'
    
    def __init__(self):
        PerlHandler.__init__(self)
        HTMLGenerator.SimpleHTMLGenerator.__init__(self, 'SCE_PL')
            
    def generate_html(self, file, buffer, lexer = PerlLexer()):
        self._file = file
        
        lexer.tokenize_by_style(buffer, self.event_handler)

perl_language_info = LanguageInfo.LanguageInfo(
                'perl',
                 ['pl', 'cgi'],
                 ['.*?perl.*?'],
                 [PerlHTMLGenerator]
            ) 

LanguageInfo.register_language(perl_language_info)
