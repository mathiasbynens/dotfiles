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

"""Completion evaluation code for Ruby"""

import re

from codeintel2.common import *
from codeintel2.tree import TreeEvaluator
from codeintel2.tree_javascript import JavaScriptTreeEvaluator
from codeintel2.database.stdlib import StdLib

# Evaluator
#   CitadelEvaluator
#       PythonCitadelEvaluator
#       ...
#   TreeEvaluator
#       PythonTreeEvaluator

# Global constants

NO_HITS = [] # Any value, as long as it's boolean(False)

_ANY_RESOLUTION = 1
_NAMESPACE_RESOLUTION = 2
_CLASS_RESOLUTION     = 3

_OP_TO_RESOLUTION = {"::" : _NAMESPACE_RESOLUTION,
                     "." : _CLASS_RESOLUTION}

# Bitmask for completion types
        
_CPLN_MODULES        = 0x0001
_CPLN_METHODS_CLASS  = 0x0002
_CPLN_METHODS_INST   = 0x0004
_CPLN_METHODS_ALL    = _CPLN_METHODS_CLASS|_CPLN_METHODS_INST
_CPLN_METHODS_ALL_FOR_MODULE = 0x0008
    # Look at the left hand side:
    # Module type: accept all methods
    # Class type: accept class methods only
_CPLN_CLASSES        = 0x0010
_CPLN_VARIABLES      = 0x0020

_CPLN_ALL_BUT_METHODS = _CPLN_MODULES|_CPLN_CLASSES|_CPLN_VARIABLES
_CPLN_ALL            = _CPLN_ALL_BUT_METHODS|_CPLN_METHODS_ALL

# Global data

letter_start_re = re.compile('^[a-zA-Z]')
token_splitter_re = re.compile(r'(\.|::)')

_looks_like_constant_re = re.compile(r'[A-Z]\w*(?:::[A-Z]\w*)*$')

class HitHelper:
    """Encapsulate the ElementTree-based represetation
    of Ruby code"""

    def get_name(self, hit):
        return hit[0].get("name")

    def get_type(self, hit):
        elem = hit[0]
        return elem.get("ilk") or elem.tag

    def is_class(self, hit):
        return self.get_type(hit) == "class"

    def is_compound(self, hit):
        return self.get_type(hit) in ("class", "namespace")

    def is_function(self, hit):
        return self.get_type(hit) == "function"

    def is_namespace(self, hit):
        return self.get_type(hit) == "namespace"

    def is_variable(self, hit):
        return self.get_type(hit) == "variable"

class TreeEvaluatorHelper(TreeEvaluator):

    def _elem_from_scoperef(self, scoperef):
        """A scoperef is (<blob>, <lpath>). Return the actual elem in
        the <blob> ciElementTree being referred to.
        """
        elem = scoperef[0]
        for lname in scoperef[1]:
            elem = elem.names[lname]
        return elem

    # Why is this not done specifically for Ruby?
    def _calltip_from_func(self, node):
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
        return '\n'.join(ctlines)

    # This code taken from JavaScriptTreeEvaluator

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


class RubyTreeEvaluator(TreeEvaluatorHelper):
    """
    scoperef: (<blob>, <lpath>) where <lpath> is list of names
        self._elem_from_scoperef()
    hit: (<elem>, <scoperef>)

    tokens = list(self._tokenize_citdl_expr(expr))   'foo.bar'
    """
    def __init__(self, ctlr, buf, trg, citdl_expr, line,
                 converted_dot_new=False):
        TreeEvaluatorHelper.__init__(self, ctlr, buf, trg, citdl_expr, line)
        #self._did_object = False
        self.converted_dot_new = converted_dot_new
        self.recursion_check_getattr = 0;
        self.visited = {}
        self._hit_helper = HitHelper()
        self._get_current_names = trg.type == "names"
        self._framework_role = buf.framework_role or ""

    recursion_check_limit = 10
    def _rec_check_inc_getattr(self):
        self.recursion_check_getattr += 1
        if self.recursion_check_getattr > self.recursion_check_limit:
            raise CodeIntelError("Expression too complex")

    def _rec_check_dec_getattr(self):
        self.recursion_check_getattr -= 1

    _common_classes = {"Kernel":None, "Class":None, "Object":None}
    def _skip_common_ref(self, cls_name):
       return self.trg.implicit and self._common_classes.has_key(cls_name)

    def _tokenize_citdl_expr(self, expr):
        toks = [x for x in token_splitter_re.split(expr) if x]
        if not toks:
            if self._get_current_names:
                return [""]
            else:
                return []
        elif toks[0] == "::":
            #XXX How does a leading :: affect symbol resolution here?
            # And a leading '.' should be a mistake
            del toks[0]
        return toks

    def eval_cplns(self):
        self.log_start()
        start_scoperef = self.get_start_scoperef()
        self.debug("eval_cplns **************** -- eval(%r), scoperef(%r)", self.expr, start_scoperef)
        self._base_scoperefs = self._calc_base_scoperefs(start_scoperef)
        # This maps blob names to None, but it should map
        # (blob_name, scoperef[0], str(scoperef[1])) to None
        self._visited_blobs = {}
        # And this should be (variable_name, scoperef) => None,
        # Not just variable_name
        self._visited_variables = {}
        hits = self._hits_from_citdl(self.expr)
        hits = self._uniqify(hits)
        # eval_cplns doesn't call itself recursively.
        self._visited_blobs = {}
        self._visited_variables = {}
        
        trg_type = self.trg.type
        if trg_type == "literal-methods":
            allowed_cplns = _CPLN_METHODS_INST
        elif trg_type == "module-names":
            allowed_cplns = _CPLN_ALL_BUT_METHODS|_CPLN_METHODS_ALL_FOR_MODULE
        elif trg_type == "object-methods":
            if _looks_like_constant_re.match(self.expr):
                allowed_cplns = _CPLN_ALL_BUT_METHODS|_CPLN_METHODS_ALL_FOR_MODULE
            else:
                allowed_cplns = _CPLN_METHODS_INST
        elif self._get_current_names:
            allowed_cplns = _CPLN_ALL
            elem = self._elem_from_scoperef(start_scoperef)
            if elem:
                ilk = elem.get("ilk")
                if ilk == "class":
                    allowed_cplns = _CPLN_ALL_BUT_METHODS|_CPLN_METHODS_CLASS
                elif ilk == "function" and not self._framework_role.startswith("rails.models"):
                    # Rails does too much with instance models dynamically
                    # at runtime:
                    # 1.) adds methods based on column names in the model's
                    #     underlying database table
                    # 2.) copies class methods into instance methods
                    
                    parent_scope = self.parent_scoperef_from_scoperef(start_scoperef)
                    parent_elem = self._elem_from_scoperef(parent_scope)
                    if parent_elem.get("ilk") == "class":
                        allowed_cplns = _CPLN_ALL_BUT_METHODS|_CPLN_METHODS_INST
                    # Otherwise allow them all
            
        else:
            raise CodeIntelError("Failed to handle trigger type '%s'" % trg_type)
        
        held_get_current_names = self._get_current_names
        self._get_current_names = False
        cplns = self._cplns_from_hits(hits, allowed_cplns)
        if held_get_current_names:
            for kwd in self.langintel.RUBY_KEYWORDS.keys():
                cplns.add(("function", kwd)) # "keyword" would be nice
            cplns = self._filter_by_prefix(cplns, self.expr)
        self.debug("eval_cplns: raw list: %r", cplns)
        cpln_list = list(cplns)
        # Don't bother if they have one more char to type.
        if (held_get_current_names and
            self.trg.implicit and
            len(cpln_list) == 1 and
            (cpln_list[0][1] == self.expr or
             (cpln_list[0][1][0 : -1] == self.expr))):
            return []
        return cpln_list

    def _filter_by_prefix(self, cplns, prefix):
        if prefix and len(prefix):
            cplns = [x for x in cplns if x[1].startswith(prefix)]
        return cplns

    def eval_calltips(self):
        self.log_start()
        self.debug("eval_calltip **************** -- eval(%r)" % self.expr)
        start_scoperef = self.get_start_scoperef()
        self._base_scoperefs = self._calc_base_scoperefs(start_scoperef)
        self._visited_blobs = {}
        self._visited_variables = {}
        hits = self._hits_from_citdl(self.expr)
        hits = self._uniqify(hits)
        self._visited_blobs = {}
        self._visited_variables = {}
        return self._calltips_from_hits(hits)

    def eval_defns(self):
        self.log_start()
        start_scoperef = self.get_start_scoperef()
        self._base_scoperefs = self._calc_base_scoperefs(start_scoperef)
        self._visited_blobs = {}
        self._visited_variables = {}
        hits = self._hits_from_citdl(self.expr)
        hits = self._uniqify(hits)
        defns = [self._defn_from_hit(hit) for hit in hits]
        return defns

    def _flatten(self, a):
        return reduce(lambda x,y: x + y, a, [])
    
    def _calc_base_scoperefs(self, curr_scoperef):
        scoperefs = [curr_scoperef, (self.built_in_blob, [])]
        # Next find the other scoperefs in the current scoperef
        imports = []
        while curr_scoperef:
            elem = self._elem_from_scoperef(curr_scoperef)
            # Are there any import tags here?
            imports.append([x for x in elem if x.tag == "import"])
            curr_scoperef = self.parent_scoperef_from_scoperef(curr_scoperef)
        imports.reverse()
        imports = self._flatten(imports)
        for imp_elem in imports:
            if imp_elem.get("module") is None:
                # include Namespace
                # Look at current scoperefs to resolve it
                namespace_name = imp_elem.get("symbol")
                if namespace_name[0].isupper():
                    # Use new_scoperefs to avoid modifying a list
                    # while we're looping over it
                    new_scoperefs = []
                    for sc in scoperefs:
                        self._visited_blobs = {}
                        sc_hits = self._hits_from_citdl(namespace_name,
                                                        resolve_var=False,
                                                        only_scoperef=sc)
                        for sc_hit in sc_hits:
                            sc_hit_name = sc_hit[0].get("name")
                            if sc_hit_name:
                                new_scoperefs.append((sc_hit[1][0],
                                        sc_hit[1][1] + sc_hit_name.split("::")))
                    scoperefs += new_scoperefs
            elif imp_elem.get("symbol") == "*":
                # Here we need to import a blob...
                blob = self._get_imported_blob(imp_elem)
                if blob is not None:
                    scoperefs.append((blob, []))

        # Check for blobs in the catalog
        # Note that we're getting closer to implementing 
        # a transitive closure for include statements.  With the
        # way Rails is implemented we're safe doing this to
        # one level of inclusion.

        if self._framework_role:
            framework_parts = self._framework_role.split(".")
            try:
                framework_name = framework_parts[0]
                catalog_selections = [framework_name]
                new_lib = self.mgr.db.get_catalog_lib("Ruby", catalog_selections)
                if new_lib:
                    node = new_lib.get_blob(framework_name)
                    framework_sc = (node, [])
                    scoperefs.append(framework_sc)

                    for imp_elem in imports:
                        if imp_elem.get("module") is None:
                            # include Namespace
                            # Look at current scoperefs to resolve it
                            namespace_name = imp_elem.get("symbol")
                            if namespace_name[0].isupper():
                                # Use new_scoperefs to avoid modifying a list
                                # while we're looping over it
                                new_scoperefs = []
                                self._visited_blobs = {}
                                sc_hits = self._hits_from_citdl(namespace_name,
                                                                resolve_var=False,
                                                                only_scoperef=framework_sc)
                                for sc_hit in sc_hits:
                                    inner_elem = sc_hit[0]
                                    sc_hit_name = inner_elem.get("name")
                                    if sc_hit_name:
                                        new_scoperefs.append((sc_hit[0], []))
                                        inner_imports = inner_elem.findall('import')
                                        for import2 in inner_imports:
                                            if import2.get('module') is None:
                                                inner_namespace_name = import2.get('symbol')
                                                if inner_namespace_name[0].isupper():
                                                    sc2_hits = self._hits_from_citdl(inner_namespace_name,
                                                                resolve_var=False,
                                                                only_scoperef=framework_sc)
                                                    for sc2_hit in sc2_hits:
                                                        new_scoperefs.append((sc2_hit[0], []))
                                scoperefs += new_scoperefs
                                
            except AttributeError, ex:
                self.debug("_calc_base_scoperefs: %s", ex)
                pass
            
        kh = self._get_kernel_hit()
        if kh is not None:
            scoperefs.append((kh[0], kh[1][1]))
        
        return scoperefs
    
    def _is_rails_application_controller(self, blob):
        for kid in blob.findall("scope"):
            if kid.tag == "scope" and kid.get("ilk") == "class" and kid.get("classrefs") == "ActiveController::Base":
                return True
        return False

    # All following methods initially stolen from tree_python.py,
    # then rewritten
    
    def _is_alias(self, elem):
        return elem.tag == "variable" and elem.get("attributes", "").find("__alias__") >= 0

    def _calltips_from_hits(self, hits):
        calltips = []
        for hit in hits:
            self.debug("looking for a calltip on hit %r", hit)
            elem, scoperef = hit
            if elem.tag == "scope":
                ilk = elem.get("ilk")
                if ilk == "function":
                    calltips.append(self._calltip_from_func(elem))
                elif ilk != "class":
                    # no calltips on classes
                    # only method and class names are expected here.
                    raise NotImplementedError("unexpected scope ilk for "
                                              "calltip hit: %r" % elem)
            elif self._is_alias(elem):
                # Is it an alias for a function?
                scoperef = self._find_first_scoperef(elem)
                if scoperef:
                    alias_hits = self._hits_from_variable_type_inference((elem, scoperef),
                                                                         resolve_var=False)
                    for alias_hit in alias_hits:
                        alias_elem = alias_hit[0]
                        if self._hit_helper.is_function(alias_hit):
                            calltip = self._calltip_from_func(alias_elem)\
                            # Hack: Perform surgery on the calltip if needed
                            if calltip.startswith(alias_elem.get("name")):
                                calltip = elem.get("name") + calltip[len(alias_elem.get("name")):]
                            calltips.append(calltip)
            else:
                raise NotImplementedError("unexpected elem for calltip "
                                          "hit: %r" % elem)
        return calltips

    def _uniqify(self, lst):
        if not lst:
            return lst
        new_list = []
        for i in range(len(lst) - 1):
            if lst[i] not in lst[i + 1:]:
                new_list.append(lst[i])
        new_list.append(lst[-1])
        return new_list
    
    def _find_first_scoperef(self, elem):
        blob = self._base_scoperefs[0][0]
        nodes = [node for node in blob.findall(".//variable")
                 if node.get("name") == elem.get("name")]
        for node in nodes:
            line_num = node.get("line")
            if line_num:
                return self.buf.scoperef_from_blob_and_line(blob, int(line_num) + 1)
            
    def _elem_classification(self, elem):
        if elem.tag == "variable":
            return _CPLN_VARIABLES
        elif elem.tag == "scope":
            ilk = elem.get("ilk")
            if ilk is None:
                return 0
            elif ilk == "namespace":
                return _CPLN_MODULES
            elif ilk == "class":
                return _CPLN_CLASSES
            elif ilk == "function":
                if (elem.get("attributes", "").find("__classmethod__") > -1
                    or elem.get("name").find(".") > -1):
                    return _CPLN_METHODS_CLASS
                else:
                    return _CPLN_METHODS_INST
        
        self.debug("Can't classify elem '%r'", elem)
        return 0
      
    def _cplns_from_hits(self, hits, allowed_cplns):
        members = set()
        self.debug("_cplns_from_hits: allowed_cplns %x", allowed_cplns)
          
        for hit in hits:
            elem, scoperef = hit
            self.debug("elem %r", elem)
            for child in elem:
                #self.debug("child %r", child)
                # child_type = self._hit_helper.get_type([child])
                if child.tag == "variable":
                    if self._is_alias(child):
                        # If the variable resolves to another object:
                        #    If it resolves to a function, use the target only
                        #    Otherwise use both the variable and its hits
                        scoperef = self._find_first_scoperef(child)
                        if scoperef:
                            alias_hits = self._hits_from_variable_type_inference((child, scoperef),
                                                                                 resolve_var=False)
                            include_self = False
                            for alias_hit in alias_hits:
                                alias_elem = alias_hit[0]
                                if self._hit_helper.is_variable(alias_hit):
                                    # Don't point var_lhs to var_rhs
                                    pass
                                elif (self._hit_helper.is_function(alias_hit)
                                      and not include_self
                                      and (allowed_cplns & _CPLN_METHODS_ALL)):
                                    include_self = True
                                    members.add( ("function", child.get("name")) )
                                    members.add( (alias_elem.get("ilk") or alias_elem.tag, alias_elem.get("name")) )
                                else:
                                    members.update(self._members_from_elem(child, allowed_cplns))
                    elif allowed_cplns & _CPLN_VARIABLES:
                        members.update(self._members_from_elem(child, allowed_cplns))
                else:
                    members.update(self._members_from_elem(child, allowed_cplns))
                    # Special case the child w.r.t the parent
                    if allowed_cplns & _CPLN_METHODS_ALL_FOR_MODULE:
                        elem_type = self._elem_classification(elem)
                        if elem_type & (_CPLN_MODULES|_CPLN_CLASSES):
                            child_type = self._elem_classification(child)
                            if ((child_type & _CPLN_METHODS_CLASS) or
                                ((child_type & _CPLN_METHODS_INST) and
                                 (elem_type == _CPLN_MODULES))):
                                members.add(("function", child.get("name")))
                    
            if elem.get("ilk") == "class":
                classref = elem.get("classrefs")
                if classref is not None:
                    if not self._visited_blobs.has_key(classref):
                        self._visited_blobs[classref] = None
                        insert_scoperef = True
                        self._base_scoperefs.insert(0, scoperef)
                        try:
                            ref_hits = self._hits_from_classref(classref)
                            del self._base_scoperefs[0]
                            insert_scoperef = False
                            if ref_hits:
                                members.update(self._cplns_from_hits(ref_hits, allowed_cplns))
                        finally:
                            if insert_scoperef:
                                del self._base_scoperefs[0]
         
                if ((allowed_cplns & _CPLN_METHODS_CLASS) or
                    ((allowed_cplns & _CPLN_METHODS_ALL_FOR_MODULE) and
                     (self._elem_classification(elem) & _CPLN_CLASSES))):
                    init_method = elem.names.get("initialize")
                    if not init_method or \
                       not init_method.get("attributes") == "private":
                        members.add(("function", "new"))
                    
        return members

    def _members_from_elem(self, elem, allowed_cplns):
        """Return the appropriate set of autocomplete completions for
        the given element. Typically this is just one, but can be more for
        '*'-imports
        """
        members = set()
        if elem.tag == "import":
            symbol_name = elem.get("symbol")
            module_name = elem.get("module")
            if module_name is None:
                if self._visited_blobs.has_key(symbol_name):
                    return members
                self._visited_blobs[symbol_name] = None
                hits = self._hits_from_citdl(symbol_name)
                for hit in hits:
                    for child in hit[0]:
                        members.update(self._members_from_elem(child, allowed_cplns))
            elif symbol_name is not None and self.citadel:
                if self._visited_blobs.has_key(module_name):
                    return members
                self._visited_blobs[module_name] = None
                import_handler = self.citadel.import_handler_from_lang(self.trg.lang)
                try:
                    self.debug("_members_from_elem: about to call import_handler.import_blob_name(module_name=%r), symbol_name=%r", module_name, symbol_name)
                    blob = import_handler.import_blob_name(
                                module_name, self.libs, self.ctlr)
                except CodeIntelError:
                    self.warn("_members_from_elem: limitation in handling imports in imported modules")
                    # It could be an incomplete module name in a require statement in the current buffer,
                    # so don't throw an exception.
                    return members
                
                # Check all children
                for blob_child in blob.getchildren():
                    imported_name = blob_child.get('name')
                    if imported_name is None:
                        continue
                    if symbol_name == "*" or symbol_name == imported_name:
                        try:
                            member_type = (blob_child.get("ilk") or blob_child.tag)
                            if symbol_name == "*":
                                if self._elem_classification(blob_child) & allowed_cplns:
                                    members.add((member_type, imported_name))
                            elif (member_type == "class"
                                  and (allowed_cplns & _CPLN_METHODS_INST)):
                                # Burrow if it doesn't match
                                for child_elem in blob_child:
                                    if self._elem_classification(child_elem) & allowed_cplns:
                                        members.add((child_elem.get("ilk"), child_elem.get("name")))
                                    else:
                                        self.debug("Not adding from %s: %s isn't allowed", imported_name, child_elem.get("name"))
                                        pass
                            else:
                                self.debug("Not adding from %s: member_type=%s or not fabricated", imported_name, member_type)
                                pass
                        except CodeIntelError, ex:
                            self.warn("_members_from_elem: %s (can't look up member %r in blob %r)", ex, imported_name, blob)
                
            elif allowed_cplns & _CPLN_MODULES:
                cpln_name = module_name.split('/', 1)[0]
                members.add( ("module", cpln_name) )
        elif self._elem_classification(elem) & allowed_cplns:
            members.add( (elem.get("ilk") or elem.tag, elem.get("name")) )
        return members
    
    def _hits_from_classref(self, expr):
        hits = self._hits_from_citdl(expr)
        if hits:
            return hits
        hits = [] # In case they're none
        # Look at the includes in this scoperef
        curr_scoperef = self._base_scoperefs[0]
        imports = []
        blobs = []
        #XXX Look only at includes in the current scope
        while curr_scoperef:
            elem = self._elem_from_scoperef(curr_scoperef)
            imports += self._get_included_modules(elem)
            blobs += [self._get_imported_blob(x) for x in self._get_required_modules(elem)]
            curr_scoperef = self.parent_scoperef_from_scoperef(curr_scoperef)
        
        for blob in blobs:
            # First look for top-level names in each blob
            hit_list = [x for x in blob if x.get("name") == expr]
            if expr in blob.names:
                hits += [(hit, (blob, [])) for hit in hit_list]
            # Now look to see if we've included any modules in blob
            for imp in imports:
                ns_name = imp.get('symbol')
                for ns_blob in blob:
                    if ns_blob.get("ilk") == "namespace" and ns_blob.get("name") == ns_name:
                        for candidate in ns_blob:
                            if candidate.get("ilk") == "class" and candidate.get("name") == expr:
                                hits += [(candidate, (blob, [ns_name]))]
        return hits
                    
            

    def _hits_from_citdl(self, expr, resolve_var=True, only_scoperef=None):
        """Resolve the given CITDL expression (starting at the given
        scope) down to a non-import/non-variable hit.
        
        The tokens contain ::'s and .'s so we know when we should have
        a namespace on the left, and when we should have a class or object.
        """
        tokens = self._tokenize_citdl_expr(expr)
        self.debug("_hit_from_citdl: expr tokens: %r, look in %d scopes",
                   tokens, only_scoperef and 1 or len(self._base_scoperefs))
        # Another note: if we only have one token, we assume we're
        # resolving a variable expression, and do the usual name lookups
        # Prefix handling has to be done by a different function that
        # looks only at self._base_scoperefs

        # First part...
        hits = self._hits_from_first_part(tokens[0], only_scoperef)
        if not hits:
            return NO_HITS
        #sys.stderr.write("%r\n" % hits)

        first_hit = hits[0]
        # If we're doing definition-lookup, we don't want to resolve
        # a standalone variable expression to its underlying type.
        # Just use the point its defined at, which is in the
        # hits variable.
        if (self._hit_helper.is_variable(first_hit) 
            and resolve_var
            and (len(tokens) > 1 or self.trg.form != TRG_FORM_DEFN)):
            hits = self._hits_from_variable_type_inference(first_hit)
            if not hits:
                return NO_HITS
            first_hit = hits[0]
            if self._hit_helper.is_variable(first_hit):
                var_name = self._hit_helper.get_name(first_hit)
                self.debug("_hit_from_citdl: failed to resolve variable '%r'",
                           var_name)
                return NO_HITS
                #raise CodeIntelError("Failed to resolve variable '%r'" % var_name)
            #sys.stderr.write("%r\n" % hits)
            prev_tok = first_hit[0].get("name", None) or tokens[0]
        else:
            prev_tok = tokens[0]
        
        # Now walk our list, first culling complete names separated
        # by [::, name] or [., name]
        idx = 1
        lim_sub1 = len(tokens) - 1

        if idx <= lim_sub1:
            if tokens[1] == "::" and not self._hit_helper.is_compound(first_hit):
                self.debug("_hit_from_citdl: trying to do namespace resolution on %s '%r'",
                           self._hit_helper.get_type(first_hit),
                           self._hit_helper.get_name(first_hit))
                return NO_HITS

        while idx <= lim_sub1 and hits:
            tok = tokens[idx]
            if tok == '::':
                filter_type = _NAMESPACE_RESOLUTION
            elif tok == '.':
                filter_type = _CLASS_RESOLUTION
            else:
                self.debug("_hit_from_citdl: got an unexpected resolution op of '%r'", tok)
                return NO_HITS
            idx += 1
            if idx > lim_sub1:
                break
            tok = tokens[idx]
            #XXX Pull out each name that isn't a prefix
            new_hits = []
            for hit in hits:
                new_hits += self._hits_from_getattr(hit, tok, filter_type) or []
            if not new_hits:
                return []
            hits = [(x[0], (x[1][0], x[1][1] + [prev_tok])) for x in new_hits]
            prev_tok = tok
            #XXX Replace with:
            #hits = [x for x in [self._continue_hit(hit, tok, filter_type) for hit in hits] if x]
            idx += 1
        return hits

    def _hits_from_getattr(self, hit, token, filter_type):
        self._rec_check_inc_getattr()
        try:
            new_hits = self._hits_from_getattr_aux(hit, token, filter_type)
            if not new_hits:
                self.debug("_hits_from_getattr: couldn't resolve %r.%r", hit[0], token)
            return new_hits
        finally:
            self._rec_check_dec_getattr()

    def _hits_from_getattr_aux(self, hit, first_token, filter_type):
        elem = hit[0]
        self.log("_hits_from_getattr: resolve getattr '%s' on %r, filter_type %d", first_token, elem, filter_type)
        
        if elem.tag == "variable":
            self.log("... failed on %s", elem.tag)
            return None
        
        assert elem.tag == "scope"
        ilk = elem.get("ilk")
        if ilk == "function":
            self.log("... failed on %s", ilk)
            return None
        elif ilk == "class":
            if first_token == 'new':
                return [hit]
            #XXX - stop allowing variables here.
            if first_token in elem.names:
                self.log("_hits_from_getattr: name %s is in %r", first_token, elem)                
                hits = []
                self._append_hits_from_name(hits, first_token, hit[1], elem)
                return hits
            self.debug("_hits_from_getattr: look for %r from imports in %r", first_token, elem)
            new_hit = self._hit_from_elem_imports(elem, first_token, filter_type)
            if new_hit:
                return [new_hit]

            classref = elem.get("classrefs")
            if classref:
                #if self._skip_common_ref(classref):
                #    continue
                if not self._visited_blobs.has_key(classref):
                    self._visited_blobs[classref] = True
                    new_hit = self._hit_from_type_inference(classref, first_token, filter_type)
                    if new_hit:
                        return [new_hit]
        elif ilk == "namespace":
            if first_token in elem.names:
                self.log("_hits_from_getattr: name %s is in %r", first_token, elem)              
                hits = []
                self._append_hits_from_name(hits, first_token, hit[1], elem)
                return hits
        
    def _hit_from_elem_imports(self, elem, first_token, filter_type):
        """See if token is from one of the imports on this <scope> elem.

        Returns a hit
        """
        #XXX Allow multiple hits
        
        self.debug("_hit_from_elem_imports :")
        # See some comments in the method with the same name in
        # tree_python.
        #
        # This routine recursively follows Ruby include statements,
        # guarding duplicates.

        imports = self._get_included_modules(elem)
        for imp in imports:
            hits = self._hits_from_citdl(imp.get("symbol"))
            for hit in hits:
                new_hits = self._hits_from_getattr(hit, first_token, filter_type)
                if new_hits:
                    return new_hits[0]
                
    def _hit_from_type_inference(self, classname, first_token, filter_type):
        hits = self._hits_from_citdl(classname)
        for hit in hits:
            new_hits = self._hits_from_getattr(hit, first_token, filter_type)
            if new_hits:
                return new_hits[0]
            
    def _get_kernel_hit(self):
        try:
            return self.built_in_blob.names["Kernel"], (self.built_in_blob, [])
        except KeyError:
            return None
        

    def _hits_from_first_part(self, first_token, only_scoperef):
        """Find all possible hits for the first token in the submitted
        scoperefs (normally the current blob and the builtin blob).
        
        We need to check all required modules as well --
        these look like <import module=lib symbol="*">
        
        Also check imported names: <import symbol=Namespace />

        Returns a list of <hit> or [] if we could
        not resolve.

        Example for 'String' normally:
            retval: [(<class 'String'>, (<blob '*'>, [])),]
        
        Let's say they opened it in the source to add a new method:
            retval: [(<class 'String'>, (<blob '*'>, [])),]
                     (<class 'String'>, (<blob 'this'>, ['file', 'class']))]
        """
        
        if self._get_current_names:
            # Look up the completions later.
            # Like in triggered lookup, move up the first blob only scoperef = self._base_scoperefs[0]
            hits = []
            scoperef = only_scoperef or self._base_scoperefs[0]
            while True:
                elem = self._elem_from_scoperef(scoperef)
                if elem is not None:
                    if only_scoperef is None:
                        hits.append((elem, scoperef))
                    elif first_token in elem.names:
                        self._append_hits_from_name(hits, first_token, scoperef, elem)
                scoperef = self.parent_scoperef_from_scoperef(scoperef)
                if not scoperef:
                    break
            
            # And put the rest of the blobs on the hit list
            if only_scoperef is None:
                hits += [(sc[0], sc) for sc in self._base_scoperefs[1:]]
            return hits
                
        # With the first one, we move up.  With others we don't.
        scoperef = only_scoperef or self._base_scoperefs[0]
        hits = []
        self.log("_hit_from_first_part: try to resolve '%s' ...", first_token)
        while scoperef:
            elem = self._elem_from_scoperef(scoperef)
            if elem is not None and first_token in elem.names:
                #TODO: skip __hidden__ names
                self.log("_hit_from_first_part: is '%s' accessible on %s? yes: %s",
                         first_token, scoperef, elem.names[first_token])
                self._append_hits_from_name(hits, first_token, scoperef, elem)
                break
            self.log("_hit_from_first_part: is '%s' accessible on %s? no", first_token, scoperef)
            scoperef = self.parent_scoperef_from_scoperef(scoperef)
        if only_scoperef or (hits and self._hit_helper.is_variable(hits[0])):
            return hits
        
        for scoperef in self._base_scoperefs[1:]:
            elem = self._elem_from_scoperef(scoperef)
            if first_token in elem.names:
                #TODO: skip __hidden__ names
                self.log("_hit_from_first_part: is '%s' accessible on %s? yes: %s",
                         first_token, scoperef, elem.names[first_token])
                self._append_hits_from_name(hits, first_token, scoperef, elem)
                
        if not hits:
            # Try importing all importable blobs then
            for scoperef in self._base_scoperefs[2:]:
                imports = self._get_required_modules(scoperef[0])
                for imp in imports:
                    blob = self._get_imported_blob(imp)
                    if blob and first_token in blob.names:
                        # Stop with one
                        return [(blob.names[first_token], [])]
                
        return hits
    
    def _append_hits_from_name(self, hits, first_token, scoperef, elem):
        blob, list = scoperef
        new_scoperef = blob, list # + [first_token]
        # Allow for multiple hits of compound things -- names() returns the last
        hit_list = [x for x in elem.findall("scope") if x.get("name") == first_token]
        if hit_list:
            if len(hit_list) > 1 and not hit_list[-1].get("name")[0].isupper():
                # Keep the last variable or function def
                hits.append((hit_list[-1], new_scoperef))
            else:
                hits += [(x, new_scoperef) for x in hit_list]
        else:
            hits.append((elem.names[first_token], new_scoperef))
                        
    def _get_imported_blob(self, imp_elem):
        return self._get_imported_blob_from_name(imp_elem.get("module"))

    def _get_imported_blob_from_name(self, module_name):
        import_handler = self.citadel.import_handler_from_lang(self.trg.lang)
        self.debug("_get_imported_blob(1): (module %r)?", module_name)
        try:
            blob = import_handler.import_blob_name(module_name, self.libs, self.ctlr)
            return blob
        except CodeIntelError, ex:
            # Continue looking
            self.warn("_get_imported_blob(2): %s", str(ex))

    def _get_included_modules(self, elem):
        return [x for x in elem.findall("import") if x.get("module") is None]

    def _get_required_modules(self, elem):
        return [x for x in elem.findall("import") if x.get("symbol") == "*"]

    def _hits_from_variable_type_inference(self, hit, resolve_var=True):
        """Resolve the type inference for 'elem' at 'scoperef'."""
        assert self._hit_helper.is_variable(hit)
        elem, scoperef = hit
        citdl = elem.get("citdl")
        if not citdl:
            raise CodeIntelError("_hit_from_variable_type_inference: no type-inference info for %r" % elem)
        if self._visited_variables.has_key(citdl):
            self.log("_hit_from_variable_type_inference: already looked at var '%s'", citdl)
            return NO_HITS
        self._visited_variables[citdl] = None
            
        self.log("_hit_from_variable_type_inference: resolve '%s' type inference for %r:", citdl, elem)
        # Always insert a scoperef while we're looking for a hit.
        self._base_scoperefs.insert(0, scoperef)
        try:
            hits = self._hits_from_citdl(citdl, resolve_var)
        finally:
            del self._base_scoperefs[0]
        self.debug("_hits_from_variable_type_inference(%s) (citdl '%r') ==> '%r'", elem.get("name"), citdl, hits)
        return hits

    _built_in_blob = None
    @property
    def built_in_blob(self):
        if self._built_in_blob is None:
            #HACK: Presume second-last or last lib is stdlib.
            #TODO: replace this with buf.stdlib.
            if isinstance(self.libs[-1], StdLib):
                stdlib = self.libs[-1]
            elif isinstance(self.libs[-2], StdLib):
                stdlib = self.libs[-2]
            assert isinstance(stdlib, StdLib), \
                   "not stdlib, but '%r'" % stdlib
            self._built_in_blob = stdlib.get_blob("*")
        return self._built_in_blob

    def parent_scoperef_from_scoperef(self, scoperef):
        #TODO: compare with CitadelEvaluator.getParentScope()
        blob, lpath = scoperef
        if lpath:
            return (blob, lpath[:-1])
        else:
            return None

    def post_process_cplns(self, cplns):
        self.debug("In RubyTreeEvaluator.post_process_cplns: %r", cplns)
        """Remove completions that don't start with a letter"""
        fixed_cplns = [x for x in cplns if letter_start_re.match(x[1])]
        return TreeEvaluatorHelper.post_process_cplns(self, fixed_cplns)

    _s_initialize_new = re.compile(r'^initialize\(')
    def post_process_calltips(self, calltips):
        #XXX Trent is this test right, or should I always convert?
        # Inside a class 'initialize' is a private class, and while
        # it shouldn't be called, it can be.
        
        if self.converted_dot_new:
            fixed_calltips = [self._s_initialize_new.sub('new(', x) for x in calltips]
            return fixed_calltips
        return calltips

    # c.f. tree_python.py::PythonTreeEvaluator
    # c.f. citadel.py::CitadelEvaluator
