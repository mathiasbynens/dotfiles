#!/usr/bin/env python
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

"""JavaScript support for Code Intelligence

    This is a Language Engine for the Code Intelligence (codeintel) system.
    Code Intelligence XML format. See:
        http://specs.tl.activestate.com/kd/kd-0100.html#xml-based-import-export-syntax-cix


Future ideas and changes for the JavaScript ciler:

  * give anonymous functions a unique identifier, so referencing code
    is able to look up the correct anonymous function.

  * create a class prototype structure

  * separate class prototype variables and functions from the local variables

  * use better push/pop handling
"""

import os
from os.path import splitext, basename, exists, dirname, normpath
import sys
import types
import logging
from cStringIO import StringIO
import weakref
from glob import glob

from ciElementTree import Element, ElementTree, SubElement

import SilverCity
from SilverCity.Lexer import Lexer
from SilverCity import ScintillaConstants
from SilverCity.ScintillaConstants import (
    SCE_C_COMMENT, SCE_C_COMMENTDOC, SCE_C_COMMENTDOCKEYWORD,
    SCE_C_COMMENTDOCKEYWORDERROR, SCE_C_COMMENTLINE,
    SCE_C_COMMENTLINEDOC, SCE_C_DEFAULT, SCE_C_IDENTIFIER, SCE_C_NUMBER,
    SCE_C_OPERATOR, SCE_C_STRING, SCE_C_CHARACTER, SCE_C_STRINGEOL, SCE_C_WORD,
    SCE_UDL_CSL_COMMENT, SCE_UDL_CSL_COMMENTBLOCK, SCE_UDL_CSL_DEFAULT,
    SCE_UDL_CSL_IDENTIFIER, SCE_UDL_CSL_NUMBER, SCE_UDL_CSL_OPERATOR,
    SCE_UDL_CSL_REGEX, SCE_UDL_CSL_STRING, SCE_UDL_CSL_WORD,
)

from codeintel2.citadel import CitadelBuffer, ImportHandler, CitadelLangIntel
from codeintel2.buffer import Buffer
from codeintel2.tree_javascript import JavaScriptTreeEvaluator
from codeintel2 import util
from codeintel2.common import *
from codeintel2.indexer import PreloadBufLibsRequest, PreloadLibRequest
from codeintel2.jsdoc import JSDoc, JSDocParameter, jsdoc_tags
from codeintel2.gencix_utils import *
from codeintel2.database.langlib import LangDirsLib
from codeintel2.udl import UDLBuffer, is_udl_csl_style
from codeintel2.accessor import AccessorCache
from codeintel2.langintel import (ParenStyleCalltipIntelMixin,
                                  ProgLangTriggerIntelMixin,
                                  PythonCITDLExtractorMixin)

if _xpcom_:
    from xpcom.server import UnwrapObject



#---- globals

lang = "JavaScript"
# Setup the logger
log = logging.getLogger("codeintel.javascript")
#log.setLevel(logging.DEBUG)
#log.setLevel(logging.INFO)
util.makePerformantLogger(log)

# When enabled, will add a specific path attribute to each cix element for where
# this element was originally created from, good for debugging gencix JavaScript
# API catalogs (YUI, ExtJS).
ADD_PATH_CIX_INFO = False
#ADD_PATH_CIX_INFO = True

# States used by JavaScriptScanner when parsing information
S_DEFAULT = 0
S_IN_ARGS = 1
S_IN_ASSIGNMENT = 2
S_IGNORE_SCOPE = 3
S_OBJECT_ARGUMENT = 4

# Types used by JavaScriptScanner when parsing information
TYPE_NONE = 0
TYPE_FUNCTION = 1
TYPE_VARIABLE = 2
TYPE_GETTER = 3
TYPE_SETTER = 4
TYPE_MEMBER = 5
TYPE_OBJECT = 6
TYPE_CLASS = 7
TYPE_PARENT = 8
TYPE_ALIAS = 9



#---- language support

class JavaScriptLexer(Lexer):
    lang = lang
    def __init__(self, mgr):
        self._properties = SilverCity.PropertySet()
        self._lexer = SilverCity.find_lexer_module_by_id(ScintillaConstants.SCLEX_CPP)
        jsli = mgr.lidb.langinfo_from_lang(self.lang)
        self._keyword_lists = [
            SilverCity.WordList(' '.join(jsli.keywords)),
            SilverCity.WordList(),
            SilverCity.WordList(),
            SilverCity.WordList(),
            SilverCity.WordList()
        ]

class PureJavaScriptStyleClassifier:
    def __init__(self):
        self.is_udl = False
        self.operator_style   = SCE_C_OPERATOR
        self.identifier_style = SCE_C_IDENTIFIER
        self.keyword_style    = SCE_C_WORD
        self.comment_styles   = (SCE_C_COMMENT,
                                 SCE_C_COMMENTDOC,
                                 SCE_C_COMMENTLINE,
                                 SCE_C_COMMENTLINEDOC,
                                 SCE_C_COMMENTDOCKEYWORD,
                                 SCE_C_COMMENTDOCKEYWORDERROR)
        self.string_styles    = (SCE_C_STRING, SCE_C_CHARACTER, SCE_C_STRINGEOL)
        self.whitespace_style = SCE_C_DEFAULT
        self.ignore_styles    = self.comment_styles + (self.whitespace_style, )

class UDLJavaScriptStyleClassifier:
    def __init__(self):
        self.is_udl = True
        self.operator_style   = SCE_UDL_CSL_OPERATOR
        self.identifier_style = SCE_UDL_CSL_IDENTIFIER
        self.keyword_style    = SCE_UDL_CSL_WORD
        self.comment_styles   = (SCE_UDL_CSL_COMMENT,
                                 SCE_UDL_CSL_COMMENTBLOCK,)
        self.string_styles    = (SCE_UDL_CSL_STRING, )
        self.whitespace_style = SCE_UDL_CSL_DEFAULT
        self.ignore_styles    = self.comment_styles + (self.whitespace_style, )

pureJSClassifier = PureJavaScriptStyleClassifier()
udlJSClassifier = UDLJavaScriptStyleClassifier()

class JavaScriptLangIntel(CitadelLangIntel,
                          ParenStyleCalltipIntelMixin,
                          ProgLangTriggerIntelMixin,
                          PythonCITDLExtractorMixin):
    lang = lang
    _evaluatorClass = JavaScriptTreeEvaluator
    extraPathsPrefName = "javascriptExtraPaths"

    # The way namespacing is done with variables in JS means that grouping
    # global vars is just annoying.
    cb_group_global_vars = False
    # Define the trigger chars we use, used by ProgLangTriggerIntelMixin
    trg_chars = tuple(".(@'\" ")
    calltip_trg_chars = tuple('(')   # excluded ' ' for perf (bug 55497)
    # Define literal mapping to citdl member, used in PythonCITDLExtractorMixin
    citdl_from_literal_type = {"string": "String"}

    def cb_variable_data_from_elem(self, elem):
        """Use the 'namespace' image in the Code Browser for a variable
        acting as one.
        """
        data = CitadelLangIntel.cb_variable_data_from_elem(self, elem)
        if len(elem) and data["img"].startswith("variable"):
            data["img"] = data["img"].replace("variable", "namespace")
        return data

    def trg_from_pos(self, buf, pos, implicit=True,
                     lang=None):
        DEBUG = False  # not using 'logging' system, because want to be fast
        #DEBUG = True
        #if DEBUG:
        #    print util.banner("JavaScript trg_from_pos(pos=%r, implicit=%r)"
        #                      % (pos, implicit))

        if pos == 0:
            return None

        if lang is None:
            lang = self.lang

        if isinstance(buf, UDLBuffer):
            jsClassifier = udlJSClassifier
        else:
            jsClassifier = pureJSClassifier

        accessor = buf.accessor
        last_pos = pos - 1
        last_char = accessor.char_at_pos(last_pos)
        last_style = accessor.style_at_pos(last_pos)
        if DEBUG:
            print "  last_pos: %s" % last_pos
            print "  last_ch: %r" % last_char
            print "  last_style: %r" % last_style

        if (jsClassifier.is_udl and last_char == '/'
            and last_pos > 0 and accessor.char_at_pos(last_pos-1) == '<'
            and last_style not in (SCE_UDL_CSL_STRING,
                                   SCE_UDL_CSL_COMMENTBLOCK,
                                   SCE_UDL_CSL_COMMENT,
                                   SCE_UDL_CSL_REGEX)):
            # Looks like start of closing '</script>' tag. While typing this
            # the styling will still be in the CSL range.
            return Trigger(buf.m_lang, TRG_FORM_CPLN,
                           "end-tag", pos, implicit)

        # JSDoc completions
        elif last_char == "@" and last_style in jsClassifier.comment_styles:
            # If the preceeding non-whitespace character is a "*" or newline
            # then we complete for jsdoc tag names
            p = last_pos - 1
            min_p = max(0, p - 50)      # Don't bother looking more than 50 chars
            if DEBUG:
                print "Checking match for jsdoc completions"
            while p >= min_p and \
                  accessor.style_at_pos(p) in jsClassifier.comment_styles:
                ch = accessor.char_at_pos(p)
                p -= 1
                #if DEBUG:
                #    print "Looking at ch: %r" % (ch)
                if ch == "*" or ch in "\r\n":
                    break
                elif ch not in " \t\v":
                    # Not whitespace, not a valid tag then
                    return None
            else:
                # Nothing found in the specified range
                if DEBUG:
                    print "trg_from_pos: not a jsdoc"
                return None
            if DEBUG:
                print "Matched trigger for jsdoc completion"
            return Trigger(lang, TRG_FORM_CPLN,
                           "jsdoc-tags", pos, implicit)

        # JSDoc calltip
        elif last_char in " \t" and last_style in jsClassifier.comment_styles:
            # whitespace in a comment, see if it matches for jsdoc calltip
            p = last_pos - 1
            min_p = max(0, p - 50)      # Don't bother looking more than 50 chars
            if DEBUG:
                print "Checking match for jsdoc calltip"
            ch = None
            ident_found_pos = None
            while p >= min_p and \
                  accessor.style_at_pos(p) in jsClassifier.comment_styles:
                ch = accessor.char_at_pos(p)
                p -= 1
                if ident_found_pos is None:
                    #print "jsdoc: Looking for identifier, at ch: %r" % (ch)
                    if ch in " \t":
                        pass
                    elif _isident(ch):
                        ident_found_pos = p+1
                    else:
                        if DEBUG:
                            print "No jsdoc, whitespace not preceeded by an " \
                                  "identifer"
                        return None
                elif ch == "@":
                    # This is what we've been looking for!
                    jsdoc_field = accessor.text_range(p+2, ident_found_pos+1)
                    if DEBUG:
                        print "Matched trigger for jsdoc calltip: '%s'" % (jsdoc_field, )
                    return Trigger(lang, TRG_FORM_CALLTIP,
                                   "jsdoc-tags", ident_found_pos, implicit,
                                   jsdoc_field=jsdoc_field)
                elif not _isident(ch):
                    if DEBUG:
                        print "No jsdoc, identifier not preceeded by an '@'"
                    # Not whitespace, not a valid tag then
                    return None
            # Nothing found in the specified range
            if DEBUG:
                print "No jsdoc, ran out of characters to look at."

        elif last_char not in self.trg_chars:
            # Check if this could be a 'complete-names' trigger, this is
            # an implicit 3-character trigger i.e. " win<|>" or an explicit
            # trigger on 3 or more characters. We cannot support less than than
            # 3-chars without involving a big penalty hit (as our codeintel
            # database uses a 3-char index).
            if last_pos >= 2 and (last_style == jsClassifier.identifier_style or
                                  last_style == jsClassifier.keyword_style):
                if DEBUG:
                    print "Checking for 'names' three-char-trigger"
                # The previous two characters must be the same style.
                p = last_pos - 1
                min_p = max(0, p - 1)
                citdl_expr = [last_char]
                while p >= min_p:
                    if accessor.style_at_pos(p) != last_style:
                        if DEBUG:
                            print "No 'names' trigger, inconsistent style: " \
                                  "%d, pos: %d" % (accessor.style_at_pos(p), p)
                        break
                    citdl_expr += accessor.char_at_pos(p)
                    p -= 1
                else:
                    # Now check the third character back.
                    # "p < 0" is for when we are at the start of a document.
                    if p >= 0:
                        ac = None
                        style = accessor.style_at_pos(p)
                        if style == last_style:
                            if implicit:
                                if DEBUG:
                                    print "No 'names' trigger, third char " \
                                          "style: %d, pos: %d" % (style, p)
                                return None
                            else:
                                # explicit can be longer than 3-chars, skip over
                                # the rest of the word/identifier.
                                ac = AccessorCache(accessor, p)
                                p, ch, style = ac.getPrecedingPosCharStyle(last_style,
                                                    jsClassifier.ignore_styles,
                                                    max_look_back=80)

                        # Now we know that we are three identifier characters
                        # preceeded by something different, which is not that
                        # common, we now need to be a little more cpu-intensive
                        # with our search to ensure we're not preceeded by a
                        # dot ".", as this would mean a different cpln type!

                        if style == jsClassifier.whitespace_style:
                            # Find out what occurs before the whitespace,
                            # ignoring whitespace and comments.
                            if ac is None:
                                ac = AccessorCache(accessor, p)
                            p, ch, style = ac.getPrecedingPosCharStyle(style,
                                                jsClassifier.ignore_styles,
                                                max_look_back=80)
                        if style is not None:
                            ch = accessor.char_at_pos(p)
                            if ch == ".":
                                if DEBUG:
                                    print "No 'names' trigger, third char " \
                                          "is a dot"
                                return None
                            elif style == jsClassifier.keyword_style:
                                p, prev_text = ac.getTextBackWithStyle(style, jsClassifier.ignore_styles, max_text_len=len("function")+1)
                                if prev_text in ("function", ):
                                    # We don't trigger after function, this is
                                    # defining a new item that does not exist.
                                    if DEBUG:
                                        print "No 'names' trigger, preceeding "\
                                              "text is 'function'"
                                    return None
                    if DEBUG:
                        print "triggering 'javascript-complete-names' at " \
                              "pos: %d" % (last_pos - 2, )
                                
                    return Trigger(self.lang, TRG_FORM_CPLN,
                                   "names", last_pos - 2, implicit,
                                   citdl_expr="".join(reversed(citdl_expr)))
            if DEBUG:
                print "trg_from_pos: no: %r is not in %r" % (
                                last_char, "".join(self.trg_chars), )
            return None

        elif last_style == jsClassifier.operator_style:
            # Go back and check what we are operating on, should be
            # an identifier or a close brace type ")]}".
            p = last_pos - 1
            while p >=0:
                style = accessor.style_at_pos(p)
                if style == jsClassifier.identifier_style:
                    break
                elif style == jsClassifier.keyword_style and last_char == ".":
                    break
                elif style == jsClassifier.operator_style and \
                     last_char == "." and accessor.char_at_pos(p) in ")]}":
                    break
                elif style in jsClassifier.string_styles:
                    break
                elif style not in jsClassifier.ignore_styles:
                    # Else, wrong style for calltip
                    if DEBUG:
                        print "not a trigger: unexpected style: %d at pos: %d" \
                              % (style, p)
                    return None
                p -= 1
            else:
                # Did not find the necessary style, no completion/calltip then
                return None

            if last_char == ".":
                if style in jsClassifier.string_styles:
                    return Trigger(lang, TRG_FORM_CPLN,
                                   "literal-members", pos, implicit,
                                   citdl_expr="String")
                elif style == jsClassifier.keyword_style:
                    # Check if it's a "this." expression
                    isThis = False
                    if last_pos >= 4:
                        word = []
                        p = last_pos - 1
                        p_end = last_pos - 5
                        while p > p_end:
                            word.insert(0, accessor.char_at_pos(p))
                            p -= 1
                        if "".join(word) == "this":
                            isThis = True
                    if not isThis:
                        return None
                return Trigger(lang, TRG_FORM_CPLN,
                               "object-members", pos, implicit)
            elif last_char == "(":
                # p is now at the end of the identifier, go back and check
                # that we are not defining a function
                ac = AccessorCache(accessor, p)
                # Get the previous style, if it's a keyword style, check that
                # the keyword is not "function"
                prev_pos, prev_char, prev_style = ac.getPrecedingPosCharStyle(jsClassifier.identifier_style, jsClassifier.ignore_styles)
                if prev_style == jsClassifier.keyword_style:
                    p, prev_text = ac.getTextBackWithStyle(prev_style, jsClassifier.ignore_styles, max_text_len=len("function")+1)
                    if prev_text in ("function", ):
                        # Don't trigger here
                        return None
                return Trigger(lang, TRG_FORM_CALLTIP,
                               "call-signature", pos, implicit)

        elif last_style in jsClassifier.string_styles and last_char in "\"'":
            prev_pos = last_pos - 1
            prev_char = accessor.char_at_pos(prev_pos)
            if prev_char != '[':
                prev_style = accessor.style_at_pos(prev_pos)
                ac = AccessorCache(accessor, prev_pos)
                if prev_style in jsClassifier.ignore_styles:
                    # Look back further.
                    prev_pos, prev_char, prev_style = ac.getPrevPosCharStyle(ignore_styles=jsClassifier.ignore_styles)
            if prev_char == '[':
                # We're good to go.
                if DEBUG:
                    print "Matched trigger for array completions"
                return Trigger(lang, TRG_FORM_CPLN,
                               "array-members", pos, implicit,
                               bracket_pos=prev_pos, trg_char=last_char)

        return None

    def preceding_trg_from_pos(self, buf, pos, curr_pos,
                               preceding_trg_terminators=None, DEBUG=False):
        DEBUG = False
        if DEBUG:
            print "pos: %d" % (pos, )
            print "ch: %r" % (buf.accessor.char_at_pos(pos), )
            print "curr_pos: %d" % (curr_pos, )

        # Check if we can match on either of the 3-character trigger or on the
        # normal preceding_trg_terminators.

        # Try the default preceding_trg_from_pos handler
        if pos != curr_pos and self._last_trg_type == "names":
            # The last trigger type was a 3-char trigger "names", we must try
            # triggering from the same point as before to get other available
            # trigger types defined at the same poisition or before.
            trg = ProgLangTriggerIntelMixin.preceding_trg_from_pos(
                    self, buf, pos+2, curr_pos, preceding_trg_terminators,
                    DEBUG=DEBUG)
        else:
            trg = ProgLangTriggerIntelMixin.preceding_trg_from_pos(
                    self, buf, pos, curr_pos, preceding_trg_terminators,
                    DEBUG=DEBUG)

        # Now try the 3-char trigger, if we get two triggers, take the closest
        # match.
        names_trigger = None
        if isinstance(buf, UDLBuffer):
            jsClassifier = udlJSClassifier
        else:
            jsClassifier = pureJSClassifier

        style = None
        if pos > 0:
            accessor = buf.accessor
            if pos == curr_pos:
                # We actually care about whats left of the cursor.
                pos -= 1
            style = accessor.style_at_pos(pos)
            if style in (jsClassifier.identifier_style, jsClassifier.keyword_style):
                ac = AccessorCache(accessor, pos)
                prev_pos, prev_ch, prev_style = ac.getPrecedingPosCharStyle(style)
                if prev_style is not None and (pos - prev_pos) > 3:
                    # We need at least 3 character for proper completion handling.
                    names_trigger = self.trg_from_pos(buf, prev_pos + 4, implicit=False)

        if DEBUG:
            print "trg: %r" % (trg, )
            print "names_trigger: %r" % (names_trigger, )
            print "last_trg_type: %r" % (self._last_trg_type, )

        if names_trigger:
            if not trg:
                trg = names_trigger
            # Two triggers, choose the best one.
            elif trg.pos == names_trigger.pos:
                if self._last_trg_type != "names":
                    # The names trigger gets priority over the other trigger
                    # types, unless the previous trigger was also a names trg.
                    trg = names_trigger
            elif trg.pos < names_trigger.pos:
                trg = names_trigger

        elif trg is None and style in jsClassifier.comment_styles:
            # Check if there is a JSDoc to provide a calltip for, example:
            #       /** @param foobar {sometype} This is field for <|>
            if DEBUG:
                print "\njs preceding_trg_from_pos::jsdoc: check for calltip"
            comment = accessor.text_range(max(0, curr_pos-200), curr_pos)
            at_idx = comment.rfind("@")
            if at_idx >= 0:
                if DEBUG:
                    print "\njs preceding_trg_from_pos::jsdoc: contains '@'"
                space_idx = comment[at_idx:].find(" ")
                if space_idx >= 0:
                    # Trigger after the space character.
                    trg_pos = (curr_pos - len(comment)) + at_idx + space_idx + 1
                    if DEBUG:
                        print "\njs preceding_trg_from_pos::jsdoc: calltip at %d" % (trg_pos, )
                    trg = self.trg_from_pos(buf, trg_pos, implicit=False)

        if trg:
            self._last_trg_type = trg.type
        return trg

    _jsdoc_cplns = [ ("variable", t) for t in sorted(jsdoc_tags) ]

    def async_eval_at_trg(self, buf, trg, ctlr):
        if _xpcom_:
            trg = UnwrapObject(trg)
            ctlr = UnwrapObject(ctlr)
        ctlr.start(buf, trg)

        # JSDoc completions
        if trg.id == (self.lang, TRG_FORM_CPLN, "jsdoc-tags"):
            #TODO: Would like a "javadoc tag" completion image name.
            ctlr.set_cplns(self._jsdoc_cplns)
            ctlr.done("success")
            return

        # JSDoc calltip
        elif trg.id == (self.lang, TRG_FORM_CALLTIP, "jsdoc-tags"):
            #TODO: Would like a "javadoc tag" completion image name.
            jsdoc_field = trg.extra.get("jsdoc_field")
            if jsdoc_field:
                #print "jsdoc_field: %r" % (jsdoc_field, )
                calltip = jsdoc_tags.get(jsdoc_field)
                if calltip:
                    ctlr.set_calltips([calltip])
            ctlr.done("success")
            return

        if trg.type == "literal-members":
            # We could leave this to citdl_expr_from_trg, but this is a
            # little bit faster, since we already know the citdl expr.
            citdl_expr = trg.extra.get("citdl_expr")
        elif trg.type == "names":
            # We could leave this to citdl_expr_from_trg, but since we already
            # know the citdl expr, use it.
            citdl_expr = trg.extra.get("citdl_expr")
        else:
            try:
                citdl_expr = self.citdl_expr_from_trg(buf, trg)
            except CodeIntelError, ex:
                ctlr.error(str(ex))
                ctlr.done("error")
                return
        line = buf.accessor.line_from_pos(trg.pos)
        evalr = self._evaluatorClass(ctlr, buf, trg, citdl_expr, line)
        buf.mgr.request_eval(evalr)

    def _extra_dirs_from_env(self, env):
        extra_dirs = set()
        include_project = env.get_pref("codeintel_scan_files_in_project", True)
        if include_project:
            proj_base_dir = env.get_proj_base_dir()
            if proj_base_dir is not None:
                extra_dirs.add(proj_base_dir)  # Bug 68850.
        for pref in env.get_all_prefs(self.extraPathsPrefName):
            if not pref: continue
            extra_dirs.update(d.strip() for d in pref.split(os.pathsep)
                              if exists(d.strip()))
        if extra_dirs:
            log.debug("%s extra lib dirs: %r", self.lang, extra_dirs)
            max_depth = env.get_pref("codeintel_max_recursive_dir_depth", 10)
            js_assocs = env.assoc_patterns_from_lang("JavaScript")
            extra_dirs = tuple(
                util.gen_dirs_under_dirs(extra_dirs,
                    max_depth=max_depth,
                    interesting_file_patterns=js_assocs)
            )
        else:
            extra_dirs = () # ensure retval is a tuple
        return extra_dirs

    @property
    def stdlibs(self):
        return [self.mgr.db.get_stdlib(self.lang)]

    def libs_from_buf(self, buf):
        env = buf.env

        # A buffer's libs depend on its env and the buf itself so
        # we cache it on the env and key off the buffer.
        if "javascript-buf-libs" not in env.cache:
            env.cache["javascript-buf-libs"] = weakref.WeakKeyDictionary()
        cache = env.cache["javascript-buf-libs"] # <buf-weak-ref> -> <libs>

        if buf not in cache:
            env.add_pref_observer(self.extraPathsPrefName,
                self._invalidate_cache_and_rescan_extra_dirs)
            env.add_pref_observer("codeintel_selected_catalogs",
                                  self._invalidate_cache)
            env.add_pref_observer("codeintel_max_recursive_dir_depth",
                                  self._invalidate_cache)
            env.add_pref_observer("codeintel_scan_files_in_project",
                                  self._invalidate_cache)
            # (Bug 68850) Both of these 'live_*' prefs on the *project*
            # prefset can result in a change of project base dir. It is
            # possible that we can get false positives here if there is ever
            # a global pref of this name.
            env.add_pref_observer("import_live",
                self._invalidate_cache_and_rescan_extra_dirs)
            env.add_pref_observer("import_dirname",
                self._invalidate_cache_and_rescan_extra_dirs)

            db = self.mgr.db
            libs = []

            # - extradirslib
            extra_dirs = self._extra_dirs_from_env(env)
            if extra_dirs:
                libs.append( db.get_lang_lib(self.lang, "extradirslib",
                                extra_dirs) )

            # Warn the user if there is a huge number of import dirs that
            # might slow down completion.
            num_import_dirs = len(extra_dirs)
            if num_import_dirs > 100:
                db.report_event("This buffer is configured with %d %s "
                                "import dirs: this may result in poor "
                                "completion performance" %
                                (num_import_dirs, self.lang))

            if buf.lang == self.lang:
                # - curdirlib (before extradirslib; only if pure JS file)
                cwd = dirname(normpath(buf.path))
                if cwd not in extra_dirs:
                    libs.insert(0, db.get_lang_lib(self.lang, "curdirlib", [cwd]))

            # - cataloglibs
            if buf.lang == "HTML5":
                # Implicit HTML 5 catalog additions.
                libs.append(db.get_catalog_lib("JavaScript", ["html5"]))
            catalog_selections = env.get_pref("codeintel_selected_catalogs")
            libs.append(db.get_catalog_lib(self.lang, catalog_selections))

            # - stdlibs
            libs += self.stdlibs

            cache[buf] = libs
        return cache[buf]

    def _invalidate_cache(self, env, pref_name):
        if "javascript-buf-libs" in env.cache:
            log.debug("invalidate 'javascript-buf-libs' cache on %r", env)
            del env.cache["javascript-buf-libs"]

    def _invalidate_cache_and_rescan_extra_dirs(self, env, pref_name):
        self._invalidate_cache(env, pref_name)
        extra_dirs = self._extra_dirs_from_env(env)
        if extra_dirs:
            extradirslib = self.mgr.db.get_lang_lib(
                self.lang, "extradirslib", extra_dirs)
            request = PreloadLibRequest(extradirslib)
            self.mgr.idxr.stage_request(request, 1.0)

    def lpaths_from_blob(self, blob):
        """Return <lpaths> for this blob
        where,
            <lpaths> is a set of externally referencable lookup-paths, e.g.
                [("YAHOO",), ("YAHOO", "util"), ...]

        Note: The jury is out on whether this should include imports.
        However, currently this is only being used for JS (no imports)
        so it doesn't yet matter.
        """
        return set(lpath for child in blob
                   for lpath in _walk_js_symbols(child))


class JavaScriptBuffer(CitadelBuffer):
    lang = lang

    # Fillup chars for JavaScript: basically, any non-identifier char.
    # XXX - '@' removed in order to better support XPCOM completions:
    #           Components.interfaces['@mozilla.]
    #       Whilst not an ideal solution, as when the '.' is hit we run into the
    #       same problem again... the ideal solution would be to override the
    #       cpln_fillup_chars to be only "\"'" for the 'array-members' trigger
    #       event. But this is not yet possible...
    # - dropped ' ' It gets in the way of common usage: "var " (bug 77950).
    cpln_fillup_chars = "~`!#%^&*()-=+{}[]|\\;:'\",.<>?/"
    cpln_stop_chars = "~`!@#%^&*()-=+{}[]|\\;:'\",.<>?/ "
    sce_prefixes = ["SCE_C_"]

    cb_show_if_empty = True

    def __init__(self, *args, **kwargs):
        CitadelBuffer.__init__(self, *args, **kwargs)
        
        # Encourage the database to pre-scan dirs relevant to completion
        # for this buffer -- because of recursive-dir-include-everything
        # semantics for JavaScript this first-time scan can take a while.
        request = PreloadBufLibsRequest(self)
        self.mgr.idxr.stage_request(request, 1.0)

    @property
    def libs(self):
        return self.langintel.libs_from_buf(self)

    @property
    def stdlib(self):
        return self.libs[-1]

    def scoperef_from_blob_and_line(self, blob, line):
        """Return the scope for the given position in this buffer.

            "line" is 1-based.

        See CitadelBuffer.scoperef_from_pos() for details.
        JavaScript has two differences here:
        - <variable>'s are scopes if they have child tags. This CIX
          technique is used in JavaScript to define customized object
          instances.
        - Currently a JavaScript "class" line range may not include its
          methods in some cases.
            function Foo() {
            }
            Foo.prototype.bar = function() {
            }
          Class "Foo" has a line range that does not include method "bar".
          c.f. test javascript/cpln/intermixed_class_definitions
        """
        DEBUG = False
        if DEBUG:
            print "scoperef_from_pos: look for line %d in %r" % (line, blob)

        best_fit_lpath = None
        for scope, lpath in _walk_js_scopes(blob):
            start = int(scope.get("line"))
            # JS CIX <scope> should alway have lineend. The default is
            # because JS <variable>'s with content (i.e. anonymous
            # custom Object instances) do not typically have lineend.
            # Note: not sure the fallback is correct.
            end = int(scope.get("lineend", start))
            if DEBUG:
                print "scoperef_from_pos:    scope %r (%r-%r)?"\
                      % (scope, start, end),
            if line < start:
                if DEBUG: print "no, before start"
                continue
            elif line > end:
                if DEBUG: print "no, after end"
                continue
            elif line <= end:
                if DEBUG: print "yes, could be"
                best_fit_lpath = lpath
            else:
                if DEBUG: print "no, passed end"
                if best_fit_lpath is not None:
                    break
        if best_fit_lpath is not None:
            return (blob, best_fit_lpath)
        else:
            return (blob, [])


class JavaScriptImportHandler(ImportHandler):
    def setCorePath(self, compiler=None, extra=None):
        self.corePath = []

    def _findScannableFiles(self, (files, searchedDirs), dirname, names):
        if sys.platform.startswith("win"):
            cpath = dirname.lower()
        else:
            cpath = dirname
        if cpath in searchedDirs:
            while names:
                del names[0]
            return
        else:
            searchedDirs[cpath] = 1
        for i in range(len(names)-1, -1, -1): # backward so can del from list
            path = os.path.join(dirname, names[i])
            if os.path.isdir(path):
                pass
            elif os.path.splitext(names[i])[1] in (".js",):
                #XXX The list of extensions should be settable on
                #    the ImportHandler and Komodo should set whatever is
                #    set in prefs.
                #XXX This check for files should probably include
                #    scripts, which might likely not have the
                #    extension: need to grow filetype-from-content smarts.
                files.append(path)

    def genScannableFiles(self, path=None, skipRareImports=False,
                          importableOnly=False):
        if path is None:
            path = self._getPath()
        searchedDirs = {}
        for dirname in path:
            if dirname == os.curdir:
                # Do NOT traverse the common '.' element of @INC. It is
                # environment-dependent so not useful for the typical call
                # of this method.
                continue
            files = []
            os.path.walk(dirname, self._findScannableFiles,
                         (files, searchedDirs))
            for file in files:
                yield file

    def find_importables_in_dir(self, dir):
        """See citadel.py::ImportHandler.find_importables_in_dir() for
        details.

        Importables for JavaScript look like this:
            {"foo.js":  ("foo.js", None, False),
             "somedir": (None,     None, True)}

        TODO: log the fs-stat'ing a la codeintel.db logging.
        """
        from os.path import join, isdir, splitext

        if dir == "<Unsaved>":
            #TODO: stop these getting in here.
            return {}

        #TODO: log the fs-stat'ing a la codeintel.db logging.
        try:
            names = os.listdir(dir)
        except OSError, ex:
            return {}
        dirs, nondirs = set(), set()
        for name in names:
            try:
                if isdir(join(dir, name)):
                    dirs.add(name)
                else:
                    nondirs.add(name)
            except UnicodeDecodeError:
                # Hit a filename that cannot be encoded in the default encoding.
                # Just skip it. (Bug 82268)
                pass

        importables = {}
        for name in nondirs:
            base, ext = splitext(name)
            if ext != ".js":
                continue
            if base in dirs:
                importables[base] = (name, None, True)
                dirs.remove(base)
            else:
                importables[base] = (name, None, False)
        for name in dirs:
            importables[name] = (None, None, True)

        return importables


class JavaScriptCILEDriver(CILEDriver):
    lang = lang

    def scan_purelang(self, buf):
        #print >> sys.stderr, buf.path
        log.info("scan_purelang: path: %r lang: %s", buf.path, buf.lang)
        norm_path = buf.path
        if sys.platform == "win32":
            # CIX requires a normalized path.
            norm_path = norm_path.replace('\\', '/')
        mtime = "XXX"
        jscile = JavaScriptCiler(self.mgr, norm_path, mtime, lang=buf.lang)
        # Profiling code: BEGIN
        #import hotshot, hotshot.stats
        #profiler = hotshot.Profile("%s.prof" % (__file__))
        #profiler.runcall(jscile.scan_puretext, buf.accessor.text)
        # Profiling code: END
        jscile.scan_puretext(buf.accessor.text)

        tree = createCixRoot()
        jscile.convertToElementTreeFile(tree, file_lang=self.lang)

        return tree

    def scan_multilang(self, buf, csl_cile_driver=None):
        """Given the buffer, scan the buffer tokens for CSL UDL tokens."""

        #print >> sys.stderr, buf.path
        log.info("scan_multilang: path: %r", buf.path)

        norm_path = buf.path
        if sys.platform == "win32":
            # CIX requires a normalized path.
            norm_path = norm_path.replace('\\', '/')
        #XXX Remove mtime when move to CIX 2.0.
        mtime = "XXX"
        jscile = JavaScriptCiler(self.mgr, norm_path, mtime)

        jscile.setStyleValues(wordStyle=SCE_UDL_CSL_WORD,
                              identiferStyle=SCE_UDL_CSL_IDENTIFIER,
                              operatorStyle=SCE_UDL_CSL_OPERATOR,
                              stringStyles=(SCE_UDL_CSL_STRING, ),
                              numberStyle=SCE_UDL_CSL_NUMBER,
                              commentStyles=jscile.UDL_COMMENT_STYLES)
        for token in buf.accessor.gen_tokens():
            # The tokens can be a generator of mixed UDL tokens (CSL, SSL, CSS
            # etc.). Need to parse out the tokens that are not CSL.
            if is_udl_csl_style(token['style']):
                jscile.token_next(**token)
        # Ensure we take notice of any text left in the ciler
        jscile._endOfScanReached()
        # We've parsed up the JavaScript, fix any variables types
        jscile.cile.updateAllScopeNames()

        tree = createCixRoot()
        jscile.convertToElementTreeFile(tree, file_lang=buf.lang, module_lang=self.lang)
        return tree

    def scan_csl_tokens(self, file_elem, blob_name, csl_tokens):
        """csl_tokens are pure JavaScript UDL tokens.
        
        There is no need to parse out other types of tokens.
        """

        #print >> sys.stderr, file_elem.get("path")
        log.info("scan_csl_tokens: %r", file_elem.get("path"))
        blob_elem = createCixModule(file_elem, blob_name, lang,
                                    src=file_elem.get("path"))
        jscile = JavaScriptCiler(self.mgr)
        jscile.setStyleValues(wordStyle=SCE_UDL_CSL_WORD,
                              identiferStyle=SCE_UDL_CSL_IDENTIFIER,
                              operatorStyle=SCE_UDL_CSL_OPERATOR,
                              stringStyles=(SCE_UDL_CSL_STRING, ),
                              numberStyle=SCE_UDL_CSL_NUMBER,
                              commentStyles=jscile.UDL_COMMENT_STYLES)
        for csl_token in csl_tokens:
            jscile.token_next(**csl_token)
        # Ensure we take notice of any text left in the ciler
        jscile._endOfScanReached()
        # We've parsed up the JavaScript, fix any variables types
        jscile.cile.updateAllScopeNames()
        jscile.convertToElementTreeModule(blob_elem)


def _sortByLineCmp(val1, val2):
    try:
    #if hasattr(val1, "line") and hasattr(val2, "line"):
        return cmp(val1.line, val2.line)
    except AttributeError:
        return cmp(val1, val2)

def sortByLine(seq):
    seq.sort(_sortByLineCmp)
    return seq

# Everything is JS is an object.... MUMUHAHAHAHAHAHAAAA.......

class JSObject:
    def __init__(self, name, parent, lineno, depth, type=None,
                 doc=None, isLocal=False, isHidden=False, path=None):
        self.name = name
        self.parent = parent
        self.cixname = self.__class__.__name__[2:].lower()
        self.line = lineno
        self.lineend = -1
        self.depth = depth
        self.type = type
        self.path = path
        self._class = None  # Used when part of a class
        self.classes = {} # declared sub-classes
        self.members = {} # all private member variables used in class
        self.variables = {} # all variables used in class
        self.functions = {}
        self.anonymous_functions = [] # anonymous functions declared in scope
        self.attributes = []    # Special attributes for object
        self.returnTypes = []    # List of possible return values
        self.constructor = None
        self.classrefs = []
        self.doc = doc
        self.metadata = None
        self.isHidden = isHidden  # Special case, should not be output to cix
        if isLocal:
            # XXX: TODO: It may be appropriate to just use private..., although
            #            my feeling of the difference between the two names
            #            is that private elements should still be listed in
            #            completions from the class itself, whereas local
            #            should not...
            #
            # Local has a special meaning within the javascript tree evaluator,
            # elements with a "__local__" attribute will not be included in js
            # codeintel completion results.
            self.attributes.append("__local__")
            # Private has a special meaning within the code browser,
            # an element with a "private" attribute shows a small lock icon.
            # Private also has special meaning for jsdoc purposes, where it
            # means not to show documentation for these elements.
            self.attributes.append("private")

        self.doc = doc
        self.jsdoc = None
        if self.doc:
            # Turn the doc list into a JSDoc object
            self.jsdoc = JSDoc("".join(self.doc))

    def setParent(self, parent):
        # Validate the parent/child relationship. This is to avoid possible
        # recursion errors - bug 85481.
        seen_scopes = [self]
        parent_scope = parent
        while parent_scope:
            if parent_scope in seen_scopes:
                raise CodeIntelError("setParent:: recursion error, scope: %r, "
                                     "parent: %r" % (self.name, parent_scope.name))
            seen_scopes.append(parent_scope)
            parent_scope = parent_scope.parent
        self.parent = parent

    def getFullPath(self):
        if self.parent:
            return self.parent.getFullPath() + [self.name]
        return [self.name]

    def addAttribute(self, attr):
        if attr not in self.attributes:
            self.attributes.append(attr)

    def removeAttribute(self, attr):
        while attr in self.attributes:
            self.attributes.remove(attr)

    def hasChildren(self):
        return self.variables or self.functions or self.classes or self.members

    def isAnonymous(self):
        return self.name == "(anonymous)"

    def addClassRef(self, baseclass):
        assert isinstance(baseclass, (str, unicode)), "baseclass %r is not a str" % (baseclass,)
        if baseclass not in self.classrefs:
            self.classrefs.append(baseclass)

    def addVariable(self, name, value=None, metadata=None):
        """Add a variable in this scope (possibly as a property)
        @param name {unicode} The name of the variable
        @param value {JSObject} The value of the variable
        @param metadata {dict} Extra metadata about the assignment
        @returns {JSObject} The resulting variable (possibly different from
                |value| if one with the given |name| exists)
        """
        v = self.variables.get(name, None)
        if v is None:
            v = self.members.get(name, None)
        if v is None:
            log.info("VAR:%s, line:%d, type:%r, scope:%r, meta:%r",
                     name, value.line, value.type, self.name, metadata)
            v = value
            self.variables[name] = v
        # Else if there is no citdl type yet, assign it the given type
        elif value.type and not v.type:
            log.debug("existing VAR:%s, setting type: %r", name, value.type)
            v.type = value.type
        if metadata:
            if v.metadata is None:
                v.metadata = metadata
            else:
                v.metadata.update(metadata)
        return v

    def addMemberVariable(self, name, value):
        """Add a member variable to this object
        @param name {unicode} The name of the member
        @param value {JSObject} The value to add
        @returns {JSObject} The resulting member (possibly different from
                |value| if one with the given |name| exists)
        """
        assert isinstance(value, JSObject), \
            "addMemberVariable: bad value%r" % (value,)
        v = self.members.get(name, None)
        if v is None:
            v = self.variables.get(name, None)
        if v is None:
            log.info("CLASSMBR: %r, in %s %r", name, self.cixname, self.name)
            self.members[name] = v = value
        # Else if there is no citdl type yet, assign it the given type
        elif value.type and not v.type:
            log.debug("existing VAR:%s, setting type: %r", name, value.type)
            v.type = value.type
        return v

    def getReturnType(self):
        """Get the JS return type for this function, JSDoc gets precedence."""
        bestType = None
        if self.jsdoc and self.jsdoc.returns:
            bestType = self.jsdoc.returns.paramtype
        elif len(self.returnTypes) > 0:
            d = {}
            bestCount = 0
            bestType = None
            for rtype in self.returnTypes:
                if isinstance(rtype, (str, unicode)):
                    count = d.get(rtype, 0) + 1
                    d[rtype] = count
                    if count > bestCount:
                        bestType = rtype
        if bestType:
            bestType = standardizeJSType(bestType)
        return bestType

    def __repr__(self):
        return "\n".join(self.outline())

    def outline(self, depth=0):
        result = []
        if self.cixname == "function":
            result.append("%s%s %s(%s)" % (" " * depth, self.cixname, self.name, ", ".join(self.args)))
        elif self.cixname == "class" and self.classrefs:
            result.append("%s%s %s [%s]" % (" " * depth, self.cixname, self.name, self.classrefs))
        elif self.cixname == "variable" and (self.type or (self.jsdoc and self.jsdoc.type)):
            result.append("%s%s %s [%s]" % (" " * depth, self.cixname, self.name, self.type or (self.jsdoc and self.jsdoc.type)))
        else:
            result.append("%s%s %s" % (" " * depth, self.cixname, self.name))
        for attrname in ("classes", "members", "functions", "variables"):
            d = getattr(self, attrname, {})
            for v in d.values():
                result += v.outline(depth + 2)
        return result

    def toElementTree(self, cixelement):
        if not self.name:
            log.info("%s has no name, line: %d, ignoring it.",
                     self.cixname, self.line)
            return None
        if self.cixname == "function":
            cixobject = createCixFunction(cixelement, self.name)
        elif self.cixname in ("object", "variable"):
            cixobject = createCixVariable(cixelement, self.name)
        elif self.cixname in ("class"):
            cixobject = createCixClass(cixelement, self.name)
        #else:
        #    print "self.cixname: %r" %(self.cixname)

        cixobject.attrib["line"] = str(self.line)
        if self.lineend >= 0:
            cixobject.attrib["lineend"] = str(self.lineend)
        if ADD_PATH_CIX_INFO and self.path:
            cixobject.attrib["path"] = self.path

        jsdoc = self.jsdoc
        if jsdoc:
            #print "jsdoc: %r" % (jsdoc)
            # the docstring
            #docElem.text = self.doc
            attributeDocs = []
            if jsdoc.isDeprecated():
                attributeDocs.append("DEPRECATED")
                self.attributes.append("deprecated")
            if jsdoc.isPrivate():
                attributeDocs.append("PRIVATE")
                if "private" not in self.attributes:
                    self.attributes.append("private")
            if jsdoc.isStatic():
                attributeDocs.append("STATIC")
                if "__static__" not in self.attributes:
                    self.attributes.append("__static__")
            if jsdoc.isConstant():
                attributeDocs.append("CONSTANT")
                if "constant" not in self.attributes:
                    self.attributes.append("constant")
            if jsdoc.isConstructor():
                attributeDocs.append("CONSTRUCTOR")
                if "__ctor__" not in self.attributes:
                    self.attributes.append("__ctor__")
            if jsdoc.is__local__():
                attributeDocs.append("__LOCAL__")
                if "__local__" not in self.attributes:
                    self.attributes.append("__local__")
            if jsdoc.tags:
                cixobject.attrib["tags"] = jsdoc.tags
            if jsdoc.doc:
                if attributeDocs:
                    setCixDoc(cixobject, "%s: %s" % (" ".join(attributeDocs), jsdoc.doc))
                else:
                    setCixDoc(cixobject, jsdoc.doc)

        # Additional one-off attributes
        if self.attributes:
            cixobject.attrib["attributes"] = " ".join(self.attributes)

        # Additional meta-data.
        if self.metadata:
            for key, value in self.metadata.items():
                cixobject.attrib[key] = value

        # Add the type information, JSDoc overrides whatever the ciler found
        if jsdoc and jsdoc.type:
            # Convert the value into a standard name
            addCixType(cixobject, standardizeJSType(jsdoc.type))
        elif self.type:
            assert isinstance(self.type, (str, unicode)), \
                "self.type %r is not a str" % (self.type)
            addCixType(cixobject, standardizeJSType(self.type))

        if isinstance(self, JSFunction):
            signature = "%s(" % (self.name)
            # Add function arguments
            if self.args:
                signature += ", ".join(self.args)
                # Add function arguments to tree
            # Add signature - calltip
            signature += ")"
            cixobject.attrib["signature"] = signature
            # Add return type for functions, JSDoc gets precedence
            returnType = self.getReturnType()
            if returnType:
                addCixReturns(cixobject, returnType)

            # Add a "this" member for class functions
            if self._class:
                createCixVariable(cixobject, "this", vartype=self._class.name)
            elif self.parent and self.parent.cixname in ("object", "variable"):
                createCixVariable(cixobject, "this", vartype=self.parent.name)

        if self.cixname == "class":
            for baseclass in self.classrefs:
                addClassRef(cixobject, baseclass)

        allValues = self.functions.values() + self.members.values() + \
                    self.classes.values() + self.variables.values() + \
                    self.anonymous_functions

        # If this is a variable with child elements, yet has a citdl type of
        # something that is not an "Object", don't bother to adding these child
        # elements, as we will just go with what the citdl information holds.
        # http://bugs.activestate.com/show_bug.cgi?id=78484
        # Ideally the ciler should include this information and have the tree
        # handler combine the completions from the citdl and also the child
        # elements, but this is not yet possible.
        if allValues and self.cixname == 'variable' and \
           cixobject.get("citdl") and cixobject.get("citdl") != "Object":
            log.info("Variable of type: %r contains %d child elements, "
                     "ignoring them.", cixobject.get("citdl"), len(allValues))
            return None

        # Sort and include contents
        for v in sortByLine(allValues):
            if not v.isHidden:
                v.toElementTree(cixobject)

        return cixobject

class JSVariable(JSObject):
    def __init__(self, name, parent, line, depth, vartype='', doc=None,
                 isLocal=False, path=None):
        if isinstance(vartype, list):
            vartype = ".".join(vartype)
        JSObject.__init__(self, name, parent, line, depth, type=vartype,
                          doc=doc, isLocal=isLocal, path=path)

class JSAlias(JSVariable):
    """An alias, which is a simple assignment from a variable (or possibly a
    class)."""
    def __init__(self, *args, **kwargs):
        """Initialize the alias
        @param target {list of unicode} The type name expression (e.g. ["Array"]
                or ["window", "document"]) to alias to
        @param scope {JSObject} The scope in which the assignment takes place,
                used to resolve the target
        @see JSVariable.__init__ - all other arguments are inherited
        """
        target = kwargs.pop("target", None)
        assert target is not None, "JSAlias requires a target= keyword argument"
        scope = kwargs.pop("scope", None)
        assert scope is not None, "JSAlias requires a scope= keyword argument"
        JSVariable.__init__(self, *args, **kwargs)
        self.cixname = "variable"
        self.target = target
        self.scope = scope

class JSArgument(JSVariable):
    """An argument for a function (or constructor)"""
    def __init__(self, *args, **kwargs):
        JSVariable.__init__(self, *args, **kwargs)
        self.cixname = "variable"
        if not self.type and ENABLE_HEURISTICS:
            if self.name == 'event': # assume that variables named event are Events
                log.debug("JSArgument: assuming argument named event is a Event")
                self.type = "Event"

    def outline(self, depth=0):
        result = []
        if self.type or (self.jsdoc and self.jsdoc.type):
            result.append("%sargument %s [%s]" % (" " * depth, self.name, self.type or (self.jsdoc and self.jsdoc.type)))
        else:
            result.append("%sargument %s" % (" " * depth, self.name))
        for attrname in ("classes", "members", "functions", "variables"):
            d = getattr(self, attrname, {})
            for v in d.values():
                result += v.outline(depth + 2)
        return result

    def toElementTree(self, *args, **kwargs):
        cixelement = JSVariable.toElementTree(self, *args, **kwargs)
        if cixelement is not None:
            cixelement.attrib["ilk"] = "argument"
        return cixelement

class JSFunction(JSObject):
    """A JavaScript function"""
    def __init__(self, funcname, parent, args, lineno, depth=0, doc=None,
                 isLocal=False, isHidden=False, path=None):
        """Initialize the function
        @param funcname {unicode} The name of the function
        @param parent {JSObject} The parent scope
        @param args {JSArgs} The arguments to the function
        @param lineo {int} The line the function starts at
        @param depth {int}
        @param doc {list of unicode} Documentation comment for the function
        @param isLocal {bool} Whether this function is local
        @param isHidden {bool} Whether this function should be hidden (not
            output into the cix file)
        @param path {list of unicode} The path to the function
        """
        # funcname: string
        # args: list (or None)
        JSObject.__init__(self, funcname, parent, lineno, depth,
                          doc=doc, isLocal=isLocal, isHidden=isHidden, path=path)
        if isinstance(parent, JSClass):
            self._class = parent
        self._parent_assigned_vars = []
        self._callers = set()
        self.args = list(args or [])
        for arg in self.args:
            self.addVariable(arg, JSArgument(name=arg, parent=self, line=lineno,
                                             depth=depth))

    ##
    # @rtype {string or JSObject} add this possible return type
    def addReturnType(self, rtype):
        self.returnTypes.append(rtype)

    def addCaller(self, caller, pos, line):
        """Add caller information to this function"""
        if isinstance(caller, (list, tuple)):
            caller = ".".join(caller)
        self._callers.add((pos, caller, line))

    def toElementTree(self, cixelement):
        if self.jsdoc:
            # fix up argument info from jsdoc
            for jsdocParam in self.jsdoc.params:
                var = self.variables.get(jsdocParam.paramname)
                if isinstance(var, JSArgument):
                    var.type = standardizeJSType(jsdocParam.paramtype)
                    # fake a JSDoc (since it's already all parsed)
                    var.jsdoc = JSDoc()
                    var.jsdoc.doc = jsdocParam.doc
        cixobject = JSObject.toElementTree(self, cixelement)
        if not cixobject:
            return cixobject
        for pos, caller, line in self._callers:
            SubElement(cixobject, "caller", citdl=caller,
                       pos=str(pos), line=str(line), attributes="__hidden__")
        return cixobject

class JSClass(JSObject):
    """A JavaScript class object (a function with a non-default .prototype)"""
    def __init__(self, name, parent, lineno, depth, doc=None, path=None):
        """Initialize the class
        @see JSObject.__init__
        """
        JSObject.__init__(self, name, parent, lineno, depth, doc=doc, path=path)
        self.constructor = name

class JSFile:
    """CIX specifies that a <file> tag have zero or more <module> children.
    In JavaScript this is a one-to-one relationship, so this class represents both
    (and emits the XML tags for both).
    """
    def __init__(self, path, mtime=None):
        self.path = path
        self.name = os.path.basename(path)
        self.parent = None
        self.cixname = self.__class__.__name__[2:].lower()
        #XXX Drop mtime when move to CIX 2.0.
        if mtime is None: mtime = "XXX"
        self.mtime = mtime

        self.functions = {} # functions declared in file
        self.anonymous_functions = [] # anonymous functions declared in file
        self.classes = {} # classes declared in file
        self.variables = {} # all variables used in file

    def __repr__(self):
        return "\n".join(self.outline())

    def getFullPath(self):
        return [self.name]

    def isAnonymous(self):
        return False

    def outline(self):
        result = ["File: %r" % (self.name) ]
        for attrname in ("classes", "functions", "variables"):
            d = getattr(self, attrname, {})
            for v in d.values():
                result += v.outline(2)
        return result

    def hasChildren(self):
        return self.variables or self.functions or self.classes

    def _findScopeWithName(self, name, scopeStack, type="variables"):
        """Find a object somewhere on the given scope stack with the given name
        @param name {unicode} The name to look for
        @param scopeStack {list of JSObject} The scope stack, with the outermost
                (and therefore last searched) scope at the lowest index
        @param type {str} The type of property to look for, e.g. "variables",
                "classs", "functions"
        @returns {JSObject or None} The object found, or None
        """
        if not name:
            return None
        log.debug("_findScopeWithName: %r with name:%r in scopeStack:%r", type, name, scopeStack[-1].name)
        # Work up the scope stack looking for the name
        #for scopePos in range(len(scope) - 1, -1, -1):
        #    currentScope = scope[scopePos]
        for scopePos in range(len(scopeStack) - 1, -1, -1):
            currentScope = scopeStack[scopePos]
            #print "Looking in scope %r" % (currentScope.name)
            #print "Looking in %s: %r" % (currentScope.__class__.__name__,
            #                             currentScope.name)
            namesDict = getattr(currentScope, type, None)
            if namesDict:
                foundScope = namesDict.get(name)
                if foundScope:
                    log.debug("Found %r in scope:%r(%s)", name,
                              currentScope.name, currentScope.cixname)
                    return foundScope
        log.debug("NO scope found for: %r", name)
        return None

    def _lookupVariableType(self, varType, jsobject, scopeStack, depth=0):
        """Resolves a variable type string to a JSObject representing a well-
                known JavaScript type
        @param varType {str} The type to look up as a dot-separated string, e.g.
                "Foo.Bar.baz" or "Array"
        @param jsobject {JSObject} The starting JSObject candidate (in case
                varType is well-known)
        @param scopeStack {list} The scope stack, with the outermost (and
                therefore last searched) scope at the lowest index
        @param depth {int} (For internal use to prevent deep recursion)
        @returns {JSObject or None} The variable type, or None
        """
        #print "Looking for varType:%r in scope:%r" % (varType, scopeStack[-1].name)
        assert not varType or isinstance(varType, (str, unicode)), \
            "varType %r is not a string" % varType
        if depth < 10 and varType:
            # Don't look any further if it's a known type
            if varType.lower() in known_javascript_types:
                return jsobject
            sp = varType.split(".")
            #print "sp: %r" % (sp)
            namePos = 0
            while namePos < len(sp):
                name = sp[namePos]
                #print "sp[%d]: %r" % (namePos, name)
                foundScope = self._findScopeWithName(name, scopeStack, type="variables")
                alternateScopeStack = scopeStack
                while foundScope and isinstance(foundScope, JSArgument) and \
                  not foundScope.type and foundScope.parent in alternateScopeStack:
                    log.debug("found untyped argument %r on %r, trying next",
                              foundScope.name, foundScope.parent.name)
                    alternateScopeStack[alternateScopeStack.index(foundScope.parent):] = []
                    foundScope = self._findScopeWithName(name, alternateScopeStack, type="variables")
                if not foundScope:
                    #print "Trying member variables"
                    # Then look for a class members with this name
                    foundScope = self._findScopeWithName(name, scopeStack, type="members")
                    #if foundScope:
                    #    print "Found a member variable with this name"
                if not foundScope:
                    # Then look for a class with this name
                    #print "Trying class"
                    foundScope = self._findScopeWithName(name, scopeStack, type="classes")
                    if foundScope:
                        #print "Found a class with this name"
                        # Only search this scope now
                        scopeStack.append(foundScope)
                if not foundScope:
                    break # returns None
                #print "Found scope"
                if isinstance(foundScope, JSVariable):
                    #print "Recursively searching scope"
                    assert foundScope.type is None or isinstance(foundScope.type, (str, unicode)), \
                        "foundScope %r has invalid type %r" % (foundScope, foundScope.type)
                    foundScope = self._lookupVariableType(foundScope.type, foundScope, scopeStack, depth+1)
                #return self._lookupVariableType(foundType, scopeStack)
                namePos += 1
            #print "Returning: %s" % foundScope
            return foundScope
        return None
        #print "jsobject:%r" % (jsobject)
        #print "jsobject.type:%r" % (jsobject.type)

    def _lookupVariableTypes(self, jstypelist, scopeStack):
        """Work out variable types according to their namespace
        @param jstypelist {list of JSObject} The list of types that shold be
            examined
        @param scopeStack {list} The scope stack, with the outermost (and
            therefore last searched) scope at the lowest index
        @returns {None}
        """

        for jstype in jstypelist:
            if hasattr(jstype, "classes"):
                # Recursive lookup for the class variables
                self._lookupVariableTypes(jstype.classes.values(), scopeStack + [jstype])
            if hasattr(jstype, "functions"):
                # Recursive lookup for the function variables
                self._lookupVariableTypes(jstype.functions.values(), scopeStack + [jstype])
            if hasattr(jstype, "variables"):
                for jsvariable in jstype.variables.values():
                    varType = jsvariable.type
                    if varType:
                        actualType = self._lookupVariableType(varType, jsvariable, scopeStack + [jstype])
                        if actualType and actualType != jsvariable:
                            if isinstance(actualType, JSVariable) and not actualType.hasChildren():
                                log.debug("variable %r: replacing type %r with %r",
                                          jsvariable.name, jsvariable.type, actualType.type)
                                jsvariable.type = actualType.type
                            else:
                                log.debug("variable %r: replacing type %r with %r",
                                          jsvariable.name, jsvariable.type, actualType.name)
                                jsvariable.type = actualType.name
            # Lookup function return type values
            if isinstance(jstype, JSFunction):
                for i in range(len(jstype.returnTypes)):
                    returnType = jstype.returnTypes[i]
                    #print "Looking up function return type: %r" % (returnType, )
                    if isinstance(returnType, (str, unicode)):
                        actualType = self._lookupVariableType(returnType, jstype, scopeStack + [jstype])
                        if actualType and actualType != jstype:
                            #print "actualType: %r" % (actualType, )
                            # Use the variable name if it's type is "Object"
                            if isinstance(actualType, JSVariable) and \
                               actualType.type != "Object":
                                #print "ActualType is: %r" % (actualType.type)
                                jstype.returnTypes[i] = actualType.type
                            else:
                                #print "ActualType is: %r" % (actualType.name)
                                jstype.returnTypes[i] = actualType.name

    def _updateClassConstructors(self, jsobject):
        """Recursively update the class constructor name of the given class
        @param jsobject {list of JSObject} The JSClasses (or things things
            containing the JSClasses) to find constructors to mark as ctors
        """
        if isinstance(jsobject, JSClass):
            if jsobject.constructor:
                jsfunc = self._findScopeWithName(jsobject.constructor, [jsobject], type='functions')
                if jsfunc and "__ctor__" not in jsfunc.attributes:
                    log.debug("Making function:%r the constructor for class:%r",
                              jsfunc.name, jsobject.name)
                    jsfunc.attributes.append("__ctor__")
        allObjects = jsobject.functions.values() + jsobject.classes.values() + \
                     jsobject.variables.values()
        if not isinstance(jsobject, JSFile):
            allObjects += jsobject.members.values()
        for subobj in allObjects:
            self._updateClassConstructors(subobj)

    def updateAllScopeNames(self):
        """We've gathered as much information as possible, update all scope
        names as best as possible."""

        log.info("****************************************")
        log.info("Finished scanning, updating all scope names")
        self._lookupVariableTypes([self], [])
        log.info("Updating all class constructor names")
        self._updateClassConstructors(self)

    def addVariable(self, name, value=None, metadata=None):
        """Add the given variable to this file
        @see JSObject.addVariable
        """
        assert value is not None, "no value given"
        v = self.variables.get(name, None)
        if v is None:
            log.info("VAR: %s on line %d, type:%r (class %r)", name, value.line,
                     value.type, type(value))
            self.variables[name] = v = value
        # Else if there is no citdl type yet, assign it the given type
        elif value.type and not v.type:
            log.debug("existing VAR:%s, setting type: %r", name, value.type)
            v.type = value.type
        if metadata:
            if v.metadata is None:
                v.metadata = metadata
            else:
                v.metadata.update(metadata)
        return v

    def convertToElementTreeModule(self, cixmodule):
        """Convert this file to a <scope> in the cix (DOM) tree
        @param cixmodule {Element} The <scope type="blob"> to write to
        """
        # Sort and include contents
        allValues = self.functions.values() + self.variables.values() + \
                    self.classes.values() + self.anonymous_functions
        for v in sortByLine(allValues):
            if not v.isHidden:
                v.toElementTree(cixmodule)

    def convertToElementTreeFile(self, cixelement, file_lang, module_lang=None):
        """Convert this file to a new .cix file
        @param cixelement {Element} The root <codeintel> element in a CIX file
        @param file_lang The language of this file (possibly not JavaScript in
            a mutli-language file)
        @param module_lang The language of this module (defaults to file_lang)
        """
        if module_lang is None:
            module_lang = file_lang
        cixfile = createCixFile(cixelement, self.path, lang=file_lang,
                                mtime=str(self.mtime))
        cixmodule = createCixModule(cixfile, self.name, lang=module_lang,
                                    src=self.path)
        self.convertToElementTreeModule(cixmodule)


class JavaScriptCiler:
    JS_COMMENT_STYLES = (SCE_C_COMMENT,
                        SCE_C_COMMENTDOC,
                        SCE_C_COMMENTLINE,
                        SCE_C_COMMENTLINEDOC,
                        SCE_C_COMMENTDOCKEYWORD,
                        SCE_C_COMMENTDOCKEYWORDERROR)
    UDL_COMMENT_STYLES = (SCE_UDL_CSL_COMMENT,
                          SCE_UDL_CSL_COMMENTBLOCK)

    def __init__(self, mgr, path="", mtime=None, lang="JavaScript"):
        """Initialize the ciler
        @param mgr {codeintel2.manager.Manager} codeintel manager
        @param path {str} Normalized filesystem path to the file being scanned
        @param mtime {str} The last modified timestamp
        @param lang {str} The language being scanned
        """
        self.mgr = mgr
        self.path = path
        self.lang = lang
        # hook up the lexical matches to a function that handles the token

        # Working variables, used in conjunction with state
        self.lineno = 0
        self.last_lineno = 0
        self.depth = 0
        self.styles = []
        self.text = []
        self.in_variable_definition = False  # for multi variable assignment
        self.comment = []
        self.last_comment_and_jsdoc = [None, None]
        self.argumentPosition = 0
        self.argumentTextPosition = 0  # keep track of arg position in self.text
        self.objectArguments = []

        # state : used to store the current JS lexing state
        # state_stack : used to store JS state to return to
        self.state = S_DEFAULT
        self.state_stack = []

        # JScile will store all references for what we scan in
        self.cile = JSFile(path, mtime)
        # Cile information, used to store code structure
        self.currentScope = self.cile
        self._scopeStack = [self.currentScope]
        self.objectStack = [self.currentScope]
        self.currentClass = None
        # Used for determining Javascript closures
        self.bracket_depth = 0
        self.lastText = []
        self.lastScope = None

        self._metadata = {}

        # Document styles used for deciding what to do
        # Note: Can be customized by calling setStyleValues()
        self.JS_WORD        = SCE_C_WORD
        self.JS_IDENTIFIER  = SCE_C_IDENTIFIER
        self.JS_OPERATOR    = SCE_C_OPERATOR
        self.JS_STRINGS     = (SCE_C_STRING, SCE_C_CHARACTER, )
        self.JS_NUMBER      = SCE_C_NUMBER
        # js_cile styles are styles that the ciler uses
        self.JS_CILE_STYLES = self.JS_STRINGS + \
                              (self.JS_WORD, self.JS_IDENTIFIER,
                               self.JS_OPERATOR, self.JS_NUMBER)
                              

    # Allows to change styles used by scanner
    # Needed for UDL languages etc... where the style bits are different
    def setStyleValues(self, wordStyle      = SCE_C_WORD,
                             identiferStyle = SCE_C_IDENTIFIER,
                             operatorStyle  = SCE_C_OPERATOR,
                             stringStyles   = (SCE_C_STRING, SCE_C_CHARACTER, ),
                             numberStyle    = SCE_C_NUMBER,
                             commentStyles  = None):
        self.JS_WORD        = wordStyle
        self.JS_IDENTIFIER  = identiferStyle
        self.JS_OPERATOR    = operatorStyle
        self.JS_STRINGS     = stringStyles
        self.JS_NUMBER      = numberStyle
        self.JS_CILE_STYLES = self.JS_STRINGS + \
                              (self.JS_WORD, self.JS_IDENTIFIER,
                               self.JS_OPERATOR, self.JS_NUMBER)
        if commentStyles:
            self.JS_COMMENT_STYLES = commentStyles

    def _logVariables(self):
        """Helper method to log about the current state"""
        if log.level >= logging.DEBUG:
            log.debug("    lineno:%r, state:%r, depth:%r", self.lineno,
                      self.state, self.depth)
            log.debug("    currentScope: %r", self.currentScope)
            log.debug("")

    def incBlock(self):
        """Increment the block (scope) count"""
        self.depth = self.depth+1
        log.info("incBlock: depth:%d, line:%d, currentScope:%r", self.depth, self.lineno, self.currentScope.name)
        if not self.currentScope:
            log.info("incBlock:: No currentScope available. Defaulting to global file scope.")
            # Use the global file scope then
            self.currentScope = self.cile
        if len(self.objectStack) == 0 or self.currentScope != self.objectStack[-1]:
            # Not the same scope...
            self.objectStack.append(self.currentScope)
        self._scopeStack.append(self.currentScope)

    def decBlock(self):
        """Decrement the block (scope) count"""
        log.info("decBlock: depth:%d, line:%d, leavingScope:%r", self.depth, self.lineno, self.currentScope.name)
        if self.depth > 0:
            self.depth = self.depth-1
            self.lastScope = self.currentScope
            # Update lineend for scope
            if hasattr(self.currentScope, "lineend"):
                self.currentScope.lineend = self.lineno
                if isinstance(self.currentScope, JSClass) and \
                   len(self.currentScope.functions) == 1:
                    jsfunc = self.currentScope.functions.values()[0]
                    if jsfunc.depth == self.depth and jsfunc.lineend == -1:
                        jsfunc.lineend = self.lineno
                        log.debug("Setting lineend: %d for scope %r",
                                 self.lineno, jsfunc)
                log.debug("Setting lineend: %d for scope %r",
                         self.lineno, self.currentScope.name)
            else:
                log.debug("Current scope does not have a lineend: %r",
                         self.currentScope.name)
            self._scopeStack.pop()
            #assert(len(self._scopeStack) > 0)
            if self._scopeStack[-1] != self.objectStack[-1]:
                self.objectStack.pop()
                #assert(len(self.objectStack) > 0)
            self.currentScope = self._scopeStack[-1]
            log.debug("decBlock: currentScope:%r", self.currentScope.name)
            if not self.currentScope:
                log.info("decBlock:: No currentScope available. Defaulting to global file scope.")
                # Use the global file scope then
                self.currentScope = self.cile
                return
            # Update currentClass variable
            oldCurrentClass = self.currentClass
            if isinstance(self.currentScope, JSClass):
                self.currentClass = self.currentScope
                log.debug("Currentclass now: %r", self.currentClass.name)
            elif isinstance(self.currentScope, JSFunction):
                self.currentClass = self.currentScope._class
                if self.currentClass:
                    log.debug("Currentclass now: %r", self.currentClass.name)
                else:
                    log.debug("Currentclass now: %r", self.currentClass)
            else:
                self.currentClass = None
                log.debug("Currentclass now: %r", self.currentClass)
            # Update line number for the current class if it doesn't have one already
            if oldCurrentClass and oldCurrentClass.lineend == -1 and \
               oldCurrentClass != self.currentClass:
                oldCurrentClass.lineend = self.lineno
        else: # Likely there is a syntax error in the document
            log.debug("decBlock:: Scope already at 0. Document has syntax errors.")

    def _findInScope(self, name, attrlist=("variables", ), scope=None):
        """Find the object of the given name in the given scope
        @param name {str} The name of the object to look for
        @param attrlist {seq of str} The attributes to look into (e.g.,
            "variables", "functions", "classes")
        @param scope {JSObject} The scope in which to find the object
        @returns {JSObject or None} The found object, an immediate child of the
            scope.
        """
        assert scope is not None, "Missing scope"
        for attr in attrlist:
            namesDict = getattr(scope, attr, None)
            if namesDict:
                subscope = namesDict.get(name)
                if subscope:
                    log.debug("_findInScope: Found a scope for: %r in %s.%s:",
                              name, scope.name, attr)
                    return subscope
        # Not found
        return None

    def _resolveAlias(self, namelist, scope=None):
        """Resolve the given alias
        @param namelist {seq of str} The path to the alias to resolve
        @param scope {JSObject} The starting scope; defaults to the current scope
        @returns {tuple of scope, {seq of str}} The scope and namelist for the
            (recursively) resolved namelist; alternatively, tuple (None, None)
            if the alias could not be resolved (e.g. not an alias)
        """
        if not namelist:
            return (None, None)
        namelist = namelist[:]
        if scope is None:
            scope = self.currentScope
        lastScope, lastNamelist = scope, namelist[:]
        log.debug("_resolveAlias: Resolving alias %r in scope %r", namelist, scope.name)
        aliasDepth = 0 # prevent infinite loop
        found = False
        while namelist:
            log.debug("_resolveAlias: Looking for %r in scope %r", namelist, scope.name)
            namesDict = getattr(scope, "variables", None)
            if not namesDict:
                # this scope has no variables
                log.debug("_resolveAlias: scope %r has no variables", scope.name)
                break
            name = namelist.pop(0)
            foundVar = namesDict.get(name)
            if foundVar is None:
                # can't find the wanted name
                log.debug("_resolveAlias: scope %r does not have variable %r", scope.name, name)
                break
            if isinstance(foundVar, JSAlias) and aliasDepth < 10:
                lastScope = scope = foundVar.scope
                namelist = foundVar.target + namelist
                lastNamelist = namelist[:]
                aliasDepth += 1
                log.debug("_resolveAlias: found alias %r on %r; new names %r",
                          foundVar.name, scope.name, namelist)
            else:
                # found a non-alias variable
                scope = foundVar
        log.debug("_resolveAlias: finished resolve: scope %r namelist %r depth %r",
                  lastScope.name, lastNamelist, aliasDepth)
        if aliasDepth == 0:
            return (None, None)
        return (lastScope, lastNamelist)

    def _locateScopeForName(self, namelist, attrlist=("variables", ), scope=None):
        """Find the scope referenced by namelist, or if it is not itself a scope,
        the containing scope
        @param namelist {seq of str} The path to the object, e.g. ["foo", "bar"]
        @param attrlist {seq of str} The types of attributes to look at
        @param scope {JSObject} The starting scope; defaults to the current scope
        @returns {JSObject} The object, if it is a scope; otherwise, the scope
            containing the object, if it is a variable.
        """

        if not namelist:
            return None
        namelist = namelist[:] # copy
        if scope is None:
            scope = self.currentScope
        log.debug("Finding in scope: %s.%r with names: %r", scope.name, attrlist, namelist)
        # If variables are defined, also search members, which is the
        # correstponding group for class scopes.
        if "variables" in attrlist:
            attrlist += ("members", )
            noVariables = False
        else:
            # add variables because aliases are stored there
            attrlist += ("variables", )
            noVariables = True
        # Work up the scope stack looking for the classname
        aliasDepth = 0
        while scope:
            currentScope = scope
            log.debug("Looking in scope %r", currentScope.name)
            foundScope = None
            namePos = -1;
            while namePos < len(namelist) - 1:
                namePos = namePos + 1
                name = namelist[namePos]
                #attrToLookIn = "variables"
                #if len(namelist) == 0:
                for attrToLookIn in attrlist:
                    log.debug("Looking for name:%r in %s of scope with name:%r",
                              name, attrToLookIn, currentScope.name)
                    namesDict = getattr(currentScope, attrToLookIn, None)
                    if namesDict:
                        foundScope = namesDict.get(name)
                        if isinstance(foundScope, JSAlias) and aliasDepth < 10:
                            # This is an alias; look again with its target
                            namelist[:namePos+1] = foundScope.target
                            currentScope = scope = foundScope.scope
                            namePos = -1
                            aliasDepth += 1
                            log.debug("_locateScopeForName: encountered alias %r, restarting with %r on %r",
                                      name, namelist, scope.name)
                            break # continue outer for loop
                        elif attrToLookIn == "variables" and noVariables:
                            # we didn't originally want to pick up variables
                            continue
                        if foundScope:
                            log.debug("_locateScopeForName: Found scope %r for: %r", foundScope.name, name)
                            # Look in this sub-scope if we have more names to check
                            if type != "variables" or namePos < len(namelist) - 1:
                                currentScope = foundScope
                            # else we've located the scope we want
                            break # goes to else: of outer for loop at end of namelist
                else:
                    # Not found
                    break
            else:
                log.debug("Found %r in scope:%s.%s", namelist, currentScope.name, attrToLookIn)
                return currentScope
            # Try parent scope
            scope = scope.parent
        log.debug("NO scope found for: %r", namelist)
        return None

    def _lookupVariableTypeFromScope(self, typeNames):
        """See if we can determine what type this is"""
        scope = self._locateScopeForName(typeNames[:-1])
        if scope:
            scope = scope.variables[typeNames[-2]]
            while isinstance(scope, JSVariable) and scope.type not in ("int", "string", "object"):
                scopeType = scope.type
                #print "scope:%r, scope.type:%r" % (scope.name, scopeType)
                scope = self._locateScopeForName(scopeType, attrlist=("variables", "classes"))
            if hasattr(scope, "type"):
                return scope.type
        return []

    ##
    # Create a JSFunction and add it to the current scope
    # @param namelist {list} list of names for the function
    # @param args {list} list of arguments for the function
    # @param doc {list} list of comment strings for given scope
    #
    def addFunction(self, namelist, args=None, doc=None, isLocal=False,
                    isHidden=False):
        log.debug("AddFunction: %s(%s)", namelist, args)
        funcName = namelist[-1]
        toScope = self.currentScope
        if len(namelist) > 1:
            isLocal = False
            scopeNames = namelist[:-1]
            if "prototype" in namelist:
                pIndex = namelist.index("prototype")
                scopeNames = namelist[:pIndex]
                jsclass = self._addClassPart(funcName, self.ADD_CLASS_FUNCTION, scopeNames, args=args, doc=doc, path=self.path)
                # Ensure we onte the currentClass which we'll be working with
                self.currentClass = jsclass
                return
            else:
                toScope = self._findOrCreateScope(namelist[:-1], ('variables', 'classes', 'functions'))
        elif isinstance(toScope, JSFile):
            isLocal = False
        log.info("FUNC: %s(%s) isLocal:%r adding to %s %r", funcName, args,
                 isLocal, toScope.cixname, toScope.name)
        #log.debug("jsdoc: %r", JSDoc("".join(doc)))
        fn = JSFunction(funcName, toScope, args, self.lineno, self.depth,
                        doc=doc, isLocal=isLocal, isHidden=isHidden)
        toScope.functions[fn.name] = fn
        self.currentScope = fn
        # Special jsdoc parameter telling us explicitly that it's a class
        jsdoc_says_class = False
        if fn.jsdoc and fn.jsdoc.isClass():
            jsdoc_says_class = True
        # Also check the last comment, sometimes it's meant for this scope
        if not jsdoc_says_class and self.last_comment_and_jsdoc[0]:
            last_jsdoc = self.last_comment_and_jsdoc[1]
            if last_jsdoc is None:
                last_jsdoc = JSDoc("".join(self.last_comment_and_jsdoc[0]))
                self.last_comment_and_jsdoc[1] = last_jsdoc
                if last_jsdoc.isClass() and \
                   fn.name == last_jsdoc.classname:
                    # Name is same, check the namespace as well if it exists
                    nspc = reversed(last_jsdoc.namespace.split("."))
                    scope = fn.parent
                    for name in nspc:
                        if scope is None or name != scope.name:
                            break
                        scope = scope.parent
                    else:
                        jsdoc_says_class = True
                        fn.jsdoc = last_jsdoc
                        log.debug("last_jsdoc classname: %r, namespace: %r",
                                  last_jsdoc.classname, last_jsdoc.namespace)
        if fn.name and jsdoc_says_class:
            # Ick, this is really a class constructor
            jsclass = self._convertFunctionToClass(fn)
            jsclass.doc = None
            jsclass.jsdoc = None

    ##
    # Create an anonymous JSFunction and add it to the current scope.
    # @param args {list} list of arguments for the function
    # @param doc {list} list of comment strings for given scope
    #
    def addAnonymousFunction(self, args=None, doc=None, isHidden=False):
        log.debug("addAnonymousFunction: (%s)", args)
        toScope = self.currentScope
        fn = JSFunction("(anonymous)", toScope, args, self.lineno, self.depth,
                        doc=doc, isLocal=True, isHidden=isHidden,
                        path=self.path)
        toScope.anonymous_functions.append(fn)
        self.currentScope = fn
        return fn

    ##
    # Create a JSFunction and add it to the current scope
    # @param namelist {list} list of names for the function
    # @param args {list} list of arguments for the function
    # @param doc {list} list of comment strings for given scope
    #
    def addClassFunction(self, namelist, args=None, doc=None):
        log.debug("AddClassFunction: %s(%s)", namelist, args)
        toScope = self.currentClass
        if not toScope:
            # See if it's a function, we'll convert it into a class then
            if isinstance(self.currentScope, JSFunction):
                toScope = self._convertFunctionToClass(self.currentScope)
        if not toScope or len(namelist) > 1:
            self.addFunction(namelist, args, doc)
        else:
            funcName = namelist[-1]
            log.info("FUNC: %s(%s) on line %d", funcName, args, self.lineno)
            fn = JSFunction(funcName, toScope, args, self.lineno, self.depth, doc=doc)
            toScope.functions[fn.name] = fn
            self.currentScope = fn

    ADD_CLASS = 0
    ADD_CLASS_MEMBER = 1
    ADD_CLASS_VARIABLE = 2
    ADD_CLASS_FUNCTION = 3
    ADD_CLASS_PARENT = 4
    ADD_CLASS_CONSTRUCTOR = 5
    def _addClassPart(self, partName, addType, scopeNames=None, args=None, doc=None, path=None, varCtor=JSVariable):
        """Add something to this class
        @param partName {unicode} The name of the thing to add
        @param addType {int} What sort of thing to add; can be one of ADD_CLASS
                (add a new child class), ADD_CLASS_MEMBER (a member varaible),
                ADD_CLASS_VARIABLE (a member variable), ADD_CLASS_FUNCTION (a
                method), ADD_CLASS_PARENT (an object on this class's prototype
                chain), ADD_CLASS_CONSTRUCTOR (a constructor function)
        @param scopeNames {list of unicode} The expression to locate the part
        @param args {JSArguments} The arguments to a method when using
                ADD_CLASS_FUNCTION
        @param doc {list of unicode} The documentation comment for this part
        @param path {list of unicode}
        @param varCtor {callable} The constructor function to create a variable
                for use with ADD_CLASS_MEMBER / ADD_CLASS_VARIABLE; the
                signature should match that of JSVariable
        """
        log.debug("_addClassPart: partName:%r, addType:%r, scopeNames:%r, args:%r",
                  partName, addType, scopeNames, args)
        jsclass = None
        fn = None
        # Find the class to place this part into
        #jsclass = self._findClassWithNames(scopeNames)
        if scopeNames:
            # Look for the class first, then if we don't find it look for
            # a function or variable: bug 70324
            jsclass = self._locateScopeForName(scopeNames, attrlist=("classes", ))
            if jsclass is None:
                jsclass = self._locateScopeForName(scopeNames, attrlist=("classes", "functions", "variables", ))
                if isinstance(jsclass, JSFunction):
                    # Convert it to a class
                    jsclass = self._convertFunctionToClass(jsclass)
        else:
            jsclass = self.currentClass
        if not jsclass and scopeNames:
            if len(scopeNames) > 1:
                toScope = self._findOrCreateScope(scopeNames, attrlist=("classes", "functions", "variables", ))
            else:
                toScope = self.currentScope
            className = scopeNames[-1]
            jsclass = JSClass(className, toScope, self.lineno, self.depth, doc=doc, path=path)
            self.currentScope.classes[jsclass.name] = jsclass
            log.info("CLASS: %r on line %d in %r at depth %d", jsclass.name,
                     jsclass.line, self.currentScope.name, self.depth)
            self.currentScope = jsclass

        if addType == self.ADD_CLASS_FUNCTION:
            log.info("CLASS_FUNC: %s(%s) on line %d", partName, args, self.lineno)
            fn = JSFunction(partName, jsclass, args, self.lineno, self.depth, doc=doc)
            fn._class = jsclass
            jsclass.functions[fn.name] = fn
            #print "num functions: %d" % (len(jsclass.functions))
            self.currentScope = fn
        elif addType == self.ADD_CLASS_MEMBER:
            if partName not in jsclass.variables:
                log.info("CLASS_MBR added: %r", partName)
                v = varCtor(partName, jsclass, self.lineno, self.depth, doc=doc, path=self.path)
                jsclass.variables[partName] = v
            else:
                log.info("CLASS_MBR already exists: %r", partName)
        elif addType == self.ADD_CLASS_VARIABLE:
            if partName not in jsclass.variables:
                log.info("CLASS_VBR added: %r", partName)
                v = varCtor(partName, jsclass, self.lineno, self.depth, doc=doc, path=self.path)
                jsclass.variables[partName] = v
            else:
                log.info("CLASS_MBR already exists: %r", partName)
        elif addType == self.ADD_CLASS_PARENT:
            log.info("CLASS_PARENT: %r", partName)
            jsclass.addClassRef(partName)
        elif addType == self.ADD_CLASS_CONSTRUCTOR:
            log.info("CLASS_CTOR: %r", partName)
            jsclass.constructor = partName

        if jsclass:
            self.currentClass = jsclass
            if addType == self.ADD_CLASS:
                self.currentScope = jsclass
            elif addType == self.ADD_CLASS_PARENT and partName == "Object":
                self.currentScope = jsclass
        return jsclass

    # a class part using prototype.name = function
    #def addClassPart(self):
    #    self._addClassPart()

    # a class using classname.prototype = { ... }
    def addClass(self, namelist, doc=None, path=None, varCtor=JSVariable):
        """Add a new class using scope.classname.prototype = {...}
        @param namelist {list of unicode} The path to get to the class; in the
                example above, ["scope", "classname"]
        @param doc {list of unicode} Documentation comment associated with this class
        @param varCtor {callable} The constructor function to create a variable
                for use with ADD_CLASS_MEMBER / ADD_CLASS_VARIABLE; the
                signature should match that of JSVariable
        """
        jsclass = self._addClassPart(namelist[-1], self.ADD_CLASS, scopeNames=namelist, doc=doc, path=path, varCtor=varCtor)
        return jsclass

    def addAnonymousClass(self, namelist, doc=None):
        # Example syntax: c.prototype = { rows: { return this._rows.length; } }
        self.addClass(namelist[:-1], doc=doc)

    def addClassOrVariableMember(self, namelist, typeNames, scope=None, doc=None,
                                 assignAsCurrentScope=False,
                                 isLocal=False, varCtor=JSVariable):
        """Add the variable to the given scope or current scope

        If the scope is a
          * variable or object: add as a variable to this scope.
          * class: add as a member to this class.
          * function: then this is a little more tricky:
            * If it's class function, then add as a member for the class.
            * If it's a function inside a variable/object, then add as a
              variable to the variable/object.
            * If it's just a function on it's own, turn the function into a
              class and then add a member variable for the class.
        """
        if not scope:
            scope = self.currentScope

        log.debug("addClassOrVariableMember: namelist:%r, type:%r, isLocal:%r, scope (%s):%s",
                  namelist, typeNames, isLocal, scope.cixname, scope.name)
        memberName = namelist[-1]

        if len(namelist) > 2 and "prototype" in namelist:
            pIndex = namelist.index("prototype")
            scopeNames = namelist[:pIndex]
            log.debug("Adding class prototype. class name: %r, variable: %r",
                      scopeNames, memberName)
            scope = self._addClassPart(memberName, self.ADD_CLASS_MEMBER,
                                       scopeNames=scopeNames, args=None, doc=doc,
                                       path=self.path, varCtor=varCtor)
            v = scope

        elif len(namelist) >= 2:
            # Find the scope to apply to.
            scope = self._findOrCreateScope(namelist[:-1],
                                            attrlist=("variables", "classes"),
                                            fromScope=scope)
            v = varCtor(memberName, scope, self.lineno, self.depth,
                        vartype=typeNames, doc=doc, isLocal=isLocal, path=self.path)
            v = scope.addVariable(memberName, value=v)
            if assignAsCurrentScope:
                self.currentScope = v

        elif scope.cixname in ("object", "variable"):
            if isLocal:
                log.warn("addClassOrVariableMember: %s:%d Trying to add %r as "
                         "a local member variable??",
                         self.cile.name, self.lineno, namelist)
                return
            v = varCtor(memberName, scope, self.lineno, self.depth,
                        vartype=typeNames, doc=doc, isLocal=isLocal, path=self.path)
            v = scope.addVariable(memberName, value=v)
            if assignAsCurrentScope:
                self.currentScope = v

        # Special case - classes and anonymous functions
        elif isinstance(scope, JSClass) or scope.isAnonymous():
            v = varCtor(memberName, scope, self.lineno, self.depth,
                        vartype=typeNames, doc=doc, isLocal=isLocal, path=self.path)
            v = scope.addMemberVariable(memberName, value=v)
            if assignAsCurrentScope:
                self.currentScope = v

        elif isinstance(scope, JSFunction):
            # If it's a function already within a class, then thats okay
            parentScope = scope.parent
            if not parentScope:
                log.debug("addClassOrVariableMember: ignoring assignment %r "
                          "into a dummy function", namelist)
                return None
            log.debug("ParentScope is: %s (%s)", parentScope.name, parentScope.cixname)
            if isinstance(parentScope, JSClass):
                self.currentClass = parentScope
                log.debug("Assigning to parent class: %r:%r",
                          parentScope.cixname, parentScope.name)
                v = varCtor(memberName, parentScope, self.lineno, self.depth,
                            typeNames, doc=doc, isLocal=isLocal, path=self.path)
                v = parentScope.addMemberVariable(memberName, value=v)
                if assignAsCurrentScope:
                    self.currentScope = v
            # If it's a function within a variable, then thats okay too
            elif parentScope and parentScope.cixname in ("object", "variable"):
                log.debug("Assigning to parent scope: %r:%r",
                          parentScope.cixname, parentScope.name)
                v = varCtor(memberName, parentScope, self.lineno, self.depth,
                            vartype=typeNames, doc=doc, isLocal=isLocal, path=self.path)
                v = parentScope.addVariable(memberName, value=v)
                # We need to keep track of what we assign in this particular
                # case, as we may later turn this function into it's own class,
                # and then we'll need to grab these "this." variables back!
                # Example code:
                #   var ko = {}
                #   ko.f1 = function() { this.x = 1; }   // x assigned to ko
                #   ko.f1.prototype.run = function() {}  // convert f1 to class
                #   // Now we want ko.x to move into class ko.f1
                scope._parent_assigned_vars.append(v)

                if assignAsCurrentScope:
                    self.currentScope = v
            # Convert the function to class then
            else:
                # If the class name exists already, assign to that class
                func = scope
                funcName = func.name
                jsclass = self._locateScopeForName([funcName], attrlist=("classes", ), scope=scope)
                if not jsclass:
                    log.debug("Creating class %r, function %r now ctor", funcName, funcName)
                    # Turn function into a constructor for the class
                    jsclass = self._convertFunctionToClass(func)
                else:
                    # Update the function class information
                    self._convertFunctionToClassContructor(func, jsclass)
                v = varCtor(memberName, jsclass, self.lineno, self.depth,
                            typeNames, doc=doc, isLocal=isLocal, path=self.path)
                v = jsclass.addMemberVariable(memberName, value=v)
                if assignAsCurrentScope:
                    self.currentScope = v
        elif isinstance(scope, JSFile):
            v = self.addVariable(namelist, typeNames, scope, doc,
                                 assignAsCurrentScope, isLocal,
                                 varCtor=varCtor)
        else:
            log.info("addClassOrVariableMember:: Invalid scope type. Could not add %r to scope: %r - %r",
                     namelist, scope.cixname, scope.name)
            v = None
        return v

    def addClassParent(self, namelist, typeNames):
        log.debug("addClassParent: namelist:%r, typeNames:%r", namelist, typeNames)
        self._addClassPart(".".join(typeNames), self.ADD_CLASS_PARENT, namelist[:-1], path=self.path)

    def addGetter(self, namelist, typeNames, scopeNames=None, doc=None):
        log.debug("addGetter: namelist:%r, type: %r, scopeNames: %r", namelist,
                  typeNames, scopeNames)
        if scopeNames:
            toScope = self._locateScopeForName(scopeNames, attrlist=("variables", "classes"))
            if not toScope:
                log.info("addGetter:: Not adding getter. Could not find scope for: %r",
                         scopeNames)
                return
            self.currentScope = toScope
        else:
            toScope = self.currentScope
        self.addClassOrVariableMember(namelist, typeNames, toScope, doc=doc)

    def addSetter(self, namelist, scopeNames=None, doc=None):
        log.debug("addSetter: namelist:%r, scopeNames: %r", namelist, scopeNames)
        if scopeNames:
            toScope = self._locateScopeForName(scopeNames, attrlist=("variables", "classes"))
            if not toScope:
                log.info("addSetter:: Not adding setter. Could not find scope for: %r",
                         scopeNames)
                return
            self.currentScope = toScope
        else:
            toScope = self.currentScope
        self.addClassOrVariableMember(namelist, [], toScope, doc=doc)

    def _convertFunctionToClassContructor(self, jsfunc, jsclass):
        # Mark it as a constructor if it's not already so marked
        funcName = jsfunc.name
        # Copy attributes across, except for "__ctor__"
        class_attributes = jsfunc.attributes[:]
        if "__ctor__" not in jsfunc.attributes:
            jsfunc.attributes.append("__ctor__")
        else:
            class_attributes.remove("__ctor__")
        jsclass.attributes = class_attributes
        # Might already be the contructor for the class
        if funcName not in jsclass.functions:
            parentScope = jsfunc.parent
            log.debug("Converting function: %r into a class contructor for: %r",
                      funcName, jsclass.name)
            jsclass.functions[funcName] = jsfunc
            # Update references
            if jsfunc.isAnonymous():
                parentScope.anonymous_functions.remove(jsfunc)
                parentScope.anonymous_functions.append(jsclass)
            else:
                parentScope.functions.pop(funcName)
                parentScope.classes[funcName] = jsclass
            # Fix starting line number
            if jsfunc.line < jsclass.line:
                jsclass.line = jsfunc.line
            # Copy over non-local variables from the function to the class,
            # all the local variables stay inside the function scope.
            for varName, v in jsfunc.variables.items():
                isLocal = "__local__" in v.attributes or isinstance(v, JSArgument)
                if not isLocal:
                    # Add to class and remove from the function
                    jsclass.variables[varName] = JSVariable(varName, jsclass, v.line,
                                                            v.depth, v.type, v.doc,
                                                            isLocal=isLocal, path=self.path)
                    del jsfunc.variables[varName]
        parent = jsfunc.parent
        for var in jsfunc._parent_assigned_vars:
            log.debug("Converting function: Moved parent assigned variable %r "
                      "into the class instance", var.name)
            jsclass.members[var.name] = var
            parent.variables.pop(var.name, None)

        # Copy across all non-local members, bug 88549.
        for name, jsobject in jsfunc.variables.items():
            if '__local__' not in jsobject.attributes and not isinstance(jsobject, JSArgument):
                jsclass.variables[name] = jsobject
                jsfunc.variables.pop(name, None)
        for name, jsobject in jsfunc.functions.items():
            if '__local__' not in jsobject.attributes:
                jsclass.functions[name] = jsobject
                jsfunc.functions.pop(name, None)
        for name, jsobject in jsfunc.classes.items():
            if '__local__' not in jsobject.attributes:
                jsclass.classes[name] = jsobject
                jsfunc.classes.pop(name, None)

        jsfunc._parent_assigned_vars = []
        jsfunc._class = jsclass
        jsfunc.setParent(jsclass)
        return jsclass

    def _convertFunctionToClass(self, jsfunc):
        """Convert the provided JSFunction into a JSClass and return it."""
        funcName = jsfunc.name
        log.debug("Creating class %r, from function %r", funcName, funcName)
        jsclass = JSClass(funcName, jsfunc.parent, jsfunc.line, self.depth - 1, jsfunc.doc)
        self._convertFunctionToClassContructor(jsfunc, jsclass)
        if self.currentScope == jsfunc:
            self.currentClass = jsclass
        # Copy across the classrefs from the jsdoc (if any).
        if jsfunc.jsdoc and jsfunc.jsdoc.baseclasses:
            for baseclass in jsfunc.jsdoc.baseclasses:
                jsclass.addClassRef(baseclass)
            jsfunc.jsdoc.baseclasses = []
        return jsclass

    def _convertFunctionToClosureVariable(self, jsfunc):
        funcName = jsfunc.name
        log.info("Creating variable %r, from function closure %r", funcName, funcName)
        jsvariable = JSVariable(funcName, jsfunc.parent, jsfunc.line,
                                jsfunc.depth, jsfunc.type, jsfunc.doc, path=self.path)
        if jsfunc.returnTypes:
            jsro = jsfunc.returnTypes[0]
            #print jsro
            if isinstance(jsro, JSVariable):
                # Convert this object into the variable
                jsro.setParent(jsfunc.parent)
                jsro.line = jsfunc.line
                jsro.name = funcName
                jsvariable = jsro
        parent = jsfunc.parent
        if not jsfunc.isAnonymous():
            parent.functions.pop(funcName, None)
            parent.variables[funcName] = jsvariable
        return jsvariable

    def _findOrCreateScope(self, namelist, attrlist=("variables", ),
                           fromScope=None, isLocal=False):
        # Don't create a window scope - bug 87442.
        global_var = {
            "JavaScript": "window",
            "Node.js":    "global",
        }.get(self.lang)
        if namelist[0] == global_var:
            fromScope = self.cile
            namelist =  namelist[1:]
            if not namelist:
                return fromScope
        # Ensure the scope exists, else create it
        # Find the base scope first
        if fromScope is None:
            fromScope = self.currentScope
        log.debug("_findOrCreateScope: %r, attrlist: %r, from scope: %s",
                  namelist, attrlist, fromScope.name)
        name = namelist[0]

        # Determine where variables get added when they are not found
        if isLocal:
            applyToScope = fromScope
        else:
            applyToScope = self.cile   # Global file level

        resolvedScope, resolvedNamelist = self._resolveAlias(namelist, fromScope)
        if resolvedScope is not None and resolvedNamelist:
            # don't use the resolved namelist if it resolves to an undeclared
            # global object; doing so can cause us to shadow things found in the
            # standard library
            if resolvedScope is not self.cile or \
              self._findInScope(resolvedNamelist[0], attrlist, resolvedScope) is not None:
                fromScope, namelist = resolvedScope, resolvedNamelist

        isTheFirstName = True
        for name in namelist:
            # When looking for the first name of the scope, traverse the parent
            # chain, subsequent names *must* reside within the current scope
            # being checked!
            if isTheFirstName:
                isTheFirstName = False
                scope = self._locateScopeForName([name], attrlist, fromScope)
            else:
                scope = self._findInScope(name, attrlist, fromScope)
            if not scope:
                v = JSVariable(name, applyToScope, self.lineno, self.depth,
                               vartype="Object", path=self.path)
                scope = applyToScope.addVariable(name, value=v)
                log.info("Could not find %r in scope: %r, creating variable (type=Object) for it on scope %r!!!",
                         name, fromScope.name, applyToScope.name)
            fromScope = scope
            applyToScope = scope
        return fromScope

    def addVariable(self, namelist, typeNames, toScope=None, doc=None,
                    assignAsCurrentScope=False, isLocal=False, value=None,
                    varCtor=JSVariable):
        varName = namelist[-1]
        if toScope is None:
            toScope = self.currentScope
        log.debug("addVariable: %r, typeNames:%r, isLocal: %r, scope: %r",
                  namelist, typeNames, isLocal, toScope.name)

        if len(namelist) > 1:
            if namelist[-2] == "prototype":
                # Adding to an existing class then
                toScope = self._locateScopeForName(namelist[:-2], attrlist=("classes", ))
                if not toScope:
                    # Create a class for it then
                    log.debug("Creating class now: %r", namelist[:-2])
                    toScope = self.addClass(namelist[:-2], doc=doc, path=self.path,
                                            varCtor=varCtor)
                    #raise CodeIntelError("Could not find scope for: %r" % (namelist[:-2], ))
                if varName == "constructor":
                    if isinstance(typeNames, JSObject):
                        ctorName = typeNames.type
                    else:
                        ctorName = ".".join(typeNames)
                    func = self._locateScopeForName([ctorName], attrlist=("functions", ))
                    if func:
                        return self._convertFunctionToClassContructor(func, toScope)
                    else:
                        return self._addClassPart(ctorName, self.ADD_CLASS_CONSTRUCTOR,
                                                  namelist[:-2], doc=doc, path=self.path,
                                                  varCtor=varCtor)
                else:
                    return self._addClassPart(varName, self.ADD_CLASS_VARIABLE,
                                              namelist[:-2], doc=doc, path=self.path,
                                              varCtor=varCtor)
            else:
                # Find or create the parent scope
                toScope = self._findOrCreateScope(namelist[:-1],
                                                  ('variables', 'classes',
                                                   'functions'),
                                                  fromScope=toScope,
                                                  isLocal=isLocal)
        elif not isLocal:
            # Try and find the scope we are assigning to, should be in
            # a parent scope somewhere!
            #print("addVariable: namelist:%r, typeNames:%r, isLocal: %r, line: %d" % (namelist, typeNames, isLocal, self.lineno))
            fromscope = toScope
            toScope = self._locateScopeForName(namelist,
                                               ('variables', 'classes',
                                                'functions'),
                                               toScope)
            if toScope is None:
                #if self.text[0] not in ("var", "const"):
                #    sys.stderr.write("Undeclared var in %s:%d, %r in %s %r\n" % (
                #            self.cile.name,
                #            self.lineno, varName, fromscope.cixname, fromscope.name))
                # Place it at the global level then
                toScope = self.cile
            else:
                toScope = toScope.parent

        # Add it to scope if it's not already in there
        if toScope:
            if isinstance(toScope, JSVariable):
                # toScope.type can be None if it's an implicitly defined scope
                # (i.e. ones we picked up by observing properties being set on it)
                if toScope.type is not None and toScope.type.lower() not in ("object", ):
                    # Not going to add sub-variables, as it's likely a class
                    # object already, which has this variable information set
                    #if not toScope.type:
                    #    msg = "Assignment to a unknown type, %s:%d, %r (%s)" % (self.filename, self.lineno, ".".join(namelist), toScope.type)
                    #    print >> sys.stderr, msg
                    return None
            #if not isLocal and varName not in toScope.variables:
            #    print("addVariable: namelist:%r, typeNames:%r, isLocal: %r, line: %d" % (namelist, typeNames, isLocal, self.lineno))
            if value is None:
                value = varCtor(varName, toScope, self.lineno, self.depth,
                                vartype=typeNames, doc=doc, isLocal=isLocal, path=self.path)
            v = toScope.addVariable(varName, value=value, metadata=self._metadata)
            if assignAsCurrentScope:
                self.currentScope = v
            return v

        # We kinda lost the scope somewhere
        return None

    def addObjectVariable(self, namelist, toScope=None, doc=None,
                          isLocal=False):
        if not toScope:
            toScope = self.currentScope
        log.debug("addObjectVariable: namelist:%r, scope:%r", namelist,
                  toScope.name)
        varName = namelist[-1]

        if len(namelist) > 1:
            # Ensure the scope exists, else create it
            toScope = self._findOrCreateScope(namelist[:-1], ("variables", "classes", "functions"), toScope)
            # Assignment to a function, outside the function scope... create a class for it
            if isinstance(toScope, JSFunction):
                toScope = self._convertFunctionToClass(toScope)
        # Add it to scope if it's not already in there
        v = JSVariable(varName, toScope, self.lineno, self.depth,
                       vartype=["Object"], doc=doc, isLocal=isLocal, path=self.path)
        v = toScope.addVariable(varName, value=v)
        self.currentScope = v

    def addReturnObject(self, doc=None):
        log.debug("addReturnObject: scope:%r", self.currentScope.name)
        jsro = JSVariable("", self.currentScope, self.lineno, self.depth, vartype="Object", doc=doc, path=self.path)
        if isinstance(self.currentScope, JSFunction):
            self.currentScope.addReturnType(jsro)
        # else:
        #   TODO: This is ignoring the return type for function getters.
        self.currentScope = jsro
        return jsro

    def addFunctionReturnType(self, typeNames, doc=None):
        if isinstance(self.currentScope, JSFunction):
            log.debug("addFunctionReturnType: type: %r, scope:%r", typeNames, self.currentScope.name)
            self.currentScope.addReturnType(".".join(typeNames))

    ##
    # Read everything up to and including the matching close paren
    # @param styles list
    # @param text list 
    # @param p int position in the styles and text list
    # @param paren string type of parenthesis
    def _getParenArguments(self, styles, text, p, paren=None):
        # Examples:
        #  (arg1, arg2) {
        #   => [(arg1, arg2)]
        #  [row][this.columns[column][0]];
        #   => [row]

        if paren is None:
            paren = text[p]
        parenMatches = { '{': '}', '[': ']', '(': ')' }
        args = []
        oppParen = parenMatches.get(paren)
        if oppParen is None:
            log.info("_getParenArguments:: No matching paren for: %r, " \
                     "ignoring arguments.", paren)
            return args, p
        parenCount = 0
        while p < len(styles):
            args.append(text[p])
            if styles[p] == self.JS_OPERATOR:
                if text[p] == paren:
                    parenCount += 1
                elif text[p] == oppParen:
                    parenCount -= 1
                    if parenCount <= 0:
                        p += 1
                        break
            p += 1
        return args, p

    def _skipOverParenArguments(self, styles, text, p, paren="("):
        args, p = self._getParenArguments(styles, text, p, paren)
        return p

    # Skip over all the variable assignment details. Returns position at
    # the end of the assignment, usually a "," or a ";" character.
    #
    # Examples:
    #    var nGroupIndex = typeof <|>p_nGroupIndex=="number" ?p_nGroupIndex :0,
    #        aGroup = this._getItemGroup(nGroupIndex);
    # should skip to "aGroup = this._getItemGroup(nGroupIndex);"
    def _skipToEndOfVariableAssignment(self, styles, text, p):
        old_p = p
        while p < len(styles):
            style = styles[p]
            if style == self.JS_OPERATOR:
                t = text[p]
                if t in '([{':
                    p = self._skipOverParenArguments(styles, text, p, t)
                    continue
                elif t in ',;':
                    break
            p += 1
        if old_p == p:
            # Ensure we at least move somewhere (avoid recursion)
            p += 1
        log.debug("_skipToEndOfVariableAssignment:: skipped text %r, p: %d",
                  text[old_p:p], p)
        return p

    def _getArgumentsFromPos(self, styles, text, pos):
        log.debug("_getArgumentsFromPos: text: %r", text[pos:])
        if pos < len(styles) and styles[pos] == self.JS_OPERATOR and text[pos] == "(":
            ids = []
            pos += 1
            start_pos = pos
            while pos < len(styles):
                if styles[pos] == self.JS_IDENTIFIER:
                    ids.append(text[pos])
                elif styles[pos] != self.JS_OPERATOR or text[pos] != ",":
                    break
                pos += 1
            return ids, pos
        return None, pos

    def _getIdentifiersFromPos(self, styles, text, pos):
        log.debug("_getIdentifiersFromPos: text: %r", text[pos:])
        start_pos = pos
        ids = []
        last_style = self.JS_OPERATOR
        while pos < len(styles):
            style = styles[pos]
            if style == self.JS_IDENTIFIER:
                if last_style != self.JS_OPERATOR:
                    break
                ids.append(text[pos])
            elif style != self.JS_OPERATOR or text[pos] != "." or \
                last_style != self.JS_IDENTIFIER:
                break
            pos += 1
            last_style = style
        return ids, pos

    ##
    # Grab all necessary citdl information from the given text
    # @param styles list
    # @param text list 
    # @param p int position in the styles and text list
    # @return the citdl list and the position after the last item swallowed
    def _getCitdlTypeInfo(self, styles, text, p):
        log.debug("_getCitdlTypeInfo:: text: %r", text[p:])
        citdl = []
        last_style = self.JS_OPERATOR
        while p < len(styles):
            style = styles[p]
            #log.debug("p: %d, text[p]: %r", p, text[p])
            #print "style: %d, last_style: %d" % (style, last_style)
            if style == self.JS_IDENTIFIER or text[p] == "this":
                if last_style != self.JS_OPERATOR:
                    break
                citdl.append(text[p])
                style = self.JS_IDENTIFIER
            elif style == self.JS_OPERATOR and last_style == self.JS_IDENTIFIER:
                if text[p] == ".":
                    pass
                elif text[p] == ")":
                    # Collect after the closing brace - bug 80581.
                    style = last_style
                elif text[p] == "(":
                    paren_pos = p
                    if citdl == ['require']:
                        # Deal with CommonJS (NodeJS) require statements.
                        args, p = self._getParenArguments(styles, text, p)
                        if len(args) >= 3 and styles[paren_pos+1] in self.JS_STRINGS:
                            self._metadata['required_library_name'] = self._unquoteJsString(args[1])
                            log.debug("Dealing with CommonJS require(%s)",
                                      self._metadata['required_library_name'])
                    else:
                        p = self._skipOverParenArguments(styles, text, p)
                    if citdl:
                        if len(citdl) > 1 and 'QueryInterface' == citdl[-1]:
                            # QueryInterface is specific to xpcom interfaces.
                            citdl = []
                            # Don't want the "." items in the citdl
                            for t in text[paren_pos+1:p-1]:
                                if t != ".":
                                    citdl.append(t)
                        else:
                            citdl[-1] = citdl[-1] + "()"
                    style = self.JS_IDENTIFIER
                    p -= 1   # Are at the pos after the paren, move back to it
                elif text[p] == "[":
                    # Arrays, just read in the arguments and add it to the citdl
                    args, p = self._getParenArguments(styles, text, p, "[")
                    if args and citdl:
                        # Check if this is an xpcom component.
                        if citdl in  (["CC"], ["Cc"],
                                      ["Components", "classes"]) and \
                           (p+2) < len(styles) and \
                           text[p] == "." and \
                           text[p+1] in ("getService", "createInstance") and \
                           text[p+2] == "(":
                            # Add the xpcom interface information.
                            # TODO: Change this once array completions are
                            #       supported
                            citdl, p = self._getArgumentsFromPos(styles, text,
                                                                 p+2)
                        else:
                            citdl[-1] = citdl[-1] + "".join(args)
                    style = self.JS_IDENTIFIER
                    p -= 1  # We are are after the last "]", move back
                else:
                    break
            else:
                break
            p += 1
            last_style = style
        return citdl, p

    def _getVariableType(self, styles, text, p, assignmentChar="="):
        """
        Get the type of the variable
        @param styles {list} The (scintilla) styles for the text
        @param text {list} The tokens to examine
        @param p {int} Offset into text/styles to start looking
        @param assignmentChar {str} The assignment character used
        @returns {tuple} {list} type names,
                         {int} new offset (p),
                         {bool} true if this is a new instance
        """
        log.debug("_getVariableType: text: %r, assign char: %s", text[p:],
                  assignmentChar)
        typeNames = []
        if p >= len(styles):
            # Nothing left to examine
            return typeNames, p, False

        if assignmentChar and styles[p] == self.JS_OPERATOR and \
           text[p] == assignmentChar:
            # Assignment to the variable
            p += 1
        if p < len(styles) and styles[p] == self.JS_OPERATOR and \
           text[p] in "+-":
            # Example: var x = -1;
            # Skip over + and -, commonly used with strings and integers
            p += 1

        isNew = False
        isAlias = False

        if p < len(styles):
            if styles[p] == self.JS_WORD:
                # Keyword
                keyword = text[p]
                if keyword == "new":
                    typeNames, p = self._getIdentifiersFromPos(styles, text, p+1)
                    #if not typeNames:
                    #    typeNames = ["object"]
                    isNew = True
                elif keyword in ("true", "false"):
                    typeNames = ["boolean"]
                elif keyword == "this":
                    typeNames, p = self._getCitdlTypeInfo(styles, text, p)
                    p -= 1   # We are already at the next position, step back
                # Don't record null, as it doesn't help us with anything
                #elif keyword == "null":
                #    typeNames = ["null"]
                p += 1
            elif styles[p] in self.JS_STRINGS:
                typeNames = ["string"]
                p += 1
            elif styles[p] == self.JS_NUMBER:
                typeNames = ["int"]
                p += 1
            elif styles[p] == self.JS_IDENTIFIER:
                typeNames, p = self._getCitdlTypeInfo(styles, text, p)
                if not isNew:
                    # this refers to an identifier without "new", it's an alias
                    isAlias = True
            elif styles[p] == self.JS_OPERATOR:
                if text[p] == "{":
                    # This is actually a newly created object
                    typeNames = ["Object"]
                    p += 1
                elif text[p] == "[":
                    while p+1 < len(styles):
                        if text[p] == "]" and styles[p] == self.JS_OPERATOR:
                            break
                        p += 1
                    typeNames = ["Array"]
                    p += 1
        return typeNames, p, isAlias

    def _unquoteJsString(self, s):
        """Return the string without quotes around it"""
        return Utils.unquoteJsString(s)

    def _getVariableDetail(self, namelist, styles, text, p, assignmentChar="="):
        # this.myname = "123";
        # myclass.prototype.list = function () {
        # this.myname = new function(x, y) {
        # var num = mf.field1;
        # names = { "myname": 1, "yourname": 2 }
        
        log.debug("_getVariableDetail: namelist: %r, text:%r", namelist, text[p:])

        if len(namelist) > 1 and "prototype" in namelist:
            # Check for special class prototypes
            protoName = namelist[-1]
            if protoName == "prototype":
                typeNames, p, isAlias = self._getVariableType(styles, text, p, assignmentChar)
                return (TYPE_PARENT, typeNames, None, p)
            elif namelist[-2] == "prototype":
                typeNames = []
                if p+1 < len(styles) and styles[p+1] in self.JS_STRINGS:
                    typeNames = [self._unquoteJsString(text[p+1])]
                if protoName == "__defineGetter__":
                    return (TYPE_GETTER, typeNames, None, p)
                elif protoName == "__defineSetter__":
                    return (TYPE_SETTER, typeNames, None, p)
        elif len(namelist) == 1 and p+1 < len(styles) and \
             styles[p] == self.JS_IDENTIFIER:
            keyword = namelist[0]
            if keyword == "get":
                # get log() {
                newnamelist, p = self._getIdentifiersFromPos(styles, text, p)
                namelist.pop()
                for name in newnamelist:
                    namelist.append(name)
                log.debug("Found getter:%r", namelist)
                return (TYPE_GETTER, [], None, p)
            elif keyword == "set":
                # set application(value) {
                newnamelist, p = self._getIdentifiersFromPos(styles, text, p)
                namelist.pop()
                for name in newnamelist:
                    namelist.append(name)
                log.debug("Found setter:%r", namelist)
                return (TYPE_SETTER, [], None, p)

        if p+1 < len(styles) and styles[p+1] == self.JS_OPERATOR and text[p+1] == "{":
            # This is actually a newly created object
            return (TYPE_OBJECT, [], None, p+2)
        elif p+2 < len(styles) and styles[p+1] == self.JS_WORD and \
             text[p+1] == "function":
            # Skip over any function name
            # Example:  var f = function my_f(a, b) { }
            p += 2
            while p < len(styles):
                if text[p] == "(":
                    break
                p += 1
            args, p = self._getArgumentsFromPos(styles, text, p)
            return (TYPE_FUNCTION, [], args, p)
        elif p+3 < len(styles) and styles[p+1] == self.JS_WORD and \
             text[p+1] == "new" and text[p+2] == "function":
            # Skip over any function name
            # Example:  var f = new function my_f(a, b) { }
            p += 3
            while p < len(styles):
                if text[p] == "(":
                    break
                p += 1
            args, p = self._getArgumentsFromPos(styles, text, p)
            return (TYPE_FUNCTION, [], args, p)
        else:
            typeNames, p, isAlias = self._getVariableType(styles, text, p, assignmentChar)
            if len(namelist) > 2 and namelist[-2:] == ["prototype", "constructor"]:
                # Foo.prototype.constructor = bar; don't treat as an alias
                pass
            elif isAlias:
                log.debug("_getVariableDetail: %r is an alias to %r",
                          namelist, typeNames)
                return (TYPE_ALIAS, typeNames, None, p)
            return (TYPE_VARIABLE, typeNames, None, p)

    def _variableHandler(self, lineno, styles, text, p, namelist,
                         allowedAssignmentChars="=",
                         isLocal=False):
        log.debug("_variableHandler:: namelist:%r, p:%d, isLocal: %r",
                  namelist, p, isLocal)
        #print "p:", p
        #print "text:", text[p:]

        # The while loop is used to handle multiple variable assignments.
        # Example1:
        #   var x = 1, y = 2, z = 3;
        #     namelist: ['x']
        #     text:     ['=', '1', ',', 'y', '=', '2', ',', 'z', '=', '3', ';']
        #
        # Example2:
        #   var x = y = z = 1;
        #     namelist: ['x']
        #     text:     ['=', 'y', '=', 'z', '=', '1', ';']
        #
        # Example3:
        #   var x, y, z = 1;
        #     namelist: ['x']
        #     text:     [',', 'y', ',', 'z', '=', '1', ';']
        #
        # Example4:
        #  this.ab['xyz']={one:1,"two":2};
        #    namelist: ['this', 'ab']
        #    text:     ['[', "'xyz'", ']', '=', '{']]
        #
        already_looped = False
        while p < len(styles):
            self._metadata = {}
            #log.debug("_variableHandler:: p: %d, text: %r", p, text[p:])
            if already_looped:
                # We've already done one loop, need to get a new namelist
                #     text:     [',', 'y', '=', '2', ',', 'z', '=', '3']
                #log.debug("_variableHandler:: already_looped:: text:%r, p:%d", text[p:], p)
                if text[p] == "=" and styles[p] == self.JS_OPERATOR and len(typeNames) > 0:
                    # Assignment to an assignment (aka Example 2)
                    namelist = typeNames
                elif text[p] != "," or styles[p] != self.JS_OPERATOR:
                    p = self._skipToEndOfVariableAssignment(styles, text, p)
                    if p < len(styles) and text[p] == ";":
                        p += 1
                    continue
                else:
                    # Multiple assignment (aka Example 1)
                    namelist, p = self._getIdentifiersFromPos(styles, text, p+1)

                # The namelist may contain array assignments that we cannot
                # deal with, check to ensure we have a variable assignment that
                # we can deal with.
                #   Handled array assignment examples:
                #     this['field1'] =
                #   Unhandled array assignment examples:
                #     this[0] =
                #     myvar[unknownvar] =
                #
                new_namelist = []
                for name in namelist:
                    if '[' in name:
                        name_parts = name.split('[')
                        for subname in name_parts:
                            if subname.endswith("]"):
                                subname = subname[:-1]
                                # ensure the array reference is a string, otherwise
                                # we cannot do anything with it.
                                if not subname or subname[0] not in "'\"":
                                    log.debug("_variableHandler:: Ignoring non-string indexed array assignment: %r", namelist)
                                    return
                                subname = self._unquoteJsString(subname)
                            new_namelist.append(subname)
                    else:
                        new_namelist.append(name)
                namelist = new_namelist
                log.debug("_variableHandler:: already_looped:: namelist now:%r, p:%d", namelist, p)

            if len(namelist) < 1:
                log.debug("_variableHandler:: Invalid namelist! Text: %r", text)
                return

            # Whether the namelist includes an array piece whose name/scope
            # could not be determined (i.e. foo[myname] = 1), as myname is
            # an unknown.
            unknown_array_namelist = False
 
            if p >= len(styles) or text[p] in ",;":
                # It's a uninitialized variable?
                already_known = False
                if len(namelist) == 1:
                    for varType in ("variables", "classes", "functions", "members"):
                        if namelist[0] in getattr(self.currentScope, varType, {}):
                            # it's a variable we already know about, don't shadow it
                            log.debug("uninitialized variable %r is already known, skipping",
                                      namelist)
                            already_known = True
                            break
                if not already_known:
                    log.debug("Adding uninitialized variable: %r, line: %d",
                              namelist, lineno)
                    self.addVariable(namelist, [],
                                     doc=self.comment,
                                     isLocal=isLocal)
                already_looped = True
                continue

            if p+1 < len(styles) and text[p] == '[' and \
                 styles[p] == self.JS_OPERATOR:
                # It may be an  array assignment (Example4 above).
                unknown_array_namelist = True
                array_args, p = self._getParenArguments(styles, text, p, '[')
                if len(array_args) == 3 and array_args[1][0] in "'\"":
                    unknown_array_namelist = False
                    namelist.append(self._unquoteJsString(array_args[1]))
                    log.debug("Namelist includes an array scope, now: %r",
                              namelist)
                if p >= len(styles):
                    already_looped = True
                    continue

            typeNames = []
            name_prefix = namelist[0]
            assignChar = text[p]
            try_getter_setter = False

            addToClass = False
            assignToCurrentScope = False
            if assignChar == ":" or name_prefix == "this":
                assignToCurrentScope = True
                if name_prefix == "this" or \
                   isinstance(self.currentScope, JSClass):
                    addToClass = True

            if p+1 < len(styles) and len(namelist) == 1 and \
               name_prefix in ("get", "set") and styles[p] == self.JS_IDENTIFIER:
                log.debug("First element in namelist is a getter/setter")
                try_getter_setter = True

            if p+1 < len(styles) and (try_getter_setter or
                                        (styles[p] == self.JS_OPERATOR and
                                         assignChar in allowedAssignmentChars)):
                if name_prefix == "this":
                    namelist = namelist[1:]
                    if len(namelist) < 1:
                        log.debug("_variableHandler:: No namelist for 'this'! Text: %r", text)
                        return
                    name_prefix = namelist[0]
                elif name_prefix[0] in "'\"":
                    # String assignment  { "myfield" : 123, ....
                    name_prefix = self._unquoteJsString(name_prefix)
                    namelist = [name_prefix]
                    # Treat it like a variable/object assignment
                    assignToCurrentScope = True

                # Assignment to the scope
                #print "text[p:]", text[p:]
                varType, typeNames, args, p = self._getVariableDetail(namelist, styles, text, p, assignmentChar=assignChar)
                if varType == TYPE_ALIAS:
                    if len(typeNames) < 1 or len(typeNames) == 1 and typeNames[0] in known_javascript_types:
                        # "alias" to a primitive
                        varType = TYPE_VARIABLE
                varType_mapping = dict([(v, k) for k,v in globals().items() if k.startswith("TYPE_")])
                log.debug("_variableHandler:: varType:%r, typeNames:%r, args:%r, p: %d", varType_mapping.get(varType, varType), typeNames, args, p)
                if varType == TYPE_FUNCTION:
                    if addToClass:
                        log.debug("_variableHandler:: Line %d, class function: %r(%r)",
                                  lineno, namelist, args)
                        self.addClassFunction(namelist, args, doc=self.comment)
                    else:
                        log.debug("_variableHandler:: Line %d, function: %r(%r)",
                                  lineno, namelist, args)
                        self.addFunction(namelist, args, doc=self.comment,
                                         isLocal=(not assignToCurrentScope))
                elif varType == TYPE_VARIABLE or varType == TYPE_ALIAS:
                    if varType == TYPE_VARIABLE:
                        varCtor = JSVariable
                        typeString = "type"
                    else: # TYPE_ALIAS
                        varCtor = lambda *args, **kwargs: \
                            JSAlias(target=typeNames, scope=self.currentScope,
                                    *args, **kwargs)
                        typeString = "alias"

                    if assignToCurrentScope:
                        log.debug("_variableHandler:: Line %d, class member variable: %r (%s=%r)",
                                  lineno, namelist, typeString, typeNames)
                        self.addClassOrVariableMember(namelist, typeNames,
                                                      doc=self.comment,
                                                      isLocal=isLocal,
                                                      varCtor=varCtor)
                    else:
                        if len(namelist) > 1:
                            log.debug("_variableHandler:: Line %d, scoped assignment: %r, %s=%r scope %r",
                                      lineno, namelist, typeString, typeNames, self.currentScope.name)
                        else:
                            log.debug("_variableHandler:: Line %d, local variable assignment: %r, %s=%r scope %r",
                                      lineno, namelist, typeString, typeNames, self.currentScope.name)
                        # XXX - Check this, do we need this hack?
                        if typeNames == ["Object"] and text[-1] == "{":
                            # Turn it into a class
                            log.info("_variableHandler:: Turning Object into class: %r", namelist)
                            #self.addVariable(namelist, typeNames)
                            self.addClass(namelist, doc=self.comment, path=self.path, varCtor=varCtor)
                        else:
                            self.addVariable(namelist, typeNames,
                                             doc=self.comment,
                                             isLocal=isLocal,
                                             varCtor=varCtor)
                    # We ignore any defined functions, as we gain no value from them
                elif varType == TYPE_PARENT:
                    if len(typeNames) > 0:
                        self.addClassParent(namelist, typeNames)
                    else:
                        self.addAnonymousClass(namelist, doc=self.comment)
                elif varType == TYPE_GETTER:
                    log.debug("_variableHandler:: Found getter:%r", namelist)
                    self.addGetter(namelist, [], doc=self.comment)
                elif varType == TYPE_SETTER:
                    log.debug("_variableHandler:: Found setter:%r", namelist)
                    self.addSetter(namelist, doc=self.comment)
                elif varType == TYPE_OBJECT:
                    # var obj = { observer: function() { ... }, count: 10 }
                    if not typeNames:
                        typeNames = ["Object"]
                    if unknown_array_namelist:
                        # Create a dummy object that will then accept any
                        # subsequent scope assignments. This object will *not*
                        # be included in the cix output.
                        log.debug("_variableHandler:: Line: %d, unknown array "
                                  "assingment, creating a dummy variable: %r",
                                  lineno, namelist)
                        self.currentScope = JSObject(None, self.currentScope,
                                                     self.lineno, self.depth,
                                                     "Object", path=self.path)
                    elif assignToCurrentScope:
                        log.debug("_variableHandler:: Line %d, class object variable: %r", lineno,
                                  namelist)
                        self.addClassOrVariableMember(namelist, typeNames,
                                                      doc=self.comment,
                                                      assignAsCurrentScope=True)
                    else:
                        log.debug("_variableHandler:: Line %d, object variable: %r", lineno,
                                  namelist)
                        self.addObjectVariable(namelist, doc=self.comment,
                                               isLocal=isLocal)
                else:
                    log.info("_variableHandler:: Ignoring. Unhandled assignment type: %r",
                             text)
                    return
            else:
                log.debug("_variableHandler:: Line %d, calling scoped variable: %r",
                          lineno, namelist)
                for pos, obj in self.objectArguments:
                    if not isinstance(obj, JSFunction):
                        continue
                    # we have a function, tell it about the caller
                    obj.addCaller(caller=namelist, pos=pos, line=lineno)
            already_looped = True

    def createObjectArgument(self, styles, text):
        log.debug("createObjectArgument")
        #obj = toScope.addVariable(varName, self.lineno, self.depth, "Object", doc=doc)
        obj = JSObject(None, None, self.lineno, self.depth, "Object", path=self.path)
        return obj

    def _addCodePiece(self, styles, text, pos=0):
        if pos >= len(styles):
            return
        lineno = self.lineno

        log.debug("*** Line: %d ********************************", lineno)
        #log.debug("Styles: %r", self.styles)
        log.debug("Text: %r", self.text[pos:])
        log.debug("currentScope: %s %r", self.currentScope.cixname,
                  self.currentScope.name)
        if self.currentClass:
            log.debug("currentClass: %r", self.currentClass.name)
        if self.in_variable_definition:
            log.debug("in_variable_definition: %r", self.in_variable_definition)
        #print "%d: %r" % (lineno, " ".join(self.text[pos:]))
        #log.debug("Comment: %r", self.comment)
        #log.debug("")

        firstStyle = styles[pos]
        if firstStyle == self.JS_WORD:
            # Keyword
            keyword = text[pos]
            if keyword == "function":
                isLocal = not isinstance(self.currentScope, JSFile)
                namelist, p = self._getIdentifiersFromPos(styles, text, pos+1)
                if namelist:
                    args, p = self._getArgumentsFromPos(styles, text, p)
                    log.debug("Line %d, function: %r(%r)",
                              lineno, namelist, args)
                    self.addFunction(namelist, args, doc=self.comment,
                                     isLocal=isLocal)
                else:
                    # We shall add the function, but without a name as it does
                    # not really have one... it's anonymous.
                    args, p = self._getArgumentsFromPos(styles, text, p)
                    self.addAnonymousFunction(args, doc=self.comment)
            elif keyword == "this":
                # Member variable of current object
                p = pos+1
                if p < len(styles) and styles[p] == self.JS_OPERATOR and \
                   text[p] == ".":
                    namelist, p = self._getIdentifiersFromPos(styles, text, p+1)
                    self._variableHandler(lineno, styles, text, p, ["this"] + namelist)
            elif keyword in ("let", "var", "const"):
                # Variable of current scope
                self.in_variable_definition = True
                namelist, p = self._getIdentifiersFromPos(styles, text, pos+1)
                # if in the global/file scope the variable is global also,
                # if the scope is something else, add as a local variable
                if namelist:
                    isLocal = not isinstance(self.currentScope, JSFile)
                    if p < len(styles):
                        self._variableHandler(lineno, styles, text, p, namelist,
                                              isLocal=isLocal)
                    else:
                        log.debug("Adding uninitialized variable: %r, line: %d",
                                  namelist, lineno)
                        self.addVariable(namelist, [],
                                         doc=self.comment,
                                         isLocal=isLocal)
            elif keyword == "return":
                p = pos+1
                if p < len(styles) and styles[p] == self.JS_OPERATOR and \
                   text[p] == "{":
                    # Returning a new object
                    self.addReturnObject(doc=self.comment)
                    ## XXX - Fixme to allow variables with sub-elements
                    #log.debug("Ignoring scope due to return of object")
                    #newstate = S_IGNORE_SCOPE
                else:
                    # Return types are only valid in functions
                    if isinstance(self.currentScope, JSFunction):
                        typeNames, p, isAlias = self._getVariableType(styles, text, pos+1, assignmentChar=None)
                        #varType, typeNames, args, p = self._getVariableDetail([], styles, text, pos, assignmentChar="return")
                        log.debug("Return type: %r", typeNames)
                        self.addFunctionReturnType(typeNames)
            elif keyword == "if":
                # if (....) xyz
                p = self._skipOverParenArguments(styles, text, pos+1)
                self._addCodePiece(styles, text, p)
            elif keyword == "else":
                pos += 1
                # Check for: 'else if (....) xyz'
                if pos < len(styles) and styles[pos] == self.JS_WORD and \
                   text[pos] == "if":
                    pos = self._skipOverParenArguments(styles, text, pos+1)
                self._addCodePiece(styles, text, pos)
            else:
                log.debug("_addCodePiece: Unhandled keyword:%r", keyword)
        elif firstStyle == self.JS_IDENTIFIER:
            isLocal = False
            if self.in_variable_definition:
                if self.currentScope != self.cile and \
                   ((pos > 0 and text[pos-1] == ",") or
                    (self.lastText and self.lastText[-1] == ",")):
                    isLocal = True
                else:
                    self.in_variable_definition = False
            # Defining scope for action
            namelist, p = self._getIdentifiersFromPos(styles, text, pos)
            self._variableHandler(lineno, styles, text, p, namelist,
                                  allowedAssignmentChars=":=",
                                  isLocal=isLocal)
        elif firstStyle == self.JS_OPERATOR:
            if self.lastText and self.lastText[-1] == "{" and \
               text[:2] == ['(', ')'] and isinstance(self.lastScope, JSFunction):
                # It's a closure
                log.debug("Found a closure: function: %r", self.lastScope.name)
                self._convertFunctionToClosureVariable(self.lastScope)
            else:
                # We don't do anything here
                log.debug("Ignoring when starting with an operator")
        elif firstStyle in self.JS_STRINGS:
            # Check for object string names, see below:
            #   "element1": [ 1, "one" ],
            #   "field1": "name",
            #print "String assignment: %r" % (text[pos], )
            #print "Text: %r" % (text, )
            if pos+1 < len(styles) and \
               styles[pos+1] == self.JS_OPERATOR and text[pos+1] == ":":
                self._variableHandler(lineno, styles, text, pos+1,
                                      text[pos:pos+1],
                                      allowedAssignmentChars=":",
                                      isLocal=False)
        else:
            log.debug("Unhandled first style:%d", firstStyle)

        self._resetState()
        #if log.level == logging.DEBUG:
        #    print
        #    print '\n'.join(self.cile.outline())
        #    print

    def _chooseBestVariable(self, jsvar1, jsvar2):
        # 1. Choose the one with a jsdoc.
        if jsvar1.jsdoc and not jsvar2.jsdoc:
            return jsvar1
        if jsvar2.jsdoc and not jsvar1.jsdoc:
            return jsvar2
        # 2. Choose the one with the a citdl.
        if jsvar1.type and not jsvar2.type:
            return jsvar1
        if jsvar2.type and not jsvar1.type:
            return jsvar2
        # 3. Choose the one with the best citdl. We prefer the one
        #    that is not a standard type, because standard types
        #    can be null or boring :D
        citdl1 = standardizeJSType(jsvar1.type)
        citdl2 = standardizeJSType(jsvar2.type)
        if citdl1 in known_javascript_types and \
           not citdl2 in known_javascript_types:
            return jsvar2
        if citdl2 in known_javascript_types and \
           not citdl1 in known_javascript_types:
            return jsvar1
        # 4. Default to the first one given.
        return jsvar1

    def _copyObjectToAnother(self, jsobject, jsother):
        #print
        #print "Full outline:"
        #print '\n'.join(self.cile.outline())
        #print
        #print "jsobject:"
        #print '\n'.join(jsobject.outline())
        #print
        #print "jsother:"
        #print '\n'.join(jsother.outline())

        appliedToGlobalScope = False
        if jsother == self.cile:
            appliedToGlobalScope = True

        for fieldname in ('classes', 'members', 'variables', 'functions', ):
            d_obj = getattr(jsobject, fieldname, {})
            d_oth = getattr(jsother, fieldname, {})
            for name, jsobj in d_obj.items():
                # Check the parents are not the same.
                if jsobj.parent == jsother:
                    parent = jsobj.parent
                    log.warn("%s %r has parent %s %r, file: %s#%d",
                             parent.cixname, parent.name, jsother.cixname,
                             jsother.name, self.cile.name, self.lineno)
                jsobj.setParent(jsother)
                if appliedToGlobalScope:
                    # Remove the __local__ and private attributes
                    if "__local__" in jsobj.attributes:
                        jsobj.attributes.remove("__local__")
                    if "private" in jsobj.attributes:
                        jsobj.attributes.remove("private")
                if fieldname == 'functions' and jsobj._class:
                    jsobj._class = jsobj.parent
            d_oth.update(d_obj)
        # Ensure the variables are not already known as member variables.
        d_members = getattr(jsother, "members", {})
        d_variables = getattr(jsother, "variables", {})
        
        for name, jsobj in d_variables.items():
            if name in d_members:
                # Decide which one to keep then, remove the variable and then
                # replace the member with the best choice.
                del d_variables[name]
                d_members[name] = self._chooseBestVariable(d_members[name],
                                                           jsobj)
                log.info("Dupe found: %s %r has both variable and member %r, "
                         "keeping %r", jsother.cixname, jsother.name, name,
                         d_members[name])

    def _handleDefineProperty(self, styles, text, p):
        # text example:
        #   ['(', 'namespace', ',', '"propname"', ',', '{', ')']
        namelist, p = self._getIdentifiersFromPos(styles, text, p+1)
        if namelist and p+3 < len(styles) and styles[p+1] in self.JS_STRINGS:
            propertyname = self._unquoteJsString(text[p+1])
            if namelist == ["this"]:
                scope = self.currentScope
            else:
                scope = self._findOrCreateScope(namelist, ('variables', 'classes', 'functions'))
            v = JSVariable(propertyname, scope, self.lineno, self.depth)
            scope.addVariable(propertyname, value=v)
            
    def _handleYAHOOExtension(self, styles, text, p):
        # text example:
        #   ['(', 'Dog', ',', 'Mammal', ',', '{', ')']
        #print "YAHOO!!!!!!"
        #print "len(self.objectArguments): %d" % (len(self.objectArguments), )
        if p+5 < len(styles) and text[p] == "(" and len(self.objectArguments) == 1:
            extendClassNamelist, p = self._getIdentifiersFromPos(styles, text, p+1)
            log.debug("_handleYAHOOExtension:: extendClassNamelist: %r", extendClassNamelist)
            parentClassNamelist, p = self._getIdentifiersFromPos(styles, text, p+1)
            if extendClassNamelist and parentClassNamelist:
                # Add class parent reference
                #print "Extending %r, parent %r" % (extendClassNamelist, parentClassNamelist)
                jsclass = self._addClassPart(".".join(parentClassNamelist), self.ADD_CLASS_PARENT, extendClassNamelist, path=self.path)
                # Now add all information from objectArguments
                self._copyObjectToAnother(self.objectArguments[0][1], jsclass)
        #log.setLevel(logging.WARN)

    def _handleDojoExtension(self, type, styles, text, p):
        if p+4 < len(styles) and text[p] == "(" and len(self.objectArguments) == 1:
            if type=='declare':
                extendClassNamelist = self._unquoteJsString(text[p+1]).split('.')
                p+=2
                parentClassNamelist, p = self._getIdentifiersFromPos(styles, text, p+1)
                if len(extendClassNamelist)>1:
                    scope = self._findOrCreateScope(extendClassNamelist[:-1], ('variables', 'classes', 'functions'))
                else:
                    scope = self.currentScope
                #TODO: should use the lineno of dojo.declare rather than self.objectArguments[0][1].line below
                jsclass = JSClass(extendClassNamelist[-1], scope, self.objectArguments[0][1].line, self.depth)
                scope.classes[jsclass.name] = jsclass
                if parentClassNamelist:
                    jsclass = self._addClassPart(".".join(parentClassNamelist), self.ADD_CLASS_PARENT, extendClassNamelist, path=self.path)
                else:
                    args,p = self._getParenArguments(styles,text,p,'[')
                    parentClassNamelists=['']
                    for arg in args[1:-1]:
                        if arg=='{': #super class is null
                        	break
                        if arg==',':
                            parentClassNamelists.append('')
                            continue
                        parentClassNamelists[-1] += arg
                    if len(parentClassNamelists[0]):
                        self._addClassPart(' '.join(parentClassNamelists), self.ADD_CLASS_PARENT, extendClassNamelist, path=self.path)

            else: #extend
                extendClassNamelist, p = self._getIdentifiersFromPos(styles, text, p+1)
                jsclass = self._locateScopeForName(extendClassNamelist, attrlist=("classes", "functions", "variables", ))
                if not jsclass:
                    return
                if isinstance(jsclass, JSFunction):
                    jsclass=self._convertFunctionToClass(jsclass)

            if jsclass:
                obj=self.objectArguments[0][1]
                self._copyObjectToAnother(obj, jsclass)
                for f in jsclass.functions:
                    jsclass.functions[f]._class = jsclass
                for f in jsclass.anonymous_functions:
                    f._class = jsclass
                # Change function constructor name to the class name so that it
                # is correctly recognized by Komodo as the constructor.
                if jsclass.functions.has_key('constructor'):
                    func=jsclass.functions.pop('constructor')
                    func.name=jsclass.name
                    jsclass.functions[jsclass.name]=func

    def _removeObjectFromScope(self, jsobject):
        removename = jsobject.name
        parent = jsobject.parent
        if parent:
            searchScopeNames = ("variables", "functions", "classes",)
            if not isinstance(parent, JSFile):
                searchScopeNames += ("members", )
            for scopeName in searchScopeNames:
                scope = getattr(parent, scopeName)
                if removename in scope and scope[removename] == jsobject:
                    log.debug("Removing %r from scope: %s in %r",
                              removename, scopeName, parent.name)
                    scope.pop(removename)
            if jsobject in parent.anonymous_functions:
                parent.anonymous_functions.remove(jsobject)

    def _handleFunctionApply(self, namelist=None):
        """Everything in the function is applied to the supplied scope/namelist"""
        # XXX : TODO
        #       Not everything should be applied. Only the "this." items get
        #       applied!
        # Examples:
        #   (function() { this.xyz = 1; }).apply(namelist);
        #   // Giving namelist an xyz member.

        if namelist is None:
            scope = self.cile
        else:
            # Find the scope
            scope = self._findOrCreateScope(namelist, attrlist=('variables', 'classes', 'functions', ))
        if self.lastScope and isinstance(self.lastScope, JSFunction):
            applyFrom = self.lastScope
            parent = applyFrom.parent
            if isinstance(parent, JSClass) and \
               parent.name == applyFrom.name:
                # We apply everything from the parent then, except the function
                # itself, start by copying everything inside the function.
                self._copyObjectToAnother(applyFrom, scope)
                # Remove the function now
                del parent.functions[applyFrom.name]
                # The class/parent becomes our next target to copy
                applyFrom = parent
            # Copy across everything in the applyFrom object
            self._copyObjectToAnother(applyFrom, scope)
            # We need to remove the applyFrom object, it's life is done
            self._removeObjectFromScope(applyFrom)
        elif self.lastScope and isinstance(self.lastScope, JSVariable):
            self._copyObjectToAnother(self.lastScope, scope)
        elif self.objectArguments and isinstance(self.objectArguments[0][1], JSObject):
            self._copyObjectToAnother(self.objectArguments[0][1], scope)

    def _handleFunctionWithArguments(self):
        styles = self.styles
        if len(styles) == 0:
            return
        text = self.text
        lineno = self.lineno

        log.debug("*** _handleFunctionWithArguments line: %d ***", lineno)
        #log.debug("Styles: %r", self.styles)
        log.debug("Text: %r", self.text)
        #log.debug("Comment: %r", self.comment)
        #log.debug("")

        pos = 0
        firstStyle = styles[pos]
        getsetPos = None
        try:
            getsetPos = text.index("__defineGetter__")
        except ValueError:
            try:
                getsetPos = text.index("__defineSetter__")
            except ValueError:
                pass
        if getsetPos is not None and len(styles) > getsetPos+3 and \
           styles[getsetPos+2] in self.JS_STRINGS:
            scopeNames, p = self._getIdentifiersFromPos(styles, text, pos)
            namelist = [ self._unquoteJsString(text[getsetPos+2]) ]
            if scopeNames and scopeNames[0] != "this":
                namelist = scopeNames[:-1] + namelist
            if text[getsetPos] == "__defineSetter__":
                self.addSetter(namelist, doc=self.comment)
            else:
                # Getter is different, it can have a type.
                citdl = None
                for i, scope in self.objectArguments:
                    if isinstance(scope, JSFunction):
                        self.lineno = scope.line
                        citdl = scope.getReturnType()
                        break
                if citdl:
                    self.addGetter(namelist, [citdl], doc=self.comment)
                else:
                    self.addGetter(namelist, [], doc=self.comment)
        elif firstStyle == self.JS_IDENTIFIER:
            namelist, p = self._getIdentifiersFromPos(styles, text, pos)
            if not namelist:
                return
            #print "namelist: %r" % (namelist, )
            if namelist == ["Object", "defineProperty"]:
                # Defines a property on a given scope.
                self._handleDefineProperty(styles, text, p)
            elif namelist[0] == "YAHOO" and \
               namelist[1:] in (["extend"], ["lang", "extend"]):
                # XXX - Should YAHOO API catalog be enabled then?
                self._handleYAHOOExtension(styles, text, p)
            elif namelist[0] == "dojo" and \
               namelist[1:] in (["extend"], ["declare"]):
                self._handleDojoExtension(namelist[1], styles, text, p)
            elif namelist == ["Ext", "extend"]:
                # Same as what YAHOO does.
                self._handleYAHOOExtension(styles, text, p)
            elif namelist == ["Ext", "apply"] and text[p:p+1] == ["("]:
                # Similar to the regular function apply (see below)
                namelist, p = self._getIdentifiersFromPos(styles, text, p+1)
                if namelist:
                    log.info("Handling Ext.apply on: %r, line: %d", namelist, self.lineno)
                    self._handleFunctionApply(namelist)
        elif firstStyle == self.JS_OPERATOR:
            if text[:4] == [")", ".", "apply", "("]:
                # Special case for function apply
                namelist, p = self._getIdentifiersFromPos(styles, text, pos+4)
                if namelist:
                    self._handleFunctionApply(namelist)
                elif text[3:5] == ["(", ")"]:
                    # Applied to the global namespace
                    self._handleFunctionApply()

    def _findScopeFromContext(self, styles, text):
        """Determine from the text (a namelist) what scope the text is referring
        to. Returns the scope found or None.
        """
        log.debug("_findScopeFromContext: %r" % (text, ))
        scope = None
        try:
            idx = text.index("prototype")
        except ValueError:
            pass
        else:
            # We have a class prototype, find the class and return with that
            # as the current scope. If it's a function that is not part of a
            # class, then convert the function into a class.
            if idx >= 2 and text[idx-1] == ".":
                namelist, p = self._getIdentifiersFromPos(styles[:idx-1], text[:idx-1], 0)
                if namelist:
                    scope = self._locateScopeForName(namelist, attrlist=("classes", ))
                    if not scope:
                        self._locateScopeForName(namelist, attrlist=("functions", ))
                        if isinstance(scope, JSFunction):
                            # Scope is a function, it should be a class,
                            # convert it now.
                            scope = self._convertFunctionToClass(scope)
                    if scope:
                        log.debug("_findScopeFromContext: found %s %r",
                                  scope.cixname, scope.name)
        return scope

    def _resetState(self, newstate=S_DEFAULT):
        self.state = newstate
        self.bracket_depth = 0
        self.styles = []
        self.lastText = self.text
        self.text = []
        if self.comment:
            self.last_comment_and_jsdoc = [self.comment, None]
        self.comment = []
        self.argumentPosition = 0
        self.argumentTextPosition = 0
        self.objectArguments = []
        #log.debug("Set state %d, line: %d", self.state, self.lineno, )

    def _popPreviousState(self, keep_style_and_text=False):
        current_styles = self.styles
        current_text = self.text
        current_arguments = self.objectArguments
        previous_state = self.state
        if len(self.state_stack) >= 1:
            # Reset to previous state
            self.state, self.bracket_depth, self.styles, \
                self.text, self.lastText, self.comment, \
                self.argumentPosition, self.argumentTextPosition, \
                self.objectArguments, \
                self.in_variable_definition = self.state_stack.pop()
        else:
            # Reset them all
            self._resetState()
        log.debug("_popPreviousState:: previous: %d, current: %d",
                  previous_state, self.state)
        if keep_style_and_text:
            self.styles += current_styles
            self.text += current_text
            self.objectArguments = current_arguments

    def _pushAndSetState(self, newstate=S_DEFAULT):
        self.state_stack.append((self.state, self.bracket_depth, self.styles,
                                 self.text, self.lastText, self.comment,
                                 self.argumentPosition,
                                 self.argumentTextPosition,
                                 self.objectArguments,
                                 self.in_variable_definition))
        self._resetState(newstate)
        self.in_variable_definition = False

    def _endOfScanReached(self):
        """Ensure any remaining text is included in the cile"""
        if len(self.styles) > 0:
            self._addCodePiece(self.styles, self.text, pos=0)

    def token_next(self, style, text, start_column, start_line, **other_args):
        """Loops over the styles in the document and stores important info.
        
        When enough info is gathered, will perform a call to analyze the code
        and generate subsequent language structures. These language structures
        will later be used to generate XML output for the document."""

        if style in self.JS_CILE_STYLES:
            # We keep track of these styles and the text associated with it.
            # When we gather enough info, these will be sent to the
            # _addCodePiece() function which will analyze the info.

            # We want to use real line numbers starting from 1 (not 0)
            start_line += 1
            #print "state: %d, text: %r" % (self.state, self.text, )
            #log.debug("state: %d, line: %d, self.text: %r, text: %r", self.state, start_line, self.text, text)

            if self.state == S_DEFAULT and len(self.styles) > 0 and \
               self.last_lineno < start_line:
                # We have moved down line(s) and we have data, check if we
                # need to add code from the previous line(s)
                # XXX: Need to be careful with e4x!
                if ((style != self.JS_OPERATOR or text[0] not in "({[.,=") and
                    (self.styles[-1] != self.JS_OPERATOR or
                     self.text[-1] not in "({[.,=") and
                    # We need to ignore certains cases, such as:
                    #   "new \n function", see bug 82569.
                    (self.styles[-1] != self.JS_WORD or self.text[-1] != "new")):
                    self._addCodePiece(self.styles, self.text, pos=0)
                    self.in_variable_definition = False
            self.lineno = start_line
            if style != self.JS_OPERATOR:
                self.styles.append(style)
                self.text.append(text)
            else:
                if text == "(": # Only the "(", it's like above
                    # Check if this is of the form "(function { .... })"
                    # This is a fix for self invoking functions/closures
                    #   http://bugs.activestate.com/show_bug.cgi?id=63297
                    if not self.text:
                        log.debug("Ignoring initial brace: '(' on line %d",
                                  self.lineno)
                        return
                #log.debug("token_next: line %d, %r, text: %r" % (self.lineno, text, self.text))
                for op in text:
                    self.styles.append(style)
                    self.text.append(op)
                    #if self.state == S_OBJECT_ARGUMENT:
                    #    if op not in "{}":
                    #        continue
                    if op == "(":
                        if self.bracket_depth == 0:
                            # We can start defining arguments now
                            log.debug("Entering S_IN_ARGS state, line: %d, col: %d", start_line, start_column)
                            newscope = self._findScopeFromContext(self.styles, self.text)
                            self._pushAndSetState(S_IN_ARGS)
                            if newscope and self.currentScope != newscope:
                                log.debug("Adjusting scope to: %r %r",
                                          newscope.cixname, newscope.name)
                                # Need to temporarily adjust the scope to deal
                                # with getters, setters and class prototypes.
                                self.currentScope = newscope
                            self.argumentTextPosition = len(self.text)
                        self.bracket_depth += 1
                    elif op == ")":
                        self.bracket_depth -= 1
                        if self.bracket_depth <= 0:
                            # Pop the state, but keep the style and text of
                            # the arguments
                            last_state = self.state
                            self._popPreviousState(keep_style_and_text=True)
                            if self.state != S_IN_ARGS and last_state == S_IN_ARGS:
                                self._handleFunctionWithArguments()
                            log.debug("Entering state %d, line: %d, col: %d", self.state, start_line, start_column)
                        elif isinstance(self.lastScope, JSFunction) and self.text[-3:] == ['{', '(', ')']:
                            # It's a function argument closure.
                            self.lastScope = self._convertFunctionToClosureVariable(self.lastScope)
                    #elif op == "=":
                    #    if text == op:
                    #        log.debug("Entering S_IN_ASSIGNMENT state, line: %d, col: %d", start_line, start_column)
                    #        self.state = S_IN_ASSIGNMENT
                    elif op == "{":
                        # Increasing depth/scope, could be an argument object
                        if self.state == S_IN_ARGS:
                            # __defineGetter__("num", function() { return this._num });
                            argTextPos = self.argumentTextPosition
                            if len(self.text) >= 2 and self.text[-2] == ")":
                                # foo( ... ( ... ) {
                                # this really only makes sense as a function expression definition
                                # foo( ... function (...) {
                                # this function may have multiple arguments, so we can't trust
                                # self.argumentTextPosition (which was clobbered)
                                try:
                                    argsStart = len(self.text) - list(reversed(self.text)).index("(")
                                    if argsStart > 1:
                                        functionPos = argsStart - 2 # position of "function" keyword
                                        if self.styles[functionPos] == self.JS_IDENTIFIER: # named function
                                            functionPos -= 1
                                        if functionPos > -1 and \
                                           self.styles[functionPos] == self.JS_WORD and \
                                           self.text[functionPos] == "function":
                                            # this is indeed a function; check arguments for sanity
                                            args = self.text[argsStart:-2]
                                            if all(x == ',' for x in args[1::2]):
                                                # Passing a function as one of the arguments,
                                                # need to create a JSFunction scope for this,
                                                # as various information may be needed, i.e.
                                                # a getter function return type.
                                                obj = self.addAnonymousFunction(args=args[::2])
                                                # don't append to self.objectArguments here, we do
                                                # it later when we see the closing brace
                                                self._pushAndSetState(S_DEFAULT)
                                except ValueError:
                                    # no "(" found in self.text
                                    pass
                            elif len(self.text) >= 2 and \
                               ((self.text[-2] == "(" and
                                 self.argumentPosition == 0) or
                                (self.text[-2] == "," and
                                 self.argumentPosition > 0)):
                                # It's an object argument
                                log.debug("Entering S_OBJECT_ARGUMENT state, line: %d, col: %d", start_line, start_column)
                                #print "Entering S_OBJECT_ARGUMENT state, line: %d, col: %d" % (start_line, start_column)
                                obj = self.createObjectArgument(self.styles, self.text)
                                self.currentScope = obj
                                self._pushAndSetState(S_OBJECT_ARGUMENT)
                            else:
                                self._pushAndSetState(S_IN_ARGS)
                        else:
                            self._addCodePiece(self.styles, self.text, pos=0)
                            self._pushAndSetState(S_DEFAULT)
                        self.incBlock()
                    elif op == "}":
                        # Decreasing depth/scope
                        previous_state = self.state
                        if self.state != S_IN_ARGS:
                            # only add this piece if we're not in an arg state
                            self._addCodePiece(self.styles, self.text, pos=0)
                        self._popPreviousState()
                        if self.state == S_IN_ARGS:
                            self.objectArguments.append((self.argumentPosition, self.currentScope))
                            log.debug("Leaving S_OBJECT_ARGUMENT state, entering S_IN_ARGS state, line: %d, col: %d", start_line, start_column)
                            #print "Leaving S_OBJECT_ARGUMENT state, entering S_IN_ARGS state, line: %d, col: %d" % (start_line, start_column)
                        self.decBlock()
                    elif op == "," and self.text[0] not in ("let", "var", "const"):
                        # Ignore when it's inside arguments
                        if self.state == S_IN_ARGS:
                            self.argumentPosition += 1
                            self.argumentTextPosition = len(self.text)
                        else:
                            self._addCodePiece(self.styles, self.text, pos=0)
                    elif op == ";":
                        # Statement is done
                        if self.state != S_IN_ARGS:
                            # only add this piece if we're not in an arg state
                            self._addCodePiece(self.styles, self.text, pos=0)
                        self.in_variable_definition = False
            # Remember the last code line we looked at
            self.last_lineno = self.lineno
        elif style in self.JS_COMMENT_STYLES:
            self.comment.append(text)

    def scan_puretext(self, content, updateAllScopeNames=True):
        """Scan the given pure javascript content"""

        #XXX Should eventually use lang_javascript.JavaScriptLexer()
        #    because (1) it's word lists might differ and (2) the
        #    codeintel system manages one instance of it.
        JavaScriptLexer(self.mgr).tokenize_by_style(content, self.token_next)
        # Ensure we take notice of any text left in the ciler
        self._endOfScanReached()
        if updateAllScopeNames:
            # We've parsed up the JavaScript, fix any variables types
            self.cile.updateAllScopeNames()

    def convertToElementTreeFile(self, cixelement, file_lang, module_lang=None):
        """Store JS information into the cixelement as a file(s) sub element"""
        self.cile.convertToElementTreeFile(cixelement, file_lang, module_lang)

    def convertToElementTreeModule(self, cixmodule):
        """Store JS information into already created cixmodule"""
        self.cile.convertToElementTreeModule(cixmodule)


class Utils(object):
    @staticmethod
    def unquoteJsString(s):
        """Return the string without quotes around it"""
        if len(s) >= 2 and s[0] in "\"'":
            return s[1:-1]
        return s

#---- internal support stuff

def _isident(char):
    return "a" <= char <= "z" or "A" <= char <= "Z" or char == "_"

def _isdigit(char):
    return "0" <= char <= "9"

def _walk_js_scopes(scope, lpath=None):
    """Walk the subscopes of the given element.
    Note that in JavaScript <variable> elements with children are
    considered a scope.  Yields (scope, lpath) depth-first.  The given
    top-level element is not yielded.
    """
    if lpath is None: lpath = []
    for subscope in scope:
        if subscope.tag == "variable" and not subscope: continue
        sublpath = lpath + [subscope.get("name")]
        yield (subscope, sublpath)
        for r in _walk_js_scopes(subscope, sublpath):
            yield r

def _walk_js_symbols(elem, _prefix=None):
    if _prefix:
        lpath = _prefix + (elem.get("name"), )
    else:
        lpath = (elem.get("name"), )
    yield lpath
    if not (elem.tag == "scope" and elem.get("ilk") == "function"):
        for child in elem:
            for child_lpath in _walk_js_symbols(child, lpath):
                yield child_lpath


#---- registration

def register(mgr):
    """Register language support with the Manager."""
    mgr.set_lang_info(lang,
                      silvercity_lexer=JavaScriptLexer(mgr),
                      buf_class=JavaScriptBuffer,
                      langintel_class=JavaScriptLangIntel,
                      import_handler_class=JavaScriptImportHandler,
                      cile_driver_class=JavaScriptCILEDriver,
                      is_cpln_lang=True)

