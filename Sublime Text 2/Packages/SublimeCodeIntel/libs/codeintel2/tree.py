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

"""New citree-based codeintel evaluation engine.

A 'citree' is basically an ElementTree of a CIX document with some tweaks.
The idea is to use these for completion/calltip evaluation instead of the
CIDB. This is mainly about performance but also about fixing some
limitations, bugs, and having a better code design (i.e. where lang-specific
quirks can be dealt with cleanly).
"""

import sys
from os.path import normpath
import logging
import re

import ciElementTree as ET
if not getattr(ET, "_patched_for_komodo_", False):
    import warnings
    warnings.warn("Not using codeintel's patched elementtree: "
                  "this may cause problems")

from codeintel2.common import *
from codeintel2.citadel import CitadelEvaluator


log = logging.getLogger("codeintel.tree")

CIX_VERSION = "2.0"


def tree_2_0_from_tree_0_1(tree):
    """Convert CIX 0.1 to CIX 2.0."""
    # - update some of the no longer used <file> attributes
    #   - drop "generator"
    try:
        del tree[0].attrib["generator"]
    except KeyError:
        pass
    #   - drop 'md5' and 'mtime' on the <file> tag
    try:
        del tree[0].attrib["md5"]
    except KeyError:
        pass
    try:
        del tree[0].attrib["mtime"]
    except KeyError:
        pass
    #   - move "language" attribute on <file> to "lang" and to "lang" on
    #     <module> (New multi-lang CIX output will allow one file to
    #     have modules of different langs.)
    for file in tree.getiterator("file"):
        lang = file.get("language")
        if lang is not None:
            file.set("lang", lang)
            for module in file.getiterator("module"):
                if module.get("lang") is None:
                    module.set("lang", lang)
            try:
                del file.attrib["language"]
            except KeyError:
                # Be tolerant of transitional CIX.
                pass

    # - move <doc> and <signature> optional sub tags into parent
    #   attribute
    #PERF: This could be done better.
    for tag in ("variable", "function", "class", "module", "interface",
                "argument", "classref", "interfaceref"):
        for node in tree.getiterator(tag):
            for child in reversed(node):
                # reversed() so can modify while iterating over
                if child.tag == "signature":
                    if child.text: # be tolerant of <signature />
                        node.set("signature", child.text)
                    node.remove(child)
                elif child.tag == "doc":
                    if child.text: # be tolerant of <doc />
                        node.set("doc", child.text)
                    node.remove(child)
            if not node: # no children now
                node.text = None

    # - move non-variable tags to attributes
    #   (XXX currently <classref> and <interfaceref> tags are not moved)
    for tag in ("variable", "argument", "classref", "interfaceref"):
        for node in tree.getiterator(tag):
            for child in reversed(node):
                if child.tag == "type":
                    node.set("citdl", child.get("type"))
                    node.remove(child)
            if not node: # no remaining children
                node.text = None
            if tag == "argument":
                node.tag = "variable"
                node.set("ilk", "argument")

    # - move <returns> to a <function> attribute
    for node in tree.getiterator("function"):
        for child in reversed(node): #PERF: could just check last child
            if child.tag == "returns":
                assert child[0].tag == "type"
                node.set("returns", child[0].get("type"))
                node.remove(child)

    # - move classrefs and interfacerefs to attributes
    #   Note: <classref attribute="__mixin__"> => "mixinrefs" attribute.
    #   This is used by Ruby (though not used for eval, yet).
    for scope_ilk in ("class", "interface"):
        for node in tree.getiterator(scope_ilk):
            interfacerefs = []
            classrefs = []
            mixinrefs = []
            for child in reversed(node):
                if child.tag == "classref":
                    if "__mixin__" in child.get("attributes", ""):
                        mixinrefs.append(child.get("citdl")
                                         or child.attrib["name"])
                    else:
                        classrefs.append(child.get("citdl")
                                         or child.attrib["name"])
                    node.remove(child)
                elif child.tag == "interfaceref":
                    interfacerefs.append(child.get("citdl")
                                         or child.attrib["name"])
                    node.remove(child)
            if classrefs:
                classrefs.reverse()
                assert not [c for c in classrefs if ' ' in c]
                node.set("classrefs", ' '.join(classrefs))
            if interfacerefs:
                interfacerefs.reverse()
                assert not [i for i in interfacerefs if ' ' in i]
                node.set("interfacerefs", ' '.join(interfacerefs))
            if mixinrefs:
                mixinrefs.reverse()
                assert not [m for m in mixinrefs if ' ' in m]
                node.set("mixinrefs", ' '.join(mixinrefs))
            if len(node) == 0:
                node.text = None

    # - make all scope tags a "scope" tag (easier for elem.find() usage)
    for tag in ("class", "function", "interface", "module"):
        for node in tree.getiterator(tag):
            node.tag = "scope"
            if tag == "class" and "__namespace__" in node.get("attributes", ""):
                node.set("ilk", "namespace")
                attributes = node.get("attributes").split()
                attributes.remove("__namespace__")
                if not attributes:
                    del node.attrib["attributes"]
                else:
                    node.set("attributes", ' '.join(attributes))
            elif tag == "module":
                node.set("ilk", "blob")
            else:
                node.set("ilk", tag)

    tree.set("version", "2.0")
    return tree

def tree_from_cix_path(cix_path):
    """Return a (ci)tree for the CIX content in the given path.

    Raises pyexpat.ExpatError if the CIX content could not be parsed.
    """
    tree = ET.parse(cix_path).getroot()
    version = tree.get("version")
    if version == CIX_VERSION:
        return tree
    elif version == "0.1":
        return tree_2_0_from_tree_0_1(tree)
    else:
        raise CodeIntelError("unknown CIX version: %r" % version)


def tree_from_cix(cix):
    """Return a (ci)tree for the given CIX content.

    Raises pyexpat.ExpatError if the CIX content could not be parsed.
    """
    if isinstance(cix, unicode):
        cix = cix.encode("UTF-8", "xmlcharrefreplace")
    tree = ET.XML(cix)
    version = tree.get("version")
    if version == CIX_VERSION:
        return tree
    elif version == "0.1":
        return tree_2_0_from_tree_0_1(tree)
    else:
        raise CodeIntelError("unknown CIX version: %r" % version)


def pretty_tree_from_tree(tree, indent_width=2):
    """Add appropriate .tail and .text values to the given tree so that
    it will have a pretty serialization.

    Note: This modifies the tree *in-place*.
    Presumption: This is a CIX 2.0 tree.
    """
    INDENT = ' '*indent_width

    def _prettify(elem, indent_level=0):
        if elem: # i.e. has children
            elem.text = '\n' + INDENT*(indent_level+1)
            for child in elem:
                _prettify(child, indent_level+1)
            elem[-1].tail = '\n' + INDENT*indent_level
            elem.tail = '\n' + INDENT*indent_level
        else:
            elem.text = None
            elem.tail = '\n' + INDENT*indent_level

    _prettify(tree)
    return tree


def check_tree(tree):
    """Generate warnings/errors for common mistakes in CIX trees.

    Yields tuples of the form:
        ("warning|error", <msg>)
    """
    assert tree.tag == "codeintel",\
        "can only check starting from <codeintel> element"
    assert tree.get("version") == CIX_VERSION, \
        "can only check CIX v%s trees" % CIX_VERSION

    # - file 'lang' is set, not 'language' 
    file = tree[0]
    if not file.get("lang"):
        yield ("error", "no 'lang' attr on <file> element")
    if file.get("language"):
        yield ("warning", "'language' attr on <file> element is obsolete,"
                          "use 'lang'")

    for blob in file:
        if blob.get("ilk") != "blob":
            yield ("error", "element under <file> is not ilk=blob: %r" % blob)
        # - blob 'lang' is set
        if not blob.get("lang"):
            yield ("error", "no 'lang' attr on <blob> element: %r" % blob)

        # - classrefs are space separated, not with commas (warn)
        for class_elem in blob.getiterator("scope"):
            if class_elem.get("ilk") != "class": continue
            classrefs = class_elem.get("classrefs")
            if not classrefs: continue
            if ',' in classrefs:
                yield ("warning", "multiple class references in 'classrefs' "
                                  "attr on class scopes must be "
                                  "space-separated: %r may be using "
                                  "comma-separation: %r"
                                  % (class_elem, classrefs))


class TreeEvaluator(CitadelEvaluator):
    def get_start_scoperef(self):
        linenum = self.line + 1 # convert to 1-based
        try:
            blob = self.buf.blob_from_lang[self.trg.lang]
        except KeyError:
            raise EvalError("no %s scan info for %r" % (self.lang, self.buf))
        return self.buf.scoperef_from_blob_and_line(blob, linenum)

    def eval(self, mgr):
        self.mgr = mgr
        self.citadel = mgr.citadel

        if self.ctlr.is_aborted():
            self.ctlr.done("aborting")
            return
        self.ctlr.info("eval %s  %s", self, self.trg)

        self.pre_eval()

        try:
            if self.trg.form == TRG_FORM_CPLN:
                cplns = self.eval_cplns()
                if cplns:
                    cplns = self.post_process_cplns(cplns)
                self.info("    cplns: %r", cplns)
                if cplns:
                    self.ctlr.set_cplns(cplns)
            elif self.trg.form == TRG_FORM_CALLTIP:
                calltips = self.eval_calltips()
                if calltips:
                    calltips = self.post_process_calltips(calltips)
                self.info("    calltips: %r", calltips)
                if calltips:
                    self.ctlr.set_calltips(calltips)
            else:  # self.trg.form == TRG_FORM_DEFN
                defns = self.eval_defns()
                if defns:
                    defns = self.post_process_defns(defns)
                self.info("    defns: %r", defns)
                if defns:
                    self.ctlr.set_defns(defns)
            self.ctlr.done("success")
        except CodeIntelError, ex:
            #XXX Should we have an error handling hook here?
            self.ctlr.error("evaluating %s: %s", self, ex)
            self.ctlr.done("eval error")
        except Exception:
            log.exception("Unexpected error with evaluator: %s", self)
            # Must still mark done on the ctlr to avoid leaks - bug 65502.
            self.ctlr.done("eval error")

    def scope_stack_from_tree_and_linenum(self, tree, linenum):
        """Get the start scope for the given line.

            "linenum" appears to be 0-based, however all CIX line data
                is 1-based so we'll convert here.
    
        Dev Notes:
        - XXX Add built-in scope.
        """
        linenum += 1 # convert to 1-based
        #XXX This is presuming that the tree has only one blob.
        scope_stack = [tree.find("file/scope")]
        while True:
            next_scope_could_be = None
            # PERF: Could make this a binary search if a scope has *lots* of
            # subscopes.
            for scope in scope_stack[-1].findall("scope"):
                start = int(scope.get("line"))
                if start <= linenum \
                   and (not scope.get("lineend")
                        or linenum <= int(scope.get("lineend"))):
                    next_scope_could_be = scope
                elif start > linenum:
                    break
            if next_scope_could_be is not None:
                scope_stack.append(next_scope_could_be)
            else:
                break
        return scope_stack
    
    #TODO: split out '()' as a separate token.
    def _tokenize_citdl_expr(self, citdl):
        for token in citdl.split('.'):
            yield token
    def _join_citdl_expr(self, tokens):
        return '.'.join(tokens)

    def str_elem(self, elem):
        if elem.tag == "scope":
            return "%s %s" % (elem.get("ilk"), elem.get("name"))
        else:
            return "%s %s" % (elem.tag, elem.get("name"))
    def str_elem_and_children(self, elem):
        s = [self.str_elem(elem)]
        for child in elem:
            s.append(self.str_elem(child))
        return "%s: %s" % (self.str_elem(elem),
                           ', '.join(self.str_elem(c) for c in elem))

    def str_import(self, elem):
        # c.f. cb.py::getDescForImport()
        module = elem.get("module")
        symbol = elem.get("symbol")
        alias = elem.get("alias")
        if alias and symbol:
            s = "from %(module)s import %(symbol)s as %(alias)s" % locals()
        elif alias:
            s = "import %(module)s as %(alias)s" % locals()
        elif symbol:
            s = "from %(module)s import %(symbol)s" % locals()
        else:
            s = "import %(module)s" % locals()
        return s

    # logging funcs (perhaps best on controller)
    def log_start(self):
        self._log = []
    def log(self, msg, *args, **kwargs):
        """
            kwargs:
                "cached" (boolean) indicates if result was from cache
        """
        log_indent = ' '*4
        if True:    # just print as we go
            if args:
                s = [msg % args]
            else:
                s = [msg]
            if kwargs.get("cached"):
                s.append(" (cached)")
            self.info(''.join(s))
        else:       # capture log for latter printing
            self._log.append(msg, args, kwargs)

    def pre_eval(self):
        self.curr_tree = self.buf.tree
        #ET.dump(self.curr_tree)

    def _eval_citdl_expr(self, expr, scope_stack):
        """Return the citree node for the given CITDL expression.
        
            os.environ.get() -> <class 'str' on stdlib blob 'built-in'>
        """
        tokens = list(self._tokenize_citdl_expr(expr))
        assert tokens, "have to adjust handling if no tokens"
        obj = self._eval_citdl_token(tokens[0], scope_stack)

        for i, token in enumerate(tokens[1:]):
            if token.endswith("()"):
                token = token[-2:]
                call = True
            else:
                call = False

            if obj.tag == "import":
                obj = self._eval_import_getattr(obj, token,
                        self._join_citdl_expr(tokens[:i+2]))
            else:
                obj = self._eval_getattr(obj, token,
                        self._join_citdl_expr(tokens[:i+2]))

            if call:
                raise CodeIntelError("_eval_citdl_expr(%r): not handling "
                                     "call on %r "
                                     % (expr, self.str_elem(obj)))

        if obj.tag == "import":
            raise CodeIntelError("_eval_citdl_expr: cannot return import "
                                 "<%s>: need to resolve it"
                                 % self.str_import(obj))
        return obj

    def _resolve_import(self, module_name, symbol_name=None):
        """Return a loaded citree node for the given import info.

            "module_name" is the name of the module to import.
            "symbol_name" (if given) is the attribute on that module to
                return.
        """
        #TODO: get logging right
        #XXX All the logging stuff should go on the controller and that
        #    should get passed in here for appropriate logging of this
        #    eval.
        #XXX Will this screw up for, e.g. in Python:
        #    'import codeintel.utils'?
        import_handler = self.citadel.import_handler_from_lang(self.lang)
        module = import_handler.import_blob_name(
                    module_name, self.buf.libs, self.ctlr)
        self.log("module '%s' imports <%s>", module_name,
                 self.str_elem(module))

        if symbol_name:
            #XXX logging won't be right here
            return self._eval_getattr(module, symbol_name,
                    "%s.%s" % (module_name, symbol_name))
            #XXX Here is the _eval_getattr code to duplicate.
            # self.log("lookup '%s' on <%s>:", name, self.str_elem(obj))
            # for child in obj:
            #     if child.get("name") == name:
            #         attr = child
            #         self.log("'%s' is <%s>", citdl_expr, self.str_elem(child))
            #         return attr
            # else:
            #     raise CodeIntelError("couldn't find '%s' attribute on <%s>"
            #                          % (name, self.str_elem(obj)))
        else:
            return module

    def _eval_import(self, imp, name):
        """Return the object imported, if any, with the given import
        node (in a citree) and name.

        Return value: If successful it returns the citree node imported.
        If 'name' was not found in a '*'-import then None is returned
        (e.g. it is not exceptional that 'from os import *' does not
        import 'fuzzywuzzy'). If the import could not be resolved, but
        it looks like it should have been, then an error is raised.
        """
        # One of these:
        #   'os' may be from <import os>:
        #       ...
        #       'os' is <blob os>
        #   'os' is from <import os>: <blob os> (cached)
        #
        #Python
        #if non-* import and matches:
        # 'os' is from <import os>
        # is <import os> from <project foo>? no
        # ...
        # is <import os> from <python-2.4-stdlib>? yes: <blob os>
        # 'os' is <blob os>
        #
        # 'dirname' may be from <from os.path import *>:
        #     is <from os.path import *> from <project foo>? no
        #     ...
        #     is <from os.path import *> from <python-2.4-stdlib>? yes: <blob os.path>

        # TOTEST:
        # - 'from xml import dom', does that get it right? I doubt it.
        
        module_name = imp.get("module")
        symbol_name = imp.get("symbol")
        alias = imp.get("alias")
        obj = None
        if alias: 
            if alias == name:   # <import foo as name> or <from foo import bar as name>
                self.log("'%s' is from <%s>", name, self.str_import(imp))
                return self._resolve_import(module_name, symbol_name)
        elif symbol_name:
            assert symbol_name != "**", "only Perl should be using '**' for imports"
            if symbol_name == "*":   # <from foo import *>
                self.log("'%s' may be from <%s>", name, imp)
                #XXX some variation of _resolve_import to specify just
                #    importing the module.
                try:
                    module = self._resolve_import(module_name)
                except CodeIntelError, ex: # use equivalent of NoModuleEntry?
                    self.warn("could not resolve '%s' import to handle <%s>",
                              module_name, self.str_import(imp))
                    return None
                #TODO:
                # see if name in export list (__all__ for Python,
                #   @EXPORT for Perl, default all top-level symbols)
                # if so, eval getattr of name on module object
                self.warn("not handling <%s>!", self.str_import(imp))
            if symbol_name == name:  # <from foo import name>
                self.log("'%s' is from <%s>", name, self.str_import(imp))
                return self._resolve_import(module_name, symbol_name)
        elif module_name == name:    # <import foo>
            self.log("'%s' is from <%s>", name, self.str_import(imp))
            return self._resolve_import(module_name)
        return None

    def _eval_citdl_token(self, token, scope_stack):
        start_scope_str = self.str_elem(scope_stack[-1])
        self.log("eval '%s' at <%s>:", token, start_scope_str)

        while scope_stack:
            scope = scope_stack.pop()
            self.log("is '%s' accessible on <%s>?",
                     token, self.str_elem(scope))
            for child in reversed(scope):
                # Check children in reverse because last definition in
                # file wins. A correct refinement *for the top-level*
                # would be to skip anything defined later in the file
                # than the current start position.
                # TODO-PERF: The list of symbols on a scope should be a
                #            dict to speed up this loop. This is complicated
                #            by '*' imports.

                if child.tag == "import":
                    obj = self._eval_import(child, token)
                    if obj:
                        return obj
                elif child.get("name") == token:
                    obj = child
                    if obj.tag == "variable":
                        citdl = obj.get("citdl")
                        if not citdl:
                            self.log("'%s' is <%s> which is of unknown type",
                                     token, self.str_elem(obj))
                            raise CodeIntelError(
                                "don't know type of <%s> on <%s>"
                                % (self.str_elem(obj), self.str_elem(scope)))
                        else:
                            self.log("'%s' is <%s> which is '%s'", token,
                                     self.str_elem(obj), citdl)
                            obj = self._eval_citdl_expr(
                                    citdl, scope_stack+[scope])
                            self.log("'%s' is <%s>", token,
                                     self.str_elem(obj))
                    else:
                        self.log("'%s' is <%s>", token, self.str_elem(obj))
                    return obj
            else:
                continue
        else:
            raise CodeIntelError("couldn't resolve '%s' starting at %s"
                                 % (token, start_scope_str))

    def _defn_from_hit(self, hit):
        elem, (blob, lpath) = hit
        #self.log("_defn_from_hit:: blob: %r", blob)
        #for attr_name, attr_value in blob.attrib.items():
        #    self.log("attr_name: %r, attr_value: %r", attr_name, attr_value)
        #self.log("_defn_from_hit:: elem: %r", elem)

        path = blob.get("src", None)
        name = elem.get("name", None)
        line = elem.get("line", 1) # e.g. for an import, just use the first line
        if line is not None:
            try:
                line = int(line)
            except ValueError:
                line = 1
        ilk = elem.get("ilk") or elem.tag
        citdl = elem.get("citdl", None)
        doc = elem.get("doc", None)
        signature = elem.get("signature", None)
        attributes = elem.get("attributes", None)
        returns = elem.get("returns", None)

        # Only fixup paths that do not look like URIs.
        if path and not re.match(r"^\w+:\/\/", path):
            if sys.platform == "win32":
                path = path.replace('/', '\\') # unnormalize path
            path = normpath(path)  # remove possible '.' and '..' elements
        defn = Definition(blob.get("lang"), path, blob.get("name"), lpath,
                          name, line, ilk, citdl, doc,
                          signature, attributes, returns)
        return defn

    # The SENTINEL_MAX_EXPR_COUNT could probably be *reduced*.
    # Note: This is an approximation that we are infinitely looping
    # on the same evaluation. The *actual* appropriate key would be:
    #
    #   (expr, scoperef)
    #
    # but that is overkill for now, I think.
    _SENTINEL_MAX_EXPR_COUNT = 10
    _eval_count_from_expr = None
    def _check_infinite_recursion(self, expr):
        if self._eval_count_from_expr is None:
            # Move this init into eval() when on TreeEvalutor.
            self._eval_count_from_expr = {}
        eval_count = self._eval_count_from_expr.get(expr, 0)
        eval_count += 1
        if eval_count >= self._SENTINEL_MAX_EXPR_COUNT:
            raise EvalError("hit eval sentinel: expr '%s' eval count "
                            "is %d (abort)" % (expr, eval_count))
        self._eval_count_from_expr[expr] = eval_count


#---- internal support stuff

def _dump_element(elem, indent=''):
    """Dump an element tree without using ET.dump() which
    (1) uses XML syntax,
    (2) can blow up if an attribute is set to None accidentally.

    This is only useful for debugging.
    """
    s = "%selement '%s': %s" % (indent, elem.tag, elem.attrib)
    print s
    for child in elem:
        _dump_element(child, indent+'  ')





