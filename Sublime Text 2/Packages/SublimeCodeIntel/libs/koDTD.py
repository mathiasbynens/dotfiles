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
import weakref
from koSimpleLexer import *

log = logging.getLogger("koDTD")
#log.setLevel(logging.DEBUG)

# XXX a cheap relativize
urimatch = re.compile("(\w+://.*|/.*|\w:\\.*|\w:/.*)")
def relativize(base, fn):
    if urimatch.match(fn):
        return fn
    return os.path.join(base, fn)

# regular expressions used for DTD parsing
collector = recollector()
a = collector.add

# secondary parsing regex
a("newlines" ,                   "[ \t]*(\r\n|\r|\n)")
a("groupedNamesSplitter", "[\s\|\*\+\(\)\?&,]+")
# not used in lex_matches
a("NDataDecl" ,     r"\s*'NDATA'\s*\S+", re.S|re.U)
a("QuotedString" ,  r'(?:")([^"]*?)(?:")|(?:\')([^\']*?)(?:\')', re.S|re.U)
a("ExternalID",     r"(?P<type>SYSTEM|PUBLIC)\s*(?P<literal1>%(QuotedString)s)\s*(?P<literal2>%(QuotedString)s)?", re.S|re.U)

# used in lex_matches
a("whitespace" ,    r"\s+", re.S|re.M)
a("section_ignore" , r'<!\[\s*IGNORE\s*\[.*?\]\]>', re.S|re.M)
a("section_start" , r'<!\[\s*(?P<name>\S+)\s*\[', re.S|re.M)
a("section_end" ,   r'\]\]>')
a("PEReference" ,   r"%%(?P<ref>[^;]+)[;\s]", re.U)
a("PEENTITY",         r'<!ENTITY\s+%%\s+(?P<name>\S+)\s+(?:--(?P<comment_entity>.*?)--\s+)?(?P<content>%(QuotedString)s|%(ExternalID)s(?:%(NDataDecl)s)?)\s*(?:--(?P<comment>.*?)--)?\s*>', re.S|re.U)
# PEENTITY2: another syntax tweak for xhtml-arch-1.mod
a("PEENTITY2",         r'<!ENTITY\s+(?P<name>\S+)\s+(?:--(?P<comment_entity>.*?)--\s+)?(?P<content>%(ExternalID)s(?:%(NDataDecl)s)?)\s*(?:--(?P<comment>.*?)--)?\s*>', re.S|re.U)
a("GEENTITY",         r'<!ENTITY\s+(?P<name>\S+)\s+(?P<type>\w+)\s+(?:--(?P<comment_entity>.*?)--\s+)?(?P<content>%(QuotedString)s)\s*(?:--(?P<comment>.*?)--)?\s*>', re.S|re.U)
a("ATTLIST",        r'<!ATTLIST\s+(?P<name>\(.*?\)|\S+)\s+(?P<content>.*?)\s*(?:>(?=\s))', re.S|re.U)
a("ELEMENT",        r'<!ELEMENT\s+(?P<name>\(.*?\)|\S+)\s+(?:(?P<start>\S)\s(?P<end>\S)\s+)?(?P<content>EMPTY|ANY|.*?)\s*(?:--(?P<comment>.*?)--)?\s*>', re.S|re.U)
a("COMMENT" ,       r"<!--(?P<comment>.*?)-->", re.S|re.M)

# we dont do anything with notations at this time
a("NOTATION" ,       r"<!NOTATION.*?>", re.S|re.M)

# stuff from HTML3.dtd that we dont use
a("USEMAP" ,       r"<!USEMAP.*?>", re.S|re.M)
a("SHORTREF" ,       r"<!SHORTREF.*?>", re.S|re.M)
a("ENTITY",         r'<!ENTITY\s+(?P<name>\S+)\s+(?P<content>%(QuotedString)s)\s*(?:--(?P<comment>.*?)--)?\s*>', re.S|re.U)

# xhtml-math-svg-flat-20020809.dtd has this, don't know why, I've never seen
# this in any DTD spec:
#   <?doc type="doctype" role="title" { XHTML 1.1 } ?>
a("PROCTAG" ,       r"<\?.*?\?>", re.S|re.M)

class dtd_dataset:
    def __init__(self):
        self.entities = {}
        self.elements = {}
        self.root = []
        self.attlist = {}
        self.namespace = ""
        self.elements_caseless = {}

    def element_info(self, element_name):
        name = element_name.lower()
        if name in self.elements_caseless:
            return self.elements_caseless[name]
        return None

    def buildRootList(self):
        all_elements = self.elements.keys()
        root = {}
        for el in all_elements:
            found = 0
            for e in self.elements.values():
                if el in e.elements:
                    found = 1
                    break
            if not found:
                root[el] = 1
        self.root = root.keys()

    def possible_children(self, element_name=None):
        if not element_name:
            return self.root
        else:
            name = element_name.lower()
            if name in self.elements_caseless:
                el =  self.elements_caseless[name]
                if el.content.lower() == "any":
                    elements = self.elements.keys()
                else:
                    elements = self.elements_caseless[name].elements
                result = set(elements)
                for el_name in elements:
                    ei = self.element_info(el_name)
                    if ei is not None and ei.start == "O":
                        # add the children for this to our list
                        result = result.union(self.possible_children(el_name))
                return result
        return self.root

    def possible_attributes(self, element_name):
        name = element_name.lower()
        if name in self.elements_caseless:
            return self.elements_caseless[name].attributes.keys()
        return []

    def possible_attribute_values(self, element_name, attribute_name):
        el = self.element_info(element_name)
        if el and attribute_name in el.attributes:
            return el.attributes[attribute_name].values
        return []
    
    def all_element_types(self):
        return self.elements.keys()
    
    def dump(self, stream):
        for e in self.elements.values():
            e.dump(stream)

def strip_quotes(str):
    if not str:
        return None
    if str[0] in ["'",'"']:
        return str[1:-1]
    return str

class dtd_entity:
    def __init__(self, d):
        self.name = d['name']
        self.data = d
        self.type = d['type']
        if 'literal1' in d:
            self.entity = strip_quotes(d['literal1'])
            self.dtd = strip_quotes(d['literal2'])
        else:
            self.entity = None
            self.dtd = None
        self.content = strip_quotes(d['content'])
        self.entityRe = re.compile(r"%%%s\b;?" % self.name, re.U)

    def applyEntity(self, text):
        if self.type is None:
            #print "replacing text [%s] with %r " % (r"%%%s;?" % self.name, self.content)
            return self.entityRe.sub(self.content, text)
        return text
        
class dtd_element:
    _top_groups = re.compile(r'([+-]\(.*?\)|\(.*?\)[\*\+]|\(.*?\))(?:\s|$)', re.S|re.U)
    def __init__(self, d, casename=False):
        self.name = d['name']
        self.data = d
        self.start = d['start']
        self.end = d['end']
        self.content = d['content']
        self.elements = [] # children names only
        self.attributes = {}
        self.namespace = ""
        
        if self.content not in ["empty", "any"]:
            matches = self._top_groups.findall(self.content)
            if matches:
                groupedNamesRe = collector.res["groupedNamesSplitter"]
                children = set()
                for match in matches:
                    if match[0] != "-" or match[-1] in ["?", "*","+",")"]:
                        # we found the potentially good children, keep them
                        children = children.union([n for n in groupedNamesRe.split(match) if n and n != '#PCDATA'])
                for match in matches:
                    if match[0] == "-":
                        children = children.difference([n for n in groupedNamesRe.split(match) if n])
                if casename:
                    self.elements = [i.lower() for i in list(children)]
                else:
                    self.elements = list(children)
        
    def dump(self, stream):
        stream.write("ELEMENT: %s\n" % self.name)
        for a in self.attributes.values():
            a.dump(stream)
        stream.write("    CHILDREN %r\n" % self.elements)

class dtd_attlist:
    _attr_line = re.compile('(?P<name>\w+)\s+(?P<type>[A-Za-z]+|\(.*?\))\s+(?P<default>#REQUIRED|#IMPLIED|\w+|(?:#FIXED)?((?:")([^"]*?)(?:")|(?:\')([^\']*?)(?:\')))\s*(?:--(?P<comment>.*?)--)?', re.S|re.U)
    def __init__(self, d, el=None, casename=False):
        self.name = d['name']
        self.data = d
        self.casename = casename
        if el:
            self.addAttributes(el)

    def addAttributes(self, el):
        for m in self._attr_line.finditer(self.data['content']):
            a = dtd_attr(m.groupdict(), self.casename)
            if a.name not in el.attributes:
                el.attributes[a.name] = a
        
    def dump(self, stream):
        pass

class dtd_attr:
    def __init__(self, d, casename=False):
        self.name = d['name']
        self.values = []
        self.type = 'CDATA'
        if d['type'][0] == '(':
            groupedNamesRe = collector.res["groupedNamesSplitter"]
            self.values = [n for n in groupedNamesRe.split(d['type']) if n]
            if casename:
                self.values = [v.lower() for v in self.values]
        else:
            self.type = d['type']
        self.default = d['default']
        self.comment = d['comment']

    def dump(self, stream):
        stream.write("ATTR: %s values %r default %s\n" %(self.name, self.values, self.default))



class DTD:

    # states
    TAGEND = 0
    TAGSTART = 1
    ENTITYTAG = 2
    ENTITY = 3
    ELEMENT = 4
    ATTRIBUTE = 5

    def __init__(self, filename, dataset=None, resolver=None, casename=False):
        # hook up the lexical matches to a function that handles the token
        self.lex_matches = [
            ('whitespace',      self.doMultiLineBlock,  EXECFN|SKIPTOK),
            ('COMMENT',         self.doCommentBlock,    EXECFN|SKIPTOK),
            ('section_ignore',  None,                   SKIPTOK),
            ('section_start',   self.section_start,     EXECFN|SKIPTOK),
            ('section_end',     self.section_end,       EXECFN|SKIPTOK),
            ('PEENTITY',        self.entity,            EXECFN|SKIPTOK),
            ('PEENTITY2',       self.entity,            EXECFN|SKIPTOK),
            ('GEENTITY',        self.entity,            EXECFN|SKIPTOK),
            ('PEReference',     self.pereference,       EXECFN|SKIPTOK),
            ('ELEMENT',         self.element,           EXECFN|SKIPTOK),
            ('ATTLIST',         self.attlist,           EXECFN|SKIPTOK),
            
            # these are formats in some DTD's that we will suppress
            ('USEMAP',          None,           SKIPTOK),
            ('SHORTREF',        None,           SKIPTOK),
            ('NOTATION',        None,           SKIPTOK),
            ('ENTITY',          None,           SKIPTOK),
            ('PROCTAG',         None,           SKIPTOK),
        ]

        self.casename = casename
        self.resolver = resolver
        if dataset is None:
            dataset = dtd_dataset()
        self.dataset = dataset
        self._element_stack = [self.dataset]
        self._includes = []
        self.filename = filename
        self.lineno = 0
        self.parse()
        self.dataset.buildRootList()

    def parse(self):
        # setup lexer and add token matching regexes
        self.l = Lexer(self.filename)
        for p in self.lex_matches:
            # log.debug("adding %r",p[0])
            attributes = p[2]
            if not attributes: attributes = MAPTOK|EXECFN
            self.l.addmatch(collector.res[p[0]],p[1],p[0],attributes)

        self.currentTag = None
        self.lineno = 1
        self.ignore = 0
        self.scanData()
        
    def scanData(self):
        #log.debug("scanData")
        f = open(self.filename)
        data = f.read()
        f.close
        
        # XXX
        # because of the many issues around comments in dtd files, and since
        # we're doing a sloppy parse, lets just get rid of all comments now.
        data = collector.res["COMMENT"].sub("", data)
        r = re.compile(r"--.*?--", re.S|re.U)
        data = r.sub("", data)
        
        data = self.applyEntities(data)
        
        self.l.settext(data)
            
        #res = []
        while 1:
            t, v = self.l.scan()
            #if t and v:
            #    log.debug("  lex symbol: %r %r", t, v)
            if t == self.l.eof:
                break
            #res.append((t, v))

    def applyEntities(self, text):
        # apply all existing entities to this text
        for e in self.dataset.entities.values():
            text = e.applyEntity(text)
        return text

    def incline(self, m):
        self.lineno = self.lineno + 1
        log.debug("line: %d",self.lineno)
        return ""

    # takes a block, and figures out how many lines it spans, to
    # keep lineno correct
    def doMultiLineBlock(self, m):
        #log.debug("block start at lineno %d",self.lineno)
        nl = collector.res["newlines"].findall(m.group(0))
        blockLen = len(nl)
        self.lineno = self.lineno + blockLen
        #log.debug("block had %d lines, lineno is %d", blockLen, self.lineno)
        return ""

    def doCommentBlock(self, m):
        self.lastComment = [m, self.lineno, 0]
        self.doMultiLineBlock(m)
        self.lastComment[2] = self.lineno
        log.debug("doCommentBlock %r", self.lastComment)
        return ""

    def section_start(self, m):
        if m.group('name') == 'IGNORE':
            self.ignore = 1
        return ""
    
    def section_end(self, m):
        self.ignore = 0
        return ""

    def entity(self, m):
        log.debug("ENTITY: [%r] on line %d", m.groupdict(), self.lineno)
        #print m.group(0)
        self.doMultiLineBlock(m)
        t = dtd_entity(m.groupdict())
        self.dataset.entities[m.group('name')] = t
        # if this is a peentity, we want to replace text with the entity content
        # we know it is a peentity if there the type is None
        if t.type is None:
            text = t.applyEntity(self.l.text[self.l.textindex:])
            self.l.text = self.l.text[:self.l.textindex-1] + text
        return ""
        
    def pereference(self, m):
        log.debug("PEReference: [%r] on line %d", m.groupdict(), self.lineno)
        # include the reference fileif any
        if self.ignore: return ""
        entity = self.dataset.entities[m.group('ref')]
        if entity.dtd:
            filename = relativize(os.path.dirname(self.filename),entity.dtd)

            if not os.path.exists(filename):
                if self.resolver:
                    filename = self.resolver.resolveURI(filename)
                    if not filename or not os.path.exists(filename):
                        filename = self.resolver.resolveExternalIdentifier(entity.entity, entity.dtd)

            if filename and os.path.exists(filename):
                #log.info("    parsing [%s]", filename)
                d = DTD(filename, self.dataset, self.resolver)
                text = self.applyEntities(self.l.text[self.l.textindex:])
                self.l.text = self.l.text[:self.l.textindex-1] + text
            else:
                log.warn("UNRESOLVED REFERENCE [%s][%s][%s][%s]", m.group('ref'), entity.type, entity.entity, filename)
        else:
            # XXX we need catalog support to do this
            log.warn("UNRESOLVED REFERENCE [%s][%s][%s]", m.group('ref'), entity.type, entity.entity)
        return ""
        
    def element(self, m):
        log.debug("ELEMENT: [%r] on line %d", m.groupdict(), self.lineno)
        self.doMultiLineBlock(m)
        if self.ignore: return ""
        d = m.groupdict()
        groupedNamesRe = collector.res["groupedNamesSplitter"]
        names = [n for n in groupedNamesRe.split(d['name']) if n]
        for name in names:
            if self.casename:
                name = name.lower()
            d['name'] = name
            t = dtd_element(d, self.casename)
            self.dataset.elements[name] = t
            self.dataset.elements_caseless[name.lower()] = t
            if name in self.dataset.attlist:
                # if attlist was defined before element, get the attributes now
                a = self.dataset.attlist[name]
                a.addAttributes(t)
        return ""

    def attlist(self, m):
        log.debug("ATTLIST: [%r] on line %d", m.groupdict(), self.lineno)
        self.doMultiLineBlock(m)
        if self.ignore: return ""
        d = m.groupdict()
        groupedNamesRe = collector.res["groupedNamesSplitter"]
        names = [n for n in groupedNamesRe.split(d['name']) if n]
        for name in names:
            if self.casename:
                name = name.lower()
            d['name'] = name
            if name in self.dataset.elements:
                el = self.dataset.elements[name]
            else:
                el = None
            t = dtd_attlist(d, el, self.casename)
            self.dataset.attlist[name] = t
        return ""

    #def entity_ref(self, m):
    #    log.debug("ENTITY REF: [%s] type [%s] decl [%s] dtd [%s] on line %d", m.group('name'), m.group('type'), self.lineno)
    #    self.doMultiLineBlock(m)
    #    return ""
        
if __name__=="__main__":
    logging.basicConfig()
    
    import sys
    if len(sys.argv)>1:
        filename = sys.argv[1]
        dtd = DTD(filename)
        dtd.dataset.dump(sys.stdout)
    else:
        # parse a single dtd
        basedir = os.path.dirname(os.path.dirname(os.getcwd()))
        filename = os.path.join(basedir, "contrib","catalogs","docbook44","docbookx.dtd")
        filename = os.path.join(basedir, "contrib","catalogs","sgml-lib","REC-xhtml11-20010531","xhtml11-flat.dtd")
        filename = os.path.join(basedir, "contrib","catalogs","sgml-lib","REC-html32-19970114","HTML32.dtd")
        filename = os.path.join(basedir, "contrib","catalogs","sgml-lib","IETF","HTML-2_0.dtd")
        filename = os.path.join(basedir, "contrib","catalogs","sgml-lib","REC-html401-19991224","strict.dtd")
        #filename = os.path.join(basedir, "contrib","catalogs","sgml-lib","ISO-HTML","15445.dtd")
        #dtd = DTD('/Users/shanec/src/dtd/dita/dtd/concept.dtd')
        #print dtd.dataset.root
        #print dtd.dataset.possible_children("related-links")
        dtd = DTD(filename, casename=True)
        print dtd.dataset.root
        #print dtd.dataset.possible_children("table")
        print dtd.dataset.possible_attributes("input")
        print dtd.dataset.possible_attribute_values("input", "type")
        #print dtd.dataset.possible_children("head")
        #dtd.dataset.dump(sys.stdout)
        #sys.exit(0)
