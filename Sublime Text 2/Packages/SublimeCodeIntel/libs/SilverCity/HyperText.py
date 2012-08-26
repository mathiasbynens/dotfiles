import HTMLGenerator
import Lexer
from DispatchHandler import DispatchHandler
import Keywords
from _SilverCity import find_lexer_module_by_id, PropertySet, WordList
from ScintillaConstants import SCLEX_HTML
import LanguageInfo
import re

class HyperTextLexer(Lexer.Lexer):
    def __init__(self, properties = PropertySet()):
        self._properties = properties
        self._lexer = find_lexer_module_by_id(SCLEX_HTML)
        self._keyword_lists = [
            WordList(Keywords.hypertext_keywords),
            WordList(Keywords.js_keywords),
            WordList(Keywords.vb_keywords),
            WordList(Keywords.python_keywords),
            WordList(Keywords.php_keywords),
            WordList(Keywords.sgml_keywords)
                               ]
class HyperTextHandler(DispatchHandler):
    def __init__(self):
        DispatchHandler.__init__(self, 'SCE_H')

class HyperTextHTMLGenerator(HTMLGenerator.SimpleHTMLGenerator, HyperTextHandler):
    name = 'html'
    description = 'HTML and PHP [with embedded: JavaScript, VBScript, Python]'

    def __init__(self):
        HyperTextHandler.__init__(self)
        HTMLGenerator.SimpleHTMLGenerator.__init__(self, 'SCE_H')

    def generate_html(self, file, buffer, lexer = HyperTextLexer()):
        self._file = file
        
        lexer.tokenize_by_style(buffer, self.event_handler)

html_language_info = LanguageInfo.LanguageInfo(
                'html',
                 ['html', 'htm', 'xhtml', re.compile('^php(\d)?$', re.IGNORECASE), 'inc'],
                 ['.*?\<!DOCTYPE\s+html'],
                 [HyperTextHTMLGenerator]
            ) 

LanguageInfo.register_language(html_language_info)
