# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
# 
# The contents of this file are subject to the Mozilla Public License
# Version 1.1 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
# 
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See the
# License for the specific language governing rights and limitations
# under the License.
# 
# The Original Code is Komodo code.
# 
# The Initial Developer of the Original Code is ActiveState Software Inc.
# Portions created by ActiveState Software Inc are Copyright (C) 2000-2007
# ActiveState Software Inc. All Rights Reserved.
# 
# Contributor(s):
#   ActiveState Software Inc
# 
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
# 
# ***** END LICENSE BLOCK *****

CommonStates = [
    'default', 'comments', 'numbers', 'strings', 'keywords',
    'classes', 'functions', 'operators', 'identifiers',
    'stringeol', 'preprocessor', 'bracebad', 'bracehighlight',
    'control characters', 'linenumbers', 'fold markers', 'indent guides',
    'stdin', 'stdout', 'stderr'
]

# We could move this to the languages
StateMap = {
    'Rx': {
        'default': (0,),
        'breakpoints': (1,),
        'children': (2,),
        'parents': (3,),
    },
    'Regex': {
        #XXX Should I be using 'default'=32? My reading of the Scintilla
        #    docs says that I should, but every Scintilla lexer uses 0.
        "default": (0,),
        # XXX Should I use the common "comments" (i.e. plural) here?
        "comment": (1,), # (?#...)
        "text": (2,),
        "special": (3,), # standalone (. ^ $ |), in charset (^ -)
        "charset_operator": (4,),
        "operator": (5,), # open/close paren (use operator for paren matching by scintilla)
        "groupref": (6,), 
        "quantifier": (7,),
        "grouptag": (8,),
        "charclass": (9,),
        "charescape": (10,),
        "eol": (11,), #XXX not currently used
        "match_highlight": (12,),
    },
    'Python': {
        'default': ('SCE_P_DEFAULT',),
        'comments' : ('SCE_P_COMMENTLINE',
                      'SCE_P_COMMENTBLOCK'),
        'numbers': ('SCE_P_NUMBER',),
        'strings': ('SCE_P_STRING',
                    'SCE_P_CHARACTER', 
                    'SCE_P_TRIPLE',
                    'SCE_P_TRIPLEDOUBLE'),
        'keywords': ('SCE_P_WORD',),
        'keywords2': ('SCE_P_WORD2',),
        'classes': ('SCE_P_CLASSNAME',),
        'functions': ('SCE_P_DEFNAME',),
        'operators': ('SCE_P_OPERATOR',),
        'identifiers': ('SCE_P_IDENTIFIER',),
        'stringeol' : ('SCE_P_STRINGEOL',),
        'decorators' : ('SCE_P_DECORATOR',),
        'stdin': ('SCE_P_STDIN',),
        'stdout': ('SCE_P_STDOUT',),
        'stderr' : ('SCE_P_STDERR',),
        },
    'C++': {
        'default': ('SCE_C_DEFAULT',),
        'comments': ('SCE_C_COMMENT',
                     'SCE_C_COMMENTLINE',
                     'SCE_C_COMMENTDOC',
                     'SCE_C_COMMENTLINEDOC',
                     'SCE_C_COMMENTDOCKEYWORD',
                     'SCE_C_COMMENTDOCKEYWORDERROR',
                     ),
        'numbers': ('SCE_C_NUMBER',),
        'strings': ('SCE_C_STRING',
                    'SCE_C_CHARACTER',
                    ),
        'keywords': ('SCE_C_WORD',),
        'keywords2': ('SCE_C_WORD2',),
        'operators': ('SCE_C_OPERATOR',),
        'identifiers': ('SCE_C_IDENTIFIER',),
        'stringeol': ('SCE_C_STRINGEOL',),
        'preprocessor': ('SCE_C_PREPROCESSOR',),
        # these are specific to this lexer
        'UUIDs': ('SCE_C_UUID',),
        'verbatim': ('SCE_C_VERBATIM',),
        'regex': ('SCE_C_REGEX',),
        'commentdockeyword': ('SCE_C_COMMENTDOCKEYWORD',),
        'commentdockeyworderror': ('SCE_C_COMMENTDOCKEYWORDERROR',),
        'globalclass': ('SCE_C_GLOBALCLASS',),
        'stringeol' : ('SCE_C_STRINGEOL',),
        'stdin': ('SCE_C_STDIN',),
        'stdout': ('SCE_C_STDOUT',),
        'stderr' : ('SCE_C_STDERR',),
    },
    'VisualBasic': {
        'default': ('SCE_B_DEFAULT',),
        'comments': ('SCE_B_COMMENT',),
        'numbers': ('SCE_B_NUMBER',),
        'keywords': ('SCE_B_KEYWORD',),
        'strings': ('SCE_B_STRING',),
        'preprocessor': ('SCE_B_PREPROCESSOR',),
        'operators': ('SCE_B_OPERATOR',),
        'identifiers': ('SCE_B_IDENTIFIER',),
        # specific to VB
        'dates': ('SCE_B_DATE',),
        },
    'LaTex': {
        'default': ('SCE_L_DEFAULT',),
        'comments': ('SCE_L_COMMENT',),

        'commands': ('SCE_L_COMMAND',),
        'tags': ('SCE_L_TAG',),
        'math': ('SCE_L_MATH',),
    },
    'Lua': {
        'default': ('SCE_LUA_DEFAULT',),
        'comments': ('SCE_LUA_COMMENT',
                     'SCE_LUA_COMMENTLINE',
                     'SCE_LUA_COMMENTDOC',),
        'numbers': ('SCE_LUA_NUMBER',),
        'strings': ('SCE_LUA_STRING',
                    'SCE_LUA_CHARACTER',
                    'SCE_LUA_LITERALSTRING',
                    ),
        'preprocessor': ('SCE_LUA_PREPROCESSOR',),
        'operators': ('SCE_LUA_OPERATOR',),
        'identifiers': ('SCE_LUA_IDENTIFIER',),
        'stringeol': ('SCE_LUA_STRINGEOL',),
        'keywords': ('SCE_LUA_WORD',),
        'keywords2': ('SCE_LUA_WORD2',
                      'SCE_LUA_WORD3',
                      'SCE_LUA_WORD4',
                      'SCE_LUA_WORD5',
                      'SCE_LUA_WORD6',),
    },
    'Tcl': {
        'default': ('SCE_TCL_DEFAULT',),
        'comments': ('SCE_TCL_COMMENT',),
        'variables': ('SCE_TCL_VARIABLE',),
        'arrays': ('SCE_TCL_ARRAY',),
        'numbers': ('SCE_TCL_NUMBER',),
        'keywords': ('SCE_TCL_WORD',),
        'strings': ('SCE_TCL_STRING',
                    'SCE_TCL_CHARACTER',
                    'SCE_TCL_LITERAL',),
        'identifiers': ('SCE_TCL_IDENTIFIER',),
        'operators': ('SCE_TCL_OPERATOR',),
        'stringeol': ('SCE_TCL_EOL',),
        'stdin': ('SCE_TCL_STDIN',),
        'stdout': ('SCE_TCL_STDOUT',),
        'stderr' : ('SCE_TCL_STDERR',),
    },
    'UDL' : {
        'default': ('SCE_UDL_M_TAGSPACE',
                    'SCE_UDL_M_DEFAULT',
                    'SCE_UDL_CSS_DEFAULT',
                    'SCE_UDL_CSL_DEFAULT',
                    'SCE_UDL_SSL_DEFAULT',
                    'SCE_UDL_TPL_DEFAULT',
                    ),
        'identifiers': ('SCE_UDL_CSS_IDENTIFIER',
                        'SCE_UDL_CSL_IDENTIFIER',
                        'SCE_UDL_SSL_IDENTIFIER',
                        'SCE_UDL_TPL_IDENTIFIER',
                        ),
        'numbers': ('SCE_UDL_CSS_NUMBER',
                    'SCE_UDL_CSL_NUMBER',
                    'SCE_UDL_SSL_NUMBER',
                    'SCE_UDL_TPL_NUMBER',
                    ),
        'strings': ('SCE_UDL_M_STRING',
                    'SCE_UDL_CSS_STRING',
                    'SCE_UDL_CSL_STRING',
                    'SCE_UDL_SSL_STRING',
                    'SCE_UDL_TPL_STRING',
                    ),
        'comments': ('SCE_UDL_M_COMMENT',
                     'SCE_UDL_CSS_COMMENT',
                     'SCE_UDL_CSL_COMMENT',
                     'SCE_UDL_CSL_COMMENTBLOCK',
                     'SCE_UDL_SSL_COMMENT',
                     'SCE_UDL_SSL_COMMENTBLOCK',
                     'SCE_UDL_TPL_COMMENT',
                     'SCE_UDL_TPL_COMMENTBLOCK',
                     ),
        'keywords': ('SCE_UDL_CSS_WORD',
                     'SCE_UDL_CSL_WORD',
                     'SCE_UDL_SSL_WORD',
                     'SCE_UDL_TPL_WORD',
                    ),
        'operators': ('SCE_UDL_M_OPERATOR',
                      'SCE_UDL_CSS_OPERATOR',
                      'SCE_UDL_CSL_OPERATOR',
                      'SCE_UDL_SSL_OPERATOR',
                      'SCE_UDL_TPL_OPERATOR',
                      ),
        'variables': ('SCE_UDL_SSL_VARIABLE',
                      'SCE_UDL_TPL_VARIABLE',
                      ),
        'regex': ('SCE_UDL_CSL_REGEX',
                  'SCE_UDL_SSL_REGEX',
                  ),
        'pi content': ('SCE_UDL_M_PI',
                       ),
        'tags': ('SCE_UDL_M_STAGO',
                 'SCE_UDL_M_TAGNAME',
                 'SCE_UDL_M_STAGC',
                 'SCE_UDL_M_EMP_TAGC',
                 'SCE_UDL_M_ETAGO',
                 'SCE_UDL_M_ETAGC',
                 ),
        'attribute value': ('SCE_UDL_M_STRING',),
        'attribute name': ('SCE_UDL_M_ATTRNAME',),
        'entity references': ('SCE_UDL_M_ENTITY',
                              ),
        'cdata' : ('SCE_UDL_M_CDATA', )
    },
    'Text': {},
    'Perl': {
        'default':('SCE_PL_DEFAULT',
                   'SCE_PL_UNKNOWN_FIELD',
                   'SCE_PL_SUB_ARGS',),
        'errors': ('SCE_PL_ERROR',),
        'comments': ('SCE_PL_COMMENTLINE',
                     'SCE_PL_POD'),
        'numbers': ('SCE_PL_NUMBER',),
        'keywords': ('SCE_PL_WORD',),
        'strings': ('SCE_PL_STRING',
                    'SCE_PL_CHARACTER',
                    'SCE_PL_STRING_Q',
                    'SCE_PL_STRING_QQ',
                    'SCE_PL_STRING_QX',
                    'SCE_PL_STRING_QR',
                    'SCE_PL_STRING_QW',
                    'SCE_PL_LONGQUOTE',
                    'SCE_PL_FORMAT',
                    ),
        'identifiers': ('SCE_PL_IDENTIFIER',),
        'operators': ('SCE_PL_OPERATOR',
                      'SCE_PL_BACKTICKS',
                      'SCE_PL_VARIABLE_INDEXER'),
        'functions': ('SCE_PL_SUB',),
        'here documents': ('SCE_PL_HERE_DELIM',
                           'SCE_PL_HERE_Q',
                           'SCE_PL_HERE_QQ',
                           'SCE_PL_HERE_QX'),
        'arrays': ('SCE_PL_ARRAY',),
        'hashes': ('SCE_PL_HASH',),
        'symbol tables': ('SCE_PL_SYMBOLTABLE',),
        'regex': ('SCE_PL_REGEX',
                  'SCE_PL_REGSUBST',),
        'preprocessor': ('SCE_PL_PREPROCESSOR',),
        'variables': ('SCE_PL_SCALAR',),
        'data sections': ('SCE_PL_DATASECTION',),
        'stdin': ('SCE_PL_STDIN',),
        'stdout': ('SCE_PL_STDOUT',),
        'stderr' : ('SCE_PL_STDERR',),
    },
    'Properties': {
        'default': ('SCE_PROPS_DEFAULT',),
        'comments': ('SCE_PROPS_COMMENT',),
        'sections': ('SCE_PROPS_SECTION',),
        'assignments': ('SCE_PROPS_ASSIGNMENT',),
        'defvals': ('SCE_PROPS_DEFVAL',),
    },
    'Batch': {
        'default': ('SCE_BAT_DEFAULT',),
        'comments': ('SCE_BAT_COMMENT',),
        'keywords': ('SCE_BAT_WORD',),
        'functions': ('SCE_BAT_LABEL',),
        'hide': ('SCE_BAT_HIDE',),
        'commands': ('SCE_BAT_COMMAND',),
        'identifiers': ('SCE_BAT_IDENTIFIER',),
        'operators': ('SCE_BAT_OPERATOR',),
    },
    'CSS': {
        'default': ('SCE_CSS_DEFAULT',),
        'tags': ('SCE_CSS_TAG',
                 'SCE_CSS_PSEUDOELEMENT',
                 'SCE_CSS_EXTENDED_PSEUDOELEMENT',
                 ),
        'classes': ('SCE_CSS_CLASS',
                    'SCE_CSS_PSEUDOCLASS',
                    'SCE_CSS_EXTENDED_PSEUDOCLASS',
                    'SCE_CSS_UNKNOWN_PSEUDOCLASS',
                    ),
        'operators': ('SCE_CSS_OPERATOR',),
        'identifiers': ('SCE_CSS_IDENTIFIER',
                        'SCE_CSS_UNKNOWN_IDENTIFIER',
                        'SCE_CSS_IDENTIFIER2',
                        'SCE_CSS_IDENTIFIER3',
                        'SCE_CSS_EXTENDED_IDENTIFIER',
                        ),
        'values': ('SCE_CSS_VALUE',),
        'comments': ('SCE_CSS_COMMENT',),
        'ids': ('SCE_CSS_ID',),
        'important': ('SCE_CSS_IMPORTANT',),
        'directives': ('SCE_CSS_DIRECTIVE',),
        'strings': ('SCE_CSS_DOUBLESTRING', 'SCE_CSS_SINGLESTRING',),
        'numbers': ('SCE_CSS_NUMBER',),
        'stringeol': ('SCE_CSS_STRINGEOL',),
        'attribute name': ('SCE_CSS_ATTRIBUTE',),
    },
    'Makefile': {
        'default': ('SCE_MAKE_DEFAULT',),
        'comments': ('SCE_MAKE_COMMENT',),
        'preprocessor': ('SCE_MAKE_PREPROCESSOR',),
        'identifiers': ('SCE_MAKE_IDENTIFIER',),
        'operators': ('SCE_MAKE_OPERATOR',),
        'targets': ('SCE_MAKE_TARGET',),
        'stringeol': ('SCE_MAKE_IDEOL',),
        },
    'Diff': {
        'default': ('SCE_DIFF_DEFAULT',),
        'comments': ('SCE_DIFF_COMMENT',),
        'commands': ('SCE_DIFF_COMMAND',),
        'chunkheader': ('SCE_DIFF_HEADER',),
        'diffline': ('SCE_DIFF_POSITION',),
        'deletionline': ('SCE_DIFF_DELETED',),
        'additionline': ('SCE_DIFF_ADDED',),
    },
    'LaTeX': {},
    'Lisp': {
        'comments': ('SCE_LISP_COMMENT',),
        'strings': ('SCE_LISP_STRING',),
        'stringeol': ('SCE_LISP_STRINGEOL',),
    },
    'Ada': {
        'default': ('SCE_ADA_DEFAULT',),
        'keywords': ('SCE_ADA_WORD',),
        'identifiers': ('SCE_ADA_IDENTIFIER',),
        'comments': ('SCE_ADA_COMMENTLINE',),
        'numbers': ('SCE_ADA_NUMBER',),
        'strings': ('SCE_ADA_CHARACTER',
                    'SCE_ADA_STRING',),
        'stringeol': ('SCE_ADA_CHARACTEREOL',
                      'SCE_ADA_STRINGEOL',),
        'illegals': ('SCE_ADA_ILLEGAL',),
        'delimiters': ('SCE_ADA_DELIMITER',),
        'labels': ('SCE_ADA_LABEL',),
        },
    'Apache': {
        'directives': ('SCE_CONF_DIRECTIVE',),
        'parameters': ('SCE_CONF_PARAMETER',),
        'extensions': ('SCE_CONF_EXTENSION',),
        'default': ('SCE_CONF_DEFAULT',),
        'numbers': ('SCE_CONF_NUMBER',),
        'identifiers': ('SCE_CONF_IDENTIFIER',),
        'strings': ('SCE_CONF_STRING',),
        'comments': ('SCE_CONF_COMMENT',),
        'ip_addresses': ('SCE_CONF_IP',),
        },
    'Fortran 77': {
        'comments': ('SCE_F_COMMENT',),
        'default': ('SCE_F_DEFAULT',),
        'keywords': ('SCE_F_WORD',
                     'SCE_F_WORD2',
                     'SCE_F_WORD3',
                     ),
        'preprocessor': ('SCE_F_PREPROCESSOR',),
        'identifiers': ('SCE_F_IDENTIFIER',),
        'operators': ('SCE_F_OPERATOR',
                      'SCE_F_OPERATOR2',
                      ),
        'numbers': ('SCE_F_NUMBER',),
        'strings': ('SCE_F_STRING1',
                    'SCE_F_STRING2',
                    ),
        'stringeol': ('SCE_F_STRINGEOL',),
        'labels': ('SCE_F_LABEL',),
        'delimiters': ('SCE_F_CONTINUATION',),
    },
    'SQL': {
        'comments': ('SCE_C_COMMENTLINE',
                     'SCE_C_COMMENT',
                     ),
    },
    'Eiffel': {
        'comments': ('SCE_EIFFEL_COMMENTLINE',),
        'default': ('SCE_EIFFEL_DEFAULT',),
        'keywords': ('SCE_EIFFEL_WORD',),
        'identifiers': ('SCE_EIFFEL_IDENTIFIER',),
        'operators': ('SCE_EIFFEL_OPERATOR',
                      ),
        'numbers': ('SCE_EIFFEL_NUMBER',),
        'strings': ('SCE_EIFFEL_STRING',
                    'SCE_EIFFEL_CHARACTER',
                    ),
        'stringeol': ('SCE_EIFFEL_STRINGEOL',),
    },
    'Baan': {
        'comments': ('SCE_BAAN_COMMENT', 'SCE_BAAN_COMMENTDOC'),
    },
    'nnCrontab': {
        'comments': ('SCE_NNCRONTAB_COMMENT',),
    },
    'Matlab': {
        'comments': ('SCE_MATLAB_COMMENT',),
    },
    'Bullant': {
        'comments': ('SCE_C_COMMENTLINE', 'SCE_C_COMMENT'),
    },
    'Errors': {
        'Default': ('SCE_ERR_DEFAULT',),
        'Error lines':
            (# 'SCE_ERR_CMD', # too brittle - see http://bugs.activestate.com/show_bug.cgi?id=26605
             'SCE_ERR_PYTHON',
             # 'SCE_ERR_GCC', # too brittle - see http://bugs.activestate.com/show_bug.cgi?id=26605
             'SCE_ERR_MS',
             'SCE_ERR_CTAG',
             'SCE_ERR_ELF',
             'SCE_ERR_NET',
             'SCE_ERR_PERL',
             'SCE_ERR_LUA',
             'SCE_ERR_BORLAND',
             'SCE_ERR_IFC',
             'SCE_ERR_PHP')
    },
    'Ruby': {
        'default':('SCE_RB_DEFAULT',),
        'errors': ('SCE_RB_ERROR',),
        'comments': ('SCE_RB_COMMENTLINE',
                     'SCE_RB_POD'),
        'numbers': ('SCE_RB_NUMBER',),
        'keywords': ('SCE_RB_WORD',
                     'SCE_RB_WORD_DEMOTED'
                     ),
        'strings': ('SCE_RB_STRING',
                    'SCE_RB_CHARACTER',
                    'SCE_RB_STRING_Q',
                    'SCE_RB_STRING_QQ',
                    'SCE_RB_STRING_QX',
                    'SCE_RB_STRING_QR',
                    'SCE_RB_STRING_QW',
                    'SCE_RB_BACKTICKS',
                    ),
        'classes': ('SCE_RB_CLASSNAME',),
        'modules': ('SCE_RB_MODULE_NAME',),
        'functions': ('SCE_RB_DEFNAME',),
        'identifiers': ('SCE_RB_IDENTIFIER',),
        'operators': ('SCE_RB_OPERATOR',),
        'global variables' : ('SCE_RB_GLOBAL',),
        'class variables' : ('SCE_RB_CLASS_VAR',),
        'instance variables' : ('SCE_RB_INSTANCE_VAR',),
        'here documents': ('SCE_RB_HERE_DELIM',
                           'SCE_RB_HERE_Q',
                           'SCE_RB_HERE_QQ',
                           'SCE_RB_HERE_QX'),
        'symbols': ('SCE_RB_SYMBOL',),
        'regex': ('SCE_RB_REGEX',),
        'data sections': ('SCE_RB_DATASECTION',),
        'stdin': ('SCE_RB_STDIN',),
        'stdout': ('SCE_RB_STDOUT',),
        'stderr' : ('SCE_RB_STDERR',),
    },
}

#Derivatives (Shared lexers)
StateMap['CoffeeScript'] = StateMap['JavaScript'] = StateMap['C++'].copy()
StateMap['Node.js'] = StateMap['JavaScript'].copy()
StateMap['JSON'] = StateMap['C++'].copy()
StateMap['Java'] = StateMap['C++'].copy()
StateMap['C#'] = StateMap['C++'].copy()
StateMap['HLSL'] = StateMap['C++'].copy()
StateMap['IDL'] = StateMap['C++'].copy()
StateMap['VBScript'] = StateMap['VisualBasic'].copy()
StateMap['Fortran'] = StateMap['Fortran 77'].copy()
StateMap['Python3'] = StateMap['Python'].copy()
StateMap['SCSS'] = StateMap['CSS'].copy()
StateMap['Less'] = StateMap['CSS'].copy()

SharedStates = {
    'bracebad' : ('STYLE_BRACEBAD',),
    'bracehighlight' : ('STYLE_BRACELIGHT',),
    'control characters' : ('STYLE_CONTROLCHAR',),
    'linenumbers': ('STYLE_LINENUMBER',),
    'indent guides': ('STYLE_INDENTGUIDE',),
}

# A map of the indicator name to the koILintResult/SciMoz indicator value used.
IndicatorNameMap = {
    'linter_error': 'DECORATOR_ERROR',
    'linter_warning': 'DECORATOR_WARNING',
    'soft_characters': 'DECORATOR_SOFT_CHAR',
    'tabstop_current': 'DECORATOR_TABSTOP_TSC',
    'tabstop_pending': 'DECORATOR_TABSTOP_TS1',
    'find_highlighting': 'DECORATOR_FIND_HIGHLIGHT',
    'tag_matching': 'DECORATOR_TAG_MATCH_HIGHLIGHT',
}

def addSharedStyles(langMap):
    langMap.update(SharedStates)

for languageName in StateMap:
    addSharedStyles(StateMap[languageName])

def addNewUDLLanguage(languageName):
    if languageName not in StateMap:
        StateMap[languageName] = StateMap['UDL'].copy()
        addSharedStyles(StateMap[languageName])

