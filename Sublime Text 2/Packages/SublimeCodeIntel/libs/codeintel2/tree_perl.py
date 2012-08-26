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

"""Completion evaluation code for Perl.

Dev Note: A Perl "package" vs. a Perl "module"
----------------------------------------------

A Perl *module* is the content of a .pm file (or .so file for binary
modules) that one imports via a "use" or "require" statement. This
corresponds to a codeintel "blob".

A Perl *package* is a language construct that is created in Perl modules
(or Perl scripts) via the "package" statement. Typically (*are* there
exceptions?) a Perl module file "Foo/Bar.pm" will define a "Foo::Bar"
package. These are represented in codeintel/CIX with a *class*.

Hence:

    -------- Salad.pm --------
    use strict;
    package Salad;
    # ...
    1;
    --------------------------

    <codeintel version="2.0">
      <file path="Salad.pm" lang="Perl">
        <scope ilk="blob" name="Salad">     <!-- this is the Salad *module* -->
          <scope ilk="class" name="Salad">  <!-- this is the Salad *package* -->
              ...
          </scope>
        </scope>
      </file>
    <codeintel>

"""

import re
from pprint import pprint

from codeintel2.common import *
from codeintel2.tree import TreeEvaluator
from codeintel2.database.stdlib import StdLib
from codeintel2.util import banner, isident


#---- internal support class for Perl package import semantics

class _PerlPkgTable(object):
    """An object for handling Perl module/package import semantics. Each
    cpln evaluation creates one of these to determine (and cache) the
    working set of loaded Perl packages.

    Usage:
        pkg_tbl = _PerlPkgTable(blob,       # top-level (i.e. current) blob
                                buf.libs)   # DB libs for the current buffer

        # Generate (<blob>, <package-names>) tuples for loaded packages.
        for blob, pkg_names in pkg_tbl.gen_loaded_pkgs():
            ...

        # Get the pkg (CIX 'class' element) defining the named package.
        pkg = pkg_tbl.pkg_from_pkg_name(pkg_name)
        mod, pkg = pkg_tbl.mod_and_pkg_from_pkg_name(pkg_name)
    """
    #TODO: Consider an index (a la toplevelname_index) for imported
    #      Perl packages. Post-4.0. Only iff Perl cpln needs the
    #      speed.

    def __init__(self, blob, libs):
        self.blob = blob
        self.libs = libs

        self._generator_cache = None
        self._mod_from_pkg_name = {}
        # Used to support multiple calls to .gen_loaded_pkgs()
        self._item_cache = []

    @property
    def _generator(self):
        if self._generator_cache is None:
            self._generator_cache = self._gen_loaded_pkgs(self.blob, set())
        return self._generator_cache

    def pkg_from_pkg_name(self, pkg_name):
        """Return the package (a CIX <scope ilk="class"> element) for
        the given package name. If the package definition cannot be
        found, this returns None.
        """
        if pkg_name in self._mod_from_pkg_name:
            mod = self._mod_from_pkg_name[pkg_name]
            if mod is not None:
                return mod.names.get(pkg_name)
        for mod, pkg_names in self._generator:
            if mod is None:
                continue
            if pkg_name in pkg_names:
                return mod.names.get(pkg_name)
        return None

    def mod_and_pkg_from_pkg_name(self, pkg_name):
        """Return the module (a CIX <scope ilk="blob">) and package (a
        CIX <scope ilk="class"> element) for the given package name. If
        the package definition cannot be found, this returns
        (None, None).
        """
        if pkg_name in self._mod_from_pkg_name:
            mod = self._mod_from_pkg_name[pkg_name]
            if mod is not None:
                return mod, mod.names.get(pkg_name)
        for mod, pkg_names in self._generator:
            if mod is None:
                continue
            if pkg_name in pkg_names:
                return mod, mod.names.get(pkg_name)
        return None, None

    def gen_loaded_pkgs(self):
        """Generate loaded (*) Perl packages recursively, starting from
        the given blob.

        This yields the following 2-tuples:
            (<blob>, <set of packages defined in this blob>)

        A "loaded" Perl package is one that is imported (via "use" or
        "require") or locally defined via a "package" statement.
        
        If a particular Perl module cannot be imported it is presumed to
        define one package of the same name (which is typical). In this
        case, <blob> will be None.
        """ 
        for item in self._item_cache:
            yield item
        for item in self._generator:
            yield item

    def _gen_loaded_pkgs(self, mod, handled_mod_names):
        mod_names, pkg_names = self._pkg_info_from_mod(mod)
        item = (mod, pkg_names)
        self._item_cache.append(item)
        for pkg_name in pkg_names:
            self._mod_from_pkg_name[pkg_name] = mod
        yield item

        for mod_name in (m for m in mod_names if m not in handled_mod_names):
            handled_mod_names.add(mod_name)
            for lib in self.libs:
                mod = lib.get_blob(mod_name)
                if mod is not None:
                    break
            else:
                #self.debug("could not import module %r, assuming it "
                #           "defines package of same name", mod_name)
                item = (None, set([mod_name]))
                self._item_cache.append(item)
                self._mod_from_pkg_name[mod_name] = None
                yield item
                continue

            for item in self._gen_loaded_pkgs(mod, handled_mod_names):
                yield item

    def _imported_mod_names_from_mod(self, mod):
        """Yield "reasonable" module names imported in the given module.
        
        "Reasonable" here means those that can be handled by the Perl
        cpln evalrs. The issue is Perl 'require' statements that can
        quote a string, use string interpolation, etc.
        """
        from os.path import splitext

        for imp_elem in mod.getiterator("import"):
            mod_name = imp_elem.get("module")
            
            if '$' in mod_name:
                # Abort on these guys:
                #   require $blah;        <import module="$blah"/>
                #   require '$foo.pm';    <import module="'$foo.pm'"/>
                continue
            elif mod_name[0] in ('"', "'"):
                # Try to gracefully handle these guys:
                #   require 'MyFoo.pm';   <import module="'MyFoo.pm'"/>
                #   require "MyBar.pm";   <import module="&quot;MyBar.pm&quot;"/>
                sans_quotes = mod_name[1:-1]
                sans_ext, ext = splitext(sans_quotes)
                if ext != ".pm":
                    # Note that we don't allow '.pl' b/c the import
                    # mechanics won't pick those up. I suspect that the
                    # frequency of "require 'foo.pl'" is low enough that
                    # we don't need to worry about this.
                    continue
                mod_name = sans_ext.replace('/', '::')
            yield mod_name

    def _pkg_info_from_mod(self, mod):
        """Return Perl package info for this module blob.
        
        Returns a 2-tuple:
            (<set of imported module names>, <set of defined package names>)
        """
        key = "perl-pkg-info"
        if key not in mod.cache:
            mod_names = set(self._imported_mod_names_from_mod(mod))
            #print "%r imports: %s" % (mod, ', '.join(mod_names))

            # Perl packages can only be defined at the top-level.
            pkg_names = set(elem.get("name") for elem in mod
                            if elem.get("ilk") == "class")
            #print "%r defines: %s" % (mod, ', '.join(pkg_names))

            mod.cache[key] = (mod_names, pkg_names)
        return mod.cache[key]




#---- the tree evaluators

class CandidatesForTreeEvaluator(TreeEvaluator):
    """Candidate functionality for the base TreeEvaluator class to be
    shared by the other lang-specific TreeEvaluators.

    TODO: evaluate and move these to base class sometime after K4
    """

    _built_in_blob = None
    @property
    def built_in_blob(self):
        if self._built_in_blob is None:
            stdlib = self.buf.stdlib
            assert isinstance(stdlib, StdLib), \
                "buf.stdlib did not return a StdLib instance: %r" % stdlib
            self._built_in_blob = stdlib.get_blob("*")
        return self._built_in_blob

    def parent_scoperef_from_scoperef(self, scoperef):
        blob, lpath = scoperef
        if lpath:
            return (blob, lpath[:-1])
        elif blob is self.built_in_blob:
            return None
        else:
            return (self.built_in_blob, [])

    def _elem_from_scoperef(self, scoperef):
        """A scoperef is (<blob>, <lpath>). Return the actual elem in
        the <blob> ciElementTree being referred to.
        """
        elem = scoperef[0]
        for lname in scoperef[1]:
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


class PerlTreeEvaluatorBase(CandidatesForTreeEvaluator):
    def __init__(self, ctlr, buf, trg, expr, line, prefix_filter=None):
        CandidatesForTreeEvaluator.__init__(self, ctlr, buf, trg, expr, line)
        self.prefix_filter = prefix_filter

    def pre_eval(self):
        curr_blob = self.buf.blob_from_lang[self.trg.lang]
        self.pkg_tbl = _PerlPkgTable(curr_blob, self.buf.libs)

    def _func_members_from_pkg(self, pkg_name, pkg, _handled_pkg_names=None):
        """Return the function completions for the given Perl package
        (traversing package inheritance, if any).
        """
        # Guard against infinite recursion.
        if _handled_pkg_names is None:
            _handled_pkg_names = set()
        if pkg_name in _handled_pkg_names:
            return []
        _handled_pkg_names.add(pkg_name)

        # Get the locally defined subs.
        members = [("function", n) for n,el in pkg.names.items()
                   if el.get("ilk") == "function"]

        # Get inherited subs.
        for classref in pkg.get("classrefs", "").split():
            if classref == "Exporter":
                # Special case: skip "Exporter" base class members in
                # Perl. These are not desired 99% of the time.
                continue
            self.info("add inherited functions from %r", classref)
            classref_pkg = self.pkg_tbl.pkg_from_pkg_name(classref)
            members += self._func_members_from_pkg(classref, classref_pkg,
                                                   _handled_pkg_names)

        return members


    # Special Perl variables/subs to typically _exclude_ from completions.
    _special_names_to_skip = set([
        "$AUTOLOAD", "AUTOLOAD", "DESTROY",
        "@EXPORT", "@EXPORT_FAIL", "@EXPORT_OK", "%EXPORT_TAGS",
        "@ISA", "import", "unimport",
    ])
    _perl_var_tokenizer = re.compile(r"([$\\%&@]+)?(\w+)")

    def post_process_cplns(self, cplns):
        DEBUG = False
        if DEBUG:
            print banner("Perl post_process_cplns (before)")
            pprint(cplns)
        
        trg_type = self.trg.type
        if trg_type in ("package-subs", "object-subs"):
            #TODO: This may not be necessary if current evalr only
            #      generates the function.
            cplns = [c for c in cplns
                     if c[0] == "function"
                     if c[1] not in self._special_names_to_skip]
        elif trg_type == "package-members":
            if self.prefix_filter in ('', '&'): # filter out variables
                cplns = [c for c in cplns
                         if c[0] != "variable"
                         if c[1] not in self._special_names_to_skip]
            elif self.prefix_filter in ('$', '@', '%'): # filter out funcs
                cplns = [c for c in cplns
                         if c[0] != "function"
                         if c[1] not in self._special_names_to_skip]
            else:
                cplns = [c for c in cplns 
                         if c[1] not in self._special_names_to_skip]
                
            # Morph type and value of variable based on the prefix.
            # For example the completions for: `$HTTP::Message::` include
            # ("variable", "$VERSION"). The actual correct completion is
            # "VERSION" (no '$'-prefix). We morph this to ("$variable",
            # "VERSION") so that:
            # 1. the proper completion will be used, and
            # 2. the different type string can be used for a custom
            #    autocomplete image.
            # Ditto for '@' and '%'.
            morphed_cplns = []
            for type, value in cplns:
                if type == "variable":
                    match = self._perl_var_tokenizer.match(value)
                    if not match:
                        self.warn("could not parse Perl var '%s': "
                                  "pattern='%s'", value,
                                  self._perl_var_tokenizer.pattern)
                        continue
                    prefix, name = match.groups()
                    if DEBUG:
                        print "tokenize perl var: %r -> %r %r"\
                              % (value, prefix, name)
                    if prefix:
                        prefix = prefix[-1] # only last char is relevant
                    
                    if self.prefix_filter in (None, '*', '$'):
                        # '*': pass all
                        # '$': pass all because arrays and hashes can have
                        #      a '$' prefix for subsequent indexing
                        pass
                    elif self.prefix_filter and self.prefix_filter != prefix:
                        # If the filter is '%' or '@', then filter out vars
                        # not of that persuasion.
                        continue
                    
                    #TODO: Test cases for these and review by Perl guy.
                    if prefix in ('$', '%', '@'):
                        # Don't yet support '*' special a/c image.
                        type = prefix+type
                    value = name
                morphed_cplns.append((type, value))
            cplns = morphed_cplns

        cplns = CandidatesForTreeEvaluator.post_process_cplns(self, cplns)
        if DEBUG:
            print banner("(after)", '-')
            pprint(cplns)
            print banner(None, '-')
        return cplns


class PerlPackageMembersTreeEvaluator(PerlTreeEvaluatorBase):
    """TreeEvaluator to handle 'perl-complete-package-members'.
    
        [prefix]SomePackage::<|>
    """
    # TODO: Consider implementing this subtlety (if current behaviour is
    #       not pleasing):
    #   - if trigger is explicit, then don't bother ensuring package
    #     is imported: *presume* it is
    #   - if trigger is implicit, then ensure package is imported

    def eval_cplns(self):
        self.log_start()

        prefix = self.expr + "::"
        prefix_len = len(prefix)
        prefix_matches = set()
        matching_blob = None
        for blob, pkg_names in self.pkg_tbl.gen_loaded_pkgs():
            for pkg_name in pkg_names:
                if pkg_name == self.expr:
                    matching_blob = blob
                elif pkg_name.startswith(prefix):
                    prefix_match = pkg_name[prefix_len:]
                    if "::" in prefix_match:
                        prefix_match = prefix_match[:prefix_match.index("::")]
                    #self.debug("prefix match: %r -> %r", pkg_name, prefix_match)
                    prefix_matches.add(prefix_match)

        if prefix_matches:
            self.info("loaded pkg prefix matches: %r", prefix_matches)
        cplns = [("class", pm) for pm in prefix_matches]
        if matching_blob is not None:
            try:
                pkg = matching_blob.names[self.expr]
            except KeyError:
                self.warn("%s unexpectedly doesn't define package %r",
                          matching_blob, self.expr)
            else:
                self.info("pkg match for %r: %r", self.expr, pkg)
                cplns += self._members_from_pkg(self.expr, pkg)
                
        return cplns

    def _members_from_pkg(self, pkg_name, pkg, _handled_pkg_names=None):
        """Return the completions for the given Perl package (traversing
        package inheritance, if any).
        """
        # Guard against infinite recursion.
        if _handled_pkg_names is None:
            _handled_pkg_names = set()
        if pkg_name in _handled_pkg_names:
            return []
        _handled_pkg_names.add(pkg_name)

        # Get the locally defined members.
        members = []
        for name, elem in pkg.names.items():
            #self.debug("%r: %r", name, elem)
            if elem.tag == "variable":
                if "__local__" not in elem.get("attributes", ""):
                    members.append(("variable", name))
            else:
                members.append((elem.get("ilk"), name))

        # Note: For perl-complete-package-members, inherited package
        # members should NOT be included. See
        # test_perl.py::test_myvars_2(). (Noting this because it might
        # be surprising.)

        return members


class PerlPackageSubsTreeEvaluator(PerlTreeEvaluatorBase):
    """TreeEvaluator to handle 'perl-complete-package-subs'

        SomePackage-><|>
    """
    def eval_cplns(self):
        self.log_start()

        # First ensure that this Perl package has been loaded.
        pkg = self.pkg_tbl.pkg_from_pkg_name(self.expr)
        if pkg is None:
            self.error("Perl package %r is not loaded", self.expr)
            return None

        self.info("pkg match for %r: %r", self.expr, pkg)
        return self._func_members_from_pkg(self.expr, pkg)

    def _func_members_from_pkg(self, pkg_name, pkg, _handled_pkg_names=None):
        """Return the function completions for the given Perl package
        (traversing package inheritance, if any).
        """
        # Guard against infinite recursion.
        if _handled_pkg_names is None:
            _handled_pkg_names = set()
        if pkg_name in _handled_pkg_names:
            return []
        _handled_pkg_names.add(pkg_name)

        # Get the locally defined subs.
        members = [("function", n) for n,el in pkg.names.items()
                   if el.get("ilk") == "function"]

        # Get inherited subs.
        for classref in pkg.get("classrefs", "").split():
            if classref == "Exporter":
                # Special case: skip "Exporter" base class members in
                # Perl. These are not desired 99% of the time.
                continue
            self.info("add inherited functions from %r", classref)
            classref_pkg = self.pkg_tbl.pkg_from_pkg_name(classref)
            members += self._func_members_from_pkg(classref, classref_pkg,
                                                   _handled_pkg_names)

        return members



class PerlTreeEvaluator(PerlTreeEvaluatorBase):
    """TreeEvaluator to handle the following triggers:

        perl-calltip-space-call-signature   "open <|>"
        perl-calltip-call-signature         "some_func(<|>"
        perl-complete-object-subs           "$foo-><|>"

    TODO: perl-defn-defn
    """
    def __init__(self, ctlr, buf, trg, expr, line, prefix_filter=None):
        PerlTreeEvaluatorBase.__init__(self, ctlr, buf, trg, expr, line)
        self.prefix_filter = prefix_filter

    def eval_cplns(self):
        self.log_start()
        start_scoperef = self.get_start_scoperef()
        self.info("start scope is %r", start_scoperef)
        hit = self._hit_from_citdl(self.expr, start_scoperef)

        elem, scoperef = hit
        if not (elem.tag == "scope" and elem.get("ilk") == "class"):
            perl_type = self._perl_type_from_elem(elem)
            self.error("cannot get completions from a Perl %s: '%s' is "
                       "<%s %s> (expected a Perl package element)",
                       perl_type, self.expr, perl_type, elem.get("name"))
            return None
        return self._func_members_from_pkg(elem.get("name"), elem)

    def eval_calltips(self):
        self.log_start()
        start_scoperef = self.get_start_scoperef()
        self.info("start scope is %r", start_scoperef)
        elem, scoperef = self._hit_from_citdl(self.expr, start_scoperef)
        if not (elem.tag == "scope" and elem.get("ilk") == "function"):
            perl_type = self._perl_type_from_elem(elem)
            self.error("cannot call a Perl %s: '%s' is <%s %s>",
                       perl_type, self.expr, perl_type, elem.get("name"))
            return None
        return [ self._calltip_from_func(elem) ]

    def eval_defns(self):
        self.log_start()
        start_scoperef = self.get_start_scoperef()
        self.info("start scope is %r", start_scoperef)
        hit = self._hit_from_citdl(self.expr, start_scoperef, defn_only=True)
        return [ self._defn_from_hit(hit) ]

    def _perl_type_from_elem(self, elem):
        if elem.tag == "scope":
            ilk = elem.get("ilk")
            return {"function": "sub",
                    "class": "package",
                    "blob": "module"}.get(ilk, ilk)
        else:
            return "variable"

    def _calltip_from_func(self, elem):
        # See "Determining a Function CallTip" in the spec for a
        # discussion of this algorithm.
        signature = elem.get("signature")
        if not signature:
            ctlines = [elem.get("name") + "(...)"]
        else:
            ctlines = signature.splitlines(0)
        doc = elem.get("doc")
        if doc:
            ctlines += doc.splitlines(0)
        return '\n'.join(ctlines)

    def _hit_from_citdl(self, expr, scoperef, defn_only=False):
        """Resolve the given CITDL expression (starting at the given
        scope) down to a non-import/non-variable hit: i.e. down to a
        function or class (a.k.a., Perl package).
        """
        self._check_infinite_recursion(expr)

        tokens = list(self._tokenize_citdl_expr(expr))
        #self.debug("expr tokens: %r", tokens)

        # First part...
        first_token = tokens.pop(0)
        hit = self._hit_from_first_part(first_token, scoperef)
        if not hit:
            raise CodeIntelError("could not resolve '%s'" % first_token)
        #self.debug("_hit_from_citdl: first part: %r -> %r", first_token, hit)

        # ...remaining parts.
        while tokens:
            token = tokens.pop(0)
            if token == "()":
                raise CodeIntelError("eval of Perl function calls not yet "
                                     "implemented: %r" % expr)
            self.info("lookup '%s' on %r in %r", token, *hit)
            #TODO: Should we catch CodeIntelError, self.error() and
            #      return None?
            hit = self._hit_from_getattr(token, *hit)
        if tokens:
            raise CodeIntelError("multi-part Perl CITDL expr '%s' cannot "
                                 "yet be handled" % expr)

        # Resolve any variable type inferences.
        elem, scoperef = hit
        if elem.tag == "variable" and not defn_only:
            hit = self._hit_from_variable_type_inference(elem, scoperef)

        self.info("'%s' is %s on %s", expr, *hit)
        return hit

    def _hit_from_first_part(self, first_token, scoperef):
        """Find a hit for the first part of the tokens.

        Returns a <hit> or None if could not resolve.

        Examples:
            '$ua'    -> <variable '$ua'>,
                        (<blob 'myscript'>, [])
            'Dumper' -> <function 'Dumper'>,
                        (<blob 'Data::Dumper'>, ['Data::Dumper'])
            'Data::Dumper' ->
                        <class 'Data::Dumper'>,
                        (<blob 'Data::Dumper'>, [])
        """
        #self.log("find '%s' starting at %s:", first_token, scoperef)
        while 1:
            elem = self._elem_from_scoperef(scoperef)
            if first_token in elem.names:
                #TODO: skip __hidden__ names
                self.log("is '%s' accessible on %s? yes: %s",
                         first_token, scoperef, elem.names[first_token])
                return elem.names[first_token], scoperef

            if "::" not in first_token:
                hit = self._hit_from_elem_imports(first_token, elem)
                if hit is not None:
                    self.log("is '%s' accessible on %s? yes: %s",
                             first_token, scoperef, hit[0])
                    return hit

            mod, pkg = self.pkg_tbl.mod_and_pkg_from_pkg_name(first_token)
            if mod is not None:
                self.log("is '%s' accessible on %s? yes: %s",
                         first_token, scoperef, pkg)
                return (pkg, (mod, [first_token]))


            self.log("is '%s' accessible on %s? no", first_token, scoperef)
            scoperef = self.parent_scoperef_from_scoperef(scoperef)
            if not scoperef:
                return None

    def _hit_from_getattr(self, token, elem, scoperef):
        """Return a hit for a getattr on the given element.

        Returns <hit> or raises CodeIntelError if cannot resolve.
        """
        if elem.tag == "variable":
            elem_is_var_on_entry = True
            elem, scoperef = self._hit_from_variable_type_inference(elem, scoperef)
        else:
            elem_is_var_on_entry = False

        assert elem.tag == "scope"
        ilk = elem.get("ilk")
        if ilk == "class": # i.e. a Perl package
            attr = elem.names.get(token)
            if attr is not None:
                return attr, (scoperef[0], scoperef[1] + [elem.get("name")])

            # To inherit or not to inherit
            # ============================
            #
            # Both of the following get here:
            #   $ua->foo();              lookup "foo" on LWP::UserAgent
            #   Data::Dumper::Dumper();  lookup "Dumper" on Data::Dumper
            # However, only the former should include inherited methods.
            #
            # I *believe* we can tell the difference based on whether
            # 'elem' (on entry to this function) is a variable. If it is
            # a variable then this is the former case.
            #
            # Note that we cannot use the trigger type to determine this
            # because this could be part of eval of
            # "perl-calltip-call-signature" for both:
            #   $ua->foo(<|>);
            #   Data::Dumper::Dumper(<|>);
            if elem_is_var_on_entry:
                # Look on inherited packages (test 'perl/cpln/lwp'
                # tests for multi-level inheritance).
                for base_mod, base_pkg \
                        in self._inherited_mods_and_pkgs_from_pkg(elem):
                    attr = base_pkg.names.get(token)
                    if attr is not None:
                        return attr, (base_mod, [base_pkg.get("name")])

        elif ilk == "blob":  # i.e. a Perl module
            raise CodeIntelError("didn't expect a getattr on a Perl "
                                 "module: %r on %r" % (token, elem))
            #attr = elem.names.get(first_token)
            #if attr is not None:
            #    self.log("attr is %r in %r", attr, elem)
            #    return attr, scoperef

        elif ilk == "function":
            raise CodeIntelError("cannot get attributes of a "
                                 "function: %r on %r" % (token, elem))

        else:
            raise NotImplementedError("unexpected scope ilk: %r" % ilk)

        raise CodeIntelError("could not resolve '%s' attr on %s"
                             % (token, elem))

    def _inherited_mods_and_pkgs_from_pkg(self, pkg, _handled_pkg_names=None):
        """Generate the inherited packages of the given package.

        Yields (mod, pkg) 2-tuples. The "Exporter" package is skipped.
        """
        pkg_name = pkg.get("name")

        # Guard against infinite recursion.
        if _handled_pkg_names is None:
            _handled_pkg_names = set()
        if pkg_name not in _handled_pkg_names:
            _handled_pkg_names.add(pkg_name)

            for classref in pkg.get("classrefs", "").split():
                if classref == "Exporter":
                    # Special case: skip "Exporter" base class members in
                    # Perl. These are not desired 99% of the time.
                    continue
                classref_mod, classref_pkg \
                    = self.pkg_tbl.mod_and_pkg_from_pkg_name(classref)
                if classref_pkg is None:
                    continue
                yield (classref_mod, classref_pkg)
                for item in self._inherited_mods_and_pkgs_from_pkg(
                                classref_pkg, _handled_pkg_names):
                    yield item

    def _hit_from_elem_imports(self, token, elem):
        """See if token is from one of the imports on this <scope> elem.

        Returns <hit> or None if not found.
        """
        for imp_elem in (i for i in elem if i.tag == "import"):
            # Note: Perl <import> elements never use 'alias'.
            symbol_name = imp_elem.get("symbol")
            module_name = imp_elem.get("module")
            assert module_name, \
                "bogus Perl <import> without module name: %r" % imp_elem

            if not symbol_name:
                # use Foo ();           <import module="Foo"/>
                # require $blah;        <import module="$blah"/>
                # require '$foo.pm';    <import module="'$foo.pm'"/>
                # require 'MyFoo.pm';   <import module="'MyFoo.pm'"/>
                # require "MyBar.pm";   <import module="&quot;MyBar.pm&quot;"/>
                pass

            elif symbol_name == token:
                # use Foo qw(a);        <import module="Foo" symbol="a"/>
                mod, pkg = self.pkg_tbl.mod_and_pkg_from_pkg_name(module_name)
                if mod is not None:
                    elem = pkg.names.get(token)
                    if elem is not None:
                        #TODO: Should we exclude this if not in
                        #      @EXPORT_OK?
                        self.debug("is '%s' from %r? yes: %s",
                                   token, imp_elem, elem)
                        return (elem, (mod, [module_name]))

            elif symbol_name == "*":
                # use Foo;              <import module="Foo" symbol="*"/>
                mod, pkg = self.pkg_tbl.mod_and_pkg_from_pkg_name(module_name)
                if mod is not None:
                    elem = pkg.names.get(token)
                    if elem is not None \
                       and "__exported__" in elem.get("attributes", ""):
                        self.debug("is '%s' from %r? yes: %s",
                                   token, imp_elem, elem)
                        return (elem, (mod, [module_name]))

            elif symbol_name == "**":
                # use Foo qw(:key);     <import module="Foo" symbol="**"/>
                mod, pkg = self.pkg_tbl.mod_and_pkg_from_pkg_name(module_name)
                if mod is not None:
                    elem = pkg.names.get(token)
                    # "__exported__" attribute means in @EXPORT
                    # "__exportable__" attribute means in @EXPORT_OK
                    if elem is not None \
                       and "__export" in elem.get("attributes", ""):
                        self.debug("is '%s' from %r? yes: %s",
                                   token, imp_elem, elem)
                        return (elem, (mod, [module_name]))

            self.debug("is '%s' from %r? no", token, imp_elem)
        return None

    def _hit_from_variable_type_inference(self, elem, scoperef):
        """Resolve the type inference for the given element."""
        #TODO:PERF: Consider cheating here with the knowledge that the
        #           current perlcile (the one as of Komodo 4.0.0) never
        #           emits anything except a package name for a type
        #           inference.
        citdl = elem.get("citdl")
        if not citdl:
            raise CodeIntelError("no type-inference info for %r" % elem)
        self.info("resolve '%s' type inference for %r:", citdl, elem)
        return self._hit_from_citdl(citdl, scoperef)

    def _hit_from_type_inference(self, citdl, scoperef):
        """Resolve the 'citdl' type inference at 'scoperef'."""
        #TODO:PERF: Consider cheating here with the knowledge that the
        #           current perlcile (the one as of Komodo 4.0.0) never
        #           emits anything except a package name for a type
        #           inference.
        self.info("resolve '%s' type inference:", citdl)
        return self._hit_from_citdl(citdl, scoperef)


