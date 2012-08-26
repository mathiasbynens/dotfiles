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

import logging
from codeintel2.common import *
from codeintel2.udl import UDLLexer, UDLBuffer, UDLCILEDriver, XMLParsingBufferMixin
from koXMLDatasetInfo import getService

#---- globals

lang = "XSLT"
log = logging.getLogger("codeintel.xslt")

class XSLTLexer(UDLLexer):
    lang = lang

class XSLTBuffer(UDLBuffer, XMLParsingBufferMixin):
    lang = lang
    m_lang = "XML"

    # Characters that should close an autocomplete UI:
    # - wanted for XML completion: ">'\" "
    cpln_stop_chars = ">'\" "

    def xml_default_dataset_info(self, node):
        #print "%s:%s node %r" % (self.lang, trg.lang, node)
        tree = self.xml_tree
        if node is not None and not tree.namespace(node):
            # Do we have an output element, if so, figure out if we're html.
            # Cheap way to get the output element.
            output = tree.tags.get(tree.namespace(tree.root), {}).get('output', None)
            if output is not None:
                lang = output.attrib.get('method').upper()
                publicId = output.attrib.get('doctype-public')
                systemId = output.attrib.get('doctype-system')
                if publicId or systemId:
                    default_dataset_info = (publicId, systemId, None)
                else:
                    datasetSvc = getService()
                    default_dataset_info = (
                        datasetSvc.getDefaultPublicId(lang, self.env),
                        None,
                        datasetSvc.getDefaultNamespace(lang, self.env)
                    )
                #print "get output type %r" % (default_dataset_info,)
                return default_dataset_info
        return XMLParsingBufferMixin.xml_default_dataset_info(self, node)

#---- registration

def register(mgr):
    """Register language support with the Manager."""
    mgr.set_lang_info(lang,
                      silvercity_lexer=XSLTLexer(),
                      buf_class=XSLTBuffer,
                      import_handler_class=None,
                      cile_driver_class=None,
                      is_cpln_lang=True)

