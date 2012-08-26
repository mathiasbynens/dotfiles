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

"""Completion evaluation code for PHP"""

from codeintel2.common import *
from codeintel2.tree import TreeEvaluator
from codeintel2.util import make_short_name_dict, banner


php_magic_global_method_data = {
    "__autoload"  : "__autoload(string $className)\n"
                    "This function is automatically called when a class\n"
                    "is being called, but which hasn't been defined yet.",
}
php_magic_class_method_data = {
    "__construct" : "__construct([mixed $args [, $...]])\n"
                    "Initializes a newly created class instance.\n"
                    "Note: parent constructors will need to be implictly\n"
                    "called.",
    "__destruct"  : "__destruct()\n"
                    "This function is called when all references to this\n"
                    "particular class instance are removed or when the\n"
                    "object is explicitly destroyed.\n"
                    "Note: parent destructors will need to be implictly\n"
                    "called.",
    "__call"      : "__call(string $name, array $arguments) -> mixed\n"
                    "Is triggered when your class instance (and inherited\n"
                    "classes) does not contain the method name.",
    "__callStatic": "__callStatic(string $name, array $arguments) -> mixed\n"
                    "Is triggered when your class is accessed statically\n"
                    "and it does not contain the method name.",
    "__get"       : "__get(string $name) -> mixed\n"
                    "Is triggered when your class instance (and inherited\n"
                    "classes) does not contain the member or method name.",
    "__set"       : "__set(string $name, mixed $value)\n"
                    "Is triggered when your class instance (and inherited\n"
                    "classes) does not contain the member or method name.",
    "__isset"     : "__isset(string $name) -> bool\n"
                    "Overload the isset function for the class instance.",
    "__unset"     : "__unset(string $name)\n"
                    "Overload the unset function for the class instance.",
    "__sleep"     : "__sleep() -> array\n"
                    "Called through serialize in order to generate a\n"
                    "storable representation of a class instance. Returns\n"
                    "an array of the variable names that need to\n"
                    "be stored.",
    "__wakeup"    : "__wakeup()\n"
                    "Called through unserialize after restoring a\n"
                    "a class instance with it's serialized values.",
    "__toString"  : "__toString() -> string\n"
                    "Returns a string representation of the class instance.",
    "__set_state" : "__set_state(array $properties)\n"
                    "Static method that is called to restore a class\n"
                    "instance's state that was previously exported\n"
                    "using the var_export() function. Properties are\n"
                    "in the form array('property' => value, ...).",
    "__clone"     : "__clone()\n"
                    "When the class instance is cloned using the\n"
                    "clone($object) function call, a new class instance\n"
                    "is created with shallow copies of all $object's\n"
                    "values. This function is then called after to allow\n"
                    "the new instance to update any of these values.",
}
php_keyword_calltip_data = {
    "array"       : "array(<list>)\n"
                    "Create a PHP array.",
    "declare"     : "declare(directive)\n"
                    "Set execution directives for a block of code.\n",
    "echo"        : "echo($arg1 [, $arg2... ])\n"
                    "Output one or more strings.",
    "eval"        : "eval($code) => mixed\n"
                    "Evaluate the $code string as PHP code.",
    "exit"        : "exit($status)\n"
                    "$status can be either a string or an int.\n"
                    "Outputs $status and then terminates the current script.\n"
                    "If status is an integer, that value will also be used as\n"
                    "the exit status. Exit statuses should be in the range 0\n"
                    "to 254, the exit status 255 is reserved by PHP and shall\n"
                    "not be used. The status 0 is used to terminate the\n"
                    "program successfully. PHP >= 4.2.0 does NOT print the\n"
                    "status if it is an integer.",
    "include"     : "include(file_path)\n"
                    "Includes and evaluates the specified file, produces a\n"
                    "Fatal Error on error.",
    "include_once": "include_once(file_path)\n"
                    "Includes and evaluates the specified file if it hasn't\n"
                    "been included before, produces a Fatal Error on error.",
    "print"       : "print($arg)\n"
                    "Output the $arg string.",
    "require"     : "require(file_path)\n"
                    "Includes and evaluates the specified file, produces a\n"
                    "Fatal Error on error.",
    "require_once": "require_once(file_path)\n"
                    "Includes and evaluates the specified file if it hasn't\n"
                    "been included before, produces a Fatal Error on error.",
}


class PHPTreeEvaluator(TreeEvaluator):
    """
    scoperef: (<blob>, <lpath>) where <lpath> is list of names
        self._elem_from_scoperef()
    hit: (<elem>, <scoperef>)
    """

    # Calltips with this expression value are ignored. See bug:
    # http://bugs.activestate.com/show_bug.cgi?id=61497
    php_ignored_calltip_expressions = ("if", "elseif",
                                       "for", "foreach",
                                       "while",
                                       "switch",
                                      )

    php_magic_global_method_cplns = [ ("function", name) for name in
                sorted(php_magic_global_method_data.keys()) ]
    # Classes can use both global and class specific functions.
    php_magic_class_method_cplns = [ ("function", name) for name in
                sorted(php_magic_class_method_data.keys()) ]

    # A variable used to track the recursion depth of _hit_from_citdl().
    eval_depth = 0

    #TODO: candidate for base TreeEvaluator class
    _langintel = None
    @property
    def langintel(self):
        if self._langintel is None:
            self._langintel = self.mgr.langintel_from_lang(self.trg.lang)
        return self._langintel

    #TODO: candidate for base TreeEvaluator class
    _libs = None
    @property
    def libs(self):
        if self._libs is None:
            self._libs = self.langintel.libs_from_buf(self.buf)
        return self._libs

    def get_next_scoperef(self, scoperef):
        blob, lpath  = scoperef
        elem = self._elem_from_scoperef(scoperef)
        linenum = self.line + 1 # convert to 1-based
        for subelem in elem.getchildren():
            start = int(subelem.get("line"))
            if start > linenum:
                if subelem.tag == "scope":
                    lpath.append(subelem.get("name"))
                break
        return (blob, lpath)

    # Un-comment for an indented log record, each indented level will represent
    # a layer of recursion - which is quite useful for debugging.
    #def log_start(self):
    #    TreeEvaluator.log_start(self)
    #    self.eval_depth = 0
    #def debug(self, msg, *args):
    #    msg = '  ' * self.eval_depth + msg
    #    TreeEvaluator.debug(self, msg, *args)
    #def info(self, msg, *args):
    #    msg = '  ' * self.eval_depth + msg
    #    TreeEvaluator.info(self, msg, *args)
        
    def eval_cplns(self):
        self.log_start()
        self._imported_blobs = {}
        start_scope = self.get_start_scoperef()
        trg = self.trg
        if trg.type == "variables":
            return self._variables_from_scope(self.expr, start_scope)
        elif trg.type == "comment-variables":
            next_scope = self.get_next_scoperef(start_scope)
            return self._comment_variables_from_scope(self.expr, next_scope)
        elif trg.type == "functions":
            # The 3-character trigger, which not actually specific to functions.
            retval = self._keywords_from_scope(self.expr, start_scope) + \
                     self._functions_from_scope(self.expr, start_scope) + \
                     self._constants_from_scope(self.expr, start_scope) + \
                     self._classes_from_scope(self.expr[:3], start_scope) + \
                     self._imported_namespaces_from_scope(self.expr, start_scope)
            #if self.ctlr.is_aborted():
            #    return None
            return retval
        elif trg.type == "classes":
            return self._classes_from_scope(None, start_scope) + \
                   self._imported_namespaces_from_scope(None, start_scope)
        elif trg.type == "namespaces":
            return self._namespaces_from_scope(self.expr, start_scope)
        elif trg.type == "namespace-members" and (not self.expr or self.expr == "\\"):
            # All available namespaces and include all available global
            # functions/classes/constants as well.
            global_scoperef = self._get_global_scoperef(start_scope)
            cplns = self._namespaces_from_scope(self.expr, start_scope)
            cplns += self._functions_from_scope(None, global_scoperef)
            cplns += self._constants_from_scope(None, global_scoperef)
            cplns += self._classes_from_scope(None, global_scoperef)
            return cplns
        elif trg.type == "interfaces":
            return self._interfaces_from_scope(self.expr, start_scope) + \
                   self._imported_namespaces_from_scope(self.expr, start_scope)
        elif trg.type == "magic-methods":
            elem = self._elem_from_scoperef(start_scope)
            if elem.get("ilk") == "function":
                # Use the parent for our check.
                blob, lpath = start_scope
                if len(lpath) > 1:
                    elem = self._elem_from_scoperef((blob, lpath[:-1]))
            if elem.get("ilk") == "class":
                # All looks good, return the magic class methods.
                return self.php_magic_class_method_cplns
            else:
                # Return global magic methods.
                return self.php_magic_global_method_cplns
        elif trg.type == "namespace-members":
            # Find the completions:
            cplns = []
            fqn = self._fqn_for_expression(self.expr, start_scope)
            hits = self._hits_from_namespace(fqn, start_scope)
            if hits:
                #self.log("self.expr: %r", self.expr)
                #self.log("hits: %r", hits)
                cplns = list(self._members_from_hits(hits))
                #self.log("cplns: %r", cplns)
            # Return additional sub-namespaces that start with this prefix.
            if hits and hits[0][0] is not None:
                # We hit a namespace, return additional namespaces that
                # start with the hit's fully qualified name (fqn).
                fqn = hits[0][0].get("name")

            self.debug("eval_cplns:: adding namespace hits that start with "
                       "fqn: %r", fqn)
            namespaces = self._namespaces_from_scope(fqn, start_scope)
            #self.log("namespaces: %r", namespaces)
            for ilk, n in namespaces:
                namespace = n[len(fqn):]
                if namespace and namespace.startswith("\\"):
                    cplns.append((ilk, namespace.strip("\\")))
            return cplns
        else:
            hit = self._hit_from_citdl(self.expr, start_scope)
            if hit[0] is not None:
                self.log("self.expr: %r", self.expr)
                # special handling for parent, explicitly set the
                # protected and private member access for this case
                if self.expr == "parent" or \
                   self.expr.startswith("parent."):
                    self.log("Allowing protected parent members")
                    return list(self._members_from_hit(hit, allowProtected=True,
                                 allowPrivate=False))
                elif self.trg.type == "array-members":
                    return list(self._members_from_array_hit(hit, self.trg.extra.get('trg_char')))
                else:
                    return list(self._members_from_hit(hit))

    def eval_calltips(self):
        self.log_start()
        self._imported_blobs = {}
        start_scope = self.get_start_scoperef()
        # Ignore doing a lookup on certain expressions
        # XXX - TODO: Might be better to do this in trg_from_pos.
        expr = self.expr
        if expr in self.php_ignored_calltip_expressions:
            return None
        elif expr in php_keyword_calltip_data:
            return [ php_keyword_calltip_data.get(expr) ]
        # XXX - Check the php version, magic methods only appeared in php 5.
        elif expr in php_magic_class_method_data:
            elem = self._elem_from_scoperef(start_scope)
            if elem.get("ilk") == "function":
                # Use the parent for our check.
                blob, lpath = start_scope
                if len(lpath) > 1:
                    elem = self._elem_from_scoperef((blob, lpath[:-1]))
            if elem.get("ilk") == "class":
                # Use the class magic methods.
                return [ php_magic_class_method_data[expr] ]
            # Else, let the tree work it out.
        elif expr in php_magic_global_method_data:
            elem = self._elem_from_scoperef(start_scope)
            if elem.get("ilk") == "function":
                # Check the parent is not a class. See:
                # http://bugs.activestate.com/show_bug.cgi?id=69758
                blob, lpath = start_scope
                if len(lpath) > 1:
                    elem = self._elem_from_scoperef((blob, lpath[:-1]))
            if elem.get("ilk") == "class":
                # Not available inside a class.
                return []
            return [ php_magic_global_method_data[expr] ]
        hit = self._hit_from_citdl(expr, start_scope)
        return self._calltips_from_hit(hit)

    def eval_defns(self):
        self.log_start()
        self._imported_blobs = {}
        start_scoperef = self.get_start_scoperef()
        self.info("start scope is %r", start_scoperef)

        hit = self._hit_from_citdl(self.expr, start_scoperef, defn_only=True)
        return [self._defn_from_hit(hit)]

    # Determine if the hit is valid
    def _return_with_hit(self, hit, nconsumed):
        # Added special attribute __not_yet_defined__ to the PHP ciler,
        # this is used to indicate the variable was made but is not yet
        # assigned a type, i.e. it's not yet defined.
        elem, scoperef = hit
        attributes = elem.get("attributes")
        if attributes:
            attr_split = attributes.split(" ")
            if "__not_yet_defined__" in attr_split:
                self.log("_return_with_hit:: hit was a not_yet_defined, ignoring it: %r", hit)
                return False
        self.log("_return_with_hit:: hit is okay: %r", hit)
        return True

    def _element_names_from_scope_starting_with_expr(self, expr, scoperef,
                                                     elem_type, scope_names,
                                                     elem_retriever):
        """Return all available elem_type names beginning with expr"""
        self.log("%s_names_from_scope_starting_with_expr:: expr: %r, scoperef: %r for %r",
                 elem_type, expr, scoperef, scope_names)
        global_blob = self._elem_from_scoperef(self._get_global_scoperef(scoperef))
        # Get all of the imports

        # Start making the list of names
        all_names = set()
        for scope_type in scope_names:
            elemlist = []
            if scope_type == "locals":
                elemlist = [self._elem_from_scoperef(scoperef)]
            elif scope_type == "globals":
                elemlist = [global_blob]
            elif scope_type == "namespace":
                elemlist = []
                namespace = self._namespace_elem_from_scoperef(scoperef)
                if namespace is not None:
                    elemlist.append(namespace)
                    # Note: This namespace may occur across multiple files, so we
                    #       iterate over all known libs that use this namespace.
                    fqn = namespace.get("name")
                    lpath = (fqn, )
                    for lib in self.libs:
                        hits = lib.hits_from_lpath(lpath, self.ctlr,
                                                   curr_buf=self.buf)
                        elemlist += [elem for elem, scoperef in hits]
            elif scope_type == "builtins":
                lib = self.buf.stdlib
                # Find the matching names (or all names if no expr)
                #log.debug("Include builtins: elem_type: %s", elem_type)
                names = lib.toplevel_cplns(prefix=expr, ilk=elem_type)
                all_names.update([n for ilk,n in names])
            # "Include everything" includes the builtins already
            elif scope_type == "imports":
                # Iterate over all known libs
                for lib in self.libs:
                    # Find the matching names (or all names if no expr)
                    #log.debug("Include everything: elem_type: %s", elem_type)
                    names = lib.toplevel_cplns(prefix=expr, ilk=elem_type)
                    all_names.update([n for ilk,n in names])
                # Standard imports, specified through normal import semantics
                elemlist = self._get_all_import_blobs_for_elem(global_blob)
            for elem in elemlist:
                names = elem_retriever(elem)
                if expr:
                    if isinstance(names, dict):
                        try:
                            names = names[expr]
                        except KeyError:
                            # Nothing in the dict matches, thats okay
                            names = []
                    else:
                        # Iterate over the names and keep the ones containing
                        # the given prefix.
                        names = [x for x in names if x.startswith(expr)]
                self.log("%s_names_from_scope_starting_with_expr:: adding %s: %r",
                         elem_type, scope_type, names)
                all_names.update(names)
        return self._convertListToCitdl(elem_type, all_names)

    def _variables_from_scope(self, expr, scoperef):
        """Return all available variable names beginning with expr"""
        # The current scope determines what is visible, see bug:
        #   http://bugs.activestate.com/show_bug.cgi?id=65159
        vars = []
        blob, lpath = scoperef
        if len(lpath) > 0:
            # Inside a function or class, don't get to see globals
            scope_chain = ("locals", "builtins", )
            if len(lpath) > 1:
                # Current scope is inside a class function?
                elem = self._elem_from_scoperef(scoperef)
                if elem is not None and elem.get("ilk") == "function":
                    p_elem = self._elem_from_scoperef((blob, lpath[:-1]))
                    if p_elem is not None and p_elem.get("ilk") == "class":
                        # Include "$this" in the completions.
                        vars = [("variable", "this")]
        else:
            # Already global scope, so get to see them all
            scope_chain = ("locals", "globals", "imports", )
        # XXX - TODO: Move to 3 char trigger (if we want/need to)
        vars += self._element_names_from_scope_starting_with_expr(None,
                            scoperef,
                            "variable",
                            scope_chain,
                            self.variable_names_from_elem)
        if expr:
            # XXX - TODO: Use VARIABLE_TRIGGER_LEN instead of hard coding 1
            expr = expr[:1]
            return [ (ilk, name) for ilk, name in vars if name.startswith(expr) ]
        else:
            return [ (ilk, name) for ilk, name in vars ]

    def _comment_variables_from_scope(self, expr, scoperef):
        """Return all available local variable names beginning with expr"""
        blob, lpath = scoperef
        # Only care about the local variables.
        scope_chain = ("locals", )
        vars = self._element_names_from_scope_starting_with_expr(None,
                            scoperef,
                            "variable",
                            scope_chain,
                            self.variable_names_from_elem)
        # XXX - TODO: Use VARIABLE_TRIGGER_LEN instead of hard coding 1
        expr = expr[:1]
        return [ (ilk, name) for ilk, name in vars if name.startswith(expr) ]

    def _constants_from_scope(self, expr, scoperef):
        """Return all available constant names beginning with expr"""
        # XXX - TODO: Use FUNCTION_TRIGGER_LEN instead of hard coding 3
        return self._element_names_from_scope_starting_with_expr(expr and expr[:3] or None,
                            scoperef,
                            "constant",
                            ("globals", "imports", "builtins"),
                            self.constant_shortnames_from_elem)

    def _keywords_from_scope(self, expr, scoperef):
        """Return all available keyword names beginning with expr"""
        keyword_completions = []
        keywords = self.langintel.langinfo.keywords
        expr = expr and expr[:3]
        for name in keywords:
            if not expr or name.startswith(expr):
                keyword_completions.append(("keyword", name))
        return keyword_completions

    def _functions_from_scope(self, expr, scoperef):
        """Return all available function names beginning with expr"""
        # XXX - TODO: Use FUNCTION_TRIGGER_LEN instead of hard coding 3
        return self._element_names_from_scope_starting_with_expr(expr and expr[:3] or None,
                            scoperef,
                            "function",
                            ("locals", "namespace", "globals", "imports",),
                            self.function_shortnames_from_elem)

    def _classes_from_scope(self, expr, scoperef):
        """Return all available class names beginning with expr"""
        return self._element_names_from_scope_starting_with_expr(expr,
                            scoperef,
                            "class",
                            ("locals", "namespace", "globals", "imports",),
                            self.class_names_from_elem)

    def _imported_namespaces_from_scope(self, expr, scoperef):
        """Return all available class names beginning with expr"""
        return self._element_names_from_scope_starting_with_expr(expr,
                            scoperef,
                            "namespace",
                            ("namespace", "globals"),
                            self.imported_namespace_names_from_elem)

    def _namespaces_from_scope(self, expr, scoperef):
        """Return all available namespaces beginning with expr"""
        if expr:
            expr = expr.strip("\\")
        namespaces = self._element_names_from_scope_starting_with_expr(expr,
                                scoperef,
                                "namespace",
                                ("globals", "imports", "builtins",),
                                self.namespace_names_from_elem)
        # We only want to see the next sub-namespace, i.e. if the expr is
        #   \mynamespace\<|>
        # then only return the immediate child namespaces, such as:
        #   \mynamespace\foo
        # but not any deeper, i.e. not:
        #   \mynamespace\foo\bar
        if expr:
            namespace_depth = expr.count("\\") + 2
        else:
            namespace_depth = 1
        filtered_namespaces = set()
        for ilk, n in namespaces:
            s = n.split("\\")
            filtered_namespaces.add((ilk, "\\".join(s[:namespace_depth])))
        return list(filtered_namespaces)

    def _interfaces_from_scope(self, expr, scoperef):
        """Return all available interface names beginning with expr"""
        # Need to work from the global scope for this one
        return self._element_names_from_scope_starting_with_expr(expr,
                            scoperef,
                            "interface",
                            ("namespace", "globals", "imports",),
                            self.interface_names_from_elem)

    # c.f. tree_python.py::PythonTreeEvaluator

    def _calltips_from_hit(self, hit):
        # TODO: compare with CitadelEvaluator._getSymbolCallTips()
        elem, scoperef = hit
        calltips = []
        if elem.tag == "variable":
            XXX
        elif elem.tag == "scope":
            ilk = elem.get("ilk")
            if ilk == "function":
                calltips.append(self._calltip_from_func(elem, scoperef))
            elif ilk == "class":
                calltips.append(self._calltip_from_class(elem, scoperef))
            else:
                raise NotImplementedError("unexpected scope ilk for "
                                          "calltip hit: %r" % elem)
        else:
            raise NotImplementedError("unexpected elem for calltip "
                                      "hit: %r" % elem)
        return calltips

    def _calltip_from_class(self, node, scoperef):
        # If the class has a defined signature then use that.
        signature = node.get("signature")
        doc = node.get("doc")
        if signature:
            ctlines = signature.splitlines(0)
            if doc:
                ctlines += doc.splitlines(0)
            return '\n'.join(ctlines)

        # Alternatively we use calltip information on the class'
        # constructor. PHP does not automatically inherit class contructors,
        # so we just return the one on the current class.
        else:
            # In PHP5 our CIX classes may have a special constructor function
            # with the name "__construct".
            ctor = node.names.get("__construct")
            if ctor is not None:
                self.log("_calltip_from_class:: ctor is %r", ctor)
                return self._calltip_from_func(ctor, scoperef)
            # In PHP4 the contructor is a function that has the same name as
            # the class name.
            name = node.get("name")
            ctor = node.names.get(name)
            if ctor is not None:
                self.log("_calltip_from_class:: ctor is %r", ctor)
                return self._calltip_from_func(ctor, scoperef)

            self.log("_calltip_from_class:: no ctor in class %r", name)

            # See if there is a parent class that has a constructor - bug 90156.
            for classref in node.get("classrefs", "").split():
                #TODO: update _hit_from_citdl to accept optional node type,
                #      i.e. to only return classes in this case.
                self.log("_calltip_from_class:: looking for parent class: %r",
                         classref)
                base_elem, base_scoperef \
                    = self._hit_from_citdl(classref, scoperef)
                if base_elem is not None and base_elem.get("ilk") == "class":
                    return self._calltip_from_class(base_elem, base_scoperef)
                else:
                    self.log("_calltip_from_class:: no parent class found: %r",
                             base_elem)

            return "%s()" % (name)

    def _members_from_array_hit(self, hit, trg_char):
        """Retrieve members from the given array element.

        @param hit {tuple} (elem, scoperef)
        @param trg_char {string}  The character that triggered the event.
        """
        self.log("_members_from_array_hit:: %r", hit)
        elem, scoperef = hit
        members = set()
        for child in elem:
            # Should look like:  SERVER_NAME']
            members.add( (child.get("ilk") or child.tag,
                          #"%s%s]" % (child.get("name"), trg_char)) )
                          child.get("name")) )
        return members

    def _members_from_elem(self, elem, name_prefix=''):
        """Return the appropriate set of autocomplete completions for
        the given element. Typically this is just one, but can be more for
        '*'-imports
        """
        members = set()
        if elem.tag == "import":
            module_name = elem.get("module")
            cpln_name = module_name.split('.', 1)[0]
            members.add( ("module", cpln_name) )
        else:
            members.add( (elem.get("ilk") or elem.tag,
                          name_prefix + elem.get("name")) )
        return members

    def _isElemInsideScoperef(self, elem, scoperef):
        blob, lpath = scoperef
        i = 0
        #self.log("_isElemInsideScoperef, elem: %r, lpath: %r", elem, lpath)
        for i in range(len(lpath)):
            name = lpath[i]
            if name == elem.get("name"):
                # XXX - It would be nice to confirm that this element is the
                #       actual elem, but this won't work correctly when there
                #       is an alternative match being used. i.e.
                #       http://bugs.activestate.com/show_bug.cgi?id=70015
                #check_elem = self._elem_from_scoperef((blob, lpath[:i+1]))
                #if check_elem == elem:
                    # It's in the scope
                    return True
        return False

    def _members_from_hit(self, hit, allowProtected=None, allowPrivate=None):
        """Retrieve members from the given hit.

        @param hit {tuple} (elem, scoperef)
        """
        elem, scoperef = hit

        # Namespaces completions only show for namespace elements.
        elem_type = elem.get("ilk") or elem.tag
        namespace_cplns = (self.trg.type == "namespace-members")
        if namespace_cplns and elem_type != "namespace":
            raise CodeIntelError("%r resolves to type %r, which is not a "
                                 "namespace" % (self.expr, elem_type, ))

        members = set()
        elem_name = elem.get("name")
        static_cplns = (self.trg.type == "static-members")

        for child in elem:
            #self.debug("_members_from_hit: checking child: %r", child)
            if child.tag == "import":
                continue
            name_prefix = ''   # Used to add "$" for static variable names.
            attributes = child.get("attributes", "").split()
            if "__hidden__" in attributes:
                continue
            if not allowProtected:
                # Protected and private vars can only be shown from inside
                # the class scope
                if "protected" in attributes:
                    if allowProtected is None:
                        # Need to check if it's allowed
                        allowProtected = self._isElemInsideScoperef(elem, self.get_start_scoperef())
                    if not allowProtected:
                        # Checked scope already and it does not allow protected
                        # Thats means it also does not allow private
                        allowPrivate = False
                        self.log("hit '%s.%s' is protected, not including",
                                 elem_name, child.get("name"))
                        continue
            if not allowPrivate:
                # we now know protected is allowed, now check private
                if "private" in attributes:
                    if allowPrivate is None:
                        # Need to check if it's allowed
                        allowPrivate = self._isElemInsideScoperef(elem, self.get_start_scoperef())
                    if not allowPrivate:
                        # Checked scope already and it does not allow private
                        self.log("hit '%s.%s' is private, not including",
                                 elem_name, child.get("name"))
                        continue
            if child.tag == "variable":
                if static_cplns:
                    # Static variables use the '$' prefix, constants do not.
                    if "static" in attributes:
                        name_prefix = '$'
                    elif child.get("ilk") != "constant":
                        continue
                elif "static" in attributes:
                    continue
                # Only namespaces allow access to constants.
                elif child.get("ilk") == "constant" and not namespace_cplns:
                    continue
            # add the element, we've already checked private|protected scopes
            members.update(self._members_from_elem(child, name_prefix))
        elem_ilk = elem.get("ilk")
        if elem_ilk == "class":
            for classref in elem.get("classrefs", "").split():
                ns_elem = self._namespace_elem_from_scoperef(scoperef)
                if ns_elem is not None:
                    # For class reference inside a namespace, *always* use the
                    # fully qualified name - bug 85643.
                    classref = "\\" + self._fqn_for_expression(classref, scoperef)
                self.debug("_members_from_hit: Getting members for inherited class: %r", classref)
                try:
                    subhit = self._hit_from_citdl(classref, scoperef)
                except CodeIntelError, ex:
                    # Continue with what we *can* resolve.
                    self.warn(str(ex))
                else:
                    if allowProtected is None:
                        # Need to check if it's allowed
                        allowProtected = self._isElemInsideScoperef(elem, self.get_start_scoperef())
                    # Checking the parent class, private is not allowed for sure
                    members.update(self._members_from_hit(subhit, allowProtected, allowPrivate=False))
        return members

    def _members_from_hits(self, hits, allowProtected=None, allowPrivate=None):
        """Retrieve members for the given hits.

        @param hits - a list of hits: [(elem, scoperef), ...]
        """
        members = set()
        for hit in hits:
            members.update(self._members_from_hit(hit))
        return members

    def _hit_from_citdl(self, expr, scoperef, defn_only=False):
        """Resolve the given CITDL expression (starting at the given
        scope) down to a non-import/non-variable hit.
        """
        self.eval_depth += 1
        self.log("_hit_from_citdl:: expr: %r, scoperef: %r", expr, scoperef)
        try:
            self._check_infinite_recursion(expr)
        except EvalError:
            # In the case of a recursion error, it is likely due to a class
            # variable having the same name as the class itself, so to try
            # to get better completions for this case we do not abort here,
            # but rather try from the parent scope instead. See bug:
            # http://bugs.activestate.com/show_bug.cgi?id=67774
            scoperef = self.parent_scoperef_from_scoperef(scoperef)
            if scoperef is None:
                # When we run out of scope, raise an error
                raise
            self.debug("_hit_from_citdl: recursion found for '%s', "
                       "moving to parent scope %r",
                       expr, scoperef)

        tokens = list(self._tokenize_citdl_expr(expr))
        self.log("_hit_from_citdl:: expr tokens: %r", tokens)

        # First part...
        hits, nconsumed = self._hits_from_first_part(tokens, scoperef)
        if not hits:
            #TODO: Add the fallback Buffer-specific near-by hunt
            #      for a symbol for the first token. See my spiral-bound
            #      book for some notes.
            if self.trg.type == "namespace-members":
                # If this is a namespace-members completion trigger, then this
                # namespace may not exist, but one of the sub-namespaces may:
                #    namespace foo\bar\bam {}
                #    \foo\<|>     # namespace 'foo' doesn't exist
                # in this case we want to return all namespaces starting with
                # this expr, which is handled in the eval_cplns() method.
                return None, None
            raise CodeIntelError("could not resolve first part of '%s'" % expr)

        self.debug("_hit_from_citdl:: first part: %r -> %r",
                   tokens[:nconsumed], hits)

        # ...the remainder.
        remaining_tokens = tokens[nconsumed:]
        while remaining_tokens:
            new_hits = []
            for hit in hits:
                new_hit = None
                try:
                    self.debug("_hit_from_citdl:: resolve %r on %r in %r",
                               remaining_tokens, *hit)
                    if remaining_tokens[0] == "()":
                        #TODO: impl this function
                        # _hit_from_call(elem, scoperef) -> hit or raise
                        #   CodeIntelError("could resolve call on %r: %s", hit[0], ex)
                        new_hit = self._hit_from_call(*hit)
                        nconsumed = 1
                    else:
                        new_hit, nconsumed \
                            = self._hit_from_getattr(remaining_tokens, *hit)
                    remaining_tokens = remaining_tokens[nconsumed:]
                except CodeIntelError, ex:
                    self.debug("error %s", ex)
                if new_hit:
                    new_hits.append(new_hit)
            if not new_hits:
                break
            hits = new_hits

        if not hits:
            raise CodeIntelError("could not resolve first part of '%s'" % expr)
        if len(hits) > 2:
            self.debug("_hit_from_citdl:: multiple hits found, returning the first hit")
        hit = hits[0]

        # Resolve any variable type inferences.
        #TODO: Need to *recursively* resolve hits.
        elem, scoperef = hit
        if elem.tag == "variable" and not defn_only:
            elem, scoperef = self._hit_from_variable_type_inference(elem, scoperef)

        self.info("_hit_from_citdl:: found '%s' => %s on %s", expr, elem, scoperef)
        return (elem, scoperef)

    def _alternative_elem_from_scoperef(self, traversed_items):
        """Find an alternative named element for the given traversal items"""
        for i in range(len(traversed_items)-1, -1, -1):
            elem, lname, failed_elems = traversed_items[i]
            self.log("Checking for alt elem: %r, lpath: %r, failed_elems: %r", elem, lname, failed_elems)
            for child in elem.getchildren():
                if child.attrib.get("name") == lname and child not in failed_elems:
                    return i, child
        return None

    def _elem_from_scoperef(self, scoperef):
        """A scoperef is (<blob>, <lpath>). Return the actual elem in
        the <blob> ciElementTree being referred to.
        """
        elem, lpath = scoperef
        traversed_items = []
        for i in range(len(lpath)):
            lname = lpath[i]
            try:
                child = elem.names[lname]
            except KeyError:
                # There is likely an alternative element that has the same name.
                # Try and find it now.
                # http://bugs.activestate.com/show_bug.cgi?id=70015
                child = None
                if i > 0:
                    #self.log("i now: %r, traversed_items: %r", i, traversed_items)
                    traversed_items[i-1][2].append(elem)
                    i, child = self._alternative_elem_from_scoperef(traversed_items)
                    traversed_items = traversed_items[:i]
                if child is None:
                    self.info("elem %r is missing lname: %r", elem, lname)
                    raise
                self.info("elem %r is missing lname: %r, found alternative: %r",
                          elem, lname, child)
            traversed_items.append((elem, lname, []))
            elem = child
        return elem

    def _namespace_elem_from_scoperef(self, scoperef):
        """A scoperef is (<blob>, <lpath>). Return the current namespace in
        the <blob> ciElementTree, walking up the scope as necessary.
        """
        blob, lpath = scoperef
        if len(lpath) >= 1:
            elem_chain = []
            elem = blob
            for i in range(len(lpath)):
                try:
                    elem = elem.names[lpath[i]]
                    elem_chain.append(elem)
                except KeyError:
                    break
            for elem in reversed(elem_chain):
                if elem.tag == "scope" and elem.get("ilk") == "namespace":
                    return elem
        return None

    def _imported_namespace_elements_from_scoperef(self, scoperef):
        namespace_elems = {}
        possible_elems = [ self._namespace_elem_from_scoperef(scoperef),
                           self._get_global_scoperef(scoperef)[0] ]
        for elem in possible_elems:
            if elem is not None:
                for child in elem:
                    if child.tag == "import":
                        symbol = child.get("symbol")
                        alias = child.get("alias")
                        if symbol is not None:
                            namespace_elems[alias or symbol] = child
        return namespace_elems

    def _fqn_for_expression(self, expr, scoperef):
        expr = expr.rstrip("\\")
        fqn = None
        if expr and not expr.startswith("\\"):
            # Looking up namespaces depends on whether we are already inside a
            # namespace or not. When inside a namespace, we need to lookup:
            #   * aliased namespaces
            #   * subnamespaces of the current namespace
            # When not inside a namespace, we need to lookup:
            #   * global namespaces
            tokens = expr.split("\\")
            first_token = tokens[0]

            used_namespaces = self._imported_namespace_elements_from_scoperef(scoperef)
            elem = used_namespaces.get(first_token)
            if elem is not None:
                symbol = elem.get("symbol")
                alias = elem.get("alias")
                self.log("_fqn_for_expression:: found used namespace: %r", elem)
                fqn = "%s\\%s" % (elem.get("module"), symbol)
                if tokens[1:]:
                    fqn += "\\%s" % ("\\".join(tokens[1:]))
            else:
                # Was not an imported/aliased namespace.
                elem = self._namespace_elem_from_scoperef(scoperef)
                if elem is not None:
                    # We are inside a namespace, work out the fully qualified
                    # name. Treat it as sub-namespace of the current namespace.
                    fqn = "%s\\%s" % (elem.get("name"), expr)
                else:
                    fqn = expr
        else:
            fqn = expr

        fqn = fqn.strip("\\")
        self.log("_fqn_for_expression:: %r => %r", expr, fqn)
        return fqn

    def _hits_from_namespace(self, fqn, scoperef):
        self.log("_hits_from_namespace:: fqn %r, scoperef: %r", fqn, scoperef)

        global_scoperef = self._get_global_scoperef(scoperef)
        global_blob = self._elem_from_scoperef(global_scoperef)

        #self.log("_hits_from_namespace:: globals: %r", global_blob.names.keys())
        hits = []
        elem = global_blob.names.get(fqn)
        if elem is not None:
            self.log("_hits_from_namespace:: found %r locally: %r", fqn, elem)
            hit_scoperef = [global_scoperef[0], global_scoperef[1] + [elem.get("name")]]
            hits.append((elem, hit_scoperef))
        else:
            # The last token in the namespace may be a class or a constant, instead
            # of being part of the namespace itself.
            tokens = fqn.split("\\")
            if len(tokens) > 1:
                partial_fqn = "\\".join(tokens[:-1])
                last_token = tokens[-1]
                self.log("_hits_from_namespace:: checking for sub-namespace match: %r",
                         partial_fqn)
        
                elem = global_blob.names.get(partial_fqn)
                if elem is not None:
                    self.log("_hits_from_namespace:: found sub-namespace locally, now find %r",
                             last_token)
                    try:
                        hit_scoperef = [global_scoperef[0], (partial_fqn, )]
                        hits.append((elem.names[last_token], hit_scoperef))
                    except KeyError:
                        # Fall through to other possible library matches (bug 85643).
                        self.debug("_hits_from_namespace:: no subsequent hit found locally for %r",
                                   last_token)

        lpath = (fqn, )
        libs = [self.buf.stdlib] + self.libs
        for lib in libs:
            lib_hits = lib.hits_from_lpath(lpath)
            if lib_hits:
                self.log("_hits_from_namespace:: found in lib: %r", lib)
                hits += lib_hits

        return hits

    def _hits_from_first_part(self, tokens, scoperef):
        """Find all hits for the first part of the tokens.

        Returns a tuple ([<hit1>, <hit2>], <num-tokens-consumed>), or
        (None, None) if it could not resolve.

        Example for 'os.sep':
            tokens: ('os', 'sep')
            retval: ([(<variable 'sep'>,  (<blob 'os', []))],   1)
        Example for 'os.path':
            tokens: ('os', 'path')
            retval: ([(<import os.path>,  (<blob 'os', []))],   2)
        """
        first_token = tokens[0]
        self.log("_hits_from_first_part:: find '%s ...' starting at %s:",
                 first_token, scoperef)

        if "\\" in first_token:
            first_token = self._fqn_for_expression(first_token, scoperef)
            # It's a namespace, lookup the correstponding namespace.
            hits = self._hits_from_namespace(first_token, scoperef)
            if hits:
                nconsumed = 1
                return (hits, nconsumed)
            self.log("_hits_from_first_part:: no namespace hits")
            if self.trg.type == "namespace-members":
                return (None, 1)

        if first_token in ("this", "self", "parent", "static"):
            # Special handling for class accessors
            self.log("_hits_from_first_part:: Special handling for %r",
                     first_token)
            elem = self._elem_from_scoperef(scoperef)
            while elem is not None and elem.get("ilk") != "class":
                # Return the class element
                blob, lpath = scoperef
                if not lpath:
                    return (None, None)
                scoperef = blob, lpath[:-1]
                elem = self._elem_from_scoperef(scoperef)
            if not elem:
                return (None, None)
            self.log("_hits_from_first_part:: need %s for %r", first_token, elem)
            if first_token == "parent":
                first_token = elem.get("classrefs")
                self.log("_hits_from_first_part:: Special handling for parent, "
                         "classref %r", first_token)
                if not first_token:
                    return (None, None)
                tokens = [first_token] + tokens[1:]
                scoperef = self.parent_scoperef_from_scoperef(scoperef)
                # Now go below and find the parent class members
            elif self._return_with_hit((elem, scoperef), 1):
                self.log("_hits_from_first_part:: %s returning scoperef: %r",
                         first_token, scoperef)
                return ([(elem, scoperef)], 1)

        while 1:
            self.log("_hits_from_first_part:: scoperef now %s:", scoperef)
            elem = self._elem_from_scoperef(scoperef)
            if first_token in elem.names:
                first_token_elem = elem.names[first_token]
                if self._return_with_hit((first_token_elem, scoperef), 1):
                    #TODO: skip __hidden__ names
                    self.log("_hits_from_first_part:: pt1: is '%s' accessible on %s? "
                             "yes: %s", first_token, scoperef, first_token_elem)
                    return ([(first_token_elem, scoperef)], 1)

            if elem.tag == "scope":
                self.log("_hits_from_first_part:: checking namespace aliases")
                imports = [child for child in elem if child.tag == "import"]
                for child in imports:
                    module = child.get("module")
                    symbol = child.get("symbol")
                    alias = child.get("alias")
                    self.log("_hits_from_first_part:: module: %r, symbol: %r"
                             ", alias: %r", module, symbol, alias)
                    if alias == first_token or \
                            (alias is None and symbol == first_token):
                        self.log("_hits_from_first_part:: pt2: is '%s' accessible on "
                                 "%s? yes: %s", first_token, scoperef, child)
                        # Aliases always use a fully qualified namespace.
                        expr = "\\%s\\%s" % (module, symbol)
                        hit = self._hit_from_citdl(expr, scoperef)
                        if hit:
                            return ([hit], 1)
                        break
            self.log("_hits_from_first_part:: pt3: is '%s' accessible on %s? no",
                     first_token, scoperef)
            # Do not go past the global scope reference
            if len(scoperef[1]) >= 1:
                scoperef = self.parent_scoperef_from_scoperef(scoperef)
                assert scoperef and scoperef[0] is not None, "Something is " \
                        "seriously wrong with our php logic."
            else:
                # We shall fallback to imports then
                break

        # elem and scoperef *are* for the global level
        hit, nconsumed = self._hit_from_elem_imports(tokens, elem)
        if hit is not None and self._return_with_hit(hit, nconsumed):
            self.log("_hits_from_first_part:: pt4: is '%s' accessible on %s? yes, "
                     "imported: %s",
                     '.'.join(tokens[:nconsumed]), scoperef, hit[0])
            return ([hit], nconsumed)
        return None, None


    def _hit_from_elem_imports(self, tokens, elem):
        """See if token is from one of the imports on this <scope> elem.

        Returns (<hit>, <num-tokens-consumed>) or (None, None) if not found.
        """
        #PERF: just have a .import_handler property on the evalr?
        self.debug("_hit_from_elem_imports:: Checking imports, tokens[0]: %r "
                   "... imp_elem: %r", tokens[0], elem)
        import_handler = self.citadel.import_handler_from_lang(self.trg.lang)
        libs = self.buf.libs

        #PERF: Add .imports method to ciElementTree for quick iteration
        #      over them. Or perhaps some cache to speed this method.
        #TODO: The right answer here is to not resolve the <import>,
        #      just return it. It is complicated enough that the
        #      construction of members has to know the original context.
        #      See the "Foo.mypackage.<|>mymodule.yo" part of test
        #      python/cpln/wacky_imports.
        #      XXX Not totally confident that this is the right answer.
        first_token = tokens[0]
        for imp_elem in (i for i in elem if i.tag == "import"):
            self.debug("_hit_from_elem_imports:: import '%s ...' from %r?",
                       tokens[0], imp_elem)
            module_name = imp_elem.get("module")
            try_module_names = [module_name]
            # If a module import is absolute and it fails, try a relative one
            # as well. Example:
            #   include (MYDIR + "/file.php");
            if module_name[0] == "/":
                try_module_names.append(module_name[1:])
            for module_name in try_module_names:
                if module_name not in self._imported_blobs:
                    try:
                        blob = import_handler.import_blob_name(
                                    module_name, libs, self.ctlr)
                    except CodeIntelError:
                        self.debug("_hit_from_elem_imports:: Failed import: %s",
                                   module_name)
                        pass # don't freak out: might not be our import anyway
                    else:
                        self._imported_blobs[module_name] = 1
                        try:
                            hit, nconsumed = self._hit_from_getattr(
                                                tokens, blob, (blob, []))
                            if hit:
                                return hit, nconsumed
                        except CodeIntelError, e:
                            self.debug("_hit_from_elem_imports:: "
                                       "_hit_from_getattr could not resolve: "
                                       "%r on %r", tokens, blob)
                            pass # don't freak out: we'll try the next import
                else:
                    self.debug("_hit_from_elem_imports:: Recursive import: "
                               "Already imported module: %r", module_name)

        # include-everything stuff
        self.log("_hit_from_elem_imports:: trying import everything: tokens: "
                 "%r", tokens)
        #self.log(banner("include-everything stuff", length=50))

        # First check the full lpath, then try for smaller and smaller lengths
        for nconsumed in range(len(tokens), 0, -1):
            lpath = tuple(tokens[:nconsumed])
            self.log("_hit_from_elem_imports:: trying with lpath: %r", lpath)
            # for each directory in all known php file directories
            for lib in self.libs:
                # see if there is a match (or partial match) in this directory
                hits = lib.hits_from_lpath(lpath, self.ctlr,
                                              curr_buf=self.buf)
                self.log("_hit_from_elem_imports:: ie: lookup %r in %s => %r",
                         lpath, lib, hits)
                for hit in hits:
                    (hit_elem, import_scoperef) = hit
                    (hit_blob, hit_lpath) = import_scoperef
                    self.log("_hit_from_elem_imports:: ie: matched %r to %r "
                             "in blob %r", lpath, hit_elem, hit_blob, )
                    unique_import_name = hit_blob.get("name") + "#" + str(lpath)
                    #print unique_import_name
                    if unique_import_name not in self._imported_blobs:
                        self._imported_blobs[unique_import_name] = 1
                        try:
                            if hit and self._return_with_hit(hit, 1):
                                return hit, nconsumed
                        except CodeIntelError, e:
                            self.debug("_hit_from_elem_imports:: ie: "
                                       "_hit_from_getattr could not resolve: "
                                       "%r on %r", tokens, blob)
                            pass # don't freak out: we'll try the next import
                    else:
                        self.debug("_hit_from_elem_imports:: ie: Recursive "
                                   "import: Already imported module: %r",
                                   unique_import_name)
            self.log("_hit_from_elem_imports:: ie: no matches found")
            #self.log(banner(None, length=50))

        return None, None

    def _hit_from_getattr(self, tokens, elem, scoperef):
        """Return a hit for a getattr on the given element.

        Returns (<hit>, <num-tokens-consumed>) or raises an EvalError.

        Typically this just does a getattr of tokens[0], but handling
        some multi-level imports can result in multiple tokens being
        consumed.
        """
        #TODO: On failure, call a hook to make an educated guess. Some
        #      attribute names are strong signals as to the object type
        #      -- typically those for common built-in classes.
        first_token = tokens[0]
        self.log("_hit_from_getattr:: resolve '%s' on %r in %r:", first_token,
                 elem, scoperef)
        if elem.tag == "variable":
            elem, scoperef = self._hit_from_variable_type_inference(elem, scoperef)

        assert elem.tag == "scope"
        ilk = elem.get("ilk")
        if ilk == "function":
            # Internal function arguments and variable should
            # *not* resolve. And we don't support function
            # attributes.
            pass
        elif ilk == "class":
            attr = elem.names.get(first_token)
            if attr is not None:
                self.log("_hit_from_getattr:: attr is %r in %r", attr, elem)
                classname = elem.get("name")
                # XXX - This works, but does not feel right.
                # Add the class name if it's not already there
                if len(scoperef[1]) == 0 or scoperef[1][-1] != classname:
                    class_scoperef = (scoperef[0], scoperef[1]+[classname])
                else:
                    class_scoperef = scoperef
                return (attr, class_scoperef), 1
            for classref in elem.get("classrefs", "").split():
                #TODO: update _hit_from_citdl to accept optional node type,
                #      i.e. to only return classes in this case.
                self.log("_hit_from_getattr:: is '%s' available on parent "
                         "class: %r?", first_token, classref)
                base_elem, base_scoperef \
                    = self._hit_from_citdl(classref, scoperef)
                if base_elem is not None and base_elem.get("ilk") == "class":
                    self.log("_hit_from_getattr:: is '%s' from %s base class?",
                             first_token, base_elem)
                    try:
                        hit, nconsumed = self._hit_from_getattr(tokens,
                                                                base_elem,
                                                                base_scoperef)
                        if hit is not None and self._return_with_hit(hit,
                                                                     nconsumed):
                            self.log("_hit_from_getattr:: is '%s' accessible "
                                     "on %s? yes: %s",
                                     '.'.join(tokens[:nconsumed]), scoperef,
                                     hit[0])
                            return hit, nconsumed
                    except CodeIntelError, e:
                        pass # don't freak out: we'll try the next classref
        elif ilk == "blob":
            attr = elem.names.get(first_token)
            if attr is not None:
                self.log("_hit_from_getattr:: attr is %r in %r", attr, elem)
                return (attr, scoperef), 1

            hit, nconsumed = self._hit_from_elem_imports(tokens, elem)
            if hit is not None:
                return hit, nconsumed
        else:
            raise NotImplementedError("unexpected scope ilk: %r" % ilk)
        raise CodeIntelError("could not resolve '%s' getattr on %r in %r"
                             % (first_token, elem, scoperef))

    def _hit_from_call(self, elem, scoperef):
        """Resolve the function call inference for 'elem' at 'scoperef'."""
        citdl = elem.get("returns")
        if not citdl:
            raise CodeIntelError("no _hit_from_call info for %r" % elem)
        self.log("_hit_from_call: resolve '%s' for %r, lpath: %r", citdl, elem, scoperef[1])
        # scoperef has to be on the function called
        func_scoperef = (scoperef[0], scoperef[1]+[elem.get("name")])
        return self._hit_from_citdl(citdl, func_scoperef)

    def _hit_from_variable_type_inference(self, elem, scoperef):
        """Resolve the type inference for 'elem' at 'scoperef'."""
        citdl = elem.get("citdl")
        if not citdl:
            raise CodeIntelError("no type-inference info for %r" % elem)
        if citdl == 'array' and self.trg.type == "array-members":
            self.log("_hit_from_variable_type_inference:: elem %r is an array",
                     elem, )
            return (elem, scoperef)
        self.log("_hit_from_variable_type_inference:: resolve '%s' type inference for %r:", citdl, elem)
        if citdl == elem.get("name") and elem.tag == "variable":
            # We really need an alternative match in this case, such as a class
            # or a function. First see if there are any matching names at the
            # same scope level, else go searching up the parent scopes.
            # http://bugs.activestate.com/show_bug.cgi?id=70015
            parent_elem = self._elem_from_scoperef(scoperef)
            if parent_elem is not None:
                sibling_matches = [x for x in parent_elem.getchildren() if x.get("name") == citdl and x.tag != "variable"]
                if sibling_matches:
                    return (sibling_matches[0], scoperef)
            scoperef = self.parent_scoperef_from_scoperef(scoperef)

        variable_namespace = elem.get("namespace")
        if variable_namespace and scoperef[0] is not None:
            # Variable was defined inside of a namespace, that means
            # it gets access to the namespace as well even though the
            # variable is defined to the global scope - bug 88964.
            self.log("_hit_from_variable_type_inference:: variable was defined in namespace %r",
                     variable_namespace)
            blob = scoperef[0]
            ns_elem = blob.names.get(variable_namespace)
            if ns_elem is not None:
                try:
                    hit = self._hit_from_citdl(citdl, (blob, [variable_namespace]))
                    if hit is not None:
                        return hit
                except:
                    self.log("_hit_from_variable_type_inference:: %r not found in namespace %r",
                             citdl, variable_namespace)

        return self._hit_from_citdl(citdl, scoperef)

    def parent_scoperef_from_scoperef(self, scoperef):
        # For PHP, either it's in the current scope or it's in the global scope
        # or last of all, it's in the builtins
        blob, lpath = scoperef
        if blob is self._built_in_blob:
            # Nothin past the builtins
            return None
        elif len(lpath) >= 1:
            if len(lpath) >= 2:
                # Return the namespace if there is one
                elem = blob.names.get(lpath[0])
                if elem is not None and elem.tag == "scope" and \
                   elem.get("ilk") == "namespace":
                    return (blob, lpath[:1])
            # Return the global scope
            return self._get_global_scoperef(scoperef)
        else:
            return (self.built_in_blob, [])


    #--- These method were inherited from JavaScriptTreeEvaluator.
    # If they are generic enough they should be moved to base
    # TreeEvaluator.

    _built_in_blob = None
    @property
    def built_in_blob(self):
        if self._built_in_blob is None:
            self._built_in_blob = self.buf.stdlib.get_blob("*")
        return self._built_in_blob

    _built_in_cache = None
    @property
    def built_in_cache(self):
        if self._built_in_cache is None:
            phpcache = self.built_in_blob.cache.get('php')
            if phpcache is None:
                phpcache = {}
                self.built_in_blob.cache['php'] = phpcache
            self._built_in_cache = phpcache
        return self._built_in_cache

    def _tokenize_citdl_expr(self, expr):
        for tok in expr.split('.'):
            if tok.endswith('()'):
                yield tok[:-2]
                yield '()'
            else:
                yield tok
    def _join_citdl_expr(self, tokens):
        return '.'.join(tokens).replace('.()', '()')

    def _calltip_from_func(self, node, scoperef):
        # See "Determining a Function CallTip" in the spec for a
        # discussion of this algorithm.
        signature = node.get("signature")
        doc = node.get("doc")
        ctlines = []
        if not signature:
            name = node.get("name")
            #XXX Note difference for Tcl in _getSymbolCallTips.
            ctlines = [name + "(...)"]
        else:
            ctlines = signature.splitlines(0)
        if doc:
            ctlines += doc.splitlines(0)
        else:
            # Check if there is a interface that has the docs - bug 83381.
            parent_elem = self._elem_from_scoperef(scoperef)
            if parent_elem.get("ilk") == "class":
                interfacerefs = parent_elem.get("interfacerefs", "").split()
                name = node.get("name")
                for interface in interfacerefs:
                    ielem, iscoperef = self._hit_from_citdl(interface, scoperef)
                    if ielem is not None:
                        # Found and interface, see if it has the info we need:
                        alt_node = ielem.names.get(name)
                        if alt_node is not None and alt_node.get("doc"):
                            ctlines += alt_node.get("doc").splitlines(0)
                            break
        return '\n'.join(ctlines)


    #---- Internal Utility functions for PHP

    def _get_global_scoperef(self, scoperef):
        return (scoperef[0], [])

    def _convertListToCitdl(self, citdl_type, lst):
        return sorted([ (citdl_type, v) for v in lst ])

    def _make_shortname_lookup_citdl_dict(self, citdl_type, namelist, length=1):
        d = make_short_name_dict(namelist, length=length)
        for key, values in d.items():
            d[key] = self._convertListToCitdl(citdl_type, values)
        return d

    # XXX PERF : Anything below here is in need of performance tweaking

    def _get_all_children_with_details(self, node, tagname, attributes=None, startswith=None):
        """Returns a list of child nodes that have the tag name and attributes.
        
        @param node {Element} the base node to search from
        @param tagname {str} the child tag name to find
        @param attributes {dict} the child node must have these attributes
        @param startswith {str} the child node name must start with this string
        @returns list of matched Element nodes
        """
        result = []
        for childnode in node.getchildren():
            if childnode.tag == tagname:
                doesMatch = True
                if attributes:
                    for attrname, attrvalue in attributes.items():
                        if childnode.get(attrname) != attrvalue:
                            doesMatch = False
                            break
                if doesMatch and startswith:
                    name = childnode.get("name")
                    if not name or not name.startswith(startswith):
                        doesMatch = False
                if doesMatch:
                    result.append(childnode)
        return result

    def _get_import_blob_with_module_name(self, module_name):
        import_handler = self.citadel.import_handler_from_lang(self.trg.lang)
        libs = self.buf.libs
        try:
            return import_handler.import_blob_name(module_name, libs,
                                                   self.ctlr)
        except CodeIntelError:
            pass # don't freak out: might not be our import anyway

    # Only used by _get_all_import_blobs_for_elem
    def _get_all_import_blobs_dict_for_elem(self, elem, imported_blobs):
        """Return all imported php blobs for the given element
        @param elem {Element} The element to find imports from.
        @param imported_blobs {dict} key: import name, value: imported blob
        """
        for imp_elem in (i for i in elem if i.tag == "import"):
            module_name = imp_elem.get("module")
            self.debug("_get_all_import_blobs_dict_for_elem:: Getting imports from %r", module_name)
            if module_name and module_name not in imported_blobs:
                import_blob = self._get_import_blob_with_module_name(module_name)
                if import_blob is not None:
                    imported_blobs[module_name] = import_blob
                    # Get imports from imports
                    # Example, foo imports bar, bar imports baz
                    self._get_all_import_blobs_dict_for_elem(import_blob, imported_blobs)
            else:
                self.debug("_get_all_import_blobs_dict_for_elem:: Recursive import: Already imported module: %r",
                           module_name)

    def _get_all_import_blobs_for_elem(self, elem):
        """Return all imported php blobs for the given element
        @param elem {Element} The element to find imports from.
        """
        # imported_blobs is used to keep track of what we import and to ensure
        # we don't get a recursive import situation
        imported_blobs = {}
        self._get_all_import_blobs_dict_for_elem(elem, imported_blobs)
        blobs = imported_blobs.values()
        self.debug("_get_all_import_blobs_for_elem:: Imported blobs: %r", blobs)
        return blobs

    #_built_in_keyword_names = None
    #@property
    #def built_in_keyword_names(self):
    #    if self._built_in_keyword_names is None:
    #        # Get all class names from the nodes
    #        # XXX - Fix keywords
    #        self._built_in_keyword_names = ["print", "echo", "class", "function"]
    #    return self._built_in_keyword_names

    def _php_cache_from_elem(self, elem):
        cache = elem.cache.get('php')
        if cache is None:
            # Add one in then
            cache = {}
            elem.cache['php'] = cache
        return cache

    def variable_names_from_elem(self, elem, cache_item_name='variable_names'):
        cache = self._php_cache_from_elem(elem)
        variable_names = cache.get(cache_item_name)
        if variable_names is None:
            variables = self._get_all_children_with_details(elem, "variable")
            variable_names = [ x.get("name") for x in variables if x.get("ilk") != "constant" ]
            cache[cache_item_name] = variable_names
        return variable_names

    def constant_names_from_elem(self, elem, cache_item_name='constant_names'):
        cache = self._php_cache_from_elem(elem)
        constant_names = cache.get(cache_item_name)
        if constant_names is None:
            constants = self._get_all_children_with_details(elem, "variable",
                                                            {"ilk": "constant"})
            constant_names = [ x.get("name") for x in constants ]
            cache[cache_item_name] = constant_names
        return constant_names

    def constant_shortnames_from_elem(self, elem, cache_item_name='constant_shortnames'):
        cache = self._php_cache_from_elem(elem)
        constant_short_names = cache.get(cache_item_name)
        if constant_short_names is None:
            constant_short_names = make_short_name_dict(
                                    self.constant_names_from_elem(elem),
                                    # XXX - TODO: Use constant_TRIGGER_LEN instead of hard coding 3
                                    length=3)
            cache[cache_item_name] = constant_short_names
        return constant_short_names

    def function_names_from_elem(self, elem, cache_item_name='function_names'):
        cache = self._php_cache_from_elem(elem)
        function_names = cache.get(cache_item_name)
        if function_names is None:
            functions = self._get_all_children_with_details(elem, "scope",
                                                            {"ilk": "function"})
            function_names = [ x.get("name") for x in functions ]
            cache[cache_item_name] = function_names
        return function_names

    def function_shortnames_from_elem(self, elem, cache_item_name='function_shortnames'):
        cache = self._php_cache_from_elem(elem)
        function_short_names = cache.get(cache_item_name)
        if function_short_names is None:
            function_short_names = make_short_name_dict(
                                    self.function_names_from_elem(elem),
                                    # XXX - TODO: Use FUNCTION_TRIGGER_LEN instead of hard coding 3
                                    length=3)
            cache[cache_item_name] = function_short_names
        return function_short_names

    def class_names_from_elem(self, elem, cache_item_name='class_names'):
        cache = self._php_cache_from_elem(elem)
        class_names = cache.get(cache_item_name)
        if class_names is None:
            classes = self._get_all_children_with_details(elem, "scope",
                                                            {"ilk": "class"})
            class_names = [ x.get("name") for x in classes ]
            cache[cache_item_name] = class_names
        return class_names

    def imported_namespace_names_from_elem(self, elem, cache_item_name='imported_namespace_names'):
        cache = self._php_cache_from_elem(elem)
        namespace_names = cache.get(cache_item_name)
        if namespace_names is None:
            namespace_names = []
            for child in elem:
                if child.tag == "import":
                    symbol = child.get("symbol")
                    alias = child.get("alias")
                    if symbol is not None:
                        namespace_names.append(alias or symbol)
            cache[cache_item_name] = namespace_names
        return namespace_names

    def namespace_names_from_elem(self, elem, cache_item_name='namespace_names'):
        cache = self._php_cache_from_elem(elem)
        namespace_names = cache.get(cache_item_name)
        if namespace_names is None:
            elems = self._get_all_children_with_details(elem, "scope",
                                                        {"ilk": "namespace"})
            namespace_names = [ x.get("name") for x in elems ]
            cache[cache_item_name] = namespace_names
        return namespace_names

    def interface_names_from_elem(self, elem, cache_item_name='interface_names'):
        cache = self._php_cache_from_elem(elem)
        interface_names = cache.get(cache_item_name)
        if interface_names is None:
            interfaces = self._get_all_children_with_details(elem, "scope",
                                                            {"ilk": "interface"})
            interface_names = [ x.get("name") for x in interfaces ]
            cache[cache_item_name] = interface_names
        return interface_names
