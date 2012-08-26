import ScintillaConstants
import Utils

def replace(text, *replacements):
    for old, new in replacements:
        text = text.replace(old, new)

    return text

class HTMLGenerator:
    def escape(self, text):
        return replace(text, ('&', '&amp;'), ('<', '&lt;'), ('>', '&gt;'))

    def preformat(self, text):
        text = self.escape(text.expandtabs())
        return replace(text, (' ', '&nbsp;'), ('\n', '<br/>\n'))

    def markup(self, text):
        # XXX This is stolen from pydoc and is way too python-centric
        # there should be some way to extend it
        import re
        
        results = []
        here = 0 
        pattern = re.compile(r'''\b((http|ftp)://[^ \t\n\r\f\v<'"]+|'''
                               r'RFC[- ]?(\d+)|'
                               r'PEP[- ]?(\d+))')
        while 1:
            match = pattern.search(text, here)
            if not match: break
            start, end = match.span()
            results.append(self.preformat(text[here:start]))

            all, scheme, rfc, pep = match.groups()
            if scheme:
                results.append('<a href="%s">%s</a>' % (all, self.preformat(all)))
            elif rfc:
                url = 'http://www.rfc-editor.org/rfc/rfc%d.txt' % int(rfc)
                results.append('<a href="%s">%s</a>' % (url, self.preformat(all)))
            elif pep:
                url = 'http://www.python.org/peps/pep-%04d.html' % int(pep)
                results.append('<a href="%s">%s</a>' % (url, self.preformat(all)))

            here = end
        results.append(self.preformat(text[here:]))
        return ''.join(results)

def generate_css_name(state):
    return state[4:].lower()

class SimpleHTMLGenerator(HTMLGenerator):
    def __init__(self, state_prefix):
        self.css_classes = {}
        for constant in Utils.list_states(state_prefix):
            self.css_classes[getattr(ScintillaConstants, constant)] = \
                generate_css_name(constant)

    def handle_other(self, style, text, **ignored):
        css_class = self.css_classes.get(style, '')
            
        if css_class:
            self._file.write('<span class="%s">' % css_class)
        
        self._file.write(self.markup(text))

        if css_class:
            self._file.write('</span>')