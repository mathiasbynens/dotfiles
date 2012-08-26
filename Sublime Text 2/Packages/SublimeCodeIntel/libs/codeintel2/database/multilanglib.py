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

"""The multilang-zone of the codeintel database.
See the database/database.py module docstring for an overview.
"""

import sys
import os
from os.path import (join, dirname, exists, expanduser, splitext, basename,
                     split, abspath, isabs, isdir, isfile, normpath)
from glob import glob
from pprint import pprint, pformat
import time
import logging
from cStringIO import StringIO
import copy

import ciElementTree as ET
from codeintel2.common import *
from codeintel2.database.langlib import LangZone
from codeintel2 import util



#---- globals

log = logging.getLogger("codeintel.db")
#log.setLevel(logging.DEBUG)



#---- Database zone and lib implementations

class MultiLangTopLevelNameIndex(object):
    """A wrapper around the plain-dictionary toplevelname_index for a
    MultiLangZone dir to provide better performance for continual updating
    and some simpler access.

        {lang -> ilk -> toplevelname -> blobnames}

    # Problem

    A 'toplevelname_index' is a merge of
        {lang -> blobname -> ilk -> toplevelnames}
    data for all resources in its dir.  As those resources are
    continually re-scanned (e.g. as a file is edited in Komodo), it
    would be too expensive to update this index everytime.

    # Solution

    Keep a list of "recent updates" and only merge them into the main
    data when that buf hasn't been updated in "a while" and when needed
    for saving the index. Note: Buffer *removals* are not put on-deck,
    but removed immediately.

    # .get_blobnames(lang, ..., ilk=None)
    
    Originally the toplevelname_index stored
        {lang -> toplevelname -> blobnames}
    The per-"ilk" level was added afterwards to support occassional ilk
    filtering for PHP (and possible eventually other langs).
    
    .get_blobnames() still behaves like a {lang -> toplevelname -> blobnames}
    mapping, but it provides an optional "ilk" keyword arg to limit the
    results to that ilk.

    # Notes on locking

    This class does not guard its datastructures with locking. It is up
    to the MultiLangZone using this to guard against simultaneous access
    on separate threads.
    """
    def __init__(self, data=None, timeout=90):
        # toplevelname_index data: {lang -> ilk -> toplevelname -> blobnames}
        if data is None:
            self._data = {}
        else:
            self._data = data

        # Time (in seconds) to hold a change "on deck".
        # Timed-out changes are merged on .get() and .update().
        self.timeout = timeout
        self._on_deck = {
            # basename                           # the basename of the buf path
            #   -> [timestamp,                   # time of the last update
            #       # The dict in res_index, a.k.a. 'res_data'
            #       {lang -> blobname -> ilk -> toplevelnames},
            #       # Lazily generated pivot, a.k.a. 'res_data_pivot'
            #       {lang -> ilk -> toplevelname -> blobnames}
            #      ]
        }

    def __repr__(self):
        return "<MultiLangTopLevelNameIndex: %d update(s) on-deck>"\
               % len(self._on_deck)

    def merge(self):
        """Merge all on-deck changes with `self.data'."""
        for base, (timestamp, res_data,
                   res_data_pivot) in self._on_deck.items():
            if res_data_pivot is None:
                res_data_pivot = self._pivot_res_data(res_data)
            # res_data_pivot: {lang -> ilk -> toplevelname -> blobnames}
            # "bftfi" means blobnames_from_toplevelname_from_ilk
            for lang, bftfi in res_data_pivot.iteritems():
                data_bftfi = self._data.setdefault(lang, {})
                for ilk, bft in bftfi.iteritems():
                    data_bft = data_bftfi.setdefault(ilk, {})
                    for toplevelname, blobnames in bft.iteritems():
                        if toplevelname not in data_bft:
                            data_bft[toplevelname] = blobnames
                        else:
                            data_bft[toplevelname].update(blobnames)
            del self._on_deck[base]

    def merge_expired(self, now):
        """Merge expired on-deck changes with `self.data'."""
        for base, (timestamp, res_data,
                   res_data_pivot) in self._on_deck.items():
            if now - timestamp < self.timeout:
                continue

            if res_data_pivot is None:
                res_data_pivot = self._pivot_res_data(res_data)
            # res_data_pivot: {lang -> ilk -> toplevelname -> blobnames}
            # "bftfi" means blobnames_from_toplevelname_from_ilk
            for lang, bftfi in res_data_pivot.iteritems():
                data_bftfi = self._data.setdefault(lang, {})
                for ilk, bft in bftfi.iteritems():
                    data_bft = data_bftfi.setdefault(ilk, {})
                    for toplevelname, blobnames in bft.iteritems():
                        if toplevelname not in data_bft:
                            data_bft[toplevelname] = blobnames
                        else:
                            data_bft[toplevelname].update(blobnames)
            del self._on_deck[base]

    @property
    def data(self):
        self.merge()
        return self._data

    def update(self, base, old_res_data, new_res_data):
        now = time.time()
        self.remove(base, old_res_data)
        self._on_deck[base] = [now, new_res_data, None]
        self.merge_expired(now)

    def remove(self, base, old_res_data):
        if base in self._on_deck:
            del self._on_deck[base]
        else:
            # Remove old refs from current data.
            # old_res_data: {lang -> blobname -> ilk -> toplevelnames}
            # self._data:   {lang -> ilk -> toplevelname -> blobnames}
            for lang, tfifb in old_res_data.iteritems():
                if lang not in self._data:
                    continue
                data_bftfi = self._data[lang]
                for blobname, tfi in tfifb.iteritems():
                    for ilk, toplevelnames in tfi.iteritems():
                        for toplevelname in toplevelnames:
                            try:
                                data_bftfi[ilk][toplevelname].remove(blobname)
                            except KeyError:
                                pass # ignore this for now, might indicate corruption
                            else:
                                if not data_bftfi[ilk][toplevelname]:
                                    del data_bftfi[ilk][toplevelname]
                        if not data_bftfi.get(ilk):
                            del data_bftfi[ilk]
                if not self._data[lang]:
                    del self._data[lang]

    def _pivot_res_data(self, res_data):
        # res_data:       {lang -> blobname -> ilk -> toplevelnames}
        # res_data_pivot: {lang -> ilk -> toplevelname -> blobnames}
        res_data_pivot = dict(
            (lang, {}) for lang in res_data
        )
        for lang, tfifb in res_data.iteritems():
            for blobname, toplevelnames_from_ilk in tfifb.iteritems():
                for ilk, toplevelnames in toplevelnames_from_ilk.iteritems():
                    pivot_bft = res_data_pivot[lang].setdefault(ilk, {})
                    for toplevelname in toplevelnames:
                        if toplevelname not in pivot_bft:
                            pivot_bft[toplevelname] = set([blobname])
                        else:
                            pivot_bft[toplevelname].add(blobname)
        return res_data_pivot

    def toplevel_cplns(self, lang, prefix=None, ilk=None):
        """Return completion info for all top-level names matching the
        given prefix and ilk.

            "prefix" is a 3-character prefix with which to filter top-level
                names. If None (or not specified), results are not filtered
                based on the prefix.
            "ilk" is a symbol type (e.g. "class", "variable", "function")
                with which to filter results. If None (or not specified),
                results of any ilk are returned.

        Returns a list of 2-tuples: (<ilk>, <name>).
        """
        self.merge_expired(time.time())

        # Need to check merged and on-deck items:
        cplns = []

        # ...on-deck items
        for base, (timestamp, res_data,
                   res_data_pivot) in self._on_deck.items():
            if lang not in res_data:
                continue
            if res_data_pivot is None:
                res_data_pivot = self._on_deck[base][2] \
                    = self._pivot_res_data(res_data)
            # res_data_pivot: {lang -> ilk -> toplevelname -> blobnames}
            bftfi = res_data_pivot[lang]
            if ilk is None:
                for i, bft in bftfi.iteritems():
                    cplns += [(i, toplevelname) for toplevelname in bft]
            elif ilk in bftfi:
                cplns += [(ilk, toplevelname) for toplevelname in bftfi[ilk]]

        # ...merged data
        # self._data: {lang -> ilk -> toplevelname -> blobnames}
        if lang in self._data:
            bftfi = self._data[lang]
            if ilk is None:
                for i, bft in bftfi.iteritems():
                    cplns += [(i, toplevelname) for toplevelname in bft]
            elif ilk in bftfi:
                cplns += [(ilk, toplevelname) for toplevelname in bftfi[ilk]]


        # Naive implementation: Instead of maintaining a separate
        # 'toplevelprefix_index' (as we do for StdLibsZone and CatalogsZone)
        # for now we'll just gather all results and filter on the prefix
        # here. Only if this proves to be a perf issue will we add the
        # complexity of another index:
        #   {lang -> ilk -> prefix -> toplevelnames}
        if prefix is not None:
            cplns = [(i, t) for i, t in cplns if t.startswith(prefix)]

        return cplns


    #TODO: Change this API to just have the empty list as a default.
    #      No point in the 'default' arg.
    def get_blobnames(self, lang, toplevelname, default=None, ilk=None):
        """Return the blobnames of the given lang defining the given
        toplevelname.

        If "ilk" is given then only symbols of that ilk will be considered.
        If not match is found the "default" is returned.
        """
        self.merge_expired(time.time())

        blobnames = set()
        # First check on-deck items.
        for base, (timestamp, res_data,
                   res_data_pivot) in self._on_deck.items():
            if lang not in res_data:
                continue
            if res_data_pivot is None:
                res_data_pivot = self._on_deck[base][2] \
                    = self._pivot_res_data(res_data)
            # res_data_pivot: {lang -> ilk -> toplevelname -> blobnames}
            bftfi = res_data_pivot[lang]
            if ilk is None:
                for bft in bftfi.itervalues():
                    if toplevelname in bft:
                        blobnames.update(bft[toplevelname])
            elif ilk in bftfi:
                if toplevelname in bftfi[ilk]:
                    blobnames.update(bftfi[ilk][toplevelname])

        #TODO: Put lookup in merged data ahead of lookup in on-deck -- so
        #      we don't do on-deck work if not necessary.
        # Then, fallback to already merged data.
        # self._data: {lang -> ilk -> toplevelname -> blobnames}
        if lang in self._data:
            bftfi = self._data[lang]
            if ilk is None:
                for bft in bftfi.itervalues():
                    if toplevelname in bft:
                        blobnames.update(bft[toplevelname])
            elif ilk in bftfi:
                if toplevelname in bftfi[ilk]:
                    blobnames.update(bftfi[ilk][toplevelname])

        if blobnames:
            return blobnames
        return default


class MultiLangZone(LangZone):
    toplevelname_index_class = MultiLangTopLevelNameIndex

    def get_lib(self, name, dirs, sublang):
        assert isinstance(dirs, (tuple, list))
        assert sublang is not None, "must specify '%s' sublang" % self.lang

        canon_dirs = tuple(abspath(normpath(expanduser(d))) for d in dirs)
        key = (canon_dirs, sublang)
        if key in self._dirslib_cache:
            return self._dirslib_cache[key]

        langdirslib = MultiLangDirsLib(self, self._lock, self.lang,
                                        name, canon_dirs, sublang)
        
        N = 10
        while len(self._ordered_dirslib_cache_keys) >= N:
            cache_key = self._ordered_dirslib_cache_keys.pop()
            del self._dirslib_cache[cache_key]
        self._dirslib_cache[key] = langdirslib
        self._ordered_dirslib_cache_keys.insert(0, key)

        return langdirslib

    def dfb_from_dir(self, dir, sublang, default=None):
        """Get the {blobname -> dbfile} mapping index for the given dir
        and lang.
        
        'dfb' stands for 'dbfile_from_blobname'.
        This must be called with the lock held.
        """
        blob_index = self.load_index(dir, "blob_index", default=default)
        try:
            return blob_index[sublang]
        except KeyError, ex:
            if default is not None:
                return default
            raise

    def get_buf_data(self, buf):
        #TODO Canonicalize path (or assert that it is canonicalized)
        #     Should have a Resource object that we pass around that
        #     handles all of this.
        self._acquire_lock()
        try:
            dir, base = split(buf.path)
            res_index = self.load_index(dir, "res_index", {})
            if base not in res_index:
                raise NotFoundInDatabase("%s buffer '%s' not found in database"
                                         % (buf.lang, buf.path))
            scan_time, scan_error, res_data = res_index[base]

            try:
                blob_index = self.load_index(dir, "blob_index")
            except EnvironmentError, ex:
                self.db.corruption("MultiLangZone.get_buf_data",
                    "could not find 'blob_index' index: %s" % ex,
                    "recover")
                raise NotFoundInDatabase("%s buffer '%s' not found in database"
                                         % (buf.lang, buf.path))

            dhash = self.dhash_from_dir(dir)
            blob_from_lang = {}
            # res_data: {lang -> blobname -> ilk -> toplevelnames}
            for lang, blobname in (
                 (lang, tfifb.keys()[0]) # only one blob per lang in a resource
                 for lang, tfifb in res_data.items()
                ):
                dbsubpath = join(dhash, blob_index[lang][blobname])
                try:
                    blob = self.load_blob(dbsubpath)
                except ET.XMLParserError, ex:
                    self.db.corruption("MultiLangZone.get_buf_data",
                        "could not parse dbfile for '%s' blob: %s"\
                            % (blobname, ex),
                        "recover")
                    self.remove_buf_data(buf)
                    raise NotFoundInDatabase(
                        "`%s' buffer %s `%s' blob was corrupted in database"
                        % (buf.path, lang, blobname))
                except EnvironmentError, ex:
                    self.db.corruption("MultiLangZone.get_buf_data",
                        "could not read dbfile for '%s' blob: %s"\
                            % (blobname, ex),
                        "recover")
                    self.remove_buf_data(buf)
                    raise NotFoundInDatabase(
                        "`%s' buffer %s `%s' blob not found in database"
                        % (buf.path, lang, blobname))
                assert blob.get("lang") == lang
                blob_from_lang[lang] = blob

            return scan_time, scan_error, blob_from_lang
        finally:
            self._release_lock()

    def remove_path(self, path):
        """Remove the given resource from the database."""
        #TODO Canonicalize path (or assert that it is canonicalized)
        #     Should have a Resource object that we pass around that
        #     handles all of this.
        self._acquire_lock()
        try:
            dir, base = split(path)

            res_index = self.load_index(dir, "res_index", {})
            try:
                scan_time, scan_error, res_data = res_index[base]
            except KeyError:
                # This resource isn't loaded in the db. Nothing to remove.
                return

            try:
                blob_index = self.load_index(dir, "blob_index")
            except EnvironmentError, ex:
                self.db.corruption("MultiLangZone.remove_path",
                    "could not read blob_index for '%s' dir: %s" % (dir, ex),
                    "recover")
                blob_index = {}

            is_hits_from_lpath_lang = self.lang in self.db.import_everything_langs
            if is_hits_from_lpath_lang:
                try:
                    toplevelname_index = self.load_index(dir, "toplevelname_index")
                except EnvironmentError, ex:
                    self.db.corruption("MultiLangZone.remove_path",
                        "could not read toplevelname_index for '%s' dir: %s"
                            % (dir, ex),
                        "recover")
                    toplevelname_index = self.toplevelname_index_class()

            dhash = self.dhash_from_dir(dir)
            del res_index[base]
            # res_data: {lang -> blobname -> ilk -> toplevelnames}
            for lang, blobname in (
                 (lang, tfifb.keys()[0]) # only one blob per lang in a resource
                 for lang, tfifb in res_data.items()
                ):
                try:
                    dbfile = blob_index[lang][blobname]
                except KeyError:
                    blob_index_path = join(dhash, "blob_index")
                    self.db.corruption("MultiLangZone.remove_path",
                        "%s '%s' blob not in '%s'" \
                            % (lang, blobname, blob_index_path),
                        "ignore")
                    continue
                del blob_index[lang][blobname]
                for path in glob(join(self.base_dir, dhash, dbfile+".*")):
                    log.debug("fs-write: remove %s|%s blob file '%s/%s'",
                              self.lang, lang, dhash, basename(path))
                    os.remove(path)
            if is_hits_from_lpath_lang:
                toplevelname_index.remove(base, res_data)

            self.changed_index(dir, "res_index")
            self.changed_index(dir, "blob_index")
            if is_hits_from_lpath_lang:
                self.changed_index(dir, "toplevelname_index")
        finally:
            self._release_lock()
        #XXX Database.clean() should remove dirs that have no
        #    dbfile_from_blobname entries.

    def remove_buf_data(self, buf):
        """Remove the given resource from the database."""
        self.remove_path(buf.path)

    def update_buf_data(self, buf, scan_tree, scan_time, scan_error,
                        skip_scan_time_check=False):
        """Update this MultiLangZone with the buffer data.

        @param buf {CitadelBuffer} the buffer whose data is being added
            to the database.
        @param scan_tree {ciElementTree} the CIX scan data. Might be None
            if there was an early scanning failure.
        @param scan_time {timestamp} the time of the scan, typically the
            mtime of the file
        @param scan_error {str} an error string if scanning failed, or
            None if it was succesful.
        @param skip_scan_time_check {boolean} (default False) is a
            boolean indicating if the buffer data should be updated even
            if `scan_time` is <= that in the database.
        """
        self._acquire_lock()
        try:
            #TODO: Canonicalize path (or assert that it is canonicalized)
            dir, base = split(buf.path)

            # Get the current data, if any.
            res_index = self.load_index(dir, "res_index", {})
            res_index_has_changed = False
            blob_index = self.load_index(dir, "blob_index", {})
            blob_index_has_changed = False
            is_hits_from_lpath_lang = self.lang in self.db.import_everything_langs
            if is_hits_from_lpath_lang:
                #TODO: Not sure {} for a default is correct here.
                toplevelname_index = self.load_index(dir, "toplevelname_index", {})
                toplevelname_index_has_changed = False
            try:
                (old_scan_time, old_scan_error, old_res_data) = res_index[base]
            except KeyError:    # adding a new entry
                (old_scan_time, old_scan_error, old_res_data) = None, None, {}
            else:               # updating an existing entry
                if not skip_scan_time_check and scan_time is not None \
                   and scan_time <= old_scan_time:
                    log.debug("skipping db update for '%s': %s < %s and "
                              "no 'skip_scan_time_check' option",
                              base, scan_time, old_scan_time)
                    return

            log.debug("update from %s buf '%s'", buf.lang, buf.path)

            # Parse the tree and get the list of blobnames.
            # res_data: {lang -> blobname -> ilk -> toplevelnames}
            new_res_data = {}
            new_blob_from_lang_and_blobname = {}
            if scan_tree:
                for blob in scan_tree[0]:
                    lang = blob.get("lang")
                    blobname = blob.get("name")
                    new_blob_from_lang_and_blobname[(lang, blobname)] = blob
                    tfifb = new_res_data.setdefault(lang, {})
                    toplevelnames_from_ilk = tfifb.setdefault(blobname, {})
                    for toplevelname, elem in blob.names.iteritems():
                        ilk = elem.get("ilk") or elem.tag
                        if ilk not in toplevelnames_from_ilk:
                            toplevelnames_from_ilk[ilk] = set([toplevelname])
                        else:
                            toplevelnames_from_ilk[ilk].add(toplevelname)
                        # For PHP namespaces, we also want to add all namespace
                        # child items, as this will make it easy for tree_php
                        # to lookup a Fully Qualified Namespace (FQN).
                        if ilk == "namespace" and lang == "PHP":
                            for childname, childelem in elem.names.iteritems():
                                child_ilk = childelem.get("ilk") or childelem.tag
                                child_fqn = "%s\\%s" % (toplevelname, childname)
                                if child_ilk not in toplevelnames_from_ilk:
                                    toplevelnames_from_ilk[child_ilk] = set([child_fqn])
                                else:
                                    toplevelnames_from_ilk[child_ilk].add(child_fqn)

            # Determine necessary changes to res_index.
            if scan_error:
                if (scan_time != old_scan_time
                    or scan_error != old_scan_error):
                    res_index[base] = (scan_time, scan_error,
                                       old_res_data)
                    res_index_has_changed = True

            else:
                # Only consider new blobs if there wasn't a scan error.
                # I.e., we want to preserve the last good scan info.

                if (scan_time != old_scan_time
                    or scan_error != old_scan_error
                    or new_res_data != old_res_data):
                    res_index[base] = (scan_time, scan_error,
                                       new_res_data)
                    res_index_has_changed = True

                if is_hits_from_lpath_lang:
                    if new_res_data != old_res_data:
                        toplevelname_index.update(base,
                            old_res_data, new_res_data)
                        toplevelname_index_has_changed = True

                # Determine necessary changes to dbfile_from_blobname index
                # and the dbfiles and then make them.
                dbfile_changes = []
                for (lang, blobname), blob \
                        in new_blob_from_lang_and_blobname.items():
                    try:
                        old_res_data[lang][blobname]
                    except KeyError:
                        dbfile_changes.append(("add", lang, blobname, blob))
                    else:
                        dbfile_changes.append(("update", lang, blobname, blob))

                for lang, old_tfifb in old_res_data.items():
                    for blobname in old_tfifb:
                        try:
                            new_res_data[lang][blobname]
                        except KeyError:
                            dbfile_changes.append(("remove", lang, blobname, None))

                dhash = self.dhash_from_dir(dir)
                for action, lang, blobname, blob in dbfile_changes:
                    if action == "add":
                        dbfile = self.db.bhash_from_blob_info(
                                    buf.path, lang, blobname)
                        blob_index.setdefault(lang, {})[blobname] = dbfile
                        blob_index_has_changed = True
                        dbdir = join(self.base_dir, dhash)
                        if not exists(dbdir):
                            self._mk_dbdir(dbdir, dir)
                        #XXX What to do on write failure?
                        log.debug("fs-write: %s|%s blob '%s/%s'",
                                  self.lang, lang, dhash, dbfile)
                        if blob.get("src") is None:
                            blob.set("src", buf.path)   # for defns_from_pos() support
                        ET.ElementTree(blob).write(join(dbdir, dbfile+".blob"))
                    elif action == "remove":
                        dbfile = blob_index[lang][blobname]
                        del blob_index[lang][blobname]
                        blob_index_has_changed = True
                        #XXX What to do on removal failure?
                        log.debug("fs-write: remove %s|%s blob '%s/%s'",
                                  self.lang, lang, dhash, dbfile)
                        try:
                            os.remove(join(self.base_dir, dhash, dbfile+".blob"))
                        except EnvironmentError, ex:
                            self.db.corruption("MultiLangZone.update_buf_data",
                                "could not remove dbfile for '%s' blob: %s"\
                                    % (blobname, ex),
                                "ignore")
                    elif action == "update":
                        # Try to only change the dbfile on disk if it is
                        # different.
                        s = StringIO()
                        if blob.get("src") is None:
                            blob.set("src", buf.path)   # for defns_from_pos() support
                        ET.ElementTree(blob).write(s)
                        new_dbfile_content = s.getvalue()
                        dbfile = blob_index[lang][blobname]
                        dbpath = join(self.base_dir, dhash, dbfile+".blob")
                        # PERF: Might be nice to cache the new dbfile
                        #       content for the next time this resource is
                        #       updated. For files under edit this will be
                        #       common. I.e. just for the "editset".
                        try:
                            fin = open(dbpath, 'r')
                        except (OSError, IOError), ex:
                            # Technically if the dbfile doesn't exist, this
                            # is a sign of database corruption. No matter
                            # though (for this blob anyway), we are about to
                            # replace it.
                            old_dbfile_content = None
                        else:
                            try:
                                old_dbfile_content = fin.read()
                            finally:
                                fin.close()
                        if new_dbfile_content != old_dbfile_content:
                            if not exists(dirname(dbpath)):
                                self._mk_dbdir(dirname(dbpath), dir)
                            #XXX What to do if fail to write out file?
                            log.debug("fs-write: %s|%s blob '%s/%s'",
                                      self.lang, lang, dhash, dbfile)
                            fout = open(dbpath, 'w')
                            try:
                                fout.write(new_dbfile_content)
                            finally:
                                fout.close()

            if res_index_has_changed:
                self.changed_index(dir, "res_index")
            if blob_index_has_changed:
                self.changed_index(dir, "blob_index")
            if is_hits_from_lpath_lang and toplevelname_index_has_changed:
                self.changed_index(dir, "toplevelname_index")
        finally:
            self._release_lock()
        #TODO: Database.clean() should remove dirs that have no
        #      blob_index entries.    



class MultiLangDirsLib(object):
    """A zone providing a view into an ordered list of dirs in a
    db/$multilang/... area of the db.

    These are dished out via Database.get_lang_lib(), which indirectly
    then is dished out by the MultiLangZone.get_lib(). Mostly this is
    just a view on the MultiLangZone singleton for this particular
    language.
    """
    def __init__(self, lang_zone, lock, lang, name, dirs, sublang):
        self.lang_zone = lang_zone
        self._lock = lock
        self.mgr = lang_zone.mgr
        self.lang = lang
        self.name = name
        self.dirs = dirs
        self.sublang = sublang
        self.import_handler \
            = self.mgr.citadel.import_handler_from_lang(sublang)
        self._have_ensured_scanned_from_dir_cache = {}

        # We keep a "weak" merged cache of blobname lookup for all dirs
        # in this zone -- where "weak" means that we verify a hit by
        # checking the current real dbfile_from_blobname index for that
        # dir (which may have changed). This caching slows down lookup
        # for single-dir LangDirsZones, but should scale better for
        # LangDirsZones with many dirs. (TODO-PERF: test this assertion.)
        self._dir_and_blobbase_from_blobname = {}
        self._importables_from_dir_cache = {}

    def __repr__(self):
        return "<%s %s>" % (self.lang, self.name)

    def _acquire_lock(self):
        self._lock.acquire()
    def _release_lock(self):
        self._lock.release()

    def has_blob(self, blobname, ctlr=None):
        dbsubpath = self._dbsubpath_from_blobname(blobname, ctlr=ctlr)
        return dbsubpath is not None

    def has_blob_in_db(self, blobname, ctlr=None):
        """Return true if the blobname is in the database.

        Typically this method is only used for debugging and .has_blob()
        is what you want.
        """
        dbsubpath = self._dbsubpath_from_blobname(
            blobname, ctlr=ctlr, only_look_in_db=True)
        return dbsubpath is not None

    def get_blob(self, blobname, ctlr=None, specific_dir=None):
        self._acquire_lock()
        try:
            if specific_dir:
                specific_dir = abspath(normpath(expanduser(specific_dir)))
            dbsubpath = self._dbsubpath_from_blobname(
                blobname, ctlr=ctlr, specific_dir=specific_dir)
            if dbsubpath is not None:
                return self.lang_zone.load_blob(dbsubpath)
            else:
                return None
        finally:
            self._release_lock()

    def hits_from_lpath(self, lpath, ctlr=None, curr_buf=None):
        """Return all hits of the given lookup path.
        
        I.e. a symbol table lookup across all files in the dirs of this
        lib.

            "lpath" is a lookup name list, e.g. ['Casper', 'Logging']
                or ['dojo', 'animation'].
            "ctlr" (optional) is an EvalController instance. If
                specified it should be used in the normal way (logging,
                checking .is_aborted()).
            "curr_buf" (optional), if specified, is the current buf for
                which this query is being made. Hits from it should be
                skipped (i.e. don't bother searching it).

        A "hit" is (<CIX node>, <scope-ref>).  Each one represent a
        scope-tag or variable-tag hit in all of the blobs for the
        execution set buffers.

        Returns the empty list if no hits.
        """
        assert isinstance(lpath, tuple)  # common mistake to pass in a string

        if curr_buf:
            curr_blobname = curr_buf.blob_from_lang.get(self.lang, {}).get("name")
            curr_buf_dir = dirname(curr_buf.path)
        
        # Naive implementation (no caching)
        hits = []
        for dir in self.dirs:
            if ctlr and ctlr.is_aborted():
                log.debug("ctlr aborted")
                break
            
            # Need to have (at least once) scanned all importables.
            # Responsibility for ensuring the scan data is *up-to-date*
            # is elsewhere.
            self.ensure_dir_scanned(dir, ctlr=ctlr)

            hit_lpath = lpath
            toplevelname_index = self.lang_zone.load_index(
                    dir, "toplevelname_index", {})
            for blobname in toplevelname_index.get_blobnames(
                                self.lang, lpath[0], ()):
                if curr_buf and curr_buf_dir == dir and blobname == curr_blobname:
                    continue
                blob = self.get_blob(blobname, ctlr=ctlr, specific_dir=dir)
                elem = blob
                try:
                    for i, p in enumerate(lpath):
                        #LIMITATION: *Imported* names at each scope are
                        # not being included here. This *should* be okay for
                        # PHP because imports only add symbols to the
                        # top-level. Worse case: the user has to add another
                        # dir to his "extra-dirs" pref.
                        try:
                            elem = elem.names[p]
                        except KeyError:
                            if i == 0 and "\\" in p and self.lang == "PHP":
                                # Deal with PHP namespaces.
                                namespace, elemname = p.rsplit("\\", 1)
                                elem = blob.names[namespace].names[elemname]
                                # The actual hit namespace has a different hit lpath.
                                hit_lpath = (namespace, elemname) + hit_lpath[1:]
                            else:
                                raise
                except KeyError:
                    continue
                hits.append( (elem, (blob, list(hit_lpath[:-1]))) )

        return hits

    def toplevel_cplns(self, prefix=None, ilk=None, ctlr=None):
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
        # Naive implementation (no caching)
        for dir in self.dirs:
            if ctlr and ctlr.is_aborted():
                log.debug("ctlr aborted")
                break

            self.ensure_dir_scanned(dir, ctlr=ctlr)

            try:
                toplevelname_index = self.lang_zone.load_index(
                    dir, "toplevelname_index")
            except EnvironmentError:
                # No toplevelname_index for this dir likely indicates that
                # there weren't any files of the current lang in this dir.
                continue
            cplns += toplevelname_index.toplevel_cplns(
                self.lang, prefix=prefix, ilk=ilk)
        return cplns

    def ensure_dir_scanned(self, dir, ctlr=None):
        """Ensure that all importables in this dir have been scanned
        into the db at least once.

        Note: This is identical to LangDirsLib.ensure_dir_scanned().
        Would be good to share.
        """
        #TODO: should "self.lang" in this function be "self.sublang"?
        if dir not in self._have_ensured_scanned_from_dir_cache:
            event_reported = False
            res_index = self.lang_zone.load_index(dir, "res_index", {})
            importables = self._importables_from_dir(dir)
            importable_values = [i[0] for i in importables.values()
                                 if i[0] is not None]
            for base in importable_values:
                if ctlr and ctlr.is_aborted():
                    log.debug("ctlr aborted")
                    return
                if base not in res_index:
                    if not event_reported:
                        self.lang_zone.db.report_event(
                            "scanning %s files in '%s'" % (self.lang, dir))
                        event_reported = True
                    try:
                        buf = self.mgr.buf_from_path(join(dir, base),
                                                     lang=self.lang)
                    except (EnvironmentError, CodeIntelError), ex:
                        # This can occur if the path does not exist, such as a
                        # broken symlink, or we don't have permission to read
                        # the file, or the file does not contain text.
                        continue
                    if ctlr is not None:
                        ctlr.info("load %r", buf)
                    buf.scan_if_necessary()

            # Remove scanned paths that don't exist anymore.
            removed_values = set(res_index.keys()).difference(importable_values)
            for base in removed_values:
                if ctlr and ctlr.is_aborted():
                    log.debug("ctlr aborted")
                    return
                if not event_reported:
                    self.lang_zone.db.report_event(
                        "scanning %s files in '%s'" % (self.lang, dir))
                    event_reported = True
                basename = join(dir, base)
                self.lang_zone.remove_path(basename)

            self._have_ensured_scanned_from_dir_cache[dir] = True

    def _importables_from_dir(self, dir):
        if dir not in self._importables_from_dir_cache:
            self._importables_from_dir_cache[dir] \
                = self.import_handler.find_importables_in_dir(dir)
        return self._importables_from_dir_cache[dir]
    
    def _dbsubpath_from_blobname(self, blobname, ctlr=None, 
                                 only_look_in_db=False, specific_dir=None):
        """Return the subpath to the dbfile for the given blobname,
        or None if not found.

        Remember that this is complicated by possible multi-level
        imports. E.g. "include('foo/bar.php')".
        """
        lang_zone = self.lang_zone

        self._acquire_lock()
        try:
            # Use our weak cache to try to return quickly.
            if blobname in self._dir_and_blobbase_from_blobname:
                blobdir, blobbase = self._dir_and_blobbase_from_blobname[blobname]

                # Check it. The actual info for that dir may have changed.
                dbfile_from_blobname = lang_zone.dfb_from_dir(blobdir, self.sublang)
                if blobbase in dbfile_from_blobname:
                    log.debug("have blob '%s' in '%s'? yes (in weak cache)",
                              blobname, blobdir)
                    return join(lang_zone.dhash_from_dir(blobdir),
                                dbfile_from_blobname[blobbase])
                del self._dir_and_blobbase_from_blobname[blobname] # drop from weak cache

            # Brute force: look in each dir.
            assert self.import_handler.sep is not None, \
                "%r.sep is None, this must be set" % self.import_handler
            blobparts = blobname.split(self.import_handler.sep)
            blobbase = blobparts[-1]
            for dir in self.dirs:
                if specific_dir is not None and dir != specific_dir:
                    continue
                if ctlr and ctlr.is_aborted():
                    log.debug("aborting search for blob '%s' on %s: ctlr aborted",
                              blobname, self)
                    return None

                # Is the blob in 'blobdir' (i.e. a non-multi-level import
                # that has been scanned already).
                blobdir = join(dir, *blobparts[:-1])
                dbfile_from_blobname = lang_zone.dfb_from_dir(
                                            blobdir, self.sublang, {})
                if blobbase in dbfile_from_blobname:
                    self._dir_and_blobbase_from_blobname[blobname] \
                        = (blobdir, blobbase)
                    log.debug("have blob '%s' in '%s'? yes (in dir index)", 
                              blobname, blobdir)
                    return join(lang_zone.dhash_from_dir(blobdir),
                                dbfile_from_blobname[blobbase])

                importables = self._importables_from_dir(blobdir)
                # 'importables' look like, for PHP:
                #   {'foo.php': ('foo.php', None, False),
                #    'foo.inc': ('foo.inc', None, False),
                #    'somedir': (None,      None, True)}

                if blobbase not in importables:
                    continue

                blobfile, subdir_blobbase, is_dir_import = importables[blobbase]
                if blobfile is None:
                    # There isn't an actual importable file here -- just
                    # a dir prefix to a multidir import.
                    log.debug("have blob '%s' in %s? no", blobname, self)
                    return None
                elif os.sep in blobfile:
                    # This is an import from a subdir. We need to get a new dbf.
                    blobdir = join(blobdir, dirname(blobfile))
                    blobfile = basename(blobfile)
                    blobbase = subdir_blobbase
                    dbfile_from_blobname = lang_zone.dfb_from_dir(
                                                blobdir, self.sublang, {})
                    if blobbase in dbfile_from_blobname:
                        self._dir_and_blobbase_from_blobname[blobname] \
                            = (blobdir, blobbase)
                        log.debug("have blob '%s' in '%s'? yes (in dir index)", 
                                  blobname, blobdir)
                        return join(lang_zone.dhash_from_dir(blobdir),
                                    dbfile_from_blobname[blobbase])

                # The file isn't loaded.
                if not only_look_in_db:
                    log.debug("%s importables in '%s':\n    %s", self.sublang,
                              blobdir, importables)
                    log.debug("'%s' likely provided by '%s' in '%s': "
                              "attempting load", blobname, blobfile, blobdir)
                    try:
                        buf = self.mgr.buf_from_path(
                                join(blobdir, blobfile), self.lang)
                    except (EnvironmentError, CodeIntelError), ex:
                        # This can occur if the path does not exist, such as a
                        # broken symlink, or we don't have permission to read
                        # the file, or the file does not contain text.
                        continue
                    buf.scan_if_necessary()

                    dbfile_from_blobname = lang_zone.dfb_from_dir(
                                                blobdir, self.sublang, {})
                    if blobbase in dbfile_from_blobname:
                        self._dir_and_blobbase_from_blobname[blobname] \
                            = (blobdir, blobbase)
                        log.debug("have blob '%s' in '%s'? yes (after load)",
                                  blobname, blobdir)
                        return join(lang_zone.dhash_from_dir(blobdir),
                                    dbfile_from_blobname[blobbase])

            log.debug("have blob '%s' in %s? no", blobname, self)
            return None
        finally:
            self._release_lock()


