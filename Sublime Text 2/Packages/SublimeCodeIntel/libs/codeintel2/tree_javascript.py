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

"""Completion evaluation code for JavaScript"""

import types
import re
from pprint import pformat

from codeintel2.common import *
from codeintel2.util import indent
from codeintel2.tree import TreeEvaluator

if _xpcom_:
    from xpcom import components



class CandidatesForTreeEvaluator(TreeEvaluator):
    # Note: the "alt" changes added in change 281350 make some of the
    # functionality on this class *not* appropriate for the shared
    # TreeEvaluator. I.e. _elem_from_scoperef et al should be moved
    # *out* of CandidatesForTreeEvaluator.
    
    # This is a dict when set, multiple elements that have the same lpath will
    # be set in here, ensuring we get the correct one from an lpath lookup.
    # Fixes the following bug:
    #   http://bugs.activestate.com/show_bug.cgi?id=71666
    # Ideally, this would not be needed once elem.names[] can return a tuple,
    # see the following bug for reference:
    #   http://bugs.activestate.com/show_bug.cgi?id=71941
    _alt_elem_from_scoperef = None

    def _elem_from_scoperef(self, scoperef):
        """A scoperef is (<blob>, <lpath>). Return the actual elem in
        the <blob> ciElementTree being referred to.
        """
        elem = scoperef[0]
        i = 0
        for lname in scoperef[1]:
            i += 1
            if self._alt_elem_from_scoperef is not None:
                scoperef_names = ".".join(scoperef[1][:i])
                alt_elem = self._alt_elem_from_scoperef.get(scoperef_names)
                if alt_elem is not None:
                    elem = alt_elem
                    continue
            elem = elem.names[lname]
        return elem

    def _tokenize_citdl_expr(self, expr):
        for tok in expr.split('.'):
            if tok.endswith('()'):
                yield tok[:-2]
                yield '()'
            else:
                yield tok
    def _join_citdl_expr(self, tokens):
        return '.'.join(tokens).replace('.()', '()')

class JavaScriptTreeEvaluator(CandidatesForTreeEvaluator):
    def eval_cplns(self):
        self.log_start()
        start_scoperef = self.get_start_scoperef()
        self.info("start scope is %r", start_scoperef)
        _add_xpcom_blob(self.built_in_blob)

        if self.trg.type == "names":
            cplns = list(self._completion_names_from_scope(self.expr,
                                                           start_scoperef))
        else:
            hits = self._hits_from_citdl(self.expr, start_scoperef)
            cplns = list(self._members_from_hits(hits))
            if not cplns:
                raise CodeIntelError("No completions found")
        # For logging messages every call
        #print indent('\n'.join("%s: %s" % (lvl, m)
        #                for lvl,m in self.ctlr.log))
        #print indent('\n'.join(["Hit: %r" % (cpln, ) for cpln in cplns]))
        return cplns

    def eval_calltips(self):
        self.log_start()
        start_scoperef = self.get_start_scoperef()
        self.info("start scope is %r", start_scoperef)
        _add_xpcom_blob(self.built_in_blob)
        hits = self._hits_from_citdl(self.expr, start_scoperef)
        if not hits:
            raise CodeIntelError("No calltips found")
        return self._calltips_from_hits(hits)

    def eval_defns(self):
        self.log_start()
        start_scoperef = self.get_start_scoperef()
        self.info("start scope is %r", start_scoperef)
        _add_xpcom_blob(self.built_in_blob)
        hits = self._hits_from_citdl(self.expr, start_scoperef, defn_only=True)
        if not hits:
            raise CodeIntelError("No definitions found")
        return [ self._defn_from_hit(x) for x in hits ]

    def parent_scoperef_from_scoperef(self, scoperef,
                                      started_in_builtin_window_scope=False):
        """
        For JavaScript-in-the-browser the top-level scope is the
        Window object instance. For now we are always presuming we
        are running in the browser if the language is JavaScript.

        Problem: if we *started* on the Window class then the parent
        scope should be -> built-in-blob. This is what
        'started_in_builtin_window_scope' is used for.
        """
        blob, lpath = scoperef
        global_var = self._global_var
        if not started_in_builtin_window_scope \
           and lpath == [global_var] and blob is self.built_in_blob:
            return None
        elif lpath:
            return (blob, lpath[:-1])
        elif blob is self.built_in_blob:
            if started_in_builtin_window_scope:
                return None
            elif global_var is not None:
                return (self.built_in_blob, [global_var])
        else:
            return (self.built_in_blob, [])

    @property
    def _global_var(self):
        """
        The type of the global variable
        """
        return {
            "JavaScript": "Window",
            "Node.js":    "global",
        }.get(self.lang)

    _langintel = None
    @property
    def langintel(self):
        if self._langintel is None:
            self._langintel = self.mgr.langintel_from_lang(self.trg.lang)
        return self._langintel

    _libs = None
    @property
    def libs(self):
        if self._libs is None:
            self._libs = self.langintel.libs_from_buf(self.buf)
        return self._libs

    @property
    def stdlib(self):
        # JS stdlib is always the last one.
        return self.libs[-1]

    _built_in_blob = None
    @property
    def built_in_blob(self):
        if self._built_in_blob is None:
            self._built_in_blob = self.stdlib.get_blob("*")
        return self._built_in_blob

    ## Specific element completions ##

    def _hit_from_first_token(self, token, scoperef):
        """Find the token at the given or a parent scope.

        Returns the found elem and the scope at which it was found. If
        not found, this returns (None, None).
        """
        self.log("find '%s' starting at %s", token, scoperef)

        # Because we fake JavaScript classes and put the ctor
        # function inside the class, we need to push start scopes at
        # the class to the ctor. See test
        # javascript/cpln/ctor_scope_cheat for an example of why.
        try:
            elem = self._elem_from_scoperef(scoperef)
        except KeyError, ex:
            self.warn("_hit_from_first_token:: no elem for scoperef: %r",
                      scoperef)
            return (None, None)
        if elem.get("ilk") == "class":
            class_name = elem.get("name")
            try:
                ctor = elem.names[class_name]
            except KeyError:
                pass
            else:
                if "__ctor__" in ctor.get("attributes", ""):
                    scoperef = (scoperef[0], scoperef[1]+[class_name])
                    self.log("push scope to class ctor %s", scoperef)

        started_in_builtin_window_scope = (scoperef[0] is self.built_in_blob
            and scoperef[1] and scoperef[1][0] == self._global_var)
        while 1:
            try:
                elem = self._elem_from_scoperef(scoperef)
            except KeyError, ex:
                raise EvalError("could not resolve scoperef %r: %s"
                                % (scoperef, ex))
            try:
                candidate = elem.names[token]
                if "__ctor__" in candidate.get("attributes", ""):
                    # In JavaScript we include the constructor
                    # function for a (faked) class as a method.
                    # We must skip it here or resolution of 'this'
                    # in a JS class methods will always hit the ctor
                    # instead of the class (which is by far the
                    # common case).
                    raise KeyError("skipping JavaScript ctor")
                self.log("is '%s' accessible on %s? yes", token, scoperef)
                return candidate, scoperef
            except KeyError:
                self.log("is '%s' accessible on %s? no", token, scoperef)
                scoperef = self.parent_scoperef_from_scoperef(scoperef,
                                    started_in_builtin_window_scope)
                if not scoperef:
                    return None, None

    def _members_from_hits(self, hits):
        members = set()
        curr_blob = self.buf.blob_from_lang.get(self.lang, None)
        for elem, scope in hits:
            # In JavaScript we include the constructor function for a
            # (faked) class as a method. Completion on an instance of
            # this class shouldn't see the ctor.
            skip_js_ctor = (elem.tag == "scope" and elem.get("ilk") == "class")

            if elem.get("ilk") == "function":
                # Functions have an implicit citdl type of "Function". See bug:
                # http://bugs.activestate.com/show_bug.cgi?id=76504
                try:
                    subhits = self._hits_from_type_inference("Function", scope)
                    members.update(self._members_from_hits(subhits))
                except CodeIntelError:
                    pass  # Ignore if Function was not found

            for child in elem:
                if elem.get("ilk") == "function" and child.get("ilk") == "argument":
                    # function arguments are not members, skip them.
                    # (we might still find properties of functions, though)
                    continue
                # Only add locals when the current scope is the same
                # as the variable scope.
                attributes = child.get("attributes", "").split()
                if curr_blob is not None and scope[0] != curr_blob:
                    if "__file_local__" in attributes:
                        self.log("skipping file_local %r in %r", elem, scope)
                        continue
                if "__local__" in attributes:
                    # XXX: Move start_scoperef to be a part of the class
                    #start_scoperef = self.get_start_scoperef()
                    #scope_elem = start_scoperef[0]
                    #for lname in start_scoperef[1]:
                    #    if elem == scope_elem:
                    #        members.add( ("variable", child.get("name")) )
                    #        break
                    #    scope_elem = scope_elem.names[lname]
                    #else: # Don't show this variable
                    continue

                if child.tag == "scope":
                    if skip_js_ctor and child.get("ilk") == "function" \
                       and "__ctor__" in attributes:
                        continue
                    members.add( (child.get("ilk"), child.get("name")) )
                elif child.tag == "variable":
                    if len(child):
                        members.add( ("namespace", child.get("name")) )
                    else:
                        members.add( ("variable", child.get("name")) )
                else:
                    raise NotImplementedError("unknown hit child tag '%s': %r"
                                              % (child.tag, child))
            for classref in elem.get("classrefs", "").split():
                try:
                    subhits = self._hits_from_type_inference(classref, scope)
                    members.update(self._members_from_hits(subhits))
                except CodeIntelError:
                    pass  # Ignore when parent class not found, bug 65447
        return members

    def _calltip_from_func(self, elem):
        # See "Determining a Function CallTip" in the spec for a
        # discussion of this algorithm.
        signature = elem.get("signature")
        doc = elem.get("doc")
        ctlines = []
        if not signature:
            name = elem.get("name")
            #XXX Note difference for Tcl in _getSymbolCallTips.
            ctlines = [name + "(...)"]
        else:
            ctlines = signature.splitlines(0)
        if doc:
            ctlines += doc.splitlines(0)
        return '\n'.join(ctlines)

    def _calltip_from_class(self, elem):
        # If the class has a defined signature then use that.
        name = elem.get("name")
        signature = elem.get("signature")
        doc = elem.get("doc")
        if signature:
            ctlines = signature.splitlines(0)
            if doc:
                ctlines += doc.splitlines(0)
            return '\n'.join(ctlines)
        elif name in elem.names:
            # Typically the class element has a contructor function of
            # the same name as the class.
            ctor = elem.names[name]
            self.log("ctor is %r", ctor)
            return self._calltip_from_func(ctor)
        else:
            ctlines = [name + "(...)"]
            if doc:
                ctlines += doc.splitlines(0)
            return '\n'.join(ctlines)

    def _calltips_from_hits(self, hits):
        """
        c.f. CitadelEvaluator._getSymbolCallTips()
        """
        calltips = []

        for elem, scoperef in hits:
            #self.log("calltip for hit: %r", hit)
            if elem.tag == "variable":
                # Ignore variable hits.
                self.debug("_calltips_from_hits:: ignoring variable: %r", elem)
                continue
            elif elem.tag == "scope":
                ilk = elem.get("ilk")
                if ilk == "function":
                    calltips.append(self._calltip_from_func(elem))
                elif ilk == "class":
                    calltips.append(self._calltip_from_class(elem))
                else:
                    raise NotImplementedError("unexpected scope ilk for "
                                              "calltip hit: %r" % elem)
            else:
                raise NotImplementedError("unexpected elem for calltip "
                                          "hit: %r" % elem)

            ## Bug 59438: adding "(from $lpath in $file)" when helpful
            ## in calltips.
            ## TODO: Don't include all (or part) when not useful:
            ##       document.getElementsByClassName -> "(from document in
            ##       prototype)". The "document in" in not necessary.
            ## TODO: Bad with empty lpath: "(from  in prototype)"
            ## TODO: Problematic for test suite with "rand??" module names.
            ## TODO: Don't add for a local hit.
            #blobname = scoperef[0].get("name")
            #if blobname == "*":
            #    blobname = "stdlib"
            #scopename = '.'.join(scoperef[1])
            #calltips[-1] += "\n(from %s in %s)" % (scopename, blobname)
        return calltips

    def _hits_from_citdl(self, expr, scoperef, defn_only=False):
        self._check_infinite_recursion(expr)

        if "[" in expr:
            # TODO: We cannot resolve array type inferences yet.
            raise CodeIntelError("no type-inference yet for arrays: %r" % expr)

        tokens = list(self._tokenize_citdl_expr(expr))

        #self.log("expr tokens: %r", tokens)

        # First part... we try to match as much as possible straight up
        hits, nconsumed = self._hits_from_first_part(tokens, scoperef)
        if not hits:
            raise CodeIntelError("could not resolve first part of '%s'" % expr)
        self.debug("_hits_from_citdl: first part: %r -> %r",
                   tokens[:nconsumed], hits)

        # ...the remainder.
        remaining_tokens = tokens[nconsumed:]
        for token in tokens[nconsumed:]:
            new_hits = []
            for elem, scoperef in hits:
                self.debug("_hits_from_citdl: resolve %r on %r in %r",
                           token, elem, scoperef)
                if token == "()":
                    try:
                        new_hits += self._hits_from_call(elem, scoperef)
                    except CodeIntelError, ex:
                        self.warn("could resolve call on %r: %s", elem, ex)
                else:
                    try:
                        new_hit = self._hit_from_getattr(
                                    elem, scoperef, token)
                    except CodeIntelError, ex:
                        self.warn(str(ex))
                    else:
                        new_hits.append(new_hit)
            hits = new_hits 

        # Resolve any variable type inferences.
        #XXX Don't we have to *recursively* resolve hits?
        #    If that is done, then need to watch out for infinite loop
        #    because _hits_from_variable_type_inference() for a variable
        #    with children just returns itself. I.e. you *can't* resolve
        #    the <variable> away.
        resolved_hits = []
        if self.buf:
            curr_blob = self.buf.blob_from_lang.get(self.lang, {})
        else:
            curr_blob = None

        for elem, scoperef in hits:
            if scoperef[0] != curr_blob:
                if "__file_local__" in elem.get("attributes", "").split():
                    self.log("skipping __file_local__ %r in %r", elem, scoperef)
                    continue
            if elem.tag == "variable" and not defn_only:
                try:
                    if (not elem.get("citdl")) and elem.get("ilk") == "argument":
                        # this is an argument, try to infer things from the caller
                        subhits = self._hits_from_argument(elem, scoperef)
                    else:
                        subhits = self._hits_from_variable_type_inference(
                                    elem, scoperef)
                except CodeIntelError, ex:
                    self.warn("could not resolve %r: %s", elem, ex)
                else:
                    resolved_hits += subhits
            else:
                resolved_hits.append( (elem, scoperef) )

        return resolved_hits

    def _hits_from_argument(self, elem, scoperef):
        """
        Return hits for an argument of a function based on its caller
        @param elem The argument; must have ilk=argument
        @param scoperef The scope containing the element
        @returns list of hits
        """
        assert elem.get("ilk") == "argument", \
           "_hits_from_argument expects an argument, got a %r" % elem.get("ilk")
        hits = []
        scope = self._elem_from_scoperef(scoperef) # the function the argument is in

        args = [arg for arg in scope.findall("variable") if arg.get("ilk") == "argument"]
        for pos in range(len(args)):
            if args[pos].get("name") == elem.get("name"):
                break
        else:
            # can't find the argument?
            return []

        for caller in scope.getiterator("caller"):
            citdl = caller.get("citdl")
            caller_pos = int(caller.get("pos") or 0) # 1-indexed
            if citdl is None or caller_pos < 1:
                # invalid caller
                continue
            for caller_hit in self._hits_from_citdl(citdl, scoperef):
                caller_func = caller_hit[0] # the calling function
                if caller_func.get("ilk") != "function":
                    # nevermind, not a function
                    continue
                caller_args = [arg for arg in caller_func.getiterator("variable") if arg.get("ilk") == "argument"]
                if caller_pos > len(caller_args):
                    # no such argument
                    continue
                caller_arg = caller_args[caller_pos - 1]
                citdl = caller_arg.get("citdl")
                if not citdl:
                    continue
                for citdl_hit in self._hits_from_citdl(citdl, caller_hit[1]):
                    # got the function being called, now look up the argument by pos
                    func = citdl_hit[0]
                    if func.get("ilk") != "function":
                        continue
                    args = [arg for arg in func.getiterator("variable") if arg.get("ilk") == "argument"]
                    if pos >= len(args):
                        continue
                    citdl = args[pos].get("citdl")
                    if not citdl:
                        continue
                    hits += self._hits_from_citdl(citdl, citdl_hit[1])
        return hits

    def _hits_from_call(self, elem, scoperef):
        """Resolve the function call inference for 'elem' at 'scoperef'."""
        if elem.tag == "variable":
            hits = []
            var_hits = self._hits_from_variable_type_inference(elem, scoperef)
            for var_elem, var_scoperef in var_hits:
                if var_elem != elem:
                    try:
                        hits += self._hits_from_call(var_elem, var_scoperef)
                    except CodeIntelError:
                        pass  # Keep trying other alternatives
            if not hits:
                raise CodeIntelError("could not resolve call on %r." % elem)
            return hits
        if elem.get("ilk") == "class":
            return [(elem, scoperef)]
        if elem.get("ilk") != "function":
            raise CodeIntelError("_hits_from_call:: unexpected element type %r"
                                 % elem)

        # CommonJS / NodeJS hack
        if elem.get("name") == "require" and \
           scoperef[0] is self.built_in_blob and \
           not scoperef[1]:
            requirename = self.trg.extra.get("_params")
            if requirename is not None:
                import codeintel2.lang_javascript
                requirename = codeintel2.lang_javascript.Utils.unquoteJsString(requirename)
                self.log("_hits_from_call: resolving CommonJS require(%r)",
                         requirename)
                hits = self._hits_from_commonjs_require(requirename, scoperef)
                if len(hits) > 0:
                    return hits

        citdl = elem.get("returns")
        if not citdl:
            raise CodeIntelError("no return type info for %r" % elem)
        self.log("_hits_from_call: resolve '%s' for %r, scoperef: %r",
                 citdl, elem, scoperef)
        # scoperef has to be set to the function called
        scoperef = (scoperef[0], scoperef[1]+[elem.get("name")])
        return self._hits_from_citdl(citdl, scoperef)

    def _hit_from_getattr(self, elem, scoperef, token):
        """Resolve the getattr of 'token' on the given 'elem'.

        Raises CodeIntelError if could not resolve it.

        Algorithm:
        - Try to resolve it.
        - Call a hook to make an educated guess. Some attribute names
          are strong signals as to the object type -- typically those
          for common built-in classes.
        """
        self.log("resolve getattr '%s' on %r in %r:", token, elem, scoperef)
        if elem.tag == "variable":
            hits = self._hits_from_variable_type_inference(elem, scoperef)
        elif elem.tag == "scope" and elem.get("ilk") == "function":
            # Functions have an implicit citdl type of "Function". Bug 80880.
            hits = self._hits_from_type_inference("Function", scoperef)
        else:
            assert elem.tag == "scope", "elem tag is not 'scope': %r" % elem.tag
            hits = [(elem, scoperef)]

        for hit_elem, hit_scoperef in hits:
            self.log("_hit_from_getattr:: hit elem %r, scoperef: %r",
                     hit_elem, hit_scoperef)
            ilk = hit_elem.get("ilk")
            if hit_elem.tag == "variable":
                attr = hit_elem.names.get(token)
                if attr is not None:
                    self.log("attr is %r on %r", attr, hit_elem)
                    var_scoperef = (hit_scoperef[0],
                                    hit_scoperef[1]+[hit_elem.get("name")])
                    return (attr, var_scoperef)
            elif ilk == "function":
                return self._hit_from_getattr(hit_elem, hit_scoperef, token)

            elif ilk == "class":
                attr = hit_elem.names.get(token)
                if attr is not None:
                    self.log("attr is %r on %r", attr, hit_elem)
                    if hit_scoperef:
                        class_scoperef = (hit_scoperef[0],
                                      hit_scoperef[1]+[hit_elem.get("name")])
                        # If this is a variable defined in a class, move the
                        # scope to become the position in the class where the
                        # variable was defined (usually the ctor class function)
                        # this ensures we get the right citdl lookup. See bug:
                        # http://bugs.activestate.com/show_bug.cgi?id=71343
                        lineno = int(attr.get("line", "-1"))
                        if attr.tag == "variable" and \
                           lineno > int(hit_elem.get("line", "-1")) and \
                           lineno <= int(hit_elem.get("lineend", "-1")):
                            # get the scope of the variable
                            blob, lpath = self.buf.scoperef_from_blob_and_line(hit_elem,
                                                                      lineno)
                            if lpath:
                                class_scoperef = (class_scoperef[0],
                                                  class_scoperef[1]+lpath)
                                self.log("Updating scoperef to: %r", class_scoperef)
                    else:
                        class_scoperef = (None, [hit_elem.get("name")])
                    return (attr, class_scoperef)
                for classref in hit_elem.get("classrefs", "").split():
                    try:
                        base_hits = self._hits_from_type_inference(classref,
                                                                   hit_scoperef)
                    except CodeIntelError:
                        pass  # Ignore when parent class not found, bug 65447
                    else:
                        for base_elem, base_scoperef in base_hits:
                            if token in base_elem.names:
                                self.log("is '%s' from %s base class? yes",
                                         token, base_elem)
                                new_scoperef = (base_scoperef[0],
                                                base_scoperef[1]+
                                                [base_elem.get("name")])
                                return (base_elem.names[token], new_scoperef)
                            self.log("is '%s' from %s base class? no", token,
                                     base_elem)
            else:
                raise NotImplementedError("unexpected scope ilk: %r" % ilk)
        raise CodeIntelError("could not resolve '%s' getattr on %r in %r"
                             % (token, elem, scoperef))

    def _hits_from_variable_type_inference(self, elem, scoperef):
        """Resolve the type inference for 'elem' at 'scoperef'."""
        assert elem.tag == "variable"
        if len(elem) != 0:
            # This is CIX for a JavaScript custom Object instance: a
            # common pattern in JS. See test javascript/cpln/local2.
            return [(elem, scoperef)]
        citdl = elem.get("citdl")
        if not citdl:
            raise CodeIntelError("no type-inference info for %r" % elem)
        self.log("resolve '%s' type inference for %r:", citdl, elem)
        if citdl == elem.get("name") and citdl not in elem.names:
            # The citdl expression is the same as the variable name, this will
            # create a recursive citdl lookup loop. What we likely want is a
            # different match that has the same name, so we go looking for it.
            # Fix for bug: http://bugs.activestate.com/show_bug.cgi?id=71666
            self.log("_hits_from_variable_type_inference:: recursive citdl "
                      " expression found, trying alternatives.")
            try:
                parent_elem = self._elem_from_scoperef(scoperef)
            except KeyError, ex:
                raise CodeIntelError("could not resolve recursive citdl expression %r" % citdl)
            else:
                alt_hits = []
                # Look for alternative non-variable matches.
                for child in parent_elem:
                    if child.tag != "variable" and child.get("name") == citdl:
                        alt_hits.append((child, scoperef))
                        # Remember the alternative hit, in case we need to
                        # look up this lpath again.
                        if self._alt_elem_from_scoperef is None:
                            self._alt_elem_from_scoperef = {}
                        alt_sref_name = ".".join(scoperef[1] + [citdl])
                        self._alt_elem_from_scoperef[alt_sref_name] = child
                        self.log("Alternative hit found: %r, scoperef: %r", child, scoperef, )
                if alt_hits:
                    return alt_hits
                # Try from the parent scoperef then.
                scoperef = self.parent_scoperef_from_scoperef(scoperef)
                if scoperef is None:
                    # When we run out of scope, raise an error
                    raise CodeIntelError("could not resolve recursive citdl expression %r" % citdl)
                # Continue looking using _hits_from_citdl with the parent.
                self.log("Continue search for %r from the parent scope.", citdl)
        if citdl == "require()":
            requirename = elem.get('required_library_name')
            self.log("_hits_from_variable_type_inference: resolving require(%r)",
                     requirename)
            if requirename:
                hits = self._hits_from_commonjs_require(requirename, scoperef)
                if hits:
                    return hits
        return self._hits_from_citdl(citdl, scoperef)

    def _hits_from_type_inference(self, citdl, scoperef):
        """Resolve the 'citdl' type inference at 'scoperef'."""
        self.log("resolve '%s' type inference:", citdl)
        return self._hits_from_citdl(citdl, scoperef)

    def _hits_from_first_part(self, tokens, scoperef):
        """Resolve the first part of the expression.
        
        If the first token is found at the global or built-in level (or
        not found at all locally) then it may be a shared namespace with
        other files in the execution set. Get that down to a list of
        hits and a remaining list of expression tokens.
        """
        elem, scoperef = self._hit_from_first_token(tokens[0], scoperef)
        if elem is not None:
            self.log("_hit_from_first_part: found elem: %s %r at %r",
                     elem.get("ilk") or elem.tag, elem.get("name"),
                     scoperef[1])
            # Special handling for xpcom components
            if elem == _g_xpcom_components_elem and len(tokens) > 2 and \
               tokens[1] == "interfaces":
                self.log("Ensuring xpcom interface is loaded: %r",
                         tokens[2])
                _xpcom_iid_to_cix(tokens[2])
                # Let it continue below, to find the proper cix element

        if (elem is None            # first token wasn't found
            or not scoperef[1]      # first token was found at global level
            # first token was found on built-in Window class (the top scope)
            or (scoperef[1] == ['Window'] and scoperef[0].get("name") == "*")
           ):
            # Search symbol table in execution set.
            #
            # Example: 'myPet.name.toLowerCase()' and 'myPet' is found
            # at top-level. First lookup 'myPet.name.toLowerCase'
            # (everything up to first '()'), in execution set, then
            # 'myPet.name', then 'myPet'. The last one should always hit
            # in current file, at least.
            for first_call_idx, token in enumerate(tokens):
                if token == "()":
                    break
            else:
                first_call_idx = len(tokens)

            hits = []
            for nconsumed in range(first_call_idx, 0, -1):
                lpath = tuple(tokens[:nconsumed]) # for hits_from_lpath()
                if elem is not None and len(lpath) > 1:
                    # Try at the current elem we found in the file
                    try:
                        self.log("Checking for deeper local match %r from scoperef %r", lpath[1:], scoperef)
                        check_elem = elem
                        for p in lpath[1:]:   # we matched first token already
                            check_elem = check_elem.names[p]
                        check_scoperef = (scoperef[0], scoperef[1] + list(lpath[:-1]))
                        hits.insert(0, (check_elem,
                                        check_scoperef))
                        self.log("_hit_from_first_part: found deeper local elem: "\
                                 "%s %r at %r",
                                check_elem.get("ilk") or check_elem.tag,
                                check_elem.get("name"),
                                check_scoperef[1])
                    except KeyError:
                        pass

                for lib in self.libs:
                    self.log("lookup '%s' in %s", '.'.join(lpath), lib)
                    hits_here = lib.hits_from_lpath(lpath, self.ctlr,
                                                    curr_buf=self.buf)
                    if hits_here:
                        self.log("found %d hits in lib", len(hits_here))
                        hits += hits_here
                if hits:
                    break
            if elem is not None:
                if not hits or nconsumed == 1:
                    hits.insert(0, (elem, scoperef))
                    nconsumed = 1
                else:
                    # Hits were found in the libs that are deeper than
                    # the hit in the local buf: we need to adjust the
                    # local hit.
                    new_elem = elem
                    for token in tokens[1:nconsumed]:
                        try:
                            new_elem = new_elem.names[token]
                        except KeyError:
                            break
                    else:
                        if new_elem not in (e for e,sr in hits):
                            new_scoperef = (scoperef[0], tokens[:nconsumed-1])
                            hits.insert(0, (new_elem, new_scoperef))
        else:
            hits = [(elem, scoperef)]
            nconsumed = 1

        return hits, nconsumed

    def _hits_from_commonjs_require(self, requirename, scoperef):
        """Resolve hits from a CommonJS require() invocation"""
        # Files usually end with a ".js" suffix, though others are like
        # ".node" are possible.
        #
        # TODO: Get these from node using "require.extensions".
        requirename += ".js"
        from codeintel2.database.langlib import LangDirsLib
        from codeintel2.database.multilanglib import MultiLangDirsLib
        from codeintel2.database.catalog import CatalogLib
        hits = []
        for lib in self.libs:
            blobs = None
            if isinstance(lib, (LangDirsLib, MultiLangDirsLib)):
                blobs = lib.blobs_with_basename(requirename, ctlr=self.ctlr)
            elif isinstance(lib, CatalogLib):
                blob = lib.get_blob(requirename)
                if blob is not None:
                    blobs = [blob]
            for blob in blobs or []:
                exports = blob.names.get("exports")
                if exports is not None and exports.tag == "variable":
                    hits += self._hits_from_variable_type_inference(exports, [blob, ["exports"]])
                else:
                    self.log("Exported exports to be a variable, got %r instead", exports)
        return hits

    ## n-char trigger completions ##

    def _completion_names_from_scope(self, expr, scoperef):
        """Return all available element names beginning with expr"""
        self.log("_completion_names_from_scope:: %r, scoperef: %r",
                 expr, scoperef)
        #global_blob = self._elem_from_scoperef(self._get_global_scoperef(scoperef))
        # Get all of the imports

        # Keep a dictionary of completions.
        all_completions = {}

        # We start off having JS keywords at a bare minimum.
        keywords = self.langintel.langinfo.keywords
        for name in keywords:
            if not expr or name.startswith(expr):
                all_completions[name] = "keyword"

        # From the local scope, walk up the parent chain including matches as
        # we go.
        # XXX - Can we skip the global (stdlib) blob in here?
        while scoperef and scoperef[0] is not None:
            # Iterate over the contents of the scope.
            self.log("_completion_names_from_scope:: checking scoperef: %r",
                     scoperef)
            elem = self._elem_from_scoperef(scoperef)
            if elem is None:
                continue
            for name in elem.names:
                #self.log("_completion_names_from_scope:: checking name: %r",
                #         name)
                if name and name.startswith(expr):
                    if name not in all_completions:
                        hit_elem = elem.names[name]
                        if "__local__" in hit_elem.get("attributes", "").split():
                            # Skip things that should be local to the parent scope
                            #self.log("_completion_names_from_scope:: skipping local %r",
                            #         name)
                            continue
                        all_completions[name] = hit_elem.get("ilk") or hit_elem.tag
            # Continue walking up the scope chain...
            scoperef = self.parent_scoperef_from_scoperef(scoperef)

        # Builtins
        # Find the matching names (or all names if no expr)
        cplns = self.stdlib.toplevel_cplns(prefix=expr)
        for ilk, name in cplns:
            if name not in all_completions:
                all_completions[name] = ilk

        # "Import everything", iterate over all known libs
        for lib in self.libs:
            # Find the matching names (or all names if no expr)
            self.log("_completion_names_from_scope:: include everything from "
                     "lib: %r", lib)
            cplns = lib.toplevel_cplns(prefix=expr)
            for ilk, name in cplns:
                if name not in all_completions:
                    all_completions[name] = ilk

        return [(ilk, name) for name, ilk in all_completions.items()]


#####################################
# Devel work
#####################################

# Dictionary of already created xpcom wrappers, used so we do not keep
# creating xpcom instances / services
from ciElementTree import Element, SubElement, dump

if _xpcom_:
    from xpcom import xpt
    _xpcom_ = True
    import xpcom.xpt
    from gencix_utils import *
    
    # Dictionary of known xpcom types and what they map to in JavaScript
    javascript_type_from_xpt_tag = {
        xpt.T_I8                : "Number",
        xpt.T_I16               : "Number",
        xpt.T_I32               : "Number",
        xpt.T_I64               : "Number",
        xpt.T_U8                : "Number",
        xpt.T_U16               : "Number",
        xpt.T_U32               : "Number",
        xpt.T_U64               : "Number",
        xpt.T_FLOAT             : "Number",
        xpt.T_DOUBLE            : "Number",
        xpt.T_BOOL              : "Boolean",
        xpt.T_CHAR              : "String",
        xpt.T_WCHAR             : "String",
        xpt.T_VOID              : "void",
        xpt.T_IID               : None,
        xpt.T_DOMSTRING         : "DOMString",
        xpt.T_CHAR_STR          : "String",
        xpt.T_WCHAR_STR         : "String",
        xpt.T_INTERFACE         : None,
        xpt.T_INTERFACE_IS      : None,
        xpt.T_ARRAY             : "Array",
        xpt.T_PSTRING_SIZE_IS   : None,
        xpt.T_PWSTRING_SIZE_IS  : None,
        # These are missing from xpt, when these cross the xpconnect boundary
        # they are converted into unicode strings automatically. See:
        # http://developer.mozilla.org/en/docs/XPCOM_string_guide#IDL_String_types
        23: "String", # T_UTF8STRING
        24: "String", # T_CSTRING
        25: "String", # T_ASTRING
    }

    def process_xpcom_arguments(m):
        args = []
        returntype = None
        param_count = 1
        for param in m.params:
            t = xpt.TypeDescriber(param.type_desc[0], param)
            if t.tag in (xpt.T_INTERFACE, ):
                arg_type = t.Describe()
            elif t.tag in (xpt.T_ARRAY, ):
                arg_type = "Array"
            else:
                arg_type = javascript_type_from_xpt_tag.get(t.tag, "unknown")
    
            if param.IsIn():
                args.append("in %s" % (arg_type))
                param_count += 1
            elif param.IsRetval():
                if t.tag in (xpt.T_INTERFACE, ):
                    returntype = "Components.interfaces.%s" % (arg_type)
                else:
                    returntype = arg_type
            elif param.IsOut():
                args.append("out %s" % (arg_type))
                param_count += 1
        return args, returntype

    def iid_to_cix(iid):
        elem = Element("scope", name=iid, ilk="class")
        try:
            interface = xpt.Interface(iid)
        except:
            print "No interface with iid: %r" % (iid, )
        else:
            # Filter out non-xpcom methods
            methods = [ m for m in interface.methods if not m.IsNotXPCOM() ]
            getters = [ m for m in methods if m.IsGetter() ]
            getters += [ m for m in methods if m.IsSetter() ]
            methods = [ m for m in methods if not m.IsGetter() and
                                              not m.IsSetter() ]
        
            for m in getters:
                args, returntype = process_xpcom_arguments(m)
                variable_elem = elem.names.get(m.name)
                # Don't override an existing element.
                if variable_elem is None:
                    variable_elem = SubElement(elem, "variable", name=m.name,
                                               citdl=returntype)
                # Else, this must be a setter, which does not have a type.
            for m in methods:
                #print m.name
                func_elem = SubElement(elem, "scope", name=m.name,
                                       ilk="function")
                args, returntype = process_xpcom_arguments(m)
                signature = "%s(%s)" % (m.name, ", ".join(args))
                if returntype is not None:
                    func_elem.attrib["returns"] = returntype
                    signature += " => %s" % (returntype, )
                func_elem.attrib["signature"] = signature
            for c in interface.constants:
                # XXX: assuming all constants are integers, I am yet to see a
                #      case where this is not true...
                variable_elem = SubElement(elem, "variable", name=c.name,
                                           citdl="Number",
                                           attributes="constant")
        return elem
    

# Globals used for holding the xpcom cix information, the base xpcom structure
# is generated once per run, then interface details are added on demand.
_g_xpcom_interfaces_elem = None
_g_xpcom_components_elem = None
# The map of iid to xpcom cix element.
_g_xpcom_cix_for_iid = {}

def _add_xpcom_blob(built_in_blob):
    global _g_xpcom_components_elem
    global _g_xpcom_interfaces_elem
    if _xpcom_:
        if _g_xpcom_components_elem is None:
            # create the blob to hold xpcom data
            #print "Building xpcom cix wrapper for the first time"
            _g_xpcom_components_elem = SubElement(built_in_blob, "variable",
                                         citdl="Object", name="Components")
            xpcComponents = iid_to_cix("nsIXPCComponents")

            elem_classes = None
            for elem in xpcComponents:
                if elem.get("name") == "classes":
                    #print "Found the classes elem: %r" % (elem, )
                    elem.attrib["citdl"] = "Object"
                    elem_classes = elem
                elif elem.get("name") == "interfaces":
                    #print "Found the interfaces elem: %r" % (elem, )
                    elem.attrib["citdl"] = "Object"
                    _g_xpcom_interfaces_elem = elem
                _g_xpcom_components_elem.append(elem)
    
            # Add Components.interfaces data
            for interface in components.interfaces.keys():
                elem = SubElement(_g_xpcom_interfaces_elem, "scope",
                                  ilk="class", name=interface)
    
            # Add Components.classes data
            for klass in components.classes.keys():
                elem = SubElement(elem_classes, "variable", name=klass)
    
            # Add some common aliases
            for alias_name in ("CI", "Ci", ):
                SubElement(built_in_blob, "variable",
                           citdl="Components.interfaces", name=alias_name)
            for alias_name in ("CC", "Cc", ):
                SubElement(built_in_blob, "variable",
                           citdl="Components.classes", name=alias_name)
            for alias_name in ("CU", "Cu", ):
                SubElement(built_in_blob, "variable",
                           citdl="Components.utils", name=alias_name)
        # This check is necessary as sometimes a blob will be cached and
        # will already contain the Components elem.
        elif built_in_blob.names.get("Components") is None:
            built_in_blob.append(_g_xpcom_components_elem)

def _xpcom_iid_to_cix(iid):
    """Return a cix element containg the xpcom interface for the given iid."""
    if not _xpcom_:
        return None
    if not iid:
        # Default to nsISupports, all xpcom components support this.
        iid = "nsISupports"
    # Try and get it from the cached interfaces.
    elem = _g_xpcom_cix_for_iid.get(iid)
    if elem is None:
        # Else, we load it up.
        elem = iid_to_cix(iid)
        # Remove the dummy place holder element if there is one, this is here
        # only to provide support for "Components.interfaces.<|>" completions.
        if iid in _g_xpcom_interfaces_elem.names:
            _g_xpcom_interfaces_elem.remove(_g_xpcom_interfaces_elem.names[iid])
        _g_xpcom_interfaces_elem.append(elem)
        _g_xpcom_cix_for_iid[iid] = elem
    return elem
