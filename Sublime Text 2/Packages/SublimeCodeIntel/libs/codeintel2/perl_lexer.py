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
Perl lexing support for codeintel/perlcile.py

Get all the lexed tokens from SilverCity, and then return them
on demand to the caller (usually a Perl pseudo-parser).

Usage:
import perl_lexer
lexer = lex_wrapper.Lexer(code)
while 1:
    tok = lexer.get_next_token()
    if tok[0] == EOF_STYLE:
        break;
    # tok is an array of (style, text, start-col, start-line, end-col, end-line)
    # column and line numbers are all zero-based.
"""

import copy
import re
import sys
import string

import SilverCity
from SilverCity import Perl, ScintillaConstants
import shared_lexer
from shared_lexer import EOF_STYLE

pod_markings = re.compile('^=(?:head|item|cut)', re.M)

class PerlLexerClassifier:
    """ This classifier is similar to the parser-level classifier, but
    it works on the SilverCity "raw" tokens as opposed to the
    tokens that get created by the lexer layer.  There should be some
    folding though."""    

    def is_comment(self, ttype):
        return ttype in (ScintillaConstants.SCE_PL_COMMENTLINE,
                         ScintillaConstants.SCE_PL_POD)
        
    @property
    def style_comment(self):
        return ScintillaConstants.SCE_PL_COMMENTLINE
        
    @property
    def style_default(self):
        return ScintillaConstants.SCE_PL_DEFAULT

    @property
    def style_operator(self):
        return ScintillaConstants.SCE_PL_OPERATOR


class _CommonLexer(shared_lexer.Lexer):
    def __init__(self):
        shared_lexer.Lexer.__init__(self)
        self.q = []
        self.multi_char_ops = self.build_dict('-> ++ -- ** =~ !~ << >> <= >= == != <=> && || ... .. => <<= >>= &&= ||= ~*= /= %= += -= .= &= |= ^= ::')

class PerlLexer(_CommonLexer):
    def __init__(self, code, provide_full_docs=True):
        _CommonLexer.__init__(self)
        self.q = []
        self.classifier = PerlLexerClassifier()
        self._provide_full_docs = provide_full_docs
        Perl.PerlLexer().tokenize_by_style(code, self._fix_token_list)
        # self._fix_token_list(q_tmp) # Updates self.q in place
        self.string_types = [ScintillaConstants.SCE_PL_STRING,
                         ScintillaConstants.SCE_PL_CHARACTER,
                         ScintillaConstants.SCE_PL_HERE_Q,
                         ScintillaConstants.SCE_PL_HERE_QQ,
                         ScintillaConstants.SCE_PL_STRING_QW,
                         ScintillaConstants.SCE_PL_STRING_Q,
                         ScintillaConstants.SCE_PL_STRING_QQ,
                         ScintillaConstants.SCE_PL_STRING_QX
                         ]
        
    def _fix_token_list(self, **tok):
        """ SilverCity doesn't know much about Perl, and breaks in two ways:
        1. It doesn't know how to separate sequences of characters into
        separate tokens.
        2. It doesn't know how to map DATASECTIONs into POD sequences.
        
        It's easier to do this once before processing tokens individually.
        
        This should all be done in silvercity.  Doing this has leaked the
        whole silvercity abstraction into this module, and it doesn't
        belong here.  This routine works with SilverCity tokens, not
        shared_lexer Tokens.
        """
        if tok['start_column'] > shared_lexer.MAX_REASONABLE_LIMIT:
            return
        ttype = tok['style']
        tval = tok['text']
        if ttype in (ScintillaConstants.SCE_PL_OPERATOR,
                     ScintillaConstants.SCE_PL_VARIABLE_INDEXER) and len(tok['text']) > 1:
            # Scineplex doesn't know how to split some sequences of styled characters
            # into syntactically different tokens, so we do it here.
            # A sequence of characters might need to be split into more than one token.
            # Push all but the last token on the pending block.
            self.append_split_tokens(tok, self.multi_char_ops, self.q)
        elif ttype == ScintillaConstants.SCE_PL_IDENTIFIER:
            tok['text'] = tok['text'].strip()
            self.q.append(tok)
        elif (not self._provide_full_docs) and \
                ttype in (ScintillaConstants.SCE_PL_DATASECTION,
                          ScintillaConstants.SCE_PL_POD):
            pass
        elif ttype == ScintillaConstants.SCE_PL_DATASECTION:
            if pod_markings.search(tval):
                # putback (KWD package), (ID main), (OP ;), (POD this)
                col = tok['start_column']
                for new_vals in ((ScintillaConstants.SCE_PL_WORD, "package"),
                                 (ScintillaConstants.SCE_PL_IDENTIFIER, "main"),
                                 (ScintillaConstants.SCE_PL_OPERATOR, ";")):
                    new_type, new_text = new_vals
                    new_tok = copy.copy(tok)
                    new_tok['text'] = new_text
                    new_tok['style'] = new_type
                    new_tok['start_column'] = col
                    new_tok['end_column'] = col + len(new_text) - 1
                    col = new_tok['end_column'] + 1
                    self.q.append(new_tok)
                tok['style'] = ScintillaConstants.SCE_PL_POD
                tok['text'] = tval;
                tok['start_column'] = col
                if tok['start_line'] == tok['end_line']:
                    tok['end_column'] = tok['start_line'] + len(tok['text']) - 1
                self.q.append(tok)
            else:
                # End of the queue => EOF
                pass
        else:
            self.q.append(tok)

class PerlMultiLangLexer(_CommonLexer):
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
        """See perl_lexer.py for details on what this routine does."""
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
        # See comment in RubyMultiLangLexer._fix_token_list
        # on why we probably don't need this code.
        #elif self.is_udl_tpl_family(ttype):
        #    self._contains_ssl = True

    def get_csl_tokens(self):
        return self.csl_tokens

    def has_perl_code(self):
        return self._contains_ssl

def provide_sample_code():
    return r"""use LWP::UserAgent;

# full-line comment
# comment at start of line
 # comment at col 1
  # comment at col 2

{
package Foo;

sub new {
   my ($class, %args) = @_;
   my $self = {count => 0, list = [] };
   bless $self, (ref $class || $class);
}

sub m {
    my ($self, $arg) = @_;
    push @{$self->{list}}, $arg;
    $self->{count} += 1;
    $arg;
}

sub no_paren {
  my ($a, $b,
     $c) = $_;
  print "blah";
}

sub our_generate { my $self = shift; my $file_info = shift;
  $self->{info} = info;
  $self->{files} = [];
  $self->{classes} = [];
  $self->{hyperlinks} = {};
  #comment on what test_fn does
  # more...

  sub test_fn {
        my ($a, $b, $c, $d, $e) = @_;
        $b |= 'val1';
        $c |= f(3);
       print "nothing\n";   # end-of-line comment
       print qq(percent string\n);
    }

   }
   }
"""


if __name__ == "__main__":
    shared_lexer.main(sys.argv, provide_sample_code, PerlLexer)
