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

"""Ruby parsing support for codeintel/rubycile.py"""

import string
import sys
import re
import textwrap

from SilverCity import ScintillaConstants
from codeintel2 import ruby_lexer
from codeintel2 import shared_lexer
from codeintel2 import shared_parser
from codeintel2 import util
from codeintel2.parser_data import Name_LineNum, VarInfo, Node, ClassNode, \
     FileNode, ArgNode, MethodNode, ModuleNode, VariableNode, BlockNode, \
     update_collection
from codeintel2.parser_data import VAR_KIND_UNKNOWN, VAR_KIND_GLOBAL, \
     VAR_KIND_CLASS, VAR_KIND_CLASSVAR, VAR_KIND_INSTANCE, VAR_KIND_LOCAL, \
     VAR_KIND_ALIAS

import logging
log = logging.getLogger("ruby_parser")
#log.setLevel(logging.DEBUG)

# Parse Ruby code

_leading_hash_re = re.compile(r'^\s*\#+\s*')

class RubyCommonClassifier:
    """Mixin class containing classifier callbacks"""

    def is_symbol_cb(self, tok):
        return tok.text[0] == ":"

    # Used for stripping the quotes off a string
    _quote_patterns = {ScintillaConstants.SCE_RB_STRING : re.compile('^\"(.*)\"$'),
                       ScintillaConstants.SCE_RB_CHARACTER : re.compile('^\'(.*)\'$'),
                       ScintillaConstants.SCE_RB_STRING_QQ : re.compile('^%Q.(.*).$'),
                       ScintillaConstants.SCE_RB_STRING_Q : re.compile('^%q.(.*).$'),
                       ScintillaConstants.SCE_RB_DEFAULT : re.compile('^.(.*).$'),
                       }

    def quote_patterns_cb(self, tok):
        # Caller wants an array.
        return [self.quote_patterns_cb_aux(tok)]

    def quote_patterns_cb_aux(self, tok):
        tval = tok.text
        if tval[0] == '"':
            return self._quote_patterns[ScintillaConstants.SCE_RB_STRING]
        elif tval[0] == '\'':
            return self._quote_patterns[ScintillaConstants.SCE_RB_CHARACTER]
        elif tval.startswith("%Q"):
            return self._quote_patterns[ScintillaConstants.SCE_RB_STRING_QQ]
        elif tval.startswith("%q"):
            return self._quote_patterns[ScintillaConstants.SCE_RB_STRING_Q]
        else:
            return self._quote_patterns[ScintillaConstants.SCE_RB_DEFAULT] # Fallback


class UDLClassifier(RubyCommonClassifier, shared_parser.UDLClassifier):
    pass

class RubyClassifier(RubyCommonClassifier, shared_parser.CommonClassifier):
    """Mixin class containing classifier callbacks"""
    def __init__(self):
        self.narrowStyles = {ScintillaConstants.SCE_RB_GLOBAL : VAR_KIND_GLOBAL,
                             ScintillaConstants.SCE_RB_INSTANCE_VAR : VAR_KIND_INSTANCE,
                             ScintillaConstants.SCE_RB_CLASS_VAR : VAR_KIND_CLASSVAR}

    def get_builtin_type(self, tok, callback):
        if self.is_number(tok):
            numval = tok.text
            if numval.find(".") >= 0:
                return "Float"
            else:
                return "Fixnum" 
        elif self.is_string(tok):
            return "String"
        elif tok.style == ScintillaConstants.SCE_RB_STRING_QR:
            return "Regexp"
        elif tok.style == ScintillaConstants.SCE_RB_STRING_QW:
            return "Array"
        return None
        
    def is_any_operator(self, tok):
        return tok.style == ScintillaConstants.SCE_RB_OPERATOR

    def is_comment(self, tok):
        return tok.style in (ScintillaConstants.SCE_RB_COMMENTLINE,
                             ScintillaConstants.SCE_RB_POD)

    def is_comment_structured(self, tok, callback):
        return tok.style == ScintillaConstants.SCE_RB_POD

    def is_identifier(self, tok, allow_keywords=False):
        return (tok.style == ScintillaConstants.SCE_RB_IDENTIFIER or
            (allow_keywords and
             tok.style in [ScintillaConstants.SCE_RB_WORD,
                           ScintillaConstants.SCE_RB_WORD_DEMOTED]))

    def is_interpolating_string(self, tok, callback):
        return tok.style in [ScintillaConstants.SCE_RB_STRING,
                             ScintillaConstants.SCE_RB_REGEX,
                             ScintillaConstants.SCE_RB_HERE_QQ,
                             ScintillaConstants.SCE_RB_STRING_QQ,
                             ScintillaConstants.SCE_RB_STRING_QR,
                             ScintillaConstants.SCE_RB_STRING_QX
                             ]

    def is_keyword(self, tok, target):
        return tok.style == ScintillaConstants.SCE_RB_WORD and tok.text == target

    def is_number(self, tok):
        return tok.style == ScintillaConstants.SCE_RB_NUMBER

    def is_operator(self, tok, target):
        return tok.style == ScintillaConstants.SCE_RB_OPERATOR and tok.text == target

    def is_string(self, tok):
        return tok.style in [ScintillaConstants.SCE_RB_STRING,
                             ScintillaConstants.SCE_RB_CHARACTER,
                             ScintillaConstants.SCE_RB_HERE_Q,
                             ScintillaConstants.SCE_RB_HERE_QQ,
                             ScintillaConstants.SCE_RB_STRING_Q,
                             ScintillaConstants.SCE_RB_STRING_QQ,
                             ScintillaConstants.SCE_RB_STRING_QX
                             ]

    def is_symbol(self, tok, callback=None):
        return tok.style == ScintillaConstants.SCE_RB_SYMBOL

    def tokenStyleToContainerStyle(self, tok, callback):
        return self.narrowStyles.get(tok.style, VAR_KIND_UNKNOWN)

    # Accessors for where we'd rather work with a style than call a predicate fn

    @property
    def style_identifier(self):
        return ScintillaConstants.SCE_RB_IDENTIFIER
    
    @property
    def style_operator(self):
        return ScintillaConstants.SCE_RB_OPERATOR

    @property
    def style_word(self):
        return ScintillaConstants.SCE_RB_WORD

lang_specific_classes = {"Ruby": RubyClassifier,
                         "RHTML" : UDLClassifier}

def remove_hashes(lines):
    return map(lambda s: _leading_hash_re.sub("", s), lines)

class RailsMigrationData:    
    def __init__(self):
        self.tableHookName = None
        self.columns = []   # Array of {name, type} pairs
    
class RailsMigrationBlock:
    def __init__(self):
        self.table_name = None
        # non-neg means we're in the pertinent scope
        self.class_indentLevel = -1
        self.upFunc_indentLevel = -1
        self.data = [] # Array of RailsMigrationData

_inflector = None
def get_inflector():
    global _inflector
    if _inflector is None:
        import inflector.Inflector
        _inflector = inflector.Inflector.Inflector()
    return _inflector

class Parser:
    # New names could be added to Rails post Rails 2.0,
    # for database-specific types like 'blob'
    _rails_migration_types = ('binary', 'boolean', 'date',
                              'datetime', 'decimal', 'float',
                              'string', 'integer',
                              )
        
    def __init__(self, tokenizer, lang):
        self.tokenizer = tokenizer
        self.block_stack = []
        self.tree = FileNode()
        self.curr_node = self.tree
        self.bracket_matchers = {"[":"]", "{":"}", "(":")"}
        self.classifier = lang_specific_classes[lang]()
        self.containers = {VAR_KIND_GLOBAL : [self.tree.global_vars],
                           VAR_KIND_CLASS : [], #classes
                           VAR_KIND_CLASSVAR : [],
                           VAR_KIND_INSTANCE : [],
                           VAR_KIND_LOCAL : [self.tree.local_vars], #locals
                           VAR_KIND_ALIAS : [self.tree.aliases],
                           }
        self.rails_migration_block = RailsMigrationBlock()

    def class_has_method(self, curr_node, the_text):
        try:
            class_node = self.containers[VAR_KIND_CLASS][-1]
            for c in class_node.children:
                if isinstance(c, MethodNode) and c.name == the_text:
                    return True
        except:
            pass
        return False


    def curr_block_start_indentation(self):
        try:
            ind = self.block_stack[-1].indentation
        except:
            ind = 0
        return ind

    # This routine compares the current line indentation
    # with the one at the start of the block
    #
    # Neg value: we've moved to far back
    # 0: same ind
    # Pos value: curr indent'n is greater than where we started
    
    def compare_curr_ind(self):
        start_ind = self.curr_block_start_indentation()
        curr_indent = self.tokenizer.get_curr_indentation() # 
        return curr_indent - start_ind
    
    def dump(self):
        self.tree.dump()
        
    def rails_migration_class_tree(self):
        rails_migration_block = self.rails_migration_block
        inflector = get_inflector()
        nodes = []
        for info in self.rails_migration_block.data:
            if info.tableHookName is None or not info.columns:
                return None                
            className = inflector.camelize(inflector.singularize(info.tableHookName))
            classNode = ClassNode(className, info.startLine, False)
            classNode.set_line_end_num(info.endLine)
            for attrib_info in info.columns:
                methodNode = MethodNode(attrib_info[0], attrib_info[2])
                methodNode.set_line_end_num(attrib_info[2])                
                classNode.append_node(methodNode)
            nodes.append(classNode)
        return nodes
        
    def parse(self):
        self.parse_aux(self.tree)
        return self.tree
        
    def get_parsing_objects(self, kwd):
        return {
            "module": [ModuleNode, self.parse_aux],
            "class" : [ClassNode, self.parse_aux],
            "def" : [MethodNode, self.parse_method]
        }.get(kwd, [None, None])

    def parse_open_parens(self):
        paren_count = 0
        while True:
            tok = self.tokenizer.get_next_token()
            if self.classifier.is_operator(tok, "("):
                paren_count += 1
            else:
                return (tok, paren_count)

    def parse_attr_stmt_capture_info(self, collection, attr_tok, tok, curr_node):
        base_name = tok.text[1:]
        update_collection(collection,
                          '@' + base_name, tok.start_line)
        if isinstance(curr_node, ClassNode):
            if attr_tok != 'attr_writer':
                new_node = MethodNode(base_name, tok.start_line)
                new_node.set_line_end_num(tok.start_line)
                curr_node.append_node(new_node)
            if attr_tok in ['attr_writer', 'attr_accessor']:
                new_node = MethodNode(base_name + '=', tok.start_line)
                new_node.set_line_end_num(tok.start_line)
                new_node.add_arg(base_name, "")
                curr_node.append_node(new_node)

    def parse_attr_stmts(self, attr_tok, curr_node):
        """
        attr_tok is one of ['attr', 'attr_reader', 'attr_writer', 'attr_accessor']
        if curr_node is a ClassNode then set up a bunch of methods as well
        """
        try:
            collection = self.containers[VAR_KIND_INSTANCE][-1]
            if collection is None:
                return
        except:
            return
        (tok, paren_count) = self.parse_open_parens()
        if self.classifier.is_symbol(tok, self.classifier.is_symbol_cb):
            self.parse_attr_stmt_capture_info(collection, attr_tok, tok, curr_node)                
        # Allow for more, but special case attr's
        while True:
            tok = self.tokenizer.get_next_token()
            if self.classifier.is_operator(tok, ","):
                tok = self.tokenizer.get_next_token()
                # Intern unless attr
                if (self.classifier.is_symbol(tok, self.classifier.is_symbol_cb) and
                    attr_tok != 'attr'):
                    self.parse_attr_stmt_capture_info(collection, attr_tok, tok, curr_node)
            else:
                self.tokenizer.put_back(tok)
                break
        # Might as well consume the closing parens
        while paren_count > 0:
            tok = self.tokenizer.get_next_token()
            if self.classifier.is_operator(tok, ")"):
                paren_count -= 1
            else:
                self.tokenizer.put_back(tok)
                break;

    def parse_assignment(self, collectionA, tok_text, start_line):
        if len(collectionA) == 0 or collectionA[-1] is None:
            return
        
        tok = self.tokenizer.get_next_token()
        # We don't need to Watch out for calls like abc=(1)
        # because that's always an assignment to a local.
        # self.abc=(1) is different
        
        if self.classifier.is_any_operator(tok):
            if tok.text == "=":
                self._finishVarAssignment(collectionA, tok_text, start_line)
                # Look to see if we have an instance of a class
                # This is 
                update_collection(collectionA[-1], tok_text, start_line)
                return
            elif tok.text in ["::", "."]:
                # Don't store fully-qualified names, but do consume them
                # Keep name for debugging purposes.
                rest_of_name = self.get_fully_qualified_name()
                return
        self.tokenizer.put_back(tok)
        
    def _actual_string_from_string_or_symbol(self, tok):
        if self.classifier.is_symbol(tok):
            return tok.text[1:]
        else:
            assert self.classifier.is_string(tok)
            return self.de_quote_string(tok)
  
    def _parse_migration_create_table_block(self):
        """This code is handled only when in the following conditions:
        1. The file path matches .../db/migrate/*.rb
        2. It's in a class that inherits from ActiveRecord::Migration
        3. It's in a function called "self.up"
        
        Database fields are found through two functions:
        create_table TABLE-NAME do |handle|
          handle.column COLUMN-NAME TYPE
        end
        
        To add:
        add_column TABLE-NAME COLUMN-NAME TYPE
        """
        tok = self.tokenizer.get_next_token()
        if not (self.classifier.is_symbol(tok) or self.classifier.is_string(tok)):
            return
        rails_migration_info = RailsMigrationData()
        rails_migration_info.tableHookName = self._actual_string_from_string_or_symbol(tok)
        rails_migration_info.startLine = tok.start_line
        # Assume we don't find the end of the block, so assume the worst
        rails_migration_info.endLine = tok.start_line + 1
        tok = self.tokenizer.get_next_token()
        if self.classifier.is_operator(tok, "{") or self.classifier.is_keyword(tok, "do"):
            control_tok = (tok.style, (tok.text == "{" and "}") or "end")
        else:
            return
        tok = self.tokenizer.get_next_token()
        if not self.classifier.is_operator(tok, "|"):
            return
        tok = self.tokenizer.get_next_token()
        if not self.classifier.is_identifier(tok):
            return
        table_handle = tok.text
        tok = self.tokenizer.get_next_token()
        if not self.classifier.is_operator(tok, "|"):
            return
        add_entry = False
        while True:
            tok = self.tokenizer.get_next_token()
            if tok.style == shared_lexer.EOF_STYLE:
                break
            elif tok.style == control_tok[0] and tok.text == control_tok[1]:
                rails_migration_info.endLine = tok.end_line
                break
            elif self.classifier.is_identifier(tok) and tok.text == table_handle:
                tok = self.tokenizer.get_next_token()
                if self.classifier.is_operator(tok, "."):
                    tok = self.tokenizer.get_next_token()
                    if self.classifier.is_identifier(tok):
                        line_num = tok.start_line
                        if tok.text == 'column':
                            tok = self.tokenizer.get_next_token()
                            if self.classifier.is_symbol(tok) or self.classifier.is_string(tok):
                                column_name = self._actual_string_from_string_or_symbol(tok)
                                tok = self.tokenizer.get_next_token()
                                if self.classifier.is_operator(tok, ','):
                                    tok = self.tokenizer.get_next_token()
                                    if self.classifier.is_symbol(tok) or self.classifier.is_string(tok):
                                        column_type = self._actual_string_from_string_or_symbol(tok)
                                    else:
                                        column_type = ""
                                    add_entry = True
                        elif tok.text in self._rails_migration_types:
                            column_type = tok.text
                            tok = self.tokenizer.get_next_token()
                            log.debug("Migration: add %s:%s",
                                      tok.text, column_type)
                            if self.classifier.is_symbol(tok) or self.classifier.is_string(tok):
                                column_name = self._actual_string_from_string_or_symbol(tok)
                                add_entry = True
                        elif tok.text == "timestamps":
                            # Rails 2.0 migration syntax in these two blocks:
                            # create_table :objects do |t|
                            #   t.<type> :<name>
                            column_type = 'datetime'
                            rails_migration_info.columns.append(('created_at', column_type, line_num))
                            rails_migration_info.endLine = line_num + 1
                            column_name = 'updated_at'
                            add_entry = True
                        if add_entry:
                            rails_migration_info.columns.append((column_name, column_type, line_num))
                            rails_migration_info.endLine = line_num + 1
                            add_entry = False
                            continue
            # Sanity check any token we have here
            if (tok.style == ScintillaConstants.SCE_RB_WORD and
                tok.text in ('class', 'def')):
                self.tokenizer.put_back(tok)
                return
        self.rails_migration_block.data.append(rails_migration_info)
        # end _parse_migration_create_table_block
        
    def _parse_migration_add_column_stmt(self):
        """This code is handled only when in the following conditions:
        1. The file path matches .../db/migrate/*.rb
        2. It's in a class that inherits from ActiveRecord::Migration
        3. It's in a function called "self.up"
        4. We saw an add_column action.
        
        Syntax:
        add_column TABLE-NAME COLUMN-NAME TYPE
        """
        tok = self.tokenizer.get_next_token()
        if not (self.classifier.is_symbol(tok) or self.classifier.is_string(tok)):
            return
        table_name = self._actual_string_from_string_or_symbol(tok)
        tok = self.tokenizer.get_next_token()
        if not self.classifier.is_operator(tok, ","):
            return
        tok = self.tokenizer.get_next_token()
        if not (self.classifier.is_symbol(tok) or self.classifier.is_string(tok)):
            return
        rails_migration_info = RailsMigrationData()
        rails_migration_info.tableHookName = table_name
        rails_migration_info.endLine = rails_migration_info.startLine = tok.start_line
        column_name = self._actual_string_from_string_or_symbol(tok)
        column_type = ""
        tok = self.tokenizer.get_next_token()
        if self.classifier.is_operator(tok, ','):
            tok = self.tokenizer.get_next_token()
            if self.classifier.is_symbol(tok) or self.classifier.is_string(tok):
                column_type = self._actual_string_from_string_or_symbol(tok)
            else:
                self.tokenizer.put_back(tok)
        else:
            self.tokenizer.put_back(tok)            
        rails_migration_info.columns.append((column_name, column_type, rails_migration_info.startLine))
        self.rails_migration_block.data.append(rails_migration_info)
    
    def _finish_interpolating_string(self, prev_tok):
        """ Matches sequences of "#{", ... "}"
        (which could nest).  Returns a list of all the tokens.
        """

        tok1 = self.tokenizer.get_next_token()
        if not self.classifier.is_any_operator(tok1) or \
           tok1.text != "#":
            self.tokenizer.put_back(tok1)
            return [prev_tok]
        tok2 = self.tokenizer.get_next_token()
        if not self.classifier.is_any_operator(tok2) or \
           tok2.text != "{":
            self.tokenizer.put_back(tok1)
            self.tokenizer.put_back(tok2)
            return [prev_tok]
        
        nested_count = 1
        tok_list = [prev_tok, tok1, tok2]
        # At this point process a contiguous stream of tokens
        while True:
            bail_out = False
            new_tok = self.tokenizer.get_next_token()
            if new_tok.style == shared_lexer.EOF_STYLE:
                bail_out = True
            elif self.classifier.is_any_operator(new_tok):
                if new_tok.text == "#":
                    tok_list.append(new_tok)
                    new_tok = self.tokenizer.get_next_token()
                    if self.classifier.is_any_operator(new_tok) and \
                       new_tok.text == "{":
                        nested_count += 1
                    elif nested_count == 0:
                        bail_out = True
                elif new_tok.text == "}" and nested_count > 0:
                    nested_count -= 1
                elif nested_count == 0:
                    bail_out = True
            elif self.classifier.is_interpolating_string(new_tok, self._test_interpolate_string):
                pass
            elif nested_count == 0:
                bail_out = True
            if bail_out:
                self.tokenizer.put_back(new_tok)
                return tok_list
            else:
                tok_list.append(new_tok)
    
    def _at_end_expression(self, tok):
        if not self.classifier.is_any_operator(tok):
            return True
        return tok.text in [",", "}", ";"]
    
    def skip_to_op(self, opText, nestedLevel=1):
        skipped_toks = []
        while 1:
            tok = self.tokenizer.get_next_token()
            skipped_toks.append(tok)
            if tok.style == shared_lexer.EOF_STYLE:
                return skipped_toks
            elif self.classifier.is_any_operator(tok):
                if tok.text in ["(", "{", "["]:
                    nestedLevel += 1
                elif tok.text in ["]", "}", ")"]:
                    nestedLevel -= 1
                    if nestedLevel <= 0:
                        return skipped_toks
                # don't care about other ops
            # don't care about other token types

    def de_quote_string(self, tok):
        tval = tok.text
        patterns = self.classifier.get_quote_patterns(tok, self.classifier.quote_patterns_cb)
        for p in patterns:
            m = p.match(tval)
            if m:
                return m.group(1)
        return tval

    def _finishVarAssignment(self, collectionA, var_name, start_line):
        # See doc for finishVarAssignment in src/perlcile/ParseModule.pm
        # for comments.
        # 1: a = b.c.d.e -- don't bother
        # 2.1: a = <number> <no op>
        # 2.2: a = <string> <no op>
        # 3. a = <classname>.New [( ... )]<no op>

        tok_list = self.get_fully_qualified_name_as_list()
        if not tok_list:
            return
        tok = tok_list[0]
        if self.classifier.is_identifier(tok):
            var_citdl = None
            toks_to_return = tok_list
            if len(toks_to_return) < 3:
                tok2 = self.tokenizer.get_next_token()
                #toks_to_return.append(tok2)
                if self.classifier.is_operator(tok2, ','):
                    #XXX : skip to end -- we must be in a parallel assignment
                    pass
                else:
                    if self._at_end_expression(tok2):
                        var_citdl = tok.text
                    self.tokenizer.put_back(tok2)
            elif self.classifier.is_operator(toks_to_return[-2], '.') and \
                self.classifier.is_identifier(toks_to_return[-1]) and \
                toks_to_return[-1].text == 'new':
                    tok3 = self.tokenizer.get_next_token()
                    if self._at_end_expression(tok3):
                        var_citdl = ''.join([tok.text for tok in tok_list[:-2]])
                        self.tokenizer.put_back(tok3)
                        # toks_to_return.append(tok3)
                    else:
                        if self.classifier.is_operator(tok3, "("):
                            skipped_toks = self.skip_to_op(")")
                            # toks_to_return += skipped_toks
                            tok4 = self.tokenizer.get_next_token()
                        else:
                            tok4 = tok3
                        if self._at_end_expression(tok4):
                            var_citdl = ''.join([tok.text for tok in tok_list[:-2]])
                        self.tokenizer.put_back(tok4)
            update_collection(collectionA[-1], var_name, start_line, var_citdl)
            # Idea: don't bother putting back these tokens
            #for t in tok_list:
            #    self.tokenizer.put_back(t)
            return
            
        builtin_type = self.classifier.get_builtin_type(tok, self._test_for_builtin_type)
        if builtin_type:
            type1, locn = tok.style, tok.start_line
            if self.classifier.is_interpolating_string(tok, self._test_interpolate_string):
                self._finish_interpolating_string(tok)
            tok2 = self.tokenizer.get_next_token()
            if self._at_end_expression(tok2):
                if self.classifier.is_number(tok):
                    type1 = "Number"
                else:
                    type1 = "String"
                update_collection(collectionA[-1], var_name, start_line, builtin_type)
                toks = [tok2]
            else:
                update_collection(collectionA[-1], var_name, start_line)
                toks = [tok2, tok]
        elif tok.style == self.classifier.style_identifier:
            raise("get_fully_qualified_name_as_list failed to process an identifer")
        elif self.classifier.is_operator(tok, "["):
            toks = self._finish_list(collectionA, var_name, start_line, tok, "]", "Array")
        elif self.classifier.is_operator(tok, "{"):
            toks = self._finish_list(collectionA, var_name, start_line, tok, "}", "Hash")
        else:
            update_collection(collectionA[-1], var_name, start_line)
            toks = [tok]
        for t in toks:
            self.tokenizer.put_back(t)
            
    def _finish_list(self, collectionA, var_name, start_line, orig_tok, end_op, class_name):
        skipped_toks = [orig_tok] + self.skip_to_op(end_op)
        final_tok = self.tokenizer.get_next_token()
        skipped_toks.append(final_tok)
        class_name_final = self._at_end_expression(final_tok) and class_name or None
        update_collection(collectionA[-1], var_name, start_line, class_name_final)
        return skipped_toks

    def _set_basename_method(self, node_class, curr_node, nm_token):
        if node_class != MethodNode: return (nm_token, False)
        method_name = nm_token[0]
        idx1 = method_name.rfind('::')
        if idx1 >= 0: idx1_len = 2
        idx2 = method_name.rfind('.')
        if idx2 >= 0: idx2_len = 1
        if idx1 < 0:
            if idx2 < 0:
                return (nm_token, False)
            idx = idx2
            idx_len = 1
        elif idx2 < idx1:
            # Includes no idx2
            idx = idx1
            idx_len = 2
        else:
            idx = idx2
            idx_len = 1
        first_part = method_name[0:idx]
        if first_part != getattr(curr_node, 'name', '') and first_part != 'self':
            # We're doing something like defining inside a mix-in
            return (nm_token, False)            
            
        basename = method_name[idx + idx_len :]
        if len(nm_token) != 2:
            raise("Expectations dashed!")
        
        return ((basename, nm_token[1]), True)

    def _test_interpolate_string(self, tok, generic_tok_type):
        if generic_tok_type == shared_parser.GENERIC_TYPE_REGEX:
            return True
        elif generic_tok_type != shared_parser.GENERIC_TYPE_STRING:
            return False
        tval = tok.text
        c1 = tval[0]
        if c1 == "'":
            return False
        elif c1 == '"':
            return True
        elif c1 == '%':
            if len(c1) == 1:
                return False  #???
            c2 = tval[1]
            if c2 in "WwQrx":
                return True
        return False

    # Callback used by get_builtin_type
    def _test_for_builtin_type(self, tok, generic_tok_type):
        if generic_tok_type == shared_parser.GENERIC_TYPE_NUMBER:
            numval = tok.text
            if numval.find(".") >= 0:
                return "Float"
            else:
                return "Fixnum"
        elif generic_tok_type == shared_parser.GENERIC_TYPE_STRING:
            tval = tok.text
            if len(tval) > 1 and tval[0] == "%":
                if tval[1] in 'wW':
                    return "Array"
                elif tval[1] == 'r':
                    return "Regexp"
            return "String"
        elif generic_tok_type == shared_parser.GENERIC_TYPE_REGEX:
            return "Regexp"
        else:
            return None

    # Callback used by tokenStyleToContainerStyle
    def _test_token_style(self, tok, is_variable_token):
        if not is_variable_token:
            return VAR_KIND_UNKNOWN
        tval = tok.text
        if tval[0] == '$':
            return VAR_KIND_GLOBAL
        elif tval[0] == '@':
            if len(tval) > 1 and tval[1] == '@':
                return VAR_KIND_CLASSVAR
            else:
                return VAR_KIND_INSTANCE
        return VAR_KIND_UNKNOWN
    
    def _try_loading_relative_library(self, tok, curr_node):
        """Look for instances of
        require File.dirname(__FILE__) + <string> and map to
        @<string>"""
        seq_start_line = tok.start_line
        if not self.classifier.is_identifier(tok) or tok.text != 'File':
            return
        tok = self.tokenizer.get_next_token()
        if not self.classifier.is_operator(tok, '.'):
            return
        tok = self.tokenizer.get_next_token()
        if not self.classifier.is_identifier(tok) or tok.text != 'dirname':
            return
        tok = self.tokenizer.get_next_token()
        if not self.classifier.is_operator(tok, '('):
            return
        tok = self.tokenizer.get_next_token()
        if not self.classifier.is_identifier(tok, True) or tok.text != '__FILE__':
            return
        tok = self.tokenizer.get_next_token()
        if not self.classifier.is_operator(tok, ')'):
            return
        tok = self.tokenizer.get_next_token()
        if not self.classifier.is_operator(tok, '+'):
            return
        tok = self.tokenizer.get_next_token()
        if self.classifier.is_string(tok):
            curr_node.imports.append(Name_LineNum
                                     (self._create_relative_libname(tok),
                                      seq_start_line))
            
    def _create_relative_libname(self, tok):
        # For now just return the path.  If we need to decorate it
        # to indicate it's a relative path, we'll do that later.
        return self.de_quote_string(tok)[1:]
            

    def _extract_alias_name(self, tok):
        if self.classifier.is_identifier(tok):
            return tok.text
        elif self.classifier.is_symbol(tok, self.classifier.is_symbol_cb):
            return tok.text[1:]
        else:
            return None

    def parse_aux(self, curr_node):
        at_start = True
        while 1:
            tok = self.tokenizer.get_next_token()
            if tok.style == shared_lexer.EOF_STYLE:
                break
            # style, text, start_column, start_line, end_column, end_line = tok
            style, text = tok.style, tok.text
            if style == self.classifier.style_word:
                if text in ["module", "class", "def"]:
                    # Check to see if we missed some nodes,
                    # using heuristic that the end statements line up
                    # with the start of each block, for definitions

                    if len(self.block_stack) > 0 and self.compare_curr_ind() <= 0:
                        # We missed one or more end's, so put the token
                        # back and try in an outer instance
                        self.tokenizer.put_back(tok)
                        return

                    curr_indent = self.tokenizer.get_curr_indentation() # 
                    node_class, node_parser = self.get_parsing_objects(text)
                    if node_class is None:
                        sys.stderr.write("Couldn't get parsing objects for type %s\n" % text)
                        break
                    elif node_class is MethodNode:
                        self.tokenizer.start_sig()

                    # Get the comments before further parsing.
                    comment_lines = remove_hashes(self.tokenizer.curr_comment())
                    nm_token = self.get_fully_qualified_name()
                    if not nm_token[0]:
                        return
                    elif nm_token[0] == "<<" and node_class == ClassNode:
                        # Singleton classes
                        nm_token = self.get_fully_qualified_name()
                        if not nm_token[0]:
                            return
                        
                    if self.rails_migration_block.class_indentLevel >= 0 and nm_token[0] == "self.up":
                        self.rails_migration_block.upFunc_indentLevel = curr_indent
                        rails_migration_clear_upfunc = True
                    else:
                        rails_migration_clear_upfunc = False

                    (nm_token, is_class_method) = self._set_basename_method(node_class, curr_node, nm_token)
                    new_node = node_class(nm_token[0], tok.start_line, nm_token[0] == "initialize")
                    if is_class_method:
                        new_node.is_classmethod = True
                    elif node_class == MethodNode and (isinstance(curr_node, ClassNode) or isinstance(curr_node, ModuleNode)):
                        # Add info on the 'self' variable
                        update_collection(new_node.local_vars, 'self', tok.start_line, curr_node.name)
                    new_node.doc_lines = comment_lines
                    new_node.indentation = curr_indent
                    self.block_stack.append(new_node)
                    curr_node.append_node(new_node)

                    # Push new containers on the symbol table
                    self.containers[VAR_KIND_LOCAL].append(new_node.local_vars)
                    if node_class in [ClassNode, ModuleNode]:
                        self.containers[VAR_KIND_CLASS].append(new_node)
                        self.containers[VAR_KIND_CLASSVAR].append(new_node.class_vars)
                        self.containers[VAR_KIND_INSTANCE].append(new_node.instance_vars)
                        self.containers[VAR_KIND_ALIAS].append(new_node.aliases)

                    # Watch out for class inheritence
                    
                    rails_migration_clear_classref = False
                    if node_class == ClassNode:
                        self.parse_classref(new_node)
                        if new_node.has_classref('ActiveRecord::Migration'):
                            self.rails_migration_block.class_indentLevel = curr_indent;
                            rails_migration_clear_classref = True
                    node_parser(new_node)  # Has self bound to it
                    if rails_migration_clear_upfunc:
                        self.rails_migration_block.upFunc_indentLevel = -1
                    elif rails_migration_clear_classref:
                        self.rails_migration_block.class_indentLevel = -1
                    self.block_stack.pop()
                    self.containers[VAR_KIND_LOCAL].pop()
                    if node_class in [ClassNode, ModuleNode]:
                        self.containers[VAR_KIND_CLASSVAR].pop()
                        self.containers[VAR_KIND_INSTANCE].pop()
                        self.containers[VAR_KIND_CLASS].pop()
                        self.containers[VAR_KIND_ALIAS].pop()

                    # Clear any comment that's hanging around
                    self.tokenizer.clear_comments()

                elif text == "alias":
                    new_tok = self.tokenizer.get_next_token()
                    new_name = self._extract_alias_name(new_tok)
                    existing_tok = self.tokenizer.get_next_token()
                    existing_name = self._extract_alias_name(existing_tok)
                    if new_name and existing_name:
                        update_collection(self.containers[VAR_KIND_ALIAS][-1], new_name, new_tok.start_line, existing_name)
                
                        # set a variable in curr_node
                elif text == "end":
                    if len(self.block_stack) > 0:
                        end_position = self.compare_curr_ind()
                        if end_position < 0:
                            # We've gone too far, so put it back and try later
                            curr_node.set_line_end_num(tok.start_line)
                            self.tokenizer.put_back(tok)
                            return
                        elif end_position == 0:
                            curr_node.set_line_end_num(tok.start_line)
                            # the caller will pop the stack
                            return
                        
            elif style == self.classifier.style_identifier:
                if text == "require" or text == "load":
                    tok = self.tokenizer.get_next_token()
                    if (self.tokenizer.is_string_token(tok)):
                        tval = self.de_quote_string(tok)
                        if tval.endswith(".rb"):
                            tval = tval[:-3]
                        curr_node.imports.append(Name_LineNum(tval, tok.start_line))
                    else:
                        self._try_loading_relative_library(tok, curr_node)
                elif text == "include":
                    nm_token = self.get_fully_qualified_name()
                    if nm_token[0]:
                        curr_node.includes.append(Name_LineNum(nm_token[0], nm_token[1]))
                #@@@@ elif text == "base":
                    # semi-hardwired rails thing
                    #@@@@ self.parse_class_extension()
                    # if next() == (OP, ".") \
                      # and next() == (ID, "extend") \
                       # and next() == (OP, "(") \
                       
                elif at_start or tok.start_column == self.tokenizer.get_curr_indentation():
                    # Look at these things only at start of line
                    if text in ['attr', 'attr_reader', 'attr_writer', 'attr_accessor']:
                        self.parse_attr_stmts(text, curr_node)
                    elif text == 'create_table' and self.rails_migration_block.upFunc_indentLevel >= 0:
                        self._parse_migration_create_table_block()
                    elif text == 'add_column' and self.rails_migration_block.upFunc_indentLevel >= 0:
                        self._parse_migration_add_column_stmt()
                    elif not self.class_has_method(curr_node, tok.text + "="):
                        # Make sure it isn't an assignment function
                        self.parse_assignment(self.containers[VAR_KIND_LOCAL], text, tok.start_line)

            elif self.classifier.is_any_operator(tok):
                if text == "{":
                    new_node = BlockNode("{", tok.start_line);
                    new_node.indentation = self.tokenizer.get_curr_indentation()
                    #XXX Transfer any children a block defines to the
                    # parent of the block.  Uncommon formulation
                    self.block_stack.append(new_node)
                    self.parse_aux(new_node)
                    self.block_stack.pop()
                elif text == "}":
                    if len(self.block_stack) > 0:
                        end_position = self.compare_curr_ind()
                        if end_position < 0:
                            # We've gone too far, so put it back and try later
                            self.tokenizer.put_back(tok)
                            return
                        elif end_position == 0:
                            # the caller will pop the stack
                            return
            # Check for assignment to some kind of variable
            else:
                narrow_style = self.classifier.tokenStyleToContainerStyle(tok, self._test_token_style)
                if narrow_style != VAR_KIND_UNKNOWN:
                    self.parse_assignment(self.containers[narrow_style], tok.text, tok.start_line)
            # end if WORD block
            #XXX: process variables as well
            at_start = False
        # end while
        return
    # end parse_aux()
    
    """
    Simplified Ruby function-defn grammar
    
method_def ::= kDEF fname f_arglist bodystmt kEND
fname ::= ID
f_arglist ::= "(" f_args opt_nl ")" | f_args term
term ::= "\n" | ";"
f_args ::= f_arg(s /,/)
	 | <nothing>
f_arg ::= f_norm_arg | f_opt | f_rest_arg | f_block_arg
f_norm_arg ::= id
f_opt ::= id '=' arg_value
f_rest_arg ::= "*" id? 
f_block_arg ::= "&" id 

arg_value ::= simple_expn
simple_expn ::= (simple_term | nested_expn)+
simple_term ::= <anything but a ";", "\n", ")", "," or a block-starter or closer
 - the exceptions depend on whether we're in a parenthesized construct or not
simple_inner_expn ::= (simple_term | nested_expn)+
nested_expn ::= "(" simple_expn ")" | "{" simple_expn "}" | "[" simple_expn "]"
"""
        
    def parse_nested_expn(self, block_end_char):
        while 1:
            tok = self.tokenizer.get_next_token()
            if tok.style == shared_lexer.EOF_STYLE:
                return
            elif self.classifier.is_any_operator(tok):
                # Don't look at commas or semi-colons here, as we might be
                # processing nested comma-sep things or even blocks
                if len(tok.text) == 1:
                    if tok.text == block_end_char:
                        return -1
                    elif "[{(".find(tok.text) >= 0:
                        self.parse_nested_expn(self.bracket_matchers[tok.text])
            elif self.classifier.is_keyword(tok, "end"):
                if len(self.block_stack) == 0:
                    return
                elif self.compare_curr_ind() <= 0:
                    # Did we go too far?
                    self.tokenizer.put_back(tok)
                    return
    # end parse_nested_expn
    
    # This might not always work
    def parse_simple_expn(self, has_paren):
        while 1:
            tok = self.tokenizer.get_next_token()
            if tok.style == shared_lexer.EOF_STYLE:
                return
            elif self.classifier.is_any_operator(tok):
                if tok.text == ",":
                    self.tokenizer.put_back(tok)
                    return
                elif has_paren and tok.text == ')':
                    self.tokenizer.put_back(tok)
                    return
                elif not has_paren and tok.text == ';':
                    self.tokenizer.put_back(tok)
                    return
                elif len(tok.text) == 1 and "[{(".find(tok.text) >= 0:
                    self.parse_nested_expn(self.bracket_matchers[tok.text])
            elif self.classifier.is_keyword(tok, "end"):
                if len(self.block_stack) == 0:
                    return
                elif self.compare_curr_ind() <= 0:
                    # Did we go too far?
                    self.tokenizer.put_back(tok)
                    return
    # end parse_simple_expn

    def parse_method_args(self, curr_node):
        tok = self.tokenizer.get_next_token()
        if tok.style == shared_lexer.EOF_STYLE:
            return
        elif self.classifier.is_operator(tok, ";"):
            self.tokenizer.put_back(tok)
            return  # No args
        elif self.classifier.is_operator(tok, "("):
            has_paren = True
        elif tok.start_line > curr_node.line_num:
            # Assume a zero-paren function
            self.tokenizer.put_back(tok)
            return  # No args
        
        else:
            self.tokenizer.put_back(tok)  # simplifies the while loop
            has_paren = False
        # Further simplification: look for the "," at the start of the loop
        comma_token = shared_lexer.Token(style=self.classifier.style_operator, text=",")
        comma_token.generated = 1
        self.tokenizer.put_back(comma_token)
        while 1:
            tok = self.tokenizer.get_next_token()
            # First check for white-space, set indent,
            if tok.style == shared_lexer.EOF_STYLE:
                return
            elif has_paren and self.classifier.is_operator(tok, ")"):
                return
            elif self.classifier.is_keyword(tok, 'end') and self.compare_curr_ind() <= 0:
                # Did we go too far?
                self.tokenizer.put_back(tok)
                return

            # Note -- silvercity swallows \-line-continuations,
            # so we don't need to handle them

            if self.classifier.is_operator(tok, ","):
                tok = self.tokenizer.get_next_token()
            else:
                self.tokenizer.put_back(tok)
                return
            
            # then check for arg-list termination,
            # and then process the arg...
            extra_info = ""
            if (self.classifier.is_any_operator(tok) and
                len(tok.text) == 1 and "*&".find(tok.text) >= 0):
                extra_info = tok.text
                tok = self.tokenizer.get_next_token()
            if self.classifier.is_identifier(tok, True):
                curr_node.add_arg(tok.text, extra_info)
            else:
                # give up -- expected to see an arg, didn't
                return
            # check for an '=' sign
            tok = self.tokenizer.get_next_token()
            if self.classifier.is_operator(tok, '='):
                self.parse_simple_expn(has_paren)
            else:
                self.tokenizer.put_back(tok)
        # end while
    # end parse_method_args
    
    def parse_method(self, curr_node):
        # Get the args before dispatching back to the main routine

        self.parse_method_args(curr_node)
        self.tokenizer.stop_sig()

        #XXX Remove newlines and \-prefixed newlines, with white-space
        curr_node.signature = self.tokenizer.get_sig() # @@@@ self.trimmer.trim_ws(self.tokenizer.get_sig())
        
        # Now look for the 'end' on the same line as a special case
        # The start line is contained in curr_node.line_num        
        while 1:
            tok = self.tokenizer.get_next_token()
            if tok.style == shared_lexer.EOF_STYLE:
                return;
            # style, text, start_column, start_line, end_column, end_line = tok
            if tok.end_line > self.block_stack[-1].line_num:
                self.tokenizer.put_back(tok)
                break
            #*** Heuristic: if we find an 'end' followed by a newline, end the sub here
            elif self.classifier.is_keyword(tok, "end"):
                # Assume that's the end
                # Let the caller pop the block_stack
                return
        # end while
        self.parse_aux(curr_node)
    # end parse_method
    
    def parse_classref(self, node):
        toks = []
        tok = self.tokenizer.get_next_token(1)
        fqname = classref_type = None
        if self.classifier.is_operator(tok, "<"):
            fqname, line_start = self.get_fully_qualified_name()
            if fqname == "DelegateClass":
                tok = self.tokenizer.get_next_token(1)
                if self.classifier.is_operator(tok, "("):
                    # No putback once we enter this point
                    inner_name, junk = self.get_fully_qualified_name()
                    tok = self.tokenizer.get_next_token()
                    if self.classifier.is_operator(tok, ")"):
                        fqname = "%s(%s)" % (fqname, inner_name)
                        classref_type = inner_name
                else:
                    toks.append(tok)
        else:
            fqname = "Object"
            line_start = tok.start_line
            toks.append(tok)
        if fqname is not None:
            node.add_classrefs(fqname, line_start, classref_type)
        
        for t in toks:
            self.tokenizer.put_back(t)

    def get_fully_qualified_name(self):
        tok = self.tokenizer.get_next_token()
        if tok.style == shared_lexer.EOF_STYLE:
            return (None, None)
        name_start = tok.text
        line_start = tok.start_line
        # Watch out if it starts with a "::"
        if name_start == "::":
            tok = self.tokenizer.get_next_token()
            if tok.style != self.classifier.style_identifier:
                self.tokenizer.put_back(tok)
                return (name_start, line_start)
            name_start += tok.text
                
        while 1:
            # Collect operator-type methods
            if self.classifier.is_any_operator(tok):
                while 1:
                    tok = self.tokenizer.get_next_token()
                    if self.classifier.is_any_operator(tok) and tok.text not in "()@${};:?,":
                        name_start += tok.text
                    else:
                        self.tokenizer.put_back(tok)
                        break
                # And it will be the end of the line
                return (name_start, line_start)
            tok = self.tokenizer.get_next_token()
            if not self.classifier.is_any_operator(tok):
                self.tokenizer.put_back(tok)
                break
            if not tok.text in ["::", "."]:
                self.tokenizer.put_back(tok)
                break
            tok2 = self.tokenizer.get_next_token()
            if tok2.style != self.classifier.style_identifier:
                self.tokenizer.put_back(tok)
                self.tokenizer.put_back(tok2)
                break
            name_start += tok.text + tok2.text
        return (name_start, line_start)

    # Consume { (CapName, ['.' | '::']) | (lcName, '::') }
    # Return a list of the tokens
    def get_fully_qualified_name_as_list(self):
        # Check for a leading '::' and throw it away
        tok = self.tokenizer.get_next_token()
        if self.classifier.is_operator(tok, '::'):
            # Throw it away
            tok = self.tokenizer.get_next_token()
        
        if self.classifier.is_identifier(tok, False):
            tok_list = [tok]
        else:
            return [tok]

        # Now look for scope-resolution operators:
        # '::' always
        # '.' followed by an upper-case name (not fully Rubyish, but...)
        
        while True:            
            # Check for a continuation
            tok = self.tokenizer.get_next_token()
            if self.classifier.is_any_operator(tok):
                if tok.text in ("::", '.'):
                    # Always keep going with a scope-resolution operator
                    tok2 = self.tokenizer.get_next_token()
                    if not self.classifier.is_identifier(tok2, True):
                        self.tokenizer.put_back(tok)
                        self.tokenizer.put_back(tok2)
                        break
                    tok_list.append(tok)
                    tok_list.append(tok2)
                    # Check if we're done
                    if tok.text == '.' and not tok2.text[0].isupper():
                        break
                else:
                    self.tokenizer.put_back(tok)
                    break
            else:
                self.tokenizer.put_back(tok)
                break

        return tok_list
            
# end class Parser
        
                    
if __name__ == "__main__":
    if len(sys.argv) == 1:
        sample_code = ruby_lexer.provide_sample_code();
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
    tokenizer = ruby_lexer.RubyLexer(sample_code)
    parser = Parser(tokenizer, "Ruby")
    tree = parser.parse()
    print "Analyze the parse tree"
    tree.dump()
