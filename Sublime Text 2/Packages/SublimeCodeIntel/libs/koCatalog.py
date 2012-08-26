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

import os
import logging
import re
from koSimpleLexer import *
from koDTD import DTD
from koRNGElementTree import rng

log = logging.getLogger("koCatalog")
#log.setLevel(logging.INFO)

from elementtree import XMLTreeBuilder
try:
    import ciElementTree as ElementTree # effbot's C module
except ImportError:
    log.error("using element tree and not cElementTree, performace will suffer")
    import elementtree.ElementTree as ElementTree # effbot's pure Python module

"""
NOTES:

SGML Catalog URI's
http://www.jclark.com/sp/catalog.htm
http://www.oasis-open.org/specs/tr9401.html (OFFICIAL SPEC)
http://www.oasis-open.org/committees/entity/spec.html (XML CATALOG)

For SGML Catalogs, we want to look at the env var SGML_CATALOG_FILES (see
jclark.com above)

"""

# regular expressions used for DTD parsing
collector = recollector()
a = collector.add

# regular expressions used for SGML Catalog parsing
a("whitespace" ,    r"\s+", re.S|re.M)
a("QuotedString" ,  r'(?:")([^"]*?)(?:")|(?:\')([^\']*?)(?:\')', re.S|re.U)
a("single_types", "(OVERRIDE|SGMLDECL|DOCUMENT|CATALOG|BASE)")
a("single",        r'(?P<type>%(single_types)s)\s+(?P<data1>%(QuotedString)s|\S+)', re.S)
a("double_types", "(PUBLIC|ENTITY|DOCTYPE|LINKTYPE|NOTATION|SYSTEM|DELEGATE)")
a("double",        r'(?P<type>%(double_types)s)\s+(?P<data1>%(QuotedString)s|\S+)\s+(?P<data2>%(QuotedString)s|\S+)', re.S)
a("COMMENT" ,       r"<!--(?P<comment>.*?)-->", re.S|re.M)
a("newlines" ,                   "[ \t]*(\r\n|\r|\n)")

def _cmpLen(a, b):
    al = len(a)
    bl = len(b)
    if al>bl: return -1
    if al==bl: return cmp(a, b)
    return 1

def strip_quotes(str):
    if not str:
        return None
    if str[0] in ["'",'"']:
        return str[1:-1]
    return str


# XXX a cheap relativize
urimatch = re.compile("(\w+://.*|/.*|\w:\\.*|\w:/.*)")
def relativize(base, fn):
    if urimatch.match(fn):
        return fn
    return os.path.join(base, fn)

class Delegate:
    def __init__(self, catalog=None, node=None):
        self.catalog = catalog
        self.node = node
        if node and not catalog:
            self.catalog = node.attrib.get('catalog')

class PublicID:
    def __init__(self, id=None, uri=None, node=None):
        self.id = id
        self.uri = uri
        self.node = node

class SystemID:
    def __init__(self, id=None, uri=None, node=None):
        self.id = id
        self.uri = uri
        self.node = node

class URI:
    def __init__(self, name=None, uri=None, node=None):
        self.name = name
        self.uri = uri
        self.node = node

class Catalog:
    # subclass and implement the parser to fill in the necessary
    # data elements
    def __init__(self, uri, resolver=None):
        self.uri = uri
        self.dir = os.path.dirname(uri)
        
        self.prefer = None

        # XMLCatalog
        self.public = {}
        self.system = {}
        self.rewritesystem = {}
        self.delegatepublic = {}
        self.delegatesystem = {}
        self.urimap = {}
        self.rewriteuri = {}
        self.delegateuri = {}
        self.nextcatalog = []
        
        # TR-9401 support
        self.doctype = {}
        self.document = {}
        self.dtddecl = {}
        self.entity = {}
        self.linktype = {}
        self.notation = {}
        self.sgmldecl = {}

        self.resolver = resolver
        self.parse()

    # Support functions for matching data to a catalog
    def _longestMatch(self, needle, haystack):
        haystack.sort(_cmpLen)
        for straw in haystack:
            if needle.find(straw) == 0:
                return straw
        return None
    
    def _getRewrite(self, id, ar):
        possible = self._longestMatch(id, ar.keys())
        if possible:
            return "%s%s" % (ar[possible],id[len(possible):])
        return None

    def _getDelegates(self, id, delegates):
        if id not in delegates:
            return None
        entries = delegates[id].keys().sort(_cmpLen)
        return [delegates[id][d].catalog for d in entries]

    def getSystemRewrite(self, systemId):
        return self._getRewrite(systemId, self.rewritesystem)

    def getURIRewrite(self, uri):
        return self._getRewrite(uri, self.rewriteuri)

    def getSystemDelegates(self, systemId):
        # 7.1.2 #4
        return self._getDelegates(systemId, self.delegatesystem)

    def getPublicDelegates(self, publicId):
        # 7.1.2 #6 
        return self._getDelegates(publicId, self.delegatepublic)

    def getURIDelegates(self, uri):
        # 7.1.2 #6 
        return self._getDelegates(uri, self.delegateuri)

class NamespaceParser(XMLTreeBuilder.FancyTreeBuilder):
    _qname = re.compile("{(.*?)}(.*)")
    def start(self, element):
        element.namespaces = self.namespaces[:]
        qn = self._qname.match(element.tag)
        element.ns = qn.group(1)
        element.tagName = qn.group(2)

class XMLCatalog(Catalog):
    # http://www.oasis-open.org/committees/entity/spec.html
    def __init__(self, uri, resolver):
        self.parent_map = {}
        Catalog.__init__(self, uri, resolver)
        
    def parse(self):
        # XXX support HTTP URI's
        self.tree = ElementTree.parse(self.uri, NamespaceParser())
        self.root = self.tree.getroot()
        if self.root.tagName != "catalog":
            raise "Invalid catalog file [%s] root tag [%s]" % (self.uri, self.root.tagName)
        self.parent_map = dict((c, p) for p in self.tree.getiterator() for c in p)
        self._parseNode(self.root)

    def _parseNode(self, node):
        methodName = "_handle_%s" % node.tagName.lower()
        #print methodName
        if hasattr(self, methodName):
            fn = getattr(self, methodName)
            fn(node)
        for child in list(node):
            #print "parsing child %s"%child.tagName
            self._parseNode(child)
        methodName = "_handle_%s_end" % node.tagName.lower()
        #print methodName
        if hasattr(self, methodName):
            fn = getattr(self, methodName)
            fn(node)

    def _handle_catalog(self, node):
        self.prefer = node.attrib.get("prefer", "public")
        
    def _get_relative_uri(self, uri, node):
        parent = self.parent_map[node]
        if parent.tagName == "group":
            base = parent.attrib.get("{http://www.w3.org/XML/1998/namespace}base", self.dir)
            if base != self.dir and not os.path.isabs(base):
                base = os.path.normpath(os.path.join(self.dir, base))
        else:
            base = self.dir
        return relativize(base, uri)

    def _handle_public(self, node):
        id = node.attrib.get('publicId')
        uri = self._get_relative_uri(node.attrib.get('uri'), node)
        self.public[id] = PublicID(id, uri, node)
        
    def _handle_system(self, node):
        id = node.attrib.get('systemId')
        uri = self._get_relative_uri(node.attrib.get('uri'), node)
        self.system[id] = SystemID(id, uri, node)
        
    def _handle_rewritesystem(self, node):
        self.rewritesystem[node.attrib.get("systemIdStartString")] = node.attrib.get("rewritePrefix")
        
    def _handle_delegatepublic(self, node):
        startId = node.attrib.get("publicIdStartString")
        if startId not in self.delegatepublic:
            self.delegatepublic[startId] = []
        self.delegatepublic[startId].append(Delegate(node=node))
        
    def _handle_delegatesystem(self, node):
        startId = node.attrib.get("systemIdStartString")
        if startId not in self.delegatesystem:
            self.delegatesystem[startId] = []
        self.delegatesystem[startId].append(Delegate(node=node))
        
    def _handle_uri(self, node):
        name = node.attrib.get("name")
        uri = self._get_relative_uri(node.attrib.get('uri'), node)
        self.urimap[name] = URI(name, uri, node)
        
    def _handle_rewriteuri(self, node):
        self.rewriteuri[node.attrib.get("uriStartString")] = node.attrib.get("rewritePrefix")
        
    def _handle_delegateuri(self, node):
        startId = node.attrib.get("uriStartString")
        if startId not in self.delegateuri:
            self.delegateuri[startId] = []
        self.delegateuri[startId].append(Delegate(node=node))
        
    def _handle_nextcatalog(self, node):
        catalogURI = self._get_relative_uri(node.attrib.get('catalog'), node)
        if self.resolver:
            try:
                self.resolver.addCatalogURI(catalogURI)
                self.nextcatalog.append(catalogURI)
            except Exception, e:
                log.error("Unable to read catalog file [%s] [%s]", catalogURI, e)
                #raise
        
    # XML Catalog support for http://www.oasis-open.org/specs/tr9401.html
    def _handle_doctype(self, node):
        self.doctype[node.attrib.get("name")] = node
        
    def _handle_document(self, node):
        self.document[node.attrib.get("uri")] = node

    def _handle_dtddecl(self, node):
        self.dtddecl[node.attrib.get("publicId")] = node

    def _handle_entity(self, node):
        self.entity[node.attrib.get("name")] = node

    def _handle_linktype(self, node):
        self.linktype[node.attrib.get("name")] = node

    def _handle_notation(self, node):
        self.notation[node.attrib.get("name")] = node

    def _handle_sgmldecl(self, node):
        self.sgmldecl[node.attrib.get("uri")] = node


class SGMLCatalog(Catalog):
    def parse(self):
        # setup lexer and add token matching regexes
        self.lex_matches = [
            ('whitespace',      self.doMultiLineBlock,  EXECFN|SKIPTOK),
            ('single',          self._handle_entity,            EXECFN|SKIPTOK),
            ('double',          self._handle_entity,            EXECFN|SKIPTOK),
        ]

        self.l = Lexer(self.uri)
        for p in self.lex_matches:
            # log.debug("adding %r",p[0])
            attributes = p[2]
            if not attributes: attributes = MAPTOK|EXECFN
            self.l.addmatch(collector.res[p[0]],p[1],p[0],attributes)

        self.lineno = 1
        self.ignore = 0
        self.scanData()
        
    def scanData(self):
        # XXX FIXME support http(s)
        f = open(self.uri)
        data = f.read()
        f.close
        
        # XXX
        # because of the many issues around comments in dtd files, and since
        # we're doing a sloppy parse, lets just get rid of all comments now.
        data = collector.res["COMMENT"].sub("", data)
        r = re.compile(r"--+.*?--+", re.S|re.U)
        data = r.sub("", data)
        
        self.l.settext(data)
            
        #res = []
        while 1:
            try:
                t, v = self.l.scan()
            except:
                #if self.l.textindex < len(self.l.text):
                #    self.l.textindex += 1
                #    continue
                raise
            log.debug("  lex symbol: %r %r", t, v)
            if t == self.l.eof:
                break
            #res.append((t, v))

    def doMultiLineBlock(self, m):
        #log.debug("block start at lineno %d",self.lineno)
        nl = collector.res["newlines"].findall(m.group(0))
        blockLen = len(nl)
        self.lineno = self.lineno + blockLen
        #log.debug("block had %d lines, lineno is %d", blockLen, self.lineno)
        return ""

    # http://www.oasis-open.org/specs/tr9401.html
    # http://www.jclark.com/sp/catalog.htm
    def _handle_entity(self, m):
        # XXX TODO need to understand teh SGML catalog better, we have
        # enough to handle sgml-lib catalogs for now
        m = m.groupdict()
        data1 = strip_quotes(m['data1'])
        if 'data2' in m:
            data2 = strip_quotes(m['data2'])
        else:
            data2 = ""
        if m['type'] == "PUBLIC":
            filename = relativize(self.dir, data2)
            self.public[data1] = PublicID(data1, filename)
        elif m['type'] == "SYSTEM":
            filename = relativize(self.dir, data2)
            self.system[data1] = SystemID(data1, filename)
        elif m['type'] == "DELEGATE":
            self.delegatepublic[data1] = Delegate(data1, data2)
        elif m['type'] == "CATALOG":
            self.nextcatalog.append(data1)
            if self.resolver:
                try:
                    self.resolver.addCatalogURI(data1)
                except Exception, e:
                    log.error("Unable to read catalog file [%s] [%s]", uri, e)
                    #raise
        elif m['type'] == "BASE":
            self.dir = data1
        return ""


class CatalogResolver:
    _urntrans = {
        '+': ' ', ':': '//', ';': '::', '%2B': '+', '%3A': ':',
        '%2F': '/', '%3B': ';', '%27': "'", '%3F': '?', '%23': '#', '%25': '%'
    }
    def __init__(self, catalogURIs=[]):
        self.init(catalogURIs)

    def init(self, catalogURIs=[]):
        # order of catalog entries is important for resolution rules
        # self.catalogs only contains the top level catalogs, but
        # catalogMap contains ALL catalogs (such as those found in
        # nextCatalog tags)
        self.catalogs = []
        self.catalogMap = {}
        self.datasets = {} # uri to dataset map
        self.resetCatalogs(catalogURIs)
    
    def resetCatalogs(self, catalogURIs=[]):
        catalogs = []
        for uri in catalogURIs:
            try:
                if uri not in self.catalogMap:
                    catalog = self.addCatalogURI(uri)
                    if not catalog:
                        continue
                catalogs.append(self.catalogMap[uri])
            except Exception, e:
                log.error("Unable to read catalog file [%s] [%s]", uri, e)
                #raise
        self.catalogs = catalogs
        
    def addCatalogURI(self, uri):
        if uri in self.catalogMap:
            log.info("Catalog already parsed [%s]", uri)
            return None
        # XXX how do we determin what type of catalog we want to open?
        ext = os.path.splitext(uri)[1]
        if ext == ".xml":
            catalog = XMLCatalog(uri, self)
        else:
            catalog = SGMLCatalog(uri, self)

        self.catalogMap[uri] = catalog
        return catalog

    def unwrapURN(self, urn):
        # http://www.oasis-open.org/committees/entity/spec.html#s.xmlcat
        # 6.4. URN "Unwrapping"
        unwrapped = urn
        # remove prefix
        if unwrapped.find('urn:publicid:') != 0:
            return None
        unwrapped = unwrapped[13:]
        # decode
        for i in range(len(unwrapped)):
            if unwrapped[i] in self._urntrans:
                unwrapped[i] = self._urntrans[unwrapped[i]]
        return unwrapped

    def findExternalIdentifierInCatalog(self, catalog, publicId=None, systemId=None):
        # 7.1.2
        if systemId:
            # 7.1.2 #2
            if systemId in catalog.system:
                if catalog.prefer == 'public' and publicId in catalog.public:
                    return catalog.public[publicId].uri
                return catalog.system[systemId].uri
            # 7.1.2 #3
            rewrite = catalog.getSystemRewrite(systemId)
            if rewrite:
                return rewrite
            # 7.1.2 #4
            delegatecatalogs = catalog.getSystemDelegates(systemId)
            if delegatecatalogs:
                return self.findExternalIdentifier(delegatecatalogs, None, systemId)
        # 7.1.2 #5
        if publicId:
            if publicId in catalog.public:
                return catalog.public[publicId].uri
            # 7.1.2 #6 
            delegatecatalogs = catalog.getPublicDelegates(publicId)
            if delegatecatalogs:
                return self.findExternalIdentifier(delegatecatalogs, publicId, None)
        for catalogURI in catalog.nextcatalog:
            ident = self.findExternalIdentifierInCatalog(self.catalogMap[catalogURI], publicId, systemId)
            if ident:
                return ident
        return None
        
    def findExternalIdentifier(self, catalogs, publicId=None, systemId=None):
        # http://www.oasis-open.org/committees/entity/spec.html#s.xmlcat

        # 7.1.1 #1
        for catalog in catalogs:
            ident = self.findExternalIdentifierInCatalog(catalog, publicId, systemId)
            if ident:
                return ident
        return None

    # e.g. info from doctype declaration
    def resolveExternalIdentifier(self, publicId=None, systemId=None):
        # resolve the dataset declaration to a uri
        if not publicId and not systemId:
            raise "no public or system id provided to the resolver"

        if publicId:
            if publicId.find('urn:publicid:') == 0:
                publicId = self.unwrapURN(publicId)
            if systemId and systemId.find('urn:publicid:') == 0:
                # either the unwrapped sysid is the same as the unwrapped
                # public id, in which case we ignore the systemid, or
                # it is an error, and we ignore the systemid anyway
                systemId = None
        elif systemId and systemId.find('urn:publicid:') == 0:
                publicId = self.unwrapURN(systemId)

        return self.findExternalIdentifier(self.catalogs, publicId, systemId)
    
    def findURIInCatalog(self, catalog, uri):
        # 7.2.2 #2
        if uri in catalog.urimap:
            return catalog.urimap[uri].uri
        # 7.2.2 #3
        rewrite = catalog.getURIRewrite(uri)
        if rewrite:
            return rewrite
        delegatecatalogs = catalog.getURIDelegates(uri)
        if delegatecatalogs:
            return self.findURI(delegatecatalogs, uri)
        for catalogURI in catalog.nextcatalog:
            ident = self.findURIInCatalog(self.catalogMap[catalogURI], uri)
            if ident:
                return ident
        return None

    def findURI(self, catalogs, uri):
        # 7.2.2 #1
        for catalog in catalogs:
            ident = self.findURIInCatalog(catalog, uri)
            if ident:
                return ident
        return None

    # e.g. an XML namespace
    def resolveURI(self, uri):
        # 7.2.1
        if uri.find('urn:publicid:') == 0:
            uri = self.unwrapURN(uri)
            return self.findExternalIdentifier(self.catalogs, uri, None)
        return self.findURI(self.catalogs, uri)
    
    def getWellKnownNamspaces(self):
        ns = {}
        for catalog in self.catalogs:
            ns.update(catalog.urimap)
        return ns
        
    def getDatasetForURI(self, uri, casename=False):
        if uri in self.datasets:
            return self.datasets[uri]
        ext = os.path.splitext(uri)[1]
        if ext == ".dtd":
            dataset = DTD(uri, resolver=self, casename=casename).dataset
        elif ext == ".rng":
            dataset = rng(uri).dataset
        else:
            raise "Unsuported Scheme type (DTD and RelaxNG only)"
        self.datasets[uri] = dataset
        return dataset

    def getDatasetForDoctype(self, publicId=None, systemId=None):
        uri = self.resolveExternalIdentifier(publicId, systemId)
        if not uri:
            return None
        casename = publicId and publicId.find(" HTML ") >= 0
        return self.getDatasetForURI(uri, casename)

    def getDatasetForNamespace(self, uri=None):
        uri = self.resolveURI(uri)
        if not uri:
            return None
        return self.getDatasetForURI(uri)
    
    def getDataset(self, publicId=None, systemId=None, uri=None):
        dataset = None
        if uri:
            dataset = self.getDatasetForNamespace(uri)
        if not dataset and (publicId or systemId):
            dataset = self.getDatasetForDoctype(publicId, systemId)
        return dataset


if __name__=="__main__":
    logging.basicConfig()
    
    import sys
    if len(sys.argv)>1:
        filename = sys.argv[1]
        catSvc = CatalogResolver([filename])
        ns = catSvc.getWellKnownNamspaces()
        print ns
        print catSvc.resolveExternalIdentifier(systemId=ns.keys()[0])
        ds = catSvc.getDatasetForNamespace(ns.keys()[0])
        ds.dump(sys.stdout)
    else:
        import os, sys
        # we're  in src/python-sitelib, we need the contrib dir
        basedir = os.path.dirname(os.path.dirname(os.getcwd()))
        catalogs = os.path.join(basedir, "contrib", "catalogs")
        # parse a single dtd
        #filename = os.path.join(catalogs, "sgml-lib","REC-smil20-20050107","SMIL20Basic.dtd")
        #dtd = DTD(filename)
        #dtd.dataset.dump(sys.stdout)
        #sys.exit(0)
        
        # parse all dtd files in a catalog
        #filename = os.path.join(catalogs, "sgml-lib","xml.soc")
        #cat = SGMLCatalog(filename)
        #print cat.public
        #print cat.system
        #
        #for pubid in cat.public.values():
        #    ext = os.path.splitext(pubid.uri)[1]
        #    if ext != ".dtd": continue
        #    print "PARSING [%s]"%pubid.uri
        #    try:
        #        dtd = DTD(pubid.uri)
        #    except Exception, e:
        #        print "...FAILED"

        # use the catalog resolver to find a catalog
        catalogFiles = [os.path.join(catalogs, "sgml-lib","xml.soc"),
                        os.path.join(catalogs, "sgml-lib","sgml.soc"),
                        #"/Users/shanec/main/Apps/Komodo-devel/test/catalogs/doesnotexist.xml"
                        ]
        catSvc = CatalogResolver(catalogFiles)
        #
        #dtdFile = catSvc.resolveExternalIdentifier(systemId="spec.dtd")
        #print "got dtd %s" % dtdFile
        #assert dtdFile == "http://www.w3.org/XML/1998/06/xmlspec-v20.dtd"
        #
        #dtdFile = catSvc.resolveExternalIdentifier(publicId="-//W3C//DTD Specification V2.0//EN")
        #print "got dtd %s" % dtdFile
        #assert dtdFile == "http://www.w3.org/XML/1998/06/xmlspec-v20.dtd"
        #
        catSvc.init(["/Users/shanec/main/Apps/Komodo-devel/test/catalogs/test1.xml"])
        print catSvc.getWellKnownNamspaces()
        #dtdFile = catSvc.resolveExternalIdentifier(publicId="-//OASIS//DTD DocBook XML V4.4//EN")
        #print "got dtd %s" % dtdFile
        #assert dtdFile == "file:///usr/share/xml/docbook44/docbookx.dtd"
        
        # testing rewriteURI and rewriteSystem
        #catSvc.init(["/Users/shanec/main/Apps/Komodo-devel/test/catalogs/test2.xml"])
        #dtdFile = catSvc.resolveURI("http://docbook.sourceforge.net/release/xsl/current/thisisatest.xml")
        #print "got dtd %s" % dtdFile
        #assert dtdFile == "file:///usr/share/xml/docbook-xsl-1.68.1/thisisatest.xml"
        #dtdFile = catSvc.resolveExternalIdentifier(systemId="http://www.oasis-open.org/docbook/xml/4.4/thisisatest.xml")
        #print "got dtd %s" % dtdFile
        #assert dtdFile == "file:///usr/share/xml/docbook44/thisisatest.xml"
        
        catSvc.init([os.path.join(catalogs, "docbook44","catalog.xml")])
        expect = os.path.join(catalogs, "docbook44", "docbookx.dtd")
        dtdFile = catSvc.resolveExternalIdentifier(publicId="-//OASIS//DTD DocBook XML V4.4//EN")
        print "got dtd %s" % dtdFile
        assert dtdFile == expect
        dtdFile = catSvc.resolveExternalIdentifier(systemId="http://www.oasis-open.org/docbook/xml/4.4/docbookx.dtd")
        print "got dtd %s" % dtdFile
        assert dtdFile == expect
        dtdFile = catSvc.resolveExternalIdentifier(systemId="http://docbook.org/xml/4.4/docbookx.dtd")
        print "got dtd %s" % dtdFile
        assert dtdFile == expect
        #catSvc.init(["/Users/shanec/tmp/dtd/DITA-OT1.3/catalog-dita_template.xml"])
        #dtdFile = catSvc.resolveExternalIdentifier(publicId="-//OASIS//DTD DITA Map//EN")
        #print "got dtd %s" % dtdFile
        
        