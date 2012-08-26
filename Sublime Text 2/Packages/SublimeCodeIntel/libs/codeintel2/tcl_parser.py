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

"""Tcl parsing support for codeintel/tclcile.py"""

import string
import sys
import re
import textwrap

from SilverCity import ScintillaConstants
from codeintel2 import tcl_lexer
from codeintel2 import shared_lexer
from codeintel2 import shared_parser
from codeintel2.parser_data import Name_LineNum, VarInfo, Node, ClassNode, \
     FileNode, ArgNode, MethodNode, ModuleNode, VariableNode, BlockNode, \
     update_collection
from codeintel2.parser_data import VAR_KIND_GLOBAL, VAR_KIND_LOCAL

class TclClassifier(shared_parser.CommonClassifier):
    _quote_patterns = {ScintillaConstants.SCE_TCL_STRING : re.compile('^\"(.*)\"$'),
                       ScintillaConstants.SCE_TCL_DEFAULT : re.compile('^.(.*).$'),
                       }

    def get_builtin_type(self, tok, callback):
        if self.is_number(tok):
            numval = tok.text
            if numval.find(".") >= 0:
                return "Float"
            else:
                return "Fixnum" 
        elif self.is_string(tok):
            return "String"
        return None
        
    def is_any_operator(self, tok):
        return tok.style == ScintillaConstants.SCE_TCL_OPERATOR

    def is_comment(self, tok):
        return tok.style == ScintillaConstants.SCE_TCL_COMMENT

    def is_comment_structured(self, tok, callback):
        return False

    def is_identifier(self, tok, allow_keywords=False):
        return (tok.style == ScintillaConstants.SCE_TCL_IDENTIFIER or
            (allow_keywords and
             tok.style == ScintillaConstants.SCE_TCL_WORD))

    def is_interpolating_string(self, tok, callback):
        return tok.style == ScintillaConstants.SCE_TCL_STRING
    
    def is_keyword(self, tok, target):
        return tok.style == ScintillaConstants.SCE_TCL_WORD and tok.text == target

    def is_number(self, tok):
        return tok.style == ScintillaConstants.SCE_TCL_NUMBER

    def is_operator(self, tok, target):
        return tok.style == ScintillaConstants.SCE_TCL_OPERATOR and tok.text == target

    def is_string(self, tok):
        return tok.style in [ScintillaConstants.SCE_TCL_STRING,
                             ScintillaConstants.SCE_TCL_CHARACTER,
                             ScintillaConstants.SCE_TCL_LITERAL
                             ]

    def is_symbol(self, tok):
        return False

    def quote_patterns_cb(self, tok):
        tval = tok.text
        if tval[0] == '"':
            return self._quote_patterns[ScintillaConstants.SCE_TCL_STRING]
        elif tval[0] == '\'':
            return self._quote_patterns[ScintillaConstants.SCE_TCL_CHARACTER]
        else:
            return self._quote_patterns[ScintillaConstants.SCE_TCL_DEFAULT] # Fallback

    # Accessors for where we'd rather work with a style than call a predicate fn

    @property
    def style_identifier(self):
        return ScintillaConstants.SCE_TCL_IDENTIFIER
    
    @property
    def style_operator(self):
        return ScintillaConstants.SCE_TCL_OPERATOR

    @property
    def style_word(self):
        return ScintillaConstants.SCE_TCL_WORD

lang_specific_classes = {"Tcl": TclClassifier,
                         "AOL" : shared_parser.UDLClassifier}

leading_hash_re = re.compile(r'^\s*\#+\s*')
mostly_dashes = re.compile(r'\s*-{10}')
spaces_and_braces_re = re.compile(r'\s*\}\s*$')

def remove_hashes(lines):
    len1 = len(lines)
    if len1 == 0:
        return []
    set1 = [leading_hash_re.sub("", s) for s in lines]
    if len1 > 0 and mostly_dashes.match(set1[0]):
        del set1[0]
    if len1 > 1 and mostly_dashes.match(set1[-1]):
        del set1[-1]
    return set1

# Parse Tcl code
class Parser:
    def __init__(self, tokenizer, lang):
        self.tokenizer = tokenizer
        self.block_stack = []
        self.tree = FileNode()
        self.curr_node = self.tree
        self.classifier = lang_specific_classes[lang]()
        self.containers = {VAR_KIND_GLOBAL : [self.tree.global_vars],
                           VAR_KIND_LOCAL : [self.tree.local_vars]} #locals
        
    def _get_fully_qualified_braced_name(self, start_line, start_column):
        brace_count = 1
        name_parts = []
        while 1:
            tok = self.tokenizer.get_next_token(skip_ws=0)
            if tok.style == shared_lexer.EOF_STYLE:
                break
            elif self.classifier.is_any_operator(tok):
                if tok.text == "{":
                    brace_count += 1
                elif tok.text == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        break
            if tok.start_line > start_line or tok.start_column > start_column:
                name_parts.append(" ")
            start_column = tok.end_column + 1
            start_line = tok.start_line
            name_parts.append(tok.text) #XXX backslashes?
        return "".join(name_parts)

    def get_fully_qualified_name(self):
        tok = self.tokenizer.get_next_token()
        if tok.style == shared_lexer.EOF_STYLE:
            return (None, None)
        line_start = tok.start_line
        if self.classifier.is_operator(tok, "{"):
            return (self._get_fully_qualified_braced_name(line_start, tok.end_column + 1), line_start)
        name_start = tok.text
        # Watch out if it starts with a "::"
        if name_start == "::":
            col = tok.end_column + 1
            tok = self.tokenizer.get_next_token()
            if tok.start_column != col or not self.classifier.is_identifier(tok):
                self.tokenizer.put_back(tok)
                return (name_start, line_start)
            name_start += tok.text
            
        col = tok.end_column + 1
        while 1:
            # Collect operator-type methods
            tok = self.tokenizer.get_next_token()
            if tok.start_column == col and self.classifier.is_operator(tok, "::"):
                name_start += tok.text
                col += 2
            else:
                self.tokenizer.put_back(tok)
                break
            
            tok = self.tokenizer.get_next_token()
            if tok.start_column == col and self.classifier.is_identifier(tok, True):
                name_start += tok.text                
                col = tok.end_column + 1
            else:
                self.tokenizer.put_back(tok)
                break
        return (name_start, line_start)  
           
    def parse(self):
        while self.parse_aux(self.tree):
            pass
        return self.tree
        
    def get_parsing_objects(self, kwd):
        return {
            "namespace": [ModuleNode, self.parse_aux],
            "proc" : [MethodNode, self.parse_method]
        }.get(kwd, [None, None])
        
    def _parse_name_list(self):
        vars = []
        while True:
            tok = self.tokenizer.get_next_token()
            if tok.style == shared_lexer.EOF_STYLE or \
                          self.classifier.is_operator(tok, "}"):
                break
            if self.classifier.is_identifier(tok):
                vars.append(tok.text)
        return vars
    
    def parse_method(self, curr_node):
        # Syntax: proc name { args } { body }
        tok = self.tokenizer.get_next_token()
        if self.classifier.is_operator(tok, "{"):
            # Standard, keep going
            do_regular_args = True
        elif self.classifier.is_identifier(tok):
            # Assume it's the one arg
            if tok.text == "args":
                curr_node.add_arg(tok.text, None, "varargs")
            else:
                curr_node.add_arg(tok.text)
            curr_node.signature = "%s {%s}" % (curr_node.name, tok.text)
            do_regular_args = False
        else:
            self.tokenizer.put_back(tok)
            return
        
        if do_regular_args:
            braceCount = 1
            init_indentation = curr_node.indentation
            tok_count = 0
            tok_lim = 1000
            self.tokenizer.start_sig()
            argStart = True
            while 1:
                tok = self.tokenizer.get_next_token()
                if self.classifier.is_any_operator(tok):
                    argStart = False
                    tval = tok.text
                    if tval == "{":
                        braceCount += 1
                        if braceCount == 2:
                            argStart = True
                    elif tval == "}":
                        braceCount -= 1
                        if braceCount <= 0:
                            break
                        elif braceCount == 1:
                            argStart = True
                elif argStart:
                    if braceCount == 2: # Wait for a } to get next arg.
                        argStart = False
                    if self.classifier.is_identifier(tok, True):
                        if tok.text == "args" and braceCount == 1:
                            # We need to peek at the next token
                            tok2 = self.tokenizer.get_next_token()
                            if self.classifier.is_operator(tok2, "}"):
                                curr_node.add_arg(tok.text, None, "varargs")
                                break
                            else:
                                self.tokenizer.put_back(tok2)
                        curr_node.add_arg(tok.text)
                tok_count += 1
                if tok_count > tok_lim and tok.start_column < init_indentation:
                    break
            
            self.tokenizer.stop_sig()
            #XXX Check white-space in the sig
            # We don't know we've hit the end of the sig until we hit
            # that final "}", so we need to pull it out.
            curr_node.signature = "%s {%s}" % (curr_node.name,
                                               spaces_and_braces_re.sub('', self.tokenizer.get_sig()))
        
        # Now get the body
        tok = self.tokenizer.get_next_token()
        if not self.classifier.is_operator(tok, "{"):
            # Give up
            self.tokenizer.put_back(tok)
            return
        braceCount = 1
        self.parse_aux(curr_node, 1) # Count the brace we just saw.
    # end parse_method

    def parse_assignment(self, tok_text, start_line, isLocal=True):
        # Don't bother trying to type it yet.
        # Figure out whether we're in a proc or not

        if isLocal:
            collectionA = self.containers[VAR_KIND_LOCAL]
        else:
            collectionA = self.containers[VAR_KIND_GLOBAL]

        if len(collectionA) == 0 or collectionA[-1] is None:
            return
        possibleType = self._finishVarAssignment(collectionA, tok_text, start_line)
        update_collection(collectionA[-1], tok_text, start_line, possibleType)
        
    def _finishVarAssignment(self, collectionA, var_name, start_line):
        #XXX Add type info
        return None
    
    def parse_aux(self, curr_node, braceCount=0):
        init_indentation = curr_node.indentation
        tok_count = 0
        tok_lim = 1000
        cmdStart = True
        curr_globals = {}
        while 1:
            tok = self.tokenizer.get_next_token()
            if tok.style == shared_lexer.EOF_STYLE:
                break
            # style, text, start_column, start_line, end_column, end_line = tok
            style, text = tok.style, tok.text
            if style == self.classifier.style_word and \
               (cmdStart or tok.start_column == self.tokenizer.get_curr_indentation()):
                cmdStart = False
                if text in ["namespace", "proc"]:
                    curr_indent = self.tokenizer.get_curr_indentation()
                    if text == "namespace":
                        tok1 = self.tokenizer.get_next_token()
                        if not (self.classifier.is_identifier(tok1, True) and tok1.text == "eval"):
                            continue
                    node_class, node_parser = self.get_parsing_objects(text)
                    if node_class is None:
                        sys.stderr.write("Couldn't get parsing objects for type %s\n" % text)
                        break
                    
                    # Get the comments before further parsing.
                    comment_lines = remove_hashes(self.tokenizer.curr_comment())
                    nm_token = self.get_fully_qualified_name()
                    fqname = nm_token[0]
                    if not fqname:
                        break                    
                    # Handle only local names for now
                    if fqname.startswith("::") and  text == "namespace":
                            fqname = fqname[2:]

                    new_node = node_class(fqname, tok.start_line)
                    new_node.doc_lines = comment_lines
                    new_node.indentation = curr_indent
                    self.block_stack.append(new_node)
                    curr_node.append_node(new_node)

                    # Push new containers on the symbol table
                    self.containers[VAR_KIND_LOCAL].append(new_node.local_vars)

                    node_parser(new_node)  # Has self bound to it
                    self.block_stack.pop()
                    self.containers[VAR_KIND_LOCAL].pop()

                    # Clear any comment that's hanging around
                    self.tokenizer.clear_comments()

                elif text == "package":
                    tok1 = self.tokenizer.get_next_token()
                    if self.classifier.is_identifier(tok1, True):
                        if tok1.text == "require":
                            tok2 = self.tokenizer.get_next_token()
                            if self.classifier.is_identifier(tok2, True) and tok2.text != "Tcl":
                                curr_node.imports.append(Name_LineNum(tok2.text, tok.start_line))
                elif text == "global":
                    # XXX: all tokens following 'global' should be declared vars
                    tok = self.tokenizer.get_next_token()
                    if self.classifier.is_identifier(tok, True):
                        curr_globals[tok.text] = None
                elif text == "set":
                    # XXX: Needs to handle lappend, append, incr, variable
                    # XXX: possibly dict set, array set, upvar, lassign,
                    # XXX: foreach, regsub (non-inline)
                    tok = self.tokenizer.get_next_token()
                    if self.classifier.is_identifier(tok, True):
                        if curr_globals.has_key(tok.text):
                            pass
                        else:
                            self.parse_assignment(tok.text, tok.start_line, isinstance(curr_node, MethodNode))
                elif text == "lassign":
                    tok = self.tokenizer.get_next_token()
                    if self.classifier.is_operator(tok, "{"):
                        start_line = tok.start_line;
                        isLocal = isinstance(curr_node, MethodNode)
                        if isLocal:
                            collectionA = self.containers[VAR_KIND_LOCAL]
                        else:
                            collectionA = self.containers[VAR_KIND_GLOBAL]
                        vars = self._parse_name_list()
                        for v in vars:
                            update_collection(collectionA[-1], v, start_line) 
            elif self.classifier.is_any_operator(tok):
                cmdStart = False
                if text == "{":
                    braceCount += 1
                elif text == "}":
                    braceCount -= 1
                    if braceCount <= 0:
                        break
                elif text in (";", "["):
                    cmdStart = True
            else:
                cmdStart = False
            # Sanity check to make sure we haven't gone too far.
            tok_count += 1
            if tok_count > tok_lim and tok.start_column < init_indentation:
                break
        # end while
        curr_node.set_line_end_num(self.tokenizer.curr_line_no())
        return tok.style != shared_lexer.EOF_STYLE
    # end parse_aux()
        

# end class Parser

if __name__ == "__main__":
    if len(sys.argv) == 1:
        sample_code = tcl_lexer.provide_sample_code();
        fs = None
    elif sys.argv[1] == "-":
        fs = sys.stdin
        closefs = False
    else:
        fs = open(sys.argv[1], "r")
        closefs = True
    if fs is not None:
        sample_code = shared_lexer.read_and_detab(fs, closefs)
        # fs comes back closed
    tokenizer = tcl_lexer.TclLexer(sample_code)
    parser = Parser(tokenizer, "Tcl")
    tree = parser.parse()
    print "Analyze the parse tree"
    tree.dump()
