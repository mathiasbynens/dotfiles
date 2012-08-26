#!/usr/bin/env python

"""A re-write a pythoncile.py using lib2to3 to be able to support Python 3
syntax.

To play along
=============

1. Get a local codeintel build:

    cd src/codeintel
    . bin/setenv.sh    # `bin\setenv.bat` on Windows
    python Makefile.py all

2. Get a local copy of lib2to3 from Python's SVN into codeintel's lib dir
   and patch it with our current modifications.

    cd lib
    svn co http://svn.python.org/projects/sandbox/trunk/2to3/lib2to3
    patch -p0 < ../play/lib2to3.patch
    cd ..

3. Setup an alias called 'pycile' (adjusting the path to Komodo accordingly)

    # Bash
    alias pycile="python2.6 $HOME/as/komodo/src/codeintel/lib/codeintel2/pythoncile2.py"
   
    # "pycile.bat" for Windows
    @python26 C:\trentm\as\komodo\src\codeintel\lib\codeintel2\pythoncile2.py %*

4. Run 'pycile' on files.

    pycile play\sample.py     # dumps CIX output
    pycile -v play\sample.py  # also pprints the syntax tree from lib2to3
    pycile -vc play\sample.py # compares with CIX from pythoncile.py
"""
#TODO:
# - foo.bar assignments for class instance vars
# - improved type inferencing: raven.py diffs, hi.py, assign.py
# - pass significant set of test suite
# - perf
# - python 2 vs python 3 handling
#
# CIX differences to check:
# - Is it necessary that <import>'s are at the top of their scope, even if
#   not matching the file order? I.e. does the Python evalr use this side-effect?
#
# Syntax TODO:
# - function and class type annonations
# - returns in functions
# - generators
# - local import syntax (play/imports.py -> put in test suite)
# - decorators (on functions and classes)
# - special handling for @classmethod, @staticmethod, @property
# - anything necessary with metaclasses?
# - kwargs to class "bases": used for Python 3 metaclasses, at least
# - global stmt
# - nonlocal stmt (http://docs.python.org/3.0/reference/simple_stmts.html#the-nonlocal-statement)
# - type inferencing as good (plus new types, no unicode, new bytes) as
#   pythoncile.py:_guessTypes
# - tuple-unpacking in function args (dropped in Python 3, but still in
#   older Python 2 syntax)
# - `a, ..., b = blah()` unpacking (and the other forms of this)
#
# New features TODO:
# - support for pythondoc-style type annotations
# - type inferencing from isinstance calls
# - type inferencing from common, well-known methods (e.g. string methods,
#   dict and list methods)

__version_info__ = (2, 0, 0)
__version__ = '2.0.0' #TODO: map/str thing


import sys
import os
from os.path import *
import time
import logging
import difflib
import re
import optparse
import types
#XXX Use ciElementTree eventually.
from xml.etree import cElementTree as ET
from collections import deque, defaultdict
import itertools
from hashlib import md5
from pprint import pprint


_komodo_src_dir = dirname(dirname(dirname(dirname(abspath(__file__)))))
sys.path.insert(0, join(_komodo_src_dir, "python-sitelib"))
sys.path.insert(0, join(_komodo_src_dir, "codeintel", "lib"))
from codeintel2.tree import pretty_tree_from_tree
from codeintel2 import util

import lib2to3   # should be in codeintel/lib/lib2to3 (read "to play along" above)
from lib2to3.pgen2 import driver
from lib2to3 import pytree, pygram
from lib2to3.pygram import python_symbols
from lib2to3.pgen2 import token

#---- globals

_gOExtraMile = True
_gClockIt = 0   # if true then we are gathering timing data
_gClock = None  # if gathering timing data this is set to time retrieval fn
_gStartTime = None   # start time of current file being scanned

log = logging.getLogger("pythoncile2")


#---- exceptions

class PythonCILEError(Exception):
    pass


#---- core module stuff

def pythoncile2(path, content=None):
    if False:
        # This tweak to the python grammar allows the parser to parse Python 3
        # content. Else it will choke on, at least, the keyword argument in
        # this:
        #       print("foo", file=sys.stderr)
        #TODO: understand why this is
        del pygram.python_grammar.keywords["print"]
    else:
        # However, to parse Python 2 with print as a statement, we need that
        # grammar item.
        #TODO: not sure about Python 2 code with `from __future__ import print_function`
        pass
    dvr = driver.Driver(pygram.python_grammar,
                        convert=pytree.convert,
                        logger=log)

    # Based on `RefactoringTool.refactor_string()`.
    if content is None:
        data = open(path, 'r').read() + '\n'
    else:
        data = content
    #try:
    #    tree = dvr.parse_string(data)
    #except Exception, err:
    #    raise PythonCILEError("Can't parse %s: %s: %s" % (
    #       path, err.__class__.__name__, err))
    ast = dvr.parse_string(data)
    if log.isEnabledFor(logging.DEBUG):
        ast.pprint(indent="`   ")

    # Traverse the AST (actually more of a concrete syntax tree).
    blob = Scope("blob", splitext(basename(path))[0],
        lang="Python", src=path)
    scanner = Scanner(blob)
    scanner.scan(ast)

    # Build the CIX tree.
    now = time.time()
    codeintel = ET.Element("codeintel", version="2.0")
    file = ET.SubElement(codeintel, "file", lang="Python", mtime=str(now),
                         path=path)
    scanner.gen_cix_tree(file)

    return codeintel


class Scope(dict):
    parent = None
    def __init__(self, ilk, name, **attrs):
        self.ilk = ilk
        self.name = name
        self.attrs = attrs
        # Ordered list of children. Note: the children are also indexed on
        # this scope's dict by name.
        self.children = []
        
    def __repr__(self):
        return "<Scope: %s '%s'>" % (self.ilk, self.name)
    
    def _add_child(self, child):
        self.children.append(child)
        self[child.name] = child
        child.parent = self
        return child
    
    def add_variable(self, name, **attrs):
        return self._add_child(Variable(name, **attrs))
    
    def add_argument(self, name, **attrs):
        return self._add_child(Argument(name, **attrs))
    
    def add_scope(self, ilk, name, **attrs):
        return self._add_child(Scope(ilk, name, **attrs))
    
    def gen_cix_tree(self, parent_elem):
        elem = ET.SubElement(parent_elem, "scope", ilk=self.ilk,
            name=self.name, **self.attrs)
        for child in self.children:
            child.gen_cix_tree(elem)

class Variable(object):
    parent = None
    def __init__(self, name, **attrs):
        self.name = name
        self.attrs = attrs
        self.citdl_nodes = []
    def __repr__(self):
        return "<Variable: '%s'>" % self.name
    def gen_cix_tree(self, parent_elem):
        ET.SubElement(parent_elem, "variable", name=self.name, **self.attrs)

class Argument(Variable):
    def __repr__(self):
        return "<Argument: '%s'>" % self.name
    def gen_cix_tree(self, parent_elem):
        ET.SubElement(parent_elem, "variable", ilk="argument",
            name=self.name, **self.attrs)


def _node_lineno(node):
    if hasattr(node, 'lineno'):
        return node.lineno
    else:
        if node.parent:
            return _node_lineno(node.parent)
        else:
            return -1

class Scanner(object):
    def __init__(self, blob):
        self.blob = blob
        self._scope_stack = deque([blob])  # stack of `Scope` instances

    def gen_cix_tree(self, file_elem):
        self.blob.gen_cix_tree(file_elem)

    def _push_scope(self, scope):
        self._scope_stack.append(scope)
    def _peek_scope(self):
        return self._scope_stack[-1]
    def _iter_scopes(self):
        for item in reversed(self._scope_stack):
            yield item
    def _close_scope(self):
        scope = self._scope_stack.pop()
        for var in scope.children:
            if not isinstance(var, Variable):
                continue
            # For now we use the first non-"None" CITDL.
            #TODO: Some experiments to see if the first or last
            #      assignment tends to do better, or some other combo.
            citdl = var.attrs.get("citdl")
            if citdl and citdl is not "None":
                continue
            for node in var.citdl_nodes:
                if isinstance(node, basestring):
                    # Sometimes it has already been rendered to a CITDL string.
                    citdl = node
                else:
                    citdl = self._citdl_from_node(node)
                if citdl and citdl is not "None":
                    var.attrs["citdl"] = citdl
                    break

    def scan(self, ast):
        visitor_from_symbol = {
            python_symbols.funcdef: self.visit_function,
            python_symbols.classdef: self.visit_class,
            python_symbols.import_name: self.visit_import,
            python_symbols.import_from: self.visit_import_from,
            python_symbols.expr_stmt: self.visit_expr,
            python_symbols.return_stmt: self.visit_return,
            python_symbols.for_stmt: self.visit_for,
        }

        traverser = _traverse(ast.children)
        first = traverser.next()
        if first == "end":
            return
        elif (first.type == python_symbols.simple_stmt
            and first.children[0].type == token.STRING):
            docstring_node = first.children[0]
            self.blob.attrs["doc"] = _docstring_from_node(docstring_node)
        else:
            traverser = itertools.chain([first], traverser)
        for node in traverser:
            if node == "end":
                self._close_scope()
                continue
            if node.type == python_symbols.simple_stmt:
                node = node.children[0]
            #print "%sNode(%s)" % ('  '*len(self._scope_stack), pytree.type_repr(node.type))
            visitor = visitor_from_symbol.get(node.type)
            if visitor:
                visitor(node)

    def _citdl_from_node(self, node):
        type = node.type
        citdl = None
        if type == token.NAME:
            citdl = node.value
        elif type == token.STRING:
            citdl = "str"
        elif type == token.NUMBER:
            citdl = "int" if _isint(node.value) else "float"
        elif type == python_symbols.power:
            # e.g. `sys.argv` in `arg=sys.argv`
            #TODO:XXX pythoncile.py returns `Raven` for:
            #       r = Raven()   # if Raven is a class
            # but here we are returning `Raven()`, which makes more sense
            # and is advocated by Todd as well in a pythoncile.py comment.
            # Need to adjust Python evalr accordingly.
            citdl = self._citdl_from_power_node(node)
        elif type == python_symbols.arith_expr:
            # assume the expression will coerce to the first value type
            for c in node.children:
                if c.type not in (token.MINUS, token.PLUS):
                    citdl = self._citdl_from_node(c)
                    break
        elif type == python_symbols.term:
            # assume the expression will coerce to the first value type
            for c in node.children:
                if c.type not in (token.PERCENT, token.STAR, token.SLASH, token.DOUBLESLASH):
                    citdl = self._citdl_from_node(c)
                    break
        elif type == python_symbols.factor:
            citdl = self._citdl_from_node(node.children[1])
        elif type == python_symbols.test:
            # try the "then" part first
            citdl = self._citdl_from_node(node.children[0])
            if citdl is None:
                # can't tell, analyse the "else" part
                citdl = self._citdl_from_node(node.children[4])
        elif type == python_symbols.atom:
            # Multi-token literals.
            citdl = {
                token.LSQB: "list",
                # Note: This could be wrong. It could be a set literal.
                token.LBRACE: "dict",
                # Note: This could be wrong. A '(' could be parens
                # around an expression.
                token.LPAR: "tuple",
            }[node.children[0].type]
        else:
            raise ValueError("unexpected parameters token (line %d): %r"
                % (_node_lineno(node), node))
            
        # de-in
        if node.parent.type == python_symbols.for_stmt:
            if citdl is not None:
                citdl += '[]'
            
        return citdl

    def _citdl_from_power_node(self, node):
        """CITDL for a given python_symbols.power Node type."""
        children = node.children
        
        from functools import partial as curry
        
        N = pytree.NodePattern   
        N.POWER   = curry(N, type=python_symbols.power)
        N.TRAILER = curry(N, type=python_symbols.trailer)
            
        L = pytree.LeafPattern
        L.NAME = curry(L, type=token.NAME)
        L.LPAR = curry(L, type=token.LPAR, content='(')
        L.RPAR = curry(L, type=token.RPAR, content=')')
        
        ANY = pytree.WildcardPattern
        
        funcall_pattern = N.POWER(content=[L.NAME(name="func"),
                                           N.TRAILER(content=[L.LPAR(),
                                                              ANY(),
                                                              L.RPAR()])])

        match = {}
        if funcall_pattern.match(node, results=match):
            func = match['func'].value
            if func in ('range', 'filter', 'map'):
                return 'list'
            elif func in ('list', 'tuple', 'dict'):
                return func
        
        bits = [children[0].value]
        for c in children[1:]:
            if c.children and c.children[0].type == token.DOT:
                bits += ['.', c.children[1].value]
            else:
                assert c.children[0].type in (token.LPAR, token.LSQB)
                bits += [c.children[0].value, c.children[-1].value]
        return ''.join(bits)

    def visit_return(self, node):
        #TODO: pythoncile.py handled (a) spliting CITDL (scoperef), (b)
        #      excluding "None" and "NoneType", (c) True/False -> bool.
        #      pythoncile.py also gather all return's and picked the most
        #      common guess.
        #TODO:XXX Evaluate the necessity of multiple return statement analysis.
        scope = self._peek_scope()
        assert scope.ilk == "function"
        if not scope.get("returns"):
            citdl = self._citdl_from_node(node.children[1])
            if citdl and citdl is not "None":
                scope.attrs["returns"] = citdl

    def visit_for(self, node):
        children = node.children
        assert len(children) in (6,8) and children[0].value == 'for', \
            "unexpected for_stmt: %r" % node
        # 0="for"
        # 1=exprlist
        exprlist = children[1]
        # 2="in"
        # 3=testlist
        testlist = children[3]
        # 4=":"
        # 5=suite
        # 6=else
        # 7=suite
        return self._visit_for_or_expr(node, exprlist, testlist)
        
    def visit_expr(self, node):
        children = node.children
        assert len(children) == 3 and children[1].type == token.EQUAL, \
            "unexpected expr_stmt: %r" % node
        lhs = children[0]
        rhs = children[2]
        return self._visit_for_or_expr(node, lhs, rhs)

    def _visit_for_or_expr(self, node, lhs, rhs):
        parent = self._peek_scope()
        # Get left-hand side item(s).
        #  if lhs.type == token.NAME:
        if lhs.type in (token.NAME, python_symbols.power):
            var_nodes = [lhs]
        elif lhs.type == python_symbols.atom:
            # `[a,b] = ...`
            # `(a,b) = ...`
            #TODO:XXX handle type "power", i.e. `(foo.bar, baz.car) = ...`
            inside = lhs.children[1]
            assert inside.type in (python_symbols.testlist_gexp, python_symbols.listmaker)
            var_nodes = inside.children[::2]
            if set(v.type for v in var_nodes) != set([token.NAME]):
                # Skip things like `((e), f) = ...`.
                log.warn("skip expr lhs: `%s`", lhs)
                return
        elif lhs.type == python_symbols.testlist:
            # `a,b = ...`
            #TODO:XXX handle type "power", i.e. `foo.bar, baz.car = ...`
            var_nodes = lhs.children[::2]
            if set(v.type for v in var_nodes) != set([token.NAME]):
                # Skip things like `(e), f = ...`.
                log.warn("skip expr lhs: `%s`", lhs)
                return
        else:
            log.warn("unexpected expr lhs: %r", lhs)
            return

        # Resolve the names.
        var_names = []
        for vnode in var_nodes:
            if vnode.type == python_symbols.power:
                vname, vscope = self._resolve_power_node(vnode)
            else:
                vname, vscope = vnode.value, parent
            if vname:
                var_names.append(vname)

        # Create/get the args.
        #TODO:XXX `global` would be handled here
        vars = []
        for name, vnode in zip(var_names, var_nodes):
            if name not in parent:
                var = parent.add_variable(name, line=str(vnode.lineno))
                vars.append(var)
            #XXX Not sure if this is still needed.
            #vars.append(parent.names[name])

        # Capture nodes for type inferencing these vars.
        #XXX This isn't the correct handling. Need to use vscope
        if rhs.type == token.NAME:
            parent[var_names[0]].citdl_nodes.append(rhs)
        elif rhs.type == python_symbols.atom:
            # `... = [a,b]`
            # `... = []`
            # `... = (a,b)`
            # `... = ()`
            inside = rhs.children[1] if len(rhs.children) > 2 else None
            assert inside is None or inside.type in (python_symbols.testlist_gexp, python_symbols.listmaker)
            rhs_nodes = inside.children[::2] if inside else []
            if len(var_names) == len(rhs_nodes):
                for n, r in zip(var_names, rhs_nodes):
                    parent[n].citdl_nodes.append(r)
            else:
                log.warn("expr rhs item count doesn't match lhs: `%s`", node)
        elif rhs.type == python_symbols.power:
            citdl = self._citdl_from_power_node(rhs)
            if citdl:
                for i, n in enumerate(var_names):
                    #TODO:XXX This CITDL syntax, 'foo[0]', is new to evalr.
                    parent[n].citdl_nodes.append(citdl + '[' + str(i) + ']')
        else:
            log.warn("unexpected rhs: %r", rhs)

    def _resolve_power_node(self, node):
        """Resolve the given node to a namespace.

        E.g. given a Node representing `foo.bar` return the namespace (the
        Scope instance) for `foo` and the name "bar".

        @returns {tuple} (<name>, <scope for name>)
        """
        DEBUG = True
        if DEBUG:
            print "-- resolve `%s'" % re.sub(r'\s+', ' ', str(node))
        #return None, None #XXX

        # Example: `self.name` looks like:
        #    Node(power, [
        #    `   Leaf('', NAME, 'self', lineno=4),
        #    `   Node(trailer, [
        #    `   `   Leaf('', DOT, '.', lineno=4),
        #    `   `   Leaf('', NAME, 'name', lineno=4)
        #    `   ])
        #    ]),
        children = node.children

        # Find a namespace for the first name.
        # Example: 'self' -> (<variable 'self'>, <Scope: function '__init__'>)
        name = children[0].value
        for scope in self._iter_scopes():
            #XXX Need to look in *names* in this scope, not just vars.
            #XXX:TODO: test case for that, class def inside function
            if DEBUG:
                print "find first name %r in %r" % (name, scope)
            try:
                var = scope[name]
            except KeyError:
                pass
            else:
                break
        else:
            # Couldn't find `name`.
            return None
        vscope = scope
        if DEBUG:
            print "first name %r is %r in %r" % (name, var, vscope)

        # Resolve that type (i.e. eval its CITDL).
        # Example: <variable 'self'>
        #           -> CITDL 'Person()'
        #           -> (<class 'Person'>, <Scope: blob 'foo'>)
        #           XXX Not sure about that last.
        #XXX Handle it not being a var.
        citdl = var.attrs.get("citdl")
        if not citdl:
            log.debug("cannot resolve var '%s': no type inference (CITDL)", name)
            return None
        name, scope = self._resolve_citdl(citdl, vscope)
        if DEBUG:
            print "citdl %r -> (%r, %r)" % (citdl, name, scope)

        #print "XXX not complete here yet"
        return (name, scope)
        XXX
        #START HERE
        # - need a function to resolve citld from a start scope
        #   Follow _hit_from_citdl() in tree_python.py.
        

    def _resolve_citdl(self, citdl, start_scope):
        """Resolve the given CITDL and start scope to a
        (<name>, <containing-scope>).
        
        Note that this is a poorman's version of the full-on _hit_from_cidtl()
        in tree_python.py. This one doesn't look in imports, etc. Mainly this
        is okay because for the CILE'ing we (at least I think so) only need
        to resolve CITDL for assignment to class and function attributes.
        """
        DEBUG = True
        if DEBUG:
            print "-- resolve citdl %r starting in %r" % (citdl, start_scope)
        tokens = list(self._tokenize_citdl(citdl))
        print tokens
        
        # Find first part.
        first_token = tokens[0]
        scope = start_scope
        while scope:
            if DEBUG:
                print "look for CITDL token %r in %r" % (first_token, scope)
            if first_token in scope:
                break
            scope = scope.parent
        else:
            return None, None
        
        token = first_token
        for t in tokens[1:]:
            if t not in ('()',):
                next = scope.get(t)
                if next:
                    scope = next
                    token = t
                else:
                    return None, None
                    
            print "*** token=", token, " scope=", scope
        
        return token, scope
        
    
    # Should be shared with other code. See tree_python.py's.
    def _tokenize_citdl(self, citdl):
        for token in citdl.split('.'):
            if token.endswith('()'):
                yield token[:-2]
                yield '()'
            else:
                yield token

    def visit_import_from(self, node):
        pscope = self._peek_scope()
        children = node.children
        line = str(children[0].lineno)
        module = str(children[1]).lstrip()
        tail = children[3]
        tail_type = tail.type
        if tail_type == token.LPAR:
            # `from foo import (a, b, c)
            tail = children[4]
            tail_type = tail.type
        if tail_type in (token.NAME, token.STAR):
            # `from logging import basicConfig`
            pscope.add_elem("import", line=line, module=module,
                symbol=tail.value)
        elif tail_type == python_symbols.import_as_names:
            # `from os import sep, name`
            # `from os.path import isabs, join`
            for n in tail.children[::2]:
                pscope.add_elem("import", line=line, module=module,
                    symbol=n.value)
        elif tail_type == python_symbols.import_as_name:
            # `from shutil import copy2 as copy`
            pscope.add_elem("import", line=line,
                module=module,
                symbol=tail.children[0].value,
                alias=tail.children[2].value)
        else:
            raise PythonCILEError("unexpected import: `%r`" % node)

    def visit_import(self, node):
        pscope = self._peek_scope()
        children = node.children
        line = str(children[0].lineno)
        tail = children[1]
        tail_type = tail.type
        if tail_type == token.NAME:
            # `import logging`
            pscope.add_elem("import", line=line, module=tail.value)
        elif tail_type == python_symbols.dotted_as_names:
            # `import os, sys`
            for n in tail.children[::2]:
                pscope.add_elem("import", line=line, module=n.value)
        elif tail_type == python_symbols.dotted_name:
            # `import xml.sax`
            tail.set_prefix("")  # drop leading space
            pscope.add_elem("import", line=line, module=str(tail))
        elif tail_type == python_symbols.dotted_as_name:
            # `import xml.sax as saxlib`
            # `import time as timelib`
            pscope.add_elem("import", line=line,
                module=str(tail.children[0]).lstrip(),
                alias=tail.children[2].value)
        else:
            raise PythonCILEError("unexpected import: `%s`" % node)

    def visit_function(self, node):
        parent = self._peek_scope()
        children = node.children
        is_method = (parent.ilk == "class")

        body = children[-1]  # `simple_stmt` for one-liner, `suite` otherwise
        last_leaf = body.children[-1]
        lineend = ((last_leaf.lineno - 2)
            if last_leaf.type == token.DEDENT else last_leaf.lineno)
        name = children[1].value
        attributes = []

        # Signature and doc.
        #TODO: doc processing a la pythoncile.py
        if False:
            # Function sig handling in pythoncile.py:
            fallbackSig += "(%s)" % (", ".join(sigArgs))
            if node.doc:
                siglines, desclines = util.parsePyFuncDoc(node.doc, [fallbackSig])
                namespace["signature"] = "\n".join(siglines)
                if desclines:
                    namespace["doc"] = "\n".join(desclines)
            else:
                namespace["signature"] = fallbackSig
        params = children[2]
        params.children[0].prefix = ""   # Drop leading space on '('.
        if is_method:
            # Drop 'self' arg from params.
            args = params.children[1]
            if args.type == token.RPAR:  # No args, perhaps a @staticmethod?
                a = ""
            elif args.type == token.NAME:  # Just the one arg.
                a = ""
            else:  # typedargslist
                for idx, arg in enumerate(args.children):
                    if arg.type == token.COMMA:
                        idx += 1
                        break
                args.children[idx].prefix = ''   #XXX safe? What about `def method(self,)`?
                a = ''.join(arg.prefix + str(arg) for arg in args.children[idx:])
            if name == "__init__":
                attributes.append("__ctor__")
                signature = parent.name + '(' + a + ')'
            else:
                signature = name + '(' + a + ')'
            if name.startswith("__"):
                if not name.endswith("__"):
                    attributes.append("private")
            elif name.startswith("_"):
                attributes.append("protected")
        else:
            signature = name + str(params)

        attrs = dict(line=str(children[0].lineno),
            lineend=str(lineend), signature=signature)
        if node.doc:
            attrs["doc"] = node.doc
        if attributes:
            attrs["attributes"] = ' '.join(attributes)
        func = parent.add_scope("function", name, **attrs)
        self._push_scope(func)

        # Function arguments.
        args = params.children[1]
        if args.type == token.RPAR:     # no arguments
            pass  # no arguments
        elif args.type == token.NAME:   # a Leaf, just one argument
            arg = func.add_argument(args.value)
            if is_method:
                arg.attrs["citdl"] = parent.name
        else:
            assert args.type == python_symbols.typedargslist
            arg = arg_modifier = None
            for i, child in enumerate(args.children):
                ctype = child.type
                if ctype == token.NAME:
                    if arg is not None:
                        arg.attrs["citdl"] = child.value
                    else:
                        arg = func.add_argument(child.value)
                        if i == 0 and is_method:
                            arg.attrs["citdl"] = parent.name + "()"
                        elif not arg_modifier:
                            pass
                        elif arg_modifier == token.STAR:
                            arg.attrs["citdl"] = "tuple"
                            arg.attrs["attributes"] = "varargs"
                        elif arg_modifier == token.DOUBLESTAR:
                            arg.attrs["citdl"] = "dict"
                            arg.attrs["attributes"] = "kwargs"
                elif ctype == python_symbols.tfpdef:
                    # `def foo((a,b)=(1,2)):`
                    # Note: This syntax has been dropped from Python 3.
                    assert arg is None
                    tfplist = child.children[1] # the bit between '(' and ')'
                    arg_names = tfplist.children[::2]
                    assert set(a.type for a in arg_names) == set([token.NAME]), \
                        "unexpected tfplist: %r" % tfplist
                    for a in arg_names:
                        func.add_argument(a.value)
                elif ctype == token.COMMA:
                    arg = arg_modifier = None
                elif ctype in (token.STAR, token.DOUBLESTAR):
                    arg_modifier = ctype
                elif ctype == token.EQUAL:
                    pass
                # The rest are tokens after the '=' for a default arg value.
                elif arg is not None:
                    # arg is None if hit tfpdef syntax above.
                    citdl = self._citdl_from_node(child)
                    if citdl:
                        arg.attrs["citdl"] = citdl

    def visit_class(self, node):
        parent = self._peek_scope()
        children = node.children

        body = children[-1]  # `simple_stmt` for one-liner, `suite` otherwise
        last_leaf = body.children[-1]
        lineend = ((last_leaf.lineno - 2)
            if last_leaf.type == token.DEDENT else last_leaf.lineno)
        name = children[1].value

        attrs = {
            "line": str(children[0].lineno),
            "lineend": str(lineend),
        }
        if node.doc:
            attrs["doc"] = node.doc

        # Classrefs.
        if children[2].type == token.LPAR:
            idx = 3
            classrefs = []
            while True:
                c = children[idx]
                if c.type == token.RPAR:
                    break
                elif c.type == token.NAME:
                    classrefs.append(c.value)
                else:
                    #XXX This check is only here because I don't have a feel for
                    #    the possible syntax here.
                    assert c.type == token.COMMA, "unexpected classrefs token: %r" % c
                idx += 1
            if classrefs:
                attrs["classrefs"] = ' '.join(classrefs)

        class_ = parent.add_scope("class", name, **attrs)
        self._push_scope(class_)


#---- internal stuff

def _isint(s):
    try:
        int(s)
    except ValueError:
        return False
    else:
        return True

_traverse_scope_types = (
    python_symbols.funcdef,
    python_symbols.classdef,
)
def _traverse(nodes, _offset=None):
    """Helper for AST traversal.

    XXX 'splain
    """
    global _traverse_scope_types
    top = _offset is None
    if _offset is None:
        _offset = 0
    #TODO: PERF issues of islice versus `nodes[_offset]`
    for node in itertools.islice(nodes, _offset, len(nodes)):
        if node.type in _traverse_scope_types:
            # Pull out docstring, if any, and attach to node.
            body = node.children[-1]  # `simple_stmt` for one-liner, `suite` otherwise
            if body.type == python_symbols.suite:
                # Child 0 is NEWLINE, child 1 is INDENT.
                docstring_node = body.children[2]
                offset = 3
            else:
                assert body.type == python_symbols.simple_stmt
                docstring_node = body
                offset = 1
            if (isinstance(docstring_node, pytree.Node)
                and docstring_node.children[0].type == token.STRING):
                #TODO:XXX move off "self"
                doc = _docstring_from_node(docstring_node.children[0])
            else:
                offset = 0
                doc = None
            node.doc = doc

            yield node
            for n in _traverse(body.children, offset):
                yield n
            yield "end"
        elif node.type == python_symbols.if_stmt:
            # Handle each "suite" in the children. There is a pattern.
            i = 0
            children = node.children
            suites = []
            while i < len(children):
                control = children[i].value
                if control in ("if", "elif"):
                    suites.append(children[i+3])
                    i += 4
                elif control == "else":
                    suites.append(children[i+2])
                    i += 3
            for suite in suites:
                for n in _traverse(suite.children, 0):
                    yield n
        elif isinstance(node, pytree.Node):
            yield node
    if top:
        yield "end"

def _docstring_from_node(node):
    """Return the docstring content for the given docstring node."""
    CLIP_LENGTH = 2000
    s = node.value
    #TODO: Python 3's 'b' necessary?
    s = s.lstrip("urb")  # Strip potential leading string modifiers.
    if s.startswith('"""'):
        s = s[3:-3]
    elif s.startswith("'''"):
        s = s[3:-3]
    else:
        assert s[0] in ('"', "'")
        s = s[1:-1]
    return s[:CLIP_LENGTH]
if True:
    #XXX Use the docstring processing in pythoncile.py to ease comparison.
    # When they compare well, then can turn preferred doc processing back on.
    _preferred_docstring_from_node = _docstring_from_node
    def _docstring_from_node(node):
        s = _preferred_docstring_from_node(node)
        lines = util.parseDocSummary(s.splitlines(0))
        return '\n'.join(lines)


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


#---- public module interface

def scan(content, filename, md5sum=None, mtime=None, lang="Python"):
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

    if type(filename) == types.UnicodeType:
        filename = filename.encode('utf-8')
    # The 'path' attribute must use normalized dir separators.
    if sys.platform.startswith("win"):
        path = filename.replace('\\', '/')
    else:
        path = filename
    fileAttrs = {"language": "Python",
                 "generator": "Python",
                 "path": path}

    try:
        tree2 = pythoncile2(path, content).find('file').find('scope')
        #print >> sys.stderr, ("******************", tree2, tree2.tag, tree2.attrib); sys.stderr.flush()
        #assert False, ('===============', tree2.getchildren()[0].attrib)
        if tree2.get('error'):
            raise Exception(tree2.get('error'))
        if _gClockIt: sys.stdout.write(" (ast:%.3fs)" % (_gClock()-_gStartTime))
    except Exception, ex:
        fileAttrs["error"] = str(ex)
        file = '    <file%s/>' % getAttrStr(fileAttrs)
    else:
        if tree2 is None:
            # This happens, for example, with:
            #   foo(bar, baz=1, blam)
            fileAttrs["error"] = "could not generate AST"
            file = '    <file%s/>' % getAttrStr(fileAttrs)
        else:
            pretty_tree_from_tree(tree2)
            cix2 = ET.tostring(tree2, "utf-8")
            fileAttrs["md5"] = md5sum
            fileAttrs["mtime"] = mtime
            moduleName = os.path.splitext(os.path.basename(filename))[0]
            
            if _gClockIt: sys.stdout.write(" (walk:%.3fs)" % (_gClock()-_gStartTime))
            if log.isEnabledFor(logging.INFO):
                # Dump a repr of the gathering info for debugging
                # - We only have to dump the module namespace because
                #   everything else should be linked from it.
                for nspath, namespace in visitor.st.items():
                    if len(nspath) == 0: # this is the module namespace
                        pprint.pprint(namespace)
            file = '    <file%s>\n\n%s\n    </file>'\
                   % (getAttrStr(fileAttrs), cix2)
            if _gClockIt: sys.stdout.write(" (getCIX:%.3fs)" % (_gClock()-_gStartTime))

    cix = '''\
<?xml version="1.0" encoding="UTF-8"?>
<codeintel version="0.1">
%s
</codeintel>
''' % file

    return cix


#---- mainline

class _NoReflowFormatter(optparse.IndentedHelpFormatter):
    """An optparse formatter that does NOT reflow the description."""
    def format_description(self, description):
        return description or ""

def main(argv=None):
    if argv is None:
        argv = sys.argv
    if not logging.root.handlers:
        logging.basicConfig()

    usage = "usage: %prog [PATHS...]"
    version = "%prog "+__version__
    parser = optparse.OptionParser(prog="pythoncile2", usage=usage,
        version=version, description=__doc__,
        formatter=_NoReflowFormatter())
    parser.add_option("-v", "--verbose", dest="log_level",
                      action="store_const", const=logging.DEBUG,
                      help="more verbose output")
    parser.add_option("-q", "--quiet", dest="log_level",
                      action="store_const", const=logging.ERROR,
                      help="less verbose output (only show errors)")
    parser.add_option("-c", "--compare", action="store_true",
                      help="run against pythoncile.py as well (for testing)")
    parser.set_defaults(log_level=logging.INFO, compare=False)
    opts, paths = parser.parse_args(argv)
    log.setLevel(opts.log_level)
    assert len(paths) == 1, "usage: pythoncile2.py PATH"
    path = paths[0]

    try:
        tree2 = pythoncile2(path)
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

    pretty_tree_from_tree(tree2)
    cix2 = ET.tostring(tree2, "utf-8")

    if opts.compare:
        cix1 = _pythoncile_cix_from_path(path)
        if log.isEnabledFor(logging.DEBUG):
            print "-- pythoncile1 %s" % path
            print cix1
            print "-- pythoncile2 %s" % path
            print cix2

        # Normalizing for comparison.
        tree1 = ET.fromstring(cix1)
        # - mtime slightly different
        tree1[0].set("mtime", tree2[0].get("mtime"))
        # - pythoncile.py seems to put <import>'s at the top of the scope.
        #   We'll just get tree2 to look like that.
        for scope in tree2.getiterator("scope"):
            if scope.get("ilk") not in ("blob", "function"):
                continue
            indeces = []
            n = 0
            for i, child in enumerate(scope[:]):
                if child.tag == "import":
                    imp = scope[i]
                    del scope[i]
                    scope.insert(n, imp)
                    n += 1
        # - pythoncile2.py set citdl=tuple for 'varargs' arguments, and
        #   citdl=dict for 'kwargs' arguments
        for arg in tree1.getiterator("variable"):
            if arg.get("ilk") != "argument":
                continue
            if arg.get("attributes") == "varargs":
                arg.set("citdl", "tuple")
            elif arg.get("attributes") == "kwargs":
                arg.set("citdl", "dict")
        # - pythoncile2.py will set citdl=None if for `foo(a=None)`, pythoncile.py
        #   does not
        for arg in tree2.getiterator("variable"):
            if arg.get("ilk") != "argument":
                continue
            if arg.get("citdl") == "None":
                del arg.attrib["citdl"]
        # - Just can't agree on 'lineend' value for functions and classes right now.
        #   TODO:XXX Need to eventually make sure that the new lineends
        #            make sense! The main current diff is that pythoncile2
        #            includes trailing comment lines, even it not indented.
        #            I think that is fine -- might even be helpful.
        for scope in tree1.getiterator("scope"):
            if scope.get("ilk") in ("function", "class") and scope.get("lineend"):
                del scope.attrib["lineend"]
        for scope in tree2.getiterator("scope"):
            if scope.get("ilk") in ("function", "class") and scope.get("lineend"):
                del scope.attrib["lineend"]
        # - pythoncile.py incorrectly normalizes double-quotes in function signature
        #   argument default values to single quotes. This normalization will get it
        #   wrong for quotes in quotes.
        for func in tree2.getiterator("scope"):
            if func.get("ilk") == "function":
                sig = func.get("signature")
                if '"' in sig:
                    func.set("signature", sig.replace('"', "'"))
        pretty_tree_from_tree(tree2)
        norm_cix2 = ET.tostring(tree2, "utf-8")
        pretty_tree_from_tree(tree1)
        norm_cix1 = ET.tostring(tree1, "utf-8")

        import difflib
        diff = difflib.unified_diff(
                norm_cix1.splitlines(1),
                norm_cix2.splitlines(1),
                "pythoncile %s (normalized)" % path,
                "pythoncile2 %s (normalized)" % path)
        diff = ''.join(list(diff))
        if diff:
            print diff
    else:
        sys.stdout.write(cix2)


def _pythoncile_cix_from_path(path):
    import subprocess
    argv = [sys.executable, join(_komodo_src_dir, "sdk", "bin", "codeintel.py"),
            'scan', '-p', path]
    p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if stderr:
        lines = [line for line in stderr.splitlines(0)
                 if "error registering" not in line]
        print '\n'.join(lines)
    return stdout

if __name__ == "__main__":
    #sys.exit( main(sys.argv) )
    sys.exit( main(['/home/mikei/tmp/t.py']) )
