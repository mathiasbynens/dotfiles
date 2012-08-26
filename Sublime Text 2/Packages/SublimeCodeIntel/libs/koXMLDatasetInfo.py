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

"""
koXMLDatasetInfo ties together the use of koXMLTreeService and
XML Catalog/DTD support in koCatalog to supply data handlers for determining
valid elements/attributes for the current position in the tree.

All tree arguments are cElementTree elements and should be the root element
of an XMLDocument from koXMLTreeService.

Note: most of this logic moved out of koXMLCompletionBase.py in order to
allow testing outside of Komodo.
"""

import sys
import os
import logging

import koXMLTreeService
from koCatalog import CatalogResolver


log = logging.getLogger("koXMLDatasetInfo")



class EmptyDatasetHandler:
    def tagnames(self, tree, node=None):
        if node is None:
            node = tree.current
        if node is not None:
            tags = tree.tags.get(tree.namespace(node), {})
        else:
            tags = tree.tags.get("", {})
        return [t for t in tags.keys() if t]

    def attrs(self, tree, node=None):
        if node is None:
            node = tree.current
        attrs = {}
        nodes = [n for n in tree.nodes if n.tag.lower() == node.tag.lower()]
        # now, get all attributes from all the tags
        for n in nodes:
            attrs.update(n.attrib)
        return attrs.keys()

    def values(self, attrname, tree, node=None):
        return []

class DataSetHandler(EmptyDatasetHandler):
    def __init__(self, namespace, dataset):
        self.namespace = namespace
        self.dataset = dataset

    def getnamespace(self, tree):
        """ if we were created without a namespace (eg. doctype only) then
            use the top level namespace for the document we're handling
            don't save the namespace, as it could change from document
            to document.  """
        if not self.namespace and tree.root is not None:
            return tree.root.ns
        return self.namespace

    def tagnames(self, tree, node=None):
        namespace = self.getnamespace(tree)
        if node is None:
            node = tree.current
        if node is None:
            # get root elements
            return self.dataset.possible_children()
        orig_node = node
        while node is not None:
            #print "node [%s] ns [%s]" % (node.localName, tree.namespace(node))
            ns = tree.namespace(node)
            if node.localName and (not ns or ns.lower()==namespace.lower()):
                if self.dataset.element_info(node.localName):
                    return self.dataset.possible_children(node.localName)
            node = tree.parent(node)
        if self.dataset.element_info(orig_node.localName):
            return self.dataset.possible_children(orig_node.localName)
        return self.dataset.all_element_types()

    def attrs(self, tree, node=None):
        if node is None:
            node = tree.current
        return self.dataset.possible_attributes(node.localName)

    def values(self, attrname, tree, node=None):
        if node is None:
            node = tree.current
        return self.dataset.\
               possible_attribute_values(node.localName, attrname)

class DatasetHandlerService:
    handlers = {} # empty dataset handlers
    resolver = None
    def __init__(self):
        self.defaultHandler = EmptyDatasetHandler()
        self.resolver = CatalogResolver()
        
    def setCatalogs(self, catalogs):
        self.resolver.resetCatalogs(catalogs)
        DatasetHandlerService.handlers = {}

    def getDefaultPublicId(self, lang, env):
        if lang == "HTML":
            return "-//W3C//DTD HTML 4.01//EN"
        return None

    def getDefaultNamespace(self, lang, env):
        return None

    def createDatasetHandler(self, publicId, systemId, namespace):
        dataset = self.resolver.getDataset(publicId, systemId, namespace)
        if not dataset:
            handler = EmptyDatasetHandler()
        else:
            handler = DataSetHandler(namespace, dataset)
        if namespace:
            self.handlers[namespace] = handler
        if publicId or systemId:
            self.handlers[(publicId, systemId)] = handler
                
        return handler

    def getDocumentHandler(self, publicId=None, systemId=None, namespace=None):
        if namespace:
            if namespace not in self.handlers:
                handler = self.createDatasetHandler(publicId, systemId, namespace)
            else:
                handler = self.handlers.get(namespace)
            if handler:
                return handler
        if publicId or systemId:
            key = (publicId, systemId)
            if key not in self.handlers:
                handler = self.createDatasetHandler(publicId, systemId, namespace)
            else:
                handler = self.handlers.get(key)
            if handler:
                return handler
        return EmptyDatasetHandler()




if "CODEINTEL_NO_PYXPCOM" in os.environ:
    _xpcom_ = False
else:
    try:
        from xpcom import components, _xpcom
        from xpcom.server import WrapObject, UnwrapObject
        from xpcom._xpcom import PROXY_SYNC, PROXY_ALWAYS, PROXY_ASYNC, getProxyForObject
        _xpcom_ = True
    except ImportError:
        _xpcom_ = False

if _xpcom_:
    PyDatasetHandlerService = DatasetHandlerService
    class XPCOMDatasetHandlerService(PyDatasetHandlerService):
        """koDatasetHandlerService
        subclass the dataset handler service so we can provide catalog paths
        from preferences
        """
        _com_interfaces_ = [components.interfaces.nsIObserver]
        def __init__(self):
            self._prefSvc = components.classes["@activestate.com/koPrefService;1"].\
                                    getService(components.interfaces.koIPrefService)
            self._prefsProxy = getProxyForObject(1,
                components.interfaces.koIPrefService, self._prefSvc,
                PROXY_ALWAYS | PROXY_SYNC)
            
            self._wrapped = WrapObject(self, components.interfaces.nsIObserver)
            self._prefSvc.prefs.prefObserverService.addObserver(self._wrapped,'xmlCatalogPaths',0);
            
            PyDatasetHandlerService.__init__(self)
            self.reset()

        def getDefaultPublicId(self, lang, env):
            return env.get_pref("default%sDecl" % lang)

        def getDefaultNamespace(self, lang, env):
            return env.get_pref("default%sNamespace" % lang)
        
        def reset(self):
            catalogs = self._prefsProxy.prefs.getStringPref("xmlCatalogPaths") or []
            if catalogs:
                catalogs = catalogs.split(os.pathsep)

            # get xml catalogs from extensions
            from directoryServiceUtils import getExtensionDirectories
            for dir in getExtensionDirectories():
                candidates = [
                    # The new, cleaner, location.
                    os.path.join(dir, "xmlcatalogs", "catalog.xml"),
                    # The old location (for compat). This is DEPRECATED
                    # and should be removed in a future Komodo version.
                    os.path.join(dir, "catalog.xml"),
                ]
                for candidate in candidates:
                    if os.path.exists(candidate):
                        catalogs.append(candidate)
                        break

            # add our default catalog file
            koDirs = components.classes["@activestate.com/koDirs;1"].\
              getService(components.interfaces.koIDirs)
            catalogs.append(os.path.join(str(koDirs.supportDir), "catalogs", "catalog.xml"))
            self.setCatalogs(catalogs)
    
        def observe(self, subject, topic, data):
            # watch for changes to XMLCatalogPaths and update our resolver with
            # new catalogs
            if topic == "xmlCatalogPaths":
                self.reset()
        
    DatasetHandlerService = XPCOMDatasetHandlerService

__datasetSvc = None
def getService():
    global __datasetSvc
    if not __datasetSvc:
        __datasetSvc = DatasetHandlerService()
    return __datasetSvc

def get_tree_handler(tree, node=None, default=None):
    # if we have a namespace, use it,  otherwise, fallback to the doctype
    namespace = None
    if node is None:
        node = tree.root
    if node is not None:
        namespace = tree.namespace(node)
    log.info("getting handler for (%s,%s,%s)"%(tree.publicId, tree.systemId, namespace))
    #print "getDocumentHandler (%s,%s,%s)"%(tree.publicId, tree.systemId, namespace)
    publicId = tree.publicId
    systemId = tree.systemId
    if not (publicId or systemId or namespace) and default:
        #print "using defaults %r" % (default,)
        publicId = default[0]
        systemId = default[1]
        namespace = default[2]
    return getService().getDocumentHandler(publicId, systemId, namespace)
    
if __name__ == "__main__":
    import sys, os
    # basic logging configuration
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

    # utility functions for testing, these are *SIMILAR* to codeintel lang_xml
    default_completion = { 'HTML': ('-//W3C//DTD XHTML 1.0 Strict//EN',
                              'http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd',
                              'http://www.w3.org/1999/xhtml') }
    
    def getDefaultCompletion(tree, node, lang):
        if lang=="XSLT":
            if node is not None and not tree.namespace(node):
                # do we have an output element, if so, figure out if we're html
                # cheap way to get the output element
                output = tree.tags.get('http://www.w3.org/1999/XSL/Transform', []).get('output')
                if output is not None:
                    lang = output.attrib.get('method').upper()
                    publicId = output.attrib.get('doctype-public')
                    systemId = output.attrib.get('doctype-system')
                    default_dataset_info = default_completion.get(lang)
                    if publicId or systemId:
                        default_dataset_info = (publicId, systemId, default_dataset_info[2])
                return default_dataset_info
            return None
        return default_completion.get(lang)
      
    def getValidTagNames(text, uri=None, lang=None):
        """getValidTagNames
        return a list of valid element names that can be inserted at the end
        of the text segment
        """
        tree = koXMLTreeService.getService().getTreeForURI(uri, text)
        default_dataset_info = getDefaultCompletion(tree, tree.current, lang)
        handlerclass = get_tree_handler(tree, tree.current, default_dataset_info)
        tagnames = handlerclass.tagnames(tree)
        if not tagnames:
            return None
        tagnames.sort()
        return tagnames
    
    def getOpenTagName(text, uri=None):
        """getOpenTagName
        return the current tag name
        """
        tree = koXMLTreeService.getService().getTreeForURI(uri, text)
        if tree.current is None: return None
        return tree.tagname(tree.current)
    
    def getValidAttributes(text, uri=None, lang=None):
        """getValidAttributes
        get the current tag, and return the attributes that are allowed in that
        element
        """
        tree = koXMLTreeService.getService().getTreeForURI(uri, text)
        if tree.current is None: return None
        already_supplied = tree.current.attrib.keys()
        handlerclass = get_tree_handler(tree, tree.current, default_completion.get(lang))
        attrs = handlerclass.attrs(tree)
        if not attrs:
            return None
        attrs = [name for name in attrs if name not in already_supplied]
        attrs.sort()
        return attrs
    
    def getValidAttributeValues(text, attr, uri=None, lang=None):
        """getValidAttributeValues
        get the current attribute, and return the values that are allowed in that
        attribute
        """
        tree = koXMLTreeService.getService().getTreeForURI(uri, text)
        if tree.current is None: return None
        handlerclass = get_tree_handler(tree, tree.current, default_completion.get(lang))
        values = handlerclass.values(attr, tree)
        if not values:
            return None
        values.sort()
        return values

    # configure catalogs to use
    basedir = os.path.dirname(os.path.dirname(os.getcwd()))
    catalogs = os.path.join(basedir, "test", "stuff", "xml")
    getService().setCatalogs([os.path.join(catalogs, "testcat.xml")])

    from ciElementTree import Element
    tree = koXMLTreeService.XMLDocument()
    tree.root = tree.current = Element('')
    handlerclass = get_tree_handler(tree, tree.current)
    assert handlerclass != None, "no handler class for empty tree"

    xml = """<?xml version="1.0"?> 
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="html" indent="yes"/>
  <html> <
"""
    tags = getValidTagNames(xml, lang="XSLT")
    assert tags == ['body', 'head'], \
                "invalid output tags for stylesheet"

    xml = "<"
    assert getValidTagNames(xml) == None, "invalid children for html"

    xml = """<html>
    <body>
        <scr"""
    assert "script" in getValidTagNames(xml, lang="HTML"), "invalid children for body"

    html = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">"""
    # XXX this should only be html, have to figure out why area is there.
    tags = getValidTagNames(html)
    assert tags == ["html"], "invalid children for doc root"

    xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE window PUBLIC "-//MOZILLA//DTD XUL V1.0//EN" "http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul">
<window xmlns="http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul">
    <popupset id="editorTooltipSet">
        <popup type="tooltip" id="editorTooltip" flex="1">
            <description multiline="true" id="editorTooltip-tooltipText" class="tooltip-label" flex="1"/>
        </popup><
        <popup type="autocomplete" id="popupTextboxAutoComplete"/>
    </popupset>

"""
    tags = getValidTagNames(xml) 
    assert tags == ["popup"], "invalid children for popupset %r" % tags

    xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
"""
    # lets get the next valid element
    assert getValidTagNames(xml) == ['body', 'head'], "invalid children for html tag"

    xml ="""<
    
<?php
?>
"""
    tags = getValidTagNames(xml, lang="HTML")
    assert tags == ['html'], "invalid attributes for html tag"

    xml = """<html """
    attrs = getValidAttributes(xml, lang="HTML")
    assert attrs == ['dir', 'id', 'lang'], "invalid attributes for html tag"
    
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html """
    attrs = getValidAttributes(xml)
    assert attrs == ['dir', 'id', 'lang'], "invalid attributes for html tag"

    xml = """<?xml version="1.0"?> 
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="xml" indent="yes"/>
  <xsl:
  
  <xsl:template/>
"""
    assert getValidTagNames(xml) == ['attribute-set', 'decimal-format', 'import', 'include', 'key', 'namespace-alias', 'output', 'param', 'preserve-space', 'strip-space', 'template', 'variable'], \
                "invalid children tags for stylesheet"

    xml = """<?xml version="1.0"?> 
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="xml" indent="yes"/>
  <xsl:template"""
    assert getValidAttributes(xml) == ['match', 'mode', 'name', 'priority'], \
                "invalid attributes for template"

    xml = """<?xml version="1.0"?> 
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="xml" indent="yes"/>
  <xsl:"""
    assert getValidTagNames(xml) == ['attribute-set', 'decimal-format', 'import', 'include', 'key', 'namespace-alias', 'output', 'param', 'preserve-space', 'strip-space', 'template', 'variable'], \
                "invalid children for stylesheet"

    # test getting custom tags from the default namespace
    xml = """<?xml version="1.0"?> 
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="xml" indent="yes"/>
  <mycustomtag>
  <
  
  <xsl:template/>
"""
    assert getValidTagNames(xml) == ['mycustomtag'], \
                "invalid children for mycustomtag"

    xml = """<?xml version="1.0"?> 
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="xml" indent="yes"/><xsl:
  <xsl:template/>
</xsl:stylesheet>
"""
    assert getValidTagNames(xml) == ['attribute-set', 'decimal-format', 'import', 'include', 'key', 'namespace-alias', 'output', 'param', 'preserve-space', 'strip-space', 'template', 'variable'], \
                "invalid children for stylesheet"

    xml = """<?xml version="1.0"?> 
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="xml" indent="yes"/>

  <xsl:template>
  </xsl:template><xsl:

  <xsl:template>
  </xsl:template>
</xsl:stylesheet>
"""
    assert getValidTagNames(xml) == ['attribute-set', 'decimal-format', 'import', 'include', 'key', 'namespace-alias', 'output', 'param', 'preserve-space', 'strip-space', 'template', 'variable'], \
                "invalid children for stylesheet"

