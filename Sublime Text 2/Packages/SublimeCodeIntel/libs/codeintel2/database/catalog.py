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

"""The API catalogs-zone of the codeintel database.
See the database/database.py module docstring for an overview.
"""

import sys
import os
from os.path import (join, dirname, exists, expanduser, splitext, basename,
                     split, abspath, isabs, isdir, isfile, normpath,
                     normcase)
import cPickle as pickle
import threading
import time
from hashlib import md5
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
from codeintel2.util import dedent, safe_lang_from_lang, banner, hotshotit
from codeintel2.tree import tree_from_cix_path
from codeintel2.database.util import filter_blobnames_for_prefix
from codeintel2.database.resource import AreaResource



#---- globals

log = logging.getLogger("codeintel.db")
#log.setLevel(logging.DEBUG)



#---- Database zone and lib implementations

class CatalogsZone(object):
    """Singleton zone managing the db/catalogs/... area.

    TODO: Locking: .cull_mem() and .save() will be called periodically
          on indexer thread. Anything they access needs to be guarded.
    """
    _res_index = None
    _blob_index = None
    _toplevelname_index = None
    _toplevelprefix_index = None
    
    _have_updated_at_least_once = False

    def __init__(self, mgr, catalog_dirs=None):
        self.mgr = mgr
        self.db = mgr.db

        if catalog_dirs is None:
            catalog_dirs = []
        assert isinstance(catalog_dirs, list)
        std_catalog_dir = join(dirname(dirname(abspath(__file__))), "catalogs")
        if std_catalog_dir not in catalog_dirs:
            catalog_dirs.append(std_catalog_dir)
        self.catalog_dirs = catalog_dirs

        self.base_dir = join(self.db.base_dir, "db", "catalogs")

        self._lib_cache = {} # (lang, selection_res_ids) -> CatalogLib

        self._lock = threading.RLock()
        self._blob_and_atime_from_blobname_from_lang_cache = {}
        self._dbsubpaths_and_lpaths_to_save = []

    def __repr__(self):
        return "<catalog zone>"

    def _selection_from_selector(self, selections):
        """Given a sequence of catalog selection strings (each is a
        catalog name or full path to a catalog .cix file) return a dict
        mapping:

            <normalized-selector> -> <selection-string>

        If "selections" is None, this returns None.
        """
        if selections is None:
            return None
        selection_from_selector = {}
        for selection in selections:
            if isabs(selection):
                selector = normpath(normcase(selection))
            else:
                selector = selection.lower()
            selection_from_selector[selector] = selection
        return selection_from_selector

    _res_ids_from_selector_cache = None
    def _res_ids_from_selections(self, selections):
        """Returns a tuple of the database resource ids for the given
        selections and a list of selections that didn't match any loaded
        resources.
        """
        if self._res_ids_from_selector_cache is None:
            cache = self._res_ids_from_selector_cache = {}
            for cix_area_path, res_data in self.res_index.items():
                cix_path = AreaResource(cix_area_path).path
                res_id = res_data[0]
                cache[normpath(normcase(cix_path))] = [res_id]
                name = splitext(basename(cix_path))[0].lower()
                if name not in cache:
                    cache[name] = []
                cache[name].append(res_id)
            log.debug("_res_ids_from_selector_cache: %r", cache)

        res_ids = []
        missing_selections = []
        for selector, selection \
            in self._selection_from_selector(selections).items():
            try:
                res_ids += self._res_ids_from_selector_cache[selector]
            except KeyError, ex:
                missing_selections.append(selection)
        log.debug("_res_ids_from_selections: res_ids=%r", res_ids)
        return tuple(res_ids), missing_selections

    def get_lib(self, lang, selections=None):
        """Return a CatalogLib for the given lang and selections."""
        assert not isinstance(selections, basestring),\
            "catalog lib 'selections' must be None or a sequence, not %r: %r"\
            % (type(selections), selections)
        if not self._have_updated_at_least_once:
            self.update(selections)

        if selections is not None:
            selection_res_ids, missing_selections \
                = self._res_ids_from_selections(selections)
            if missing_selections:
                self.update(missing_selections)
                selection_res_ids, missing_selections \
                    = self._res_ids_from_selections(selections)
            if missing_selections:
                log.warn("the following catalog selections didn't match "
                         "any loaded API catalog: '%s'",
                         "', '".join(missing_selections))
        else:
            selection_res_ids = None
        key = (lang, selection_res_ids)
        if key not in self._lib_cache:
            self._lib_cache[key] = CatalogLib(self, lang,
                                              selections, selection_res_ids)
        return self._lib_cache[key]

    @property
    def res_index(self):
        """Load and return the resource index (res_index)."""
        if self._res_index is None:
            idxpath = join(self.base_dir, "res_index")
            self._res_index = self.db.load_pickle(idxpath, {})
        return self._res_index

    @property
    def blob_index(self):
        """Load and return the blob index (blob_index)."""
        if self._blob_index is None:
            idxpath = join(self.base_dir, "blob_index")
            self._blob_index = self.db.load_pickle(idxpath, {})
        return self._blob_index

    @property
    def toplevelname_index(self):
        """Load and return the top-level name index (toplevelname_index)."""
        if self._toplevelname_index is None:
            idxpath = join(self.base_dir, "toplevelname_index")
            self._toplevelname_index = self.db.load_pickle(idxpath, {})
        return self._toplevelname_index

    @property
    def toplevelprefix_index(self):
        """Load and return the top-level prefix index (toplevelprefix_index)."""
        if self._toplevelprefix_index is None:
            idxpath = join(self.base_dir, "toplevelprefix_index")
            self._toplevelprefix_index = self.db.load_pickle(idxpath, {})
        return self._toplevelprefix_index

    def save(self):
        self._lock.acquire()
        try:
            for dbsubpath, lpaths in self._dbsubpaths_and_lpaths_to_save:
                self.db.save_pickle(join(self.base_dir, dbsubpath), lpaths)
            self._dbsubpaths_and_lpaths_to_save = []
        finally:
            self._lock.release()

    def cull_mem(self):
        """Drop blobs from cache that have not been accessed in over 5
        minutes.

        To attempt to keep memory consumption under control we want to
        ensure we don't keep everything cached from the db in memory
        until process completion.
        """
        #TOTEST: Does Python/Komodo actually release this memory or
        #        are we kidding ourselves?
        self._lock.acquire()
        try:
            N = 10
            if len(self._blob_and_atime_from_blobname_from_lang_cache) < N:
                # Too few blobs in memory to bother culling.
                return

            log.info("catalog: culling memory")
            now = time.time()
            for lang, blob_and_atime_from_blobname \
                in self._blob_and_atime_from_blobname_from_lang_cache.items():
                for blobname, (blob, atime) in blob_and_atime_from_blobname.items():
                    if now - atime > 300.0: # >5 minutes since last access
                        del blob_and_atime_from_blobname[blobname]
        finally:
            self._lock.release()

    def avail_catalogs(self, selections=None):
        """Generate a list of available catalogs.

            "selections" (optional) is a list of string of the same form
                as to `.get_lib()'. It is used to determine the boolean
                value of <selected> in the yielded tuples.

        Generated dicts as follows:
            {"name": <catalog-name>,    # 'name' attr of <codeintel> tag
                                        #   or file basename
             "lang": <lang>,            # 'lang' attribute of first <file> tag
             "description": <desc>,     # 'description' attr of <codeintel>
             "cix_path": <cix-path>,
             "selected": <selected>,
             "selection": <selection>,
            }
        where <selected> is boolean indicating if this catalog is
        selected according to "selections" and <selection> is the string
        in "selections" that resulted in this.
        """
        selection_from_selector = self._selection_from_selector(selections)
        for cix_path in (cix_path for d in self.catalog_dirs if exists(d)
                         for cix_path in glob(join(d, "*.cix"))):
            name = lang = description = None
            try:
                for event, elem in ET.iterparse(cix_path, events=("start",)):
                    if elem.tag == "codeintel":
                        name = elem.get("name")
                        description = elem.get("description")
                    elif elem.tag == "file":
                        lang = elem.get("lang")
                        break
            except ET.XMLParserError, ex:
                log.warn("%s: error reading catalog, skipping it (%s)",
                         cix_path, ex)
                continue
            if lang is None:
                log.warn("%s: no 'lang' attribute on catalog <file> tag, "
                         "skipping it", cix_path)
                continue
            if name is None:
                name = splitext(basename(cix_path))[0]
            norm_name = name.lower()
            norm_cix_path = normpath(normcase(cix_path))
            if selection_from_selector is None:
                selected = True
                selection = None
            else:
                selection = (selection_from_selector.get(norm_name)
                             or selection_from_selector.get(norm_cix_path))
                selected = selection is not None
            yield {"name": name,
                   "lang": lang,
                   "description": description,
                   "cix_path": cix_path,
                   "selected": selected,
                   "selection": selection}

    def update(self, selections=None, progress_cb=None):
        """Update the catalog as necessary.
        
            "selections" (optional) is a list of string of the same form
                as to `.get_lib()' -- used here to filter the catalogs
                that we consider for updating.
            "progress_cb" (optional) is a callable that is called as
                follows to show the progress of the update:
                    progress_cb(<desc>, <value>)
                where <desc> is a short string describing the current step
                and <value> is an integer between 0 and 100 indicating the
                level of completeness.
        """
        self._lock.acquire()
        try:
            self._have_updated_at_least_once = True
    
            # Figure out what updates need to be done...
            if progress_cb:
                try:    progress_cb("Determining necessary catalog updates...", 5)
                except: log.exception("error in progress_cb (ignoring)")
            res_name_from_res_path = dict(  # this is our checklist
                (p, v[2]) for p,v in self.res_index.items())
            todos = []
            log.info("updating %s: %d catalog dir(s)", self,
                     len(self.catalog_dirs))
            for catalog_info in self.avail_catalogs(selections):
                cix_path = catalog_info["cix_path"]
                res = AreaResource(cix_path)
                # check that the update-time is the mtime (i.e. up-to-date)
                try:
                    res_id, last_updated, name, res_data \
                        = self.res_index[res.area_path]
                except KeyError:
                    # add this new CIX file
                    todos.append(("add", res, catalog_info["name"]))
                else:
                    mtime = os.stat(cix_path).st_mtime
                    if last_updated != mtime: # epsilon? '>=' instead of '!='?
                        # update with newer version
                        todos.append(("update", res, catalog_info["name"]))
                    #else:
                    #    log.debug("not updating '%s' catalog: mtime is unchanged",
                    #              catalog_info["name"])
                    del res_name_from_res_path[res.area_path] # tick it off
    
            for res_area_path, res_name in res_name_from_res_path.items():
                # remove this obsolete CIX file
                try:
                    todos.append( ("remove", AreaResource(res_area_path), res_name) )
                except ValueError, ex:
                    # Skip resources in unknown areas. This is primarily to
                    # allow debugging/testing (when the set of registered
                    # path_areas may not include the set when running in
                    # Komodo.)
                    pass
    
            # Filter todos on selections, if any.
            if selections is not None:
                selection_from_selector = self._selection_from_selector(selections)
                before = todos[:]
                todos = [todo for todo in todos
                    if todo[2].lower() in selection_from_selector
                    or normpath(normcase(todo[1].path)) in selection_from_selector
                ]
    
            # ... and then do them.
            if not todos:
                return
            for i, (action, res, name) in enumerate(todos):
                log.debug("%s `%s' catalog (%s)", action, name, res)
                try:
                    if action == "add":
                        desc = "Adding '%s' API catalog" % basename(res.subpath)
                        self.db.report_event(desc)
                        if progress_cb:
                            try:    progress_cb(desc, (5 + 95/len(todos)*i))
                            except: log.exception("error in progress_cb (ignoring)")
                        self._add_res(res)
                    elif action == "remove":
                        desc = "Removing '%s' API catalog" % basename(res.subpath)
                        self.db.report_event(desc)
                        if progress_cb:
                            try:    progress_cb(desc, (5 + 95/len(todos)*i))
                            except: log.exception("error in progress_cb (ignoring)")
                        self._remove_res(res)
                    elif action == "update":
                        desc = "Updating '%s' API catalog" % basename(res.subpath)
                        self.db.report_event(desc)
                        if progress_cb:
                            try:    progress_cb(desc, (5 + 95/len(todos)*i))
                            except: log.exception("error in progress_cb (ignoring)")
                        #XXX Bad for filesystem. Change this to do it
                        #    more intelligently if possible.
                        self._remove_res(res)
                        self._add_res(res)
                except DatabaseError, ex:
                    log.warn("%s (skipping)" % ex)
    
            if progress_cb:
                try:    progress_cb("Saving catalog indeces...", 95)
                except: log.exception("error in progress_cb (ignoring)")
            self._res_ids_from_selector_cache = None # invalidate this cache
            if self._res_index is not None:
                self.db.save_pickle(
                    join(self.base_dir, "res_index"),
                    self._res_index)
            if self._blob_index is not None:
                self.db.save_pickle(
                    join(self.base_dir, "blob_index"),
                    self._blob_index)
            if self._toplevelname_index is not None:
                self.db.save_pickle(
                    join(self.base_dir, "toplevelname_index"),
                    self._toplevelname_index)
            if self._toplevelprefix_index is not None:
                self.db.save_pickle(
                    join(self.base_dir, "toplevelprefix_index"),
                    self._toplevelprefix_index)
        finally:
            self._lock.release()

    _existing_res_ids_cache = None
    _new_res_id_counter = 0
    def _new_res_id(self):
        if self._existing_res_ids_cache is None:
            self._existing_res_ids_cache \
                = dict((d[0], True) for d in self.res_index.values())
        while True:
            if self._new_res_id_counter not in self._existing_res_ids_cache:
                new_res_id = self._new_res_id_counter
                self._new_res_id_counter += 1
                self._existing_res_ids_cache[new_res_id] = True
                return new_res_id
            self._new_res_id_counter += 1

    def _remove_res(self, res):
        LEN_PREFIX = self.db.LEN_PREFIX
        res_id, last_updated, name, res_data = self.res_index[res.area_path]
        # res_data: {lang -> blobname -> ilk -> toplevelnames}
        for lang, tfifb in res_data.items():
            dbfile_and_res_id_from_blobname = self.blob_index[lang]
            for blobname, toplevelnames_from_ilk in tfifb.items():
                # Update 'blob_index' for $lang.
                dbfile, res_id = dbfile_and_res_id_from_blobname[blobname]
                del dbfile_and_res_id_from_blobname[blobname]

                # Remove ".blob" file (and associated caches).
                pattern = join(self.base_dir, safe_lang_from_lang(lang),
                               dbfile+".*")
                try:
                    for path in glob(pattern):
                        log.debug("fs-write: remove catalog %s blob file '%s'",
                                  lang, basename(path))
                        os.remove(path)
                except EnvironmentError, ex:
                    #XXX If get lots of these, then try harder. Perhaps
                    #    creating a zombies area, or creating a list of
                    #    them: self.db.add_zombie(dbpath).
                    #XXX THis isn't a correct analysis: the dbfile may just
                    #    not have been there.
                    log.warn("could not remove dbfile '%s' (%s '%s'): "
                             "leaving zombie", dbpath, lang, blobname)

                # Update 'toplevel*_index' for $lang.
                # toplevelname_index:   {lang -> ilk -> toplevelname -> res_id -> blobnames}
                # toplevelprefix_index: {lang -> ilk -> prefix -> res_id -> toplevelnames}
                for ilk, toplevelnames in toplevelnames_from_ilk.iteritems():
                    try:
                        bfrft = self.toplevelname_index[lang][ilk]
                        for toplevelname in toplevelnames:
                            del bfrft[toplevelname][res_id]
                            if not bfrft[toplevelname]:
                                del bfrft[toplevelname]
                    except KeyError, ex:
                        self.db.corruption("CatalogsZone._remove_res",
                            "error removing top-level names of ilk '%s' for "
                                "'%s' resource from toplevelname_index: %s"
                                % (ilk, basename(res.path), ex),
                            "ignore")

                    try:
                        tfrfp = self.toplevelprefix_index[lang][ilk]
                        for toplevelname in toplevelnames:
                            prefix = toplevelname[:LEN_PREFIX]
                            del tfrfp[prefix][res_id]
                            if not tfrfp[prefix]:
                                del tfrfp[prefix]
                    except KeyError, ex:
                        self.db.corruption("CatalogsZone._remove_res",
                            "error removing top-level name of ilk '%s' for "
                                "'%s' resource from toplevelprefix_index: %s"
                                % (ilk, basename(res.path), ex),
                            "ignore")

        del self.res_index[res.area_path]

    def _add_res(self, res):
        cix_path = res.path
        try:
            tree = tree_from_cix_path(cix_path)
        except ET.XMLParserError, ex:
            log.warn("could not load `%s' into catalog (skipping): %s",
                     cix_path, ex)
            return

        LEN_PREFIX = self.db.LEN_PREFIX
        res_id = self._new_res_id()
        res_data = {}   # {lang -> blobname -> ilk -> toplevelnames}
        name = tree.get("name") or splitext(basename(cix_path))[0]
        for blob in tree.findall("file/scope"):
            lang, blobname = blob.get("lang"), blob.get("name")
            if not lang:
                raise DatabaseError("add `%s': no 'lang' attr on %r"
                                    % (res, blob))

            # Create 'res_data'.
            tfifb = res_data.setdefault(lang, {})
            toplevelnames_from_ilk = tfifb.setdefault(blobname, {})
            if lang in self.db.import_everything_langs:
                for toplevelname, elem in blob.names.iteritems():
                    ilk = elem.get("ilk") or elem.tag
                    if ilk not in toplevelnames_from_ilk:
                        toplevelnames_from_ilk[ilk] = set([toplevelname])
                    else:
                        toplevelnames_from_ilk[ilk].add(toplevelname)

            # Update 'toplevel*_index'.
            # toplevelname_index:   {lang -> ilk -> toplevelname -> res_id -> blobnames}
            # toplevelprefix_index: {lang -> ilk -> prefix -> res_id -> toplevelnames}
            bfrftfi = self.toplevelname_index.setdefault(lang, {})
            tfrfpfi = self.toplevelprefix_index.setdefault(lang, {})
            for ilk, toplevelnames in toplevelnames_from_ilk.iteritems():
                bfrft = bfrftfi.setdefault(ilk, {})
                tfrfp = tfrfpfi.setdefault(ilk, {})
                for toplevelname in toplevelnames:
                    bfr = bfrft.setdefault(toplevelname, {})
                    if res_id not in bfr:
                        bfr[res_id] = set([blobname])
                    else:
                        bfr[res_id].add(blobname)
                    prefix = toplevelname[:LEN_PREFIX]
                    tfr = tfrfp.setdefault(prefix, {})
                    if res_id not in tfr:
                        tfr[res_id] = set([toplevelname])
                    else:
                        tfr[res_id].add(toplevelname)

            # Update 'blob_index'.
            dbfile_and_res_id_from_blobname \
                = self.blob_index.setdefault(lang, {})
            assert blobname not in dbfile_and_res_id_from_blobname, \
                   ("codeintel: %s %r blob in `%s' collides "
                    "with existing %s %r blob (from res_id %r) in catalog: "
                    "(XXX haven't decided how to deal with that yet)"
                    % (lang, blobname, cix_path, lang, blobname,
                       dbfile_and_res_id_from_blobname[blobname][1]))
            dbfile = self.db.bhash_from_blob_info(cix_path, lang, blobname)
            dbfile_and_res_id_from_blobname[blobname] = (dbfile, res_id)

            # Write out '.blob' file.
            dbdir = join(self.base_dir, safe_lang_from_lang(lang))
            if not exists(dbdir):
                log.debug("fs-write: mkdir '%s'", dbdir)
                os.makedirs(dbdir)
            log.debug("fs-write: catalog %s blob '%s'", lang, dbfile)
            ET.ElementTree(blob).write(join(dbdir, dbfile+".blob"))

        # Update 'res_index'.
        last_updated = os.stat(cix_path).st_mtime
        self.res_index[res.area_path] \
            = (res_id, last_updated, name, res_data)

    def res_id_from_lang_and_blobname(self, lang, blobname):
        try:
            dbfile, res_id = self.blob_index[lang][blobname]
        except KeyError:
            return None
        else:
            return res_id

    def get_blob(self, lang, blobname, look_in_cache_only=False):
        try:
            dbfile, res_id = self.blob_index[lang][blobname]
        except KeyError:
            return None

        # If index path is in the cache: return it, update its atime.
        now = time.time()
        blob_and_atime_from_blobname \
            = self._blob_and_atime_from_blobname_from_lang_cache.setdefault(lang, {})
        if blobname in blob_and_atime_from_blobname:
            log.debug("cache-read: load %s blob `%s'", lang, blobname)
            blob, atime = blob_and_atime_from_blobname[blobname]
            blob_and_atime_from_blobname[blobname] = (blob, now)
            return blob

        # Need to load and cache it.
        if look_in_cache_only:
            return None
        dbsubpath = join(self.base_dir, safe_lang_from_lang(lang), dbfile)
        blob = self.db.load_blob(dbsubpath)
        blob_and_atime_from_blobname[blobname] = (blob, now)
        return blob

    def lpaths_from_lang_and_blobname(self, lang, blobname):
        """Get lpaths for the named blob.

        We get it from the blob's "lpaths" cache key (calculating that
        if necessary).
        """
        blob = self.get_blob(lang, blobname, look_in_cache_only=True)
        if blob is not None: 
            if "lpaths" in blob.cache:
                return blob.cache["lpaths"]
        else:
            blob = self.get_blob(lang, blobname)
            if blob is None:
                raise NotFoundInDatabase("%s '%s' blob not found in catalogs"
                                         % (lang, blobname))
            if "lpaths" in blob.cache:
                return blob.cache["lpaths"]

        # Need to calculate lpaths from 'blob'.
        log.debug("calc symbol info for %s '%s' catalog blob", lang, blobname)
        langintel = self.mgr.langintel_from_lang(lang)
        lpaths = langintel.lpaths_from_blob(blob)

        # Update cache and queue this up to be saved to disk (by .save()).
        blob.cache["lpaths"] = lpaths
        dbfile, res_id = self.blob_index[lang][blobname]
        self._lock.acquire()
        try:
            self._dbsubpaths_and_lpaths_to_save.append(
                (join(safe_lang_from_lang(lang), dbfile+".lpaths"), lpaths)
            )
        finally:
            self._lock.release()

        return lpaths


class CatalogLib(object):
    """A light lang-specific and selection-filtered view on the whole
    CatalogsZone.
    """
    name = "cataloglib"

    def __init__(self, catalogs_zone, lang,
                 selections=None, selection_res_ids=None):
        self.catalogs_zone = catalogs_zone
        self.lang = lang
        self.selections = selections
        if selection_res_ids is None:
            self.selection_res_id_set = None
        else:
            self.selection_res_id_set = set(selection_res_ids)
        self._import_handler = None
        self._blob_imports_from_prefix_cache = {}
        
    _repr_cache = None
    def __repr__(self):
        if self._repr_cache is None:
            # Include the base names of the selected resources in the name.
            if self.selection_res_id_set is None:
                selection_names = ['(all)']
            else:
                selection_names = []
                for s in self.selections:
                    if isabs(s):
                        selection_names.append(splitext(basename(s))[0])
                    else:
                        selection_names.append(s)
            self._repr_cache = "<%s cataloglib: %s>"\
                               % (self.lang, ', '.join(selection_names))
        return self._repr_cache

    @property
    def import_handler(self):
        if self._import_handler is None:
            self._import_handler \
                = self.catalogs_zone.mgr.citadel.import_handler_from_lang(self.lang)
        return self._import_handler

    def has_blob(self, blobname):
        res_id = self.catalogs_zone.res_id_from_lang_and_blobname(self.lang,
                                                                  blobname)
        if res_id is None:
            return False
        if self.selection_res_id_set is None:
            return True
        return res_id in self.selection_res_id_set

    def get_blob(self, blobname):
        if not self.has_blob(blobname): # knows how to filter on selections
            return None
        return self.catalogs_zone.get_blob(self.lang, blobname)
    
    def get_blob_imports(self, prefix):
        """Return the set of imports under the given prefix.

            "prefix" is a tuple of import name parts. E.g. ("xml", "sax")
                for "import xml.sax." in Python. Or ("XML", "Parser") for
                "use XML::Parser::" in Perl.

        See description in database.py docstring for details.
        """
        # This code works fine if prefix is the empty tuple.
        if prefix not in self._blob_imports_from_prefix_cache:
            try:
                dbfile_and_res_id_from_blobname \
                    = self.catalogs_zone.blob_index[self.lang]
            except KeyError:
                return set()
            
            if self.selection_res_id_set is None:
                matches = filter_blobnames_for_prefix(
                    dbfile_and_res_id_from_blobname,
                    prefix,
                    self.import_handler.sep)
            else:
                matches = filter_blobnames_for_prefix(
                    (bn
                     for bn, (f, res_id) in dbfile_and_res_id_from_blobname.items()
                     if res_id in self.selection_res_id_set),
                    prefix,
                    self.import_handler.sep)
            self._blob_imports_from_prefix_cache[prefix] = matches
        return self._blob_imports_from_prefix_cache[prefix]

    def _blobnames_from_toplevelname(self, toplevelname, ilk=None):
        """Yield all blobnames in the currently selected catalogs
        with the given toplevelname.
        
        If "ilk" is given then only symbols of that ilk will be considered.
        """
        # toplevelname_index: {lang -> ilk -> toplevelname -> res_id -> blobnames}
        if self.lang in self.catalogs_zone.toplevelname_index:
            for i, potential_bfrft \
                in self.catalogs_zone.toplevelname_index[self.lang].iteritems():
                if ilk is not None and i != ilk:
                    continue
                if toplevelname not in potential_bfrft:
                    continue
                potential_bfr = potential_bfrft[toplevelname]
                if self.selection_res_id_set is None:
                    for blobnames in potential_bfr.itervalues():
                        for blobname in blobnames:
                            yield blobname
                else:
                    for res_id, blobnames in potential_bfr.iteritems():
                        if res_id not in self.selection_res_id_set:
                            continue
                        for blobname in blobnames:
                            yield blobname

    def hits_from_lpath(self, lpath, ctlr=None, curr_buf=None):
        assert isinstance(lpath, tuple)  # common mistake to pass in a string
        
        hits = []
        for blobname in self._blobnames_from_toplevelname(lpath[0]):
            lpaths = self.catalogs_zone.lpaths_from_lang_and_blobname(
                        self.lang, blobname)
            if lpath not in lpaths: continue
            blob = self.catalogs_zone.get_blob(self.lang, blobname)
            #TODO: Convert lpath's in tree-evalrs to tuples instead of lists.
            elem = _elem_from_scoperef( (blob, list(lpath)) )
            hits.append( (elem, (blob, list(lpath[:-1]))) )

        return hits

    def toplevel_cplns(self, prefix=None, ilk=None, ctlr=None):
        """Return completion info for all top-level names matching the
        given prefix and ilk in all selected blobs in this lib.
        
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
            # Use 'toplevelname_index':
            #   {lang -> ilk -> toplevelname -> res_id -> blobnames}
            toplevelname_index = self.catalogs_zone.toplevelname_index
            if self.lang in toplevelname_index:
                if ilk is not None:
                    try:
                        bfrft = toplevelname_index[self.lang][ilk]
                    except KeyError:
                        pass
                    else:
                        if self.selection_res_id_set is None:
                            cplns += [(ilk, t) for t in bfrft]
                        else:
                            cplns += [(ilk, t) for t, bfr in bfrft.iteritems()
                                      if self.selection_res_id_set.intersection(bfr)]
                elif self.selection_res_id_set is None:
                    for i, bfrft in toplevelname_index[self.lang].iteritems():
                        cplns += [(i, t) for t in bfrft]
                else: # ilk=None, have a selection set
                    for i, bfrft in toplevelname_index[self.lang].iteritems():
                        cplns += [(i, t) for t, bfr in bfrft.iteritems()
                                  if self.selection_res_id_set.intersection(bfr)]
        else:
            # Use 'toplevelprefix_index':
            #   {lang -> ilk -> prefix -> res_id -> toplevelnames}
            toplevelprefix_index = self.catalogs_zone.toplevelprefix_index
            if self.lang in toplevelprefix_index:
                if ilk is not None:
                    try:
                        tfr = toplevelprefix_index[self.lang][ilk][prefix]
                    except KeyError:
                        pass
                    else:
                        if self.selection_res_id_set is None:
                            cplns += [(ilk, t)
                                      for toplevelnames in tfr.itervalues()
                                      for t in toplevelnames]
                        else:
                            cplns += [(ilk, t)
                                      for r in self.selection_res_id_set.intersection(tfr)
                                      for t in tfr[r]]
                elif self.selection_res_id_set is None:
                    for i, tfrfp in toplevelprefix_index[self.lang].iteritems():
                        if prefix not in tfrfp:
                            continue
                        cplns += [(i, t)
                                  for toplevelnames in tfrfp[prefix].itervalues()
                                  for t in toplevelnames]
                else: # ilk=None, have a selection set
                    for i, tfrfp in toplevelprefix_index[self.lang].iteritems():
                        if prefix not in tfrfp:
                            continue
                        tfr = tfrfp[prefix]
                        cplns += [(i, t)
                                  for r in self.selection_res_id_set.intersection(tfr)
                                  for t in tfr[r]]
        return cplns



#---- internal support routines

def _elem_from_scoperef(scoperef):
    """A scoperef is (<blob>, <lpath>). Return the actual elem in
    the <blob> ciElementTree being referred to.
    """
    elem = scoperef[0]
    for lname in scoperef[1]:
        elem = elem.names[lname]
    return elem


