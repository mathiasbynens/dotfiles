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

"""Shared CIX tools for Code Intelligence

    CIX helpers for codeintel creation. Code Intelligence XML format. See:
        http://specs.tl.activestate.com/kd/kd-0100.html#xml-based-import-export-syntax-cix
"""

import os
import sys
import re
import shutil
from cStringIO import StringIO
import warnings

from ciElementTree import Element, ElementTree, SubElement
from codeintel2.util import parseDocSummary

# Dictionary of known js types and what they map to
known_javascript_types = {
    "object":       "Object",
    "obj":          "Object",
    "function":     "Function",
    "array":        "Array",
    "string":       "String",
    "text":         "String",
    "int":          "Number",
    "integer":      "Number",
    "number":       "Number",
    "numeric":      "Number",
    "decimal":      "Number",
    "short":        "Number",
    "unsigned short": "Number",
    "long":         "Number",
    "unsigned long":"Number",
    "float":        "Number",
    "bool":         "Boolean",
    "boolean":      "Boolean",
    "true":         "Boolean",
    "false":        "Boolean",
    "date":         "Date",
    "regexp":       "RegExp",
    # Dom elements
    "element":      "Element",
    "node":         "Node",
    "domnode":      "DOMNode",
    "domstring":    "DOMString",
    "widget":       "Widget",
    "domwidget":    "DOMWidget",
    "htmlelement":  "HTMLElement",
    "xmldocument":  "XMLDocument",
    "htmldocument": "HTMLDocument",
    # Special
    "xmlhttprequest": "XMLHttpRequest",
    "void":          "",
    # Mozilla special
    "UTF8String":    "String",
    "AString":       "String",
}

def standardizeJSType(vartype):
    """Return a standardized name for the given type if it is a known type.

    Example1: given vartype of "int", returns "Number"
    Example2: given vartype of "YAHOO.tool", returns "YAHOO.tool"
    """

    if vartype:
        typename = known_javascript_types.get(vartype.lower(), None)
        if typename is None:
            #print "Unknown type: %s" % (vartype)
            return vartype
        return typename

spacere = re.compile(r'\s+')
def condenseSpaces(s):
    """Remove any line enedings and condense multiple spaces"""

    s = s.replace("\n", " ")
    s = spacere.sub(' ', s)
    return s.strip()

def remove_directory(dirpath):
    """ Recursively remove the directory path given """

    if os.path.exists(dirpath):
        shutil.rmtree(dirpath, ignore_errors=True)

def getText(elem):
    """Return the internal text for the given ElementTree node"""

    l = []
    for element in elem.getiterator():
        if element.text:
            l.append(element.text)
        if element.tail:
            l.append(element.tail)
    return " ".join(l)

def getAllTextFromSubElements(elem, subelementname):
    descnodes = elem.findall(subelementname)
    if len(descnodes) == 1:
        return getText(descnodes[0])
    return None

_invalid_char_re = re.compile(u'[^\u0009\u000A\u000D\u0020-\uD7FF\uE000-\uFFFD]')
def strip_invalid_xml_chars(s):
    """Return the string with any invalid XML characters removed.

    The valid characters are listed here:
        http://www.w3.org/TR/REC-xml/#charsets
        #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | [#x10000-#x10FFFF]
    """
    return _invalid_char_re.sub("", s)

def setCixDoc(cixelement, doctext, parse=False):
    if parse:
        doclines = parseDocSummary(doctext.splitlines(0))
        doctext = "\n".join(doclines)
    elif sys.platform.startswith("win"):
        doctext = doctext.replace("\r\n", "\n")
    #TODO: By default clip doc content down to a smaller set -- just
    #      enough for a good calltip. By then also want an option to
    #      *not* clip, for use in documentation generation.
    #if len(doctext) > 1000:
    #    warnings.warn("doctext for cixelement: %r has length: %d" % (
    #                    cixelement.get("name"), len(doctext)))
    cixelement.attrib["doc"] = strip_invalid_xml_chars(doctext)

def setCixDocFromNodeChildren(cixelement, node, childnodename):
    doctext = getAllTextFromSubElements(node, childnodename)
    if doctext:
        setCixDoc(cixelement, condenseSpaces(doctext), parse=True)

def addCixArgument(cixelement, argname, argtype=None, doc=None):
    cixarg = SubElement(cixelement, "variable", ilk="argument", name=argname)
    if argtype:
        addCixType(cixarg, argtype)
    if doc:
        setCixDoc(cixarg, doc)
    return cixarg

def addCixReturns(cixelement, returntype=None):
    if returntype and returntype != "void":
        cixelement.attrib["returns"] = returntype

def addCixType(cixobject, vartype):
    if vartype:
        cixobject.attrib["citdl"] = vartype

def addCixAttribute(cixobject, attribute):
    attrs = cixobject.get("attributes")
    if attrs:
        sp = attrs.split()
        if attribute not in sp:
            attrs = "%s %s" % (attrs, attribute)
    else:
        attrs = attribute
    cixobject.attrib["attributes"] = attrs

def addClassRef(cixclass, name):
    refs = cixclass.get("classrefs", None)
    if refs:
        if name not in refs.split(" "):
            cixclass.attrib["classrefs"] = "%s %s" % (refs, name)
    else:
        cixclass.attrib["classrefs"] = "%s" % (name)

def addInterfaceRef(cixinterface, name):
    refs = cixinterface.get("interfacerefs", None)
    if refs:
        if name not in refs.split(" "):
            cixinterface.attrib["interfacerefs"] = "%s %s" % (refs, name)
    else:
        cixinterface.attrib["interfacerefs"] = "%s" % (name)

def setCixSignature(cixelement, signature):
    cixelement.attrib["signature"] = signature

def createCixVariable(cixobject, name, vartype=None, attributes=None):
    if attributes:
        v = SubElement(cixobject, "variable", name=name,
                       attributes=attributes)
    else:
        v = SubElement(cixobject, "variable", name=name)
    if vartype:
        addCixType(v, vartype)
    return v

def createCixFunction(cixmodule, name, attributes=None):
    if attributes:
        return SubElement(cixmodule, "scope", ilk="function", name=name,
                          attributes=attributes)
    else:
        return SubElement(cixmodule, "scope", ilk="function", name=name)

def createCixInterface(cixmodule, name):
    return SubElement(cixmodule, "scope", ilk="interface", name=name)

def createCixClass(cixmodule, name):
    return SubElement(cixmodule, "scope", ilk="class", name=name)

def createCixNamespace(cixmodule, name):
    return SubElement(cixmodule, "scope", ilk="namespace", name=name)

def createCixModule(cixfile, name, lang, src=None):
    if src is None:
        return SubElement(cixfile, "scope", ilk="blob", name=name, lang=lang)
    else:
        return SubElement(cixfile, "scope", ilk="blob", name=name, lang=lang, src=src)

def createOrFindCixModule(cixfile, name, lang, src=None):
    for module in cixfile.findall("./scope"):
        if module.get("ilk") == "blob" and module.get("name") == name and \
           module.get("lang") == lang:
            return module
    return createCixModule(cixfile, name, lang, src)

def createCixFile(cix, path, lang="JavaScript", mtime="1102379523"):
    return SubElement(cix, "file",
                        lang=lang,
                        #mtime=mtime,
                        path=path)

def createCixRoot(version="2.0", name=None, description=None):
    cixroot = Element("codeintel", version=version)
    if name is not None:
        cixroot.attrib["name"] = name
    if description is not None:
        cixroot.attrib["description"] = description
    return cixroot

# Add .text and .tail values to make the CIX output pretty. (Only have
# to avoid "doc" tags: they are the only ones with text content.)
def prettify(elem, level=0, indent='  ', youngestsibling=0):
    if elem and elem.tag != "doc":
        elem.text = '\n' + (indent*(level+1))
    for i in range(len(elem)):
        prettify(elem[i], level+1, indent, i==len(elem)-1)
    elem.tail = '\n' + (indent*(level-youngestsibling))

def get_cix_string(cix, prettyFormat=True):
    # Get the CIX.
    if prettyFormat:
        prettify(cix)
    cixstream = StringIO()
    cixtree = ElementTree(cix)
    cixstream.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    cixtree.write(cixstream)
    cixcontent = cixstream.getvalue()
    cixstream.close()
    return cixcontent

def outline_ci_elem(elem, _lvl=0, brief=False, doSort=False, includeLineNos=False):
    """Return an outline of the given codeintel tree element."""
    indent = '  '
    result = []

    def _dump(s):
        if includeLineNos:
            startline = elem.get("line")
            lineend = elem.get("lineend")
            line_str = ""
            if startline or lineend:
                line_str = " (%r-%r)" % (startline, lineend)
            result.append(indent*_lvl + s + line_str + '\n')
        else:
            result.append(indent*_lvl + s + '\n')

    if elem.tag == "codeintel":
        _lvl -= 1 # don't count this one
    elif brief:
        name = elem.get("name")
        if name:
            _dump(name)
    elif elem.tag == "file":
        lang = elem.get("lang")
        _dump("file %(path)s [%(lang)s]" % elem.attrib)
    elif elem.tag == "variable":
        if elem.get("ilk") == "argument":
            s = "arg "+elem.get("name") # skip?
        else:
            s = "var "+elem.get("name")
        if elem.get("citdl"):
            s += " [%s]" % elem.get("citdl")
        _dump(s)
    elif elem.tag == "scope" and elem.get("ilk") == "function" \
         and elem.get("signature"):
        _dump("function %s" % elem.get("signature").split('\n')[0])
    elif elem.tag == "scope" and elem.get("ilk") == "blob":
        lang = elem.get("lang")
        _dump("blob %(name)s [%(lang)s]" % elem.attrib)
    elif elem.tag == "scope" and elem.get("ilk") == "class" \
         and elem.get("classrefs"):
        _dump("%s %s(%s)" % (elem.get("ilk"), elem.get("name"),
                             ', '.join(elem.get("classrefs").split())))
    elif elem.tag == "scope":
        _dump("%s %s" % (elem.get("ilk"), elem.get("name")))
    elif elem.tag == "import":
        module = elem.get("module")
        symbol = elem.get("symbol")
        alias = elem.get("alias")
        value = "import '%s" % (module, )
        if symbol:
            value += ".%s" % (symbol, )
        value += "'"
        if alias:
            value +" as %r" % (alias, )
        _dump(value)
    else:
        raise ValueError("unknown tag: %r (%r)" % (elem.tag, elem))

    if doSort and hasattr(elem, "names") and elem.names:
        for name in sorted(elem.names.keys()):
            child = elem.names[name]
            result.append(outline_ci_elem(child, _lvl=_lvl+1,
                                          brief=brief, doSort=doSort,
                                          includeLineNos=includeLineNos))
    else:
        for child in elem:
            result.append(outline_ci_elem(child, _lvl=_lvl+1,
                                          brief=brief, doSort=doSort,
                                          includeLineNos=includeLineNos))
    return "".join(result)

def remove_cix_line_numbers_from_tree(tree):
    for node in tree.getiterator():
        node.attrib.pop("line", None)
        node.attrib.pop("lineend", None)
