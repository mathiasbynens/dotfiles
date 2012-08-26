#!/usr/bin/env python

# Copyright (c) 2006 Bermi Ferrer Martinez
# info at bermi dot org
# See the end of this file for the free software, open source license (BSD-style).

import re
from Base import Base

class English (Base):
    """
    Inflector for pluralize and singularize English nouns.
    
    This is the default Inflector for the Inflector obj
    """
    
    def pluralize(self, word) :
        '''Pluralizes English nouns.'''
        
        rules = [
            ['(?i)(quiz)$' , '\\1zes'],
            ['^(?i)(ox)$' , '\\1en'],
            ['(?i)([m|l])ouse$' , '\\1ice'],
            ['(?i)(matr|vert|ind)ix|ex$' , '\\1ices'],
            ['(?i)(x|ch|ss|sh)$' , '\\1es'],
            ['(?i)([^aeiouy]|qu)ies$' , '\\1y'],
            ['(?i)([^aeiouy]|qu)y$' , '\\1ies'],
            ['(?i)(hive)$' , '\\1s'],
            ['(?i)(?:([^f])fe|([lr])f)$' , '\\1\\2ves'],
            ['(?i)sis$' , 'ses'],
            ['(?i)([ti])um$' , '\\1a'],
            ['(?i)(buffal|tomat)o$' , '\\1oes'],
            ['(?i)(bu)s$' , '\\1ses'],
            ['(?i)(alias|status)' , '\\1es'],
            ['(?i)(octop|vir)us$' , '\\1i'],
            ['(?i)(ax|test)is$' , '\\1es'],
            ['(?i)s$' , 's'],
            ['(?i)$' , 's']
        ]
        
        uncountable_words = ['equipment', 'information', 'rice', 'money', 'species', 'series', 'fish', 'sheep']
        
        irregular_words = {
            'person' : 'people',
            'man' : 'men',
            'child' : 'children',
            'sex' : 'sexes',
            'move' : 'moves'
        }
        
        lower_cased_word = word.lower();
        
        for uncountable_word in uncountable_words:
            if lower_cased_word[-1*len(uncountable_word):] == uncountable_word :
                return word
        
        for irregular in irregular_words.keys():
            match = re.search('('+irregular+')$',word, re.IGNORECASE)
            if match:
                return re.sub('(?i)'+irregular+'$', match.expand('\\1')[0]+irregular_words[irregular][1:], word)
        
        for rule in range(len(rules)):
            match = re.search(rules[rule][0], word, re.IGNORECASE)
            if match :
                groups = match.groups()
                for k in range(0,len(groups)) :
                    if groups[k] == None :
                        rules[rule][1] = rules[rule][1].replace('\\'+str(k+1), '')
                        
                return re.sub(rules[rule][0], rules[rule][1], word)
        
        return word


    def singularize (self, word) :
        '''Singularizes English nouns.'''
        
        rules = [
            ['(?i)(quiz)zes$' , '\\1'],
            ['(?i)(matr)ices$' , '\\1ix'],
            ['(?i)(vert|ind)ices$' , '\\1ex'],
            ['(?i)^(ox)en' , '\\1'],
            ['(?i)(alias|status)es$' , '\\1'],
            ['(?i)([octop|vir])i$' , '\\1us'],
            ['(?i)(cris|ax|test)es$' , '\\1is'],
            ['(?i)(shoe)s$' , '\\1'],
            ['(?i)(o)es$' , '\\1'],
            ['(?i)(bus)es$' , '\\1'],
            ['(?i)([m|l])ice$' , '\\1ouse'],
            ['(?i)(x|ch|ss|sh)es$' , '\\1'],
            ['(?i)(m)ovies$' , '\\1ovie'],
            ['(?i)(s)eries$' , '\\1eries'],
            ['(?i)([^aeiouy]|qu)ies$' , '\\1y'],
            ['(?i)([lr])ves$' , '\\1f'],
            ['(?i)(tive)s$' , '\\1'],
            ['(?i)(hive)s$' , '\\1'],
            ['(?i)([^f])ves$' , '\\1fe'],
            ['(?i)(^analy)ses$' , '\\1sis'],
            ['(?i)((a)naly|(b)a|(d)iagno|(p)arenthe|(p)rogno|(s)ynop|(t)he)ses$' , '\\1\\2sis'],
            ['(?i)([ti])a$' , '\\1um'],
            ['(?i)(n)ews$' , '\\1ews'],
            ['(?i)s$' , ''],
        ];
    
        uncountable_words = ['equipment', 'information', 'rice', 'money', 'species', 'series', 'fish', 'sheep','sms'];
    
        irregular_words = {
            'people' : 'person',
            'men' : 'man',
            'children' : 'child',
            'sexes' : 'sex',
            'moves' : 'move'
        }
    
        lower_cased_word = word.lower();
    
        for uncountable_word in uncountable_words:
            if lower_cased_word[-1*len(uncountable_word):] == uncountable_word :
                return word
            
        for irregular in irregular_words.keys():
            match = re.search('('+irregular+')$',word, re.IGNORECASE)
            if match:
                return re.sub('(?i)'+irregular+'$', match.expand('\\1')[0]+irregular_words[irregular][1:], word)
            

        for rule in range(len(rules)):
            match = re.search(rules[rule][0], word, re.IGNORECASE)
            if match :
                groups = match.groups()
                for k in range(0,len(groups)) :
                    if groups[k] == None :
                        rules[rule][1] = rules[rule][1].replace('\\'+str(k+1), '')
                        
                return re.sub(rules[rule][0], rules[rule][1], word)
        
        return word
    


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