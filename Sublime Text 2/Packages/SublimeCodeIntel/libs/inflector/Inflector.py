#!/usr/bin/env python

# Copyright (c) 2006 Bermi Ferrer Martinez
# info at bermi dot org
# See the end of this file for the free software, open source license (BSD-style).

import re
from Rules.English import English
from Rules.Spanish import Spanish

class Inflector :
    """
    Inflector for pluralize and singularize nouns.
    
    It also provides method for helping to create programs 
    based on naming conventions like on Ruby on Rails.
    """
    
    def __init__( self, Inflector = English ) :
        assert callable(Inflector), "Inflector should be a callable obj"
        self.Inflector = apply(Inflector);
        
    def pluralize(self, word) :
        '''Pluralizes nouns.'''
        return self.Inflector.pluralize(word)
    
    def singularize(self, word) :
        '''Singularizes nouns.'''
        return self.Inflector.singularize(word)
    
    def conditionalPlural(self, numer_of_records, word) :
        '''Returns the plural form of a word if first parameter is greater than 1'''
        return self.Inflector.conditionalPlural(numer_of_records, word)

    def titleize(self, word, uppercase = '') :
        '''Converts an underscored or CamelCase word into a sentence.
            The titleize function converts text like "WelcomePage",
            "welcome_page" or  "welcome page" to this "Welcome Page".
            If the "uppercase" parameter is set to 'first' it will only
            capitalize the first character of the title.'''
        return self.Inflector.titleize(word, uppercase)

    def camelize(self, word):
        ''' Returns given word as CamelCased
        Converts a word like "send_email" to "SendEmail". It
        will remove non alphanumeric character from the word, so
        "who's online" will be converted to "WhoSOnline"'''
        return self.Inflector.camelize(word)
    
    def underscore(self, word) :
        ''' Converts a word "into_it_s_underscored_version"
        Convert any "CamelCased" or "ordinary Word" into an
        "underscored_word".
        This can be really useful for creating friendly URLs.'''
        return self.Inflector.underscore(word)
    
    def humanize(self, word, uppercase = '') :
        '''Returns a human-readable string from word
        Returns a human-readable string from word, by replacing
        underscores with a space, and by upper-casing the initial
        character by default.
        If you need to uppercase all the words you just have to
        pass 'all' as a second parameter.'''
        return self.Inflector.humanize(word, uppercase)
    
    
    def variablize(self, word) :
        '''Same as camelize but first char is lowercased
        Converts a word like "send_email" to "sendEmail". It
        will remove non alphanumeric character from the word, so
        "who's online" will be converted to "whoSOnline"'''
        return self.Inflector.variablize(word)
    
    def tableize(self, class_name) :
        ''' Converts a class name to its table name according to rails
        naming conventions. Example. Converts "Person" to "people" '''
        return self.Inflector.tableize(class_name)
    
    def classify(self, table_name) :
        '''Converts a table name to its class name according to rails
        naming conventions. Example: Converts "people" to "Person" '''
        return self.Inflector.classify(table_name)
    
    def ordinalize(self, number) :
        '''Converts number to its ordinal form.
        This method converts 13 to 13th, 2 to 2nd ...'''
        return self.Inflector.ordinalize(number)
    
    
    def unaccent(self, text) :
        '''Transforms a string to its unaccented version. 
        This might be useful for generating "friendly" URLs'''
        return self.Inflector.unaccent(text)
    
    def urlize(self, text) :
        '''Transform a string its unaccented and underscored
        version ready to be inserted in friendly URLs'''
        return self.Inflector.urlize(text)
    
    
    def demodulize(self, module_name) :
        return self.Inflector.demodulize(module_name)
    
    def modulize(self, module_description) :
        return self.Inflector.modulize(module_description)
    
    def foreignKey(self, class_name, separate_class_name_and_id_with_underscore = 1) :
        ''' Returns class_name in underscored form, with "_id" tacked on at the end. 
        This is for use in dealing with the database.'''
        return self.Inflector.foreignKey(class_name, separate_class_name_and_id_with_underscore)
    



# Copyright (c) 2006 Bermi Ferrer Martinez
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software to deal in this software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of this software, and to permit
# persons to whom this software is furnished to do so, subject to the following
# condition:
#
# THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THIS SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THIS SOFTWARE.