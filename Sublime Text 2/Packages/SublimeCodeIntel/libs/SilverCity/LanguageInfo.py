import re
import os
import types

class LanguageInfo:
    def __init__(self, language_name, extension_patterns, shebang_patterns, html_generators):
        self.language_name = language_name

        self.extension_patterns = []            
        self.extension_patterns = extension_patterns
        self.shebang_patterns = shebang_patterns
        self.html_generators = html_generators
               
    def known_extension(self, extension):
        for pattern in self.extension_patterns:
            # pattern can either be a regular expression or a
            # string
            if isinstance(pattern, types.StringTypes):
                if extension.lower() == pattern.lower():
                    return 1
            elif pattern.match(extension):
                return 1
        return 0
        
    def known_shebang(self, shebang):
        for pattern in self.shebang_patterns:
            if re.match(pattern, shebang):
                return 1
        return 0

    def get_default_html_generator(self):
        return self.html_generators[0]

def guess_languages_for_shebang(shebang):
    guesses = []
    for language in registered_languages:
        if language.known_shebang(shebang):
            guesses.append(language)

    return guesses

def guess_languages_for_extension(extension):
    guesses = []
    for language in registered_languages:
        if language.known_extension(extension):
            guesses.append(language)
    
    return guesses

def guess_language_for_file(filename):
    ext = os.path.splitext(os.path.basename(filename))[1]
    if len(ext) > 1:
        ext = ext[1:]
        extension_guesses = guess_languages_for_extension(ext)
    else:
        extension_guesses = []

    if len(extension_guesses) == 1:
        return extension_guesses[0]
    else:
        shebang = open(filename, 'r').readline()
        shebang_guesses = guess_languages_for_shebang(shebang)

        guesses = [eg for eg in extension_guesses
                       if eg in shebang_guesses]
            
        if len(guesses) == 1:
            return guesses[0]

        import NULL
        return NULL.null_language_info

def guess_language_for_buffer(buffer):
    shebang = buffer.split('\n')[0]
    guesses = guess_languages_for_shebang(shebang)
        
    if len(guesses) == 1:
        return guesses[0]

    import NULL
    return NULL.null_language_info
    
def find_generator_by_name(name):
    for language in registered_languages:
        for generator in language.html_generators:            
            if name == generator.name:
                return generator

def get_generator_names():
    names = []
    for language in registered_languages:
        for generator in language.html_generators:            
            names.append(generator.name)

    return names

def get_generator_names_descriptions():
    """Return a tuple of the name and description"""
    descs = []
    for language in registered_languages:
        for generator in language.html_generators:
            # if there is no description, use the name
            description = getattr(generator, "description", None)
            if description is None:
                description = generator.name
            descs.append((generator.name, description))

    return descs
    
registered_languages = []
def register_language(language):
    registered_languages.append(language)

def add_extension(name, ext):
    """Add an extension pattern (in regular expression syntax) to
    the named generator"""
    
    languages = []
    for language in registered_languages:
        for generator in language.html_generators:            
            if name == generator.name:
                language.extension_patterns.append(ext)
    
def do_registration():
    import CPP
    import CSS
    import HyperText
    import JavaScript
    import Java
    import NULL
    import Perl
    import Python    import PostScript
    import Ruby
    import SQL
    import Verilog
    import YAML
    import XML
    import XSLT
