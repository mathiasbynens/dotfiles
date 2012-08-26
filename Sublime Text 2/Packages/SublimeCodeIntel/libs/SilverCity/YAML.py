import HTMLGenerator
import Keywords
import Lexer
from DispatchHandler import DispatchHandler
from _SilverCity import find_lexer_module_by_id, PropertySet, WordList
from ScintillaConstants import SCLEX_YAML
import LanguageInfo

class YAMLLexer(Lexer.Lexer):
    def __init__(self, properties = PropertySet()):
        self._properties = properties
        self._lexer = find_lexer_module_by_id(SCLEX_YAML)
        self._keyword_lists = [
            WordList(Keywords.yaml_keywords),
                               ]
            
class YAMLHandler(DispatchHandler):
    def __init__(self):
        DispatchHandler.__init__(self, 'SCE_YAML')

class YAMLHTMLGenerator(HTMLGenerator.SimpleHTMLGenerator, YAMLHandler):
    name = 'yaml'
    description = 'YAML'

    def __init__(self):
        YAMLHandler.__init__(self)
        HTMLGenerator.SimpleHTMLGenerator.__init__(self, 'SCE_YAML')
            
    def generate_html(self, file, buffer, lexer = YAMLLexer()):
        self._file = file
        
        lexer.tokenize_by_style(buffer, self.event_handler)


yaml_language_info = LanguageInfo.LanguageInfo(
                'YAML',
                 ['yml', 'yaml'],
                 [],
                 [YAMLHTMLGenerator]
            ) 

LanguageInfo.register_language(yaml_language_info)
