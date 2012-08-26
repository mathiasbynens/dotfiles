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
# Portions created by ActiveState Software Inc are Copyright (C) 2010-2011
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

"""NodeJS support for CodeIntel"""

import os
import json
import logging

from codeintel2.util import makePerformantLogger
from codeintel2.lang_javascript import (JavaScriptLexer,
                                        JavaScriptLangIntel,
                                        JavaScriptBuffer,
                                        JavaScriptImportHandler,
                                        JavaScriptCILEDriver)
from codeintel2.tree_javascript import JavaScriptTreeEvaluator

#---- globals

lang = "Node.js"
log = logging.getLogger("codeintel.nodejs")
#log.setLevel(logging.DEBUG)
makePerformantLogger(log)


#---- language support

class NodeJSTreeEvaluator(JavaScriptTreeEvaluator):
    @property
    def nodejslib(self):
        if not hasattr(self, "_nodejslib"):
            libdir = os.path.join(os.path.dirname(__file__),
                                  "lib_srcs",
                                  "node.js")
            for lib in self.libs:
                if libdir in getattr(lib, "dirs", []):
                    self._nodejslib = lib
                    break
            else:
                self._nodejslib = None
        return self._nodejslib

    def _hits_from_commonjs_require(self, requirename, scoperef):
        """Resolve hits from a CommonJS require() invocation"""
        # this overrides the version in tree_javascript (JavaScriptTreeEvaluator)
        from codeintel2.database.langlib import LangDirsLib
        from codeintel2.database.multilanglib import MultiLangDirsLib
        from codeintel2.database.catalog import CatalogLib

        self.log("resolving require(%r) in %r", requirename, scoperef[0])

        stdlib = self.nodejslib
        if stdlib.has_blob(requirename + ".js"):
            # require(X) where X is a core module
            self.log("require(%r) is a core module", requirename)
            blob = stdlib.blobs_with_basename(requirename + ".js", ctlr=self.ctlr)[0]
            exports = blob.names.get("exports")
            return self._hits_from_variable_type_inference(exports, [blob, ["exports"]])

        srcdir = os.path.dirname(scoperef[0].get("src") or self.buf.path)
        if srcdir == "":
            # no source directory, can't do non-core lookups
            self.log("no source directory found, can't resolve require(%r)", requirename)
            return []

        def get_hits_from_lib(lib, filename):
            """Get the hits from a given LangDirsLib, or None"""
            hits = []
            basename = os.path.basename(filename)
            blobs = lib.blobs_with_basename(basename, ctlr=self.ctlr)
            for blob in blobs or []:
                if os.path.normpath(blob.get("src")) != filename:
                    # wrong file
                    continue
                self.log("require() found at %s", filename)
                exports = blob.names.get("exports")
                if exports is not None and exports.tag == "variable":
                    hits += self._hits_from_variable_type_inference(exports, [blob, ["exports"]])
                else:
                    # try module.exports
                    module = blob.names.get("module")
                    if module is not None:
                        exports = module.names.get("exports")
                        if exports is not None and exports.tag == "variable":
                            hits += self._hits_from_variable_type_inference(exports, [blob, ["module", "exports"]])
            return hits or None

        def load_as_file(path):
            """Load "path" as a file and return hits from there
            If it does not exist / isn't a valid node.js module, return None
            """
            path = os.path.normpath(path)
            if os.path.isfile(path):
                filename = path
            elif os.path.isfile(path + ".js"):
                filename = path + ".js"
            else:
                # we don't deal with binary components; otherwise, it's missing
                return None
            self.log("looking to resolve require() via %s", path)
            dirname = os.path.dirname(filename)

            for lib in self.libs:
                if lib == self.nodejslib:
                    # skip the core modules, they're looked at above
                    continue
                if not isinstance(lib, (LangDirsLib, MultiLangDirsLib)):
                    # can't deal with anything but these
                    self.log("skipping lib %r, don't know how to deal", lib)
                    continue

                if dirname in map(os.path.normpath, lib.dirs):
                    # Found a lib with the directory we want. Whether we found
                    # a hit or not, we don't need to look in any other libs
                    # (since they will just give the same results)
                    self.log("looking up lib %r (filename %r)", lib.dirs, filename)
                    return get_hits_from_lib(lib, filename)

            # none of the libs we know about has it, but we do have a file...
            # try to force scan it
            lib = self.mgr.db.get_lang_lib(self.lang, "node_modules_lib", (dirname,))
            return get_hits_from_lib(lib, filename)

        def load_as_directory(path):
            """Load "path" as a directory and return hits from there
            If it does not exist / isn't a valid node.js module, return None
            """
            path = os.path.normpath(path)
            if not os.path.isdir(path):
                # not a directory, don't bother
                return None
            hits = None
            manifest_path = os.path.join(path, "package.json")
            if os.path.isfile(manifest_path):
                manifest_file = open(manifest_path)
                try:
                    manifest = json.load(manifest_file)
                    if "main" in manifest:
                        main_path = os.path.join(path, manifest.get("main"))
                        main_path = os.path.normpath(main_path)
                        self.log("found module via %r, trying %r",
                                 manifest_path, main_path)
                        hits = load_as_file(main_path)
                except ValueError, e:
                    self.log("Error loading %r: %r", manifest_path, e)
                finally:
                    manifest_file.close()
            if hits is None:
                hits = load_as_file(os.path.join(path, "index"))
            return hits

        if requirename.lstrip(".").startswith("/"):
            self.log("require(%r) is file system", requirename)
            # filesystem path
            if requirename.startswith("/"):
                filename = requirename
            elif requirename.startswith("./") or requirename.startswith("../"):
                filename = os.path.join(srcdir, requirename)
            else:
                # invalid name
                return []
            filename = os.path.normpath(filename)
            self.log("resolving relative require(%r) via %s", requirename, filename)
            hits = load_as_file(filename)
            if hits is None:
                hits = load_as_directory(filename)
            return hits or []

        # if we get here, this is a bare module name, require("foo") or require("foo/bar")
        parts = os.path.normpath(srcdir).split(os.sep)
        try:
            root_index = parts.index("node_modules") - 1
        except ValueError:
            # no node_modules in the path at all
            root_index = -1
        for part_index in range(len(parts), root_index, -1):
            if part_index > 0 and parts[part_index - 1] == "node_modules":
                # don't try foo/node_modules/node_modules
                continue
            dir = os.sep.join(parts[:part_index] + ["node_modules"])
            hits = load_as_file(os.path.join(dir, requirename))
            if hits is None:
                hits = load_as_directory(os.path.join(dir, requirename))
            if hits is not None:
                return hits

        # last-ditch: try the extradirs pref
        extra_dirs = []
        for pref in self.buf.env.get_all_prefs(self.langintel.extraPathsPrefName):
            if not pref: continue
            for dir in pref.split(os.pathsep):
                dir = dir.strip()
                if not os.path.isdir(dir):
                    continue
                if not dir in extra_dirs:
                    extra_dirs.append(dir)
        for dir in extra_dirs:
            hits = load_as_file(os.path.join(dir, requirename))
            if hits is None:
                hits = load_as_directory(os.path.join(dir, requirename))
            if hits is not None:
                return hits

        self.log("Failed to find module for require(%r)", requirename)

        # getting here means we exhausted all possible modules; give up
        return []


class NodeJSLexer(JavaScriptLexer):
    lang = lang

class NodeJSLangIntel(JavaScriptLangIntel):
    lang = lang
    _evaluatorClass = NodeJSTreeEvaluator
    interpreterPrefName = "nodejsDefaultInterpreter"
    extraPathsPrefName = "nodejsExtraPaths"

    @property
    def stdlibs(self):
        libdir = os.path.join(os.path.dirname(__file__), "lib_srcs", "node.js")
        db = self.mgr.db
        node_sources_lib = db.get_lang_lib(lang="Node.js",
                                           name="node.js stdlib",
                                           dirs=(libdir,))
        return [node_sources_lib,
                db.get_stdlib(self.lang)]

class NodeJSBuffer(JavaScriptBuffer):
    lang = lang

class NodeJSImportHandler(JavaScriptImportHandler):
    lang = lang

class NodeJSCILEDriver(JavaScriptCILEDriver):
    lang = lang

#---- registration

def register(mgr):
    """Register language support with the Manager."""
    mgr.set_lang_info(lang,
                      silvercity_lexer=NodeJSLexer(mgr),
                      buf_class=NodeJSBuffer,
                      langintel_class=NodeJSLangIntel,
                      import_handler_class=NodeJSImportHandler,
                      cile_driver_class=NodeJSCILEDriver,
                      is_cpln_lang=True)
