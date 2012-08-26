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

"""CSS support for CodeIntel"""

import os
from os.path import isfile, isdir, exists, dirname, abspath, splitext, join
import sys
import stat
import string
from cStringIO import StringIO
import logging
import traceback
from pprint import pprint

import SilverCity
from SilverCity.Lexer import Lexer
from SilverCity import ScintillaConstants
from SilverCity.ScintillaConstants import (
    SCE_CSS_DIRECTIVE, SCE_CSS_DOUBLESTRING, SCE_CSS_IDENTIFIER,
    SCE_CSS_IDENTIFIER2, SCE_CSS_OPERATOR, SCE_CSS_SINGLESTRING,
    SCE_CSS_TAG, SCE_CSS_UNKNOWN_IDENTIFIER, SCE_CSS_VALUE,
    SCE_UDL_CSS_COMMENT, SCE_UDL_CSS_DEFAULT, SCE_UDL_CSS_IDENTIFIER,
    SCE_UDL_CSS_NUMBER, SCE_UDL_CSS_OPERATOR, SCE_UDL_CSS_STRING,
    SCE_UDL_CSS_WORD, SCE_UDL_M_STRING, SCE_UDL_M_ATTRNAME, SCE_UDL_M_OPERATOR,
)
from SilverCity import Keywords

from codeintel2.common import *
from codeintel2.buffer import Buffer
from codeintel2.util import (OrdPunctLast, make_short_name_dict,
                             makePerformantLogger)
from codeintel2.langintel import LangIntel, ParenStyleCalltipIntelMixin
from codeintel2.udl import UDLBuffer, is_udl_css_style
from codeintel2.accessor import AccessorCache
from codeintel2 import constants_css3 as constants_css
from codeintel2 import constants_css_microsoft_extensions
from codeintel2 import constants_css_moz_extensions
from codeintel2 import constants_css_webkit_extensions

if _xpcom_:
    from xpcom.server import UnwrapObject



#---- globals

lang = "CSS"
log = logging.getLogger("codeintel.css")
makePerformantLogger(log)
WHITESPACE = tuple(" \t\r\n")  # care about '\v', '\f'?



#---- language support

# Taken from the Scite version 2.0.2 css.properties file
# Silvercity wants the # of wordlists to be the same as the
# number hardwired in the lexer, so that's why there are 5 empty lists.
raw_word_lists = [
    # CSS1 keywords
    """
    background background-attachment background-color background-image
    background-position background-repeat border border-bottom
    border-bottom-width border-color border-left border-left-width
    border-right border-right-width border-style border-top
    border-top-width border-width clear color display float font
    font-family font-size font-style font-variant font-weight height
    letter-spacing line-height list-style list-style-image
    list-style-position list-style-type margin margin-bottom margin-left
    margin-right margin-top padding padding-bottom padding-left
    padding-right padding-top text-align text-decoration text-indent
    text-transform vertical-align white-space width word-spacing
    """,
    # CSS pseudo-classes
    """
    active after before first first-child first-letter first-line
    focus hover lang left link right visited
    """,

    # CSS2 keywords
    """
    ascent azimuth baseline bbox border-bottom-color
    border-bottom-style border-collapse border-color border-left-color
    border-left-style border-right-color border-right-style
    border-spacing border-style border-top-color border-top-style
    bottom cap-height caption-side centerline clip content
    counter-increment counter-reset cue cue-after cue-before cursor
    definition-src descent direction elevation empty-cells
    font-size-adjust font-stretch left marker-offset marks mathline
    max-height max-width min-height min-width orphans outline
    outline-color outline-style outline-width overflow page
    page-break-after page-break-before page-break-inside panose-1
    pause pause-after pause-before pitch pitch-range play-during
    position quotes richness right size slope speak speak-header
    speak-numeral speak-punctuation speech-rate src stemh stemv stress
    table-layout text-shadow top topline unicode-bidi unicode-range
    units-per-em visibility voice-family volume widows widths x-height
    z-index
    """,
    # CSS3 Properties
    "",
    # Pseudo-elements
    "",
    # Browser-Specific CSS Properties
    "",
    # Browser-Specific Pseudo-classes
    "",
    # Browser-Specific Pseudo-elements
    "",
    ]
    
class CSSLexer(Lexer):
    lang = "CSS"
    def __init__(self):
        self._properties = SilverCity.PropertySet()
        self._lexer = SilverCity.find_lexer_module_by_id(ScintillaConstants.SCLEX_CSS)
        self._keyword_lists = []
        for i in range(len(raw_word_lists)):
            self._keyword_lists.append(SilverCity.WordList(raw_word_lists[i]))

class _StraightCSSStyleClassifier(object):
    def is_css_style(self, style, accessorCacheBack=None):
        return True

    def is_default(self, style, accessorCacheBack=None):
        return style in self.default_styles

    def is_comment(self, style, accessorCacheBack=None):
        return style in self.comment_styles

    def is_string(self, style, accessorCacheBack=None):
        return style in self.string_styles

    def is_operator(self, style, accessorCacheBack=None):
        return style in self.operator_styles or \
               style == ScintillaConstants.SCE_CSS_IMPORTANT

    def is_identifier(self, style, accessorCacheBack=None):
        return style in self.identifier_styles

    def is_value(self, style, accessorCacheBack=None):
        return style in self.value_styles

    def is_tag(self, style, accessorCacheBack=None):
        return style in self.tag_styles

    def is_class(self, style, accessorCacheBack=None):
        return style in self.class_styles

    def is_number(self, style, accessorCacheBack=None):
        return style in self.number_styles

    @property
    def default_styles(self):
        return (ScintillaConstants.SCE_CSS_DEFAULT, )

    @property
    def comment_styles(self):
        return (ScintillaConstants.SCE_CSS_COMMENT,)

    @property
    def string_styles(self):
        return (ScintillaConstants.SCE_CSS_SINGLESTRING,
                ScintillaConstants.SCE_CSS_DOUBLESTRING)

    @property
    def operator_styles(self):
        return (ScintillaConstants.SCE_CSS_OPERATOR, )

    @property
    def identifier_styles(self):
        return (ScintillaConstants.SCE_CSS_IDENTIFIER,
                ScintillaConstants.SCE_CSS_IDENTIFIER2,
                ScintillaConstants.SCE_CSS_UNKNOWN_IDENTIFIER)

    @property
    def value_styles(self):
        return (ScintillaConstants.SCE_CSS_VALUE,
                ScintillaConstants.SCE_CSS_NUMBER)

    @property
    def tag_styles(self):
        return (ScintillaConstants.SCE_CSS_TAG, )

    @property
    def class_styles(self):
        return (ScintillaConstants.SCE_CSS_CLASS, )

    @property
    def number_styles(self):
        return ()

    @property
    def ignore_styles(self):
        return (ScintillaConstants.SCE_CSS_DEFAULT,
                ScintillaConstants.SCE_CSS_COMMENT)

DebugStatus = False

class _UDLCSSStyleClassifier(_StraightCSSStyleClassifier):
    def is_css_style(self, style, accessorCacheBack=None):
        return is_udl_css_style(style)

    def _is_html_style_attribute(self, ac, style):
        # Check to see if it's a html style attribute
        # Note: We are starting from the html string delimiter, i.e.:
        #   <body style=<|>"abc...
        DEBUG = DebugStatus
        # We may have already found out this is a style attribute, check it
        if getattr(ac, "is_html_style_attribute", False):
            return True
        p, ch, style = ac.getPrecedingPosCharStyle(style,
                        ignore_styles=self.ignore_styles)
        if DEBUG:
            print "  _is_html_style_attribute:: Prev style: %d, ch: %r" % (
                  style, ch, )
        if style == SCE_UDL_M_OPERATOR:
            p, ch, style = ac.getPrecedingPosCharStyle(style,
                            ignore_styles=self.ignore_styles)
            if style == SCE_UDL_M_ATTRNAME:
                p, name = ac.getTextBackWithStyle(style)
                if DEBUG:
                    print "  _is_html_style_attribute:: HTML Attribute: %r" % (
                          name, )
                if name == "style":
                    # Remember this is a html style attribute
                    ac.is_html_style_attribute = True
                    return True
        return False

    def is_identifier(self, style, accessorCacheBack=None):
        if style not in self.identifier_styles:
            return False

        # Previous style must be operator and one of "{;"
        ac = accessorCacheBack
        if ac is not None:
            DEBUG = DebugStatus
            #DEBUG = True
            pcs = ac.getCurrentPosCharStyle()
            if DEBUG:
                print "  is_identifier:: pcs: %r" % (pcs, )
            try:
                # Check that the preceding character before the identifier
                ppcs = ac.getPrecedingPosCharStyle(pcs[2],
                                                   ignore_styles=self.ignore_styles)
                if DEBUG:
                    print "  is_identifier:: ppcs: %r" % (ppcs, )
                if self.is_operator(ppcs[2]) and ppcs[1] in "{;":
                    return True
                elif ppcs[2] == SCE_UDL_M_STRING and \
                     self._is_html_style_attribute(ac, ppcs[2]):
                    return True
                if DEBUG:
                    print "  is_identifier:: Not an identifier style"
            finally:
                # Reset the accessor back to the current position
                ac.resetToPosition(pcs[0])
        return False

    def is_class(self, style, accessorCacheBack=None):
        ac = accessorCacheBack
        if ac is not None:
            pcs = ac.getCurrentPosCharStyle()
            print "  is_class:: pcs: %r" % (pcs, )
            if self.is_operator(pcs[2]) and pcs[1] in ">.;}{":
                return True
            try:
                DEBUG = DebugStatus
                # Check that the preceding character before the identifier is a "."
                ppcs = ac.getPrecedingPosCharStyle(pcs[2],
                                                   ignore_styles=self.ignore_styles)
                if DEBUG:
                    print "  is_class:: ppcs: %r" % (ppcs, )
                if ppcs[2] in self.identifier_styles:
                    ppcs = ac.getPrecedingPosCharStyle(ppcs[2],
                                                       ignore_styles=self.ignore_styles)
                    if self.is_operator(ppcs[2]) and ppcs[1] == ".":
                        return True
                    elif not is_udl_css_style(ppcs[2]):
                        return True
                # If there is no identifer, may be operator, which is okay
                elif not is_udl_css_style(ppcs[2]) or \
                     (self.is_operator(ppcs[2]) and ppcs[1] in "};"):
                    return True
                if DEBUG:
                    print "  is_class:: Not a class style"
            finally:
                # Reset the accessor back to the current position
                ac.resetToPosition(pcs[0])
        return False

    def is_tag(self, style, accessorCacheBack=None):
        ac = accessorCacheBack
        if ac is not None:
            # Tags follow operators or other tags
            # For use, we'll go back until we find an operator in "}>"
            if style in self.identifier_styles:
                DEBUG = DebugStatus
                p, ch, style = ac.getCurrentPosCharStyle()
                start_p = p
                min_p = max(0, p - 50)
                try:
                    while p > min_p:
                        # Check that the preceding character before the identifier is a "."
                        p, ch, style = ac.getPrecedingPosCharStyle(style,
                                            ignore_styles=self.ignore_styles)
                        if style in self.operator_styles:
                            # Thats good, we get our decision now
                            if ch in "}>":
                                return True
                            elif ch == ",":
                                # Might be following another tag, "div, div",
                                # http://bugs.activestate.com/show_bug.cgi?id=58637
                                continue
                            if DEBUG:
                                print "  is_tag:: Not a tag operator ch: %s" % (ch)
                            return False
                        elif not self.is_css_style(style):
                            if DEBUG:
                                print "  is_tag:: Not a css style: %d, ch: %r" % (style, ch, )
                            if style == SCE_UDL_M_STRING and \
                               self._is_html_style_attribute(ac, style):
                                return False
                            return True
                        elif style not in self.identifier_styles:
                            if DEBUG:
                                print "  is_tag:: Not a tag style, style: %d" % (style)
                            return False
                        # else: # Thats okay, we'll keep going
                finally:
                    # Reset the accessor back to the current position
                    ac.resetToPosition(start_p)
        return False

    @property
    def default_styles(self):
        return (ScintillaConstants.SCE_UDL_CSS_DEFAULT, )

    @property
    def comment_styles(self):
        return (ScintillaConstants.SCE_UDL_CSS_COMMENT,)

    @property
    def string_styles(self):
        return (ScintillaConstants.SCE_UDL_CSS_STRING, )

    @property
    def operator_styles(self):
        return (ScintillaConstants.SCE_UDL_CSS_OPERATOR, )

    @property
    def identifier_styles(self):
        return (ScintillaConstants.SCE_UDL_CSS_IDENTIFIER,
                ScintillaConstants.SCE_UDL_CSS_WORD)

    @property
    def value_styles(self):
        return (ScintillaConstants.SCE_UDL_CSS_WORD,
                ScintillaConstants.SCE_UDL_CSS_IDENTIFIER,
                ScintillaConstants.SCE_UDL_CSS_NUMBER)

    @property
    def tag_styles(self):
        return (ScintillaConstants.SCE_CSS_TAG, )

    @property
    def number_styles(self):
        return (ScintillaConstants.SCE_UDL_CSS_NUMBER, )

    @property
    def ignore_styles(self):
        return (ScintillaConstants.SCE_UDL_CSS_DEFAULT,
                ScintillaConstants.SCE_UDL_CSS_COMMENT)


StraightCSSStyleClassifier = _StraightCSSStyleClassifier()
UDLCSSStyleClassifier      = _UDLCSSStyleClassifier()

class CSSLangIntel(LangIntel, ParenStyleCalltipIntelMixin):
    lang = "CSS"

    # CSS attributes:
    #     key (string) is the css property (attribute) name
    #     value (list) is the possible css property (attribute) values
    CSS_ATTRIBUTES = constants_css.CSS_ATTR_DICT.copy()
    CSS_ATTRIBUTES.update(constants_css_microsoft_extensions.CSS_MICROSOFT_SPECIFIC_ATTRS_DICT)
    CSS_ATTRIBUTES.update(constants_css_moz_extensions.CSS_MOZ_SPECIFIC_ATTRS_DICT)
    CSS_ATTRIBUTES.update(constants_css_webkit_extensions.CSS_WEBKIT_SPECIFIC_ATTRS_DICT)
    # Setup the names triggered for "property-names"
    CSS_PROPERTY_NAMES = sorted(CSS_ATTRIBUTES.keys(), key=OrdPunctLast)

    # Calltips for css property attributes
    CSS_PROPERTY_ATTRIBUTE_CALLTIPS_DICT = constants_css.CSS_PROPERTY_ATTRIBUTE_CALLTIPS_DICT.copy()
    CSS_PROPERTY_ATTRIBUTE_CALLTIPS_DICT.update(constants_css_microsoft_extensions.CSS_MICROSOFT_SPECIFIC_CALLTIP_DICT)
    CSS_PROPERTY_ATTRIBUTE_CALLTIPS_DICT.update(constants_css_moz_extensions.CSS_MOZ_SPECIFIC_CALLTIP_DICT)
    CSS_PROPERTY_ATTRIBUTE_CALLTIPS_DICT.update(constants_css_webkit_extensions.CSS_WEBKIT_SPECIFIC_CALLTIP_DICT)

    # Tag names
    CSS_HTML_TAG_NAMES = sorted(Keywords.hypertext_elements.split())

    # pseudo-class-names
    CSS_PSEUDO_CLASS_NAMES = sorted(constants_css.CSS_PSEUDO_CLASS_NAMES, key=OrdPunctLast)

    # at rules
    CSS_AT_RULE_NAMES = sorted(["import", "media", "charset", "font-face", "page", "namespace"],
                               key=OrdPunctLast)


    def preceding_trg_from_pos(self, buf, pos, curr_pos):
        DEBUG = DebugStatus # not using 'logging' system, because want to be fast
        #DEBUG = True # not using 'logging' system, because want to be fast

        if DEBUG:
            print "\npreceding_trg_from_pos -- pos: %d, curr_pos: %d" % (
                    pos, curr_pos, )
        if isinstance(buf, UDLBuffer):
            styleClassifier = UDLCSSStyleClassifier
        else:
            styleClassifier = StraightCSSStyleClassifier
        ac = AccessorCache(buf.accessor, curr_pos+1, fetchsize=50)
        currTrg = self._trg_from_pos(buf, (curr_pos == pos) and pos or pos+1,
                                     implicit=False, DEBUG=DEBUG,
                                     ac=ac, styleClassifier=styleClassifier)
        if DEBUG:
            print "  currTrg: %r" % (currTrg, )

        # If we're not looking for a previous trigger, or else the current
        # trigger position is for a calltip, then do not look any further.
        if (pos == curr_pos) or (currTrg and currTrg.form == TRG_FORM_CALLTIP):
            return currTrg
        # Else, work our way backwards from pos.

        ac.resetToPosition(pos+1)
        p, ch, style = ac.getPrevPosCharStyle()
        if DEBUG:
            print "  preceding_trg_from_pos: p: %r, ch: %r, style: %r" % (p, ch, style)
        min_p = max(0, p - 200)
        ignore_styles = styleClassifier.comment_styles + \
                        styleClassifier.string_styles + \
                        styleClassifier.number_styles
        while p > min_p and styleClassifier.is_css_style(style):
            p, ch, style = ac.getPrecedingPosCharStyle(style, ignore_styles=ignore_styles, max_look_back=100)
            if DEBUG:
                print "  preceding_trg_from_pos: Trying preceding p: %r, ch: %r, style: %r" % (p, ch, style)
            if ch and (isident(ch) or ch in ":( \t"):
                trg = self._trg_from_pos(buf, p+1, implicit=False, DEBUG=DEBUG,
                                         ac=ac, styleClassifier=styleClassifier)
                if trg is not None:
                    if DEBUG:
                        print "trg: %r" % (trg, )
                    if currTrg is not None:
                        if currTrg.type != trg.type:
                            if DEBUG:
                                print "  Next trigger is a different type, ending search"
                            return None
                        elif currTrg.form != trg.form:
                            return trg
                        elif DEBUG:
                            print "  Found same trigger again, continuing " \
                                  "looking for a different trigger"
                    else:
                        return trg
        return None

    def _trg_from_pos(self, buf, pos, implicit=True, DEBUG=False, ac=None, styleClassifier=None):
        #DEBUG = True # not using 'logging' system, because want to be fast
        if DEBUG:
            print "\n----- CSS _trg_from_pos(pos=%r, implicit=%r) -----"\
                  % (pos, implicit)
        try:
            if pos == 0:
                return None

            if ac is None:
                ac = AccessorCache(buf.accessor, pos, fetchsize=50)
            else:
                ac.resetToPosition(pos)
            # Ensure this variable is initialized as False, it is used by UDL
            # for checking if the css style is inside of a html tag, example:
            #   <p style="mycss: value;" />
            # When it's found that it is such a case, this value is set True
            ac.is_html_style_attribute = False

            last_pos, last_char, last_style = ac.getPrevPosCharStyle()
            if DEBUG:
                print "  _trg_from_pos:: last_pos: %s" % last_pos
                print "  last_char: %r" % last_char
                print "  last_style: %s" % last_style
    
            # The easy ones are triggering after any of '#.[: '.
            # For speed, let's get the common ' ' out of the way. The only
            # trigger on space is 'complete-property-values'.

            if styleClassifier.is_default(last_style):
                if DEBUG:
                    print "  _trg_from_pos:: Default style: %d, ch: %r" % (last_style, last_char)
                # Move backwards resolving ambiguity, default on "property-values"
                min_pos = max(0, pos - 200)
                while last_pos > min_pos:
                    last_pos, last_char, last_style = ac.getPrevPosCharStyle()
                    if styleClassifier.is_operator(last_style, ac) or styleClassifier.is_value(last_style, ac):
                        if DEBUG:
                            print " _trg_from_pos: space => property-values"
                        return Trigger("CSS", TRG_FORM_CPLN, "property-values",
                                       pos, implicit, extra={"ac": ac})
                    elif styleClassifier.is_tag(last_style, ac):
                        if DEBUG:
                            print " _trg_from_pos: space => tag-names"
                        return Trigger("CSS", TRG_FORM_CPLN, "tag-names",
                               pos, implicit, extra={"ac": ac})
                    elif styleClassifier.is_identifier(last_style, ac):
                        if DEBUG:
                            print " _trg_from_pos: space => property-names"
                        return Trigger("CSS", TRG_FORM_CPLN, "property-names",
                               pos, implicit, extra={"ac": ac})
                if DEBUG:
                    print " _trg_from_pos: couldn't resolve space, settling on property-names"
                return Trigger("CSS", TRG_FORM_CPLN, "property-values",
                                   pos, implicit, extra={"ac": ac})

            elif styleClassifier.is_operator(last_style, ac):
                # anchors
                if DEBUG:
                    print "  _trg_from_pos:: OPERATOR style"
                if last_char == '#':
                    return Trigger("CSS", TRG_FORM_CPLN, "anchors",
                                   pos, implicit, extra={"ac": ac})

                elif last_char == ':':
                    try:
                        p, ch, style = ac.getPrevPosCharStyle(ignore_styles=styleClassifier.ignore_styles)
                        if DEBUG:
                            print "  _trg_from_pos:: Looking at p: %d, ch: %r, style: %d" % (p, ch, style)
                    except IndexError:
                        style = None
                    if DEBUG:
                        print "  _trg_from_pos:: style: %r" % (style)
                    if style is None or \
                       not styleClassifier.is_identifier(style, ac):
                    #if style is None or \
                    #   not styleClassifier.is_css_style(style) or \
                    #   styleClassifier.is_class(style, ac):
                        # complete for pseudo-class-names
                        return Trigger("CSS", TRG_FORM_CPLN, "pseudo-class-names",
                                       pos, implicit, extra={"ac": ac})
                    else:
                    #if styleClassifier.is_identifier(style, ac):
                        # calltip for property-values
                        return Trigger("CSS", TRG_FORM_CALLTIP, "property-values",
                                       pos, implicit, extra={"ac": ac})

                # class-names
                elif last_char == '.':
                    return Trigger("CSS", TRG_FORM_CPLN, "class-names",
                                   pos, implicit, extra={"ac": ac})

                # at-rule
                elif last_char == '@':
                    #p, ch, style = ac.getPrevPosCharStyle(ignore_styles=styleClassifier.comment_styles)
                    # XXX - Should check not beyond first rule set
                    #     - Should check not within a rule block.
                    return Trigger("CSS", TRG_FORM_CPLN, "at-rule",
                                   pos, implicit, extra={"ac": ac})

                elif last_char == '/':
                    try:
                        p, ch, style = ac.getPrevPosCharStyle()
                    except IndexError:
                        pass
                    else:
                        if ch == "<":
                            # Looks like start of closing '</style>'
                            # tag. While typing this the styling will
                            # still be in the CSS range.
                            return Trigger(buf.m_lang, TRG_FORM_CPLN,
                                           "end-tag", pos, implicit)

            # tag-names
            elif styleClassifier.is_tag(last_style, ac):
                # We trigger on tag names of specified length >= 1 char
                if DEBUG:
                    print "  _trg_from_pos:: TAG style"
                p, ch, style = last_pos, last_char, last_style
                try:
                    while p >= 0:
                        if DEBUG:
                            print "  _trg_from_pos:: Looking at p: %d, ch: %r, style: %d" % (p, ch, style)
                        if not isident(ch):
                            p += 1
                            break
                        elif style != last_style:
                            if DEBUG:
                                print "  _trg_from_pos:: Current style is not a tag: %d" % (style)
                            return None
                        p, ch, style = ac.getPrevPosCharStyle()
                except IndexError:
                    p = 0
                return Trigger("CSS", TRG_FORM_CPLN, "tag-names",
                               p, implicit, extra={"ac": ac})

            elif styleClassifier.is_identifier(last_style, ac):
                if DEBUG:
                    print "  _trg_from_pos:: IDENTIFIER style"
                # property-names
                #print "here", accessor.text_range(0, pos)
                # We trigger on identifier names with any length >= 1 char
                pos = last_pos
                while pos >= 0:
                    pos, ch, style = ac.getPrevPosCharStyle()
                    if not isident(ch):
                        break
                    elif style != last_style:
                        return None
                return Trigger("CSS", TRG_FORM_CPLN, "property-names",
                               pos+1, implicit, extra={"ac": ac})

            elif styleClassifier.is_value(last_style, ac):
                p, ch, style = ac.getPrevPosCharStyle(ignore_styles=styleClassifier.comment_styles)
                if DEBUG:
                    print "  _trg_from_pos:: VALUE style"
                    print "  _trg_from_pos::   p: %s" % p
                    print "  _trg_from_pos::   ch: %r" % ch
                    print "  _trg_from_pos::   style: %s" % style
                    ac.dump()
                # Implicit triggering only happens on a whitespace character
                # after any one of these ":,%) " characters
                # Note: last_char can be a value style yet also be whitespace
                #       in straight CSS.
                if last_char in WHITESPACE:
                    return Trigger("CSS", TRG_FORM_CPLN, "property-values",
                                   last_pos+1, implicit, extra={"ac": ac})
                elif ch in WHITESPACE or ch in ":,%)":
                    # Check to ensure this is not a pseudo-class! Bug:
                    #   http://bugs.activestate.com/show_bug.cgi?id=71073
                    if ch == ":":
                        # Last style must be an identifier then!
                        pp, pch, pstyle = ac.getPrevPosCharStyle(
                                ignore_styles=styleClassifier.ignore_styles)
                        if DEBUG:
                            print "pp: %d, pch: %r, pstyle: %d" % (pp, pch,
                                                                   pstyle)
                        if not styleClassifier.is_identifier(pstyle, ac):
                            # This is likely a pseudo-class definition then,
                            # no trigger here.
                            if DEBUG:
                                print "pseudo-class style found, no trigger."
                            return None
                    return Trigger("CSS", TRG_FORM_CPLN, "property-values",
                                   p+1, implicit, extra={"ac": ac})
                # For explicit, we can also be inside a property already
                if not implicit and isident(ch):
                    # If there is already part of a value there, we need to move
                    # the trigger point "p" to the start of the value.
                    while isident(ch):
                        p, ch, style = ac.getPrevPosCharStyle()
                    return Trigger("CSS", TRG_FORM_CPLN, "property-values",
                                   p+1, implicit, extra={"ac": ac})
                return None

            elif DEBUG:
                print "  _trg_from_pos:: Unexpected style: %d, ch: %r" % (last_style, last_char)

            # XXX "at-property-names" - Might be used later
            #elif last_style == SCE_CSS_DIRECTIVE:
            #    # property-names
            #    # We trigger on identifier names with length == 3
            #    #print "here", accessor.text_range(0, pos)
            #    if pos >= 4 and accessor.char_at_pos(pos - 4) == ' ' and \
            #       self._is_ident_of_length(accessor, pos, length=3):
            #        # We are good for completion
            #        if DEBUG:
            #            print "Got a trigger for 'at-property-names'"
            #        return Trigger("CSS", TRG_FORM_CPLN, "at-property-names",
            #                       pos-3, implicit, extra={"ac": ac})

        except IndexError:
            # Wen't out of range of buffer before we found anything useful
            pass

        if DEBUG:
            print "----- CSS trg_from_pos() -----"
        return None

    def trg_from_pos(self, buf, pos, implicit=True, ac=None):
        DEBUG = DebugStatus # not using 'logging' system, because want to be fast
        if isinstance(buf, UDLBuffer):
            # This is CSS content in a multi-lang buffer.
            return self._trg_from_pos(buf, pos, implicit, DEBUG, ac, UDLCSSStyleClassifier)
        else:
            return self._trg_from_pos(buf, pos, implicit, DEBUG, ac, StraightCSSStyleClassifier)

    def _async_eval_at_trg(self, buf, trg, ctlr, styleClassifier):
        # Note: Currently this is NOT asynchronous. I believe that is fine
        # as long as evaluation is fast -- because the IDE UI thread could
        # be blocked on this. If processing might be slow (e.g. scanning
        # a number of project files for appropriate anchors, etc.), then
        # this should be made asynchronous.
        if _xpcom_:
            trg = UnwrapObject(trg)
            ctlr = UnwrapObject(ctlr)
        DEBUG = DebugStatus
        #DEBUG = True
        if DEBUG:
            print "\n----- async_eval_at_trg(trg=%r) -----"\
                  % (trg)

        # Setup the AccessorCache
        extra = trg.extra
        ac = None
        #print "Extra: %r" % (extra)
        if isinstance(extra, dict):
            extra = extra.get("extra", None)
            if isinstance(extra, dict):
                ac = extra.get("ac", None)
                if ac and DEBUG:
                    print "  _async_eval_at_trg:: Trigger had existing AC"
                    ac.dump()
        if ac is None:
            if DEBUG:
                print "  _async_eval_at_trg:: Created new trigger!"
            ac = AccessorCache(buf.accessor, trg.pos, fetchsize=20)

        ctlr.start(buf, trg)
        pos = trg.pos

        try:
            if trg.id == ("CSS", TRG_FORM_CPLN, "tag-names"):
                if DEBUG:
                    print "  _async_eval_at_trg:: 'tag-names'"
                cplns = self.CSS_HTML_TAG_NAMES
                if DEBUG:
                    print "  _async_eval_at_trg:: cplns:", cplns
                if cplns:
                    ctlr.set_cplns( [ ("element", v) for v in cplns ] )
                ctlr.done("success")
            elif trg.id == ("CSS", TRG_FORM_CPLN, "anchors"):
                # Can be a colour or an id tag, depending upon what the
                # previous char/style is
                # The previous style must be an op style or alphanumeric ch
                #i = 0
                #max_total_lookback = 100 # Up to 100 chars back
                #while i < max_total_lookback:
                #    p, ch, style = ac.getPrecedingPosCharStyle(last_style,
                #                    ignore_styles=styleClassifier.ignore_styles)
                #    if not is_udl_css_style(style) or \
                #       (styleClassifier.is_operator(style, ac) and \
                #        ch in "};"):
                #    i = last_pos - p
                # XXX - Needs to lookup the project HTML files for anchors...
                #anchors = self._get_all_anchors_names_in_project(accessor)
                ctlr.done("success")
            elif trg.id == ("CSS", TRG_FORM_CPLN, "class-names"):
                #raise NotImplementedError("not yet implemented: completion for "
                #                          "most css triggers")
                ctlr.done("success")
            elif trg.id == ("CSS", TRG_FORM_CPLN, "property-names"):
                cplns = self.CSS_PROPERTY_NAMES
                if cplns:
                    # Note: we add the colon as well - see bug 89913.
                    ctlr.set_cplns( [ ("property", v + ": ") for v in cplns ] )
                    # We want to show the property values after autocompleting.
                    trg.retriggerOnCompletion = True
                    #print "  _async_eval_at_trg:: cplns:", cplns
                ctlr.done("success")
            elif trg.id == ("CSS", TRG_FORM_CALLTIP, "property-values"):
                property, v1, v2 \
                    = self._extract_css_declaration(ac, styleClassifier, trg,
                                                    is_for_calltip=True)
                if DEBUG:
                    print "  _async_eval_at_trg:: Property name: %r" % \
                            (property, )
                try:
                    calltip = self.CSS_PROPERTY_ATTRIBUTE_CALLTIPS_DICT[property]
                    if DEBUG:
                        print "  _async_eval_at_trg:: calltip:", calltip
                    ctlr.set_calltips([calltip])
                except KeyError:
                    #print "Unknown CSS property: '%s'" % (property)
                    pass    # Ignore unknown CSS attributes
                ctlr.done("success")
            elif trg.id == ("CSS", TRG_FORM_CPLN, "property-values"):
                property, current_value, values \
                    = self._extract_css_declaration(ac, styleClassifier, trg)
                if DEBUG:
                    print "  _async_eval_at_trg:: XXX property: %r, " \
                          " current_value: %r, values: %r" % (property,
                                                              current_value,
                                                              values)
                try:
                    #print "\ndict:", self.CSS_ATTRIBUTES[property]
                    property_values = sorted(self.CSS_ATTRIBUTES[property],
                                             key=OrdPunctLast)
                    # Check if it matches anything, if not, dismiss the list
                    if current_value:
                        clen = len(current_value)
                        for v in property_values:
                            if clen <= len(v) and current_value == v[:clen]:
                                # Found a match
                                break
                        # Else, return the full list, even though no match made
                        # XXX - May want to cancel the CC list, any way to do this?
                    cplns = [("value", v)
                             for v in property_values
                             if v not in values or v == current_value]
                    ctlr.set_cplns(cplns)
                except KeyError:
                    if DEBUG: 
                        print "  _async_eval_at_trg:: Unknown CSS property: "\
                              "'%s'" % (property)
                    pass    # Ignore unknown CSS attributes
                ctlr.done("success")
    
                #XXX Handling for property not in list.
            elif trg.id == ("CSS", TRG_FORM_CPLN, "pseudo-class-names"):
                cplns = [("pseudo-class", v)
                         for v in self.CSS_PSEUDO_CLASS_NAMES]
                ctlr.set_cplns(cplns)
                ctlr.done("success")
            elif trg.id == ("CSS", TRG_FORM_CPLN, "at-rule"):
                cplns = [("rule", v)
                         for v in self.CSS_AT_RULE_NAMES]
                ctlr.set_cplns(cplns)
                ctlr.done("success")
    
            # Punt - Lower priority
            #elif trg.id == ("CSS", TRG_FORM_CPLN, "units"):
    
            # Punt - Fancy
            #elif trg.id == ("CSS", TRG_FORM_CPLN, "import-url"):
    
            # Punt - uncommon
            #elif trg.id == ("CSS", TRG_FORM_CPLN, "attr-names"):
            #elif trg.id == ("CSS", TRG_FORM_CPLN, "attr-values"):
    
            else:
                raise NotImplementedError("not yet implemented: completion for "
                                          "most css triggers: trg.id: %s" % (trg.id,))
        except IndexError:
            # Tried to go out of range of buffer, nothing appropriate found
            if DEBUG:
                print "  _async_eval_at_trg:: ** Out of range error **"
            ctlr.done("success")

    def async_eval_at_trg(self, buf, trg, ctlr):
        if isinstance(buf, UDLBuffer):
            # This is CSS content in a multi-lang buffer.
            return self._async_eval_at_trg(buf, trg, ctlr,
                                           UDLCSSStyleClassifier)
        else:
            return self._async_eval_at_trg(buf, trg, ctlr,
                                           StraightCSSStyleClassifier)

    def _get_all_anchors_names_in_project(self):
        #anchors = []
        #pos = 0
        #LENGTH = accessor.length
        #style = 0
        #func_style_at_pos = accessor.style_at_pos
        #func_char_at_pos = accessor.char_at_pos
        #while pos < LENGTH:
        #    if func_char_at_pos(pos) == '#' and \
        #       func_style_at_pos(pos) == SCE_CSS_OPERATOR:
        #        # Likely an anchor
        #        pass
        #    pos += 1
        #return anchors
        return []

    def _is_ident_of_length(self, accessor, pos, length=3):
        # Fourth char to left should not be an identifier
        if pos > length and isident(accessor.char_at_pos((pos - length) - 1)):
            return False
        # chars to left should all be identifiers
        for i in range(pos - 1, (pos - length) -1, -1):
            if not isident(accessor.char_at_pos(i)):
                return False
        return True

    def _extract_css_declaration(self, ac, styleClassifier, trg,
                                 is_for_calltip=False):
        """Extract the CSS declaration around the given position.

        Returns a 3-tuple:
            (<property>, <current_value>, <value_list>)

        If is_for_calltip is true, we do not bother to parse out the values, so
        <current_value> and <value_list> will be empty.

        The value gets parsed into <value_list>, a list of individual values.
        Comments and strings are striped from the return value.

        If the <current_value> is '', then the trigger position is
        ready to start a new value.
        """
        DEBUG = DebugStatus
        #DEBUG = True
        #PERF: Use accessor.gen_chars_and_styles() if possible.
        try:
            ac.resetToPosition(trg.pos)
            p, ch, style = ac.getPrevPosCharStyle()
            if not styleClassifier.is_operator(style, ac):
                if DEBUG:
                    print "Current ch is not an operator, so getting the " \
                          "preceeding one, p: %d, ch: %r, style: %d" % \
                          (p, ch, style, )
                p, ch, style = ac.getPrevPosCharStyle(
                                    ignore_styles=styleClassifier.ignore_styles)
        except IndexError:
            # This occurs when already at the end of the buffer, so we reset to
            # the last buffer position then
            ac.resetToPosition(trg.pos - 1)
            p, ch, style = ac.getCurrentPosCharStyle()
        if DEBUG:
            print """------ _extract_css_declaration -----"""
            print "  _extract_css_declaration:: Trg.pos: %d" % (trg.pos)
            #ac._debug = True
            print "  _extract_css_declaration:: pos: %r" % (p)
            print "  _extract_css_declaration:: ch: %r" % (ch)
            print "  _extract_css_declaration:: style: %r" % (style)
            ac.dump()
        # Walk back to ':' operator.
        num_close_parenthesis = 0
        min_pos = max(0, trg.pos - 200)  # Lookback up to 200 chars in total
        while p >= min_pos:
            #print "ch: %r, style: %d" % (ch, style, )
            if ch == ':' and styleClassifier.is_operator(style, ac):
                break
            elif num_close_parenthesis > 0:
                if ch == "(":
                    num_close_parenthesis -= 1
                    if DEBUG:
                        print "Found matching open paren," \
                              " num_close_parenthesis now: %d" % (
                                    num_close_parenthesis)
                elif DEBUG:
                    print "Ignoring everything inside the parenthesis"
            elif ch == "(" and (styleClassifier.is_operator(style) or
                                styleClassifier.is_value(style)):
                if DEBUG:
                    print "Already inside a paren, no cpln's then."
                    #XXX SCSS and Less support arithmetic expressions
                return (None, None, None)
            elif ch == ")" and (styleClassifier.is_operator(style) or
                                styleClassifier.is_value(style)):
                num_close_parenthesis += 1
                if DEBUG:
                    print "Found close paren, need to skip over contents," \
                          " num_close_parenthesis: %d" % (
                                num_close_parenthesis)
            elif styleClassifier.is_operator(style):
                if ch not in ":,%":
                    if DEBUG:
                        print "%s: couldn't find ':' operator, found invalid " \
                              "operator: %d %r %d" % (trg.name, p, ch, style)
                    #TODO: SCSS and Less support arithmetic expressions
                    return (None, None, None)
            elif styleClassifier.is_string(style):
                # Used to skip over string items in property values
                if DEBUG:
                    print "Found string style, ignoring it"
            elif not (styleClassifier.is_value(style) or styleClassifier.is_default(style)):
                # old CSS lexer: everything betwee ":" and ';' used to be a value.
                if DEBUG:
                    print "%s: couldn't find ':' operator, found invalid " \
                          "style: pcs: %d %r %d" % (trg.name, p, ch, style)
                return (None, None, None)
            p, ch, style = ac.getPrevPosCharStyle(
                                    ignore_styles=styleClassifier.ignore_styles)
        else:
            if DEBUG:
                print "%s: couldn't find ':' operator within 200 chars, " \
                      "giving up" % (trg.name)
            return (None, None, None)

        if DEBUG:
            print "  _extract_css_declaration:: Found ':' at pos: %d" % (p)
        # Parse out the property name.
        colan_pos = p
        p, ch, style = ac.getPrecedingPosCharStyle(style,
                                    ignore_styles=styleClassifier.ignore_styles,
                                    max_look_back=150)
        if style not in styleClassifier.identifier_styles:
            if DEBUG:
                print "  _extract_css_declaration:: No identifier style found" \
                      " before ':', found style %d instead" % (style)
            return (None, None, None)
        p, property = ac.getTextBackWithStyle(style)
        property = property.strip()

        if is_for_calltip:
            # We have all the info we need
            if DEBUG:
                print "  _extract_css_declaration:: Returning property: %r" % (
                            property)
            return (property, '', [])

        # Walk forward parsing the value information, ends when we hit a ";" or
        # have gone ahead a maximum of 200 chars.
        ac.resetToPosition(colan_pos)
        prev_pos, prev_ch, prev_style = ac.getCurrentPosCharStyle()
        from_pos = prev_pos
        p = colan_pos
        # Value info, list of tuples (pos, text)
        value_info = []
        max_p = p + 200
        try:
            while p < max_p:
                p, ch, style = ac.getNextPosCharStyle(max_look_ahead=100, ignore_styles=styleClassifier.comment_styles)
                if p is None or not styleClassifier.is_css_style(style):
                    # Went past max_look_ahead, just use what we've got then
                    if DEBUG:
                        print "%s: css value reached max length or end of " \
                              "document: trg.pos %d" % (trg.name, trg.pos)
                    value_info.append((from_pos, ac.text_range(from_pos, p)))
                    break
    
                if ch in WHITESPACE or styleClassifier.is_string(style):
                    if not prev_ch in WHITESPACE and not styleClassifier.is_string(prev_style):
                        value_info.append((from_pos, ac.text_range(from_pos, p)))
                    from_pos = p+1
                elif styleClassifier.is_operator(style):
                    if ch in ";{}":
                        value_info.append((from_pos, ac.text_range(from_pos, p)))
                        break
                    # Other chars should be okay to collect
                elif not styleClassifier.is_value(style) and \
                     style not in styleClassifier.ignore_styles:
                    if DEBUG:
                        print "%s: invalid style found: pos %d, style: %d" % (
                                 trg.name, trg.pos, style)
                    return (None, None, None)
                prev_pos, prev_ch, prev_style = p, ch, style
            else:
                if DEBUG:
                    print "%s: css value too long: trg.pos %d" % (trg.name, trg.pos)
                return (None, None, None)
        except IndexError:
            if DEBUG:
                print "ran out of buffer"

        # Work out the values and the current value
        current_value = None
        values = []
        trg_pos = trg.pos
        for p, value in value_info:
            if value and _isident_first_char(value[0]):
                if DEBUG:
                    print "Is a valid value, p: %d, value: %r" % (p, value, )
                values.append(value)
                if current_value is None and trg_pos >= p and \
                   trg_pos <= p + len(value):
                    current_value = value

        if DEBUG:
            print "  _extract_css_declaration:: Returning property: %r, " \
                  "current_value: %r, values: %r" % (property, current_value,
                                                     values)
        return (property, current_value, values)


class CSSBuffer(Buffer):
    lang = "CSS"
    sce_prefixes = ["SCE_CSS_"]
    # Removed '(' - double braces for completions that contain a '(' (bug 80063)
    # Removed '.' - conflict with floating point values: .5em (bug 80126)
    # Removed '{' - gets in way of "rule {" style declarations (bug 82358)
    # Removed '#' - gets in the way of hex colors and id selectors (bug 82968)
    # Removed '>' - gets in the way of child selectors (bug 87403)
    cpln_fillup_chars = " '\";},/"
    cpln_stop_chars = " ('\";{},.>/"



#---- internal support stuff

_ident_chars = string.lowercase + string.uppercase + string.digits + "-"
_ident_chars_dictionary = {}
ch = None
for ch in _ident_chars:
    _ident_chars_dictionary[ch] = 1
# Cleanup un-needed namespace definitions
del ch
del _ident_chars

def _isident_first_char(char):
    return isident(char) and char != "-" and (char < "0" or char > "9")

def isident(char):
    # In CSS2, identifiers  (including element names, classes, and IDs in
    # selectors) can contain only the characters [A-Za-z0-9] and ISO 10646
    # characters 161 and higher, plus the hyphen (-); they cannot start with a
    # hyphen or a digit
    return char in _ident_chars_dictionary or ord(char) >= 161

def _isdigit(char):
    return "0" <= char <= "9"

def _is_udl_css_ident(char):
    return "a" <= char <= "z" or "A" <= char <= "Z" \
            or char == "_" or char == "="



#---- registration

def register(mgr):
    """Register language support with the Manager."""
    mgr.set_lang_info(lang,
                      silvercity_lexer=CSSLexer(),
                      buf_class=CSSBuffer,
                      langintel_class=CSSLangIntel,
                      is_cpln_lang=True)

