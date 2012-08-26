import HTMLGenerator
import Keywords
import Lexer
from DispatchHandler import DispatchHandler
from _SilverCity import find_lexer_module_by_id, PropertySet, WordList
from ScintillaConstants import SCLEX_CSS
import LanguageInfo

class _CSSLexerTemplate(Lexer.Lexer):
    def __init__(self, properties):
        self._properties = properties
        self._lexer = find_lexer_module_by_id(SCLEX_CSS)
        self._keyword_lists = [
            WordList(Keywords.css_keywords),
            WordList(Keywords.css_pseudo_classes),
            WordList(Keywords.css_keywords_2),
            WordList(Keywords.css_properties_3),
            WordList(Keywords.css_pseudo_elements),
            WordList(Keywords.css_browser_specific_properties),
            WordList(Keywords.css_browser_specific_pseudo_classes),
            WordList(Keywords.css_browser_specific_pseudo_elements),
                               ]

class CSSLexer(_CSSLexerTemplate):
    def __init__(self, properties = PropertySet()):
        _CSSLexerTemplate.__init__(self, properties)
            
class SCSSLexer(_CSSLexerTemplate):
    def __init__(self, properties = PropertySet()):
        _CSSLexerTemplate.__init__(self, properties)
        properties['lexer.css.scss.language'] = '1'

class LessLexer(_CSSLexerTemplate):
    def __init__(self, properties = PropertySet()):
        _CSSLexerTemplate.__init__(self, properties)
        properties['lexer.css.less.language'] = '1'

class CSSHandler(DispatchHandler):
    def __init__(self):
        DispatchHandler.__init__(self, 'SCE_CSS')

class CSSHTMLGenerator(HTMLGenerator.SimpleHTMLGenerator, CSSHandler):
    name = 'css'
    description = 'Cascading Style Sheets'
    
    def __init__(self):
        CSSHandler.__init__(self)
        HTMLGenerator.SimpleHTMLGenerator.__init__(self, 'SCE_CSS')
            
    def generate_html(self, file, buffer, lexer = CSSLexer()):
        self._file = file
        lexer.tokenize_by_style(buffer, self.event_handler)

css_language_info = LanguageInfo.LanguageInfo(
                'css',
                 ['css'],
                 ['.*?css.*?'],
                 [CSSHTMLGenerator]
            ) 

LanguageInfo.register_language(css_language_info)
