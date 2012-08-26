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

import time
import re
from ciElementTree import TreeBuilder, XMLParser, Element
import logging
log = logging.getLogger("koXMLTreeService")
#log.setLevel(logging.INFO)

class recollector:
    def __init__(self):
        self.res = {}
        self.regs = {}
        
    def add(self, name, reg, mods=None ):
        self.regs[name] = reg % self.regs
        #print "%s = %s" % (name, self.regs[name])
        if mods:
            self.res[name] = re.compile(self.regs[name], mods) # check that it is valid
        else:
            self.res[name] = re.compile(self.regs[name]) # check that it is valid

collector = recollector()
a = collector.add

a("S" , "[ \\n\\t\\r]+")
a("NameStrt" , "[A-Za-z_:]|[^\\x00-\\x7F]")
a("NameChar" , "[A-Za-z0-9_:.-]|[^\\x00-\\x7F]")
a("Name" , "(?:%(NameStrt)s)(?:%(NameChar)s)*")
a("AttValSE" , "\"[^<\"]*\"|'[^<']*'")
a("attrfinderRE" , "(?:[\n \t]*)(%(Name)s)(?:%(S)s)?=(?:%(S)s)?(%(AttValSE)s)")
a("namespaces", 'xmlns(?::(?P<prefix>\w+))?=(?P<ns>(?:")([^"]*?)(?:")|(?:\')([^\']*?)(?:\'))', re.S|re.U)
a("tagpart", '(?:<(?![?!-/>\s]))((?:(?P<prefix>[^\s/>]+):)?(?P<name>[^:\s/>]+)?)(?:\s+(?P<data>[^/<>]*))?', re.S|re.U)
a("tags", '<!--.*?-->|%(tagpart)s(?:/)?>', re.S|re.U)
a("alltags", '<!--.*?-->|(<[^\[!>?-].*?>)', re.S|re.U)
a("QuoteSE" , "\"[^\"]*\"|'[^']*'")
a("DOCTYPE",        r'<!DOCTYPE\s+(?P<type>\S+)\s+(?P<ident>PUBLIC|SYSTEM)\s+(?P<data1>%(QuoteSE)s)\s*(?P<data2>%(QuoteSE)s)?\s*(?:\[|>)', re.S)

def getdoctype(text):
    doctype = None
    regex = collector.res["DOCTYPE"]
    m = regex.search(text)
    if m:
        m = m.groupdict()
        # [1:-1] is to strip quotes
        if m['data1']:
            m['data1'] = m['data1'][1:-1]
        if m['data2']:
            m['data2'] = m['data2'][1:-1]
        if m['ident'] == 'PUBLIC':
            doctype = (m['type'], m['ident'], m['data1'], m['data2'])
        else:
            doctype = (m['type'], m['ident'], "", m['data1'])
    return doctype

def getattrs(text):
    attrs = {}
    regex = collector.res["attrfinderRE"]
    match = regex.findall(text)
    for a in match:
        if a[1]:
            attrs[a[0]]=a[1][1:-1]
        else:
            attrs[a[0]]=""
    return attrs

def currentTag(text):
    m = collector.res["tagpart"].search(text)
    if not m: return None
    td = m.groupdict()
    ad = {}
    if td['data']:
        ad.update(getattrs(td['data']))
    return (td['prefix'],td['name'],ad, m.start(0))

def elementFromTag(tree, tag, parent=None):
    tagName = tag[1]
    if not tagName:
        tagName = ""
    ns = None
    if tag[0]:
        if tag[0] in tree.prefixmap:
            ns = tree.prefixmap[tag[0]]
        else:
            nsattr = "xmlns:%s"%tag[0]
            if nsattr in tag[2]:
                ns = tag[2][nsattr]
                del tag[2][nsattr]
                tree.prefixmap[tag[0]] = ns
    elif "xmlns" in tag[2]:
        ns = tag[2]["xmlns"]
        del tag[2]["xmlns"]
    elif parent is not None:
        ns = parent.ns
    localName = tag
    if ns:
        tagName = "{%s}%s" % (ns, tagName)
    elem = Element(tagName, tag[2])
    try:
        elem.start = tree.err_info
        elem.end = None
    except:
        # will happen when parsing with cElementTree
        pass
    #print elem.localName
    if parent is not None:
        parent.append(elem)
    tree.nodemap[elem] = parent
    tree.nodes.append(elem)
    if elem.ns is not None:
        if elem.ns not in tree.tags:
            tree.tags[elem.ns] = {}
        tree.tags[elem.ns][elem.localName]=elem
    return elem

def elementFromText(tree, text, parent=None):
    current = currentTag(text)
    if current:
        return elementFromTag(tree, current, parent)
    return None

class iterparse:
    """iterparse that catches syntax errors so we can still handle any
    events that happen prior to the syntax error"""
    def __init__(self, content, events=("start", "end", "start-ns", "end-ns")):
        self.content = content
        self._events = events
        self.err = None
        self.err_info = None
        self.root = None

    def __iter__(self):
        events = []
        b = TreeBuilder()
        p = XMLParser(b)
        p._setevents(events, self._events)
        try:
            p.feed(self.content)
        except SyntaxError, e:
            self.err = e
            self.err_info = (p.CurrentLineNumber, p.CurrentColumnNumber, p.CurrentByteIndex)

        for event in events:
            yield event
        del events[:]
        try:
            self.root = p.close()
        except SyntaxError, e:
            # if we had a previous syntax error, keep it
            if not self.err:
                self.err = e
                self.err_info = (p.CurrentLineNumber, p.CurrentColumnNumber, p.CurrentByteIndex)
        for event in events:
            yield event

def bisect_left_nodes_start(a, x, lo=0, hi=None):
    """A version of bisect.bisect_left which compares nodes based on their start position.
    """
    if hi is None:
        hi = len(a)
    while lo < hi:
        mid = (lo+hi)//2
        #print "comparing", a[mid].start[:2], "and", x
        if a[mid].start is None: return mid
        if a[mid].start[:2] == x: return mid
        if a[mid].start[:2] < x: lo = mid+1
        else: hi = mid
    return lo

class XMLDocument(object):
    
    def __init__(self, content=None):
        self.content = content
        self.reset()
        if self.content:
            self.getDoctype()

    def getDoctype(self):
        self.doctype = getdoctype(self.content)
        if self.doctype:
            self.publicId = self.doctype[2]
            self.systemId = self.doctype[3]

    def reset(self):
        self.doctype = None
        self.publicId = None
        self.systemId = None
        self.err = None
        self.err_info = None
        self.root = None
        self.current = None

        self._rootnodes = []
        self.nodes = [] # flat list of all nodes
        self.tags = {} # { namespace_uri: { tag_local_name: elem, ...} , ...}
        self.nodemap = {} # {child_elem: parent_elem, ... }
        self.namespaces = [] # flat list of namespace uri's
        self.nsmap = {} # { "http:/...": "xslt", ... }
        self.prefixmap = {} # { "xslt": "http://.....", ... }

    def getRoots(self):
        # return a list of all nodes that have no parent
        if not self._rootnodes:
            self._rootnodes = [node for node in self.nodemap if self.nodemap[node] is None]
        return self._rootnodes

    def namespace(self, elem):
        #print "%s:%s xmlns[%s]"%(self.prefix(elem),elem.localName,elem.ns)
        if hasattr(elem, "ns") and elem.ns:
            return elem.ns
        return self.nsmap.get("")

    def parent(self, elem):
        return self.nodemap.get(elem)

    def qname(self, name):
        if name and name[0] == '{':
            ns, ln = name[1:].split('}')
            prefix = self.nsmap.get(ns)
            if prefix:
                return "%s:%s" % (prefix, ln)
            return ln
        return name

    def isAncestorOf(self, node, child):
        """ Return true if child is a descendant of node """
        #print "asking if %r is an ancestor of %r" %( node, child)
        currentParent = self.parent(child)
        while currentParent != child and currentParent is not None:
            #print "\tparent =", currentParent
            if node == currentParent:
                #print "-->is a parent"
                return True
            currentParent = self.parent(currentParent)
        #print "-->isn't a parent"
        return False

    def locateNode(self, line, col):
        # nodes are 1-indexed, so we need to switch our indexing scheme
        line += 1

        # first look for the last node to start at or before the current
        # position
        idx = bisect_left_nodes_start(self.nodes, (line, col))-1
        if idx < 0:
            if self.nodes:
                return self.nodes[0]
            return None
        assert idx < len(self.nodes)
        node = self.nodes[idx]
        # that was easy.  Now we may need to move up the parent chain
        # from this node if we are past the end of a node but before
        # the beginning of another, e.g.  <foo><bar>asd</bar>|</foo>
        # -- the right node is foo, but the current value of node is 'bar'
        startPos = node.start[:2]
        if startPos is None:  # if we're in a partial node, that's it
            return node
        if startPos[:2] == (line, col):  # if it's an exact match, that's it
            return node
        #if idx == 0: return node # if we're at the toplevel, so be it
        while node is not None:
            while node.end:
                # move up the parent chain until you get a parent
                # whose end is after the current location
                last_line, last_col = node.end[:2]
                if (last_line, last_col) < (line, col):
                    node = self.parent(node)
                    if node is None: return node
                    continue
                break

            if node is not None and not node.end:
                # check it's parents and see if they have end markers
                pnode = self.parent(node)
                while pnode:
                    if pnode.end:
                        last_line, last_col = pnode.end[:2]
                        if (last_line, last_col) < (line, col):
                            node = pnode
                            break
                    pnode = self.parent(pnode)
                if node.end:
                    continue
            break
                
        return node

    def prefixFromNS(self, ns):
        if self.prefixmap.get("") == ns:
            return ""
        prefix = self.nsmap.get(ns)
        if not prefix:
            prefix = self.nsmap.get(self.root.ns)
        return prefix
        
    def prefix(self, elem):
        if not hasattr(elem, "ns") or not elem.ns:
            return ""
        return self.prefixFromNS(elem.ns)

    def tagname(self, elem):
        prefix = self.prefix(elem)
        if prefix:
            return "%s:%s" % (prefix, elem.localName)
        return elem.localName

    _endtagRe = re.compile(r"(</(\w+:)?\w+>)", re.U)
    def parse(self, content=None):
        self.reset()
        self.content = content
        if content:
            # first, find the doctype decl
            self.getDoctype()
        elif not self.content:
            raise Exception("no content to parse")
        
        elstack = [None]
        self.current = None
        tags = {}
        last_pos_ok = None
        iter = iterparse(self.content)
        for event, elem in iter:
            if event == "start":
                #print "%r %r %d %d %d" % (event, elem, elem.start[0], elem.start[1], elem.start[2])
                self.nodemap[elem] = self.current
                self.nodes.append(elem)
                if elem.ns not in self.tags:
                    self.tags[elem.ns] = {}
                self.tags[elem.ns][elem.localName]=elem
                elstack.append(elem)
                self.current = elem
            elif event == "end":
                #print "%r %r %r %r" % (event, elem, elem.start, elem.end)
                if elem.end:
                    try:
                        pos = elem.end[2]
                        #print "  len %d pos %d" % (len(self.content), pos)
                        # put the end location at the end of the end tag
                        m = self._endtagRe.match(self.content[pos:])
                        if m and m.groups():
                            pos = pos + m.end(1)
                            if pos > 0:
                                # we want to be after the ">"
                                diff = pos - elem.end[2] + 1 
                                elem.end = (elem.end[0], elem.end[1] + diff, pos)
                    except IndexError, e:
                        # XXX FIXME BUG 56337
                        log.exception(e)
                        pass
                node = elstack.pop()
                if elstack[-1] is None:
                    self._rootnodes.append(node)
                self.current = elstack[-1]
            elif event == "start-ns":
                self.namespaces.append(elem)
                self.prefixmap[elem[0]] = elem[1]
                self.nsmap[elem[1]] = elem[0]
            elif event == "end-ns":
                self.namespaces.pop()
        self.root = iter.root
        self.err = iter.err
        self.err_info = iter.err_info
        # set the root if we can
        if self.root is None and self.nodes:
            self.root = self.nodes[0]
        self.end_error(self.content)
        # if we still do not have a root, do it
        # now, as we should have a node
        if self.root is None and self.nodes:
            self.root = self.nodes[0]
        # release content
        self.content = None

    def end_error(self, content):
        if not self.err_info:
            return
        if not content:
            raise Exception("No content?")
        # create an element for the last part of the parse
        parent = self.current
        if self.err_info[2] >= 0:
            start = self.err_info[2]
        else:
            # slower
            #print self.err_info
            p = 0
            for i in range(self.err_info[0] - 1):
                # use re.search("\r|\n|\r\n")
                p = content.find("\n", p + 1)
            start = p + self.err_info[1] + 1
        end = content.find("<", start+1)
        if end <= start:
            end = len(content)
        # fixup the start position
        start = content.rfind(">", 0, start) + 1
        if start >= end:
            return
        #print self.err_info
        #print content[start:end]
        current = currentTag(content[start:end])
        if not current:
            return

        #print "%s:%s %r %d" % current
        # fix error info
        start = start+current[3]
        line = content.count('\n', 0, start)
        col = start - content.rfind('\n', 0, start)
        self.err_info = (line, col, start)
        self.current = elem = elementFromTag(self, current, parent)
    
    def dump(self):
        print "error ",self.err
        print "error_info ",self.err_info
        print "%d nodes created" % len(self.nodemap)
        print "doctype ",self.doctype
        print "publicId ",self.publicId
        print "systemId ",self.systemId
        print self.prefixmap
        print self.nsmap
        print "root ",self.root
        if self.root:
            print "root tag ",self.root.tag
            print "root ns ",self.root.ns
            print "root localName ",self.root.localName
            print "root start ",self.root.start
            print "root end ",self.root.end
        print "tree.current ",self.current

import HTMLTreeParser
class HTMLDocument(XMLDocument):

    def parse(self, content=None):
        if content:
            self.reset()
            self.content = content
            # first, find the doctype decl
            self.getDoctype()
        elif not self.content:
            raise Exception("no content to parse")

        p = HTMLTreeParser.Parser(HTMLTreeParser.HTMLTreeBuilder())
        p.feed(content)
        self.root = p.close()
        self.nodes = p._builder.nodes
        self.nodemap = p._builder.nodemap
        self._rootnodes = p._builder._rootnodes
        self.current = p._builder.current

class TreeService:
    __treeMap = {} # map uri to elementtree
    def __init__(self):
        pass

    def treeFromCache(self, uri):
        if uri in self.__treeMap:
            #print "tree cache hit for [%s]"%uri
            return self.__treeMap[uri]
        return None
    
    def getTreeForURI(self, uri, content=None):
        if not uri and not content:
            return None
        tree = None
        if uri and uri in self.__treeMap:
            tree = self.__treeMap[uri]
            #if tree is not None:
            #    print "tree cache hit for [%s]"%uri
            if not content:
                return tree

        if not tree:
            if not content:
                # get the content
                try:
                    f = open(uri, 'r')
                    content = f.read(-1)
                    f.close()
                except IOError, e:
                    # ignore file errors and return an empty tree
                    content = ""
            if not content.startswith("<?xml"):
                tree = HTMLDocument()
            if not tree:
                tree = XMLDocument()
                #raise Exception("NOT IMPLEMENTED YET")
        if content:
            tree.parse(content)
        if uri:
            self.__treeMap[uri] = tree
        return tree
    
    def getTreeForContent(self, content):
        return self.getTreeForURI(None, content)
        

__treeservice = None
def getService():
    global __treeservice
    if not __treeservice:
        __treeservice = TreeService()
    return __treeservice

if __name__ == "__main__":
    import sys
    # basic logging configuration
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

    bigfile = "/Users/shanec/main/Apps/Komodo-devel/test/bigfile.xml"
    fn = "/Users/shanec/main/Apps/Komodo-devel/src/samples/xslt_sample.xsl"
    from elementtree.ElementTree import tostring
    
    if 0:
        #fn = "/Users/shanec/main/Apps/Komodo-devel/src/install/wix/feature-core.wxs"
        t1 = time.clock()
        tree = getService().getTreeForURI(bigfile)
        t2 = time.clock()
        print "cElementTree took ",(t2-t1)
        tree.dump()
    
    if 0:
        f = open(bigfile, 'r')
        content = f.read(-1)
        f.close()
        t1 = time.clock()
        tree = HTMLDocument()
        tree.parse(content)
        t2 = time.clock()
        print "HTMLBuilder took ",(t2-t1)
        
    if 0:
        print currentTag("<xsl")
        print currentTag("<xsl:")
        print currentTag("<xsl:tag")
        print currentTag("text><xsl:tag")
        #print nodemap

    html = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">

<head>
"""
    tree = getService().getTreeForURI("Text.html", html)
    print tostring(tree.root)

    html = u"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<html>
<HEAD>
 <TITLE>Mozilla Cross-Reference</TITLE>
 <link HREF=http://www.activestate.com/global.css rel="stylesheet" type="text/css">
</HEAD>
<BODY   BGCOLOR="#FFFFFF" TEXT="#000000"
	LINK="#0000EE" VLINK="#551A8B" ALINK="#FF0000">

<table width="100%" border="0" cellspacing="0" cellpadding="0">
  <tr>
    <td> 
      <table width="100%" border="0" cellspacing="0" cellpadding="0">
        <tr>
          <td width="145"><a href=http://www.activestate.com/index.html><img src=http://www.activestate.com/img/Main_Logo_Border.gif width="167" height="66" border="0" alt="ActiveState Tool Corp."></a></td>
          <td bgcolor="#000000" colspan=2 width="90%" align="center"><img src=http://www.activestate.com/img/Main_Banner.gif alt="Programming for the People."></td>
        </tr>
      </table>
      <table width="100%" bgcolor="#000000" border="0" cellpadding="0" cellspacing="0">
 <tr> 
  <td width="600"> 
    <table width="600" border="0" cellpadding="0" cellspacing="3">
     <tr> 
       <td class="mainnav" bgcolor="#C2B266" width="100" align="center"><a href=http://www.activestate.com/Products/index.html>Products</a></td>
       <td class="mainnav" bgcolor="#C2B266" width="100" align="center"><a href=http://www.activestate.com/Support/index.html>Support</a></td>
       <td class="mainnav" bgcolor="#C2B266" width="100" align="center"><a href=http://www.activestate.com/Corporate/index.html>About Us</a></td>
       <td class="mainnav" bgcolor="#C2B266" width="100" align="center"><a href=http://www.activestate.com/Contact_Us.html>Contact</a></td>
       <td class="mainnav" bgcolor="#C2B266" width="100" align="center"><a href=http://www.activestate.com/Site_Map.html>Site Map</a></td>
     </tr>
    </table>
   </td>
   <td class="mainnav" width="100%"> 
     <table width="100%" border="0" cellpadding="0" cellspacing="0">
       <tr> 
         <td class="mainnav" bgcolor="#C2B266" width="100%">&nbsp;</td>
         <td class="mainnav" bgcolor="#000000" width="3">&nbsp;</td>
       </tr>
     </table>
  </td>
 </tr>
</table>
</td>
</tr>
</table>

<I>$treename</I>
<P>

"""
    tree = getService().getTreeForURI("Text.html", html)
    print tostring(tree.root)

    html = """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN">
<HTML>
    <BODY>

        <FORM><FIELDSET ><SELECT class=""><OPTGROUP >            

"""
    tree = getService().getTreeForContent(html)
    

    tree = getService().getTreeForURI("newfile.txt", "")
    tree = getService().getTreeForURI("newfile.txt", "<html>")
    tree = getService().getTreeForURI("newfile.txt", "<html> <")
    node = tree.locateNode(tree.current.start[0], tree.current.start[1])
    assert node == tree.current, "locateNode returned incorrect node"

    tree = getService().getTreeForURI("newfile.txt", "<table></table>\n\n\n\n")
    node = tree.locateNode(2, 0)
    assert node is None, "locateNode returned incorrect node"
    node = tree.locateNode(0, 7)
    assert node is not None, "locateNode returned incorrect node"
    sys.exit(0)
    
    xml = """
<c1><c2 a1="1" a2='1' a3='val'><e1 /><e2 f1="1" f2 = '33' /><c3 a='1'>blah</c3></c2  >  </"""
    tree = getService().getTreeForContent(xml)
    node = tree.locateNode(tree.current.start[0], tree.current.start[1])
    assert node == tree.current, "locateNode returned incorrect node"
    
    xml = """<?xml version="1.0"?> 
<xsl:stylesheet xxmlns="xyz" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="xml" indent="yes"/>
<xsl:template match="Class">
    <html> <xsl:apply-imports/>
    <xsl:
            <xsl:apply-templates select="Order"/>
    </html>
</xsl:template>
"""
    tree = getService().getTreeForContent(xml)
    node = tree.locateNode(tree.current.start[0], tree.current.start[1])
    assert node == tree.current, "locateNode returned incorrect node"

    # ensure we get the correct current node
    xml = """<?xml version="1.0"?>
<!DOCTYPE window PUBLIC "-//MOZILLA//DTD XUL V1.0//EN" "http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul">
<window xmlns="http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul">
    <popupset id="editorTooltipSet">
        <popup type="tooltip" id="editorTooltip" flex="1">
            <description multiline="true" id="editorTooltip-tooltipText" class="tooltip-label" flex="1"/>
        </popup><
        <popup type="autocomplete" id="popupTextboxAutoComplete"/>
    </popupset>

"""
    tree = getService().getTreeForContent(xml)
    assert tree.current.localName == "popupset", "current element is incorrect"

    # ensure we get the correct current node
    xml = """<?xml version="1.0"?>
<!DOCTYPE window PUBLIC "-//MOZILLA//DTD XUL V1.0//EN" "http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul">
<window xmlns="http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul">
    <popupset id="editorTooltipSet">
        <popup type="tooltip" id="editorTooltip" flex="1">
            <description multiline="true" id="editorTooltip-tooltipText" class="tooltip-label" flex="1"/>
        </popup> <
        <popup type="autocomplete" id="popupTextboxAutoComplete"/>
    </popupset>

"""
    tree = getService().getTreeForContent(xml)
    assert tree.current.localName == "popupset", "current element is incorrect"
        
    xml = """<?xml version="1.0"?> 
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="xml" indent="yes"/>
  <
  
  <xsl:template/>
"""
    tree = getService().getTreeForContent(xml)
    assert tree.current == tree.root, "current element is incorrect"
    assert tree.current.localName == "stylesheet", "current element is incorrect"

    xml = """<?xml version="1.0"?> 
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="xml" indent="yes"/>
  <xsl:"""
    tree = getService().getTreeForContent(xml)
    assert tree.current.tag == "{http://www.w3.org/1999/XSL/Transform}", "current element is incorrect"
    assert tree.current.localName == "", "current element is incorrect"


    xml = """<?xml version="1.0"?> 
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="xml" indent="yes"/>
"""
    tree = getService().getTreeForContent(xml)
    assert tree.current.localName == "stylesheet", "current element is incorrect"

    xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html """

    tree = getService().getTreeForContent(xml)
    assert tree.current.localName == "html", "current element is incorrect"

    xml = """<?xml version="1.0"?> 
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="xml" indent="yes"/>
  <xsl:template
"""
    tree = getService().getTreeForContent(xml)
    assert tree.current.localName == "template", "current element is incorrect"

    xml = """<?xml version="1.0"?> 
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="xml" indent="yes"/><xsl:template"""
    tree = getService().getTreeForContent(xml)
    assert tree.current.localName == "template", "current element is incorrect"

    xml = u"""<?xml version="1.0"?> 
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="xml" indent="yes"/>
  <xsl:
  
  <xsl:template/>
"""
    tree = getService().getTreeForContent(xml)
    assert tree.current.localName == "", "current element is incorrect"
    assert tree.current.tag == "{http://www.w3.org/1999/XSL/Transform}", "current element is incorrect"
    
    html="""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<html><body><p><ul><li><li><li></ul></body>
"""
    tree = getService().getTreeForContent(html)
    #print tostring(tree.root)
    assert tree.current.localName == "html", "current element is incorrect"

    html = """<!DOCTYPE h:html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<h:html xmlns:h='urn:test'"""
    tree = getService().getTreeForContent(html)
    #print tostring(tree.root)
    assert tree.current.localName == "html", "current element is incorrect"

    #from cElementTree import Element
    #tag = u"{urn:test}test"
    #print tag
    #e = Element(tag, {})
    #print e.localName
    #print e.tag

    xml = """<?xml version="1.0" encoding="UTF-8"?>
<!-- This sample XML file shows you ... -->

<Class>
<Order Name="TINAMIFORMES">
        <Family Name="TINAMIDAE">
            <Species attr="value">content.</Species>
            <![CDATA[
                This is a CDATA section
            ]]>
        </Family>
    </Order>
"""
    tree = getService().getTreeForContent(xml)
    #print tostring(tree.root)
    assert len(tree.root[0][0][0]) == 0, "bad parent/child relationship"

    xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html>
    <body
        <!-- a comment -->
    <title>
    </title>
</html>
"""

    tree = getService().getTreeForContent(xml)
    #print tostring(tree.root)
    assert tree.current.localName == "body", "current element is incorrect"
    assert tree.parent(tree.current).localName == "html", "current element is incorrect"

    xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html
    <body
"""

    tree = getService().getTreeForContent(xml)
    #print tostring(tree.root)
    assert tree.current.localName == "html", "current element is incorrect"
