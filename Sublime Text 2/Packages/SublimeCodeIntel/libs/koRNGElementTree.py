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
from xml.dom import pulldom
import logging
import re

log = logging.getLogger("koRNG")
log.setLevel(logging.DEBUG)

from elementtree import XMLTreeBuilder
try:
    import ciElementTree as ElementTree # effbot's C module
except ImportError:
    log.error("using element tree and not cElementTree, performace will suffer")
    import elementtree.ElementTree as ElementTree # effbot's pure Python module


class NamespaceParser(XMLTreeBuilder.FancyTreeBuilder):
    _qname = re.compile("{(.*?)}(.*)")
    def start(self, element):
        element.namespaces = self.namespaces[:]
        qn = self._qname.match(element.tag)
        element.ns = qn.group(1)
        element.tagName = qn.group(2)


class rng_base_dataset:
    def __init__(self):
        self.name = None
        self.elements = [] # root level elements
        self.attributes = []
        self.values = []
        self.refs = []

    def resolveRefs(self, dataset):
        for ref in self.refs[:]:
            if ref not in dataset.defs.keys():
                if ref not in dataset.ref_unresolved:
                    dataset.ref_unresolved[ref] = []
                dataset.ref_unresolved[ref].append(self)
                continue
            d = dataset.defs[ref]
            del self.refs[self.refs.index(ref)]
            if d.refs:
                d.resolveRefs(dataset)

            # grab what we care about from this definition
            self.attributes += [a for a in d.attributes if a.name]
            self.elements += [e for e in d.elements if e.name]
            self.values += d.values

class rng_dataset(rng_base_dataset):
    def __init__(self):
        rng_base_dataset.__init__(self)
        self.name = "root"
        self.all_elements = {}
        self.elements_caseless = {}
        self.defs = {}
        self.namespace = ""
        self.datatypeLibrary = ""
        self.xmlns = ""

        self.ref_resolving = {}
        self.ref_unresolved = {}

    def resolveRefs(self, dataset=None):
        if not dataset:
            dataset = self
        rng_base_dataset.resolveRefs(self, dataset)

        for d in self.defs.values():
            d.resolveRefs(dataset)

        for e in self.all_elements.values():
            e.resolveRefs(dataset)

        for a in self.attributes[:]:
            a.resolveRefs(dataset)
            
        self.resolveUnresolvedRefs()

    def resolveCircularRefs(self):
        for ref in self.ref_circular.keys()[:]:
            #print "resolving earlier circular reference %s"%ref
            el = self.ref_circular[ref]
            del self.ref_circular[ref]
            for e in el:
                e.resolveRefs(self)

    def resolveUnresolvedRefs(self):
        for ref in self.ref_unresolved.keys()[:]:
            print "resolving earlier unresolved reference %s"%ref
            el = self.ref_unresolved[ref]
            del self.ref_unresolved[ref]
            for e in el:
                e.resolveRefs(self)

    def element_info(self, element_name):
        name = element_name.lower()
        if name in self.elements_caseless:
            return self.elements_caseless[name]
        return None

    def possible_children(self, element_name=None):
        if not element_name:
            return [el.name for el in self.elements]
        else:
            name = element_name.lower()
            if name not in self.elements_caseless:
                return []
            return [el.name for el in self.elements_caseless[name].elements]

    def possible_attributes(self, element_name):
        name = element_name.lower()
        if name in self.elements_caseless:
            return [a.name for a in self.elements_caseless[name].attributes]
        return []

    def possible_attribute_values(self, element_name, attribute_name):
        el = self.element_info(element_name)
        if el:
            for a in el.attributes:
                if attribute_name == a.name:
                    return a.values
        return []
    
    def all_element_types(self):
        return self.all_elements.keys()


    def dump(self, stream):
        print "RNG NS: %s" % self.xmlns
        print "Namespace: %s" % self.namespace
        print "datatypeLibrary: %s" % self.datatypeLibrary
        print "-"*60
        for e in self.elements:
            e.dump(stream)
        print "-"*60
        for e in self.all_elements.values():
            e.dump(stream)
        print "-"*60

class rng_node_info(rng_base_dataset):
    def __init__(self, node):
        rng_base_dataset.__init__(self)
        self.name = node.attrib.get("name")
        self._node = node

class element_info(rng_node_info):
    def dump(self, stream):
        attrs = []
        for n,v in self._node.attrib.items():
            attrs.append('%s="%s"' % (n, v))
        stream.write("<element %s>\n" % ' '.join(attrs))
        names = [el.name for el in self.elements]
        stream.write("    children %r\n" % names)
        for attr in self.attributes:
            attr.dump(stream)
        stream.write("    refs remaining: %r\n"%self.refs)

class attribute_info(rng_node_info):
    def dump(self, stream):
        stream.write("    attr %s %r\n" % (self.name, self.values))

class definition(rng_node_info):
    def dump(self, stream):
            stream.write("definition %s has %d refs\n" % (self.name, len(self.refs)))
            names = [el.name for el in self.elements]
            stream.write("   has %d elements %r\n" % (len(self.elements), names))
            names = [el.name for el in self.attributes]
            stream.write("   has %d attributes %r\n" % (len(self.attributes), names))
            stream.write("   has %d values %r\n" % (len(self.values), self.values))

    def resolveRefs(self, dataset):
        for e in self.elements[:]:
            e.resolveRefs(dataset)
        for a in self.attributes[:]:
            a.resolveRefs(dataset)
        rng_node_info.resolveRefs(self, dataset)

class rng:
    def __init__(self, filename, dataset=None):
        if dataset is None:
            dataset = rng_dataset()
        self.dataset = dataset
        self._element_stack = [self.dataset]
        self._includes = []
        self.filename = filename
        self.parse()

    def parse(self):
        self.tree = ElementTree.parse(self.filename, NamespaceParser())
        self.root = self.tree.getroot()
        if self.root.tagName != "grammar":
            raise "Invalid RNG file [%s] root tag [%s]" % (self.filename, self.root.tagName)
        self.parent_map = dict((c, p) for p in self.tree.getiterator() for c in p)
        self.parseNode(self.root)
        self.dataset.resolveRefs()

    def parseNode(self, node):
        methodName = "handle_%s" % node.tagName
        #print methodName
        if hasattr(self, methodName):
            fn = getattr(self, methodName)
            fn(node)
        for child in list(node):
            #print "parsing child %s"%child.tagName
            self.parseNode(child)
        methodName = "handle_%s_end" % node.tagName
        #print methodName
        if hasattr(self, methodName):
            fn = getattr(self, methodName)
            fn(node)
            
    def handle_include(self, node):
        # XXX handle relative dirs
        path = node.attrib.get("href")
        if not os.path.exists(path):
            path = os.path.join(os.path.dirname(self.filename), path)
        #print "file included [%s]"%path
        rng(path, self.dataset)
        
    def handle_grammar(self, node):
        if not self.dataset.namespace:
            self.dataset.xmlns = node.attrib.get('xmlns')
            self.dataset.namespace = node.attrib.get('ns')
            self.dataset.datatypeLibrary = node.attrib.get('datatypeLibrary')

    #def handle_start(self, node):
    #    self._element_stack.append(self)
    #def handle_start_end(self, node):
    #    self._element_stack.pop()

    def handle_attribute(self, node):
        self._element_stack.append(attribute_info(node))

    def handle_attribute_end(self, node):
        # attributes get added to the last item in the element stack
        attr = self._element_stack.pop()
        el = self._element_stack[-1]
        el.attributes.append(attr)

    def handle_name_end(self, node):
        # is the parent node an attribute?
        parent = self.parent_map[node]
        if node.text and parent.tagName == "attribute":
            #print "name value...%r"%node.text
            e = self._element_stack[-1]
            e.name = node.text
            self.dataset.all_elements[node.text] = e
            self.dataset.elements_caseless[node.text.lower()] = e

    def handle_element(self, node):
        #print "handle_element %s" %node.attrib.get("name")
        e = element_info(node)
        if e.name:
            self.dataset.all_elements[e.name] = e
            self.dataset.elements_caseless[e.name.lower()] = e
        self._element_stack.append(e)
    
    def handle_element_end(self, node):
        #print "handle_element_end %s" %node.attrib.get("name")
        el = self._element_stack.pop()
        self._element_stack[-1].elements.append(el)

    def handle_define(self, node):
        d = definition(node)
        #print "definition: %s" % d.name
        self.dataset.defs[d.name] = d
        self._element_stack.append(d)

    def handle_define_end(self, node):
        d = self._element_stack.pop()

    def handle_ref(self, node):
        self._element_stack[-1].refs.append(node.attrib.get("name"))

    def handle_value(self, node):
        self._element_stack[-1].values.append(node.text)


    #def handle_zeroOrMore(self, node):
    #    pass
    #def handle_choice(self, node):
    #    pass
    #def handle_interleave(self, node):
    #    pass
    #def handle_mixed(self, node):
    #    pass
    #def handle_empty(self, node):
    #    pass
    #def handle_notAllowed(self, node):
    #    pass
    #def handle_group(self, node):
    #    pass
    #def handle_optional(self, node):
    #    pass
    #def handle_text(self, node):
    #    pass
    #def handle_div(self, node):
    #    pass
    #def handle_list(self, node):
    #    pass
    #def handle_data(self, node):
    #    pass
    #def handle_except(self, node):
    #    pass
    #def handle_oneOrMore(self, node):
    #    pass
    #def handle_param(self, node):
    #    pass


if __name__=="__main__":
    import sys
    if len(sys.argv)>1:
        filename = sys.argv[1]
        machine = rng(filename)
    else:
        import os, sys
        # we're  in src/python-sitelib, we need the contrib dir
        basedir = os.path.dirname(os.path.dirname(os.getcwd()))
        filename = os.path.join(basedir, "contrib","catalogs","rng","xslt.rng")
        machine = rng(filename)
        #assert "template" in machine.possible_children("stylesheet")
        #assert "text" in machine.all_element_types()
        #assert machine.possible_children("text")==[]
        #assert machine.possible_children("garbage")==[]
        #assert "version" in machine.possible_attributes("transform")
        #assert machine.possible_attributes("garbage")==[]
        #assert "upper-first" in machine.possible_attribute_values("sort", "case-order")
        #assert machine.possible_attribute_values("garbage", "garbage") == []
        #assert machine.possible_attribute_values("garbate", "case-order") == []
        ## filename = "..\\languages\\xhtml\\xhtml-state-machine.xml"
        ## machine = state_machine_info(filename)
        ## for element in machine.all_element_types():
            ## if element!="#LITERAL":
                ## assert "lang" in machine.possible_attributes(element), "no lang on %s" % element

    machine.dataset.dump(sys.stdout)
    #machine.dataset.element_info("tr").dump(sys.stdout)
