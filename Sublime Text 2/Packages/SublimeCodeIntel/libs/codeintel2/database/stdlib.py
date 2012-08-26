#!python
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

"""The stdlib zone of the codeintel database.
See the database/database.py module docstring for an overview.
"""


import sys
import os
from os.path import (join, dirname, exists, expanduser, splitext, basename,
                     split, abspath, isabs, isdir, isfile)
import cPickle as pickle
import threading
import time
import bisect
import fnmatch
from glob import glob
from pprint import pprint, pformat
import logging
from cStringIO import StringIO
import codecs
import copy
import weakref
import Queue

import ciElementTree as ET
from codeintel2.common import *
from codeintel2.buffer import Buffer
from codeintel2.util import dedent, safe_lang_from_lang, banner
from codeintel2.tree import tree_from_cix_path
from codeintel2.database.resource import AreaResource
from codeintel2.database.util import (rmdir, filter_blobnames_for_prefix)



#---- globals

log = logging.getLogger("codeintel.db")
#log.setLevel(logging.DEBUG)



#---- Database zone and lib implementations

class StdLib(object):
    """Singleton lib managing a particular db/stdlibs/<stdlib-name>
    area of the db.

    These are dished out via Database.get_stdlib(), which indirectly
    then is dished out by the StdLibsZone.get_lib().

    Because (1) any updating of the stdlib db area for this language has
    already been done (by StdLibsZone.get_lib()) and (2) this is a
    singleton: we shouldn't have to worry about locking.
    """
    _blob_index = None
    _toplevelname_index = None
    _toplevelprefix_index = None

    def __init__(self, db, base_dir, lang, name):
        self.db = db
        self.lang = lang
        self.name = name
        self.base_dir = base_dir
        self._import_handler = None
        self._blob_imports_from_prefix_cache = {}
        self._blob_from_blobname = {}

    def __repr__(self):
        return "<%s stdlib>" % self.name

    @property
    def import_handler(self):
        if self._import_handler is None:
            self._import_handler \
                = self.db.mgr.citadel.import_handler_from_lang(self.lang)
        return self._import_handler

    @property
    def blob_index(self):
        if self._blob_index is None:
            idxpath = join(self.base_dir, "blob_index")
            self._blob_index = self.db.load_pickle(idxpath)
        return self._blob_index

    @property
    def toplevelname_index(self):
        if self._toplevelname_index is None:
            idxpath = join(self.base_dir, "toplevelname_index")
            self._toplevelname_index = self.db.load_pickle(idxpath)
        return self._toplevelname_index

    @property
    def toplevelprefix_index(self):
        if self._toplevelprefix_index is None:
            idxpath = join(self.base_dir, "toplevelprefix_index")
            self._toplevelprefix_index = self.db.load_pickle(idxpath)
        return self._toplevelprefix_index

    def has_blob(self, blobname):
        return blobname in self.blob_index

    def get_blob(self, blobname):
        # Cache the blob once. Don't need to worry about invalidating the stdlib
        # blobs as stdlibs should not change during a Komodo session, bug 65502.
        blob = self._blob_from_blobname.get(blobname)
        if blob is None:
            try:
                dbfile = self.blob_index[blobname]
            except KeyError:
                return None
            blob = self.db.load_blob(join(self.base_dir, dbfile))
            self._blob_from_blobname[blobname] = blob
        return blob

    def get_blob_imports(self, prefix):
        """Return the set of imports under the given prefix.

            "prefix" is a tuple of import name parts. E.g. ("xml", "sax")
                for "import xml.sax." in Python. Or ("XML", "Parser") for
                "use XML::Parser::" in Perl.

        See description in database.py docstring for details.
        """
        if prefix not in self._blob_imports_from_prefix_cache:
            matches = filter_blobnames_for_prefix(self.blob_index,
                        prefix, self.import_handler.sep)
            self._blob_imports_from_prefix_cache[prefix] = matches
        return self._blob_imports_from_prefix_cache[prefix]

    def hits_from_lpath(self, lpath, ctlr=None, curr_buf=None):
        """Return all hits of the given lookup path.
        
        I.e. a symbol table lookup across all files in the dirs of this
        lib.

            "lpath" is a lookup name list, e.g. ['Casper', 'Logging']
                or ['dojo', 'animation'].
            "ctlr" (optional) is an EvalController instance. If
                specified it should be used in the normal way (logging,
                checking .is_aborted()).
            "curr_buf" (optional) is not relevant for StdLib. Used for
                other *Lib classes.

        A "hit" is (<CIX node>, <scope-ref>).  Each one represent a
        scope-tag or variable-tag hit in all of the blobs for the
        execution set buffers.

        Returns the empty list if no hits.
        """
        assert isinstance(lpath, tuple)  # common mistake to pass in a string
        hits = []
        # toplevelname_index: {ilk -> toplevelname -> blobnames}
        for blobnames_from_toplevelname in self.toplevelname_index.itervalues():
            for blobname in blobnames_from_toplevelname.get(lpath[0], ()):
                blob = self.get_blob(blobname)
                try:
                    elem = blob
                    for p in lpath:
                        #LIMITATION: *Imported* names at each scope are
                        # not being included here. This is fine while we
                        # just care about JavaScript.
                        elem = elem.names[p]
                except KeyError:
                    continue
                hits.append( (elem, (blob, list(lpath[:-1]))) )
        return hits

    def toplevel_cplns(self, prefix=None, ilk=None):
        """Return completion info for all top-level names matching the
        given prefix and ilk in all blobs in this lib.
        
            "prefix" is a 3-character prefix with which to filter top-level
                names. If None (or not specified), results are not filtered
                based on the prefix.
            "ilk" is a symbol type (e.g. "class", "variable", "function")
                with which to filter results. If None (or not specified),
                results of any ilk are returned.
            "ctlr" (optional) is an EvalController instance. If
                specified it should be used in the normal way (logging,
                checking .is_aborted()).

        Returns a list of 2-tuples: (<ilk>, <name>).

        Note: the list is not sorted, because often some special sorting
        is required for the different completion evaluators that might use
        this API.
        """
        cplns = []
        if prefix is None:
            # Use 'toplevelname_index': {ilk -> toplevelname -> blobnames}
            for i, bft in self.toplevelname_index.iteritems():
                if ilk is not None and i != ilk:
                    continue
                cplns += [(i, toplevelname) for toplevelname in bft]
        else:
            # Use 'toplevelprefix_index':
            #   {ilk -> prefix -> toplevelnames}
            if ilk is not None:
                try:
                    toplevelnames = self.toplevelprefix_index[ilk][prefix]
                except KeyError:
                    pass
                else:
                    cplns += [(ilk, t) for t in toplevelnames]
            else:
                for i, tfp in self.toplevelprefix_index.iteritems():
                    if prefix not in tfp:
                        continue
                    cplns += [(i, t) for t in tfp[prefix]]

        return cplns
        


class StdLibsZone(object):
    """Singleton zone managing the db/stdlibs/... area.

    Because this is a singleton we shouldn't have to worry about locking
    to prevent corruption.
    """
    _res_index = None                   # cix-path -> last-updated

    def __init__(self, db):
        self.db = db
        self.stdlibs_dir = join(dirname(dirname(__file__)), "stdlibs")
        self.base_dir = join(self.db.base_dir, "db", "stdlibs")
        self._stdlib_from_stdlib_ver_and_name = {} # cache of StdLib singletons
        self._vers_and_names_from_lang = {} # lang -> ordered list of (ver, name)

    def vers_and_names_from_lang(self, lang):
        "Returns an ordered list of (ver, name) for the given lang."
        #  _vers_and_names_from_lang = {
        #    "php": [
        #              ((4,3), "php-4.3"),
        #              ((5.0), "php-5.0"),
        #              ((5.1), "php-5.1"),
        #              ((5.2), "php-5.2"),
        #              ((5,3), "php-5.3")
        #         ],
        #    "ruby": [
        #              (None, "ruby"),
        #         ],
        #    ...
        #  }
        vers_and_names = self._vers_and_names_from_lang.get(lang)
        if vers_and_names is None:
            # Find the available stdlibs for this language.
            cix_glob = join(self.stdlibs_dir, safe_lang_from_lang(lang)+"*.cix")
            cix_paths = glob(cix_glob)
            vers_and_names = []
            for cix_path in cix_paths:
                name = splitext(basename(cix_path))[0]
                if '-' in name:
                    base, ver_str = name.split('-', 1)
                    ver = _ver_from_ver_str(ver_str)
                else:
                    base = name
                    ver = None
                if base.lower() != lang.lower():
                    # Only process when the base name matches the language.
                    # I.e. skip if base is "python3" and lang is "python".
                    continue
                vers_and_names.append((ver, name))
            vers_and_names.sort()
            self._vers_and_names_from_lang[lang] = vers_and_names
        return vers_and_names

    @property
    def res_index(self):
        "cix-path -> last-updated"
        if self._res_index is None:
            idxpath = join(self.base_dir, "res_index")
            self._res_index = self.db.load_pickle(idxpath, {})
        return self._res_index
    
    def save(self):
        if self._res_index is not None:
            self.db.save_pickle(join(self.base_dir, "res_index"),
                                self._res_index)

    def get_lib(self, lang, ver_str=None):
        """Return a view into the stdlibs zone for a particular language
        and version's stdlib.

            "lang" is the language, e.g. "Perl", for which to get a
                stdlib.
            "ver_str" (optional) is a specific version of the language,
                e.g. "5.8".

        On first get of a stdlib for a particular language, all
        available stdlibs for that lang are updated, if necessary.

        Returns None if there is not stdlib for this language.
        """
        vers_and_names = self.vers_and_names_from_lang(lang)
        if not vers_and_names:
            return None
        if ver_str is None:
            # Default to the latest version.
            ver = vers_and_names[-1][0]
        else:
            ver = _ver_from_ver_str(ver_str)

        # Here is something like what we have for PHP:
        #    vers_and_names = [
        #        (None, "php"),
        #        ((4,0), "php-4.0"),
        #        ((4,1), "php-4.1"),
        #        ((4,2), "php-4.2"),
        #        ((4,3), "php-4.3"),
        #        ((5,0), "php-5.0"),
        #        ((5,1), "php-5.1"),
        #    ]
        # We want to (quickly) pick the best fit stdlib for the given
        # PHP version:
        #   PHP (ver=None): php
        #   PHP 3.0:        php
        #   PHP 4.0:        php-4.0 (exact match)
        #   PHP 4.0.2:      php-4.0 (higher sub-version)
        #   PHP 4.4:        php-4.3
        #   PHP 6.0:        php-5.1
        key = (ver, "zzz") # 'zzz' > any stdlib name (e.g., 'zzz' > 'php-4.2')
        idx = max(0, bisect.bisect_right(vers_and_names, key)-1)
        log.debug("best stdlib fit for %s ver=%s in %s is %s",
                  lang, ver, vers_and_names, vers_and_names[idx])
        
        stdlib_match = vers_and_names[idx]
        stdlib_ver, stdlib_name = stdlib_match

        if stdlib_match not in self._stdlib_from_stdlib_ver_and_name:
            # TODO: This _update_lang_with_ver method should really moved into
            #       the StdLib class.
            self._update_lang_with_ver(lang, ver=stdlib_ver)
            stdlib = StdLib(self.db,
                            join(self.base_dir, stdlib_name),
                            lang, stdlib_name)
            self._stdlib_from_stdlib_ver_and_name[stdlib_match] = stdlib

        return self._stdlib_from_stdlib_ver_and_name[stdlib_match]

    def _get_preload_zip(self):
        return join(self.stdlibs_dir, "stdlibs.zip")

    def can_preload(self):
        """Return True iff can preload."""
        if exists(self.base_dir):
            log.info("can't preload stdlibs: `%s' exists", self.base_dir)
            return False
        try:
            import process
            import which
        except ImportError, ex:
            log.info("can't preload stdlibs: %s", ex)
            return False
        try:
            which.which("unzip")
        except which.WhichError, ex:
            log.info("can't preload stdlibs: %s", ex)
            return False
        preload_zip = self._get_preload_zip()
        if not exists(preload_zip):
            log.info("can't preload stdlibs: `%s' does not exist", preload_zip)
            return False
        return True

    def preload(self, progress_cb=None):
        """Pre-load the stdlibs zone, if able.

            "progress_cb" (optional) is a callable that is called as
                follows to show the progress of the update:
                    progress_cb(<desc>, <value>)
                where <desc> is a short string describing the current step
                and <value> is an integer between 0 and 100 indicating the
                level of completeness.

        Use `.can_preload()' to determine if able to pre-load.
        """
        import which
        import process

        log.debug("preloading stdlibs zone")
        if progress_cb:
            try:    progress_cb("Preloading stdlibs...", None)
            except: log.exception("error in progress_cb (ignoring)")
        preload_zip = self._get_preload_zip()
        unzip_exe = which.which("unzip")
        cmd = '"%s" -q -d "%s" "%s"'\
              % (unzip_exe, dirname(self.base_dir), preload_zip)
        p = process.ProcessOpen(cmd, stdin=None)
        stdout, stderr = p.communicate()
        retval = p.wait()
        if retval:
            raise OSError("error running '%s'" % cmd)

    #TODO: Add ver_str option (as per get_lib above) and only update
    #      the relevant stdlib.
    def remove_lang(self, lang):
        """Remove the given language from the stdlib zone."""
        log.debug("update '%s' stdlibs", lang)

        # Figure out what updates need to be done...
        cix_glob = join(self.stdlibs_dir, safe_lang_from_lang(lang)+"*.cix")
        todo = []
        for area, subpath in self.res_index:
            res = AreaResource(subpath, area)
            if fnmatch.fnmatch(res.path, cix_glob):
                todo.append(("remove", AreaResource(subpath, area)))

        # ... and then do them.
        self._handle_res_todos(lang, todo)
        self.save()

    def _update_lang_with_ver(self, lang, ver=None, progress_cb=None):
        """Import stdlib data for this lang, if necessary.
        
            "lang" is the language to update.
            "ver" (optional) is a specific version of the language,
                e.g. (5, 8).
            "progress_cb" (optional) is a callable that is called as
                follows to show the progress of the update:
                    progress_cb(<desc>, <value>)
                where <desc> is a short string describing the current step
                and <value> is an integer between 0 and 100 indicating the
                level of completeness.
        """
        log.debug("update '%s' stdlibs", lang)
        # Figure out what updates need to be done...
        if progress_cb:
            try:    progress_cb("Determining necessary updates...", 5)
            except: log.exception("error in progress_cb (ignoring)")
        if ver is not None:
            ver_str = ".".join(map(str, ver))
            cix_path = join(self.stdlibs_dir,
                            "%s-%s.cix" % (safe_lang_from_lang(lang), ver_str))
        else:
            cix_path = join(self.stdlibs_dir,
                             "%s.cix" % (safe_lang_from_lang(lang), ))

        # Need to acquire db lock, as the indexer and main thread may both be
        # calling into _update_lang_with_ver at the same time.
        self.db.acquire_lock()
        try:
            todo = []
            res = AreaResource(cix_path, "ci-pkg-dir")
            try:
                last_updated = self.res_index[res.area_path]
            except KeyError:
                todo.append(("add", res))
            else:
                mtime = os.stat(cix_path).st_mtime
                if last_updated != mtime: # epsilon? '>=' instead of '!='?
                    todo.append(("update", res))

            # ... and then do them.
            self._handle_res_todos(lang, todo, progress_cb)
            self.save()
        finally:
            self.db.release_lock()

    def update_lang(self, lang, progress_cb=None, ver=None):
        vers_and_names = self.vers_and_names_from_lang(lang)
        if ver is not None:
            ver = _ver_from_ver_str(ver)
            key = (ver, "zzz") # 'zzz' > any stdlib name (e.g., 'zzz' > 'php-4.2')
            idx = max(0, bisect.bisect_right(vers_and_names, key)-1)
            log.debug("update_lang: best stdlib fit for %s ver=%s in %s is %s",
                      lang, ver, vers_and_names, vers_and_names[idx])
            # Just update the one version for this language.
            vers_and_names = [vers_and_names[idx]]
        for ver, name in vers_and_names:
            self._update_lang_with_ver(lang, ver, progress_cb)

    def _handle_res_todos(self, lang, todo, progress_cb=None):
        if not todo:
            return
        for i, (action, res) in enumerate(todo):
            cix_path = res.path
            name = splitext(basename(cix_path))[0]
            if '-' in name:
                base, ver_str = name.split('-', 1)
                ver = _ver_from_ver_str(ver_str)
            else:
                base = name
                ver = None
            assert base == safe_lang_from_lang(lang)

            log.debug("%s %s stdlib: `%s'", action, name, cix_path)
            verb = {"add": "Adding", "remove": "Removing",
                    "update": "Updating"}[action]
            desc = "%s %s stdlib" % (verb, name)
            self.db.report_event(desc)
            if progress_cb:
                try:    progress_cb(desc, (5 + 95/len(todo)*i))
                except: log.exception("error in progress_cb (ignoring)")

            if action == "add":
                self._add_res(res, lang, name, ver)
            elif action == "remove":
                self._remove_res(res, lang, name, ver)
            elif action == "update":
                #XXX Bad for filesystem. Change this to do it
                #    more intelligently if possible.
                self._remove_res(res, lang, name, ver)
                self._add_res(res, lang, name, ver)

    def _remove_res(self, res, lang, name, ver):
        log.debug("%s stdlibs: remove %s", lang, res)
        del self.res_index[res.area_path]
        dbdir = join(self.base_dir, name)
        try:
            rmdir(dbdir)
        except OSError, ex:
            try:
                os.rename(dbdir, dbdir+".zombie")
            except OSError, ex2:
                log.error("could not remove %s stdlib database dir `%s' (%s): "
                          "couldn't even rename it to `%s.zombie' (%s): "
                          "giving up", name, dbdir, ex, name, ex2)
            else:
                log.warn("could not remove %s stdlib database dir `%s' (%s): "
                         "moved it to `%s.zombie'", name, dbdir, ex)

    def _add_res(self, res, lang, name, ver):
        log.debug("%s stdlibs: add %s", lang, res)
        cix_path = res.path
        try:
            tree = tree_from_cix_path(cix_path)
        except ET.XMLParserError, ex:
            log.warn("could not load %s stdlib from `%s' (%s): skipping",
                     name, cix_path, ex)
            return

        dbdir = join(self.base_dir, name)
        if exists(dbdir):
            log.warn("`db/stdlibs/%s' already exists and should not: "
                     "removing it", name)
            try:
                rmdir(dbdir)
            except OSError, ex:
                log.error("could not remove `%s' to create %s stdlib in "
                          "database (%s): skipping", dbdir, name)
        if not exists(dbdir):
            os.makedirs(dbdir)

        # Create 'blob_index' and 'toplevel*_index' and write out
        # '.blob' file.
        LEN_PREFIX = self.db.LEN_PREFIX
        is_hits_from_lpath_lang = lang in self.db.import_everything_langs
        blob_index = {} # {blobname -> dbfile}
        toplevelname_index = {} # {ilk -> toplevelname -> blobnames}
        toplevelprefix_index = {} # {ilk -> prefix -> toplevelnames}
        for blob in tree.findall("file/scope"):
            assert lang == blob.get("lang")
            blobname = blob.get("name")
            dbfile = self.db.bhash_from_blob_info(cix_path, lang, blobname)
            blob_index[blobname] = dbfile
            ET.ElementTree(blob).write(join(dbdir, dbfile+".blob"))
            for toplevelname, elem in blob.names.iteritems():
                if "__local__" in elem.get("attributes", "").split():
                    # this is internal to the stdlib
                    continue
                ilk = elem.get("ilk") or elem.tag
                bft = toplevelname_index.setdefault(ilk, {})
                if toplevelname not in bft:
                    bft[toplevelname] = set([blobname])
                else:
                    bft[toplevelname].add(blobname)
                prefix = toplevelname[:LEN_PREFIX]
                tfp = toplevelprefix_index.setdefault(ilk, {})
                if prefix not in tfp:
                    tfp[prefix] = set([toplevelname])
                else:
                    tfp[prefix].add(toplevelname)

        self.db.save_pickle(join(dbdir, "blob_index"), blob_index)
        self.db.save_pickle(join(dbdir, "toplevelname_index"),
                            toplevelname_index)
        self.db.save_pickle(join(dbdir, "toplevelprefix_index"),
                            toplevelprefix_index)

        mtime = os.stat(cix_path).st_mtime
        self.res_index[res.area_path] = mtime



#---- internal support stuff

def _ver_from_ver_str(ver_str):
    """Convert a version string to a version object as used internally
    for the "stdlibs" area of the database.
   
        >>> _ver_from_ver_str("5.8")
        (5, 8)
        >>> _ver_from_ver_str("1.8.2")
        (1, 8, 2)
        >>> _ver_from_ver_str("ecma")
        'ecma'
        >>> _ver_from_ver_str("ie")
        'ie'
    """
    ver = []
    for s in ver_str.split('.'):
        try:
            ver.append(int(s))
        except ValueError:
            ver.append(s)
    return tuple(ver)




