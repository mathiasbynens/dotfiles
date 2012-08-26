import HTMLGenerator
import Lexer
from DispatchHandler import DispatchHandler
import Keywords
from _SilverCity import find_lexer_module_by_id, PropertySet, WordList
from ScintillaConstants import SCLEX_XML
import LanguageInfo

class XMLLexer(Lexer.Lexer):
    def __init__(self, properties = PropertySet()):
        self._properties = properties
        self._lexer = find_lexer_module_by_id(SCLEX_XML)
        self._keyword_lists = [
            WordList(),
            WordList(),
            WordList(),
            WordList(),
            WordList(),
            WordList(Keywords.sgml_keywords)
                               ]

class XMLHandler(DispatchHandler):
    def __init__(self):
        DispatchHandler.__init__(self, 'SCE_H')

class XMLHTMLGenerator(HTMLGenerator.SimpleHTMLGenerator, XMLHandler):
    name = 'xml'
    description = 'XML'

    def __init__(self):
        XMLHandler.__init__(self)
        HTMLGenerator.SimpleHTMLGenerator.__init__(self, 'SCE_H')
            
    def generate_html(self, file, buffer, lexer = XMLLexer()):
        self._file = file
        
        lexer.tokenize_by_style(buffer, self.event_handler)

xml_language_info = LanguageInfo.LanguageInfo(
                'xml',
                 ['xml', 'dtd'],
                 [r'.*?\<\?xml.*?'],
                 [XMLHTMLGenerator]
            ) 

LanguageInfo.register_language(xml_language_info)        
