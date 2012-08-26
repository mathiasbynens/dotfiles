import HTMLGenerator
import Lexer
import Keywords
from _SilverCity import find_lexer_module_by_id, PropertySet, WordList
from DispatchHandler import DispatchHandler
from ScintillaConstants import SCLEX_PYTHON
import LanguageInfo

class PythonLexer(Lexer.Lexer):
    def __init__(self, properties = PropertySet()):
        self._properties = properties
        self._lexer = find_lexer_module_by_id(SCLEX_PYTHON)
        self._keyword_lists = [
            WordList(Keywords.python_keywords),
            WordList(), # Highlighted identifiers
                            ]

class PythonHandler(DispatchHandler):
    def __init__(self):
        DispatchHandler.__init__(self, 'SCE_P')
        
    def event_handler(self, style, **kwargs):
        kwargs.update({'style' : style})
        # Mask out tab.timmy.whinge.level for dispatch
        handler = self.handlers.get(style & 63, None)
        if handler is None:
            self.handle_other(**kwargs)

        getattr(self, handler, self.handle_other)(**kwargs)
        
class PythonHTMLGenerator(HTMLGenerator.SimpleHTMLGenerator, PythonHandler):
    name = 'python'
    description = 'Python'
    
    def __init__(self):
        PythonHandler.__init__(self)
        HTMLGenerator.SimpleHTMLGenerator.__init__(self, 'SCE_P')
        
    def handle_other(self, style, text, **ignored):
        tab_problem = style & 64
        style = style & 63
        css_class = self.css_classes.get(style, '')
            
        if css_class:
            self._file.write('<span class="%s">' % css_class)

        if tab_problem:
            self._file.write('<span class="p_tabtimmywingylevel">')
        
        self._file.write(self.markup(text))

        if tab_problem:
            self._file.write('</span>')

        if css_class:
            self._file.write('</span>')

    def generate_html(self, file, buffer, lexer = PythonLexer()):
        self._file = file
        
        lexer.tokenize_by_style(buffer, self.event_handler)

import HyperText
class EmbeddedHyperTextHTMLGenerator(HyperText.HyperTextHTMLGenerator):
    def handle_h_tag(self, text, **ignored):
        self._file.write('<span class="python_h_tag">')
        self._file.write(self.markup(text))
        self._file.write('</span>')
        
    def handle_h_tag_unknown(self, **kwargs):
        self.handle_h_tag(**kwargs)

    def handle_h_attribute(self, text, **ignored):
        self._file.write('<span class="python_h_attribute">')
        self._file.write(self.markup(text))
        self._file.write('</span>')

    def handle_h_attribute_unknown(self, **kwargs):
        self.handle_h_attribute(**kwargs)
        
    def handle_h_double_string(self, text, **ignored):
        self._file.write('<span class="python_h_string">')
        self._file.write(self.markup(text))
        self._file.write('</span>')

    def handle_h_string_string(self, **kwargs):
        self.handle_h_double_string(**kwargs)

    def handle_other(self, style, text, **ignored):
        self._file.write('<span class="python_string">')
        self._file.write(self.markup(text))
        self._file.write('</span>')

def looks_like_markup(s):
    return s.count('<') and (s.count('/>') or s.count('</'))

def looks_like_xsl(s):
    return s.find('xsl:') != -1

def looks_like_html(s):
    # This is pretty bad...
    return s.count('html')

def guess_generator(s):
    import HyperText
    import XML
    import XSLT
    
    if looks_like_markup(s):
        if looks_like_xsl(s):
            return XSLT.XSLTHTMLGenerator()
        elif looks_like_html(s):
            return HyperText.HyperTextHTMLGenerator()
        else:
            return XML.XMLHTMLGenerator()

    return None

class SmartPythonHTMLGenerator(PythonHTMLGenerator):
    name = 'smart_python'
    description = 'Python with styled strings'

    def __init__(self):
        PythonHandler.__init__(self)
        HTMLGenerator.SimpleHTMLGenerator.__init__(self, 'SCE_P')
        
    def handle_p_string(self, text, **ignored):
        generator = guess_generator(text)
        if generator is not None:
            generator.generate_html(self._file, text)
        else:
            self.handle_other(text=text, **ignored)
                
    def handle_p_character(self, **kwargs):
        self.handle_p_string(**kwargs)
        
    def handle_p_triple(self, **kwargs):
        self.handle_p_string(**kwargs)
        
    def handle_p_tripledouble(self, **kwargs):
        self.handle_p_string(**kwargs)
        
    def handle_p_stringeol(self, **kwargs):
        self.handle_p_string(**kwargs)


python_language_info = LanguageInfo.LanguageInfo(
                'python',
                 ['py', 'pyw', 'cgi'],
                 ['.*?python.*?'],
                 [PythonHTMLGenerator, SmartPythonHTMLGenerator]
            )

LanguageInfo.register_language(python_language_info) 
