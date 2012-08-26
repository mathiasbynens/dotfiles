#!/usr/bin/env python
# Copyright (c) 2008 ActiveState Software Inc.
# See LICENSE.txt for license details.

"""MXML support for codeintel"""

import logging

from codeintel2.common import *
from codeintel2.udl import UDLLexer, UDLBuffer, UDLCILEDriver, XMLParsingBufferMixin
import koXMLDatasetInfo

#---- globals

lang = "MXML"
log = logging.getLogger("codeintel.MXML")

#---- language support

class MXMLLexer(UDLLexer):
    lang = lang

class MXMLBuffer(UDLBuffer, XMLParsingBufferMixin):
    lang = lang
    m_lang = "XML"
    css_lang = "CSS"
    csl_lang = "JavaScript"

    cpln_stop_chars = ">'\" "

    def xml_parse(self):
        log.debug(">> MXMLBuffer.xml_parse")
        from koXMLTreeService import getService
        text = self.accessor.text.replace("<![CDATA[", "         ").replace("]]>", "   ")
        self._xml_tree_cache = getService().getTreeForURI(self.path, text)
    
    def _mxml_default_dataset_info(self, node):
        log.debug(">> MXMLBuffer._mxml_default_dataset_info")
        #print "%s node %r" % (buf.lang, node)
        tree = self.xml_tree
        parent = node
        while parent is not None:
            if parent.localName == "Content":
                if parent.attrib.get("type", "").startswith("html"):
                    datasetSvc = koXMLDatasetInfo.getService()
                    default_dataset_info = (
                        datasetSvc.getDefaultPublicId("HTML", self.env),
                        None,
                        datasetSvc.getDefaultNamespace("HTML", self.env)
                    )
                    return default_dataset_info
                break
            parent = tree.parent(parent)
        return None

    def xml_tree_handler(self, node=None):
        log.debug(">> MXMLBuffer.xml_tree_handler")
        default = self._mxml_default_dataset_info(node)
        if default:
            # force HTML based completion
            return koXMLDatasetInfo.getService().getDocumentHandler(default[0], default[1], default[2])
        return XMLParsingBufferMixin.xml_tree_handler(self, node)

# This gives global window completions but does not produce cile
# information, so completions for local variables and functions will
# not work.
class MXMLCILEDriver(UDLCILEDriver):
    lang = lang
    csl_lang = "JavaScript"

#---- registration

def register(mgr):
    """Register language support with the Manager."""
    log.debug(">> register MXML language support")
    mgr.set_lang_info(lang,
                      silvercity_lexer=MXMLLexer(),
                      buf_class=MXMLBuffer,
                      import_handler_class=None,
                      cile_driver_class=MXMLCILEDriver,
                      is_cpln_lang=True)
