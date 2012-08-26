#!/usr/bin/env python
# Copyright (c) 2004-2006 ActiveState Software Inc.
#
# Contributors:
#   Trent Mick (TrentM@ActiveState.com)

"""
    pythoncile - a Code Intelligence Language Engine for the Python language

    Module Usage:
        from pythoncile import scan
        mtime = os.stat("foo.py")[stat.ST_MTIME]
        content = open("foo.py", "r").read()
        scan(content, "foo.py", mtime=mtime)
    
    Command-line Usage:
        pythoncile.py [<options>...] [<Python files>...]

    Options:
        -h, --help          dump this help and exit
        -V, --version       dump this script's version and exit
        -v, --verbose       verbose output, use twice for more verbose output
        -f, --filename <path>   specify the filename of the file content
                            passed in on stdin, this is used for the "path"
                            attribute of the emitted <file> tag.
        --md5=<string>      md5 hash for the input
        --mtime=<secs>      modification time for output info, in #secs since
                            1/1/70.
        -L, --language <name>
                            the language of the file being scanned
        -c, --clock         print timing info for scans (CIX is not printed)

    One or more Python files can be specified as arguments or content can be
    passed in on stdin. A directory can also be specified, in which case
    all .py files in that directory are scanned.

    This is a Language Engine for the Code Intelligence (codeintel) system.
    Code Intelligence XML format. See:
        http://specs.activestate.com/Komodo_3.0/func/code_intelligence.html
    
    The command-line interface will return non-zero iff the scan failed.
"""
# Dev Notes:
# <none>
#
#TODO:
# - type inferencing: asserts
# - type inferencing: calls to isinstance
# - special handling for None may be required
# - Comments and doc strings. What format?
#   - JavaDoc - type hard to parse and not reliable
#     (http://java.sun.com/j2se/javadoc/writingdoccomments/).
#   - PHPDoc? Possibly, but not that rigorous.
#   - Grouch (http://www.mems-exchange.org/software/grouch/) -- dunno yet.
#     - Don't like requirement for "Instance attributes:" landmark in doc
#       strings.
#     - This can't be a full solution because the requirement to repeat
#       the argument name doesn't "fit" with having a near-by comment when
#       variable is declared.
#     - Two space indent is quite rigid
#     - Only allowing attribute description on the next line is limiting.
#     - Seems focussed just on class attributes rather than function
#       arguments.
#   - Perhaps what PerlCOM POD markup uses?
#   - Home grown? My own style? Dunno
# - make type inferencing optional (because it will probably take a long
#   time to generate), this is tricky though b/c should the CodeIntel system
#   re-scan a file after "I want type inferencing now" is turned on? Hmmm.
# - [lower priority] handle staticmethod(methname) and
#   classmethod(methname). This means having to delay emitting XML until
#   end of class scope and adding .visitCallFunc().
# - [lower priority] look for associated comments for variable
#   declarations (as per VS.NET's spec, c.f. "Supplying Code Comments" in
#   the VS.NET user docs)


import os
import sys
import getopt
from hashlib import md5
import re
import logging
import pprint
import glob
import time
import stat
import types
from cStringIO import StringIO
from functools import partial

# this particular ET is different from xml.etree and is expected
# to be returned from scan_et() by the clients of this module
import ciElementTree as et

import compiler
from compiler import ast
from compiler.visitor import dumpNode, ExampleASTVisitor
import parser

from codeintel2.common import CILEError
from codeintel2 import util
from codeintel2 import tdparser

#---- exceptions

class PythonCILEError(CILEError):
    pass



#---- global data

_version_ = (0, 3, 0)
log = logging.getLogger("pythoncile")
#log.setLevel(logging.DEBUG)
util.makePerformantLogger(log)

_gClockIt = 0   # if true then we are gathering timing data
_gClock = None  # if gathering timing data this is set to time retrieval fn
_gStartTime = None   # start time of current file being scanned



#---- internal routines and classes

def _isclass(namespace):
    return (len(namespace["types"]) == 1
            and "class" in namespace["types"])

def _isfunction(namespace):
    return (len(namespace["types"]) == 1
            and "function" in namespace["types"])

def getAttrStr(attrs):
    """Construct an XML-safe attribute string from the given attributes
    
        "attrs" is a dictionary of attributes
    
    The returned attribute string includes a leading space, if necessary,
    so it is safe to use the string right after a tag name. Any Unicode
    attributes will be encoded into UTF8 encoding as part of this process.
    """
    from xml.sax.saxutils import quoteattr
    s = ''
    for attr, value in attrs.items():
        if not isinstance(value, basestring):
            value = str(value)
        elif isinstance(value, unicode):
            value = value.encode("utf-8")
        s += ' %s=%s' % (attr, quoteattr(value))
    return s

# match 0x00-0x1f except TAB(0x09), LF(0x0A), and CR(0x0D)
_encre = re.compile('([\x00-\x08\x0b\x0c\x0e-\x1f])')

# XXX: this is not used anywhere, is it needed at all?
if sys.version_info >= (2, 3):
    charrefreplace = 'xmlcharrefreplace'
else:
    # Python 2.2 doesn't have 'xmlcharrefreplace'. Fallback to a
    # literal '?' -- this is better than failing outright.
    charrefreplace = 'replace'

def xmlencode(s):
    """Encode the given string for inclusion in a UTF-8 XML document.
    
    Note: s must *not* be Unicode, it must be encoded before being passed in.

    Specifically, illegal or unpresentable characters are encoded as
    XML character entities.
    """
    # As defined in the XML spec some of the character from 0x00 to 0x19
    # are not allowed in well-formed XML. We replace those with entity
    # references here.
    #   http://www.w3.org/TR/2000/REC-xml-20001006#charsets
    #
    # Dev Notes:
    # - It would be nice if Python has a codec for this. Perhaps we
    #   should write one.
    # - Eric, at one point, had this change to '_xmlencode' for rubycile:
    #    p4 diff2 -du \
    #        //depot/main/Apps/Komodo-devel/src/codeintel/ruby/rubycile.py#7 \
    #        //depot/main/Apps/Komodo-devel/src/codeintel/ruby/rubycile.py#8
    #   but:
    #        My guess is that there was a bug here, and explicitly
    #        utf-8-encoding non-ascii characters fixed it. This was a year
    #        ago, and I don't recall what I mean by "avoid shuffling the data
    #        around", but it must be related to something I observed without
    #        that code.
    
    # replace with XML decimal char entity, e.g. '&#7;'
    return _encre.sub(lambda m: '&#%d;' % ord(m.group(1)), s)

def cdataescape(s):
    """Return the string escaped for inclusion in an XML CDATA section.
    
    Note: Any Unicode will be encoded to UTF8 encoding as part of this process.

    A CDATA section is terminated with ']]>', therefore this token in the
    content must be escaped. To my knowledge the XML spec does not define
    how to do that. My chosen escape is (courteousy of EricP) is to split
    that token into multiple CDATA sections, so that, for example:
    
        blah...]]>...blah
    
    becomes:
    
        blah...]]]]><![CDATA[>...blah
    
    and the resulting content should be copacetic:
    
        <b><![CDATA[blah...]]]]><![CDATA[>...blah]]></b>
    """
    if isinstance(s, unicode):
        s = s.encode("utf-8")
    parts = s.split("]]>")
    return "]]]]><![CDATA[>".join(parts)

def _unistr(x):
    if isinstance(x, unicode):
        return x
    elif isinstance(x, str):
        return x.decode('utf8')
    else:
        return unicode(x)

def _et_attrs(attrs):
    return dict((_unistr(k), xmlencode(_unistr(v))) for k, v in attrs.items()
                                                    if v is not None)

def _et_data(data):
    return xmlencode(_unistr(data))
    
def _node_attrs(node, **kw):
    return dict(name=node["name"],
                line=node.get("line"),
                doc=node.get("doc"),
                attributes=node.get("attributes") or None,
                **kw)

def _node_citdl(node):
    max_type = None
    max_score = -1
    #'guesses' is a types dict: {<type guess>: <score>, ...}
    guesses = node.get("types", {})
    for type, score in guesses.items():
        if ' ' in type:
            #XXX Drop the <start-scope> part of CITDL for now.
            type = type.split(None,1)[0]
        # Don't emit None types, it does not help us. Fix for bug:
        #  http://bugs.activestate.com/show_bug.cgi?id=71989
        if type != "None":
            if score > max_score:
                max_type = type
                max_score = score
    return max_type
    

class AST2CIXVisitor:
    """Generate Code Intelligence XML (CIX) from walking a Python AST tree.
    
    This just generates the CIX content _inside_ of the <file/> tag. The
    prefix and suffix have to be added separately.

    Note: All node text elements are encoded in UTF-8 format by the Python AST
          tree processing, no matter what encoding is used for the file's
          original content. The generated CIX XML will also be UTF-8 encoded.
    """
    DEBUG = 0
    def __init__(self, moduleName=None, content=None, lang="Python"):
        self.lang = lang
        if self.DEBUG is None:
            self.DEBUG = log.isEnabledFor(logging.DEBUG)
        self.moduleName = moduleName
        if content:
            self.lines = content.splitlines(0)
        else:
            self.lines = None
        # Symbol Tables (dicts) are built up for each scope. The namespace
        # stack to the global-level is maintain in self.nsstack.
        self.st = { # the main module symbol table
            # <scope name>: <namespace dict>
        }
        self.nsstack = []
        self.cix = et.TreeBuilder()

    def emit_start(self, s, attrs={}):
        self.cix.start(s, _et_attrs(attrs))

    def emit_data(self, data):
        self.cix.data(_et_data(data))

    def emit_end(self, s):
        self.cix.end(s)

    def emit_tag(self, s, attrs={}, data=None):
        self.emit_start(s, _et_attrs(attrs))
        if data is not None:
            self.emit_data(data)
        self.emit_end(s)

    def cix_module(self, node):
        """Emit CIX for the given module namespace."""
        #log.debug("cix_module(%s, level=%r)", '.'.join(node["nspath"]), level)
        assert len(node["types"]) == 1 and "module" in node["types"]
        attrs = _node_attrs(node, lang=self.lang, ilk="blob")
        module = self.emit_start('scope', attrs)
        for import_ in node.get("imports", []):
            self.cix_import(import_)
        self.cix_symbols(node["symbols"])
        self.emit_end('scope')

    def cix_import(self, node):
        #log.debug("cix_import(%s, level=%r)", node["module"], level)
        attrs = node
        self.emit_tag('import', attrs)

    def cix_symbols(self, node, parentIsClass=0):
        # Sort variables by line order. This provide the most naturally
        # readable comparison of document with its associate CIX content.
        vars = sorted(node.values(), key=lambda v: v.get("line"))
        for var in vars:
            self.cix_symbol(var, parentIsClass)

    def cix_symbol(self, node, parentIsClass=0):
        if _isclass(node):
            self.cix_class(node)
        elif _isfunction(node):
            self.cix_function(node)
        else:
            self.cix_variable(node, parentIsClass)

    def cix_variable(self, node, parentIsClass=0):
        #log.debug("cix_variable(%s, level=%r, parentIsClass=%r)",
        #          '.'.join(node["nspath"]), level, parentIsClass)
        attrs = _node_attrs(node, citdl=_node_citdl(node))
        if parentIsClass and "is-class-var" not in node:
            # Special CodeIntel <variable> attribute to distinguish from the
            # usual class variables.
            if attrs["attributes"]:
                attrs["attributes"] += " __instancevar__"
            else:
                attrs["attributes"] = "__instancevar__"
        self.emit_tag('variable', attrs)

    def cix_class(self, node):
        #log.debug("cix_class(%s, level=%r)", '.'.join(node["nspath"]), level)

        if node["classrefs"]:
            citdls = (t for t in (_node_citdl(n) for n in node["classrefs"])
                        if t is not None)
            classrefs = " ".join(citdls)
        else:
            classrefs = None

        attrs = _node_attrs(node,
                            lineend=node.get("lineend"),
                            signature=node.get("signature"),
                            ilk="class",
                            classrefs=classrefs)

        self.emit_start('scope', attrs)

        for import_ in node.get("imports", []):
            self.cix_import(import_)

        self.cix_symbols(node["symbols"], parentIsClass=1)
        
        self.emit_end('scope')

    def cix_argument(self, node):
        #log.debug("cix_argument(%s, level=%r)", '.'.join(node["nspath"]), level)
        attrs = _node_attrs(node, citdl=_node_citdl(node), ilk="argument")
        self.emit_tag('variable', attrs)

    def cix_function(self, node):
        #log.debug("cix_function(%s, level=%r)", '.'.join(node["nspath"]), level)
        # Determine the best return type.
        best_citdl = None
        max_count = 0
        for citdl, count in node["returns"].items():
            if count > max_count:
                best_citdl = citdl

        attrs = _node_attrs(node,
                            lineend=node.get("lineend"),
                            returns=best_citdl,
                            signature=node.get("signature"),
                            ilk="function")

        self.emit_start("scope", attrs)

        for import_ in node.get("imports", []):
            self.cix_import(import_)
        argNames = []
        for arg in node["arguments"]:
            argNames.append(arg["name"])
            self.cix_argument(arg)
        symbols = {} # don't re-emit the function arguments
        for symbolName, symbol in node["symbols"].items():
            if symbolName not in argNames:
                symbols[symbolName] = symbol
        self.cix_symbols(symbols)
        #XXX <returns/> if one is defined
        self.emit_end('scope')

    def getCIX(self, path):
        """Return CIX content for parsed data."""
        log.debug("getCIX")
        moduleNS = self.st[()]
        self.emit_start('file', dict(lang=self.lang, path=path))
        self.cix_module(moduleNS)
        self.emit_end('file')
        file = self.cix.close()
        return file

    def visitModule(self, node):
        log.info("visitModule")
        nspath = ()
        namespace = {"name": self.moduleName,
                     "nspath": nspath,
                     "types": {"module": 1},
                     "symbols": {}}
        if node.doc:
            summarylines = util.parseDocSummary(node.doc.splitlines(0))
            namespace["doc"] = "\n".join(summarylines)
            
        if node.lineno:
            namespace["line"] = node.lineno

        self.st[nspath] = namespace
        self.nsstack.append(namespace)
        self.visit(node.node)
        self.nsstack.pop()

    def visitReturn(self, node):
        log.info("visitReturn: %r", node.value)
        citdl_types = self._guessTypes(node.value)
        for citdl in citdl_types:
            if citdl:
                citdl = citdl.split(None, 1)[0]
                if citdl and citdl not in ("None", "NoneType"):
                    if citdl in ("False", "True"):
                        citdl = "bool"
                    func_node = self.nsstack[-1]
                    t = func_node["returns"]
                    t[citdl] = t.get(citdl, 0) + 1

    def visitClass(self, node):
        log.info("visitClass:%d: %r", node.lineno,
                 self.lines and self.lines[node.lineno-1])
        locals = self.nsstack[-1]
        name = node.name
        nspath = locals["nspath"] + (name,)
        namespace = {
            "nspath": nspath,
            "name": name,
            "types": {"class": 1},
            #XXX Example of a base class that might surprise: the
            #    __metaclass__ class in
            #    c:\python22\lib\site-packages\ctypes\com\automation.py
            #    Should this be self._getCITDLExprRepr()???
            "classrefs": [],
            "symbols": {},
        }
        namespace["declaration"] = namespace

        if node.lineno: namespace["line"] = node.lineno
        lastNode = node
        while lastNode.getChildNodes():
            lastNode = lastNode.getChildNodes()[-1]
        if lastNode.lineno: namespace["lineend"] = lastNode.lineno

        attributes = []
        if name.startswith("__") and name.endswith("__"):
            pass
        elif name.startswith("__"):
            attributes.append("private")
        elif name.startswith("_"):
            attributes.append("protected")
        namespace["attributes"] = ' '.join(attributes)

        if node.bases:
            for baseNode in node.bases:
                baseName = self._getExprRepr(baseNode)
                classref = {"name": baseName, "types": {}}
                for t in self._guessTypes(baseNode):
                    if t not in classref["types"]:
                        classref["types"][t] = 0
                    classref["types"][t] += 1
                namespace["classrefs"].append(classref)
        if node.doc:
            siglines, desclines = util.parsePyFuncDoc(node.doc)
            if siglines:
                namespace["signature"] = "\n".join(siglines)
            if desclines:
                namespace["doc"] = "\n".join(desclines)
        self.st[nspath] = locals["symbols"][name] = namespace

        self.nsstack.append(namespace)
        self.visit(node.code)
        self.nsstack.pop()

    def visitFunction(self, node):
        log.info("visitFunction:%d: %r", node.lineno,
                 self.lines and self.lines[node.lineno-1])
        parent = self.nsstack[-1]
        parentIsClass = _isclass(parent)
        
        namespace = {
            "types": {"function": 1},
            "returns": {},
            "arguments": [],
            "symbols": {},
        }
        
        namespace["declaration"] = namespace
        if node.lineno: namespace["line"] = node.lineno
        lastNode = node
        while lastNode.getChildNodes():
            lastNode = lastNode.getChildNodes()[-1]
        if lastNode.lineno: namespace["lineend"] = lastNode.lineno

        name = node.name
        
        # Determine attributes
        attributes = []
        if name.startswith("__") and name.endswith("__"):
            pass
        elif name.startswith("__"):
            attributes.append("private")
        elif name.startswith("_"):
            attributes.append("protected")
        if name == "__init__" and parentIsClass:
            attributes.append("__ctor__")
            
        # process decorators
        prop_var = None
        if node.decorators:
            for deco in node.decorators.nodes:
                prop_mode = None
                if hasattr(deco, 'name') and deco.name == 'property':
                    prop_mode = 'getter'
                elif hasattr(deco, 'attrname') and deco.attrname in ('getter',
                                                                     'setter',
                                                                     'deleter'):
                    prop_mode = deco.attrname
                    
                if prop_mode:
                    if prop_mode == 'getter':
                        # it's a getter, create a pseudo-var
                        prop_var = parent["symbols"].get(name, None)
                        if prop_var is None:
                            prop_var = dict(name=name,
                                            nspath=parent["nspath"] + (name,),
                                            doc=None,
                                            types={},
                                            symbols={})
                            var_attrs = ['property']
                            if name.startswith("__") and name.endswith("__"):
                                pass
                            elif name.startswith("__"):
                                var_attrs.append("private")
                            elif name.startswith("_"):
                                var_attrs.append("protected")
                            prop_var["attributes"] = ' '.join(var_attrs)
                            prop_var["declaration"] = prop_var
                            parent["symbols"][name] = prop_var
                        
                        if not "is-class-var" in prop_var:
                            prop_var["is-class-var"] = 1
                            
                    # hide the function  
                    attributes += ['__hidden__']
                    name += " (property %s)" % prop_mode
                    
                    # only one property decorator makes sense
                    break
            
        namespace["attributes"] = ' '.join(attributes)
        
        if parentIsClass and name == "__init__":
            fallbackSig = parent["name"]
        else:
            fallbackSig = name
        namespace["name"] = name
        
        nspath = parent["nspath"] + (name,)
        namespace["nspath"] = nspath
        
        # Handle arguments. The format of the relevant Function attributes
        # makes this a little bit of pain.
        defaultArgsBaseIndex = len(node.argnames) - len(node.defaults)
        if node.kwargs:
            defaultArgsBaseIndex -= 1
            if node.varargs:
                defaultArgsBaseIndex -= 1
                varargsIndex = len(node.argnames)-2
            else:
                varargsIndex = None
            kwargsIndex = len(node.argnames)-1
        elif node.varargs:
            defaultArgsBaseIndex -= 1
            varargsIndex = len(node.argnames)-1
            kwargsIndex = None
        else:
            varargsIndex = kwargsIndex = None
        sigArgs = []
        for i in range(len(node.argnames)):
            argOrArgTuple = node.argnames[i]

            if isinstance(argOrArgTuple, tuple):
                # If it is a tuple arg with a default assignment, then we
                # drop that info (except for the sig): too hard and too rare
                # to bother with.
                sigArg = str(argOrArgTuple)
                if i >= defaultArgsBaseIndex:
                    defaultNode = node.defaults[i-defaultArgsBaseIndex]
                    try:
                        default = self._getExprRepr(defaultNode)
                    except PythonCILEError, ex:
                        raise PythonCILEError("unexpected default argument node "
                                              "type for Function '%s': %s"
                                              % (node.name, ex))
                    sigArg += "="+default
                sigArgs.append(sigArg)
                arguments = []
                for argName in argOrArgTuple:
                    argument = {"name": argName,
                                "nspath": nspath+(argName,),
                                "doc": None,
                                "types": {},
                                "symbols": {}}
                    arguments.append(argument)
            else:
                argName = argOrArgTuple
                argument = {"name": argName,
                            "nspath": nspath+(argName,),
                            "doc": None,
                            "types": {},
                            "symbols": {}}
                if i == kwargsIndex:
                    argument["attributes"] = "kwargs"
                    sigArgs.append("**"+argName)
                elif i == varargsIndex:
                    argument["attributes"] = "varargs"
                    sigArgs.append("*"+argName)
                elif i >= defaultArgsBaseIndex:
                    defaultNode = node.defaults[i-defaultArgsBaseIndex]
                    try:
                        argument["default"] = self._getExprRepr(defaultNode)
                    except PythonCILEError, ex:
                        raise PythonCILEError("unexpected default argument node "
                                              "type for Function '%s': %s"
                                              % (node.name, ex))
                    sigArgs.append(argName+'='+argument["default"])
                    for t in self._guessTypes(defaultNode):
                        log.info("guessed type: %s ::= %s", argName, t)
                        if t not in argument["types"]:
                            argument["types"][t] = 0
                        argument["types"][t] += 1
                else:
                    sigArgs.append(argName)

                if i == 0 and parentIsClass:
                    # If this is a class method, then the first arg is the class
                    # instance.
                    className = self.nsstack[-1]["nspath"][-1]
                    argument["types"][className] = 1
                    argument["declaration"] = self.nsstack[-1]
                arguments = [argument]
                
            for argument in arguments:
                if "declaration" not in argument:
                    argument["declaration"] = argument # namespace dict of the declaration
                namespace["arguments"].append(argument)
                namespace["symbols"][argument["name"]] = argument
        # Drop first "self" argument from class method signatures.
        # - This is a little bit of a compromise as the "self" argument
        #   should *sometimes* be included in a method's call signature.
        if _isclass(parent) and sigArgs:
            del sigArgs[0]
        fallbackSig += "(%s)" % (", ".join(sigArgs))
        if node.doc:
            siglines, desclines = util.parsePyFuncDoc(node.doc, [fallbackSig])
            namespace["signature"] = "\n".join(siglines)
            if desclines:
                namespace["doc"] = "\n".join(desclines)
        else:
            namespace["signature"] = fallbackSig
        self.st[nspath] = parent["symbols"][name] = namespace

        self.nsstack.append(namespace)
        self.visit(node.code)
        self.nsstack.pop()
        
        if prop_var:
            # this is a property getter function,
            # copy its return types to the corresponding property variable...
            var_types = prop_var["types"]
            for t in namespace["returns"]:
                if t not in var_types:
                    var_types[t] = 0
                else:
                    var_types[t] += 1
            # ... as well as its line number
            if "line" in namespace:
                prop_var["line"] = namespace["line"]

    def visitImport(self, node):
        log.info("visitImport:%d: %r", node.lineno,
                 self.lines and self.lines[node.lineno-1])
        imports = self.nsstack[-1].setdefault("imports", [])
        for module, alias in node.names:
            import_ = {"module": module}
            if node.lineno: import_["line"] = node.lineno
            if alias: import_["alias"] = alias
            imports.append(import_)

    def visitFrom(self, node):
        log.info("visitFrom:%d: %r", node.lineno,
                 self.lines and self.lines[node.lineno-1])
        imports = self.nsstack[-1].setdefault("imports", [])
        module = node.modname
        if node.level > 0:
            module = ("." * node.level) + module
        for symbol, alias in node.names:
            import_ = {"module": module, "symbol": symbol}
            if node.lineno:
                import_["line"] = node.lineno
            if alias:
                import_["alias"] = alias
            imports.append(import_)

    #XXX
    #def visitReturn(self, node):
    #    # set __rettypes__ on Functions
    #    pass
    #def visitGlobal(self, node):
    #    # note for future visitAssign to control namespace
    #    pass
    #def visitYield(self, node):
    #    # modify the Function into a generator??? what are the implications?
    #    pass
    #def visitAssert(self, node):
    #    # support the assert hints that Wing does
    #    pass

    def _assignVariable(self, varName, namespace, rhsNode, line,
                        isClassVar=0):
        """Handle a simple variable name assignment.

            "varName" is the variable name being assign to.
            "namespace" is the namespace dict to which to assign the variable.
            "rhsNode" is the ast.Node of the right-hand side of the
                assignment.
            "line" is the line number on which the variable is being assigned.
            "isClassVar" (optional) is a boolean indicating if this var is
                a class variable, as opposed to an instance variable
        """
        log.debug("_assignVariable(varName=%r, namespace %s, rhsNode=%r, "
                  "line, isClassVar=%r)", varName,
                  '.'.join(namespace["nspath"]), rhsNode, isClassVar)
        variable = namespace["symbols"].get(varName, None)
        
        new_var = False
        if variable is None:
            new_var = True
            variable = {"name": varName,
                        "nspath": namespace["nspath"]+(varName,),
                        # Could try to parse documentation from a near-by
                        # string.
                        "doc": None,
                        # 'types' is a dict mapping a type name to the number
                        # of times this was guessed as the variable type.
                        "types": {},
                        "symbols": {}}
            # Determine attributes
            attributes = []
            if varName.startswith("__") and varName.endswith("__"):
                pass
            elif varName.startswith("__"):
                attributes.append("private")
            elif varName.startswith("_"):
                attributes.append("protected")
            variable["attributes"] = ' '.join(attributes)

            variable["declaration"] = variable
            if line: variable["line"] = line
            namespace["symbols"][varName] = variable
            
        if isClassVar and not "is-class-var" in variable:
            variable["is-class-var"] = 1
            # line number of first class-level assignment wins
            if line:
                variable["line"] = line

        if (not new_var and
            _isfunction(variable) and
            isinstance(rhsNode, ast.CallFunc) and
            rhsNode.args and
            isinstance(rhsNode.args[0], ast.Name) and
            variable["name"] == rhsNode.args[0].name
            ):
            # a speial case for 2.4-styled decorators
            return
                        
        varTypes = variable["types"]
        for t in self._guessTypes(rhsNode, namespace):
            log.info("guessed type: %s ::= %s", varName, t)
            if t not in varTypes:
                varTypes[t] = 0
            varTypes[t] += 1

    def _visitSimpleAssign(self, lhsNode, rhsNode, line):
        """Handle a simple assignment: assignment to a symbol name or to
        an attribute of a symbol name. If the given left-hand side (lhsNode)
        is not an node type that can be handled, it is dropped.
        """
        log.debug("_visitSimpleAssign(lhsNode=%r, rhsNode=%r)", lhsNode,
                  rhsNode)
        if isinstance(lhsNode, ast.AssName):
            # E.g.:  foo = ...
            # Assign this to the local namespace, unless there was a
            # 'global' statement. (XXX Not handling 'global' yet.)
            ns = self.nsstack[-1]
            self._assignVariable(lhsNode.name, ns, rhsNode, line,
                                 isClassVar=_isclass(ns))
        elif isinstance(lhsNode, ast.AssAttr):
            # E.g.:  foo.bar = ...
            # If we can resolve "foo", then we update that namespace.
            variable, citdl = self._resolveObjectRef(lhsNode.expr)
            if variable:
                self._assignVariable(lhsNode.attrname,
                                     variable["declaration"], rhsNode, line)
        else:
            log.debug("could not handle simple assign (module '%s'): "
                      "lhsNode=%r, rhsNode=%r", self.moduleName, lhsNode,
                      rhsNode)

    def visitAssign(self, node):
        log.info("visitAssign:%d: %r", node.lineno,
                 self.lines and self.lines[node.lineno-1])
        lhsNode = node.nodes[0]
        rhsNode = node.expr
        if isinstance(lhsNode, (ast.AssName, ast.AssAttr)):
            # E.g.:
            #   foo = ...       (AssName)
            #   foo.bar = ...   (AssAttr)
            self._visitSimpleAssign(lhsNode, rhsNode, node.lineno)
        elif isinstance(lhsNode, (ast.AssTuple, ast.AssList)):
            # E.g.:
            #   foo, bar = ...
            #   [foo, bar] = ...
            # If the RHS is a sequence with the same number of elements,
            # then we update each assigned-to variable. Otherwise, bail.
            if isinstance(rhsNode, (ast.Tuple, ast.List)):
                if len(lhsNode.nodes) == len(rhsNode.nodes):
                    for i in range(len(lhsNode.nodes)):
                        self._visitSimpleAssign(lhsNode.nodes[i],
                                                rhsNode.nodes[i],
                                                node.lineno)
            elif isinstance(rhsNode, ast.Dict):
                if len(lhsNode.nodes) == len(rhsNode.items):
                    for i in range(len(lhsNode.nodes)):
                        self._visitSimpleAssign(lhsNode.nodes[i],
                                                rhsNode.items[i][0],
                                                node.lineno)
            elif isinstance(rhsNode, ast.CallFunc):
                for i in range(len(lhsNode.nodes)):
                    self._visitSimpleAssign(lhsNode.nodes[i],
                                            None, # we don't have a good type.
                                            node.lineno)
            else:
                log.info("visitAssign:: skipping unknown rhsNode type: %r - %r",
                         type(rhsNode), rhsNode)
        elif isinstance(lhsNode, ast.Slice):
            # E.g.:  bar[1:2] = "foo"
            # We don't bother with these: too hard.
            log.info("visitAssign:: skipping slice - too hard")
            pass
        elif isinstance(lhsNode, ast.Subscript):
            # E.g.:  bar[1] = "foo"
            # We don't bother with these: too hard.
            log.info("visitAssign:: skipping subscript - too hard")
            pass
        else:
            raise PythonCILEError("unexpected type of LHS of assignment: %r"
                                  % lhsNode)

    def _resolveObjectRef(self, expr):
        """Try to resolve the given expression to a variable namespace.
        
            "expr" is some kind of ast.Node instance.
        
        Returns the following 2-tuple for the object:
            (<variable dict>, <CITDL string>)
        where,
            <variable dict> is the defining dict for the variable, e.g.
                    {'name': 'classvar', 'types': {'int': 1}}.
                This is None if the variable could not be resolved.
            <CITDL string> is a string of CITDL code (see the spec) describing
                how to resolve the variable later. This is None if the
                variable could be resolved or if the expression is not
                expressible in CITDL (CITDL does not attempt to be a panacea).
        """
        log.debug("_resolveObjectRef(expr=%r)", expr)
        if isinstance(expr, ast.Name):
            name = expr.name
            nspath = self.nsstack[-1]["nspath"]
            for i in range(len(nspath), -1, -1):
                ns = self.st[nspath[:i]]
                if name in ns["symbols"]:
                    return (ns["symbols"][name], None)
                else:
                    log.debug("_resolveObjectRef: %r not in namespace %r", name,
                              '.'.join(ns["nspath"]))
        elif isinstance(expr, ast.Getattr):
            obj, citdl = self._resolveObjectRef(expr.expr)
            decl = obj and obj["declaration"] or None # want the declaration
            if (decl #and "symbols" in decl #XXX this "and"-part necessary?
                and expr.attrname in decl["symbols"]):
                return (decl["symbols"][expr.attrname], None)
            elif isinstance(expr.expr, ast.Const):
                # Special case: specifically refer to type object for
                # attribute access on constants, e.g.:
                #   ' '.join
                citdl = "__builtins__.%s.%s"\
                        % ((type(expr.expr.value).__name__), expr.attrname)
                return (None, citdl)
                #XXX Could optimize here for common built-in attributes. E.g.,
                #    we *know* that str.join() returns a string.
        elif isinstance(expr, ast.Const):
            # Special case: specifically refer to type object for constants.
            return (None, "__builtins__.%s" % type(expr.value).__name__)
        elif isinstance(expr, ast.CallFunc):
            #XXX Would need flow analysis to have an object dict for whatever
            #    a __call__ would return.
            pass

        # Fallback: return CITDL code for delayed resolution.
        log.debug("_resolveObjectRef: could not resolve %r", expr)
        scope = '.'.join(self.nsstack[-1]["nspath"])
        exprrepr = self._getCITDLExprRepr(expr)
        if exprrepr:
            if scope:
                citdl = "%s %s" % (exprrepr, scope)
            else:
                citdl = exprrepr
        else:
            citdl = None
        return (None, citdl)

    def _guessTypes(self, expr, curr_ns=None):
        log.debug("_guessTypes(expr=%r)", expr)
        ts = []
        if isinstance(expr, ast.Const):
            ts = [type(expr.value).__name__]
        elif isinstance(expr, ast.Tuple):
            ts = [tuple.__name__]
        elif isinstance(expr, (ast.List, ast.ListComp)):
            ts = [list.__name__]
        elif isinstance(expr, ast.Dict):
            ts = [dict.__name__]
        elif isinstance(expr, (ast.Add, ast.Sub, ast.Mul, ast.Div, ast.Mod,
                               ast.Power)):
            order = ["int", "bool", "long", "float", "complex", "string",
                     "unicode"]
            possibles = self._guessTypes(expr.left)+self._guessTypes(expr.right)
            ts = []
            highest = -1
            for possible in possibles:
                if possible not in order:
                    ts.append(possible)
                else:
                    highest = max(highest, order.index(possible))
            if not ts and highest > -1:
                ts = [order[highest]]
        elif isinstance(expr, (ast.FloorDiv, ast.Bitand, ast.Bitor,
                               ast.Bitxor, ast.RightShift, ast.LeftShift)):
            ts = [int.__name__]
        elif isinstance(expr, (ast.Or, ast.And)):
            ts = []
            for node in expr.nodes:
                for t in self._guessTypes(node):
                    if t not in ts:
                        ts.append(t)
        elif isinstance(expr, (ast.Compare, ast.Not)):
            ts = [type(1==2).__name__]
        elif isinstance(expr, (ast.UnaryAdd, ast.UnarySub, ast.Invert,
                               ast.Not)):
            ts = self._guessTypes(expr.expr)
        elif isinstance(expr, ast.Slice):
            ts = [list.__name__]
        elif isinstance(expr, ast.Backquote):
            ts = [str.__name__]

        elif isinstance(expr, (ast.Name, ast.Getattr)):
            variable, citdl = self._resolveObjectRef(expr)
            if variable:
                if _isclass(variable) or _isfunction(variable):
                    ts = [ '.'.join(variable["nspath"]) ]
                else:
                    ts = variable["types"].keys()
            elif citdl:
                ts = [citdl]
        elif isinstance(expr, ast.CallFunc):
            variable, citdl = self._resolveObjectRef(expr.node)
            if variable:
                #XXX When/if we support <returns/> and if we have that
                #    info for this 'variable' we can return an actual
                #    value here.
                # Optmizing Shortcut: If the variable is a class then just
                # call its type that class definition, i.e. 'mymodule.MyClass'
                # instead of 'type(call(mymodule.MyClass))'.

                # Remove the common leading namespace elements.
                scope_parts = list(variable["nspath"])
                if curr_ns is not None:
                    for part in curr_ns["nspath"]:
                        if scope_parts and part == scope_parts[0]:
                            scope_parts.pop(0)
                        else:
                            break
                scope = '.'.join(scope_parts)
                if _isclass(variable):
                    ts = [ scope ]
                else:
                    ts = [scope+"()"]
            elif citdl:
                # For code like this:
                #   for line in lines:
                #       line = line.rstrip()
                # this results in a type guess of "line.rstrip <funcname>".
                # That sucks. Really it should at least be line.rstrip() so
                # that runtime CITDL evaluation can try to determine that
                # rstrip() is a _function_ call rather than _class creation_,
                # which is the current resuilt. (c.f. bug 33493)
                # XXX We *could* attempt to guess based on where we know
                #     "line" to be a module import: the only way that
                #     'rstrip' could be a class rather than a function.
                # TW: I think it should always use "()" no matter if it's
                #     a class or a function. The codeintel handler can work
                #     out which one it is. This gives us the ability to then
                #     distinguish between class methods and instance methods,
                #     as class methods look like:
                #       MyClass.staticmethod()
                #     and instance methods like:
                #       MyClass().instancemethod()
                # Updated to use "()".
                # Ensure we only add the "()" to the type part, not to the
                # scope (if it exists) part, which is separated by a space. Bug:
                #   http://bugs.activestate.com/show_bug.cgi?id=71987
                # citdl in this case looks like "string.split myfunction"
                ts = citdl.split(None, 1)
                ts[0] += "()"
                ts = [" ".join(ts)]
        elif isinstance(expr, (ast.Subscript, ast.Lambda)):
            pass
        else:
            log.info("don't know how to guess types from this expr: %r" % expr)
        return ts

    def _getExprRepr(self, node):
        """Return a string representation for this Python expression.
        
        Raises PythonCILEError if can't do it.
        """
        s = None
        if isinstance(node, ast.Name):
            s = node.name
        elif isinstance(node, ast.Const):
            s = repr(node.value)
        elif isinstance(node, ast.Getattr):
            s = '.'.join([self._getExprRepr(node.expr), node.attrname])
        elif isinstance(node, ast.List):
            items = [self._getExprRepr(c) for c in node.getChildren()]
            s = "[%s]" % ", ".join(items)
        elif isinstance(node, ast.Tuple):
            items = [self._getExprRepr(c) for c in node.getChildren()]
            s = "(%s)" % ", ".join(items)
        elif isinstance(node, ast.Dict):
            items = ["%s: %s" % (self._getExprRepr(k), self._getExprRepr(v))
                     for (k, v) in node.items]
            s = "{%s}" % ", ".join(items)
        elif isinstance(node, ast.CallFunc):
            s = self._getExprRepr(node.node)
            s += "("
            allargs = []
            for arg in node.args:
                allargs.append( self._getExprRepr(arg) )
            if node.star_args:
                for arg in node.star_args:
                    allargs.append( "*" + self._getExprRepr(arg) )
            if node.dstar_args:
                for arg in node.dstar_args:
                    allargs.append( "**" + self._getExprRepr(arg) )
            s += ",".join( allargs )
            s += ")"
        elif isinstance(node, ast.Subscript):
            s = "[%s]" % self._getExprRepr(node.expr)
        elif isinstance(node, ast.Backquote):
            s = "`%s`" % self._getExprRepr(node.expr)
        elif isinstance(node, ast.Slice):
            dumpNode(node)
            s = self._getExprRepr(node.expr)
            s += "["
            if node.lower:
                s += self._getExprRepr(node.lower)
            s += ":"
            if node.upper:
                s += self._getExprRepr(node.upper)
            s += "]"
        elif isinstance(node, ast.UnarySub):
            s = "-" + self._getExprRepr(node.expr)
        elif isinstance(node, ast.UnaryAdd):
            s = "+" + self._getExprRepr(node.expr)
        elif isinstance(node, ast.Add):
            s = self._getExprRepr(node.left) + "+" + self._getExprRepr(node.right)
        elif isinstance(node, ast.Sub):
            s = self._getExprRepr(node.left) + "-" + self._getExprRepr(node.right)
        elif isinstance(node, ast.Mul):
            s = self._getExprRepr(node.left) + "*" + self._getExprRepr(node.right)
        elif isinstance(node, ast.Div):
            s = self._getExprRepr(node.left) + "/" + self._getExprRepr(node.right)
        elif isinstance(node, ast.FloorDiv):
            s = self._getExprRepr(node.left) + "//" + self._getExprRepr(node.right)
        elif isinstance(node, ast.Mod):
            s = self._getExprRepr(node.left) + "%" + self._getExprRepr(node.right)
        elif isinstance(node, ast.Power):
            s = self._getExprRepr(node.left) + "**" + self._getExprRepr(node.right)
        elif isinstance(node, ast.LeftShift):
            s = self._getExprRepr(node.left) + "<<" + self._getExprRepr(node.right)
        elif isinstance(node, ast.RightShift):
            s = self._getExprRepr(node.left) + ">>"+ self._getExprRepr(node.right)
        elif isinstance(node, ast.Keyword):
            s = node.name + "=" + self._getExprRepr(node.expr)
        elif isinstance(node, ast.Bitor):
            creprs = []
            for cnode in node.nodes:
                if isinstance(cnode, (ast.Const, ast.Name)):
                    crepr = self._getExprRepr(cnode)
                else:
                    crepr = "(%s)" % self._getExprRepr(cnode)
                creprs.append(crepr)
            s = "|".join(creprs)
        elif isinstance(node, ast.Bitand):
            creprs = []
            for cnode in node.nodes:
                if isinstance(cnode, (ast.Const, ast.Name)):
                    crepr = self._getExprRepr(cnode)
                else:
                    crepr = "(%s)" % self._getExprRepr(cnode)
                creprs.append(crepr)
            s = "&".join(creprs)
        elif isinstance(node, ast.Bitxor):
            creprs = []
            for cnode in node.nodes:
                if isinstance(cnode, (ast.Const, ast.Name)):
                    crepr = self._getExprRepr(cnode)
                else:
                    crepr = "(%s)" % self._getExprRepr(cnode)
                creprs.append(crepr)
            s = "^".join(creprs)
        elif isinstance(node, ast.Lambda):
            s = "lambda"
            defaultArgsBaseIndex = len(node.argnames) - len(node.defaults)
            if node.kwargs:
                defaultArgsBaseIndex -= 1
                if node.varargs:
                    defaultArgsBaseIndex -= 1
                    varargsIndex = len(node.argnames)-2
                else:
                    varargsIndex = None
                kwargsIndex = len(node.argnames)-1
            elif node.varargs:
                defaultArgsBaseIndex -= 1
                varargsIndex = len(node.argnames)-1
                kwargsIndex = None
            else:
                varargsIndex = kwargsIndex = None
            args = []
            for i in range(len(node.argnames)):
                argOrArgTuple = node.argnames[i]
                if isinstance(argOrArgTuple, tuple):
                    arg = "(%s)" % ','.join(argOrArgTuple)
                    if i >= defaultArgsBaseIndex:
                        defaultNode = node.defaults[i-defaultArgsBaseIndex]
                        try:
                            arg += "="+self._getExprRepr(defaultNode)
                        except PythonCILEError:
                            #XXX Work around some trouble cases.
                            arg += arg+"=..."
                else:
                    argname = node.argnames[i]
                    if i == kwargsIndex:
                        arg = "**"+argname
                    elif i == varargsIndex:
                        arg = "*"+argname
                    elif i >= defaultArgsBaseIndex:
                        defaultNode = node.defaults[i-defaultArgsBaseIndex]
                        try:
                            arg = argname+"="+self._getExprRepr(defaultNode)
                        except PythonCILEError:
                            #XXX Work around some trouble cases.
                            arg = argname+"=..."
                    else:
                        arg = argname
                args.append(arg)
            if args:
                s += " " + ",".join(args)
            try:
                s += ": " + self._getExprRepr(node.code)
            except PythonCILEError:
                #XXX Work around some trouble cases.
                s += ":..."
        else:
            raise PythonCILEError("don't know how to get string repr "
                                  "of expression: %r" % node)
        return s

    def _getCITDLExprRepr(self, node, _level=0):
        """Return a string repr for this expression that CITDL processing
        can handle.
        
        CITDL is no panacea -- it is meant to provide simple delayed type
        determination. As a result, many complicated expressions cannot
        be handled. If the expression is not with CITDL's scope, then None
        is returned.
        """
        s = None
        if isinstance(node, ast.Name):
            s = node.name
        elif isinstance(node, ast.Const):
            s = repr(node.value)
        elif isinstance(node, ast.Getattr):
            exprRepr = self._getCITDLExprRepr(node.expr, _level+1)
            if exprRepr is None:
                pass
            else:
                s = '.'.join([exprRepr, node.attrname])
        elif isinstance(node, ast.List):
            s = "[]"
        elif isinstance(node, ast.Tuple):
            s = "()"
        elif isinstance(node, ast.Dict):
            s = "{}"
        elif isinstance(node, ast.CallFunc):
            # Only allow CallFunc at the top-level. I.e. this:
            #   spam.ham.eggs()
            # is in scope, but this:
            #   spam.ham().eggs
            # is not.
            if _level != 0:
                pass
            else:
                s = self._getCITDLExprRepr(node.node, _level+1)
                if s is not None:
                    s += "()"
        return s


def _quietCompilerParse(content):
    oldstderr = sys.stderr
    sys.stderr = StringIO()
    try:
        return compiler.parse(content)
    finally:
        sys.stderr = oldstderr

def _quietCompile(source, filename, kind):
    oldstderr = sys.stderr
    sys.stderr = StringIO()
    try:
        return compile(source, filename, kind)
    finally:
        sys.stderr = oldstderr


def _getAST(content):
    """Return an AST for the given Python content.
    
    If cannot, raise an error describing the problem.
    """
    # EOL issues:
    # compiler.parse() can't handle '\r\n' EOLs on Mac OS X and can't
    # handle '\r' EOLs on any platform. Let's just always normalize.
    # Unfortunately this is work only for the exceptional case. The
    # problem is most acute on the Mac.
    content = '\n'.join(content.splitlines(0))
    # Is this faster?
    #   content = content.replace('\r\n', '\n').replace('\r', '\n')

    errlineno = None # line number of a SyntaxError
    ast_ = None
    try:
        ast_ = _quietCompilerParse(content)
    except SyntaxError, ex:
        errlineno = ex.lineno
        log.debug("compiler parse #1: syntax error on line %d", errlineno)
    except parser.ParserError, ex:
        log.debug("compiler parse #1: parse error")
        # Try to get the offending line number.
        # compile() only likes LFs for EOLs.
        lfContent = content.replace("\r\n", "\n").replace("\r", "\n")
        try:
            _quietCompile(lfContent, "dummy.py", "exec")
        except SyntaxError, ex2:
            errlineno = ex2.lineno
        except:
            pass
        if errlineno is None:
            raise # Does this re-raise 'ex' (as we want) or 'ex2'?

    if errlineno is not None:
        # There was a syntax error at this line: try to recover by effectively
        # nulling out the offending line.
        lines = content.splitlines(1)
        offender = lines[errlineno-1]
        log.info("syntax error on line %d: %r: trying to recover",
                 errlineno, offender)
        indent = ''
        for i in range(0, len(offender)):
            if offender[i] in " \t":
                indent += offender[i]
            else:
                break
        lines[errlineno-1] = indent+"pass"+"\n"
        newContent = ''.join(lines)

        errlineno2 = None
        try:
            ast_ = _quietCompilerParse(newContent)
        except SyntaxError, ex:
            errlineno2 = ex.lineno
            log.debug("compiler parse #2: syntax error on line %d", errlineno)
        except parser.ParserError, ex:
            log.debug("compiler parse #2: parse error")
            # Try to get the offending line number.
            # compile() only likes LFs for EOLs.
            lfContent = newContent.replace("\r\n", "\n").replace("\r", "\n")
            try:
                _quietCompile(lfContent, "dummy.py", "exec")
            except SyntaxError, ex2:
                errlineno2 = ex2.lineno
            except:
                pass
            if errlineno2 is None:
                raise

        if ast_ is not None:
            pass
        elif errlineno2 == errlineno:
            raise ValueError("cannot recover from syntax error: line %d"
                             % errlineno)
        else:
            raise ValueError("cannot recover from multiple syntax errors: "
                             "line %d and then %d" % (errlineno, errlineno2))
    
    if ast_ is None:
        raise ValueError("could not generate AST")
    
    return ast_


_rx_cache = {}

def _rx(pattern, flags=0):
    if pattern not in _rx_cache:
        _rx_cache[pattern] = re.compile(pattern, flags)
    return _rx_cache[pattern]

def _convert3to2(src):
    # XXX: this might be much faster to do all this stuff by manipulating
    #      parse trees produced by tdparser
    
    # except Foo as bar => except (Foo,) bar
    src = _rx(r'(\bexcept\s*)(\S.+?)\s+as\s+(\w+)\s*:').sub(r'\1(\2,), \3:', src)
    
    # 0o123 => 123
    src = _rx(r'\b0[oO](\d+)').sub(r'\1', src)
    
    # print(foo) => print_(foo)
    src = _rx(r'\bprint\s*\(').sub(r'print_(', src)
    
    # change forms of class Foo(metaclass=Cls3) to class Foo
    src = _rx(r'(\bclass\s+\w+\s*)\(\s*\w+\s*=\s*\w+\s*\)\s*:').sub(r'\1:', src)
    
    # change forms of class Foo(..., arg=Base1, metaclass=Cls3) to class Foo(...)
    src = _rx(r'(\bclass\s+\w+\s*\(.*?),?\s*\w+\s*=.+?\)\s*:').sub(r'\1):', src)

    # Remove return type annotations like def foo() -> int:
    src = _rx(r'(\bdef\s+\w+\s*\(.*?\))\s*->\s*\w+\s*:').sub(r'\1:', src)

    # def foo(foo:Bar, baz=lambda x: qoox): => def foo(bar, baz=_lambda(qoox)):
    src = _rx(r'(\bdef\s+\w+\s*\()(.+?)(\)\s*:)').sub(_clean_func_args, src)
    
    return src

def _clean_func_args(defn):
    argdef = defn.group(2)
    
    parser = tdparser.PyExprParser()
    try:
        arglist = parser.parse_bare_arglist(argdef)

        seen_args = False
        seen_kw = False
        py2 = []
        for arg in arglist:
            name, value, type = arg
            if name.id == "*":
                if not seen_kw:
                    name.value = "**kwargs"
                    py2.append(arg)
                    seen_kw = True
                    seen_args = True
            elif name.value[:2] == "**":
                if not seen_kw:
                    py2.append(arg)
                    seen_kw = True
                    seen_args = True
            elif name.value[0] == "*":
                if not seen_args:
                    seen_args = True
                    py2.append(arg)
            else:
                if seen_args or seen_kw:
                    break
                else:
                    py2.append(arg)
        
        cleared = tdparser.arg_list_py(py2)
    except tdparser.ParseError, ex:
        cleared = argdef
        log.exception("Couldn't parse (%r)" % argdef)
    
    return defn.group(1) + cleared + defn.group(3)


#---- public module interface

def scan_cix(content, filename, md5sum=None, mtime=None, lang="Python"):
    """Scan the given Python content and return Code Intelligence data
    conforming the the Code Intelligence XML format.
    
        "content" is the Python content to scan. This should be an
            encoded string: must be a string for `md5` and
            `compiler.parse` -- see bug 73461.
        "filename" is the source of the Python content (used in the
            generated output).
        "md5sum" (optional) if the MD5 hexdigest has already been calculated
            for the content, it can be passed in here. Otherwise this
            is calculated.
        "mtime" (optional) is a modified time for the file (in seconds since
            the "epoch"). If it is not specified the _current_ time is used.
            Note that the default is not to stat() the file and use that
            because the given content might not reflect the saved file state.
        "lang" (optional) is the language of the given file content.
            Typically this is "Python" (i.e. a pure Python file), but it
            may also be "DjangoHTML" or similar for Python embedded in
            other documents.
        XXX Add an optional 'eoltype' so that it need not be
            re-calculated if already known.
    
    This can raise one of SyntaxError, PythonCILEError or parser.ParserError
    if there was an error processing. Currently this implementation uses the
    Python 'compiler' package for processing, therefore the given Python
    content must be syntactically correct.
    """
    codeintel = scan_et(content, filename, md5sum, mtime, lang)
    tree = et.ElementTree(codeintel)

    stream = StringIO()

    # this is against the W3C spec, but ElementTree wants it lowercase
    tree.write(stream, "utf-8")
    
    raw_cix = stream.getvalue()
    
    # XXX: why this 0xA -> &#xA; conversion is necessary?
    #      It makes no sense, but some tests break without it
    #      (like cile/scaninputs/path:cdata_close.py)
    cix = raw_cix.replace('\x0a', '&#xA;')
    
    return cix


def scan_et(content, filename, md5sum=None, mtime=None, lang="Python"):
    """Scan the given Python content and return Code Intelligence data
    conforming the the Code Intelligence XML format.
    
        "content" is the Python content to scan. This should be an
            encoded string: must be a string for `md5` and
            `compiler.parse` -- see bug 73461.
        "filename" is the source of the Python content (used in the
            generated output).
        "md5sum" (optional) if the MD5 hexdigest has already been calculated
            for the content, it can be passed in here. Otherwise this
            is calculated.
        "mtime" (optional) is a modified time for the file (in seconds since
            the "epoch"). If it is not specified the _current_ time is used.
            Note that the default is not to stat() the file and use that
            because the given content might not reflect the saved file state.
        "lang" (optional) is the language of the given file content.
            Typically this is "Python" (i.e. a pure Python file), but it
            may also be "DjangoHTML" or similar for Python embedded in
            other documents.
        XXX Add an optional 'eoltype' so that it need not be
            re-calculated if already known.
    
    This can raise one of SyntaxError, PythonCILEError or parser.ParserError
    if there was an error processing. Currently this implementation uses the
    Python 'compiler' package for processing, therefore the given Python
    content must be syntactically correct.
    """
    log.info("scan '%s'", filename)
    if md5sum is None:
        md5sum = md5(content).hexdigest()
    if mtime is None:
        mtime = int(time.time())
        
    # 'compiler' both (1) wants a newline at the end and (2) can fail on
    # funky *whitespace* at the end of the file.
    content = content.rstrip() + '\n'

    if lang == "Python3":
        # Make Python3 code as compatible with pythoncile's Python2
        # parser as neessary for codeintel purposes.
        content = _convert3to2(content)
    
    if type(filename) == types.UnicodeType:
        filename = filename.encode('utf-8')
    # The 'path' attribute must use normalized dir separators.
    if sys.platform.startswith("win"):
        path = filename.replace('\\', '/')
    else:
        path = filename

    try:
        ast_ = _getAST(content)
        if _gClockIt:
            sys.stdout.write(" (ast:%.3fs)" % (_gClock()-_gStartTime))
    except Exception, ex:
        file = et.Element('file', _et_attrs(dict(lang=lang,
                                                 path=path,
                                                 error=str(ex))))
    else:
        moduleName = os.path.splitext(os.path.basename(filename))[0]
        visitor = AST2CIXVisitor(moduleName, content=content, lang=lang)
        if log.isEnabledFor(logging.DEBUG):
            walker = ExampleASTVisitor()
            walker.VERBOSE = 1
        else:
            walker = None
        compiler.walk(ast_, visitor, walker)
        if _gClockIt: sys.stdout.write(" (walk:%.3fs)" % (_gClock()-_gStartTime))
        if log.isEnabledFor(logging.INFO):
            # Dump a repr of the gathering info for debugging
            # - We only have to dump the module namespace because
            #   everything else should be linked from it.
            for nspath, namespace in visitor.st.items():
                if len(nspath) == 0: # this is the module namespace
                    pprint.pprint(namespace)
        
        file = visitor.getCIX(path)
        if _gClockIt: sys.stdout.write(" (getCIX:%.3fs)" % (_gClock()-_gStartTime))

    codeintel = et.Element('codeintel', _et_attrs(dict(version="2.0")))
    codeintel.append(file)
    return codeintel




#---- mainline

def main(argv):
    logging.basicConfig()

    # Parse options.
    try:
        opts, args = getopt.getopt(argv[1:], "Vvhf:cL:",
            ["version", "verbose", "help", "filename=", "md5=", "mtime=",
             "clock", "language="])
    except getopt.GetoptError, ex:
        log.error(str(ex))
        log.error("Try `pythoncile --help'.")
        return 1
    numVerboses = 0
    stdinFilename = None
    md5sum = None
    mtime = None
    lang = "Python"
    global _gClockIt
    for opt, optarg in opts:
        if opt in ("-h", "--help"):
            sys.stdout.write(__doc__)
            return
        elif opt in ("-V", "--version"):
            ver = '.'.join([str(part) for part in _version_])
            print "pythoncile %s" % ver
            return
        elif opt in ("-v", "--verbose"):
            numVerboses += 1
            if numVerboses == 1:
                log.setLevel(logging.INFO)
            else:
                log.setLevel(logging.DEBUG)
        elif opt in ("-f", "--filename"):
            stdinFilename = optarg
        elif opt in ("-L", "--language"):
            lang = optarg
        elif opt in ("--md5",):
            md5sum = optarg
        elif opt in ("--mtime",):
            mtime = optarg
        elif opt in ("-c", "--clock"):
            _gClockIt = 1
            import time
            global _gClock
            if sys.platform.startswith("win"):
                _gClock = time.clock
            else:
                _gClock = time.time

    if len(args) == 0:
        contentOnStdin = 1
        filenames = [stdinFilename or "<stdin>"]
    else:
        contentOnStdin = 0
        paths = []
        for arg in args:
            paths += glob.glob(arg)
        filenames = []
        for path in paths:
            if os.path.isfile(path):
                filenames.append(path)
            elif os.path.isdir(path):
                pyfiles = [os.path.join(path, n) for n in os.listdir(path)
                           if os.path.splitext(n)[1] == ".py"]
                pyfiles = [f for f in pyfiles if os.path.isfile(f)]
                filenames += pyfiles

    try:
        for filename in filenames:
            if contentOnStdin:
                log.debug("reading content from stdin")
                content = sys.stdin.read()
                log.debug("finished reading content from stdin")
                if mtime is None:
                    mtime = int(time.time())
            else:
                if mtime is None:
                    mtime = int(os.stat(filename)[stat.ST_MTIME])
                fin = open(filename, 'r')
                try:
                    content = fin.read()
                finally:
                    fin.close()

            if _gClockIt:
                sys.stdout.write("scanning '%s'..." % filename)
                global _gStartTime
                _gStartTime = _gClock()
            data = scan_cix(content, filename, md5sum=md5sum, mtime=mtime,
                            lang=lang)
            if _gClockIt:
                sys.stdout.write(" %.3fs\n" % (_gClock()-_gStartTime))
            elif data:
                sys.stdout.write(data)
    except PythonCILEError, ex:
        log.error(str(ex))
        if log.isEnabledFor(logging.DEBUG):
            print
            import traceback
            traceback.print_exception(*sys.exc_info())
        return 1
    except KeyboardInterrupt:
        log.debug("user abort")
        return 1


if __name__ == "__main__":
    sys.exit( main(sys.argv) )
    
