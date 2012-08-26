#!/usr/bin/env python
# Copyright (c) 2010 ActiveState Software Inc.
# See LICENSE.txt for license details.

"""HTML 5 support for CodeIntel"""

import logging

from codeintel2.common import _xpcom_
from codeintel2.lang_html import HTMLLexer, HTMLLangIntel, HTMLBuffer, HTMLCILEDriver

if _xpcom_:
    from xpcom.server import UnwrapObject


#---- globals

lang = "HTML5"
log = logging.getLogger("codeintel.html5")
#log.setLevel(logging.DEBUG)


#---- language support

class HTML5Lexer(HTMLLexer):
    # This must be defined as "HTML" in order to get autocompletion working.
    lang = "HTML"

class HTML5LangIntel(HTMLLangIntel):
    lang = lang

class HTML5Buffer(HTMLBuffer):
    lang = lang

    # Override the xml_default_dataset_info in order to change the DTD catalog
    # that gets used for HTML completions. The namespace is set through the
    # Komodo prefs system (defaultHTML5Decl and defaultHTML5DeclSystemIdentifier).
    def xml_default_dataset_info(self, node=None):
        if self._xml_default_dataset_info is None:
            import koXMLDatasetInfo
            datasetSvc = koXMLDatasetInfo.getService()
            self._xml_default_dataset_info = (datasetSvc.getDefaultPublicId(lang, self.env),
                                              None,
                                              datasetSvc.getDefaultNamespace(lang, self.env))
        return self._xml_default_dataset_info

class HTML5CILEDriver(HTMLCILEDriver):
    lang = lang


#---- registration

def register(mgr):
    """Register language support with the Manager."""
    mgr.set_lang_info(lang,
                      silvercity_lexer=HTML5Lexer(),
                      buf_class=HTML5Buffer,
                      langintel_class=HTML5LangIntel,
                      cile_driver_class=HTML5CILEDriver,
                      is_cpln_lang=True)

