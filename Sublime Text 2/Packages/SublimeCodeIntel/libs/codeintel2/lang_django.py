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

"""Django support for codeintel"""

import logging

from codeintel2.common import *
from codeintel2.langintel import LangIntel
from codeintel2.udl import UDLLexer, UDLBuffer, UDLCILEDriver, XMLParsingBufferMixin

if _xpcom_:
    from xpcom.server import UnwrapObject

#---- globals

lang = "Django"
log = logging.getLogger("codeintel.django")


django_keywords = [
    "and",
    "as",
    "by",
    "in",
    "not",
    "or",
]

django_tags = [
    "autoescape",
    "block",
    "comment",
    "csrf_token",
    "cycle",
    "debug",
    "else",
    "empty",   # used with for loop
    "extends",
    "filter",
    "firstof",
    "for",
    "if",
    "ifchanged",
    "ifequal",
    "ifnotequal",
    "include",
    "load",
    "now",
    "regroup",
    "spaceless",
    "ssi",
    "templatetag",
    "url",
    "widthratio",
    "with",
    
    # end tags
    "endautoescape",
    "endblock",
    "endcomment",
    "endfilter",
    "endfor",
    "endif",
    "endifchanged",
    "endifequal",
    "endifnotequal",
    "endspaceless",
    "endwith",
    
    # Escape keywords
    "openblock",
    "closeblock",
    "openvariable",
    "closevariable",
    "openbrace",
    "closebrace",
]

django_default_filter_names = [
    # These are default filter names in django
    "add",
    "addslashes",
    "capfirst",
    "center",
    "cut",
    "date",
    "default",
    "default_if_none",
    "dictsort",
    "dictsortreversed",
    "divisibleby",
    "escape",
    "escapejs",
    "filesizeformat",
    "first",
    "fix_ampersands",
    "floatformat",
    "get_digit",
    "iriencode",
    "join",
    "last",
    "length",
    "length_is",
    "linebreaks",
    "linebreaksbr",
    "linenumbers",
    "ljust",
    "lower",
    "make_list",
    "phone2numeric",
    "pluralize",
    "pprint",
    "random",
    "removetags",
    "rjust",
    "safe",
    "safeseq",
    "slice",
    "slugify",
    "stringformat",
    "striptags",
    "time",
    "timesince",
    "timeuntil",
    "title",
    "truncatewords",
    "truncatewords_html",
    "unordered_list",
    "upper",
    "urlencode",
    "urlize",
    "urlizetrunc",
    "wordcount",
    "wordwrap",
    "yesno",
]


#---- language support

class DjangoLexer(UDLLexer):
    lang = lang

class DjangoBuffer(UDLBuffer, XMLParsingBufferMixin):
    lang = lang
    tpl_lang = lang
    m_lang = "HTML"
    css_lang = "CSS"
    csl_lang = "JavaScript"
    ssl_lang = "Django"

    # Characters that should close an autocomplete UI:
    # - wanted for XML completion: ">'\" "
    # - wanted for CSS completion: " ('\";},.>"
    # - wanted for JS completion:  "~`!@#%^&*()-=+{}[]|\\;:'\",.<>?/ "
    # - dropping ':' because I think that may be a problem for XML tag
    #   completion with namespaces (not sure of that though)
    # - dropping '[' because need for "<!<|>" -> "<![CDATA[" cpln
    # - dropping '-' because causes problem with CSS (bug 78312)
    # - dropping '!' because causes problem with CSS "!important" (bug 78312)
    cpln_stop_chars = "'\" (;},~`@#%^&*()=+{}]|\\;,.<>?/"


class DjangoLangIntel(LangIntel):
    lang = lang

    # Used by ProgLangTriggerIntelMixin.preceding_trg_from_pos()
    trg_chars = tuple('| ')
    calltip_trg_chars = tuple()

    def trg_from_pos(self, buf, pos, implicit=True, DEBUG=False):
        """
            CODE       CONTEXT      RESULT
            '{<|>'     anywhere     tag names, i.e. {% if %}
            'foo|<|>'  filters      filter names, i.e. {{ foo|capfirst }}
        """
        #DEBUG = True # not using 'logging' system, because want to be fast
        if DEBUG:
            print "\n----- Django trg_from_pos(pos=%r, implicit=%r) -----"\
                  % (pos, implicit)

        if pos < 2:
            return None
        accessor = buf.accessor
        last_pos = pos - 1
        last_char = accessor.char_at_pos(last_pos)
        if DEBUG:
            print "  last_pos: %s" % last_pos
            print "  last_char: %r" % last_char
            print 'accessor.text_range(last_pos-2, last_pos): %r' % (accessor.text_range(last_pos-2, last_pos), )

        if last_char == " " and \
           accessor.text_range(last_pos-2, last_pos) == "{%":
            if DEBUG:
                print "  triggered: 'complete-tags'"
            return Trigger(lang, TRG_FORM_CPLN,
                           "complete-tags", pos, implicit)

        if last_char == "|":
            if DEBUG:
                print "  triggered: 'complete-filters'"
            return Trigger(lang, TRG_FORM_CPLN,
                           "complete-filters", pos, implicit)


    _djangotag_cplns =    [ ("element", t) for t in sorted(django_tags) ]
    _djangofilter_cplns = [ ("function", t) for t in sorted(django_default_filter_names) ]

    def async_eval_at_trg(self, buf, trg, ctlr):
        if _xpcom_:
            trg = UnwrapObject(trg)
            ctlr = UnwrapObject(ctlr)

        ctlr.start(buf, trg)

        # Django tag completions
        if trg.id == (lang, TRG_FORM_CPLN, "complete-tags"):
            ctlr.set_cplns(self._djangotag_cplns)
            ctlr.done("success")
            return
        if trg.id == (lang, TRG_FORM_CPLN, "complete-filters"):
            ctlr.set_cplns(self._djangofilter_cplns)
            ctlr.done("success")
            return

        ctlr.done("success")


class DjangoCILEDriver(UDLCILEDriver):
    lang = lang
    csl_lang = "JavaScript"
    tpl_lang = "Django"



#---- registration

def register(mgr):
    """Register language support with the Manager."""
    mgr.set_lang_info(lang,
                      silvercity_lexer=DjangoLexer(),
                      buf_class=DjangoBuffer,
                      langintel_class=DjangoLangIntel,
                      import_handler_class=None,
                      cile_driver_class=DjangoCILEDriver,
                      is_cpln_lang=True)

