import HTMLGenerator
import Keywords
import Lexer
from DispatchHandler import DispatchHandler
from _SilverCity import find_lexer_module_by_id, PropertySet, WordList
from ScintillaConstants import SCLEX_SQL
import LanguageInfo

class SQLLexer(Lexer.Lexer):
    def __init__(self, properties = PropertySet()):
        self._properties = properties
        self._lexer = find_lexer_module_by_id(SCLEX_SQL)
        self._keyword_lists = [
            WordList(Keywords.sql_keywords),
            WordList(), # Database Objects
            WordList(), # PLDoc
            WordList(), # SQL*Plus
            WordList(), # User Keywords 1
            WordList(), # User Keywords 2
            WordList(), # User Keywords 3
            WordList()  # User Keywords 4
                               ]
            
class SQLHandler(DispatchHandler):
    def __init__(self):
        DispatchHandler.__init__(self, 'SCE_C')

class SQLHTMLGenerator(HTMLGenerator.SimpleHTMLGenerator, SQLHandler):
    name = 'sql'
    description = 'SQL'

    def __init__(self):
        SQLHandler.__init__(self)
        HTMLGenerator.SimpleHTMLGenerator.__init__(self, 'SCE_C')
            
    def generate_html(self, file, buffer, lexer = SQLLexer()):
        self._file = file
        
        lexer.tokenize_by_style(buffer, self.event_handler)

sql_language_info = LanguageInfo.LanguageInfo(
                'sql',
                 ['sql'],
                 [],
                 [SQLHTMLGenerator]
            ) 

LanguageInfo.register_language(sql_language_info)
