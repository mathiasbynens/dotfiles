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

"""XML support for CodeIntel"""

import os
from os.path import isfile, isdir, exists, dirname, abspath, splitext, join
import sys
from cStringIO import StringIO
import logging
import re
import traceback
from pprint import pprint

from codeintel2.common import *
from codeintel2.citadel import CitadelBuffer, CitadelEvaluator
from codeintel2.langintel import LangIntel
from codeintel2.udl import UDLBuffer, UDLLexer, XMLParsingBufferMixin

import koXMLTreeService, koXMLDatasetInfo
from koXMLDatasetInfo import getService

from SilverCity.ScintillaConstants import (SCE_UDL_M_STAGO, SCE_UDL_M_DEFAULT,
                                           SCE_UDL_M_ETAGO, SCE_UDL_M_TAGNAME,
                                           SCE_UDL_M_ATTRNAME, SCE_UDL_M_TAGSPACE,
                                           SCE_UDL_M_STRING,
                                           SCE_UDL_M_PI,
                                           SCE_XML_DEFAULT,
                                           SCE_XML_START_TAG_NAME,
                                           SCE_XML_START_TAG_ATTR_NAME,
                                           SCE_XML_START_TAG_OPEN,
                                           SCE_XML_START_TAG_CLOSE,
                                           SCE_XML_START_TAG_WHITE_SPACE,
                                           SCE_XML_START_TAG_ATTR_QUOT_OPEN,
                                           SCE_XML_START_TAG_ATTR_APOS_OPEN,
                                           SCE_XML_START_TAG_ATTR_QUOT_CLOSE,
                                           SCE_XML_START_TAG_ATTR_APOS_CLOSE,
                                           SCE_XML_START_TAG_ATTR_EQUALS,
                                           SCE_XML_END_TAG_OPEN,
                                           SCE_XML_END_TAG_NAME,
                                           SCE_XML_END_TAG_CLOSE,
                                           SCE_XML_DATA_CHARS,
                                           SCE_XML_DATA_NEWLINE,
                                           SCE_XML_START_TAG_ATTR_APOS_CONTENT,
                                           SCE_XML_START_TAG_ATTR_QUOT_CONTENT,
                                           SCE_XML_PI_OPEN,
                                           )


if _xpcom_:
    from xpcom import components, _xpcom
    from xpcom.server import WrapObject, UnwrapObject
    from xpcom._xpcom import PROXY_SYNC, PROXY_ALWAYS, PROXY_ASYNC



#---- globals

lang = "XML"
log = logging.getLogger("codeintel.xml")

STYLE_DEFAULT = 0
STYLE_START_TAG = 1
STYLE_END_TAG = 2
STYLE_TAG_NAME = 3
STYLE_ATTR_NAME = 4
STYLE_TAG_SPACE = 5
STYLE_STRING = 6
STYLE_PI_OPEN = 7
udl_styles = {
    STYLE_DEFAULT: (SCE_UDL_M_DEFAULT,),
    STYLE_START_TAG: SCE_UDL_M_STAGO,
    STYLE_END_TAG: SCE_UDL_M_ETAGO,
    STYLE_TAG_NAME: SCE_UDL_M_TAGNAME,
    STYLE_ATTR_NAME: SCE_UDL_M_ATTRNAME,
    STYLE_TAG_SPACE: SCE_UDL_M_TAGSPACE,
    STYLE_STRING: (SCE_UDL_M_STRING,),
    STYLE_PI_OPEN : SCE_UDL_M_PI,
}
# XXX FIXME for Lex_XML
pure_styles = {
    STYLE_DEFAULT: (SCE_XML_DEFAULT, SCE_XML_DATA_CHARS, SCE_XML_DATA_NEWLINE),
    STYLE_START_TAG: SCE_XML_START_TAG_OPEN,
    STYLE_END_TAG: SCE_XML_END_TAG_OPEN,
    STYLE_TAG_NAME: SCE_XML_START_TAG_NAME,
    STYLE_ATTR_NAME: SCE_XML_START_TAG_ATTR_NAME,
    STYLE_TAG_SPACE: SCE_XML_START_TAG_WHITE_SPACE,
    STYLE_STRING: (SCE_XML_START_TAG_ATTR_QUOT_OPEN,
                   SCE_XML_START_TAG_ATTR_APOS_OPEN,
                   SCE_XML_START_TAG_ATTR_APOS_CONTENT,
                   SCE_XML_START_TAG_ATTR_QUOT_CONTENT,
                  ),
    STYLE_PI_OPEN : SCE_XML_PI_OPEN,
}
common_namespace_cplns = [('namespace', x) for x in (
    'atom="http://purl.org/atom/ns#"',
    'blogChannel="http://backend.userland.com/blogChannelModule"',
    'dc="http://purl.org/dc/elements/1.1/"',
    'mml="http://www.w3.org/1998/Math/MathML"',
    'rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"',
    'rss="http://purl.org/rss/1.0/"',
    'xhtml="http://www.w3.org/TR/xhtml1/strict"',
    'xsd="http://www.w3.org/2000/10/XMLSchema"',
    'xsi="http://www.w3.org/2000/10/XMLSchema-instance"',
    'xs="http://schemas.xmlsoap.org/soap/envelope/"',
    'xsl="http://www.w3.org/1999/XSL/Transform"',
)]

trg_chars = tuple('<: "\'/!')


#---- language support

class XMLLexer(UDLLexer):
    lang = lang

class XMLLangIntel(LangIntel):
    lang = lang
    def trg_from_pos(self, buf, pos, implicit=True, DEBUG=False):
        """XML trigger types:
    
        xml-complete-tags-and-namespaces    <|
        xml-complete-ns-tags                <x:|  
        xml-complete-tag-attrs              <x:foo |
        xml-complete-ns-tag-attrs           <x:foo y:|
        xml-complete-attr-enum-values       <x:foo y:bar="|
        xml-complete-end-tag                <x ...>...</|
        xml-complete-well-known-ns          <x xmlns:|
        xml-gt-bang                         <!|
        
        Not yet implemented:
            xml-complete-well-known-ns-value    <x xmlns:x="|
            xml-complete-prolog                 <?xml |
            xml-complete-doctype                <!DOCTYPE |
        """
        #XXX Eventually we'll use UDL for pure XML too, so won't need
        #    this check.
        if isinstance(buf, UDLBuffer):
            styles = udl_styles
        else:
            styles = pure_styles

        if DEBUG:
            print "\n----- UDL %s trg_from_pos(pos=%r, implicit=%r) -----"\
                  % (self.lang, pos, implicit)
    
        if pos == 0:
            return None
        accessor = buf.accessor
        buf_length = accessor.length()
        last_pos = pos - 1
        last_char = accessor.char_at_pos(last_pos)
        last_style = accessor.style_at_pos(last_pos)
        if DEBUG:
            print "  last_pos: %s" % last_pos
            print "  last_char: %r" % last_char
            print "  last_style: %r %s" \
                  % (last_style, buf.style_names_from_style_num(last_style))
            #for i in xrange(pos):
                #print "style at pos %d (%c) : %d" % (i,
                #   accessor.char_at_pos(i), accessor.style_at_pos(i))
    
        if last_char == '<' and \
           last_style in styles[STYLE_DEFAULT] or last_style == styles[STYLE_START_TAG]:
            return Trigger(self.lang, TRG_FORM_CPLN, "tags-and-namespaces",
                           pos, implicit)
    
        elif last_char == '/' and last_style == styles[STYLE_END_TAG]:
            return Trigger(self.lang, TRG_FORM_CPLN, "end-tag",
                           pos, implicit)
    
        elif last_char == ':':
            # x:|`` **** xml-complete-ns-tags
            # **** list valid tags in given namespace
            if last_style in (styles[STYLE_TAG_NAME], styles[STYLE_ATTR_NAME]):
                current_word = accessor.text_range(
                    *accessor.contiguous_style_range_from_pos(last_pos))
                # Make sure it's the first ":" in the sequence
                if current_word.count(":") != 1:
                    return None
                if current_word == "xmlns:" \
                   and last_style == styles[STYLE_ATTR_NAME]:
                    return Trigger(self.lang, TRG_FORM_CPLN, "well-known-ns",
                                   pos, implicit)
                if last_style == styles[STYLE_TAG_NAME]:
                    return Trigger(self.lang, TRG_FORM_CPLN,
                                   "ns-tags", pos, implicit)
                else:
                    return Trigger(self.lang, TRG_FORM_CPLN,
                                   "ns-tags-attrs", pos, implicit)
    
        elif last_char == "!" and pos >= 2:
            last_last_char = accessor.char_at_pos(pos-2)
            last_last_style = accessor.style_at_pos(pos-2)
            if last_last_char == '<' and last_last_style in styles[STYLE_DEFAULT]:
                return Trigger(self.lang, TRG_FORM_CPLN, "gt-bang",
                               pos, implicit)
    
        elif last_char in (' ', '\t', '\n') \
             and last_style == styles[STYLE_TAG_SPACE]:
            # See bug 65200 for reason for this check.
            have_trg = False
            while last_pos > 0:
                last_pos -= 1
                last_style = accessor.style_at_pos(last_pos)
                if last_style in (styles[STYLE_TAG_SPACE],
                                  styles[STYLE_DEFAULT]):
                    pass
                elif last_style in styles[STYLE_STRING]:
                    have_trg = True
                    break
                elif last_style == styles[STYLE_TAG_NAME]:
                    # Now move back looking for an STAGO, so we don't
                    # trigger on a space after an end-tag
                    while last_pos > 0:
                        last_pos -= 1
                        last_style = accessor.style_at_pos(last_pos)
                        if last_style == styles[STYLE_TAG_NAME]:
                            # <.... foo="val" <|>
                            pass
                        elif last_style == styles[STYLE_START_TAG]:
                            # <foo <|>
                            have_trg = True
                            break
                        else:
                            # </foo <|>
                            break
                    break
                else:
                    return None
            if have_trg:
                return Trigger(self.lang, TRG_FORM_CPLN, "tag-attrs",
                               pos, implicit)
            else:
                return None
                
    
        elif last_char in ('\'', '"') and last_style in styles[STYLE_STRING] \
             and pos >= 5:
            # Look back to determine if we're in an <<xmlns:pfx = >> situation
            prev_style = accessor.style_at_pos(pos - 2)
            if prev_style == last_style:
                # It's the end of the string, not the beginning
                return None
            else:
                return Trigger(self.lang, TRG_FORM_CPLN, "attr-enum-values",
                               pos, implicit)
        return None


    def preceding_trg_from_pos(self, buf, pos, curr_pos, DEBUG=False):
        #XXX Eventually we'll use UDL for pure HTML too, so won't need
        #    this check.
        if isinstance(buf, UDLBuffer):
            styles = udl_styles
        else:
            styles = pure_styles

        accessor = buf.accessor
        #print "pos:", pos, ", curr_pos:", curr_pos
        for char, style in accessor.gen_char_and_style_back(pos-1, max(-1,pos-50)):
            #print "Style: %d char %s"% (style, char)
            if char == ":" and style in (styles[STYLE_TAG_NAME], styles[STYLE_ATTR_NAME]) or \
               char in ["<","!"] and style in styles[STYLE_DEFAULT] or style == styles[STYLE_START_TAG] or \
               char in (' ', '\t', '\n') and style == styles[STYLE_TAG_SPACE] or \
               char in ('\'', '"') and style in styles[STYLE_STRING] or \
               char == '/' and style == styles[STYLE_END_TAG]:
                return self.trg_from_pos(buf, pos, implicit=False, DEBUG=DEBUG)
            pos -= 1
        return None
    
    def async_eval_at_trg(self, buf, trg, ctlr):
        if _xpcom_:
            if hasattr(trg, "_comobj_"):
                trg = UnwrapObject(trg)
            if hasattr(ctlr, "_comobj_"):
                ctlr = UnwrapObject(ctlr)

        cplns = None
        ctlr.start(buf, trg)
        type = trg.type
        if type == "tags-and-namespaces":
            # extract tag hierarchy context -> context
            # pass context to schema-based-evaluator -> completions
            cplns = self.cpln_start_tag(buf, trg, True)
        elif type == "gt-bang":
            cplns = [
                ('doctype', 'DOCTYPE'),
                ('cdata', '[CDATA['),
                ('comment', '--'),
            ]
        elif type == "end-tag":
            cplns = self.cpln_end_tag(buf, trg)
        elif type == "well-known-ns":
            # this is a hack, we should get this from the catalog, but
            # prefix names are *not* standardized.
            cplns = common_namespace_cplns
        elif type == "well-known-ns-uri":
            # we get all uri's known to our catalog system
            uris = getService().resolver.getWellKnownNamspaces()
            cplns = [('namespace', x) for x in uris]
        elif type == "ns-tags":
            plns = self.cpln_start_tag(buf, trg, False)
        elif type == "ns-tags-attrs":
            cplns = self.cpln_start_attrribute(buf, trg)
        elif type == "tag-attrs":
            cplns = self.cpln_start_attrribute(buf, trg)
        elif type == "attr-enum-values":
            cplns = self.cpln_start_attribute_value(buf, trg)
        else:
            ctlr.error("unknown UDL-based XML completion: %r" % (id,))
            ctlr.done("error")
            return
        if cplns:
            ctlr.set_cplns(cplns)
        ctlr.done("success")


    def get_valid_tagnames(self, buf, pos, withPrefix=False):
        node = buf.xml_node_at_pos(pos)
        #print "get_valid_tagnames NODE %s:%s xmlns[%s] %r"%(buf.xml_tree.prefix(node),node.localName,node.ns,node.tag)
        handlerclass = buf.xml_tree_handler(node)
        tagnames = handlerclass.tagnames(buf.xml_tree, node)
        if not tagnames:
            return None
        tagnames = list(tagnames)
        tagnames.sort()
        if withPrefix and node is not None:
            prefix = buf.xml_tree.prefix(node)
            if prefix:
                return ["%s:%s" % (prefix, name) for name in tagnames]
        return tagnames
    
    def get_valid_attributes(self, buf, pos):
        """get_valid_attributes
        get the current tag, and return the attributes that are allowed in that
        element
        """
        node = buf.xml_node_at_pos(pos)
        if node is None: return None
        #print "get_valid_attributes NODE %s:%s xmlns[%s] %r"%(tree.prefix(node),node.localName,node.ns,node.tag)
        already_supplied = node.attrib.keys()
        handlerclass = buf.xml_tree_handler(node)
        attrs = handlerclass.attrs(buf.xml_tree, node)
        if not attrs:
            return None
        attrs = [name for name in attrs if name not in already_supplied]
        attrs.sort()
        return attrs
    
    def get_valid_attribute_values(self, attr, buf, pos):
        """get_valid_attribute_values
        get the current attribute, and return the values that are allowed in that
        attribute
        """
        node = buf.xml_node_at_pos(pos)
        if node is None: return None
        handlerclass = buf.xml_tree_handler(node)
        values = handlerclass.values(attr, buf.xml_tree, node)
        if not values:
            return None
        values.sort()
        return values
    
    
    def cpln_start_tag(self, buf, trg, withPrefix=True):
        lastpos = trg.pos
        if withPrefix:
            accessor = buf.accessor
            lastpos = accessor.text.rfind("<", 0, trg.pos)
            lastpos = max(lastpos, 0)
        tagnames = self.get_valid_tagnames(buf, lastpos, withPrefix=withPrefix)
        if not tagnames:
            return []
        return [('element', tag) for tag in tagnames]
    
    def cpln_end_tag(self, buf, trg):
        node = buf.xml_node_at_pos(trg.pos)
        if node is None: return None
        tagName = buf.xml_tree.tagname(node)
        if not tagName:
            return []
        return [('element',tagName+">")]    
    
    def cpln_start_attribute_value(self, buf, trg):
        accessor = buf.accessor
        attrName = accessor.text_range(*accessor.contiguous_style_range_from_pos(trg.pos-3))
        if not attrName:
            log.warn("no attribute name in cpln_start_attribute_value")
            return []
    
        values = self.get_valid_attribute_values(attrName, buf, trg.pos)
        if not values:
            return []
    
        return [('attribute_value', value) for value in values]
    
    def cpln_start_attrribute(self, buf, trg):
        accessor = buf.accessor
        attrs = self.get_valid_attributes(buf, trg.pos)
        if not attrs:
            return []
        attrName = accessor.text_range(*accessor.contiguous_style_range_from_pos(trg.pos-1))
        if attrName:
            attrName = attrName.strip()
        if attrName:
            return [('attribute', attr+"=") for attr in attrs if attr.startswith(attrName)]
        return [('attribute', attr+"=") for attr in attrs]
    

class XMLBuffer(UDLBuffer, XMLParsingBufferMixin):
    lang = lang
    m_lang = "XML"

    # Characters that should close an autocomplete UI:
    # - wanted for XML completion: ">'\" "
    # - dropping '[' because need for "<!<|>" -> "<![CDATA[" cpln
    # - Removed '#' - gets in the way of hex colors and id selectors (bug 82968)
    cpln_stop_chars = "'\" (;},~`!@%^&*()-=+{}]|\\;,.<>?/"



#---- registration

def register(mgr):
    """Register language support with the Manager."""
    mgr.set_lang_info(lang,
                      silvercity_lexer=XMLLexer(),
                      buf_class=XMLBuffer,
                      langintel_class=XMLLangIntel,
                      import_handler_class=None,
                      cile_driver_class=None,
                      is_cpln_lang=True)

