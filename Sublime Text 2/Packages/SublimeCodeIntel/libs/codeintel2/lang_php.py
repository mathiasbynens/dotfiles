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
#
# Contributors:
#   Shane Caraveo (ShaneC@ActiveState.com)
#   Trent Mick (TrentM@ActiveState.com)
#   Todd Whiteman (ToddW@ActiveState.com)

"""codeintel support for PHP"""

import os
from os.path import isdir, join, basename, splitext, exists, dirname
import sys
import re
import logging
import time
import warnings
from cStringIO import StringIO
import weakref
from glob import glob

from SilverCity.ScintillaConstants import (SCE_UDL_SSL_DEFAULT,
                                           SCE_UDL_SSL_OPERATOR,
                                           SCE_UDL_SSL_IDENTIFIER,
                                           SCE_UDL_SSL_WORD,
                                           SCE_UDL_SSL_VARIABLE,
                                           SCE_UDL_SSL_STRING,
                                           SCE_UDL_SSL_NUMBER,
                                           SCE_UDL_SSL_COMMENT,
                                           SCE_UDL_SSL_COMMENTBLOCK)

from codeintel2.parseutil import *
from codeintel2.phpdoc import phpdoc_tags
from codeintel2.citadel import ImportHandler, CitadelLangIntel
from codeintel2.udl import UDLBuffer, UDLLexer, UDLCILEDriver, is_udl_csl_style, XMLParsingBufferMixin
from codeintel2.common import *
from codeintel2 import util
from codeintel2.indexer import PreloadBufLibsRequest, PreloadLibRequest
from codeintel2.gencix_utils import *
from codeintel2.tree_php import PHPTreeEvaluator
from codeintel2.langintel import (ParenStyleCalltipIntelMixin,
                                  ProgLangTriggerIntelMixin)
from codeintel2.accessor import AccessorCache

if _xpcom_:
    from xpcom.server import UnwrapObject



#---- global data

lang = "PHP"
log = logging.getLogger("codeintel.php")
#log.setLevel(logging.DEBUG)
util.makePerformantLogger(log)

#---- language support


class PHPLexer(UDLLexer):
    lang = lang

def _walk_php_symbols(elem, _prefix=None):
    if _prefix:
        lpath = _prefix + (elem.get("name"), )
    else:
        lpath = (elem.get("name"), )
    yield lpath
    if not (elem.tag == "scope" and elem.get("ilk") == "function"):
        for child in elem:
            for child_lpath in _walk_php_symbols(child, lpath):
                yield child_lpath

class PHPLangIntel(CitadelLangIntel, ParenStyleCalltipIntelMixin,
                   ProgLangTriggerIntelMixin):
    lang = lang

    # Used by ProgLangTriggerIntelMixin.preceding_trg_from_pos()
    trg_chars = tuple('$>:(,@"\' \\')
    calltip_trg_chars = tuple('(')   # excluded ' ' for perf (bug 55497)

    # named styles used by the class
    whitespace_style = SCE_UDL_SSL_DEFAULT
    operator_style   = SCE_UDL_SSL_OPERATOR
    identifier_style = SCE_UDL_SSL_IDENTIFIER
    keyword_style    = SCE_UDL_SSL_WORD
    variable_style   = SCE_UDL_SSL_VARIABLE
    string_style     = SCE_UDL_SSL_STRING
    comment_styles   = (SCE_UDL_SSL_COMMENT, SCE_UDL_SSL_COMMENTBLOCK)
    comment_styles_or_whitespace = comment_styles + (whitespace_style, )

    def _functionCalltipTrigger(self, ac, pos, DEBUG=False):
        # Implicit calltip triggering from an arg separater ",", we trigger a
        # calltip if we find a function open paren "(" and function identifier
        #   http://bugs.activestate.com/show_bug.cgi?id=70470
        if DEBUG:
            print "Arg separater found, looking for start of function"
        # Move back to the open paren of the function
        paren_count = 0
        p = pos
        min_p = max(0, p - 200) # look back max 200 chars
        while p > min_p:
            p, c, style = ac.getPrecedingPosCharStyle(ignore_styles=self.comment_styles)
            if style == self.operator_style:
                if c == ")":
                    paren_count += 1
                elif c == "(":
                    if paren_count == 0:
                        # We found the open brace of the func
                        trg_from_pos = p+1
                        p, ch, style = ac.getPrevPosCharStyle()
                        if DEBUG:
                            print "Function start found, pos: %d" % (p, )
                        if style in self.comment_styles_or_whitespace:
                            # Find previous non-ignored style then
                            p, c, style = ac.getPrecedingPosCharStyle(style, self.comment_styles_or_whitespace)
                        if style in (self.identifier_style, self.keyword_style):
                            return Trigger(lang, TRG_FORM_CALLTIP,
                                           "call-signature",
                                           trg_from_pos, implicit=True)
                    else:
                        paren_count -= 1
                elif c in ";{}":
                    # Gone too far and noting was found
                    if DEBUG:
                        print "No function found, hit stop char: %s at p: %d" % (c, p)
                    return None
        # Did not find the function open paren
        if DEBUG:
            print "No function found, ran out of chars to look at, p: %d" % (p,)
        return None

    #@util.hotshotit
    def trg_from_pos(self, buf, pos, implicit=True, DEBUG=False, ac=None):
        #DEBUG = True
        if pos < 4:
            return None

        #DEBUG = True
        # Last four chars and styles
        if ac is None:
            ac = AccessorCache(buf.accessor, pos, fetchsize=4)
        last_pos, last_char, last_style = ac.getPrevPosCharStyle()
        prev_pos, prev_char, prev_style = ac.getPrevPosCharStyle()
        # Bump up how much text is retrieved when cache runs out
        ac.setCacheFetchSize(20)

        if DEBUG:
            print "\nphp trg_from_pos"
            print "  last_pos: %s" % last_pos
            print "  last_char: %s" % last_char
            print "  last_style: %r" % last_style
            ac.dump()

        try:
            # Note: If a "$" exists by itself, it's styled as whitespace.
            #       Generally we want it to be indicating a variable instead.
            if last_style == self.whitespace_style and last_char != "$":
                if DEBUG:
                    print "Whitespace style"
                WHITESPACE = tuple(" \t\n\r\v\f")
                if not implicit:
                    # If we're not already at the keyword style, find it
                    if prev_style != self.keyword_style:
                        prev_pos, prev_char, prev_style = ac.getPrecedingPosCharStyle(last_style, self.comment_styles)
                        if DEBUG:
                            print "Explicit: prev_pos: %d, style: %d, ch: %r" % (prev_pos, prev_style, prev_char)
                else:
                    prev_pos = pos - 2
                if last_char in WHITESPACE and \
                    (prev_style == self.keyword_style or
                     (prev_style == self.operator_style and prev_char == ",")):
                    p = prev_pos
                    style = prev_style
                    ch = prev_char
                    #print "p: %d" % p
                    while p > 0 and style == self.operator_style and ch == ",":
                        p, ch, style = ac.getPrecedingPosCharStyle(style, self.comment_styles_or_whitespace)
                        #print "p 1: %d" % p
                        if p > 0 and style == self.identifier_style:
                            # Skip the identifier too
                            p, ch, style = ac.getPrecedingPosCharStyle(style, self.comment_styles_or_whitespace)
                            #print "p 2: %d" % p
                    if DEBUG:
                        ac.dump()
                    p, text = ac.getTextBackWithStyle(style, self.comment_styles, max_text_len=len("implements"))
                    if DEBUG:
                        print "ac.getTextBackWithStyle:: pos: %d, text: %r" % (p, text)
                    if text in ("new", "extends"):
                        return Trigger(lang, TRG_FORM_CPLN, "classes", pos, implicit)
                    elif text in ("implements", ):
                        return Trigger(lang, TRG_FORM_CPLN, "interfaces", pos, implicit)
                    elif text in ("use"):
                        return Trigger(lang, TRG_FORM_CPLN, "namespaces", pos, implicit)
                    elif prev_style == self.operator_style and \
                         prev_char == "," and implicit:
                        return self._functionCalltipTrigger(ac, prev_pos, DEBUG)
            elif last_style == self.operator_style:
                if DEBUG:
                    print "  lang_style is operator style"
                    print "Prev char: %r" % (prev_char)
                    ac.dump()
                if last_char == ":":
                    if not prev_char == ":":
                        return None
                    ac.setCacheFetchSize(10)
                    p, c, style = ac.getPrecedingPosCharStyle(prev_style, self.comment_styles)
                    if DEBUG:
                        print "Preceding: %d, %r, %d" % (p, c, style)
                    if style is None:
                        return None
                    elif style == self.keyword_style:
                        # Check if it's a "self::" or "parent::" expression
                        p, text = ac.getTextBackWithStyle(self.keyword_style,
                                                          # Ensure we don't go too far
                                                          max_text_len=6)
                        if DEBUG:
                            print "Keyword text: %d, %r" % (p, text)
                            ac.dump()
                        if text not in ("parent", "self", "static"):
                            return None
                    return Trigger(lang, TRG_FORM_CPLN, "static-members",
                                   pos, implicit)
                elif last_char == ">":
                    if prev_char == "-":
                        p, c, style = ac.getPrevPosCharStyle(ignore_styles=self.comment_styles_or_whitespace)
                        if style in (self.variable_style, self.identifier_style) or \
                           (style == self.operator_style and c == ')'):
                            return Trigger(lang, TRG_FORM_CPLN, "object-members",
                                           pos, implicit)
                        elif DEBUG:
                            print "Preceding style is not a variable, pos: %d, style: %d" % (p, style)
                elif last_char in "(,":
                    # where to trigger from, updated by "," calltip handler
                    if DEBUG:
                        print "Checking for function calltip"

                    # Implicit calltip triggering from an arg separater ","
                    #   http://bugs.activestate.com/show_bug.cgi?id=70470
                    if implicit and last_char == ',':
                        return self._functionCalltipTrigger(ac, prev_pos, DEBUG)

                    if prev_style in self.comment_styles_or_whitespace:
                        # Find previous non-ignored style then
                        p, c, prev_style = ac.getPrecedingPosCharStyle(prev_style, self.comment_styles_or_whitespace)
                    if prev_style in (self.identifier_style, self.keyword_style):
                        return Trigger(lang, TRG_FORM_CALLTIP, "call-signature",
                                       pos, implicit)
                elif last_char == "\\":
                    # Ensure does not trigger when defining a new namespace,
                    # i.e., do not trigger for:
                    #      namespace foo\<|>
                    style = last_style
                    while style in (self.operator_style, self.identifier_style):
                        p, c, style = ac.getPrecedingPosCharStyle(style, max_look_back=30)
                    if style == self.whitespace_style:
                        p, c, style = ac.getPrecedingPosCharStyle(self.whitespace_style, max_look_back=30)
                    if style is None:
                        if DEBUG:
                            print "Triggering namespace completion"
                        return Trigger(lang, TRG_FORM_CPLN, "namespace-members",
                                       pos, implicit)
                    prev_text = ac.getTextBackWithStyle(style, max_text_len=15)
                    if DEBUG:
                        print "prev_text: %r" % (prev_text, )
                    if prev_text[1] != "namespace":
                        if DEBUG:
                            print "Triggering namespace completion"
                        return Trigger(lang, TRG_FORM_CPLN, "namespace-members", pos, implicit)

            elif last_style == self.variable_style or \
                 (not implicit and last_char == "$"):
                if DEBUG:
                    print "Variable style"
                # Completion for variables (builtins and user defined variables),
                # must occur after a "$" character.
                if not implicit and last_char == '$':
                    # Explicit call, move ahead one for real trigger position
                    pos += 1
                if not implicit or prev_char == "$":
                    # Ensure we are not triggering over static class variables.
                    # Do this by checking that the preceding text is not "::"
                    # http://bugs.activestate.com/show_bug.cgi?id=78099
                    p, c, style = ac.getPrecedingPosCharStyle(last_style,
                                                              max_look_back=30)
                    if c == ":" and style == self.operator_style and \
                        ac.getTextBackWithStyle(style, max_text_len=3)[1] == "::":
                        return None
                    return Trigger(lang, TRG_FORM_CPLN, "variables",
                                   pos-1, implicit)
            elif last_style in (self.identifier_style, self.keyword_style):
                if DEBUG:
                    if last_style == self.identifier_style:
                        print "Identifier style"
                    else:
                        print "Identifier keyword style"
                # Completion for keywords,function and class names
                # Works after first 3 characters have been typed
                #if DEBUG:
                #    print "identifier_style: pos - 4 %s" % (accessor.style_at_pos(pos - 4))
                #third_char, third_style = last_four_char_and_styles[2]
                #fourth_char, fourth_style = last_four_char_and_styles[3]
                if prev_style == last_style:
                    trig_pos, ch, style = ac.getPrevPosCharStyle()
                    if style == last_style:
                        p, ch, style = ac.getPrevPosCharStyle(ignore_styles=self.comment_styles)
                        # style is None if no change of style (not ignored) was
                        # found in the last x number of chars
                        #if not implicit and style == last_style:
                        #    if DEBUG:
                        #        print "Checking back further for explicit call"
                        #    p, c, style = ac.getPrecedingPosCharStyle(style, max_look_back=100)
                        #    if p is not None:
                        #        trg_pos = p + 3
                        if style in (None, self.whitespace_style,
                                     self.operator_style):
                            # Ensure we are not in another trigger zone, we do
                            # this by checking that the preceeding text is not
                            # one of "->", "::", "new", "function", "class", ...
                            if style == self.whitespace_style:
                                p, c, style = ac.getPrecedingPosCharStyle(self.whitespace_style, max_look_back=30)
                            if style is None:
                                return Trigger(lang, TRG_FORM_CPLN, "functions",
                                               trig_pos, implicit)
                            prev_text = ac.getTextBackWithStyle(style, max_text_len=15)
                            if DEBUG:
                                print "prev_text: %r" % (prev_text, )
                            if (prev_text[1] not in ("new", "function",
                                                    "class", "interface", "implements",
                                                    "public", "private", "protected",
                                                    "final", "abstract", "instanceof",)
                                        # For the operator styles, we must use
                                        # endswith, as it could follow a "()",
                                        # bug 90846.
                                        and prev_text[1][-2:] not in ("->", "::",)):
                                return Trigger(lang, TRG_FORM_CPLN, "functions",
                                               trig_pos, implicit)
                        # If we want implicit triggering on more than 3 chars
                        #elif style == self.identifier_style:
                        #    p, c, style = ac.getPrecedingPosCharStyle(self.identifier_style)
                        #    return Trigger(lang, TRG_FORM_CPLN, "functions",
                        #                   p+1, implicit)
                        elif DEBUG:
                            print "identifier preceeded by an invalid style: " \
                                  "%r, p: %r" % (style, p, )

                    elif last_char == '_' and prev_char == '_' and \
                         style == self.whitespace_style:
                        # XXX - Check the php version, magic methods only
                        #       appeared in php 5.
                        p, ch, style = ac.getPrevPosCharStyle(ignore_styles=self.comment_styles)
                        if style == self.keyword_style and \
                           ac.getTextBackWithStyle(style, max_text_len=9)[1] == "function":
                            if DEBUG:
                                print "triggered:: complete magic-methods"
                            return Trigger(lang, TRG_FORM_CPLN, "magic-methods",
                                           prev_pos, implicit)

            # PHPDoc completions
            elif last_char == "@" and last_style in self.comment_styles:
                # If the preceeding non-whitespace character is a "*" or newline
                # then we complete for phpdoc tag names
                p = last_pos - 1
                min_p = max(0, p - 50)      # Don't look more than 50 chars
                if DEBUG:
                    print "Checking match for phpdoc completions"
                accessor = buf.accessor
                while p >= min_p and \
                      accessor.style_at_pos(p) in self.comment_styles:
                    ch = accessor.char_at_pos(p)
                    p -= 1
                    #if DEBUG:
                    #    print "Looking at ch: %r" % (ch)
                    if ch in "*\r\n":
                        break
                    elif ch not in " \t\v":
                        # Not whitespace, not a valid tag then
                        return None
                else:
                    # Nothing found in the specified range
                    if DEBUG:
                        print "trg_from_pos: not a phpdoc"
                    return None
                if DEBUG:
                    print "Matched trigger for phpdoc completion"
                return Trigger("PHP", TRG_FORM_CPLN,
                               "phpdoc-tags", pos, implicit)

            # PHPDoc calltip
            elif last_char in " \t" and last_style in self.comment_styles:
                # whitespace in a comment, see if it matches for phpdoc calltip
                p = last_pos - 1
                min_p = max(0, p - 50)      # Don't look more than 50 chars
                if DEBUG:
                    print "Checking match for phpdoc calltip"
                ch = None
                ident_found_pos = None
                accessor = buf.accessor
                while p >= min_p and \
                      accessor.style_at_pos(p) in self.comment_styles:
                    ch = accessor.char_at_pos(p)
                    p -= 1
                    if ident_found_pos is None:
                        #print "phpdoc: Looking for identifier, ch: %r" % (ch)
                        if ch in " \t":
                            pass
                        elif _isident(ch):
                            ident_found_pos = p+1
                        else:
                            if DEBUG:
                                print "No phpdoc, whitespace not preceeded " \
                                      "by an identifer"
                            return None
                    elif ch == "@":
                        # This is what we've been looking for!
                        phpdoc_field = accessor.text_range(p+2,
                                                           ident_found_pos+1)
                        if DEBUG:
                            print "Matched trigger for phpdoc calltip: '%s'" % (
                                        phpdoc_field, )
                        return Trigger("PHP", TRG_FORM_CALLTIP,
                                       "phpdoc-tags", ident_found_pos, implicit,
                                       phpdoc_field=phpdoc_field)
                    elif not _isident(ch):
                        if DEBUG:
                            print "No phpdoc, identifier not preceeded by '@'"
                        # Not whitespace, not a valid tag then
                        return None
                # Nothing found in the specified range
                if DEBUG:
                    print "No phpdoc, ran out of characters to look at."

            # Array completions
            elif last_style == self.string_style and last_char in '\'"':
                if prev_char != '[':
                    if prev_style in self.comment_styles_or_whitespace:
                        # Look back further.
                        prev_pos, prev_char, prev_style = ac.getPrevPosCharStyle(ignore_styles=self.comment_styles_or_whitespace)
                if prev_char == '[':
                    # We're good to go.
                    if DEBUG:
                        print "Matched trigger for array completions"
                    return Trigger("PHP", TRG_FORM_CPLN,
                                   "array-members", pos, implicit,
                                   bracket_pos=prev_pos,
                                   trg_char=last_char)

            # Variable completions inside of comments
            elif prev_char == "$" and last_style in self.comment_styles:
                if DEBUG:
                    print "Comment variable style"
                # Completion for variables (builtins and user defined variables),
                # must occur after a "$" character.
                return Trigger(lang, TRG_FORM_CPLN, "comment-variables",
                               pos-1, implicit)

            elif DEBUG:
                print "trg_from_pos: no handle for style: %d" % last_style

        except IndexError:
            # Not enough chars found, therefore no trigger
            pass

        return None

    #@util.hotshotit
    def preceding_trg_from_pos(self, buf, pos, curr_pos,
                               preceding_trg_terminators=None, DEBUG=False):
        #DEBUG = True
        # Try the default preceding_trg_from_pos handler
        trg = ProgLangTriggerIntelMixin.preceding_trg_from_pos(
                self, buf, pos, curr_pos, preceding_trg_terminators,
                DEBUG=DEBUG)
        if trg is not None:
            return trg

        # Else, let's try to work out some other options
        accessor = buf.accessor
        prev_style = accessor.style_at_pos(curr_pos - 1)
        if prev_style in (self.identifier_style, self.keyword_style):
            # We don't know what to trigger here... could be one of:
            # functions:
            #   apache<$><|>_getenv()...
            #   if(get_e<$><|>nv()...
            # classes:
            #   new Exce<$><|>ption()...
            #   extends Exce<$><|>ption()...
            # interfaces:
            #   implements apache<$><|>_getenv()...
            ac = AccessorCache(accessor, curr_pos)
            pos_before_identifer, ch, prev_style = \
                     ac.getPrecedingPosCharStyle(prev_style)
            if DEBUG:
                print "\nphp preceding_trg_from_pos, first chance for identifer style"
                print "  curr_pos: %d" % (curr_pos)
                print "  pos_before_identifer: %d" % (pos_before_identifer)
                print "  ch: %r" % ch
                print "  prev_style: %d" % prev_style
                ac.dump()
            if pos_before_identifer < pos:
                resetPos = min(pos_before_identifer + 4, accessor.length() - 1)
                ac.resetToPosition(resetPos)
                if DEBUG:
                    print "preceding_trg_from_pos:: reset to position: %d, ac now:" % (resetPos)
                    ac.dump()
                # Trigger on the third identifier character
                return self.trg_from_pos(buf, resetPos,
                                         implicit=False, DEBUG=DEBUG, ac=ac)
            elif DEBUG:
                print "Out of scope of the identifier"

        elif prev_style in self.comment_styles:
            # Check if there is a PHPDoc to provide a calltip for, example:
            #       /** @param $foo foobar - This is field for <|>
            if DEBUG:
                print "\nphp preceding_trg_from_pos::phpdoc: check for calltip"
            comment = accessor.text_range(max(0, curr_pos-200), curr_pos)
            at_idx = comment.rfind("@")
            if at_idx >= 0:
                if DEBUG:
                    print "\nphp preceding_trg_from_pos::phpdoc: contains '@'"
                space_idx = comment[at_idx:].find(" ")
                if space_idx >= 0:
                    # Trigger after the space character.
                    trg_pos = (curr_pos - len(comment)) + at_idx + space_idx + 1
                    if DEBUG:
                        print "\nphp preceding_trg_from_pos::phpdoc: calltip at %d" % (trg_pos, )
                    return self.trg_from_pos(buf, trg_pos,
                                             implicit=False, DEBUG=DEBUG)

    _phpdoc_cplns = [ ("variable", t) for t in sorted(phpdoc_tags) ]

    #@util.hotshotit
    def async_eval_at_trg(self, buf, trg, ctlr):
        if _xpcom_:
            trg = UnwrapObject(trg)
            ctlr = UnwrapObject(ctlr)
        pos = trg.pos
        ctlr.start(buf, trg)
        #print "trg.type: %r" % (trg.type)

        # PHPDoc completions
        if trg.id == ("PHP", TRG_FORM_CPLN, "phpdoc-tags"):
            #TODO: Would like a "javadoc tag" completion image name.
            ctlr.set_cplns(self._phpdoc_cplns)
            ctlr.done("success")
            return

        # PHPDoc calltip
        elif trg.id == ("PHP", TRG_FORM_CALLTIP, "phpdoc-tags"):
            phpdoc_field = trg.extra.get("phpdoc_field")
            if phpdoc_field:
                #print "phpdoc_field: %r" % (phpdoc_field, )
                calltip = phpdoc_tags.get(phpdoc_field)
                if calltip:
                    ctlr.set_calltips([calltip])
            ctlr.done("success")
            return

        elif trg.type in ("classes", "interfaces"):
            # Triggers from zero characters, thus calling citdl_expr_from_trg
            # is no help
            line = buf.accessor.line_from_pos(pos)
            evalr = PHPTreeEvaluator(ctlr, buf, trg, "", line)
            buf.mgr.request_eval(evalr)

        else:
            try:
                citdl_expr = self.citdl_expr_from_trg(buf, trg)
            except CodeIntelError, ex:
                ctlr.error(str(ex))
                ctlr.done("error")
                return
            line = buf.accessor.line_from_pos(pos)
            evalr = PHPTreeEvaluator(ctlr, buf, trg, citdl_expr, line)
            buf.mgr.request_eval(evalr)

    def _citdl_expr_from_pos(self, trg, buf, pos, implicit=True,
                             include_forwards=False, DEBUG=False):
        #DEBUG = True
        #PERF: Would dicts be faster for all of these?
        WHITESPACE = tuple(" \t\n\r\v\f")
        EOL = tuple("\r\n")
        BLOCKCLOSES = tuple(")}]")
        STOPOPS = tuple("({[,&$+=^|%/<;:->!.@?")
        EXTRA_STOPOPS_PRECEDING_IDENT = BLOCKCLOSES # Might be others.

        #TODO: This style picking is a problem for the LangIntel move.
        if trg.type == "comment-variables":
            # Dev note: skip_styles in the other cases below will be a dict.
            skip_styles = set()
        elif implicit:
            skip_styles = buf.implicit_completion_skip_styles
        else:
            skip_styles = buf.completion_skip_styles

        citdl_expr = []
        accessor = buf.accessor

        # Use a cache of characters, easy to keep track this way
        i = pos
        ac = AccessorCache(accessor, i)

        if include_forwards:
            try:
                # Move ahead to include forward chars as well
                lastch_was_whitespace = False
                while 1:
                    i, ch, style = ac.getNextPosCharStyle()
                    if DEBUG:
                        print "include_forwards:: i now: %d, ch: %r" % (i, ch)
                    if ch in WHITESPACE:
                        lastch_was_whitespace = True
                        continue
                    lastch_was_whitespace = False
                    if ch in STOPOPS:
                        if DEBUG:
                            print "include_forwards:: ch in STOPOPS, i:%d ch:%r" % (i, ch)
                        break
                    elif ch in BLOCKCLOSES:
                        if DEBUG:
                            print "include_forwards:: ch in BLOCKCLOSES, i:%d ch:%r" % (i, ch)
                        break
                    elif lastch_was_whitespace:
                        # Two whitespace separated words
                        if DEBUG:
                            print "include_forwards:: ch separated by whitespace, i:%d ch:%r" % (i, ch)
                        break
                # Move back to last valid char
                i -= 1
                if DEBUG:
                    if i > pos:
                        print "include_forwards:: Including chars from pos %d up to %d" % (pos, i)
                    else:
                        print "include_forwards:: No valid chars forward from pos %d, i now: %d" % (pos, i)
            except IndexError:
                # Nothing forwards, user what we have then
                i = min(i, accessor.length() - 1)
                if DEBUG:
                    print "include_forwards:: No more buffer, i now: %d" % (i)
            ac.resetToPosition(i)

        ch = None
        try:
            while i >= 0:
                if ch == None and include_forwards:
                    i, ch, style = ac.getCurrentPosCharStyle()
                else:
                    i, ch, style = ac.getPrevPosCharStyle()
                if DEBUG:
                    print "i now: %d, ch: %r" % (i, ch)

                if ch in WHITESPACE:
                    if trg.type in ("namespaces", "namespace-members"):
                        # Namespaces cannot be split over whitespace.
                        break
                    while ch in WHITESPACE:
                        # drop all whitespace
                        next_char = ch
                        i, ch, style = ac.getPrevPosCharStyle()
                        if ch in WHITESPACE \
                           or (ch == '\\' and next_char in EOL):
                            if DEBUG:
                                print "drop whitespace: %r" % ch
                    # If there are two whitespace-separated words then this is
                    # (likely or always?) a language keyword or declaration
                    # construct at which we want to stop. E.g.
                    #   if foo<|> and ...
                    #   def foo<|>(...
                    #   if \foo<|>(...     # uses a namespace
                    if citdl_expr \
                       and (_isident(citdl_expr[-1]) or citdl_expr[-1] == '\\') \
                       and (_isident(ch) or _isdigit(ch)):
                        if DEBUG:
                            print "stop at (likely?) start of keyword or "\
                                  "declaration: %r" % ch
                        break
                    # Not whitespace anymore, move into the main checks below
                    if DEBUG:
                        print "Out of whitespace: i now: %d, ch: %s" % (i, ch)

                if style in skip_styles: # drop styles to ignore
                    while i >= 0 and style in skip_styles:
                        i, ch, style = ac.getPrevPosCharStyle()
                        if DEBUG:
                            print "drop char of style to ignore: %r" % ch
                elif ch in ":>" and i > 0:
                    # Next char has to be ":" or "-" respectively
                    prev_pos, prev_ch, prev_style = ac.getPrevPosCharStyle()
                    if (ch == ">" and prev_ch == "-") or \
                       (ch == ":" and prev_ch == ":"):
                        citdl_expr.append(".")
                        if DEBUG:
                            print "Turning member accessor '%s%s' into '.'" % (prev_ch, ch)
                        i -= 2
                    else:
                        if DEBUG:
                            print "citdl_expr: %r" % (citdl_expr)
                            print "stop at special stop-operator %d: %r" % (i, ch)
                        break
                elif (ch in STOPOPS or ch in EXTRA_STOPOPS_PRECEDING_IDENT) and \
                     (ch != ")" or (citdl_expr and citdl_expr[-1] != ".")):
                    if ch == '$':
                        # This may not be the end of the road, given static
                        # variables are accessed through "Class::$static".
                        prev_pos, prev_ch, prev_style = ac.peekPrevPosCharStyle()
                        if prev_ch == ":":
                            # Continue building up the citdl then.
                            continue
                    if DEBUG:
                        print "citdl_expr: %r" % (citdl_expr)
                        print "stop at stop-operator %d: %r" % (i, ch)
                    break
                elif ch in BLOCKCLOSES:
                    if DEBUG:
                        print "found block at %d: %r" % (i, ch)
                    citdl_expr.append(ch)
        
                    BLOCKS = { # map block close char to block open char
                        ')': '(',
                        ']': '[',
                        '}': '{',
                    }
                    stack = [] # stack of blocks: (<block close char>, <style>)
                    stack.append( (ch, style, BLOCKS[ch], i) )
                    while i >= 0:
                        i, ch, style = ac.getPrevPosCharStyle()
                        if DEBUG:
                            print "finding matching brace: ch %r (%s), stack %r"\
                                  % (ch, ', '.join(buf.style_names_from_style_num(style)), stack)
                        if ch in BLOCKS and style not in skip_styles:
                            stack.append( (ch, style, BLOCKS[ch]) )
                        elif ch == stack[-1][2] and style not in skip_styles:
                            #XXX Replace the second test with the following
                            #    when LexPython+SilverCity styling bugs are fixed
                            #    (spurious 'stderr' problem):
                            #       and style == stack[-1][1]:
                            stack.pop()
                            if not stack:
                                if DEBUG:
                                    print "jump to matching brace at %d: %r" % (i, ch)
                                citdl_expr.append(ch)
                                break
                    else:
                        # Didn't find the matching brace.
                        if DEBUG:
                            print "couldn't find matching brace"
                        raise EvalError("could not find matching brace for "
                                        "'%s' at position %d"
                                        % (stack[-1][0], stack[-1][3]))
        
                else:
                    if DEBUG:
                        style_names = buf.style_names_from_style_num(style)
                        print "add char: %r (%s)" % (ch, ', '.join(style_names))
                    citdl_expr.append(ch)
                    i -= 1
        except IndexError:
            # Nothing left to consume, return what we have
            pass

        # Remove any unecessary starting dots
        while citdl_expr and citdl_expr[-1] == ".":
            citdl_expr.pop()
        citdl_expr.reverse()
        citdl_expr = ''.join(citdl_expr)
        if DEBUG:
            print "return: %r" % citdl_expr
            print util.banner("done")
        return citdl_expr

    def citdl_expr_from_trg(self, buf, trg):
        """Return a PHP CITDL expression preceding the given trigger.

        The expression drops newlines, whitespace, and function call
        arguments -- basically any stuff that is not used by the codeintel
        database system for determining the resultant object type of the
        expression. For example (in which <|> represents the given position):
        
            GIVEN                           RETURN
            -----                           ------
            foo-<|>>                        foo
            Foo:<|>:                        Foo
            foo(bar-<|>>                    bar
            foo(bar,blam)-<|>>              foo()
            foo(bar,                        foo()
                blam)-<|>>
            foo(arg1, arg2)->bar-<|>>       foo().bar
            Foo(arg1, arg2)::bar-<|>>       Foo().bar
            Foo\bar:<|>:                    Foo\bar
            Foo\bar::bam-<|>>               Foo\bar.bam
            Foo\bar(arg1, arg2)::bam-<|>>   Foo\bar().bam
        """
        #DEBUG = True
        DEBUG = False
        if DEBUG:
            print util.banner("%s citdl_expr_from_trg @ %r" % (buf.lang, trg))

        if trg.form == TRG_FORM_CPLN:
            # "->" or "::"
            if trg.type == "classes":
                i = trg.pos + 1
            elif trg.type == "functions":
                i = trg.pos + 3   # 3-char trigger, skip over it
            elif trg.type in ("variables", "comment-variables"):
                i = trg.pos + 1   # triggered on the $, skip over it
            elif trg.type == "array-members":
                i = trg.extra.get("bracket_pos")   # triggered on foo['
            elif trg.type == "namespaces":
                i = trg.pos + 1
            elif trg.type == "namespace-members":
                i = trg.pos - 1
            else:
                i = trg.pos - 2 # skip past the trigger char
            return self._citdl_expr_from_pos(trg, buf, i, trg.implicit,
                                             DEBUG=DEBUG)
        elif trg.form == TRG_FORM_DEFN:
            return self.citdl_expr_under_pos(trg, buf, trg.pos, DEBUG)
        else:   # trg.form == TRG_FORM_CALLTIP:
            # (<|>
            return self._citdl_expr_from_pos(trg, buf, trg.pos-1, trg.implicit,
                                             DEBUG=DEBUG)

    def citdl_expr_under_pos(self, trg, buf, pos, DEBUG=False):
        """Return a PHP CITDL expression around the given pos.

        Similar to citdl_expr_from_trg(), but looks forward to grab additional
        characters.

            GIVEN                       RETURN
            -----                       ------
            foo-<|>>                    foo
            F<|>oo::                    Foo
            foo->ba<|>r                 foo.bar
            f<|>oo->bar                 foo
            foo(bar-<|>>                bar
            foo(bar,blam)-<|>>          foo()
            foo(bar,                    foo()
                blam)-<|>>
            foo(arg1, arg2)->bar-<|>>   foo().bar
            Foo(arg1, arg2)::ba<|>r->   Foo().bar
            Fo<|>o(arg1, arg2)::bar->   Foo
        """
        #DEBUG = True
        expr = self._citdl_expr_from_pos(trg, buf, pos-1, implicit=True,
                                         include_forwards=True, DEBUG=DEBUG)
        if expr:
            # Chop off any trailing "." characters
            return expr.rstrip(".")
        return expr


    def libs_from_buf(self, buf):
        env = buf.env

        # A buffer's libs depend on its env and the buf itself so
        # we cache it on the env and key off the buffer.
        if "php-buf-libs" not in env.cache:
            env.cache["php-buf-libs"] = weakref.WeakKeyDictionary()
        cache = env.cache["php-buf-libs"] # <buf-weak-ref> -> <libs>

        if buf not in cache:
            # - curdirlib
            # Using the dirname of this buffer isn't always right, but
            # hopefully is a good first approximation.
            cwd = dirname(buf.path)
            if cwd == "<Unsaved>":
                libs = []
            else:
                libs = [ self.mgr.db.get_lang_lib("PHP", "curdirlib", [cwd], "PHP")]

            libs += self._buf_indep_libs_from_env(env)
            cache[buf] = libs
        return cache[buf]

    def lpaths_from_blob(self, blob):
        """Return <lpaths> for this blob
        where,
            <lpaths> is a set of externally referencable lookup-paths, e.g.
                [("MyOwnClass",), ("MyOwnClass", "function1"), ...]
        """
        return set(lpath for child in blob
                   for lpath in _walk_php_symbols(child))

    def _php_from_env(self, env):
        import which
        path = [d.strip() 
                for d in env.get_envvar("PATH", "").split(os.pathsep)
                if d.strip()]
        for exe_name in ("php", "php4", "php-cgi", "php-cli"):
            try:
                return which.which(exe_name, path=path) 
            except which.WhichError:
                pass
        return None

    def _php_info_from_php(self, php, env):
        """Call the given PHP and return:
            (<version>, <include_path>)
        Returns (None, []) if could not determine.
        """
        import process
        import tempfile

        # Use a marker to separate the start of output from possible
        # leading lines of PHP loading errors/logging.
        marker = "--- Start of Good Stuff ---"
        info_cmd = (r'<?php '
                    + r'echo("%s\n");' % marker
                    + r'echo(phpversion()."\n");'
                    + r'echo(ini_get("include_path")."\n");'
                    + r' ?>')
        
        argv = [php]
        envvars = env.get_all_envvars()
        php_ini_path = env.get_pref("phpConfigFile")
        if php_ini_path:
            envvars["PHPRC"] = php_ini_path

        fd, filepath = tempfile.mkstemp(suffix=".php")
        try:
            os.write(fd, info_cmd)
            os.close(fd)
            argv.append(filepath)
            p = process.ProcessOpen(argv, env=env.get_all_envvars())
            stdout, stderr = p.communicate()
        finally:
            os.remove(filepath)

        stdout_lines = stdout.splitlines(0)
        retval = p.returncode
        if retval:
            log.warn("failed to determine PHP info:\n"
                     "  path: %s\n"
                     "  retval: %s\n"
                     "  stdout:\n%s\n"
                     "  stderr:\n%s\n",
                     php, retval, util.indent('\n'.join(stdout_lines)),
                     util.indent(stderr))
            return None, []

        stdout_lines = stdout_lines[stdout_lines.index(marker)+1:]
        php_ver = stdout_lines[0]
        include_path = [p.strip() for p in stdout_lines[1].split(os.pathsep)
                        if p.strip()]

        return php_ver, include_path

    def _extra_dirs_from_env(self, env):
        extra_dirs = set()
        include_project = env.get_pref("codeintel_scan_files_in_project", True)
        if include_project:
            proj_base_dir = env.get_proj_base_dir()
            if proj_base_dir is not None:
                extra_dirs.add(proj_base_dir)  # Bug 68850.
        for pref in env.get_all_prefs("phpExtraPaths"):
            if not pref: continue
            extra_dirs.update(d.strip() for d in pref.split(os.pathsep)
                              if exists(d.strip()))
        if extra_dirs:
            log.debug("PHP extra lib dirs: %r", extra_dirs)
            max_depth = env.get_pref("codeintel_max_recursive_dir_depth", 10)
            php_assocs = env.assoc_patterns_from_lang("PHP")
            extra_dirs = tuple(
                util.gen_dirs_under_dirs(extra_dirs,
                    max_depth=max_depth,
                    interesting_file_patterns=php_assocs)
            )
        else:
            extra_dirs = () # ensure retval is a tuple
        return extra_dirs

    def _buf_indep_libs_from_env(self, env):
        """Create the buffer-independent list of libs."""
        cache_key = "php-libs"
        if cache_key not in env.cache:
            env.add_pref_observer("php", self._invalidate_cache)
            env.add_pref_observer("phpExtraPaths",
                self._invalidate_cache_and_rescan_extra_dirs)
            env.add_pref_observer("phpConfigFile",
                                  self._invalidate_cache)
            env.add_pref_observer("codeintel_selected_catalogs",
                                  self._invalidate_cache)
            env.add_pref_observer("codeintel_max_recursive_dir_depth",
                                  self._invalidate_cache)
            env.add_pref_observer("codeintel_scan_files_in_project",
                                  self._invalidate_cache)
            # (Bug 68850) Both of these 'live_*' prefs on the *project*
            # prefset can result in a change of project base dir. It is
            # possible that we can false positives here if there is ever
            # a global pref of this name.
            env.add_pref_observer("import_live",
                self._invalidate_cache_and_rescan_extra_dirs)
            env.add_pref_observer("import_dirname",
                self._invalidate_cache_and_rescan_extra_dirs)

            db = self.mgr.db

            # Gather information about the current php.
            php = None
            if env.has_pref("php"):
                php = env.get_pref("php").strip() or None
            if not php or not exists(php):
                php = self._php_from_env(env)
            if not php:
                log.warn("no PHP was found from which to determine the "
                         "import path")
                php_ver, include_path = None, []
            else:
                php_ver, include_path \
                    = self._php_info_from_php(php, env)
                
            libs = []

            # - extradirslib
            extra_dirs = self._extra_dirs_from_env(env)
            if extra_dirs:
                libs.append( db.get_lang_lib("PHP", "extradirslib",
                                             extra_dirs, "PHP") )

            # - inilib (i.e. dirs in the include_path in PHP.ini)
            include_dirs = [d for d in include_path
                            if d != '.'  # handled separately
                            if exists(d)]
            if include_dirs:
                max_depth = env.get_pref("codeintel_max_recursive_dir_depth", 10)
                php_assocs = env.assoc_patterns_from_lang("PHP")
                include_dirs = tuple(
                    util.gen_dirs_under_dirs(include_dirs,
                        max_depth=max_depth,
                        interesting_file_patterns=php_assocs)
                )
                if include_dirs:
                    libs.append( db.get_lang_lib("PHP", "inilib",
                                                 include_dirs, "PHP") )

            # Warn the user if there is a huge number of import dirs that
            # might slow down completion.
            num_import_dirs = len(extra_dirs) + len(include_dirs)
            if num_import_dirs > 100:
                db.report_event("This buffer is configured with %d PHP "
                                "import dirs: this may result in poor "
                                "completion performance" % num_import_dirs)

            # - cataloglib, stdlib
            catalog_selections = env.get_pref("codeintel_selected_catalogs")
            libs += [
                db.get_catalog_lib("PHP", catalog_selections),
                db.get_stdlib("PHP", php_ver)
            ]
            env.cache[cache_key] = libs

        return env.cache[cache_key]

    def _invalidate_cache(self, env, pref_name):
        for key in ("php-buf-libs", "php-libs"):
            if key in env.cache:
                log.debug("invalidate '%s' cache on %r", key, env)
                del env.cache[key]

    def _invalidate_cache_and_rescan_extra_dirs(self, env, pref_name):
        self._invalidate_cache(env, pref_name)
        extra_dirs = self._extra_dirs_from_env(env)
        if extra_dirs:
            extradirslib = self.mgr.db.get_lang_lib(
                "PHP", "extradirslib", extra_dirs, "PHP")
            request = PreloadLibRequest(extradirslib)
            self.mgr.idxr.stage_request(request, 1.0)

    #---- code browser integration
    cb_import_group_title = "Includes and Requires"   

    def cb_import_data_from_elem(self, elem):
        alias = elem.get("alias")
        symbol = elem.get("symbol")
        module = elem.get("module")
        if alias is not None:
            if symbol is not None:
                name = "%s (%s\%s)" % (alias, module, symbol)
                detail = "from %(module)s import %(symbol)s as %(alias)s" % locals()
            else:
                name = "%s (%s)" % (alias, module)
                detail = "import %(module)s as %(alias)s" % locals()
        elif symbol is not None:
            if module == "\\":
                name = '\\%s' % (symbol)
            else:
                name = '%s\\%s' % (module, symbol)
            detail = "from %(module)s import %(symbol)s" % locals()
        else:
            name = module
            detail = 'include "%s"' % module
        return {"name": name, "detail": detail}

    def cb_variable_data_from_elem(self, elem):
        """Use the 'constant' image in the Code Browser for a variable constant.
        """
        data = CitadelLangIntel.cb_variable_data_from_elem(self, elem)
        if elem.get("ilk") == "constant":
            data["img"] = "constant"
        return data


class PHPBuffer(UDLBuffer, XMLParsingBufferMixin):
    lang = lang
    m_lang = "HTML"
    css_lang = "CSS"
    csl_lang = "JavaScript"
    ssl_lang = "PHP"

    cb_show_if_empty = True

    # Fillup chars for PHP: basically, any non-identifier char.
    # - dropped '#' to prevent annoying behavior with $form['#foo']
    # - dropped '@' I could find no common use of "@" following func/variable
    # - dropped '$' It gets in the way of common usage: "$this->$"
    # - dropped '\\' I could find no common use of "\" following func/variable
    # - dropped '?' It gets in the way of common usage: "<?php "
    # - dropped '/', it gets in the way of "</" closing an XML/HTML tag
    # - dropped '!' It gets in the way of "<!" in XML/HTML tag (bug 78632)
    # - dropped '=' It gets in the way of "<a href=" in XML/HTML cpln (bug 78632)
    # - dropped ':' It gets in the way of "<a d:blah=" in XML/HTML cpln
    # - dropped '>' It gets in the way of "<p>asdf</" in XML/HTML tag cpln (bug 80348)
    cpln_fillup_chars = "~`%^&*()-+{}[]|;'\",.< "
    #TODO: c.f. cpln_stop_chars stuff in lang_html.py
    # - dropping '[' because need for "<!<|>" -> "<![CDATA[" cpln
    # - dropping '#' because we need it for $form['#foo']
    # - dropping '$' because: MyClass::$class_var
    # - dropping '-' because causes problem with CSS (bug 78312)
    # - dropping '!' because causes problem with CSS "!important" (bug 78312)
    cpln_stop_chars = "~`@%^&*()=+{}]|\\;:'\",.<>?/ "

    def __init__(self, *args, **kwargs):
        super(PHPBuffer, self).__init__(*args, **kwargs)
        
        # Encourage the database to pre-scan dirs relevant to completion
        # for this buffer -- because of recursive-dir-include-everything
        # semantics for PHP this first-time scan can take a while.
        request = PreloadBufLibsRequest(self)
        self.mgr.idxr.stage_request(request, 1.0)

    @property
    def libs(self):
        return self.langintel.libs_from_buf(self)

    @property
    def stdlib(self):
        return self.libs[-1]


class PHPImportHandler(ImportHandler):
    sep = '/'

    def setCorePath(self, compiler=None, extra=None):
        #XXX To do this independent of Komodo this would need to do all
        #    the garbage that koIPHPInfoEx is doing to determine this. It
        #    might also require adding a "rcfile" argument to this method
        #    so the proper php.ini file is used in the "_shellOutForPath".
        #    This is not crucial now because koCodeIntel._Manager() handles
        #    this for us.
        if not self.corePath:
            raise CodeIntelError("Do not know how to determine the core "
                                 "PHP include path. 'corePath' must be set "
                                 "manually.")

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
            elif os.path.splitext(names[i])[1] in (".php", ".inc",
                                                   ".module", ".tpl"):
                #XXX The list of extensions should be settable on
                #    the ImportHandler and Komodo should set whatever is
                #    set in prefs. ".module" and ".tpl" are for
                #    drupal-nerds until CodeIntel gets this right.
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
                # Do NOT traverse '.' if it is in the include_path. Not sure
                # if this is at all common for PHP.
                continue
            files = []
            os.path.walk(dirname, self._findScannableFiles,
                         (files, searchedDirs))
            for file in files:
                yield file

    def find_importables_in_dir(self, dir):
        """See citadel.py::ImportHandler.find_importables_in_dir() for
        details.

        Importables for PHP look like this:
            {"foo.php": ("foo.php", None, False),
             "bar.inc": ("bar.inc", None, False),
             "somedir": (None,      None, True)}

        TODO: log the fs-stat'ing a la codeintel.db logging.
        """
        from os.path import join, isdir
        from fnmatch import fnmatch

        if dir == "<Unsaved>":
            #TODO: stop these getting in here.
            return {}

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
        patterns = self.mgr.env.assoc_patterns_from_lang("PHP")
        for name in nondirs:
            for pattern in patterns:
                if fnmatch(name, pattern):
                    break
            else:
                continue
            if name in dirs:
                importables[name] = (name, None, True)
                dirs.remove(name)
            else:
                importables[name] = (name, None, False)
        for name in dirs:
            importables[name] = (None, None, True)
        return importables


class PHPCILEDriver(UDLCILEDriver):
    lang = lang
    ssl_lang = "PHP"
    csl_lang = "JavaScript"

    def scan_multilang(self, buf, csl_cile_driver=None):
      #try:
        """Scan the given multilang (UDL-based) buffer and return a CIX
        element tree.

            "buf" is the multi-lang Buffer instance (e.g.
                lang_rhtml.RHTMLBuffer for RHTML).
            "csl_cile_driver" (optional) is the CSL (client-side language)
                CILE driver. While scanning, CSL tokens should be gathered and,
                if any, passed to the CSL scanner like this:
                    csl_cile_driver.scan_csl_tokens(
                        file_elem, blob_name, csl_tokens)
                The CSL scanner will append a CIX <scope ilk="blob"> element
                to the <file> element.
        """
        # Create the CIX tree.
        mtime = "XXX"
        fullpath = buf.path
        cixtree = createCixRoot()
        cixfile = createCixFile(cixtree, fullpath, lang=buf.lang)
        if sys.platform.startswith("win"):
            fullpath = fullpath.replace('\\', '/')
        basepath = os.path.basename(fullpath)
        cixblob = createCixModule(cixfile, basepath, "PHP", src=fullpath)

        phpciler = PHPParser(fullpath, buf.accessor.text, mtime)
        csl_tokens = phpciler.scan_multilang_content(buf.accessor.text)
        phpciler.convertToElementTreeModule(cixblob)

        # Hand off the csl tokens if any
        if csl_cile_driver and csl_tokens:
            csl_cile_driver.scan_csl_tokens(cixfile, basepath, csl_tokens)

        return cixtree

      #except Exception, e:
      #    print "\nPHP cile exception"
      #    import traceback
      #    traceback.print_exc()
      #    print
      #    raise



#---- internal routines and classes


# States used by PHP scanner when parsing information
S_DEFAULT = 0
S_IN_ARGS = 1
S_IN_ASSIGNMENT = 2
S_IGNORE_SCOPE = 3
S_OBJECT_ARGUMENT = 4
S_GET_HEREDOC_MARKER = 5
S_IN_HEREDOC = 6
# Special tags for multilang handling (i.e. through UDL)
S_OPEN_TAG  = 10
S_CHECK_CLOSE_TAG = 11
S_IN_SCRIPT = 12

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


def _sortByLineCmp(val1, val2):
    try:
    #if hasattr(val1, "line") and hasattr(val2, "line"):
        return cmp(val1.linestart, val2.linestart)
    except AttributeError:
        return cmp(val1, val2)

def sortByLine(seq):
    seq.sort(_sortByLineCmp)
    return seq


class PHPArg:
    def __init__(self, name, citdl=None, signature=None, default=None):
        """Set details for a function argument"""
        self.name = name
        self.citdl = citdl
        if signature:
            self.signature = signature
        else:
            if citdl:
                self.signature = "%s $%s" % (citdl, name)
            else:
                self.signature = "$%s" % (name, )
        self.default = default

    def __repr__(self):
        return self.signature

    def updateCitdl(self, citdl):
        self.citdl = citdl
        if self.signature.startswith("$") or self.signature.startswith("&") or \
           " " not in self.signature:
            self.signature = "%s %s" % (citdl, self.signature)
        else:
            self.signature = "%s %s" % (citdl, self.signature.split(" ", 1)[1])

    def toElementTree(self, cixelement):
        cixarg = addCixArgument(cixelement, self.name, argtype=self.citdl)
        if self.default:
            cixarg.attrib["default"] = self.default


class PHPVariable:

    # PHPDoc variable type sniffer.
    _re_var = re.compile(r'^\s*@var\s+(\$(?P<variable>\w+)\s+)?(?P<type>\w+)(?:\s+(?P<doc>.*?))?', re.M|re.U)
    _ignored_php_types = ("object", "mixed")

    def __init__(self, name, line, vartype='', attributes='', doc=None,
                 fromPHPDoc=False, namespace=None):
        self.name = name
        self.types = [(line, vartype, fromPHPDoc)]
        self.linestart = line
        if attributes:
            if not isinstance(attributes, list):
                attributes = attributes.strip().split()
            self.attributes = ' '.join(attributes)
        else:
            self.attributes = None
        self.doc = doc
        self.created_namespace = None
        if namespace:
            self.created_namespace = namespace.name

    def addType(self, line, type, fromPHPDoc=False):
        self.types.append((line, type, fromPHPDoc))

    def __repr__(self):
        return "var %s line %s type %s attributes %s\n"\
               % (self.name, self.linestart, self.types, self.attributes)

    def toElementTree(self, cixblob):
        # Work out the best vartype
        vartype = None
        doc = None
        if self.doc:
            # We are only storing the doc string for cases where we have an
            # "@var" phpdoc tag, we should actually store the docs anyway, but
            # we don't yet have a clean way to ensure the doc is really meant
            # for this specific variable (i.e. the comment was ten lines before
            # the variable definition).
            if "@var" in self.doc:
                doc = uncommentDocString(self.doc)
                # get the variable citdl type set by "@var"
                all_matches = re.findall(self._re_var, doc)
                if len(all_matches) >= 1:
                    #print "all_matches[0]: %r" % (all_matches[0], )
                    vartype = all_matches[0][2]
                    if vartype and vartype.lower() in self._ignored_php_types:
                        # Ignore these PHP types, they don't help codeintel.
                        # http://bugs.activestate.com/show_bug.cgi?id=77602
                        vartype = None

        if not vartype and self.types:
            d = {}
            max_count = 0
            for line, vtype, fromPHPDoc in self.types:
                if vtype:
                    if fromPHPDoc:
                        if vtype.lower() in self._ignored_php_types:
                            # Ignore these PHP types, they don't help codeintel.
                            continue
                        # The doc gets priority.
                        vartype = vtype
                        break
                    count = d.get(vtype, 0) + 1
                    d[vtype] = count
                    if count > max_count:
                        # Best found so far
                        vartype = vtype
                        max_count = count
        cixelement = createCixVariable(cixblob, self.name, vartype=vartype,
                                       attributes=self.attributes)
        if doc:
            setCixDoc(cixelement, doc)
        cixelement.attrib["line"] = str(self.linestart)
        if self.created_namespace:
            # Need to remember that the object was created in a namespace, so
            # that the starting lookup scope can start in the given namespace.
            cixelement.attrib["namespace"] = self.created_namespace
        return cixelement

class PHPConstant(PHPVariable):
    def __init__(self, name, line, vartype=''):
        PHPVariable.__init__(self, name, line, vartype)

    def __repr__(self):
        return "constant %s line %s type %s\n"\
               % (self.name, self.linestart, self.types)

    def toElementTree(self, cixblob):
        cixelement = PHPVariable.toElementTree(self, cixblob)
        cixelement.attrib["ilk"] = "constant"
        return cixelement

class PHPFunction:
    def __init__(self, funcname, phpArgs, lineno, depth=0,
                 attributes=None, doc=None, classname='', classparent='',
                 returnType=None, returnByRef=False):
        self.name = funcname
        self.args = phpArgs
        self.linestart = lineno
        self.lineend = None
        self.depth = depth
        self.classname = classname
        self.classparent = classparent
        self.returnType = returnType
        self.returnByRef = returnByRef
        self.variables = {} # all variables used in class
        # build the signature before we add any attributes that are not part
        # of the signature
        if returnByRef:
            self.signature = '&%s' % (self.name)
        else:
            self.signature = '%s' % (self.name)
        if attributes:
            attrs = ' '.join(attributes)
            self.shortSig = '%s %s' % (attrs, self.name)
        else:
            self.shortSig = self.name
        # both php 4 and 5 constructor methods
        if funcname == '__construct' or (classname and funcname.lower() == classname.lower()):
            attributes.append('__ctor__')
# if we add destructor attributes...
#        elif funcname == '__destruct':
#            attributes += ['__dtor__']
        self.attributes = attributes and ' '.join(attributes) or ''
        self.doc = None

        if doc:
            if isinstance(doc, list):
                doc = "".join(doc)
            docinfo = parseDocString(doc)
            self.doc = docinfo[0]
            # See if there are any PHPDoc arguments defined in the docstring.
            if docinfo[1]:
                for argInfo in docinfo[1]:
                    for phpArg in self.args:
                        if phpArg.name == argInfo[1]:
                            phpArg.updateCitdl(argInfo[0])
                            break
                    else:
                        self.args.append(PHPArg(argInfo[1], citdl=argInfo[0]))
            if docinfo[2]:
                self.returnType = docinfo[2][0]
        if self.returnType:
            self.signature = '%s %s' % (self.returnType, self.signature, )
        self.signature += "("
        if self.args:
            self.signature += ", ".join([x.signature for x in self.args])
        self.signature += ")"

    def addReturnType(self, returnType):
        if self.returnType is None:
            self.returnType = returnType

    def __str__(self):
        return self.signature
        # The following is busted and outputting multiple lines from __str__
        # and __repr__ is bad form: make debugging prints hard.
        #if self.doc:
        #    if self.args:
        #        return "%s(%s)\n%s" % (self.shortSig, self.args.argline, self.doc)
        #    else:
        #        return "%s()\n%s" % (self.shortSig, self.doc)
        #return "%s(%s)" % (self.shortSig, self.argline)

    def __repr__(self):
        return self.signature

    def hasArgumentWithName(self, name):
        if self.args:
            for phpArg in self.args:
                if phpArg.name == name:
                    return True
        return False

    def toElementTree(self, cixblob):
        cixelement = createCixFunction(cixblob, self.name,
                                       attributes=self.attributes)
        cixelement.attrib["line"] = str(self.linestart)
        if self.lineend is not None:
            cixelement.attrib['lineend'] = str(self.lineend)
        setCixSignature(cixelement, self.signature)
        if self.doc:
            setCixDoc(cixelement, self.doc)
        if self.args:
            for phpArg in self.args:
                phpArg.toElementTree(cixelement)
        if self.returnType:
            addCixReturns(cixelement, self.returnType)
        # Add a "this" and "self" member for class functions
        #if self.classname:
        #    createCixVariable(cixelement, "this", vartype=self.classname)
        #    createCixVariable(cixelement, "self", vartype=self.classname)
        # Add a "parent" member for class functions that have a parent
        #if self.classparent:
        #    createCixVariable(cixelement, "parent", vartype=self.classparent)

        # XXX for variables inside functions
        for v in self.variables.values():
            v.toElementTree(cixelement)

class PHPInterface:
    def __init__(self, name, extends, lineno, depth, doc=None):
        self.name = name
        self.extends = extends
        self.linestart = lineno
        self.lineend = None
        self.depth = depth
        self.constants = {} # declared class constants
        self.members = {} # declared class variables
        self.variables = {} # all variables used in class
        self.functions = {}
        self.doc = None
        if doc:
            self.doc = uncommentDocString(doc)

    def __repr__(self):
        # dump our contents to human readable form
        r = "INTERFACE %s" % self.name
        if self.extends:
            r += " EXTENDS %s" % self.extends
        r += '\n'

        if self.constants:
            r += "Constants:\n"
            for m in self.constants:
                r += "    var %s line %s\n"  % (m, self.constants[m])

        if self.members:
            r += "Members:\n"
            for m in self.members:
                r += "    var %s line %s\n"  % (m, self.members[m])

        if self.functions:            
            r += "functions:\n"
            for f in self.functions.values():
                r += "    %r" % f

        if self.variables:
            r += "variables:\n"
            for v in self.variables.values():
                r += "    %r" % v
            
        return r + '\n'

    def toElementTree(self, cixblob):
        cixelement = createCixInterface(cixblob, self.name)
        cixelement.attrib["line"] = str(self.linestart)
        if self.lineend is not None:
            cixelement.attrib["lineend"] = str(self.lineend)
        signature = "%s" % (self.name)
        if self.extends:
            signature += " extends %s" % (self.extends)
            for name in self.extends.split(","):
                addInterfaceRef(cixelement, name.strip())
            #SubElement(cixelement, "classref", name=self.extends)
        cixelement.attrib["signature"] = signature

        if self.doc:
            setCixDoc(self.doc)

        allValues = self.functions.values() + self.constants.values() + \
                    self.members.values() + self.variables.values()
        for v in sortByLine(allValues):
            v.toElementTree(cixelement)

class PHPClass:

    # PHPDoc magic property sniffer.
    _re_magic_property = re.compile(r'^\s*@property(-(?P<type>read|write))?\s+((?P<citdl>\w+)\s+)?(?P<name>\$\w+)(?:\s+(?P<doc>.*?))?', re.M|re.U)
    _re_magic_method = re.compile(r'^\s*@method\s+((?P<citdl>\w+)\s+)?(?P<name>\w+)(\(\))?(?P<doc>.*?)$', re.M|re.U)

    def __init__(self, name, extends, lineno, depth, attributes=None,
                 interfaces=None, doc=None):
        self.name = name
        self.extends = extends
        self.linestart = lineno
        self.lineend = None
        self.depth = depth
        self.constants = {} # declared class constants
        self.members = {} # declared class variables
        self.variables = {} # all variables used in class
        self.functions = {}
        if interfaces:
            self.interfaces = interfaces.split(',')
        else:
            self.interfaces = []
        if attributes:
            self.attributes = ' '.join(attributes)
        else:
            self.attributes = None
        self.doc = None
        if doc:
            if isinstance(doc, list):
                doc = "".join(doc)
            self.doc = uncommentDocString(doc)
            if self.doc.find("@property") >= 0:
                all_matches = re.findall(self._re_magic_property, self.doc)
                for match in all_matches:
                    varname = match[4][1:]  # skip "$" in the name.
                    v = PHPVariable(varname, lineno, match[3], doc=match[5])
                    self.members[varname] = v
            if self.doc.find("@method") >= 0:
                all_matches = re.findall(self._re_magic_method, self.doc)
                for match in all_matches:
                    citdl = match[1] or None
                    fnname = match[2]
                    fndoc = match[4]
                    phpArgs = []
                    fn = PHPFunction(fnname, phpArgs, lineno, depth=self.depth+1,
                                     doc=fndoc, returnType=citdl)
                    self.functions[fnname] = fn

    def __repr__(self):
        # dump our contents to human readable form
        r = "CLASS %s" % self.name
        if self.extends:
            r += " EXTENDS %s" % self.extends
        r += '\n'

        if self.constants:
            r += "Constants:\n"
            for m in self.constants:
                r += "    var %s line %s\n"  % (m, self.constants[m])

        if self.members:
            r += "Members:\n"
            for m in self.members:
                r += "    var %s line %s\n"  % (m, self.members[m])

        if self.functions:            
            r += "functions:\n"
            for f in self.functions.values():
                r += "    %r" % f

        if self.variables:
            r += "variables:\n"
            for v in self.variables.values():
                r += "    %r" % v
            
        return r + '\n'

    def toElementTree(self, cixblob):
        cixelement = createCixClass(cixblob, self.name)
        cixelement.attrib["line"] = str(self.linestart)
        if self.lineend is not None:
            cixelement.attrib["lineend"] = str(self.lineend)
        if self.attributes:
            cixelement.attrib["attributes"] = self.attributes

        if self.doc:
            setCixDoc(cixelement, self.doc)

        if self.extends:
            addClassRef(cixelement, self.extends)

        for i in self.interfaces:
            addInterfaceRef(cixelement, i.strip())

        allValues = self.functions.values() + self.constants.values() + \
                    self.members.values() + self.variables.values()
        for v in sortByLine(allValues):
            v.toElementTree(cixelement)

class PHPImport:
    def __init__(self, name, lineno, alias=None, symbol=None):
        self.name = name
        self.lineno = lineno
        self.alias = alias
        self.symbol = symbol

    def __repr__(self):
        # dump our contents to human readable form
        if self.alias:
            return "IMPORT %s as %s\n" % (self.name, self.alias)
        else:
            return "IMPORT %s\n" % self.name

    def toElementTree(self, cixmodule):
        elem = SubElement(cixmodule, "import", module=self.name, line=str(self.lineno))
        if self.alias:
            elem.attrib["alias"] = self.alias
        if self.symbol:
            elem.attrib["symbol"] = self.symbol
        return elem

def qualifyNamespacePath(namespace_path):
    # Ensure the namespace does not begin or end with a backslash.
    return namespace_path.strip("\\")

class PHPNamespace:
    def __init__(self, name, lineno, depth, doc=None):
        assert not name.startswith("\\")
        assert not name.endswith("\\")
        self.name = name
        self.linestart = lineno
        self.lineend = None
        self.depth = depth
        self.doc = None
        if doc:
            self.doc = uncommentDocString(doc)
        
        self.functions = {} # functions declared in file
        self.classes = {} # classes declared in file
        self.constants = {} # all constants used in file
        self.interfaces = {} # interfaces declared in file
        self.includes = [] # imported files/namespaces

    def __repr__(self):
        # dump our contents to human readable form
        r = "NAMESPACE %s\n" % self.name

        for v in self.includes:
            r += "    %r" % v

        r += "constants:\n"
        for v in self.constants.values():
            r += "    %r" % v

        r += "interfaces:\n"
        for v in self.interfaces.values():
            r += "    %r" % v

        r += "functions:\n"
        for f in self.functions.values():
            r += "    %r" % f

        r += "classes:\n"
        for c in self.classes.values():
            r += repr(c)

        return r + '\n'

    def toElementTree(self, cixblob):
        cixelement = createCixNamespace(cixblob, self.name)
        cixelement.attrib["line"] = str(self.linestart)
        if self.lineend is not None:
            cixelement.attrib["lineend"] = str(self.lineend)

        if self.doc:
            setCixDoc(cixelement, self.doc)

        for v in self.includes:
            v.toElementTree(cixelement)

        allValues = self.functions.values() + self.constants.values() + \
                    self.interfaces.values() + self.classes.values()
        for v in sortByLine(allValues):
            v.toElementTree(cixelement)

class PHPFile:
    """CIX specifies that a <file> tag have zero or more
    <scope ilk="blob"> children.  In PHP this is a one-to-one
    relationship, so this class represents both (and emits the XML tags
    for both).
    """
    def __init__(self, filename, content=None, mtime=None):
        self.filename = filename
        self.content = content
        self.mtime = mtime
        self.error = None
        
        self.content = content
        if mtime is None:
            self.mtime = int(time.time())

        self.functions = {} # functions declared in file
        self.classes = {} # classes declared in file
        self.variables = {} # all variables used in file
        self.constants = {} # all constants used in file
        self.includes = [] # imported files/namespaces
        self.interfaces = {} # interfaces declared in file
        self.namespaces = {} # namespaces declared in file

    def __repr__(self):
        # dump our contents to human readable form
        r = "FILE %s\n" % self.filename

        for v in self.includes:
            r += "    %r" % v

        r += "constants:\n"
        for v in self.constants.values():
            r += "    %r" % v

        r += "interfaces:\n"
        for v in self.interfaces.values():
            r += "    %r" % v

        r += "functions:\n"
        for f in self.functions.values():
            r += "    %r" % f

        r += "variables:\n"
        for v in self.variables.values():
            r += "    %r" % v

        r += "classes:\n"
        for c in self.classes.values():
            r += repr(c)

        r += "namespaces:\n"
        for v in self.namespaces.values():
            r += "    %r" % v

        return r + '\n'

    def convertToElementTreeModule(self, cixmodule):
        for v in self.includes:
            v.toElementTree(cixmodule)

        allValues = self.constants.values() + self.functions.values() + \
                    self.interfaces.values() + self.variables.values() + \
                    self.classes.values() + self.namespaces.values()
        for v in sortByLine(allValues):
            v.toElementTree(cixmodule)

    def convertToElementTreeFile(self, cix):
        if sys.platform.startswith("win"):
            path = self.filename.replace('\\', '/')
        else:
            path = self.filename
        cixfile = createCixFile(cix, path, lang="PHP", mtime=str(self.mtime))
        if self.error:
            cixfile.attrib["error"] = self.error
        cixmodule = createCixModule(cixfile, os.path.basename(self.filename),
                                    "PHP")
        self.convertToElementTreeModule(cixmodule)

class PHPcile:
    def __init__(self):
        # filesparsed contains all files parsed
        self.filesparsed={}

    def clear(self, filename):
        # clear include links from the cache
        if filename not in self.filesparsed:
            return
        del self.filesparsed[filename]
        
    def __repr__(self):
        r = ''
        for f in self.filesparsed:
            r += repr(self.filesparsed[f])
        return r + '\n'

    #def toElementTree(self, cix):
    #    for f in self.filesparsed.values():
    #        f.toElementTree(cix)

    def convertToElementTreeModule(self, cixmodule):
        for f in self.filesparsed.values():
            f.convertToElementTreeModule(cixmodule)

    def convertToElementTreeFile(self, cix):
        for f in self.filesparsed.values():
            f.convertToElementTreeFile(cix)


class PHPParser:

    PHP_COMMENT_STYLES = (SCE_UDL_SSL_COMMENT, SCE_UDL_SSL_COMMENTBLOCK)
    # lastText, lastStyle are use to remember the previous tokens.
    lastText = None
    lastStyle = None

    def __init__(self, filename, content=None, mtime=None):
        self.filename = filename
        self.cile = PHPcile()
        self.fileinfo = PHPFile(self.filename, content, mtime)

        # Working variables, used in conjunction with state
        self.classStack = []
        self.currentClass = None
        self.currentNamespace = None
        self.currentFunction = None
        self.csl_tokens = []
        self.lineno = 0
        self.depth = 0
        self.styles = []
        self.linenos = []
        self.text = []
        self.comment = None
        self.comments = []
        self.heredocMarker = None

        # state : used to store the current JS lexing state
        # return_to_state : used to store JS state to return to
        # multilang_state : used to store the current UDL lexing state
        self.state = S_DEFAULT
        self.return_to_state = S_DEFAULT
        self.multilang_state = S_DEFAULT

        self.PHP_WORD        = SCE_UDL_SSL_WORD
        self.PHP_IDENTIFIER  = SCE_UDL_SSL_IDENTIFIER
        self.PHP_VARIABLE    = SCE_UDL_SSL_VARIABLE
        self.PHP_OPERATOR    = SCE_UDL_SSL_OPERATOR
        self.PHP_STRINGS     = (SCE_UDL_SSL_STRING,)
        self.PHP_NUMBER      = SCE_UDL_SSL_NUMBER

        # XXX bug 44775
        # having the next line after scanData below causes a crash on osx
        # in python's UCS2 to UTF8.  leaving this here for later
        # investigation, see bug 45362 for details.
        self.cile.filesparsed[self.filename] = self.fileinfo

    # parses included files
    def include_file(self, filename):
        # XXX Very simple prevention of include looping.  Really should
        # recurse the indices to make sure we are not creating a loop
        if self.filename == filename:
            return ""

        # add the included file to our list of included files
        self.fileinfo.includes.append(PHPImport(filename, self.lineno))

    def incBlock(self):
        self.depth = self.depth+1
        # log.debug("depth at %d", self.depth)

    def decBlock(self):
        self.depth = self.depth-1
        # log.debug("depth at %d", self.depth)
        if self.currentClass and self.currentClass.depth == self.depth:
            # log.debug("done with class %s at depth %d", self.currentClass.name, self.depth)
            self.currentClass.lineend = self.lineno
            log.debug("done with %s %s at depth %r",
                      isinstance(self.currentClass, PHPInterface) and "interface" or "class",
                      self.currentClass.name, self.depth)
            self.currentClass = self.classStack.pop()
        if self.currentNamespace and self.currentNamespace.depth == self.depth:
            log.debug("done with namespace %s at depth %r", self.currentNamespace.name, self.depth)
            self.currentNamespace.lineend = self.lineno
            self.currentNamespace = None
        elif self.currentFunction and self.currentFunction.depth == self.depth:
            self.currentFunction.lineend = self.lineno
            # XXX stacked functions used to work in php, need verify still is
            self.currentFunction = None

    def addFunction(self, name, phpArgs=None, attributes=None, doc=None,
                    returnByRef=False):
        log.debug("FUNC: %s(%r) on line %d", name, phpArgs, self.lineno)
        classname = ''
        extendsName = ''
        if self.currentClass:
            classname = self.currentClass.name
            extendsName = self.currentClass.extends
        self.currentFunction = PHPFunction(name,
                                           phpArgs,
                                           self.lineno,
                                           self.depth,
                                           attributes=attributes,
                                           doc=doc,
                                           classname=classname,
                                           classparent=extendsName,
                                           returnByRef=returnByRef)
        if self.currentClass:
            self.currentClass.functions[self.currentFunction.name] = self.currentFunction
        elif self.currentNamespace:
            self.currentNamespace.functions[self.currentFunction.name] = self.currentFunction
        else:
            self.fileinfo.functions[self.currentFunction.name] = self.currentFunction
        if isinstance(self.currentClass, PHPInterface) or self.currentFunction.attributes.find('abstract') >= 0:
            self.currentFunction.lineend = self.lineno
            self.currentFunction = None

    def addReturnType(self, typeName):
        if self.currentFunction:
            log.debug("RETURN TYPE: %r on line %d", typeName, self.lineno)
            self.currentFunction.addReturnType(typeName)
        else:
            log.debug("addReturnType: No current function for return value!?")

    def addClass(self, name, extends=None, attributes=None, interfaces=None, doc=None):
        toScope = self.currentNamespace or self.fileinfo
        if name not in toScope.classes:
            # push the current class onto the class stack
            self.classStack.append(self.currentClass)
            # make this class the current class
            self.currentClass = PHPClass(name,
                                         extends,
                                         self.lineno,
                                         self.depth,
                                         attributes,
                                         interfaces,
                                         doc=doc)
            toScope.classes[self.currentClass.name] = self.currentClass
            log.debug("CLASS: %s extends %s interfaces %s attributes %s on line %d in %s at depth %d\nDOCS: %s",
                     self.currentClass.name, self.currentClass.extends, 
                     self.currentClass.interfaces, self.currentClass.attributes,
                     self.currentClass.linestart, self.filename, self.depth,
                     self.currentClass.doc)
        else:
            # shouldn't ever get here
            pass
    
    def addClassMember(self, name, vartype, attributes=None, doc=None, forceToClass=False):
        if self.currentFunction and not forceToClass:
            if name not in self.currentFunction.variables:
                phpVariable = self.currentClass.members.get(name)
                if phpVariable is None:
                    log.debug("Class FUNC variable: %r", name)
                    self.currentFunction.variables[name] = PHPVariable(name,
                                                                       self.lineno,
                                                                       vartype,
                                                                       doc=doc)
                elif vartype:
                    log.debug("Adding type information for VAR: %r, vartype: %r",
                              name, vartype)
                    phpVariable.addType(self.lineno, vartype)
        elif self.currentClass:
            phpVariable = self.currentClass.members.get(name)
            if phpVariable is None:
                log.debug("CLASSMBR: %r", name)
                self.currentClass.members[name] = PHPVariable(name, self.lineno,
                                                              vartype,
                                                              attributes,
                                                              doc=doc)
            elif vartype:
                log.debug("Adding type information for CLASSMBR: %r, vartype: %r",
                          name, vartype)
                phpVariable.addType(self.lineno, vartype)

    def addClassConstant(self, name, vartype, doc=None):
        """Add a constant variable into the current class."""
        if self.currentClass:
            phpConstant = self.currentClass.constants.get(name)
            if phpConstant is None:
                log.debug("CLASS CONST: %r", name)
                self.currentClass.constants[name] = PHPConstant(name, self.lineno,
                                                              vartype)
            elif vartype:
                log.debug("Adding type information for CLASS CONST: %r, "
                          "vartype: %r", name, vartype)
                phpConstant.addType(self.lineno, vartype)

    def addInterface(self, name, extends=None, doc=None):
        toScope = self.currentNamespace or self.fileinfo
        if name not in toScope.interfaces:
            # push the current interface onto the class stack
            self.classStack.append(self.currentClass)
            # make this interface the current interface
            self.currentClass = PHPInterface(name, extends, self.lineno, self.depth)
            toScope.interfaces[name] = self.currentClass
            log.debug("INTERFACE: %s extends %s on line %d, depth %d",
                      name, extends, self.lineno, self.depth)
        else:
            # shouldn't ever get here
            pass

    def setNamespace(self, namelist, usesBracketedStyle, doc=None):
        """Create and set as the current namespace."""
        if self.currentNamespace:
            # End the current namespace before starting the next.
            self.currentNamespace.lineend = self.lineno -1

        if not namelist:
            # This means to use the global namespace, i.e.:
            #   namespace { // global code }
            #   http://ca3.php.net/manual/en/language.namespaces.definitionmultiple.php
            self.currentNamespace = None
        else:
            depth = self.depth
            if not usesBracketedStyle:
                # If the namespacing does not uses brackets, then there is no
                # good way to find out when the namespace end, we can only
                # guarentee that the namespace ends if another namespace starts.
                # Using None as the depth will ensure these semantics hold.
                depth = None
            namespace_path = qualifyNamespacePath("\\".join(namelist))
            namespace = self.fileinfo.namespaces.get(namespace_path)
            if namespace is None:
                namespace = PHPNamespace(namespace_path, self.lineno, depth,
                                         doc=doc)
                self.fileinfo.namespaces[namespace_path] = namespace
            self.currentNamespace = namespace
            log.debug("NAMESPACE: %r on line %d in %s at depth %r",
                      namespace_path, self.lineno, self.filename, depth)

    def addNamespaceImport(self, namespace, alias):
        """Import the namespace."""
        namelist = namespace.split("\\")
        namespace_path = "\\".join(namelist[:-1])
        if namespace.startswith("\\") and not namespace_path.startswith("\\"):
            namespace_path = "\\%s" % (namespace_path, )
        symbol = namelist[-1]
        toScope = self.currentNamespace or self.fileinfo
        toScope.includes.append(PHPImport(namespace_path, self.lineno,
                                          alias=alias, symbol=symbol))
        log.debug("IMPORT NAMESPACE: %s\%s as %r on line %d",
                  namespace_path, symbol, alias, self.lineno)

    def addVariable(self, name, vartype='', attributes=None, doc=None,
                    fromPHPDoc=False):
        log.debug("VAR: %r type: %r on line %d", name, vartype, self.lineno)
        phpVariable = None
        already_existed = True
        if self.currentFunction:
            phpVariable = self.currentFunction.variables.get(name)
            # Also ensure the variable is not a function argument.
            if phpVariable is None and \
               not self.currentFunction.hasArgumentWithName(name):
                phpVariable = PHPVariable(name, self.lineno, vartype,
                                          attributes, doc=doc,
                                          fromPHPDoc=fromPHPDoc)
                self.currentFunction.variables[name] = phpVariable
                already_existed = False
        elif self.currentClass:
            pass
            # XXX this variable is local to a class method, what to do with it?
            #if m.group('name') not in self.currentClass.variables:
            #    self.currentClass.variables[m.group('name')] =\
            #        PHPVariable(m.group('name'), self.lineno)
        else:
            # Variables cannot get defined in a namespace, so if it's not a
            # function or a class, then it goes into the global scope.
            phpVariable = self.fileinfo.variables.get(name)
            if phpVariable is None:
                phpVariable = PHPVariable(name, self.lineno, vartype,
                                          attributes, doc=doc,
                                          fromPHPDoc=fromPHPDoc,
                                          namespace=self.currentNamespace)
                self.fileinfo.variables[name] = phpVariable
                already_existed = False

        if phpVariable and already_existed:
            if doc:
                if phpVariable.doc:
                    phpVariable.doc += doc
                else:
                    phpVariable.doc = doc
            if vartype:
                log.debug("Adding type information for VAR: %r, vartype: %r",
                          name, vartype)
                phpVariable.addType(self.lineno, vartype, fromPHPDoc=fromPHPDoc)
        return phpVariable

    def addConstant(self, name, vartype='', doc=None):
        """Add a constant at the global or namelisted scope level."""

        log.debug("CONSTANT: %r type: %r on line %d", name, vartype, self.lineno)
        toScope = self.currentNamespace or self.fileinfo
        phpConstant = toScope.constants.get(name)
        # Add it if it's not already defined
        if phpConstant is None:
            if vartype and isinstance(vartype, (list, tuple)):
                vartype = ".".join(vartype)
            toScope.constants[name] = PHPConstant(name, self.lineno, vartype)

    def addDefine(self, name, vartype='', doc=None):
        """Add a define at the global or namelisted scope level."""

        log.debug("DEFINE: %r type: %r on line %d", name, vartype, self.lineno)
        # Defines always go into the global scope unless explicitly defined
        # with a namespace:
        #   http://ca3.php.net/manual/en/language.namespaces.definition.php
        toScope = self.fileinfo
        namelist = name.split("\\")
        if len(namelist) > 1:
            namespace_path = "\\".join(namelist[:-1])
            namespace_path = qualifyNamespacePath(namespace_path)
            log.debug("defined in namespace: %r", namespace_path)
            namespace = toScope.namespaces.get(namespace_path)
            # Note: This does not change to the namespace, it just creates
            #       it when it does not already exist!
            if namespace is None:
                namespace = PHPNamespace(namespace_path, self.lineno,
                                         self.depth)
                self.fileinfo.namespaces[namespace_path] = namespace
            toScope = namespace
        const_name = namelist[-1]
        phpConstant = toScope.constants.get(const_name)
        # Add it if it's not already defined
        if phpConstant is None:
            if vartype and isinstance(vartype, (list, tuple)):
                vartype = ".".join(vartype)
            toScope.constants[const_name] = PHPConstant(const_name, self.lineno, vartype)

    def _parseOneArgument(self, styles, text):
        """Create a PHPArg object from the given text"""

        # Arguments can be of the form:
        #  foo($a, $b, $c)
        #  foo(&$a, &$b, &$c)
        #  foo($a, &$b, $c)
        #  foo($a = "123")
        #  makecoffee($types = array("cappuccino"), $coffeeMaker = NULL)
        # Arguments can be statically typed declarations too, bug 79003:
        #  foo(MyClass $a)
        #  foo(string $a = "123")
        #  foo(MyClass &$a)
        # References the inner class:
        #  static function bar($x=self::X)

        pos = 0
        name = None
        citdl = None
        default = None
        sig_parts = []
        log.debug("_parseOneArgument: text: %r", text)
        while pos < len(styles):
            sig_parts.append(text[pos])
            if name is None:
                if styles[pos] == self.PHP_VARIABLE:
                    name = self._removeDollarSymbolFromVariableName(text[pos])
                elif styles[pos] in (self.PHP_IDENTIFIER, self.PHP_WORD):
                    # Statically typed argument.
                    citdl = text[pos]
                    sig_parts.append(" ")
                elif text[pos] == '&':
                    sig_parts.append(" ")
            elif not citdl:
                if text[pos] == "=":
                    sig_parts[-1] = " = "
                    # It's an optional argument
                    default = "".join(text[pos+1:])
                    valueType, pos = self._getVariableType(styles, text, pos+1)
                    if valueType:
                        citdl = valueType[0]
                    break
            else:
                pos += 1
                break
            pos += 1
        sig_parts += text[pos:]
        if name is not None:
            return PHPArg(name, citdl=citdl, signature="".join(sig_parts),
                          default=default)

    def _getArgumentsFromPos(self, styles, text, pos):
        """Return a list of PHPArg objects"""

        p = pos
        log.debug("_getArgumentsFromPos: text: %r", text[p:])
        phpArgs = []
        if p < len(styles) and styles[p] == self.PHP_OPERATOR and text[p] == "(":
            p += 1
            paren_count = 0
            start_pos = p
            while p < len(styles):
                if styles[p] == self.PHP_OPERATOR:
                    if text[p] == "(":
                        paren_count += 1
                    elif text[p] == ")":
                        if paren_count <= 0:
                            # End of the arguments.
                            break
                        paren_count -= 1
                    elif text[p] == "," and paren_count == 0:
                        # End of the current argument.
                        phpArg = self._parseOneArgument(styles[start_pos:p],
                                                       text[start_pos:p])
                        if phpArg:
                            phpArgs.append(phpArg)
                        start_pos = p + 1
                p += 1
            if start_pos < p:
                phpArg = self._parseOneArgument(styles[start_pos:p],
                                               text[start_pos:p])
                if phpArg:
                    phpArgs.append(phpArg)
        return phpArgs, p

    def _getOneIdentifierFromPos(self, styles, text, pos, identifierStyle=None):
        if identifierStyle is None:
            identifierStyle = self.PHP_IDENTIFIER
        log.debug("_getIdentifiersFromPos: text: %r", text[pos:])
        start_pos = pos
        ids = []
        last_style = self.PHP_OPERATOR
        isNamespace = False
        while pos < len(styles):
            style = styles[pos]
            #print "Style: %d, Text[%d]: %r" % (style, pos, text[pos])
            if style == identifierStyle:
                if last_style != self.PHP_OPERATOR:
                    break
                if isNamespace:
                    ids[-1] += text[pos]
                else:
                    ids.append(text[pos])
            elif style == self.PHP_OPERATOR:
                t = text[pos]
                isNamespace = False
                if t == "\\":
                    isNamespace = True
                    if ids:
                        ids[-1] += "\\"
                    else:
                        ids.append("\\")
                elif ((t != "&" or last_style != self.PHP_OPERATOR) and \
                      (t != ":" or last_style != identifierStyle)):
                    break
            else:
                break
            pos += 1
            last_style = style
        return ids, pos

    def _getIdentifiersFromPos(self, styles, text, pos, identifierStyle=None):
        typeNames, p = self._getOneIdentifierFromPos(styles, text, pos, identifierStyle)
        if typeNames:
            typeNames[0] = self._removeDollarSymbolFromVariableName(typeNames[0])
        log.debug("typeNames: %r, p: %d, text left: %r", typeNames, p, text[p:])
        # Grab additional fields
        # Example: $x = $obj<p>->getFields()->field2
        while p+2 < len(styles) and styles[p] == self.PHP_OPERATOR and \
              text[p] in (":->\\"):
            isNamespace = False
            if text[p] == "\\":
                isNamespace = True
            p += 1
            log.debug("while:: p: %d, text left: %r", p, text[p:])
            if styles[p] == self.PHP_IDENTIFIER or \
               (styles[p] == self.PHP_VARIABLE and text[p-1] == ":"):
                additionalNames, p = self._getOneIdentifierFromPos(styles, text, p, styles[p])
                log.debug("p: %d, additionalNames: %r", p, additionalNames)
                if additionalNames:
                    if isNamespace:
                        if typeNames:
                            typeNames[-1] += "\\%s" % (additionalNames[0])
                        else:
                            typeNames.append("\\%s" % (additionalNames[0]))
                    else:
                        typeNames.append(additionalNames[0])
                    if p < len(styles) and \
                       styles[p] == self.PHP_OPERATOR and text[p][0] == "(":
                        typeNames[-1] += "()"
                        p = self._skipPastParenArguments(styles, text, p+1)
                        log.debug("_skipPastParenArguments:: p: %d, text left: %r", p, text[p:])
        return typeNames, p

    def _skipPastParenArguments(self, styles, text, p):
        paren_count = 1
        while p < len(styles):
            if styles[p] == self.PHP_OPERATOR:
                if text[p] == "(":
                    paren_count += 1
                elif text[p] == ")":
                    if paren_count == 1:
                        return p+1
                    paren_count -= 1
            p += 1
        return p

    _citdl_type_from_cast = {
        "int":       "int",
        "integer":   "int",
        "bool":      "boolean",
        "boolean":   "boolean",
        "float":     "int",
        "double":    "int",
        "real":      "int",
        "string":    "string",
        "binary":    "string",
        "array":     "array()",   # array(), see bug 32896.
        "object":    "object",
    }
    def _getVariableType(self, styles, text, p, assignmentChar="="):
        """Set assignmentChar to None to skip over looking for this char first"""

        log.debug("_getVariableType: text: %r", text[p:])
        typeNames = []
        if p+1 < len(styles) and (assignmentChar is None or \
                                  (styles[p] == self.PHP_OPERATOR and \
                                   text[p] == assignmentChar)):
            # Assignment to the variable
            if assignmentChar is not None:
                p += 1
                if p+1 >= len(styles):
                    return typeNames, p

            if styles[p] == self.PHP_OPERATOR and text[p] == '&':
                log.debug("_getVariableType: skipping over reference char '&'")
                p += 1
                if p+1 >= len(styles):
                    return typeNames, p

            elif p+3 <= len(styles) and styles[p] == self.PHP_OPERATOR and \
                 text[p+2] == ')' and text[p+1] in self._citdl_type_from_cast:
                # Looks like a casting:
                # http://ca.php.net/manual/en/language.types.type-juggling.php#language.types.typecasting
                #   $bar = (boolean) $foo;
                typeNames = [self._citdl_type_from_cast.get(text[p+1])]
                log.debug("_getVariableType: casted to type: %r", typeNames)
                p += 3
                return typeNames, p

            if styles[p] == self.PHP_WORD:
                # Keyword
                keyword = text[p].lower()
                p += 1
                if keyword == "new":
                    typeNames, p = self._getIdentifiersFromPos(styles, text, p)
                    #if not typeNames:
                    #    typeNames = ["object"]
                elif keyword in ("true", "false"):
                    typeNames = ["boolean"];
                elif keyword == "array":
                    typeNames = ["array()"];
            elif styles[p] in self.PHP_STRINGS:
                p += 1
                typeNames = ["string"]
            elif styles[p] == self.PHP_NUMBER:
                p += 1
                typeNames = ["int"]
            elif styles[p] == self.PHP_IDENTIFIER:
                # PHP Uses mixed upper/lower case for boolean values.
                if text[p].lower() in ("true", "false"):
                    p += 1
                    typeNames = ["boolean"]
                elif text[p] == "clone":
                    # clone is a special method - bug 85534.
                    typeNames, p = self._getIdentifiersFromPos(styles, text, p+1,
                                            identifierStyle=self.PHP_VARIABLE)
                else:
                    typeNames, p = self._getIdentifiersFromPos(styles, text, p)
                    # Don't record null, as it doesn't help us with anything
                    if typeNames == ["NULL"]:
                        typeNames = []
                    elif typeNames and p < len(styles) and \
                       styles[p] == self.PHP_OPERATOR and text[p][0] == "(":
                        typeNames[-1] += "()"
            elif styles[p] == self.PHP_VARIABLE:
                typeNames, p = self._getIdentifiersFromPos(styles, text, p, self.PHP_VARIABLE)
            elif styles[p] == self.PHP_OPERATOR and text[p] == "\\":
                typeNames, p = self._getIdentifiersFromPos(styles, text, p, self.PHP_IDENTIFIER)
                    
        return typeNames, p

    def _getKeywordArguments(self, styles, text, p, keywordName):
        arguments = None
        while p < len(styles):
            if styles[p] == self.PHP_WORD and text[p] == keywordName:
                # Grab the definition
                p += 1
                arguments = []
                last_style = self.PHP_OPERATOR
                namespaced = False
                while p < len(styles):
                    if styles[p] == self.PHP_IDENTIFIER and \
                       last_style == self.PHP_OPERATOR:
                        if namespaced:
                            arguments[-1] += text[p]
                            namespaced = False
                        else:
                            arguments.append(text[p])
                    elif styles[p] == self.PHP_OPERATOR and text[p] == "\\":
                        if not arguments or last_style != self.PHP_IDENTIFIER:
                            arguments.append(text[p])
                        else:
                            arguments[-1] += text[p]
                        namespaced = True
                    elif styles[p] != self.PHP_OPERATOR or text[p] != ",":
                        break
                    last_style = styles[p]
                    p += 1
                arguments = ", ".join(arguments)
                break
            p += 1
        return arguments

    def _getExtendsArgument(self, styles, text, p):
        return self._getKeywordArguments(styles, text, p, "extends")

    def _getImplementsArgument(self, styles, text, p):
        return self._getKeywordArguments(styles, text, p, "implements")

    def _unquoteString(self, s):
        """Return the string without quotes around it"""
        if len(s) >= 2 and s[0] in "\"'":
            return s[1:-1]
        return s

    def _removeDollarSymbolFromVariableName(self, name):
        if name[0] == "$":
            return name[1:]
        return name

    def _getIncludePath(self, styles, text, p):
        """Work out the include string and return it (without the quotes)"""

        # Some examples (include has identical syntax):
        #   require 'prepend.php';
        #   require $somefile;
        #   require ('somefile.txt');
        # From bug: http://bugs.activestate.com/show_bug.cgi?id=64208
        # We just find the first string and use that
        #   require_once(CEON_CORE_DIR . 'core/datatypes/class.CustomDT.php');
        # Skip over first brace if it exists
        if p < len(styles) and \
           styles[p] == self.PHP_OPERATOR and text[p] == "(":
            p += 1
        while p < len(styles):
            if styles[p] in self.PHP_STRINGS:
                requirename = self._unquoteString(text[p])
                if requirename:
                    # Return with the first string found, we could do better...
                    return requirename
            p += 1
        return None

    def _unescape_string(self, s):
        """Unescape a PHP string."""
        return s.replace("\\\\", "\\")

    def _getConstantNameAndType(self, styles, text, p):
        """Work out the constant name and type is, returns these as tuple"""

        # Some examples (include has identical syntax):
        #   define('prepend', 1);
        #   define ('somefile', "file.txt");
        #   define('\namespace\CONSTANT', True);
        #   define(__NAMESPACE__ . '\CONSTANT', True);
        constant_name = ""
        constant_type = None
        if styles[p] == self.PHP_OPERATOR and text[p] == "(":
            p += 1
        while p < len(styles):
            if styles[p] in self.PHP_STRINGS:
                constant_name += self._unquoteString(text[p])
            elif styles[p] == self.PHP_IDENTIFIER and \
                 text[p] == "__NAMESPACE__" and self.currentNamespace:
                # __NAMESPACE__ is a special constant - we can expand this as we
                # know what the current namespace is.
                constant_name += self.currentNamespace.name
            elif text[p] == ",":
                constant_type, p = self._getVariableType(styles, text, p+1,
                                                         assignmentChar=None)
                break
            p += 1
        # We must ensure the name (which came from a PHP string is unescaped),
        # bug 90795.
        return self._unescape_string(constant_name), constant_type

    def _addAllVariables(self, styles, text, p):
        while p < len(styles):
            if styles[p] == self.PHP_VARIABLE:
                namelist, p = self._getIdentifiersFromPos(styles, text, p, self.PHP_VARIABLE)
                if len(namelist) == 1:
                    name = self._removeDollarSymbolFromVariableName(namelist[0])
                    # Don't add special internal variable names
                    if name in ("this", "self"):
                        # Lets see what we are doing with this
                        if p+3 < len(styles) and "".join(text[p:p+2]) in ("->", "::"):
                            # Get the variable the code is accessing
                            namelist, p = self._getIdentifiersFromPos(styles, text, p+2)
                            typeNames, p = self._getVariableType(styles, text, p)
                            if len(namelist) == 1 and typeNames:
                                log.debug("Assignment through %r for variable: %r", name, namelist)
                                self.addClassMember(namelist[0],
                                                    ".".join(typeNames),
                                                    doc=self.comment,
                                                    forceToClass=True)
                    elif name is not "parent":
                        # If next text/style is not an "=" operator, then add
                        # __not_defined__, which means the variable was not yet
                        # defined at the position it was ciled.
                        attributes = None
                        if p < len(styles) and text[p] != "=":
                            attributes = "__not_yet_defined__"
                        self.addVariable(name, attributes=attributes)
            p += 1

    def _handleVariableComment(self, namelist, comment):
        """Determine any necessary information from the provided comment.
        Returns true when the comment was used to apply variable info, false
        otherwise.
        """
        log.debug("_handleVariableComment:: namelist: %r, comment: %r",
                  namelist, comment)
        if "@var" in comment:
            doc = uncommentDocString(comment)
            # get the variable citdl type set by "@var"
            all_matches = re.findall(PHPVariable._re_var, doc)
            if len(all_matches) >= 1:
                #print all_matches[0]
                varname = all_matches[0][1]
                vartype = all_matches[0][2]
                php_variable = None
                if varname:
                    # Optional, defines the variable this is applied to.
                    php_variable = self.addVariable(varname, vartype,
                                                    doc=comment,
                                                    fromPHPDoc=True)
                    return True
                elif namelist:
                    php_variable = self.addVariable(namelist[0], vartype,
                                                    doc=comment,
                                                    fromPHPDoc=True)
                    return True
        return False

    def _variableHandler(self, styles, text, p, attributes, doc=None,
                         style="variable"):
        log.debug("_variableHandler:: style: %r, text: %r, attributes: %r",
                  style, text[p:], attributes)
        classVar = False
        if attributes:
            classVar = True
            if "var" in attributes:
                attributes.remove("var")  # Don't want this in cile output
        if style == "const":
            if self.currentClass is not None:
                classVar = True
            elif self.currentNamespace is not None:
                classVar = False
            else:
                log.debug("Ignoring const %r, as not defined in a "
                          "class or namespace context.", text)
                return
        looped = False
        while p < len(styles):
            if looped:
                if text[p] != ",":  # Variables need to be comma delimited.
                    p += 1
                    continue
                p += 1
            else:
                looped = True
            if style == "const":
                namelist, p = self._getIdentifiersFromPos(styles, text, p,
                                                          self.PHP_IDENTIFIER)
            else:
                namelist, p = self._getIdentifiersFromPos(styles, text, p,
                                                          self.PHP_VARIABLE)
            if not namelist:
                break
            log.debug("namelist:%r, p:%d", namelist, p)
            # Remove the dollar sign
            name = self._removeDollarSymbolFromVariableName(namelist[0])
            # Parse special internal variable names
            if name == "parent":
                continue
            thisVar = False
            if name in ("this", "self", ):
                classVar = True
                thisVar = True # need to distinguish between class var types.
                if len(namelist) <= 1:
                    continue
                # We don't need the this/self piece of the namelist.
                namelist = namelist[1:]
                name = namelist[0]
            if len(namelist) != 1:
                # Example:  "item->foo;"  translates to namelist: [item, foo]
                if self.comment:
                    # We may be able to get some PHPDoc out of the comment.
                    if self._handleVariableComment(namelist, self.comment):
                        self.comment = None
                log.info("multiple part variable namelist (ignoring): "
                         "%r, line: %d in file: %r", namelist,
                         self.lineno, self.filename)
                continue
            if name.endswith("()"):
                # Example:  "foo(x);"  translates to namelist: [foo()]
                if self.comment:
                    # We may be able to get some PHPDoc out of the comment.
                    if self._handleVariableComment(namelist, self.comment):
                        self.comment = None
                log.info("variable is making a method call (ignoring): "
                         "%r, line: %d in file: %r", namelist,
                         self.lineno, self.filename)
                continue

            assignChar = text[p]
            typeNames = []
            mustCreateVariable = False
            # Work out the citdl, we also ensure this is not just a comparison,
            # i.e. not "$x == 2".
            if p+1 < len(styles) and styles[p] == self.PHP_OPERATOR and \
                                         assignChar in "=" and \
               (p+2 >= len(styles) or text[p+1] != "="):
                # Assignment to the variable
                mustCreateVariable = True
                typeNames, p = self._getVariableType(styles, text, p, assignChar)
                log.debug("typeNames: %r", typeNames)
                # Skip over paren arguments from class, function calls.
                if typeNames and p < len(styles) and \
                   styles[p] == self.PHP_OPERATOR and text[p] == "(":
                    p = self._skipPastParenArguments(styles, text, p+1)

            # Create the variable cix information.
            if mustCreateVariable or (not thisVar and p < len(styles) and
                                      styles[p] == self.PHP_OPERATOR and \
                                      text[p] in ",;"):
                log.debug("Line %d, variable definition: %r",
                         self.lineno, namelist)
                if style == "const":
                    if classVar:
                        self.addClassConstant(name, ".".join(typeNames),
                                              doc=self.comment)
                    else:
                        self.addConstant(name, ".".join(typeNames),
                                         doc=self.comment)
                elif classVar and self.currentClass is not None:
                    self.addClassMember(name, ".".join(typeNames),
                                        attributes=attributes, doc=self.comment,
                                        forceToClass=classVar)
                else:
                    self.addVariable(name, ".".join(typeNames),
                                     attributes=attributes, doc=self.comment)

    def _useNamespaceHandler(self, styles, text, p):
        log.debug("_useNamespaceHandler:: text: %r", text[p:])
        looped = False
        while p < len(styles):
            if looped:
                if text[p] != ",":  # Use statements need to be comma delimited.
                    p += 1
                    continue
                p += 1
            else:
                looped = True

            namelist, p = self._getIdentifiersFromPos(styles, text, p)
            log.debug("use:%r, p:%d", namelist, p)
            if namelist:
                alias = None
                if p+1 < len(styles):
                    if styles[p] == self.PHP_WORD and \
                       text[p] == "as":
                        # Uses an alias
                        alias, p = self._getIdentifiersFromPos(styles, text, p+1)
                        if alias:
                            alias = alias[0]
                self.addNamespaceImport(namelist[0], alias)

    def _addCodePiece(self, newstate=S_DEFAULT, varnames=None):
        styles = self.styles
        if len(styles) == 0:
            return
        text = self.text
        lines = self.linenos

        log.debug("*** Line: %d ********************************", self.lineno)
        #log.debug("Styles: %r", self.styles)
        log.debug("Text: %r", self.text)
        #log.debug("Comment: %r", self.comment)
        #log.debug("")

        pos = 0
        attributes = []
        firstStyle = styles[pos]

        try:
            # We may be able to get some PHPDoc out of the comment already,
            # such as targeted "@var " comments.
            # http://bugs.activestate.com/show_bug.cgi?id=76676
            if self.comment and self._handleVariableComment(None, self.comment):
                self.comment = None

            # Eat special attribute keywords
            while firstStyle == self.PHP_WORD and \
                  text[pos] in ("var", "public", "protected", "private",
                                "final", "static", "abstract"):
                attributes.append(text[pos])
                pos += 1
                firstStyle = styles[pos]
    
            if firstStyle == self.PHP_WORD:
                keyword = text[pos].lower()
                pos += 1
                if pos >= len(lines):
                    # Nothing else here, go home
                    return
                self.lineno = lines[pos]
                if keyword in ("require", "include", "require_once", "include_once"):
                    # Some examples (include has identical syntax):
                    # require 'prepend.php';
                    # require $somefile;
                    # require ('somefile.txt');
                    # XXX - Below syntax is not handled...
                    # if ((include 'vars.php') == 'OK') {
                    namelist = None
                    if pos < len(styles):
                        requirename = self._getIncludePath(styles, text, pos)
                        if requirename:
                            self.include_file(requirename)
                        else:
                            log.debug("Could not work out requirename. Text: %r",
                                      text[pos:])
                elif keyword == "define":
                    # Defining a constant
                    #   define("FOO",     "something");
                    #   define('TEST_CONSTANT', FALSE);
                    name, citdl = self._getConstantNameAndType(styles, text, pos)
                    if name:
                        self.addDefine(name, citdl)

                elif keyword == "const":
                    # Defining a class constant
                    #   const myconstant = x;
                    self._variableHandler(styles, text, pos, attributes,
                                          doc=self.comment, style="const")

                elif keyword == "function":
                    namelist, p = self._getIdentifiersFromPos(styles, text, pos)
                    log.debug("namelist:%r, p:%d", namelist, p)
                    if namelist:
                        returnByRef = (text[pos] == "&")
                        phpArgs, p = self._getArgumentsFromPos(styles, text, p)
                        log.debug("Line %d, function: %r(%r)",
                                 self.lineno, namelist, phpArgs)
                        if len(namelist) != 1:
                            log.info("warn: invalid function name (ignoring): "
                                     "%r, line: %d in file: %r", namelist,
                                     self.lineno, self.filename)
                            return
                        self.addFunction(namelist[0], phpArgs, attributes,
                                         doc=self.comment,
                                         returnByRef=returnByRef)
                elif keyword == "class":
                    # Examples:
                    #   class SimpleClass {
                    #   class SimpleClass2 extends SimpleClass {
                    #   class MyClass extends AbstractClass implements TestInterface, TestMethodsInterface {
                    #
                    namelist, p = self._getIdentifiersFromPos(styles, text, pos)
                    if namelist and "{" in text:
                        if len(namelist) != 1:
                            log.info("warn: invalid class name (ignoring): %r, "
                                     "line: %d in file: %r", namelist,
                                     self.lineno, self.filename)
                            return
                        extends = self._getExtendsArgument(styles, text, p)
                        implements = self._getImplementsArgument(styles, text, p)
                        #print "extends: %r" % (extends)
                        #print "implements: %r" % (implements)
                        self.addClass(namelist[0], extends=extends,
                                      attributes=attributes,
                                      interfaces=implements, doc=self.comment)
                elif keyword == "interface":
                    # Examples:
                    #   interface Foo {
                    #   interface SQL_Result extends SeekableIterator, Countable {
                    #
                    namelist, p = self._getIdentifiersFromPos(styles, text, pos)
                    if namelist and "{" in text:
                        if len(namelist) != 1:
                            log.info("warn: invalid interface name (ignoring): "
                                     "%r, line: %d in file: %r", namelist,
                                     self.lineno, self.filename)
                            return
                        extends = self._getExtendsArgument(styles, text, p)
                        self.addInterface(namelist[0], extends, doc=self.comment)
                elif keyword == "return":
                    # Returning value for a function call
                    #   return 123;
                    #   return $x;
                    typeNames, p = self._getVariableType(styles, text, pos, assignmentChar=None)
                    log.debug("typeNames:%r", typeNames)
                    if typeNames:
                        self.addReturnType(".".join(typeNames))
                elif keyword == "catch" and pos+3 >= len(text):
                    # catch ( Exception $e)
                    pos += 1   # skip the paren
                    typeNames, p = self._getVariableType(styles, text, pos, assignmentChar=None)
                    namelist, p = self._getIdentifiersFromPos(styles, text, p, self.PHP_VARIABLE)
                    if namelist and typeNames:
                        self.addVariable(namelist[0], ".".join(typeNames))
                elif keyword == "namespace":
                    namelist, p = self._getIdentifiersFromPos(styles, text, pos)
                    log.debug("namelist:%r, p:%d", namelist, p)
                    if namelist:
                        usesBraces = "{" in text
                        self.setNamespace(namelist, usesBraces,
                                          doc=self.comment)
                elif keyword == "use":
                    self._useNamespaceHandler(styles, text, pos)
                else:
                    log.debug("Ignoring keyword: %s", keyword)
                    self._addAllVariables(styles, text, pos)
    
            elif firstStyle == self.PHP_IDENTIFIER:
                log.debug("Ignoring when starting with identifier")
            elif firstStyle == self.PHP_VARIABLE:
                # Defining scope for action
                self._variableHandler(styles, text, pos, attributes,
                                      doc=self.comment)
            else:
                log.debug("Unhandled first style:%d", firstStyle)
        finally:
            self._resetState(newstate)

    def _resetState(self, newstate=S_DEFAULT):
        self.state = newstate
        self.styles = []
        self.linenos = []
        self.text = []
        self.comment = None
        self.comments = []

    def token_next(self, style, text, start_column, start_line, **other_args):
        """Loops over the styles in the document and stores important info.
        
        When enough info is gathered, will perform a call to analyze the code
        and generate subsequent language structures. These language structures
        will later be used to generate XML output for the document."""
        #log.debug("text: %r", text)
        #print "text: %r, style: %r" % (text, style)

        if self.state == S_GET_HEREDOC_MARKER:
            if not text.strip():
                log.debug("Ignoring whitespace after <<<: %r", text)
                return
            self.heredocMarker = self._unquoteString(text)
            log.debug("getting heredoc marker: %r, now in heredoc state", text)
            self._resetState(S_IN_HEREDOC)

        elif self.state == S_IN_HEREDOC:
            # Heredocs *must* be on the start of a newline
            if text == self.heredocMarker and self.lastText and \
               self.lastText[-1] in "\r\n":
                log.debug("end of heredoc: %r", self.heredocMarker)
                self._resetState(self.return_to_state)
            else:
                log.debug("ignoring heredoc material")

        elif (style in (self.PHP_WORD, self.PHP_IDENTIFIER,
                      self.PHP_OPERATOR, self.PHP_NUMBER, self.PHP_VARIABLE) or
            style in (self.PHP_STRINGS)):
            # We keep track of these styles and the text associated with it.
            # When we gather enough info, these will be sent to the
            # _addCodePiece() function which will analyze the info.
            self.lineno = start_line + 1

            if style != self.PHP_OPERATOR:
                # Have to trim whitespace, as the identifier style is
                # also the default whitespace style... ugly!
                if style == self.PHP_IDENTIFIER:
                    text = text.strip()
                if text:
                    self.text.append(text)
                    self.styles.append(style)
                    self.linenos.append(self.lineno)
                    #print "Text:", text
            else:
                # Do heredoc parsing, since UDL cannot as yet
                if text == "<<<":
                    self.return_to_state = self.state
                    self.state = S_GET_HEREDOC_MARKER
                # Remove out any "<?php" and "?>" tags, see syntax description:
                #   http://www.php.net/manual/en/language.basic-syntax.php
                elif text.startswith("<?"):
                    if text[:5].lower() == "<?php":
                        text = text[5:]
                    elif text.startswith("<?="):
                        text = text[len("<?="):]
                    else:
                        text = text[len("<?"):]
                elif text.startswith("<%"):
                    if text.startswith("<%="):
                        text = text[len("<%="):]
                    else:
                        text = text[len("<%"):]
                if text.endswith("?>"):
                    text = text[:-len("?>")]
                elif text.endswith("<%"):
                    text = text[:-len("%>")]

                col = start_column + 1
                #for op in text:
                #    self.styles.append(style)
                #    self.text.append(op)
                #log.debug("token_next: line %d, %r" % (self.lineno, text))
                for op in text:
                    self.styles.append(style)
                    self.text.append(op)
                    self.linenos.append(self.lineno)
                    if op == "(":
                        # We can start defining arguments now
                        #log.debug("Entering S_IN_ARGS state")
                        self.return_to_state = self.state
                        self.state = S_IN_ARGS
                    elif op == ")":
                        #log.debug("Entering state %d", self.return_to_state)
                        self.state = self.return_to_state
                    elif op == "=":
                        if text == op:
                            #log.debug("Entering S_IN_ASSIGNMENT state")
                            self.state = S_IN_ASSIGNMENT
                    elif op == "{":
                        # Increasing depth/scope, could be an argument object
                        self._addCodePiece()
                        self.incBlock()
                    elif op == "}":
                        # Decreasing depth/scope
                        if len(text) == 1 and text[0] == "}":
                            self._resetState()
                        else:
                            self._addCodePiece()
                        self.decBlock()
                    elif op == ":":
                        # May be an alternative syntax
                        if len(self.text) > 0 and \
                           self.styles[0] == self.PHP_WORD and \
                           self.text[0].lower() in ("if", "elseif", "else", "while", "for", "foreach", "switch"):
                            #print "Alt syntax? text: %r" % (self.text, )
                            self._addCodePiece()
                        elif "case" in self.text or "default" in self.text:
                            # Part of a switch statement - bug 86927.
                            self._addCodePiece()
                    elif op == ";":
                        # Statement is done
                        if len(self.text) > 0 and \
                           self.styles[0] == self.PHP_WORD and \
                           self.text[-1].lower() in ("endif", "endwhile", "endfor", "endforeach", "endswitch"):
                            # Alternative syntax, remove this from the text.
                            self.text = self.text[:-1]
                        self._addCodePiece()
                    col += 1
        elif style in self.PHP_COMMENT_STYLES:
            # Use rstrip to remove any trailing spaces or newline characters.
            comment = text.rstrip()
            # Check if it's a continuation from the last comment. If we have
            # already collected text then this is a comment in the middle of a
            # statement, so do not set self.comment, but rather just add it to
            # the list of known comment sections (self.comments).
            if not self.text:
                if style == SCE_UDL_SSL_COMMENT and self.comment and \
                   start_line <= (self.comments[-1][2] + 1) and \
                   style == self.comments[-1][1]:
                    self.comment += comment
                else:
                    self.comment = comment
            self.comments.append([comment, style, start_line, start_column])
        elif style == SCE_UDL_SSL_DEFAULT and \
             self.lastStyle in self.PHP_COMMENT_STYLES and text[0] in "\r\n":
            # This is necessary as line comments are supplied to us without
            # the newlines, so check to see if this is a newline and if the
            # last line was a comment, append it the newline to it.
            if self.comment:
                self.comment += "\n"
            self.comments[-1][0] += "\n"
        elif is_udl_csl_style(style):
            self.csl_tokens.append({"style": style,
                                    "text": text,
                                    "start_column": start_column,
                                    "start_line": start_line})
        self.lastText = text
        self.lastStyle = style

    def scan_multilang_content(self, content):
        """Scan the given PHP content, only processes SSL styles"""
        PHPLexer().tokenize_by_style(content, self.token_next)
        return self.csl_tokens

    def convertToElementTreeFile(self, cixelement):
        """Store PHP information into the cixelement as a file(s) sub element"""
        self.cile.convertToElementTreeFile(cixelement)

    def convertToElementTreeModule(self, cixblob):
        """Store PHP information into already created cixblob"""
        self.cile.convertToElementTreeModule(cixblob)


#---- internal utility functions

def _isident(char):
    return "a" <= char <= "z" or "A" <= char <= "Z" or char == "_"

def _isdigit(char):
    return "0" <= char <= "9"


#---- public module interface


#---- registration

def register(mgr):
    """Register language support with the Manager."""
    mgr.set_lang_info(lang,
                      silvercity_lexer=PHPLexer(),
                      buf_class=PHPBuffer,
                      langintel_class=PHPLangIntel,
                      import_handler_class=PHPImportHandler,
                      cile_driver_class=PHPCILEDriver,
                      is_cpln_lang=True)
