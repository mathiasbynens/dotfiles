import HTMLGenerator
import Lexer
from DispatchHandler import DispatchHandler
import Keywords
from _SilverCity import find_lexer_module_by_id, PropertySet, WordList
from ScintillaConstants import SCLEX_XML
import LanguageInfo

class XSLTLexer(Lexer.Lexer):
    def __init__(self, properties = PropertySet()):
        self._properties = properties
        self._lexer = find_lexer_module_by_id(SCLEX_XML)
        self._keyword_lists = [
            WordList(Keywords.xslt_keywords),
            WordList(Keywords.js_keywords),
            WordList(Keywords.vb_keywords),
            WordList(Keywords.python_keywords),
            WordList(Keywords.php_keywords),
            WordList(Keywords.sgml_keywords)
                               ]

class XSLTHandler(DispatchHandler):
    def __init__(self):
        DispatchHandler.__init__(self, 'SCE_H')

class XSLTHTMLGenerator(HTMLGenerator.SimpleHTMLGenerator, XSLTHandler):
    name = 'xslt'
    description = 'XSLT'

    def __init__(self):
        XSLTHandler.__init__(self)
        HTMLGenerator.SimpleHTMLGenerator.__init__(self, 'SCE_H')
            
    def generate_html(self, file, buffer, lexer = XSLTLexer()):
        self._file = file
        
        lexer.tokenize_by_style(buffer, self.event_handler)

xslt_language_info = LanguageInfo.LanguageInfo(
                'xslt',
                 ['xsl', 'xslt'],
                 [],
                 [XSLTHTMLGenerator]
            ) 

LanguageInfo.register_language(xslt_language_info) 
