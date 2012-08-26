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
#
# Contributors:
#   Eric Promislow (EricP@ActiveState.com)

"""
Ruby lexing support for codeintel/rubycile.py

Get all the lexed tokens from SilverCity, and then return them
on demand to the caller (usually a Ruby pseudo-parser).

Usage:
import ruby_lexer
lexer = ruby_lexer.Lexer(code)
while 1:
    tok = lexer.get_next_token()
    if tok[0] == EOF_STYLE:
        break;
    # tok is an array of (style, text, start-col, start-line, end-col, end-line)
    # column and line numbers are all zero-based.
"""

import re
import sys
import string

# import SilverCity
from SilverCity import Ruby, ScintillaConstants
import shared_lexer
from shared_lexer import EOF_STYLE

class RubyLexerClassifier:
    """ This classifier is similar to the parser-level classifier, but
    it works on the SilverCity "raw" tokens as opposed to the
    tokens that get created by the lexer layer.  There should be some
    folding though."""

    def is_comment(self, ttype):
        return ttype in (ScintillaConstants.SCE_RB_COMMENTLINE,
                         ScintillaConstants.SCE_RB_POD)

    @property
    def style_comment(self):
        return ScintillaConstants.SCE_RB_COMMENTLINE
        
    @property
    def style_default(self):
        return ScintillaConstants.SCE_RB_DEFAULT

    @property
    def style_operator(self):
        return ScintillaConstants.SCE_RB_OPERATOR

class _CommonLexer(shared_lexer.Lexer):
    def __init__(self):
        shared_lexer.Lexer.__init__(self)
        self.q = []
        self.multi_char_ops = self.build_dict('!= !~ && ** :: <= << == => =~ >> ||')    

class RubyLexer(_CommonLexer):
    def __init__(self, code):
        _CommonLexer.__init__(self)
        self.classifier = RubyLexerClassifier()
        Ruby.RubyLexer().tokenize_by_style(code, self._fix_token_list)
        self.string_types = [ScintillaConstants.SCE_RB_STRING,
                ScintillaConstants.SCE_RB_CHARACTER,
                ScintillaConstants.SCE_RB_STRING_Q,
                ScintillaConstants.SCE_RB_STRING_QQ,
                ScintillaConstants.SCE_RB_STRING_QX,
                ScintillaConstants.SCE_RB_STRING_QR,
                ScintillaConstants.SCE_RB_STRING_QW
                ]
        
    def _fix_token_list(self, **tok):
        """See perl_lexer.py for details on what this routine does."""
        if tok['style'] == ScintillaConstants.SCE_RB_OPERATOR and len(tok['text']) > 1:
            self.append_split_tokens(tok, self.multi_char_ops, self.q)
        else:
            self.q.append(tok)

class RubyMultiLangLexer(_CommonLexer):
    def __init__(self, token_source):
        _CommonLexer.__init__(self)
        self.csl_tokens = []
        # http://www.mozilla.org/js/language/grammar14.html
        self.js_multi_char_ops = self.build_dict('++ -- << >> >>> <= >= == != === !== && || *= /= %= += -= <<= >>= >>>= &= ^= |=')
        self.string_types = [ScintillaConstants.SCE_UDL_SSL_STRING
                ]
        self.classifier = shared_lexer.UDLLexerClassifier()
        self._contains_ssl = False
        self._build_tokens(token_source)

    def _build_tokens(self, token_source):
        while True:
            try:
                tok = token_source.next()
                self._fix_token_list(tok)
            except StopIteration:
                break
    
    def _fix_token_list(self, tok):
        """See ruby_lexer.py for details on what this routine does."""
        ttype = tok['style']
        tval = tok['text']
        if self.is_udl_csl_family(ttype):
            if ttype == ScintillaConstants.SCE_UDL_CSL_OPERATOR and len(tval) > 1:
                # Point the token splitter to the correct token queue
                self.append_split_tokens(tok, self.js_multi_char_ops,
                                         self.csl_tokens)
            else:
                self.csl_tokens.append(tok)
        elif self.is_udl_ssl_family(ttype):
            if tok['style'] == ScintillaConstants.SCE_UDL_SSL_OPERATOR and len(tok['text']) > 1:
                self.append_split_tokens(tok, self.multi_char_ops, self.q)
            else:
                self.q.append(tok)
            self._contains_ssl = True
        # The only reason to count TPL tokens is to provide RHTML/Ruby
        # triggers when "<%" or "<%=" falls at the end of the buffer,
        # as in
        # <%=lin<!>.  There will be a delay anyway between when the
        # first TPL or SSL characters are typed, and when the buffer
        # is re-ciled, so there's no need to check TPL tokens.
        #elif self.is_udl_tpl_family(ttype):
        #    self._contains_ssl = True

    def get_csl_tokens(self):
        return self.csl_tokens

    def has_ruby_code(self):
        return self._contains_ssl

def provide_sample_code():
    return r"""require 'rdoc/parsers/parse_rb.rb'

# full-line comment
# comment at start of line
 # comment at col 1
  # comment at col 2

module Generators
  class XMLGenerator < HTMLGenerator # a comment here
    def our_generate(file_info)
      @info       = info
      @files      = []
      @classes    = []
      @hyperlinks = {}
    end
    # comment on what test_fn does
    # more...

    def test_fn(a, b='val1', c=f(3), *d, &e)
       print "nothing\n"   # end-of-line comment
       print %Q(percent string\n)
    end

    def no_paren a, b, \
           c
       print "blah"
    end
  end
end
"""


if __name__ == "__main__":
    shared_lexer.main(sys.argv, provide_sample_code, RubyLexer)
