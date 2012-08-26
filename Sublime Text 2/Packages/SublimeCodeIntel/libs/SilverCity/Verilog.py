import HTMLGenerator
import Keywords
import Lexer
from DispatchHandler import DispatchHandler
from _SilverCity import find_lexer_module_by_id, PropertySet, WordList
from ScintillaConstants import SCLEX_VERILOG
import LanguageInfo

class VerilogLexer(Lexer.Lexer):
    def __init__(self, properties = PropertySet()):
        self._properties = properties
        self._lexer = find_lexer_module_by_id(SCLEX_VERILOG)
        self._keyword_lists = [
            WordList(Keywords.verilog_keywords), #"Primary keywords and identifiers"
            WordList(Keywords.verilog_keywords2),# "Secondary keywords and identifiers"
            WordList(),# "System Tasks"
            WordList(),# "User defined tasks and identifiers"
            WordList(),# "Unused"
            ]
            
class VerilogHandler(DispatchHandler):
    def __init__(self):
        DispatchHandler.__init__(self, 'SCE_V')

class VerilogHTMLGenerator(HTMLGenerator.SimpleHTMLGenerator, VerilogHandler):
    name = 'verilog'
    description = 'verilog'

    def __init__(self):
        VerilogHandler.__init__(self)
        HTMLGenerator.SimpleHTMLGenerator.__init__(self, 'SCE_V')
            
    def generate_html(self, file, buffer, lexer = VerilogLexer()):
        self._file = file
        
        lexer.tokenize_by_style(buffer, self.event_handler)


verilog_language_info = LanguageInfo.LanguageInfo(
                'Verilog',
                 ['v', 'vh', 'sv', 'svh' ],
                 [],
                 [VerilogHTMLGenerator]
            ) 

LanguageInfo.register_language(verilog_language_info)
