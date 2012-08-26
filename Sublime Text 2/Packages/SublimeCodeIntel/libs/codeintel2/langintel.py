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

"""Base LangIntel class definition

Each lang_*.py registers a LangIntel instance -- a singleton (somewhat
similar to Komodo's language services, I suppose). This langintel defines
smarts for handling language content. This module contains some mixins
so that particular languages can implement the requisite interface easily.

Any single-language buffer has a '.langintel' attribute pointing to this
singleton. Any multi-language buffer (i.e. a subclass of UDLBuffer) has
a '.langintel_from_udl_family' dictionary.

TODO:
- document what interfaces a particular LangIntel is meant to provide

Dev Notes:
- Usage of LangIntel objects in code should always use 'langintel' in
  the variable name.
"""

import os
import re
import operator
from pprint import pformat, pprint
import logging

from codeintel2.common import *
from codeintel2.util import banner, indent, markup_text, isident, isdigit
import langinfo

if _xpcom_:
    from xpcom.server import UnwrapObject

log = logging.getLogger("codeintel.langintel")



class LangIntel(object):
    """Smarts about content of a given language.
    
    Typically the Buffer implementations defer to a language's LangIntel
    class for handling stuff specific to that language content. This is
    how multi-language buffers are handled.
    """
    # All "leaf" LangIntel subclasses must set the `lang` attribute.
    lang = None
    # Used by `preceding_trg_from_pos` for 3-char triggering for some langs.
    _last_trg_type = None 

    def __init__(self, mgr):
        self.mgr = mgr

    _langinfo_cache = None
    @property
    def langinfo(self):
        if self._langinfo_cache is None:
            try:
                self._langinfo_cache = self.mgr.lidb.langinfo_from_komodo_lang(self.lang)
            except langinfo.LangInfoError, ex:
                self._langinfo_cache = None
                log.exception("error getting langinfo for '%s'", self.lang)
        return self._langinfo_cache

    # Code Browser integration.
    cb_import_group_title = "Imports"
    cb_globalvar_group_title = "Global Variables"
    cb_group_global_vars = True

    def cb_blob_detail_from_elem_and_buf(self, elem, buf):
        if elem.get("lang") != buf.lang: # multi-lang doc
            return "%s Code in %s" % (elem.get("lang"), buf.path)
        else:
            dir, base = os.path.split(buf.path)
            if dir:
                return "%s (%s)" % (base, dir)
            else:
                return base

    def cb_import_data_from_elem(self, elem):
        # Python form by default.
        alias = elem.get("alias")
        symbol = elem.get("symbol")
        module = elem.get("module")
        if alias:
            if symbol:
                name = "%s (%s.%s)" % (alias, module, symbol)
                detail = "from %(module)s import %(symbol)s as %(alias)s" % locals()
            else:
                name = "%s (%s)" % (alias, module)
                detail = "import %(module)s as %(alias)s" % locals()
        elif symbol:
            name = '.'.join([module, symbol])
            detail = "from %(module)s import %(symbol)s" % locals()
        else:
            name = module
            detail = "import %(module)s" % locals()
        return {"name": name, "detail": detail}

    def cb_variable_data_from_elem(self, elem):
        attrs = elem.get("attributes", "").split()
        if elem.get("ilk") == "argument":
            img = "argument"
        elif "__instancevar__" in attrs:
            img = "instance-variable"
        else:
            img = "variable"
        if "private" in attrs:
            img += "-private"
        elif "protected" in attrs:
            img += "-protected"
        #TODO: Add 'detail'. C.f. cb.py::getDescForSymbol().
        return {"name": elem.get("name"),
                "img": img}

    def cb_function_detail_from_elem(self, elem):
        # by default (some languages may choose to override)
        sig = elem.get("signature")
        if sig:
            return sig
        else:
            return elem.get("name")+"(...)"
    
    def cb_class_detail_from_elem(self, elem):
        classrefs = elem.get("classrefs")
        if classrefs:
            return elem.get("name") + "(" + classrefs + ")"
        return elem.get("name")+"()"

    def cb_interface_detail_from_elem(self, elem):
        interfacerefs = elem.get("interfacerefs")
        if interfacerefs:
            return elem.get("name") + "(" + interfacerefs + ")"
        return elem.get("name")+"()"

    def cb_namespace_detail_from_elem(self, elem):
        return elem.get("name")

    def cb_data_from_elem_and_buf(self, elem, buf):
        """Return a dict of info for a code browser row for this element.
        
        - Should define "name" key.
        - Can define "detail" key. This is the string displayed when
          hovering over the image in the code browser.
        - Can define "img" key. This is string used to identify the
          image type. The following are common values:
            argument, variable, class, function, import, interface, namespace
          The symbol-types have -protected and -private versions, e.g.:
            variable-private, variable-protected, class-private, ...
          As well, many of the languages have associated icons:
            Perl, Python, JavaScript, Ruby, ...
          A few special ones for class instance vars:
            instance-variable, instance-variable-protected,
            instance-variable-private
          Some special ones:
            container, scanning, error
        """
        if elem.tag == "import":
            data = {"img": "import"}
            data.update( self.cb_import_data_from_elem(elem) )
            return data

        elif elem.tag == "variable":
            return self.cb_variable_data_from_elem(elem)

        elif elem.tag == "scope":
            ilk = elem.get("ilk")
            if ilk == "blob":
                img = elem.get("lang")
                detail = self.cb_blob_detail_from_elem_and_buf(elem, buf)
            else:
                img = ilk
                attrs = elem.get("attributes", "").split()
                if "private" in attrs:
                    img += "-private"
                elif "protected" in attrs:
                    img += "-protected"
                if ilk == "function":
                    detail = self.cb_function_detail_from_elem(elem)
                elif ilk == "class":
                    detail = self.cb_class_detail_from_elem(elem)
                elif ilk == "interface":
                    detail = self.cb_interface_detail_from_elem(elem)
                elif ilk == "namespace":
                    detail = self.cb_namespace_detail_from_elem(elem)
                else: # what else could it be?
                    log.warn("don't know how to get cb detail for '%s' elem",
                             ilk)
                    detail = elem.get("name")

            return {"name": elem.get("name"),
                    "img": img,
                    "detail": detail}
        else:
            return {"name": repr(elem)}


class ImplicitLangIntel(LangIntel):
    def __init__(self, lang, mgr):
        self.lang = lang
        LangIntel.__init__(self, mgr)
    def trg_from_pos(self, buf, pos, implicit=True):
        return None
    def preceding_trg_from_pos(self, buf, pos, curr_pos):
        return None
    def async_eval_at_trg(self, buf, trg, ctlr):
        if _xpcom_:
            trg = UnwrapObject(trg)
            ctlr = UnwrapObject(ctlr)
        ctlr.start(buf, trg)
        ctlr.done("success")

class ParenStyleCalltipIntelMixin(object):
    """A mixin class to implement `curr_calltip_arg_range' for languages
    with parenthesis-style call signatures.
    """
    # A sequence of terminator characters for a calltip region.
    calltip_region_terminators = tuple(']});')

    def calltip_verify_termination(self, accessor, ch, trg_pos, curr_pos):
        """Hook to allow language-specific, context-specific checking."""
        return True

    _parsed_calltip_cache = (None, None) # (<last-calltip>, <last-parsed-calltip>)
    def curr_calltip_arg_range(self, buf, trg_pos, calltip, curr_pos,
                               DEBUG=False):
        """Return that range in the calltip of the "current" arg.
        I.e. what argument is currently being entered.
        
            "buf" is the buffer object on which this is being done.
            "trg_pos" is the trigger position.
            "calltip" is the full calltip text.
            "curr_pos" is the current position in the buffer.
            
        Returns a range: (start, end)
        Set `start == -1` to cancel the calltip, i.e. if the entered text
        has closed the call region.

        The default implementation uses:
            self.calltip_region_terminators
        to handle languages with calltip signatures with the following
        characteristics:
        - uses '(' and ')' to bound the argument list (though because of
          support for ';' statement termination, this isn't absolutely
          required)
        - uses a comma to separate arguments
        - basic block delimiters are {}, (), and []

        For example:
            foo()
            blam(a, b)
            range([start,] stop[, step]) -> list of integers
            bar(arg1, *args, **kwargs)
            flash(boom, bang=42)
        """
        # Dev Notes:
        # - Eventually should pass in the trigger to aid in processing.
        # - TODO figure out dependence on buf.comment_styles() and
        #   buf.string_styles()
        accessor = buf.accessor
        if DEBUG:
            print banner("curr_calltip_arg_range")
            print "calltip:\n%s" % indent(calltip)
            print "buffer:\n%s" % indent(markup_text(accessor.text,
                                                     trg_pos=trg_pos,
                                                     pos=curr_pos))
            
        # Start from the trigger position and walk forward to the current
        # pos: counting args and looking for termination of the calltip
        # region.
        skip_styles = dict(
            (s, True) for s in buf.comment_styles() + buf.string_styles())
        if accessor.style_at_pos(trg_pos-1) in skip_styles:
            skip_styles = {}
        comma_count = 0
        blocks = {
            # Map a block start token to its block end token.
            '(': ')', '[': ']', '{': '}',
        }
        block_stack = []
        p = trg_pos
        for ch, style in accessor.gen_char_and_style(trg_pos, curr_pos):
            if DEBUG: print "pos %2d: %r (%2s) --" % (p, ch, style),
            if style in skip_styles:
                if DEBUG: print "skip"
            elif ch in blocks:
                if DEBUG: print "open block"
                block_stack.append(blocks[ch])
            elif block_stack:
                if ch == block_stack[-1]:
                    if DEBUG: print "close block"
                    block_stack.pop()
                elif ch in self.calltip_region_terminators:
                    if DEBUG: print "end of call region: (-1, -1)"
                    return (-1, -1)
                elif DEBUG:
                    print "ignore (in block)"
            elif ch == ',':
                if DEBUG: print "next arg"
                comma_count += 1
            elif ch in self.calltip_region_terminators and \
                 self.calltip_verify_termination(accessor, ch, trg_pos, curr_pos):
                if DEBUG: print "end of call region: (-1, -1)"
                return (-1, -1)
            elif DEBUG:
                print "ignore"
            p += 1

        # Parse the signature from the calltip. If there is no signature
        # then we default to not indicating any arg range.
        if self._parsed_calltip_cache[0] == calltip:
            parsed = self._parsed_calltip_cache[1]
        else:
            parsed = _parse_calltip(calltip, DEBUG)
            self._parsed_calltip_cache = (calltip, parsed)
        if parsed is None:
            if DEBUG: print "couldn't parse any calltip: (0, 0)"
            return (0, 0)
        signature, name, args = parsed
        if DEBUG:
            print "parsed calltip:\n  signature:\n%s\n  name:\n%s\n  args:\n%s"\
                  % (indent(signature), indent(name), indent(pformat(args)))

        if not args:
            if DEBUG: print "no args in signature: (0, 0)"
            return (0, 0)
        elif comma_count >= len(args):
            #XXX ellipsis
            if DEBUG: print "more commas than args: ellipsis?"
            span = args[-1].span # default to last arg
        else:
            span = args[comma_count].span

        if DEBUG:
            print "curr calltip range (%s, %s):" % (span[0], span[1])
            print indent(signature)
            print "    %s%s" % (' '*span[0], '-'*(span[1]-span[0]))
        return span



class ProgLangTriggerIntelMixin(object):
    """A mixin class to implement `preceding_trg_from_pos' for
    programming languages.

    How do you know if this is appropriate for your language? Write
    some test cases using assertPrecedingTriggerMatches() and see
    if this mixin works for those tests. It works fine for Python and
    Perl, for example.
    """
    # A sequence of characters at which all triggers occur.
    trg_chars = tuple('.(')

    # A sequence of characters at which all calltip triggers occur.
    calltip_trg_chars = tuple('(')

    # A dict of chars at which to always stop backtracking looking
    # for a preceding trigger point.  If no style is given the
    # character alone is sufficient.  Otherwise trigger if the
    # style matches.
    preceding_trg_terminators = {';': None}

    def preceding_trg_from_pos(self, buf, pos, curr_pos,
                               preceding_trg_terminators=None, DEBUG=False):
        accessor = buf.accessor
        if preceding_trg_terminators is None:
            preceding_trg_terminators = self.preceding_trg_terminators
        if DEBUG:
            print banner("preceding_trg_from_pos(pos=%r, curr_pos=%r)"
                          % (pos, curr_pos))
            print indent(markup_text(accessor.text, pos=curr_pos,
                                     start_pos=pos))
            print banner(None, '-')

        # Skip over comments and strings in our checking, unless we are
        # in one of these styles for the whole range. This is so an explicit
        # trigger in a comment (or, e.g., a doc string) will work, but
        # the appearance of small comments or strings in code will not mess
        # things up.
        comment_and_string_styles = dict(
            (s, True) for s in buf.comment_styles() + buf.string_styles())
        skip_styles = {}
        start_style = accessor.style_at_pos(pos-1)
        EOL_CHARS = tuple("\n\r")

        # Limiting simplification: Only backtrack a max of 200 chars.
        # Can increase that if necessary. The problem is detecting a
        # statement boundary backwards in langs like Python and Ruby
        # where you can't rely on ';' (actually
        # `preceding_trg_terminators').
        limit = max(1, pos - 200)
        
        # First stage. We only consider autocomplete trigger (i.e.
        # trg.form==TRG_FORM_COMPLETION) if within range of the
        # curr_pos. Here "within range" means you don't have to more the
        # cursor to show the autocomplete UI.
        first_stage_limit = curr_pos
        for (char, style) in accessor.gen_char_and_style_back(curr_pos-1,
                                                              limit-1):
            if not isident(char):
                break
            first_stage_limit -= 1
        if DEBUG:
            print "[stage 1] first_stage_limit=%d (prev_ch=%r)"\
                  % (first_stage_limit,
                     (first_stage_limit > 0
                      and accessor.char_at_pos(first_stage_limit-1)
                      or None))
        p = pos
        if p >= first_stage_limit:
            for (prev_ch, prev_style) in accessor.gen_char_and_style_back(p-1,
                                                          first_stage_limit-2):
                if (not skip_styles and prev_style != start_style
                    # EOLs in comments seem to always be style 0. Don't count
                    # them.
                    and prev_ch not in EOL_CHARS):
                    if DEBUG:
                        print "[stage 1] have seen a style change (%d -> %d), " \
                              "now skipping strings and comments" \
                              % (start_style, prev_style)
                    skip_styles = comment_and_string_styles
                if DEBUG:
                    print "[stage 1] consider pos %2d: prev_ch=%r (%d) --"\
                          % (p, prev_ch, prev_style),
                if prev_style in skip_styles:
                    if DEBUG: print "comment or string, skip it"
                elif self._is_terminating_char(prev_ch, prev_style,
                                               preceding_trg_terminators):
                    if DEBUG: print "in `preceding_trg_terminators': break"
                    return None
                elif prev_ch in self.trg_chars:
                    if DEBUG: print "trigger char, try it"
                    trg = buf.trg_from_pos(p, implicit=False)
                    if trg:
                        if DEBUG: print "[stage 1] %s" % trg
                        return trg
                    p -= 1
                    break
                elif DEBUG:
                    print "not a trigger char, skip it"
                p -= 1
        if DEBUG:
            print "[stage 1] end of possible autocomplete trigger range"

        # Second stage. We only consider calltip triggers now
        # (self.calltip_trg_chars).
        # 
        # As well, ignore enclosed paren sections to make sure we are
        # in-range. For example, we shouldn't trigger on "bar(" here:
        #   foo(bar("skip", "this", "arg", "list"), <|>)
        close_paren_count = 0
        for (prev_ch, prev_style) in accessor.gen_char_and_style_back(p-1, limit-2):
            if (not skip_styles and prev_style != start_style
                # EOLs in comments seem to always be style 0. Don't count
                # them.
                and prev_ch not in EOL_CHARS):
                if DEBUG:
                    print "[stage 2] seen a style change (%d -> %d), now " \
                          "skipping strings and comments" \
                          % (start_style, prev_style)
                skip_styles = comment_and_string_styles

            if DEBUG:
                print "[stage 2] consider pos %2d: prev_ch=%r (%d) --"\
                      % (p, prev_ch, prev_style),
            if prev_style in skip_styles:
                if DEBUG: print "comment or string, skip it"
            elif prev_ch == ')':
                close_paren_count += 1
                if DEBUG: print "close paren: count=%d" % close_paren_count
            elif close_paren_count and prev_ch == '(':
                close_paren_count -= 1
                if DEBUG: print "open paren: count=%d" % close_paren_count
            elif self._is_terminating_char(prev_ch, prev_style,
                                           preceding_trg_terminators):
                if DEBUG: print "in `preceding_trg_terminators': break"
                return None
            elif prev_ch in self.calltip_trg_chars:
                if DEBUG: print "trigger char, try it"
                trg = buf.trg_from_pos(p, implicit=False)
                if trg:
                    if DEBUG: print "[stage 2] %s" % trg
                    return trg
            elif DEBUG:
                print "not a trigger char, skip it"
            p -= 1

        return None

    def _is_terminating_char(self, ch, style, preceding_trg_terminators):
        terminating_style = preceding_trg_terminators.get(ch, -1)
        return terminating_style is None or terminating_style == style

class PythonCITDLExtractorMixin(object):
    """A LangIntel mixin class for
        citdl_expr_from_trg()
    for Python-like syntax.
    """

    # Dictionary of literal types to specific language citdl type.
    # Example for Python: {"string": "str"}
    # Example for JavaScript: {"string": "String"}
    citdl_from_literal_type = {}

    def _citdl_expr_from_pos(self, buf, pos, implicit=False,
                             include_forwards=False, DEBUG=False, trg=None):

        #PERF: Would dicts be faster for all of these?
        WHITESPACE = tuple(" \t\n\r\v\f")
        EOL = tuple("\r\n")
        BLOCKCLOSES = tuple(")}]")
        STOPOPS = tuple("({[,&+-=!^|%/<>;:#@")
        EXTRA_STOPOPS_PRECEDING_IDENT = BLOCKCLOSES # Might be others.

        #TODO: clean this up for LangIntel-usage
        if implicit:
            skip_styles = buf.implicit_completion_skip_styles
        else:
            skip_styles = buf.completion_skip_styles
        string_styles = buf.string_styles()
        comment_styles = buf.comment_styles()

        #XXX Add sentinel num chars?
        citdl_expr = []
        accessor = buf.accessor
        i = pos

        # Move ahead to include forward chars as well
        # We stop when we go out of the expression or when the expression is
        # becomes a multiple fragment, i.e.
        #  'sys.pa<|>th.expanduser' -> 'sys.path'
        if include_forwards:
            buf_length = accessor.length()
            if i < buf_length:
                max_look_ahead = min(buf_length, i+100)
                lastch_was_whitespace = False
                while i < max_look_ahead:
                    ch = accessor.char_at_pos(i)
                    style = accessor.style_at_pos(i)
                    if ch in WHITESPACE:
                        lastch_was_whitespace = True
                    elif ch in ".)}]" or ch in STOPOPS:
                        break
                    elif lastch_was_whitespace:
                        break
                    else:
                        lastch_was_whitespace = False
                    i += 1
                # Move back to last valid char
                i -= 1
            else:
                i = buf_length - 1
            if DEBUG:
                if i > pos:
                    print "Including chars from pos %d up to %d" % (pos, i)
                else:
                    print "No valid chars forward from pos %d, i now: %d" % (pos, i)

        # Be careful here, we cannot move from code into a comment, but we
        # can be in a comment to begin with.
        first_citdl_expr_style = None
        first_citdl_expr_style_is_comment = False
        while i >= 0:
            ch = accessor.char_at_pos(i)
            style = accessor.style_at_pos(i)
            if ch in WHITESPACE:
                # drop all whitespace
                while i >= 0:
                    ch = accessor.char_at_pos(i)
                    if ch in WHITESPACE \
                       or (ch == '\\' and accessor.char_at_pos(i+1) in EOL):
                        if DEBUG:
                            print "drop whitespace: %r" % accessor.char_at_pos(i)
                    else:
                        break
                    i -= 1
                # If there are two whitespace-separated words with no .
                # in between we're changing expressions:
                #   if foo<|> and ...
                #   def foo<|>(...
                if i >= 0 and citdl_expr and isident(citdl_expr[-1]) \
                   and ch != '.':
                    if DEBUG: 
                        print "stop at non-dot: %r" % ch
                    break
            elif style in string_styles: # Convert to string
                citdl_type = self.citdl_from_literal_type.get("string")
                if DEBUG:
                    print "found string style, converting to: %s and now " \
                          "finished" % (citdl_type)
                if citdl_type:
                    citdl_expr += reversed(citdl_type)
                break
            elif style in skip_styles: # drop styles to ignore
                while i >= 0 and accessor.style_at_pos(i) in skip_styles:
                    if DEBUG:
                        print "drop char of style to ignore: %r"\
                              % accessor.char_at_pos(i)
                    i -= 1
            elif ch in STOPOPS or (
                 # This check ensures that, for example, we get "foo" instead
                 # of "bar()foo" in the following:
                 #      bar()
                 #      foo<|>.
                 citdl_expr and citdl_expr[-1] != '.'
                 and ch in EXTRA_STOPOPS_PRECEDING_IDENT):
                if DEBUG:
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
                i -= 1
                num_lines = 0
                while i >= 0:
                    ch = accessor.char_at_pos(i)
                    style = accessor.style_at_pos(i)
                    if DEBUG:
                        print "finding matching brace: ch %r (%s), stack %r"\
                              % (ch, ', '.join(buf.style_names_from_style_num(style)), stack)
                    if ch in EOL:
                        num_lines += 1
                    if num_lines >= 3:
                        if DEBUG: print "stop search for matching brace at 3 line sentinel"
                        break
                    elif ch in BLOCKS and style not in skip_styles:
                        stack.append( (ch, style, BLOCKS[ch]) )
                    elif ch == stack[-1][2] and style not in skip_styles:
                        #XXX Replace the second test with the following
                        #    when LexPython+SilverCity styling bugs are fixed
                        #    (spurious 'stderr' problem):
                        #       and style == stack[-1][1]:
                        last_frame = stack.pop()
                        if not stack:
                            if DEBUG:
                                print "jump to matching brace at %d: %r" % (i, ch)
                            citdl_expr.append(ch)
                            if trg:
                                # save the text in params, in case the completion
                                # needs to special-case things depending on the
                                # argument.
                                trg.extra["_params"] = accessor.text_range(i + 1, last_frame[3])
                            i -= 1
                            break
                    i -= 1
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
                if first_citdl_expr_style is None:
                    # Remember the first citdl style we found
                    first_citdl_expr_style = style
                    first_citdl_expr_style_is_comment = style in comment_styles
                elif first_citdl_expr_style != style and \
                     (first_citdl_expr_style_is_comment or
                      style in comment_styles):
                    # We've moved into or out of a comment, let's leave now
                    # Fixes: http://bugs.activestate.com/show_bug.cgi?id=65672
                    break
                citdl_expr.append(ch)
                i -= 1

        citdl_expr.reverse()
        citdl_expr = ''.join(citdl_expr)
        if DEBUG:
            print "return: %r" % citdl_expr
            print banner("done")
        return citdl_expr

    def citdl_expr_from_trg(self, buf, trg):
        """Return a Python CITDL expression preceding the given trigger.
        
        The expression drops newlines, whitespace, and function call
        arguments -- basically any stuff that is not used by the codeintel
        database system for determining the resultant object type of the
        expression. For example (in which <|> represents the given position):
        
            GIVEN                       RETURN
            -----                       ------
            foo<|>.                     foo
            foo(bar<|>.                 bar
            foo(bar,blam)<|>.           foo()
            foo(bar,                    foo()
                blam)<|>.
            @foo<|>(                    foo

        If (trg.form == TRG_FORM_DEFN), then it's similar to above, except it
        looks forward to grab additional characters.

            GIVEN                       RETURN
            -----                       ------
            foo<|>.                     foo
            f<|>oo.bar                  foo.bar
            foo(bar<|>.                 bar
            foo(bar,blam)<|>.           foo()
            foo(bar,                    foo().bar
                blam).b<|>ar
        """
        DEBUG = False
        if DEBUG:
            print banner("Python-style citdl_expr_from_trg @ %d" % trg.pos)
        if trg.form == TRG_FORM_DEFN:
            pos = trg.pos
            expr = self._citdl_expr_from_pos(buf, pos, implicit=True, trg=trg,
                                             include_forwards=True, DEBUG=DEBUG)
            if expr:
                # Chop off any trailing "." characters
                return expr.rstrip(".")
            return expr
        else:
            if trg.type == 'array-members':
                # Get everything before the bracket position.
                pos = trg.extra.get('bracket_pos') - 1
            else:
                pos = trg.pos - 2   # skip ahead of the trigger char
            return self._citdl_expr_from_pos(buf, pos, implicit=trg.implicit,
                                             DEBUG=DEBUG, trg=trg)


#---- internal calltip parsing support

class Arg(object):
    def __init__(self):
        self.start = None
        self.end = None
        self.name_chs = []
        self.default_chs = []

    def done(self, p):
        self.end = p

    def append_ch(self, p, ch):
        if not self.name_chs:
            self.start = p
        self.name_chs.append(ch)

    def append_default_ch(self, p, ch):
        self.default_chs.append(ch)

    def __nonzero__(self):
        return operator.truth(self.name_chs)

    def __repr__(self):
        default_str = (self.default
                       and ', default=%r'%self.default
                       or '')
        return "Arg(%r, %s, %s%s)" \
               % (self.name, self.start, self.end, default_str)

    @property
    def name(self):
        return ''.join(self.name_chs)

    @property
    def default(self):
        if self.default_chs:
            return ''.join(self.default_chs)
        else:
            return None

    @property
    def span(self):
        return (self.start, self.end)

def _parse_calltip(calltip, DEBUG=False):
    r"""Parse the given calltip text as follows:

        >>> _parse_calltip('foo(a)\nblam')
        ('foo(a)', 'foo', [Arg('a', 4, 5)])
        >>> _parse_calltip('foo(a, b)')
        ('foo(a, b)', 'foo', [Arg('a', 4, 5), Arg('b', 7, 8)])
        >>> _parse_calltip('foo(a=42)')
        ('foo(a=42)', 'foo', [Arg('a', 4, 8, default='42')])
        >>> _parse_calltip('flash(boom, bang=42)')
        ('flash(boom, bang=42)', 'flash', [Arg('boom', 6, 10), Arg('bang', 12, 19, default='42')])

    Not currently doing anything magical for calltips like these:
        range([start,] stop[, step]) -> list of integers
    """
    signature = calltip.splitlines(0)[0]
    arg_start_pos = signature.find('(')
    if arg_start_pos == -1 or ')' not in signature:
        if DEBUG:
            print "no '(' and ')' in first line of calltip"
        return None
    name = calltip[:arg_start_pos].strip()

    #XXX Should add block skipping.
    #skip_blocks = {
    #    '"': '"',
    #    "'": "'",
    #    "/*": "*/",  # JavaScript comments
    #}

    length = len(signature)
    p = arg_start_pos + 1
    args = [Arg()]
    OPERATOR, ARGUMENT, DEFAULT = range(3)
    WHITESPACE = tuple(" \t[]")
    state = OPERATOR
    while p < length:
        ch = signature[p]
        if ch == ')':
            break # end of argument region
        elif state == OPERATOR:
            if ch in WHITESPACE:
                pass
            elif ch == ',':
                args[-1].done(p)
                args.append(Arg())
            else:
                state = ARGUMENT
                continue # do this char again
        elif state == ARGUMENT:
            if ch == ',':
                state = OPERATOR
                continue
            elif ch == '=':
                state = DEFAULT
            else:
                args[-1].append_ch(p, ch)
        elif state == DEFAULT:
            if ch == ',':
                state = OPERATOR
                continue
            else:
                args[-1].append_default_ch(p, ch)
        p += 1
    if not args[-1]:
        del args[-1]
    else:
        args[-1].done(p)
    return (signature, name, args)

