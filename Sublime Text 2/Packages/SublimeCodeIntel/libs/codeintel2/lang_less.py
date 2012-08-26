#!/usr/bin/env python
# Copyright (c) 2010 ActiveState Software Inc.
# See LICENSE.txt for license details.

"""Less support for CodeIntel"""

import logging

from codeintel2.common import _xpcom_
from codeintel2.lang_css import CSSLexer, CSSLangIntel, CSSBuffer
from codeintel2.lang_css import isident, WHITESPACE
from codeintel2.accessor import AccessorCache
from codeintel2.common import Trigger, TRG_FORM_CPLN, TRG_FORM_CALLTIP
from codeintel2.util import OrdPunctLast
# ... and a whole lot more?

if _xpcom_:
    from xpcom.server import UnwrapObject


#---- globals

log = logging.getLogger("codeintel.less")
#log.setLevel(logging.DEBUG)


#---- language support

class LessLexer(CSSLexer):
    # This must be defined as "Less" in order to get autocompletion working.
    lang = "Less"

class SCSSLexer(CSSLexer):
    # This must be defined as "Less" in order to get autocompletion working.
    lang = "SCSS"

DebugStatus = False

def _OrdPunctLastOnSecondItem(value):
    return OrdPunctLast(value[1])

class _NestedCSSLangIntel(CSSLangIntel):
    def _trg_from_pos(self, buf, pos, implicit=True, DEBUG=False, ac=None, styleClassifier=None):
        #DEBUG = True # not using 'logging' system, because want to be fast
        if DEBUG:
            print "\n----- %s _trg_from_pos(pos=%r, implicit=%r) -----"\
                  % (self.lang, pos, implicit)
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
                        # Now we need to move further back to see which 
                        # region we're in.
                        if DEBUG:
                            print " _trg_from_pos: space => tag-names"
                        return self._get_property_name_trigger_check_context(ac, styleClassifier, pos, implicit)
                    elif styleClassifier.is_identifier(last_style, ac):
                        if DEBUG:
                            print " _trg_from_pos: space => property-names"
                        return Trigger(self.lang, TRG_FORM_CPLN, "tag-or-property-names",
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
                # Not quite like CSS: don't handle </

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
                return self._get_property_name_trigger_check_context(ac, styleClassifier, p, implicit)

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
                return self._get_property_name_trigger_check_context(ac, styleClassifier, pos + 1, implicit)

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

    def _get_property_name_trigger_check_context(self, ac,
                                                 styleClassifier, pos, implicit):
        min_pos = pos - 200
        if min_pos < 1:
            min_pos = 1
        try:
            ac.resetToPosition(pos)
        except IndexError:
            # We're at the start, so return tags only
            return Trigger("CSS", TRG_FORM_CPLN, "tag-names",
                           pos, implicit, extra={"ac": ac})
        
        # States:
        #
        last_pos, last_ch, last_style = ac.getCurrentPosCharStyle()
        #print "_get_property_name_trigger_check_context: last_pos:%d, last_ch:%c, last_style:%d" % (last_pos, last_ch, last_style)
        cpln_type = None
        p = last_pos
        while p > min_pos:
            try:
                p, ch, style = ac.getPrevPosCharStyle()
            except IndexError:
                p, ch, style = last_pos, last_ch, last_style
            if ch == '\n' and styleClassifier.is_default(style):
                # Main heuristic: if the tag starts on col 1, assume we're at the top-level
                if (styleClassifier.is_tag(last_style)
                    or styleClassifier.is_operator(last_style)):
                    cpln_type = "tag-names"
                    break
                elif styleClassifier.is_default(last_style):
                    cpln_type = "tag-or-property-names"
                    break
            elif ch == '{' and styleClassifier.is_operator(style):
                cpln_type = "tag-or-property-names"
                break
            if p < min_pos:
                break
            last_ch = ch
            last_style = style
        if cpln_type is None:
            if p <= 0:
                cpln_type = "tag-names"
            else:
                cpln_type = "tag-or-property-names"
        if cpln_type == "tag-or-property-names":
            lang = self.lang
        else:
            lang = "CSS" # Use the parent class.
        return Trigger(lang, TRG_FORM_CPLN, cpln_type,
                       pos, implicit, extra={"ac": ac})

    def _async_eval_at_trg(self, buf, trg, ctlr, styleClassifier):
        if _xpcom_:
            trg = UnwrapObject(trg)
            ctlr = UnwrapObject(ctlr)
        # Handle ambiguous property-names here
        DEBUG = DebugStatus
        #DEBUG = True
        if DEBUG:
            print "Less: _async_eval_at_trg: trg: %s(%r)" % (trg, trg)
        if trg.id != (self.lang, TRG_FORM_CPLN, "tag-or-property-names"):
            CSSLangIntel._async_eval_at_trg(self, buf, trg, ctlr, styleClassifier)
            return
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
            cplns1 = [ ("property", v + ": ") for v in self.CSS_PROPERTY_NAMES ]
            cplns2 = [ ("element", v) for v in self.CSS_HTML_TAG_NAMES ]
            cplns = sorted(cplns1 + cplns2, key=_OrdPunctLastOnSecondItem)
            # Note: we add the colon as well - see bug 89913.
            ctlr.set_cplns(cplns)
            #print "  _async_eval_at_trg:: cplns:", cplns
            ctlr.done("success")
            trg.retriggerOnCompletion = True
        except IndexError:
            # Tried to go out of range of buffer, nothing appropriate found
            if DEBUG:
                print "  _async_eval_at_trg:: ** Out of range error **"
            ctlr.done("success")

class LessLangIntel(_NestedCSSLangIntel):
    # This must be defined as "Less" in order to get autocompletion working.
    lang = "Less"

class SCSSLangIntel(_NestedCSSLangIntel):
    lang = "SCSS"

class LessBuffer(CSSBuffer):
    lang = "Less"

class SCSSBuffer(CSSBuffer):
    lang = "SCSS"

#---- registration

def register(mgr):
    """Register language support with the Manager."""
    mgr.set_lang_info("Less",
                      silvercity_lexer=LessLexer(),
                      buf_class=LessBuffer,
                      langintel_class=LessLangIntel,
                      is_cpln_lang=True)
    mgr.set_lang_info("SCSS",
                      silvercity_lexer=SCSSLexer(),
                      buf_class=SCSSBuffer,
                      langintel_class=SCSSLangIntel,
                      is_cpln_lang=True)

