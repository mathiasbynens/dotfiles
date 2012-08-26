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

"""Perl parsing support for codeintel/perlcile.py"""

import copy
import os.path
import string
import sys
import re
import textwrap
import time
import cPickle
import logging

from ciElementTree import Element, SubElement, tostring
from SilverCity import ScintillaConstants
from SilverCity.ScintillaConstants import (
    SCE_PL_DEFAULT, SCE_PL_ERROR, SCE_PL_COMMENTLINE, SCE_PL_POD,
    SCE_PL_NUMBER, SCE_PL_WORD, SCE_PL_STRING, SCE_PL_CHARACTER,
    SCE_PL_PUNCTUATION, SCE_PL_PREPROCESSOR, SCE_PL_OPERATOR,
    SCE_PL_IDENTIFIER, SCE_PL_SCALAR, SCE_PL_ARRAY, SCE_PL_HASH,
    SCE_PL_SYMBOLTABLE, SCE_PL_VARIABLE_INDEXER, SCE_PL_REGEX,
    SCE_PL_REGSUBST, SCE_PL_LONGQUOTE, SCE_PL_BACKTICKS, SCE_PL_DATASECTION,
    SCE_PL_HERE_DELIM, SCE_PL_HERE_Q, SCE_PL_HERE_QQ, SCE_PL_HERE_QX,
    SCE_PL_STRING_Q, SCE_PL_STRING_QQ, SCE_PL_STRING_QX, SCE_PL_STRING_QR,
    SCE_PL_STRING_QW, SCE_PL_POD_VERB, SCE_PL_SUB, SCE_PL_SUB_ARGS,
    SCE_PL_UNKNOWN_FIELD, SCE_PL_STDIN, SCE_PL_STDOUT, SCE_PL_STDERR,
    SCE_PL_FORMAT, SCE_PL_UPPER_BOUND)

from codeintel2.common import CILEError
from codeintel2 import perl_lexer
from codeintel2 import shared_lexer
from codeintel2 import shared_parser

SCE_PL_UNUSED = shared_lexer.EOF_STYLE

log = logging.getLogger("perlcile")
#log.setLevel(logging.DEBUG)

#----  memoize from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/496879

TIMING = False # set to true to capture timing data from regexen
REGEXEN = {} # unused if TIMING is not True

def memoize(function, limit=None):
    if isinstance(function, int):
        def memoize_wrapper(f):
            return memoize(f, function)

        return memoize_wrapper

    dict = {}
    list = []
    def memoize_wrapper(*args, **kwargs):
        key = cPickle.dumps((args, kwargs))
        try:
            list.append(list.pop(list.index(key)))
        except ValueError:
            dict[key] = function(*args, **kwargs)
            list.append(key)
            if limit is not None and len(list) > limit:
                del dict[list.pop(0)]

        return dict[key]

    memoize_wrapper._memoize_dict = dict
    memoize_wrapper._memoize_list = list
    memoize_wrapper._memoize_limit = limit
    memoize_wrapper._memoize_origfunc = function
    memoize_wrapper.func_name = function.func_name
    return memoize_wrapper


class TimingRe:
    "A wrapper around compiled regexen that keeps track of timing data"
    def __init__(self, re, orig_re):
        self._re = re
        self._orig_re = orig_re
    def sub(self, *args):
        return self._timing_operation('sub', *args)
    def match(self, *args):
        return self._timing_operation('match', *args)
    def search(self, *args):
        return self._timing_operation('search', *args)
    def split(self, *args):
        return self._timing_operation('split', *args)
    def findall(self, *args):
        return self._timing_operation('findall', *args)

    def _timing_operation(self, methodname, *args):
        start = time.time()
        retval = getattr(self._re, methodname)(*args)
        end = time.time()
        delta = end-start
        #if delta > 0.01:
        #    print delta,'\t', self._orig_re, str(args)[:80]
        if self._orig_re not in REGEXEN:
            REGEXEN[self._orig_re] = 0.0
        REGEXEN[self._orig_re] += delta
        return retval

@memoize
def re_compile(regex, *args):
    """A version of re.compile which memoizes and optionally keeps track of timing
    data"""
    if TIMING:
        return TimingRe(re.compile(regex, *args), regex)
    else:
        return re.compile(regex, *args)

def re_sub(*args):
    """a version of re.sub which deals with TimingRe objects and prints out
    details of slow regexen"""
    if TIMING:
        start = time.time()
        if isinstance(args[0], TimingRe):
            retval = args[0].sub(*args[1:])
        else:
            retval = re.sub(*args)
        end = time.time()
        delta = end-start
        if delta > 0.01: #adjust as needed.
            print delta,'\t',args
    else:
        retval = re.sub(*args)
    return retval

class PerlCommonClassifier:
    """Mixin class containing classifier callbacks"""

    def is_array_cb(self, tok):
        tval = tok.text
        return len(tval) >= 2 and tval[0] == '@' and tval[1] != '$'
        # @$name is more like an expression -- don't return it

    def is_scalar_cb(self, tok):
        tval = tok.text
        return len(tval) > 1 and tval[0] == '$' and (tval[1].isalnum or tval[1] == "_")

    def is_pod_cb(self, tok):
        return tok.text[0] == '=' and tok.text[1].isalnum and tok.text.find("\n=cut", 5) > 0
    
    def is_string_qw_cb(self, tok):
        return re_compile(r'^qw\s*[^\w\d_]').match(tok.text)
                                                   

    # Used for stripping the quotes off a string
    _quote_patterns = {SCE_PL_STRING : re.compile('^[\'\"](.*)[\'\"]$'),
                       SCE_PL_CHARACTER : re.compile('^\'(.*)\'$'),
                       SCE_PL_STRING_Q : re.compile(r'^q\s*.(.*).$'),
                       SCE_PL_STRING_QQ : re.compile(r'^q\w\s*.(.*).$'),
                       SCE_PL_DEFAULT : re.compile('^.(.*).$'), #fallback
                       }

    def quote_patterns_cb(self, tok):
        # Caller wants an array.
        return [self.quote_patterns_cb_aux(tok)]

    def quote_patterns_cb_aux(self, tok):
        tval = tok.text
        if tval[0] == '"':
            return self._quote_patterns[SCE_PL_STRING]
        elif tval[0] == '\'':
            return self._quote_patterns[SCE_PL_CHARACTER]
        elif tval.startswith("Q"):
            return self._quote_patterns[SCE_PL_STRING_QQ]
        elif tval.startswith("q"):
            return self._quote_patterns[SCE_PL_STRING_Q]
        else:
            return self._quote_patterns[SCE_PL_DEFAULT] # Fallback

class UDLClassifier(PerlCommonClassifier, shared_parser.UDLClassifier):
    pass

class PerlClassifier(PerlCommonClassifier, shared_parser.CommonClassifier):
    def get_builtin_type(self, tok, callback):
        raise CILEError("Unexpected call to perl_parser.get_builtin_type")
        
    def is_any_operator(self, tok):
        return tok.style == ScintillaConstants.SCE_PL_OPERATOR

    def is_comment(self, tok):
        return tok.style in (ScintillaConstants.SCE_PL_COMMENT,
                             ScintillaConstants.SCE_PL_POD)

    def is_comment_structured(self, tok, callback):
        return tok.style == ScintillaConstants.SCE_PL_POD

    def is_identifier(self, tok, allow_keywords=False):
        return (tok.style == ScintillaConstants.SCE_PL_IDENTIFIER or
            (allow_keywords and
             tok.style == ScintillaConstants.SCE_PL_WORD))

    def is_index_op(self, tok, pattern=None):
        if not (tok.style in (SCE_PL_OPERATOR, SCE_PL_VARIABLE_INDEXER)):
            return False
        elif not pattern:
            return True
        return len(tok.text) > 0 and pattern.search(tok.text)

    def is_interpolating_string(self, tok, callback):
        return tok.style in [ScintillaConstants.SCE_PL_STRING,
                             ScintillaConstants.SCE_PL_REGEX,
                             ScintillaConstants.SCE_PL_HERE_QQ,
                             ScintillaConstants.SCE_PL_STRING_QQ,
                             ScintillaConstants.SCE_PL_STRING_QR,
                             ScintillaConstants.SCE_PL_STRING_QX
                             ]

    def is_keyword(self, tok, target):
        return tok.style == ScintillaConstants.SCE_PL_WORD and tok.text == target

    def is_number(self, tok):
        return tok.style == ScintillaConstants.SCE_PL_NUMBER

    def is_operator(self, tok, target):
        return tok.style == ScintillaConstants.SCE_PL_OPERATOR and tok.text == target

    def is_string(self, tok):
        return tok.style in [ScintillaConstants.SCE_PL_STRING,
                             ScintillaConstants.SCE_PL_CHARACTER,
                             ScintillaConstants.SCE_PL_HERE_Q,
                             ScintillaConstants.SCE_PL_HERE_QQ,
                             ScintillaConstants.SCE_PL_STRING_Q,
                             ScintillaConstants.SCE_PL_STRING_QQ,
                             ScintillaConstants.SCE_PL_STRING_QX,
                             ]

    def is_string_qw(self, tok, callback):
        return tok.style == ScintillaConstants.SCE_PL_STRING_QW

    def is_symbol(self, tok):
        return False

    def is_variable(self, tok):
        return SCE_PL_SCALAR <= tok.style <= SCE_PL_SYMBOLTABLE

    # Types of variables
    def is_variable_array(self, tok, callback=None):
        return tok.style == ScintillaConstants.SCE_PL_ARRAY and \
            len(tok.text) > 1 and tok.text[1] != '$'
        
    def is_variable_scalar(self, tok, callback=None):
        return tok.style == ScintillaConstants.SCE_PL_SCALAR and \
            len(tok.text) > 1 and tok.text[1] != '$'
        
    # Accessors for where we'd rather work with a style than call a predicate fn

    @property
    def style_identifier(self):
        return ScintillaConstants.SCE_PL_IDENTIFIER
    
    @property
    def style_word(self):
        return ScintillaConstants.SCE_PL_WORD

def _get_classifier(lang):
    """Factory method for choosing the style classifier."""
    cls = lang == "Perl" and PerlClassifier or UDLClassifier
    return cls()

# Parse Perl code

showWarnings = False

class ModuleInfo:
    def __init__(self, provide_full_docs):
        self.provide_full_docs = provide_full_docs

        self.modules = {}
        self.currentFunction = None
        self.currentNS = None
        self.textWrapper = textwrap.TextWrapper()
        self.textWrapper.width = 60
        self.max_doclet_low_water_mark = 80
        self.max_doclet_high_water_mark = 100
        self.pod_escape_seq = {'lt' : "&lt;",
                               'gt' : "&gt;",
                               'verbar' : "|",
                               'sol' : "/"}
        # Things for attrs, etc.
        self.export_string = '__exported__'
        self.export_ok_string = '__exportable__'
        self.local_string = '__local__'
        # Cached regular expressions
        self.re_bl = r'\r?\n\s*\r?\n'
        self.tryGettingDoc_Sig_re3 = re_compile(r'^=(?:item|head)\w*\s*((?:(?!\n=).)*)(?!\n=)',
                                 re.M|re.S)
        self.printDocInfo_re4 = re_compile(r'^=(?:item|head)\w*\s*((?:(?!\n=).)*)(?!\n=)', re.S|re.M)
        
        self.printDocInfo_re2 = re_compile(r'^=\w+\s+DESCRIPTION%s(.*?)(?:%s|^=)' % (self.re_bl, self.re_bl), re.M)
        self.printDocInfo_re6 = re_compile(r'^=\w+\s+SYNOPSIS' + self.re_bl + '(.*?)^=',
                                           re.M|re.S)
        self.printDocInfo_bdot_re = re_compile(r'\.\s+[A-Z].*\Z')

        self._get_first_sentence_re1 = re_compile(r'\.\s+[A-Z].*\Z', re.S)

        self._simple_depod_e_re = re_compile(r'E<(.*?)>', re.S)
        self._simple_depod_c_re = re_compile(r'C<{2,}\s*(.*?)\s*>{2,}', re.S)
        self._simple_depod_ibcfsxl_re1 = re_compile(r'[IBCFSXL]<[^>\n]*>')
        self._simple_depod_ibcfsxl_re2 = re_compile(r'[IBCFSX]<(<*[^<>]*?>*)>', re.S)
        self._simple_depod_l_re = re_compile(r'L<\/?(.*?)>')
        self._simple_depod_rest_re = re_compile(r'\w<\/?(<*.*?>*)>')

        self._depod_re1 = re_compile(r'^=begin\s+man\s+.*?^=end\s+man\s*', re.M|re.S)
        self._depod_re2 = re_compile(r'^=\w+\s*', re.M)
        self._depod_re3 = re_compile(r'\]\]>')
        self._depod_re4 = re_compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')

        self.trim_ws_re1 = re_compile(r'(?<=\w[\.\!\?])\s+')
        self.trim_ws_re2 = re_compile(r'[\r\n\t]')
        self.trim_ws_re3 = re_compile(r' {2,}')

        self.printFunctions_re1 = re_compile(r'(\S)\s*\n(?:\s*\n)*\s*(\S)')
    
    def doStartNS(self, ns):
        name = ns.name
        if not self.modules.has_key(name):
            self.modules[name] = ns
        self.currentNS = ns
        
    def doEndNS(self, **attrInfo):
        if attrInfo.has_key('lineNo'):
            self.currentNS.lineend = attrInfo['lineNo']
        self.currentNS = None
        
    def getNS(self, name, **attrInfo):
        if self.modules.has_key(name):
            return self.modules[name]
        else:
            return NamespaceInfo(name, **attrInfo)
        
    def doSetArg(self, name):
        self.currentFunction.aArg[name] = []
        self.currentFunction.argList.append(name)
        
    def doSetParent(self, **attrInfo):
        ns = attrInfo.get('ns')
        if ns:
            self.currentNS.aParent.append(ns)
            
    def doStartFn(self, fn):
        self.currentFunction = fn
        
    def doEndFn(self, **attrInfo):
        if attrInfo.has_key('lineNo'):
            self.currentFunction.lineend = attrInfo.get('lineNo')
        self.currentNS.aFunc.append(self.currentFunction)
        self.currentFunction = None
        
    def doStartVar(self, **attrInfo):
        self.thisVar = {}
        self.thisVar['name'] = attrInfo.get('name')
        for field in ['line', 'aType', 'scope']:
            if attrInfo.has_key(field):
                self.thisVar[field] = attrInfo[field]
    
    def doEndVar(self, forceGlobal):
        name = self.thisVar['name']
        if (not forceGlobal) and self.currentFunction:
            if self.currentFunction.aArg.has_key(name):
                self.currentFunction.aArg[name].append(self.thisVar)
            else:
                self.set_or_append(self.currentFunction.aVar, name, self.thisVar)
        else:
            self.set_or_append(self.currentNS.aVar, name, self.thisVar)
        del self.thisVar
        
    def set_or_append(self, obj, name, val):
        if obj.has_key(name):
            obj[name].append(val)
        else:
            obj[name] = [val]
            
    def doSetVar(self, **args):
        if args.has_key('forceGlobal'):
            forceGlobal = args['forceGlobal']
            del args['forceGlobal']
        else:
            forceGlobal = False
        self.doStartVar(**args)
        self.doEndVar(forceGlobal)

    def add_imported_module(self, args, **kwargs):
        args2 = copy.copy(args)
        args2.update(kwargs)
        if self.currentFunction:
            self.currentFunction.aImports.append(args2)
        else:
            self.currentNS.aImports.append(args2)
    
    def printDocInfo(self, modInfo, funcInfo, currNode):
        docs = modInfo.hDocs['modules']
        modName = modInfo.name
        # These REs need rebuilding each time, as their values change on each call.
        printDocInfo_re1 = re_compile(r'^=\w+\s+NAME%s%s[\s-]+(.*?)(?:%s|^=)' %
                                      (self.re_bl, modName, self.re_bl), re.M)
            
        try:
            mainDocs = self.modules['main'].hDocs['modules'] or []
        except:
            mainDocs = []
        finalDoc = None
        if not funcInfo:
            # Just dump the module-level docs for now,
            # but favor extracting the synopsis.
            #
            # First, find the first item with a synopsis
            #
            # Otherwise, go with the first one.
            for doc in docs:
                m1 = printDocInfo_re1.search(doc)
                if m1:
                    finalDoc = self.trim_ws(m1.group(1), True)
                    break
                else:
                    m2 = self.printDocInfo_re2.search(doc)
                    if m2:
                        finalDoc = self.trim_ws(m2.group(1), True)
                        break
            if finalDoc is None:
                # Look only for a qualified name in the NAME section,
                # but don't look at the DESCRIPTION part until we can
                # select the main class in a module.
                for doc in mainDocs:
                    m1 = printDocInfo_re1.search(doc)
                    if m1:
                        finalDoc = self.trim_ws(m1.group(1), True)
                        break
        else:
            # First look for the function name in an item
            # Then look in the synopsis.
            # Look for a top-level synopsis first
            funcName = funcInfo.name
            # Allow for datasection-based POD\
            if docs:
                re3_s = (r'''
                                ((?:^=(?:item|head)\w*\s*\r?\n(?:\s*\r?\n)*
                                .*?(?:%s\s*::|%s\s*->|\$[\w_]+\s*->|[ \t]+)
                                %s(?![\w\d_]).*\r?\n\s*\r?\n)+)
                                # Now the description
                                # Everything up to the an equal-sign (or end)
                                ((?:\r?\n|.)*?)(?:^=|\Z)''' %
                                (modName, modName, funcName))
                printDocInfo_re3 = re_compile(re3_s, re.X|re.M)
                for doc in docs:
                    # Speed up: do index before doing a reg
                    if doc.find(funcName) == -1:
                        continue
                    # Find a function definition in an item or head thing
                    # Very general-purpose, might pick up false-positives
                    # The gist:
                    # Look for one or more =item/head lines,
                    # separate by blank lines,
                    # followed by a paragraph description
                    m1 = printDocInfo_re3.search(doc)
                    if m1:
                        part1 = m1.group(1)
                        finalDoc = self.trim_ws(m1.group(2), True)
                        part2 = [self.trim_ws(s, True) for s in self.printDocInfo_re4.findall(part1)]
                        finalDoc = "\n\n".join(part2) + "\n\n" + finalDoc
                        finalDoc = self._get_first_sentence(finalDoc)
                        break
            if not finalDoc:
                # Look in the __END__ section
                # XXXX VERY SLOW
                re1_s = r'''(?:^(?:item|head)\w*\s*
                           .*?
                           \b%s.*%s)+
                            # Now the description
                            # Everything up to the an equal-sign (or end)
                            ((?:\r?\n|.)*?)(?=$|^=)''' % (funcName, self.re_bl)
                printDocInfo_re1 = re_compile(re1_s, re.M|re.X)
                for doc in mainDocs:
                    m1 = printDocInfo_re1.search(doc)
                    if m1:
                        before_period = self.printDocInfo_bdot_re.sub('.', m1.group(1))
                        finalDoc = self.trim_ws(self._get_first_sentence(m1.group(1)), True)
                        break
            if not finalDoc:
                # Try to find a synopsis entry
                printDocInfo_re7 = re_compile(r'(.*(?:::|->|\b)%s\b.*)' % (funcName,))
                for doc in docs + mainDocs:
                    m1 = self.printDocInfo_re6.search(doc)
                    if m1:
                        synopsis = m1.group(1)
                        m2 = printDocInfo_re7.search(synopsis)
                        if m2:
                            finalDoc = self.trim_ws(self._get_first_sentence(m2.group(1)))
                            break
        if finalDoc:
            self.printDocString(finalDoc, currNode)
            
    def _get_first_sentence(self, s1):
        s2 = self._get_first_sentence_re1.sub('.', s1)
        return s2
    
    def printDocString(self, finalDoc, currNode):
        finalDoc2 = self._depod(finalDoc)
        if finalDoc2:
            currNode.set('doc', finalDoc2)
        
    def _process_e_pod(self, src):
        val = self.pod_escape_seq.get(src.lower())
        if val: return val
        if re.search(r'^\d+$', src):
            return '&#%s;' % src
        m1 = re.search(r'^0[Xx]([0-9a-fA-F]+)$', src)
        if m1:
            return '&#x%s;' % src
        else:
            # Assume it's an entity name of somekind,
            # and return it as an escaped representation
            # For example, pod E<eacute> will be encoded as
            #                  &amp;eacute;
            # and will appear as
            #                  &eacute;
            # Not great, but it causes no breakage.
            return '&amp;%s' % src
        
    def _wrap_process_e_pod(self, m):
        return self._process_e_pod(m.group(1))
        
    def _simple_depod(self, doc):
        # Simple inline-markup removal (doesn't handle nested inlines)
        # In Perl, do this:
        # $doc =~ s/E<(.*?)>/_process_e_pod($1)/eg;

        doc = re_sub(self._simple_depod_e_re, self._wrap_process_e_pod, doc)

        # And handle the inline codes-- thse nest with E codes...
        
        doc = self._simple_depod_c_re.sub(r'\1', doc)

        # Above code replaces this:
        # doc = re_sub(r'C<{2,}\s+(.*?)\s+>{2,}', r'\1', doc)
        # doc = XmlAttrEscape(doc) -- No longer needed with ElementTree
            
        # Allow the other sequences to nest, and loop until there
        # aren't any left.
        
        old_doc = doc
        while self._simple_depod_ibcfsxl_re1.search(doc):
            # Most formatting sequences wrap a single clump of code
            doc = self._simple_depod_ibcfsxl_re2.sub(r'\1', doc)
            # Handling of links - this is more complicated.
            doc = self._simple_depod_l_re.sub(r'\1', doc)
    
            # We need to make sure we pull out when nothing changes.
            #XXX A log message would be useful here.
            if old_doc != doc:
                old_doc = doc
            else:
                break
        # Remove any unrecognized sequences
        doc = self._simple_depod_rest_re.sub(r'\1', doc)

        # And shrink entities back into strings.
        # This is done because we can't convert constructs like
        # E<gt> into ">" directly, because they'll prevent
        # proper handling of outer C<...> in strings like 'C<if (a E<gt> b) { ...>'
        doc = doc.replace("&lt;", "<").replace("&gt;", ">")
        return doc

# Precondition: this text is emitted inside a cdata-section

    def _depod(self, doc):
        # Remove embedded man directives
        doc1 = self._depod_re1.sub('', doc)
    
        # Pull out leading equal signs and the directives
        doc2 = self._depod_re2.sub('', doc1)
        doc3 = self._simple_depod(doc2)
        # Handle strings that could cause the XML parser trouble
        doc4 = self._depod_re3.sub(']<!>]>', doc3)
        doc5 = self._depod_re4.sub('?', doc4)
        return doc5
        
    def trim_ws(self, str1, truncate=False):
        # First split into sentences
        str2 = str1.strip()
        if truncate:
            sentences = self.trim_ws_re1.split(str2)
            keep_sentences = []
            sum = 0
            # Keep sentences until we pass max_doclet_high_water_mark chars.
            for s in sentences:
                thisLen = len(s)
                if sum and sum + thisLen > self.max_doclet_high_water_mark:
                    break
                s1 = self.trim_ws_re2.sub(' ', s)
                s2 = self.trim_ws_re3.sub(' ', s1)
                keep_sentences.append(s2)
                sum += thisLen
                if sum > self.max_doclet_high_water_mark:
                    break
            str2 = "  ".join(keep_sentences)
        
        if str2.find("\n") >= 0 or len(str2) > self.textWrapper.width * 1.1:
            str2 = "\n".join(self.textWrapper.wrap(str2))
        return str2

    def printClassParents(self, modInfo, currNode):
        if not hasattr(modInfo, 'aParent'): return
        classrefs = [info[0] for info in modInfo.aParent]
        if len(classrefs) > 0:
            currNode.set('classrefs', " ".join(classrefs))
            
    def printImports(self, modInfo, currNode):
        # -- this will be correct only when there are deliberate conflicts
        # better to use object inheritance to choose methods dynamically.
        #imports = getattr(modInfo, 'aImports', [])
        #imports.reverse()
        for _import in getattr(modInfo, 'aImports', []):
            attrs = _import.keys()
            importNode = SubElement(currNode, "import")
            for k in attrs:
                importNode.set(k, str(_import[k]))
            
    def printTypeInfo(self, argInfo, currNode):
        types={}
        for type_ in argInfo:
            typeInfo = type_.get('aType')
            if not typeInfo:
                continue
            elif not typeInfo.has_key('assign'):
                continue
            tp = typeInfo['assign']
            if types.has_key(tp):
                continue
            types[tp] = None
            currNode.set('citdl', tp)
            
    def printVariables(self, modInfo, currNode):
        if not hasattr(modInfo, 'aVar'): return
        def sorter1(a,b):
            return (cmp(a[0]['line'], b[0]['line']) or
                    cmp(a[0]['name'].lower(), b[0]['name'].lower()))
                   
        variables = modInfo.aVar.values()
        variables.sort(sorter1)
        try:
            export_info = modInfo.export_info
        except:
            if not hasattr(self, 'default_export_info'):
                self.default_export_info = {'@EXPORT':{},'@EXPORT_OK':{}}
            export_info = self.default_export_info
        for varInfo in variables:
            var_name = varInfo[0]['name']
            varNode = SubElement(currNode, 'variable', line=str(varInfo[0]['line']),
                                 name=var_name)
            attr_parts = []
            if export_info['@EXPORT'].has_key(var_name):
                attr_parts.append(self.export_string)
            if export_info['@EXPORT_OK'].has_key(var_name):
                attr_parts.append(self.export_ok_string)
            try:
                if varInfo[0]['scope'] == 'my':
                    attr_parts.append(self.local_string)
            except:
                pass
            if attr_parts:
                varNode.set('attributes', ' '.join(attr_parts))
            self.printTypeInfo(varInfo, varNode)
    
    def printFunctions(self, modInfo, currNode):
        for funcInfo in getattr(modInfo, 'aFunc', []):
            sig, docString = self.tryGettingDoc_Sig(modInfo, funcInfo)
            funcName = funcInfo.name
            if not sig:
                sig = '%s(%s)' % (funcName, ', '.join(funcInfo.argList))
            else:
                sig = self._simple_depod(sig.strip())
                sig = self.printFunctions_re1.sub('\\1\n\\2', sig)
            funcNode = SubElement(currNode, 'scope', ilk='function', name=funcName)
            for attr_name in ['line', 'lineend']:
                ln = getattr(funcInfo, attr_name, None)
                if ln:
                    funcNode.set(attr_name, str(ln))
    
            attr_parts = []
            if funcInfo.isConstructor:
                attr_parts.append("__ctor__")
            export_info = modInfo.export_info
            for tuple in [['@EXPORT', self.export_string],
                          ['@EXPORT_OK', self.export_ok_string]]:
                if export_info[tuple[0]].has_key(funcName):
                    attr_parts.append(tuple[1])
            if attr_parts:
                funcNode.set('attributes', ' '.join(attr_parts))

            funcNode.set('signature', sig)
            
            for argName in funcInfo.argList:
                argInfo = funcInfo.aArg.get(argName)
                if argInfo:
                    argNode = SubElement(funcNode, 'variable', ilk='argument', name=argInfo[0]['name'])
                    self.printTypeInfo(argInfo, argNode)
            if self.provide_full_docs:
                if not docString:
                    self.printDocInfo(modInfo, funcInfo, funcNode)
                else:
                    self.printDocString(docString, funcNode)
            self.printImports(funcInfo, funcNode)
            self.printVariables(funcInfo, funcNode)
            
    def tryGettingDoc_Sig(self, modInfo, funcInfo):
        if not self.provide_full_docs:
            return (None, None)
        modName = modInfo.name
        funcName = funcInfo.name
        re1_s = r"""((?:^=(?:item|head)\w*\s*
                       .*?(?:%s\s*\:\:|%s\s*->|\$[\w_]+\s*->|[ \t])
                       %s(?:[^\w_]|$).*%s)+)
                      # Now the description
                      # Everything up to the an equal-sign (or end)
                      ((?:\r?\n|.)*?)(?:^=|\Z)""" % \
                         (modName, modName, funcName, self.re_bl)
        re1 = re_compile(re1_s, re.X|re.M)
        re2a = re_compile(funcName + r'\s+\w')
        re2b = re_compile(r'\s\w+\s+' + funcName + r'\b')
        re4_s = (r'''^=(?:item|head)\s*\*?\s*\r?\n
                        (?:^\s*\r?\n)*
                        ^\s*C<+(.*%s.*)>+\s*\r?\n
                        (?:^\s*\r?\n)*
                        # Now the description
                        # Everything up to the an equal-sign (or end)
                        ((?:.*\r?\n(?!=))+)''' % (funcName,))
        re4 = re_compile(re4_s, re.M|re.X)
        for doc in modInfo.hDocs['modules'] + self.modules['main'].hDocs['modules']:
            if doc.find(funcName) == -1:
                continue
            m1 = re1.search(doc)
            if m1:
                part1 = m1.group(1)
                # If the function name is followed by text, it's probably
                # an English description.  We need to check for a whole word
                # before the name to avoid the pod directive
                if (re2a.search(part1) or
                    re2b.search(part1)):
                    continue
                finalDoc = self.trim_ws(self._get_first_sentence(m1.group(2)), True)
                part2 = [s.strip() for s in self.tryGettingDoc_Sig_re3.findall(part1)]
                finalSig = (part2 and "\n\n".join(part2)) or None
                return (finalSig, finalDoc)
            else:
                m1 = re4.search(doc)
                if m1:
                    finalSig = m1.group(1)
                    finalDoc = self.trim_ws(self._get_first_sentence(m1.group(2)), True)
                    return (finalSig, finalDoc)
        return (None, None)
    
class NamespaceInfo:
    def __init__(self, name, **attrInfo):
        self.name = name
        self.line = attrInfo.get('lineNo') or 0
        self.aFunc = []
        self.aVar = {}
        self.aParent = []
        self.hDocs = {'modules':[], # hash of modules => array of docs,
                      'subs':{}     # subs => subname => array of docs
        }
        self.aImports = []
        self._isProbablyClass = False
        self.export_info = {'@EXPORT':{},
                            '@EXPORT_OK':{}}

    def isProbablyClass(self, val):
        self._isProbablyClass = val

class FunctionInfo:
    def __init__(self, name, **attrInfo):
        self.name = name
        self.aArg = {}
        self.aVar = {}
        self.resultType = []
        self.argList = []
        self.aImports = []
        self.isConstructor = attrInfo.get('isConstructor', False)
        if attrInfo.has_key('lineNo'):
            self.line = attrInfo.get('lineNo')
    
if not os.path.altsep or os.path.altsep == os.path.sep:
    def pathSplitter(s):
        return s.split(os.path.sep)
else:
    def pathSplitter(s):
        return re.split(re_compile('[' + re.escape(os.path.sep)
                                   + re.escape(os.path.altsep) + ']'), s)

class Parser:
    def __init__(self, tokenizer, lang="Perl", provide_full_docs=True):
        self.tokenizer = tokenizer
        self._provide_full_docs = provide_full_docs
        self.block_stack = []
        self.bracket_matchers = {"[":"]", "{":"}", "(":")"}
        self.classifier = _get_classifier(lang)
        
        # Use simple knowledge of Perl's syntax
        # to skip quickly through code to skip.
        self.opHash = {"(" : [0, 1],
                ")" : [0, -1],
                "{" : [1, 1],
                "}" : [1, -1],
                "[" : [2, 1],
                "]" : [2, -1]}

        self.pragmaNames = {'attributes' : None,
                            'attrs' : None,
                            'autouse' : None,
                            'bigint' : None,
                            'bignum' : None,
                            'bigrat' : None,
                            'blib' : None,
                            'bytes' : None,
                            'charnames' : None,
                            'constant' : None,
                            'diagnostics' : None,
                            'encoding' : None,
                            'fields' : None,
                            'filetest' : None,
                            'if' : None,
                            'integer' : None,
                            'less' : None,
                            'lib' : None,
                            'locale' : None,
                            'open' : None,
                            'ops' : None,
                            'overload' : None,
                            're' : None,
                            'sigtrap' : None,
                            'sort' : None,
                            'strict' : None,
                            'subs' : None,
                            'threads' : None,
                            'utf8' : None,
                            'vmsish' : None,
                            'warnings' : None,
                            }
        self.find_open_indexer_re = re_compile(r'[\[{]')
        self.provide_full_docs = provide_full_docs

    def _is_stmt_end_op(self, tok):
        tval = tok.text
        if self.classifier.is_keyword(tok, 'or'):
            return True
        elif self.classifier.is_any_operator(tok):
            return tval in (';', '||')
        return False

    def _is_string(self, tok):
        return tok.style in self.tokenizer.string_types
        
        
    def printHeader(self, mtime):
        moduleName = self.moduleName
        root = Element("codeintel", version="2.0")
        fileNode = Element("file", lang="Perl",
                           path=moduleName)
        if mtime:
            fileNode.set('mtime', str(mtime))
        root.append(fileNode)
        return (root, fileNode)
        
    def printContents(self, moduleContentsName, currNode):
        name = os.path.splitext(os.path.basename(self.moduleName))[0]
        moduleNode = SubElement(currNode, 'scope', ilk='blob', lang="Perl", name=name)
        
        innerModules = self.moduleInfo.modules
        mainInfo = innerModules.get('main', None)
        if mainInfo:
            if self.provide_full_docs:
                self.moduleInfo.printDocInfo(mainInfo, None, moduleNode)
            self.moduleInfo.printImports(mainInfo, moduleNode)
            self.moduleInfo.printVariables(mainInfo, moduleNode)
        
        def sorter1(a,b):
            amod = innerModules.get(a)
            bmod = innerModules.get(b)
            aline = getattr(amod, 'line', None)
            if aline:
                bline = getattr(bmod, 'line', None)
                if aline and bline: return cmp(aline, bline)
            return cmp(getattr(amod, 'name', ""), getattr(bmod, 'name', ""))
        
        # Sub-packages need to updated their parent blob name - bug 88814.
        # I.e. when parsing "XML/Simple.pm" the blob name is "Simple", but we
        #      need it be "XML::Simple" in this case. The bestPackageName is
        #      used to find the best matching name.
        packages = [x for x in self.moduleInfo.modules.keys() if x != 'main']
        packages.sort(sorter1)
        bestPackageName = None
        for k in packages:
            modInfo = innerModules[k]

            if name in k and \
               (bestPackageName is None or len(bestPackageName) > k):
                bestPackageName = k
                moduleNode.set("name", bestPackageName)

            classNode = SubElement(moduleNode, 'scope', ilk='class', name=modInfo.name, line=str(modInfo.line))
            if hasattr(modInfo, 'lineend'):
                classNode.set('lineend', str(modInfo.lineend))
            self.moduleInfo.printClassParents(modInfo, classNode)
            if self.provide_full_docs:
                self.moduleInfo.printDocInfo(modInfo, None, classNode)
            self.moduleInfo.printImports(modInfo, classNode)
            self.moduleInfo.printVariables(modInfo, classNode)
            self.moduleInfo.printFunctions(modInfo, classNode)

        # And do main's functions after its classes
        if mainInfo:
            self.moduleInfo.printFunctions(mainInfo, moduleNode)

    def printTrailer(self, root):
        pass

    def at_end_expression(self, tok):
        if not self.classifier.is_any_operator(tok):
            return False
        return tok.text in (';', ',', '}')

        
    def collect_multiple_args(self, origLineNo, context, var_scope):
        nameList = []
        while True:
            tok = self.tokenizer.get_next_token()
            if self.classifier.is_variable(tok):
                nameList.append((tok.text, tok.start_line))
            else:
                break
            tok = self.tokenizer.get_next_token()
            if self.classifier.is_any_operator(tok):
                tval = tok.text
                if tval == ")": break
                elif tval != ",": break
        if not self.classifier.is_operator(tok, ")"):
            return
        tok = self.tokenizer.get_next_token()
        isArg = False
        if self.classifier.is_operator(tok, "="):
            tok = self.tokenizer.get_next_token()
            if self.classifier.is_variable_array(tok, self.classifier.is_array_cb) and tok.text == "@_":
                tok = self.tokenizer.get_next_token()
                isArg = self._is_stmt_end_op(tok)
            else:
                tok = self.tokenizer.put_back(tok)
        for varInfo in nameList:
            if isArg: self.moduleInfo.doSetArg(varInfo[0])
            self.moduleInfo.doSetVar(name=varInfo[0], line=varInfo[1],
                                     scope=var_scope)
    # end collect_multiple_args
    
    # Expect = shift ;
    def collect_single_arg(self, varName, origLineNo, context, var_scope):
        tok = self.tokenizer.get_next_token()
        if not self.classifier.is_operator(tok, '='):
            isArg = False
        else:
            tok = self.tokenizer.get_next_token()
            if self.classifier.is_keyword(tok, 'shift') or tok.text == '@_':
                tok = self.tokenizer.get_next_token()
                isArg = self._is_stmt_end_op(tok)
                self.tokenizer.put_back(tok)
            else:
                self.tokenizer.put_back(tok)
                self.finish_var_assignment(varName, origLineNo, False,
                                           scope=var_scope, context=context)
                return
        if isArg:
            self.moduleInfo.doSetArg(varName)
        self.moduleInfo.doSetVar(name=varName, line=origLineNo,
                                 scope=var_scope)
        
    def de_quote_string(self, tok):
        tval = tok.text
        patterns = self.classifier.get_quote_patterns(tok, self.classifier.quote_patterns_cb)
        for p in patterns:
            m = p.match(tval)
            if m:
                return m.group(1)
        return tval
    
    # Called from both assignments and
# my <var> = ... statements, where the RHS isn't 'shift' or '@_';
    def finish_var_assignment(self, identifier, origLineNo, forceGlobal, **inherited_args):
        tok = self.tokenizer.get_next_token()
    
        # Narrow down to these possibilities:
    
        # 1. We're assigning a method call to a scalar
    
        # $lhs = $rhs->method()->{property}->...
        #
        # Reduces to
        # $lhs = $rhs
        
        # 2. We're assigning a string/int -- i.e., it's likely
        # to be a non-object value:
        
        # $lhs = "acb" eq $q
        # $lhs = $r
        # $lhs = 42
        
        # 3. We're assigning a constructor
        # Now we can take two forms:
        # <constructor> <subpath>
        # <subpath> -> <constructor>
        # Note that if we don't know anything about the module, we can't say
        # anything intelligent about Package::Midd::Function -- we don't know
        # if this returns a constructor or not, although it likely doesn't.
        
        rhs_StarterVal = None
        args = { 'name':identifier, 'line':origLineNo,
                'forceGlobal':forceGlobal }
        if inherited_args:
            args.update(inherited_args)
        ttype = tok.style
        if self.classifier.is_variable_scalar(tok, self.classifier.is_scalar_cb):
            rhs_StarterVal = tok.text
            tok = self.tokenizer.get_next_token()
            # Check and skip indexers
            if self.classifier.is_index_op(tok, self.find_open_indexer_re):
                self.skip_to_close_match()
                tok = self.tokenizer.get_next_token()
                
            # Now get the list of accessors that take us to the
            # semi-colon or close-brace.  Hop over arg lists.
            # Left looking at ->, ;, }, or leave
            
            accessors = []
            while self.classifier.is_operator(tok, "->") or self.classifier.is_index_op(tok, self.find_open_indexer_re):
                if tok.text == "->":
                    tok = self.tokenizer.get_next_token()
                if self.classifier.is_index_op(tok, self.find_open_indexer_re):
                    propertyName = self._get_property_token()
                    if not propertyName:
                        break
                    accessors.append(propertyName)
                    tok = self.tokenizer.get_next_token()
                elif not self.classifier.is_identifier_or_keyword(tok):
                    break
                else:
                    fqName = self.get_rest_of_subpath(tok.text, 1)
                    accessors.append(fqName)
                    tok = self.tokenizer.get_next_token()
                if self.classifier.is_operator(tok, "("):
                    self.skip_to_close_paren()
                    tok = self.tokenizer.get_next_token()
            # end while
            
            if accessors or self.at_end_expression(tok):
                if self.at_end_expression(tok):
                    self.tokenizer.put_back(tok)
                fqname = (accessors and rhs_StarterVal.join(accessors)) or rhs_StarterVal
            self.moduleInfo.doSetVar(**args)
            
        elif self.classifier.is_number(tok):
            #XXX: Any expressions starting with an integer that
            # don't yield an int value?
            tok = self.tokenizer.get_next_token()
            if self.at_end_expression(tok):
                self.tokenizer.put_back(tok)
            self.moduleInfo.doSetVar(**args)
        elif self._is_string(tok):
            tok = self.tokenizer.get_next_token()
            if self.at_end_expression(tok):
                self.tokenizer.put_back(tok)
            self.moduleInfo.doSetVar(**args)
        elif self.classifier.is_identifier(tok):
            rhs_StarterVal = tok.text
            tok = self.tokenizer.get_next_token()
            updateVarInfo = None
            if self.classifier.is_operator(tok, "::"):
                # Package->method  or Package::method notation
                rhs_StarterVal = self.get_rest_of_subpath(rhs_StarterVal + '::', 0)
                tok = self.tokenizer.get_next_token()
            if self.classifier.is_operator(tok, "->"):
                # a->b is always good
                tok = self.tokenizer.get_next_token()
                if self.classifier.is_identifier_or_keyword(tok) and tok.text == "new":
                    # 80/20 rule: assume a new on a class gives an instance
                    args['aType'] = {'assign' : rhs_StarterVal }
            elif self.classifier.is_identifier_or_keyword(tok):
                if rhs_StarterVal.find("::") > -1:
                    # obj A::B is always good
                    pass
                elif rhs_StarterVal == 'new':
                    # 80/20 rule
                    package_name = tok.text
                    tok = self.tokenizer.get_next_token()
                    if self.classifier.is_operator(tok, "::"):
                        # new Package notation
                        package_name = self.get_rest_of_subpath(package_name + '::', 0)
                        tok = self.tokenizer.get_next_token()
                    args['aType'] = {'assign' : package_name }
            self.moduleInfo.doSetVar(**args)
        elif self.classifier.is_keyword(tok, 'bless') and self.moduleInfo.currentFunction:
            self.moduleInfo.currentFunction.isConstructor = True
            self.moduleInfo.doSetVar(**args)
        elif self.classifier.is_keyword(tok, 'new'):
            tok = self.tokenizer.get_next_token()
            if self.classifier.is_identifier(tok):
                package_name = tok.text
                tok = self.tokenizer.get_next_token()
            else:
                package_name = ""
            if self.classifier.is_operator(tok, "::"):
                package_name = self.get_rest_of_subpath(package_name + '::', 0)
            if package_name != "":
                args['aType'] = {'assign': package_name}
                self.moduleInfo.doSetVar(**args)
        else:
            self.moduleInfo.doSetVar(**args)
            if self.classifier.is_index_op(tok, self.find_open_indexer_re):
                self.tokenizer.put_back(tok)
    # end finish_var_assignment
    
    def get_exported_names(self, export_keyword):
        tok = self.tokenizer.get_next_token()
        if not self.classifier.is_operator(tok, '='):
            self.tokenizer.put_back(tok)
            return
        names = self.get_list_of_strings()
        for obj in names:
            name = obj[0]
            if name[0] == '&': name = name[1:]
            self.moduleInfo.currentNS.export_info[export_keyword][name] = None
    # end export_keyword

    def get_for_vars(self):
        tok = self.tokenizer.get_next_token()
        if (tok.style == ScintillaConstants.SCE_PL_WORD
            and tok.text in ('my', 'state')):
            tlineNo = tok.start_line
            tok = self.tokenizer.get_next_token()
            if self.classifier.is_variable(tok):
                # Don't do any more processing, as we're probably looking
                # at an open-paren.
                self.moduleInfo.doSetVar(name=tok.text, line=tlineNo, scope='my')
    
    def get_list_of_var_names(self):
        resArray = []
        while 1:
            tok = self.tokenizer.get_next_token()
            if self.classifier.is_variable(tok):
                resArray.append([tok.text, tok.start_line])
            else:
                break
            tok = self.tokenizer.get_next_token()
            if not self.classifier.is_operator(tok, ","):
                break
        return resArray
    
    def get_list_of_strings(self, tok=None):
        if tok is None:
            tok = self.tokenizer.get_next_token()
        if self.classifier.is_operator(tok, "("):
            resArray = []
            while 1:
                # Simple -- either a string or a qw here as well
                tok = self.tokenizer.get_next_token()
                if self._is_string(tok):
                    resArray += self.get_string_array(tok)
                else:
                    break
                tok = self.tokenizer.get_next_token()
                if self.classifier.is_any_operator(tok):
                    if tok.text == ")":
                        break
                    elif tok.text == ",":
                        continue
                    break
        elif self._is_string(tok):
            resArray = self.get_string_array(tok)
        else:
            return []
        return resArray
    # end get_list_of_strings
    
    def get_our_vars(self, context, var_scope):
        tok = self.tokenizer.get_next_token()
        varNames = []
        if self.classifier.is_operator(tok, "("):
            varNames = self.get_list_of_var_names()
        elif self.classifier.is_variable(tok):
            tval = tok.text.strip()
            if tval == '@ISA':
                self.get_parent_namespaces(True)
            else:
                lineNo = tok.start_line
                tok = self.tokenizer.get_next_token()
                if self.classifier.is_operator(tok, "="):
                    self.finish_var_assignment(tval, lineNo, 0, scope=var_scope, context=context)
                    return
                varNames = [(tval, lineNo)]
        for varInfo in varNames:
            self.moduleInfo.doSetVar(name=varInfo[0], line=varInfo[1], scope=var_scope)
    
    # Look for = stringList...
    def get_parent_namespaces(self, doingIsa):
        tok = self.tokenizer.get_next_token()
        if doingIsa:
            if not self.classifier.is_operator(tok, '='):
                self.tokenizer.put_back(tok)
                return
        parentNamespaces = self.get_list_of_strings()
        for parentInfo in parentNamespaces:
            self.moduleInfo.currentNS.aParent.append(parentInfo)
            
        # Undocumented attribute, but it means one of the methods
        # should either invoke bless, SUPER:: ..., or a parent
        # constructor.
        self.moduleInfo.currentNS.isProbablyClass(True)
    # end get_parent_namespaces
    
    # Precondition: saw ident, "->", '{'
    # Still looking at the "{"
    def _get_property_token(self):
        tok = self.tokenizer.get_next_token()
        if self._is_string(tok):
            finalVal = self.de_quote_string(tok)
        elif not (self.classifier.is_identifier_or_keyword(tok) or
                  self.classifier.is_variable_scalar(tok, self.classifier.is_scalar_cb)):
            return ""
        else:
            finalVal = tok.text
        tok = self.tokenizer.get_next_token()
        
        if not self.classifier.is_index_op(tok, re_compile(r'\}')):
            # Swallow the close-brace for the property.
            finalVal = "???";
            # Consume everything until we find the close-brace
            while True:
                tok = self.tokenizer.get_next_token()
                if tok.style == SCE_PL_UNUSED:
                    break
                elif self.classifier.is_index_op(tok, re_compile(r'[\}\]]')):
                    break
        return finalVal

    def get_rest_of_subpath(self, retval, expectingDblColon):
        if expectingDblColon:
            tok = self.tokenizer.get_next_token()
            ttype = tok.style
            tval = tok.text
            if not self.classifier.is_operator(tok, "::"):
                self.tokenizer.put_back(tok)
                return retval
            else:
                retval += "::"
            
        while 1:
            tok = self.tokenizer.get_next_token()
            ttype = tok.style
            if not self.classifier.is_identifier(tok):
                if ttype != self.classifier.style_word or len(retval) == 0:
                    break
            retval += tok.text
            tok = self.tokenizer.get_next_token()
            if not self.classifier.is_operator(tok, "::"):
                break
            retval += "::"
            
        self.tokenizer.put_back(tok)
        return retval
    # end get_rest_of_subpath
    
    def get_string_array(self, tok):
        if self.classifier.is_string_qw(tok, self.classifier.is_string_qw_cb):
            res = []
            qw_re = re_compile(r'\Aqw\s*.(.*)\s*\S\s*\Z', re.DOTALL)
            match_res = qw_re.match(tok.text)
            if match_res:
                wordsPart = match_res.group(1)
                # Find first line of token
                finalLineNo = tok.start_line
                for line in wordsPart.split('\n'):
                    for var in re.split(r'\s', line):
                        if re_compile(r'\s*$').match(var):
                            continue
                        res.append((var, finalLineNo))
                    finalLineNo += 1
            return res
        else:
            tval = self.de_quote_string(tok)
            return [(tval, tok.start_line)]
        
    def get_used_vars(self, scope):
        tok = self.tokenizer.get_next_token()
        if self._is_string(tok):
            varNames = self.get_list_of_strings(tok)
        elif self.classifier.is_operator(tok, "("):
            varNames = self.get_list_of_strings()
        else:
            varNames = self.get_list_of_var_names()
        for varInfo in varNames:
            self.moduleInfo.doSetVar(name=varInfo[0],
                                     line=varInfo[1],
                                     scope=scope)
    
    def look_for_object_var_assignment(self, tok, isInnerSub):
        identifier = tok.text
        if re_compile(r'^\$[^_\w]').match(identifier) or identifier == '$_':
            # Ignore special variables, and $#$... array ref final-item index
            return
        origLineNo = tok.start_line
        tok = self.tokenizer.get_next_token()
        if not self.classifier.is_index_op(tok):
            self.tokenizer.put_back(tok)
            return
        elif tok.text != '=':
            self.tokenizer.put_back(tok)
            return
        # Is it an implicit global?
        checkGlobalScope = True
        forceGlobal = False
        #XXX Update, check this
        if self.moduleInfo.currentFunction:
            # Is it defined in the current function?
            if (self.moduleInfo.currentFunction.aVar.has_key(identifier) or
                self.moduleInfo.currentFunction.aArg.has_key(identifier)):
                checkGlobalScope = False
                # Defined in current function.
            elif isInnerSub:
                checkGlobalScope = False
                # Assume that it's defined in the containing sub
        if checkGlobalScope:
            if not self.moduleInfo.currentNS.aVar.has_key(identifier):
                self.moduleInfo.currentNS.aVar[identifier] = [{'name':identifier,
                                                               'line':origLineNo}]
            forceGlobal = True
        self.finish_var_assignment(identifier, origLineNo, forceGlobal)
    # end look_for_object_var_assignment

    # Handle arrays, hashes, typeglobs, but don't bother figuring out a type.
    # No 'my', 'our', 'state', or 'use vars' given
    def look_for_var_assignment(self, tok1):
        # First make sure this var hasn't already been defined
        # Is it an implicit global?
        var_name = tok1.text
        if len(var_name) < 2 or var_name[1] == '$':
            return
        if self.moduleInfo.currentFunction:
            # Is it defined in the current function?
            if (self.moduleInfo.currentFunction.aVar.has_key(var_name) or
                self.moduleInfo.currentFunction.aArg.has_key(var_name)):
                return
            scope = 'my'
        else:
            scope = 'our'
        if self.moduleInfo.currentNS.aVar.has_key(var_name):
            return
        tok2 = self.tokenizer.get_next_token()
        if self.classifier.is_operator(tok2, "="):
            varInfo = (tok1.text, tok1.start_line)
            self.moduleInfo.doSetVar(name=var_name, line=tok1.start_line,
                                     scope=scope)
        else:
            self.tokenizer.put_back(tok2)

    def process_import(self, fqModule, origLineNo, import_vars=None):
        tok = self.tokenizer.get_next_token()
        if self._is_string(tok) or self.classifier.is_operator(tok, "("):
            varNames = self.get_list_of_strings(tok)
            imports_nothing = not varNames
        else:
            self.tokenizer.put_back(tok)
            varNames = []
            imports_nothing = None
        args = {'module':fqModule, 'line':origLineNo}
        if not varNames:
            if import_vars and not imports_nothing:
                args['symbol'] = '*'
            self.moduleInfo.add_imported_module(args)
        elif [x[0] for x in varNames if x[0][0] == ":"]:
            # If there's a tag, assume we're just bringing in all exported names.
            if import_vars:
                args['symbol'] = '**'
            self.moduleInfo.add_imported_module(args)
        else:
            for varName in varNames:
                self.moduleInfo.add_imported_module(args, line=varName[1], symbol=varName[0])
    # end process_import
    
    def process_module(self, moduleName, mtime, _showWarnings=False):
        showWarnings=_showWarnings
        self.moduleName = moduleName
        self.parse()
        xmlTree = self.get_CIX(mtime)
        return xmlTree

    def get_CIX(self, mtime=None):
        (root, currNode) = self.printHeader(mtime)
        self.printContents(self.moduleName, currNode)
        self.printTrailer(root)
        return root

    def produce_CIX(self, actual_mtime=None):
        return self.get_CIX(actual_mtime)

    def produce_CIX_NoHeader(self, cix_node):
        """Get the CIX for the current contents, and attach it to the cix_node.
        """
        self.printContents(self.moduleName, cix_node)

    # Codeintel interface to the parser
    def parse(self):
        origLineNo = self.tokenizer.curr_line_no()
        self.moduleInfo = ModuleInfo(self.provide_full_docs)
        self.moduleInfo.doStartNS(NamespaceInfo(name='main', lineNo=origLineNo))
        self.process_package_inner_contents(True)
        if self.provide_full_docs:
            # Check for a trailing pod doc
            podName = re_sub(r'.p[ml]$', '.pod', self.moduleName)
            if not os.path.isfile(podName) and os.path.isfile(os.path.join('..', 'test', podName)):
                podName = os.path.join('..', 'test', podName)
            if os.path.isfile(podName):
                try:
                    f = open(podName)
                    pod_str = f.read()
                    f.close()
                    self.moduleInfo.currentNS.hDocs['modules'].append(pod_str)
                except:
                    pass
        self.moduleInfo.doEndNS(lineNo = self.tokenizer.curr_line_no())
        
        
    
    def process_package_inner_contents(self, doingTopLevel):
        currPackage = self.moduleInfo.currentNS
        popNS = 0
        curr_pkg_line_no = self.tokenizer.curr_line_no()
        while 1:
            tok = self.tokenizer.get_next_token()
            ttype = tok.style
            if ttype == shared_lexer.EOF_STYLE:
                return
            tval = tok.text
            if ttype == self.classifier.style_word:
                if tval == 'package':
                    packageName = self.get_rest_of_subpath("", 0)
                    if packageName:
                        self.moduleInfo.doEndNS(lineNo=curr_pkg_line_no)
                        ns = self.moduleInfo.getNS(packageName,
                                                   lineNo=self.tokenizer.curr_line_no())
                        self.moduleInfo.doStartNS(ns)
                        popNS = 1
                elif tval == 'sub':
                    self.start_process_sub_definition(False); # Is outer sub
                elif tval in ['BEGIN', 'END', 'AUTOLOAD']:
                    self.skip_anon_sub_contents()
                elif tval in ['our', 'my', 'state']:
                    if tval == 'state':
                        tval = 'my'
                    self.get_our_vars('global', tval)
                    # Small warning: vars defined at this lexical level belong to
                    # the containing package, but are visible without
                    # qualification in other packages in the same file.
                elif tval in ['for', 'foreach']:
                    self.get_for_vars()
                elif tval == 'use':
                    self.process_use(0)
                elif tval == 'require':
                    origLineNo = tok.start_line
                    tok = self.tokenizer.get_next_token()
                    ttype = tok.style
                    tval = tok.text
                    if (self.classifier.is_identifier(tok) or
                        self.classifier.is_variable_scalar(tok,
                                                           self.classifier.is_scalar_cb)):
                        # codeintel allows variables
                        fqModule = self.get_rest_of_subpath(tval, 1)
                        self.process_import(fqModule, origLineNo)
                        
                    elif self.classifier.is_string(tok) and not self.classifier.is_string_qw(tok, self.classifier.is_string_qw_cb):
                        # Rewritten to work with UDL languages as well as native perl
                        self.process_import(tval, origLineNo)
                else:
                    self.skip_to_end_of_stmt()
            elif self.classifier.is_variable_array(tok, self.classifier.is_array_cb):
                if tval == '@ISA':
                    self.get_parent_namespaces(True)
                elif tval in ('@EXPORT', '@EXPORT_OK'):
                    self.get_exported_names(tval)
                else:
                    self.look_for_var_assignment(tok)
            elif self.classifier.is_any_operator(tok):
                if tval == '{':
                    self.process_package_inner_contents(False)
                elif tval == '}':
                    if not doingTopLevel:
                        if popNS:
                            self.moduleInfo.doEndNS(lineNo=curr_pkg_line_no)
                            self.moduleInfo.doStartNS(currPackage)
                        break
            elif self.classifier.is_variable_scalar(tok, self.classifier.is_scalar_cb):
                self.look_for_object_var_assignment(tok, False)
            elif self.classifier.is_variable(tok):
                if tval == '%EXPORT_TAGS':
                    pass
                else:
                    self.look_for_var_assignment(tok)
            elif self.classifier.is_comment_structured(tok, self.classifier.is_pod_cb):
                self.moduleInfo.currentNS.hDocs['modules'].append(tval)
            
            curr_pkg_line_no = self.tokenizer.curr_line_no()
    # end process_package_inner_contents
    
    def process_sub_contents(self, isInnerSub):
        # Get to the open brace or semicolon (outside the parens)
        braceCount = 0
        parenCount = 0
        while True:
            tok = self.tokenizer.get_next_token()
            ttype = tok.style
            if ttype == SCE_PL_UNUSED:
                return
            # Expect a paren for args, the open-brace, or a semi-colon
            tval = tok.text
            if parenCount > 0:
                if self.classifier.is_operator(tok, ")"):
                    parenCount -= 1
            elif self.classifier.is_any_operator(tok):
                if tval  == "(":
                    parenCount += 1
                elif tval == "{":
                    braceCount = 1
                    break
                elif tval == ';':
                    return
    
        # So now look for these different things:
        # '}' taking us to brace count of 0
        # my, name, =, shift;
        # my (..., ..., ...) = @_;
        # bless => mark this as a constructor
        # return => try to figure out what we're looking at
    
        while True:
            tok = self.tokenizer.get_next_token()
            ttype = tok.style
            if ttype == SCE_PL_UNUSED:
                break
            tval = tok.text
            if self.classifier.is_index_op(tok):
                if tval == "{":
                    braceCount += 1
                elif tval == "}":
                    braceCount -= 1
                    if braceCount <= 0:
                        break
                elif tval == ':':
                    # Stay here -- it indicates a label
                    pass
                else:
                    self.tokenizer.put_back(tok)
                    self.skip_to_end_of_stmt()
            elif ttype == self.classifier.style_word:
                tlineNo = tok.start_line
                if tval in ('my', 'state'):
                    tok = self.tokenizer.get_next_token()
                    if self.classifier.is_operator(tok, '('):
                        # Treat 'state' variables as 'my', as both
                        # are only visible locally.
                        self.collect_multiple_args(tlineNo, 'local', 'my')
                    elif self.classifier.is_variable(tok):
                        self.collect_single_arg(tok.text, tlineNo, 'local', 'my')
                        if self.classifier.is_operator(tok, '{'):
                            braceCount += 1
                    else:
                        self.get_our_vars('local', 'my')
                elif tval in ('for', 'foreach'):
                    self.get_for_vars()
                    if self.classifier.is_operator(tok, '{'):
                        braceCount += 1
                elif tval == 'bless':
                    self.moduleInfo.currentFunction.isConstructor = True
                elif tval == 'return':
                    # If we return something of type (<(module)name ('::' name)*> "->" new)
                    # Return an instance of type (module)
                    # Either it returned an identifier, or it put the token back
                    tok = self.tokenizer.get_next_token()
                    ttype = tok.style
                    if self.classifier.is_identifier(tok):
                        subclass = self.get_rest_of_subpath(tok.text, 1)
                        tok = self.tokenizer.get_next_token()
                        if tok.text != '->':
                            self.tokenizer.put_back(tok)
                        else:
                            tok = self.tokenizer.get_next_token()
                            if tok.text == 'new':
                                if self.moduleInfo.currentFunction:
                                    self.moduleInfo.currentFunction.resultType.append(subclass)
                            else:
                                self.tokenizer.put_back(tok)
                    else:
                        self.tokenizer.put_back(tok)
                elif tval == 'require':
                    tok = self.tokenizer.get_next_token()
                    ttype = tok.style
                    if self.classifier.is_identifier(tok):
                        origLineNo = tok.start_line
                        fqModule = self.get_rest_of_subpath(tok.text, 1)
                        self.process_import(fqModule, origLineNo)
                elif tval == 'use':
                    self.process_use(1)
                elif tval == 'sub':
                    # Nested subs in Perl aren't really nested --
                    # They're kind of like named closures -- accessible
                    # by name from an outer context, but they can bind
                    # the local state of the sub when defined.
                    # But we can call them anyway, so let's process them
    
                    self.start_process_sub_definition(True) # Is inner
                else:
                    self.skip_to_end_of_stmt()
            elif self.classifier.is_variable_scalar(tok, self.classifier.is_scalar_cb):
                self.look_for_object_var_assignment(tok, isInnerSub)
            elif self.classifier.is_variable(tok):
                if tval == '%EXPORT_TAGS':
                    pass
                else:
                    self.look_for_var_assignment(tok)
            elif self.classifier.is_comment_structured(tok, self.classifier.is_pod_cb):
                if self.moduleInfo.currentFunction:
                    name = getattr(self.moduleInfo.currentFunction, 'name', None)
                    if name:
                        # hdoc_subs = self.moduleInfo.currentNS.hDocs['subs']
                        self.moduleInfo.set_or_append(self.moduleInfo.currentNS.hDocs['subs'], name, tval)
        # end while
    # end process_sub_contents

    def process_use(self, local):
        tok = self.tokenizer.get_next_token()
        if self.classifier.is_identifier_or_keyword(tok):
            origLineNo = tok.start_line
            #@@@ RE
            if re_compile('^[a-z]+$').match(tok.text):
                if tok.text == 'vars':
                    self.get_used_vars(local and 'local' or 'global')
                    return
                elif tok.text == 'base':
                    if not local:
                        self.get_parent_namespaces(False)
                    return
                elif self.pragmaNames.has_key(tok.text):
                    firstMod = tok.text
                    tok = self.tokenizer.get_next_token()
                    if not self.classifier.is_operator(tok, "::"):
                        self.tokenizer.put_back(tok)
                        return
                    self.tokenizer.put_back(tok)
                    tval = firstMod
                else:
                    tval = tok.text
            else:
                tval = tok.text
            fqModule = self.get_rest_of_subpath(tval, 1)
            self.process_import(fqModule, origLineNo, import_vars=1)
    # end process_use

    def skip_anon_sub_contents(self):
        tok = self.tokenizer.get_next_token()
        if self.classifier.is_operator(tok, "{"):
            self.process_package_inner_contents(False)
    # end skip_anon_sub_contents

    def skip_to_close_match(self):
        nestedCount = 1
        while 1:
            tok = self.tokenizer.get_next_token()
            ttype = tok.style
            if ttype == SCE_PL_UNUSED:
                return
            elif self.classifier.is_index_op(tok):
                tval = tok.text
                if self.opHash.has_key(tval):
                    if self.opHash[tval][1] == 1:
                        nestedCount += 1
                    else:
                        nestedCount -= 1
                        if nestedCount <= 0:
                            break
    # end get_rest_of_subpath
    
    def skip_to_close_paren(self):
        tok = self.tokenizer.get_next_token()
        nestedCount = 1
        while 1:
            ttype = tok.style
            if ttype == SCE_PL_UNUSED:
                return
            elif self.classifier.is_any_operator(tok):
                tval = tok.text
                if tval == "(":
                    nestedCount += 1
                    tok = self.tokenizer.get_next_token()
                elif tval == ")":
                    nestedCount -= 1
                    if nestedCount <= 0:
                        break
                else:
                    tok = self.tokenizer.get_next_token()
            else:
                tok = self.tokenizer.get_next_token()
    #end skip_to_close_paren
    
    def skip_to_end_of_stmt(self):
        nestedCount = 0
        while 1:
            tok = self.tokenizer.get_next_token()
            ttype = tok.style
            if ttype == SCE_PL_UNUSED:
                break
            if self.classifier.is_index_op(tok):
                tval = tok.text
                if self.opHash.has_key(tval):
                    if tval == "{":
                        if nestedCount == 0:
                            self.tokenizer.put_back(tok)
                            # At an open-brace, keep going.
                            break
                    vals = self.opHash[tval]
                    if vals[1] == 1:
                        nestedCount += 1
                    else:
                        nestedCount -= 1
                        if nestedCount <= 0:
                            nestedCount = 0
                            if tval == "}":
                                self.tokenizer.put_back(tok)
                                break
                elif tval == ";":
                     # Don't worry about commas, since they don't separate
                     # declaration-type things.
                    if nestedCount == 0:
                        break
    # end skip_to_end_of_stmt
    
    def start_process_sub_definition(self, isInnerSub):
        tok = self.tokenizer.get_next_token()
        # Watch out for lexer buffoonery
        if self.classifier.is_identifier(tok) and len(tok.text.strip()) == 0:
            tok = self.tokenizer.get_next_token()
        if (self.classifier.is_operator(tok, "{") or
            not self.classifier.is_identifier_or_keyword(tok)):
            self.tokenizer.put_back(tok)
            self.skip_to_end_of_stmt()
        else:
            startLineNo = tok.start_line
            fnName = self.get_rest_of_subpath(tok.text, 0)
            if fnName:
                tok = self.tokenizer.get_next_token()
                if self.classifier.is_operator(tok, "("):
                    self.skip_to_close_paren()
                    tok = self.tokenizer.get_next_token()
                if self.classifier.is_operator(tok, ";"):
                    # Don't process
                    pass
                else:
                    self.tokenizer.put_back(tok)
                    # Python doesn't have Perl's localizer, so we do this manually.
                    currFunction = self.moduleInfo.currentFunction
                    self.moduleInfo.doStartFn(FunctionInfo(name=fnName.strip(), lineNo=startLineNo))
                    self.process_sub_contents(isInnerSub)
                    self.moduleInfo.doEndFn(lineNo=self.tokenizer.curr_line_no())
                    self.moduleInfo.currentFunction = currFunction
            else:
                self.skipAnonSubContents()
    # end start_process_sub_definition
        
# end class Parser

def pp(etree, fd):
    s = tostring(etree)
    ind = 0
    iw = 4
    need_nl = False
    #actual_empty_tag_ptn = re_compile(r'<(\w[-\w\d_.]*)([^>]+?)>\s*</\1>', re.S)
    tags = [(re_compile(r'<\?.*?\?>', re.S), False, 0, False),
            (re_compile(r'<!--.*?-->', re.S), False, 0, False),
            (re_compile(r'</[^>]+?>', re.S), True, 0, True), # update before emitting newline
            (re_compile(r'<[^>]+?/>', re.S), True, 0, False),
            (re_compile(r'<[^>]+?>', re.S), True, 1, True),# update after emitting newline
            ]
    fd.write("""<?xml version="1.0" encoding="UTF-8"?>\n""")
    while len(s) > 0:
        if need_nl:
            if s[0:1] == "\r\n":
                s = s[2:]
            elif s[0] == "\n":
                s = s[1:]
            fd.write("\n" + ' ' * (ind * iw))
            need_nl = False
        ltpt = s.find("<")
        if ltpt < 0:
            fd.write(s)
            break
        fd.write(s[0:ltpt])
        s = s[ltpt:]
        #m = actual_empty_tag_ptn.match(s)
        #if m:
        #    print "<%s%s />" % (m.group(1), m.group(2)),
        #    need_nl = True
        #    s = s[len(m.group(1)):]
        #    continue
        for tt in tags:
            m = tt[0].match(s)
            if m:
                tag_end_idx = len(m.group(0))
                need_nl = tt[1]
                if tt[3] and len(s) > tag_end_idx and s[tag_end_idx] != "<":
                    gtpt = s.find(">", tag_end_idx)
                    fd.write(s[0:gtpt+1])
                    s = s[gtpt+1:]
                else:
                    ind += tt[2]
                    fd.write(s[:tag_end_idx])
                    s = s[tag_end_idx:]
                # Preview end-tag breaking
                if s.startswith("</"):
                    need_nl = True
                    if ind > 0:
                        ind -= 1
                break
        else:
            fd.write(s[0:ltpt+1])
            s = s[ltpt+1:]

def main(sample_code, modulePath, mtime, showWarnings, provide_full_docs=True):
    sys.stderr.write("Skipping POD: %r\n" % provide_full_docs)
    sys.exit(1)
    tokenizer = perl_lexer.PerlLexer(sample_code, provide_full_docs)
    parser = Parser(tokenizer, provide_full_docs)
    showWarnings = False
    elementTreeRepn = parser.process_module(modulePath, mtime, showWarnings)
    return elementTreeRepn
        
if __name__ == "__main__":
    if len(sys.argv) == 1:
        sample_code = perl_lexer.provide_sample_code()
        fs = None
        closefs = False
        modulePath = "__main__"
        mtime = time.time()
    elif sys.argv[1] == "-":
        fs = sys.stdin
        closefs = False
        modulePath = "stdin"
        mtime = time.time()
    else:
        modulePath = sys.argv[1]
        mtime = os.stat(modulePath).st_mtime
        fs = open(modulePath, "r")
        closefs = True
    if fs is not None:
        sample_code = shared_lexer.read_and_detab(fs, closefs)
        # fs comes back closed
    # Don't show the data
    elementTreeRepn = main(sample_code, modulePath, mtime, showWarnings, False)
    sys.stdout.write(tostring(elementTreeRepn))
    sys.stdout.write("\n")

    #pp(elementTreeRepn, sys.stdout)
    #import hotshot, hotshot.stats
    #profiler = hotshot.Profile("%s.prof" % (__file__))
    #profiler.runcall(main, sample_code, modulePath, mtime, showWarnings)
    #regex_data = REGEXEN.items()
    #regex_data.sort(lambda a, b: -cmp(a[1], b[1]))
    #for x in regex_data[:20]:
    #    print x[1], x[0]

