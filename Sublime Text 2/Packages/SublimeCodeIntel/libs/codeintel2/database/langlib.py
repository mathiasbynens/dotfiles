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

"""The langzone of the codeintel database.
See the database/database.py module docstring for an overview.
"""

import sys
import os
from os.path import (join, dirname, exists, expanduser, splitext, basename,
                     split, abspath, isabs, isdir, isfile, normpath)
import threading
import time
from glob import glob
from pprint import pprint, pformat
import logging
from cStringIO import StringIO
import codecs
import copy

import ciElementTree as ET
from codeintel2.common import *
from codeintel2 import util
from codeintel2.database.util import rmdir



#---- globals

log = logging.getLogger("codeintel.db")
#log.setLevel(logging.DEBUG)



#---- Database zone and lib implementations

class LangDirsLib(object):
    """A zone providing a view into an ordered list of dirs in a
    db/$lang/... area of the db.

    These are dished out via Database.get_lang_lib(), which indirectly
    then is dished out by the LangZone.get_lib(). Mostly this is just a
    view on the LangZone singleton for this particular language.

    Dev Notes:
    - The goal is to provide quick has_blob() and get_blob() -- i.e.
      some caching is involved (if 'foo' referred to
      'some/path/to/foo.py' a minute ago then it still does). As well,
      scanning/loading is done automatically as necessary. For example,
      if a request for Perl blob 'Bar' is made but there is no 'Bar' in
      the database yet, this code looks for a 'Bar.pm' on the file
      system and will scan it, load it and return the blob for it.
    """
    def __init__(self, lang_zone, lock, lang, name, dirs):
        self.lang_zone = lang_zone
        self._lock = lock
        self.mgr = lang_zone.mgr
        self.lang = lang
        self.name = name
        self.dirs = dirs
        self.import_handler \
            = self.mgr.citadel.import_handler_from_lang(self.lang)

        self._blob_imports_from_prefix_cache = {}
        self._have_ensured_scanned_from_dir_cache = {}
        self._importables_from_dir_cache = {}

        # We keep a "weak" merged cache of blobname lookup for all dirs
        # in this zone -- where "weak" means that we verify a hit by
        # checking the current real blob_index for that dir (which may
        # have changed). This caching slows down lookup for single-dir
        # LangDirsZones, but should scale better for LangDirsZones with
        # many dirs. (TODO-PERF: test this assertion.)
        self._dir_and_blobbase_from_blobname = {}

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

    def get_blob(self, blobname, ctlr=None):
        self._acquire_lock()
        try:
            dbsubpath = self._dbsubpath_from_blobname(blobname, ctlr=ctlr)
            if dbsubpath is not None:
                return self.lang_zone.load_blob(dbsubpath)
            else:
                return None
        finally:
            self._release_lock()

    def get_blob_imports(self, prefix):
        """Return the set of imports under the given prefix.

            "prefix" is a tuple of import name parts. E.g. ("xml", "sax")
                for "import xml.sax." in Python. Or ("XML", "Parser") for
                "use XML::Parser::" in Perl.

        See description in database.py docstring for details.
        """
        self._acquire_lock()
        try:
            if prefix not in self._blob_imports_from_prefix_cache:
                if prefix:
                    for dir in self.dirs:
                        importables = self._importables_from_dir(dir)
                        if prefix[0] in importables:
                            sub_importables = self._importables_from_dir(
                                join(dir, *prefix))
                            imports = set(
                                (name, is_dir_import)
                                for name, (_, _, is_dir_import)
                                in sub_importables.items()
                            )
                            break
                    else:
                        imports = set()
                else:
                    imports = set()
                    for dir in self.dirs:
                        importables = self._importables_from_dir(dir)
                        imports.update(
                            (name, is_dir_import)
                            for name, (_, _, is_dir_import)
                            in importables.items()
                        )
                self._blob_imports_from_prefix_cache[prefix] = imports
            return self._blob_imports_from_prefix_cache[prefix]
        finally:
            self._release_lock()

    def blobs_with_basename(self, basename, ctlr=None):
        """Return all blobs that match the given base path.
        
        I.e. a filename lookup across all files in the dirs of this lib.

            "basename" is a string, e.g. 'Http.js'
            "ctlr" (optional) is an EvalController instance. If
                specified it should be used in the normal way (logging,
                checking .is_aborted()).

        A "blob" is a global scope-tag hit in all of the blobs for the execution
        set buffers.

        Returns the empty list if no hits.
        """
        blobs = []
        # we can't use self.get_blob because that only returns one answer; we
        # we need all of them.

        self._acquire_lock()
        try:
            for dir in self.dirs:
                self.ensure_dir_scanned(dir)
                dbfile_from_blobname = self.lang_zone.dfb_from_dir(dir, {})
                blobbase = dbfile_from_blobname.get(basename)
                if blobbase is not None:
                    dhash = self.lang_zone.dhash_from_dir(dir)
                    dbsubpath = join(dhash, blobbase)
                    blobs.append(self.lang_zone.load_blob(dbsubpath))
        finally:
            self._release_lock()
        return blobs

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

            toplevelname_index = self.lang_zone.load_index(
                    dir, "toplevelname_index", {})
            for blobname in toplevelname_index.get_blobnames(lpath[0], ()):
                if curr_buf and curr_buf_dir == dir and blobname == curr_blobname:
                    continue
                blob = self.get_blob(blobname, ctlr=ctlr)
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
            cplns += toplevelname_index.toplevel_cplns(prefix=prefix, ilk=ilk)
        return cplns

    def ensure_all_dirs_scanned(self, ctlr=None):
        """Ensure that all importables in this dir have been scanned
        into the db at least once.

        Note: This is identical to MultiLangDirsLib.ensure_dir_scanned().
        Would be good to share.
        """
        for dir in self.dirs:
            if ctlr and ctlr.is_aborted():
                log.debug("ctlr aborted")
                break
            self.ensure_dir_scanned(dir, ctlr)

    def ensure_dir_scanned(self, dir, ctlr=None):
        """Ensure that all importables in this dir have been scanned
        into the db at least once.

        Note: This is identical to MultiLangDirsLib.ensure_dir_scanned().
        Would be good to share.
        """
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
                                 only_look_in_db=False):
        """Return the subpath to the dbfile for the given blobname,
        or None if not found.

        Remember that this is complicated by possible multi-level
        imports. E.g. "import foo.bar" or "import foo" where 'foo'
        refers to 'foo/__init__.py'.
        """
        assert blobname is not None, "'blobname' cannot be None"
        lang_zone = self.lang_zone

        self._acquire_lock()
        try:
            # Use our weak cache to try to return quickly.
            if blobname in self._dir_and_blobbase_from_blobname:
                blobdir, blobbase \
                    = self._dir_and_blobbase_from_blobname[blobname]

                # Check it. The actual info for that dir may have changed.
                dbfile_from_blobname = lang_zone.dfb_from_dir(blobdir)
                if blobbase in dbfile_from_blobname:
                    log.debug("have blob '%s' in '%s'? yes (in weak cache)",
                              blobname, blobdir)
                    return join(lang_zone.dhash_from_dir(blobdir),
                                dbfile_from_blobname[blobbase])
                # Drop from weak cache.
                del self._dir_and_blobbase_from_blobname[blobname]

            # Brute force: look in each dir.
            blobparts = blobname.split(self.import_handler.sep)
            blobbase = blobparts[-1]
            for dir in self.dirs:
                if ctlr and ctlr.is_aborted():
                    log.debug("aborting search for blob '%s' on %s: "
                              "ctlr aborted", blobname, self)
                    return None

                # Is the blob in 'blobdir' (i.e. a non-multi-level import
                # that has been scanned already).
                blobdir = join(dir, *blobparts[:-1])
                dbfile_from_blobname = lang_zone.dfb_from_dir(blobdir, {})
                if self.lang == "Perl":
                    # Perl uses the full blob name - not just the blob base,
                    # see bug 89106 for details.
                    if blobname in dbfile_from_blobname:
                        self._dir_and_blobbase_from_blobname[blobname] \
                            = (blobdir, blobname)
                        log.debug("have blob '%s' in '%s'? yes (in dir index)", 
                                  blobname, blobdir)
                        return join(lang_zone.dhash_from_dir(blobdir),
                                    dbfile_from_blobname[blobname])
                if blobbase in dbfile_from_blobname:
                    self._dir_and_blobbase_from_blobname[blobname] \
                        = (blobdir, blobbase)
                    log.debug("have blob '%s' in '%s'? yes (in dir index)", 
                              blobname, blobdir)
                    return join(lang_zone.dhash_from_dir(blobdir),
                                dbfile_from_blobname[blobbase])

                importables = self._importables_from_dir(blobdir)
                # 'importables' look like, for Python:
                #   {'foo':  ('foo.py',          None,       False),
                #    'pkg':  ('pkg/__init__.py', '__init__', False)}
                # for Perl:
                #   {'LWP':  ('LWP.pm',          None,       True),
                #    'File': (None,              None,       True)}
                #    |        |                  |           `-- is-dir-import
                #    |        |                  `-- subdir-blobbase
                #    |        `-- blobfile
                #    `-- blobbase

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
                    dbfile_from_blobname = lang_zone.dfb_from_dir(blobdir, {})
                    if blobbase in dbfile_from_blobname:
                        self._dir_and_blobbase_from_blobname[blobname] \
                            = (blobdir, blobbase)
                        log.debug("have blob '%s' in '%s'? yes (in dir index)", 
                                  blobname, blobdir)
                        return join(lang_zone.dhash_from_dir(blobdir),
                                    dbfile_from_blobname[blobbase])

                # The file isn't loaded.
                if not only_look_in_db:
                    log.debug("%s importables in '%s':\n    %s", self.lang,
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

                    dbfile_from_blobname = lang_zone.dfb_from_dir(blobdir, {})
                    if self.lang == "Perl":
                        # Perl uses the full blob name - not just the blob base,
                        # see bug 89106 for details.
                        if blobname in dbfile_from_blobname:
                            self._dir_and_blobbase_from_blobname[blobname] \
                                = (blobdir, blobname)
                            log.debug("have blob '%s' in '%s'? yes (in dir index)", 
                                      blobname, blobdir)
                            return join(lang_zone.dhash_from_dir(blobdir),
                                        dbfile_from_blobname[blobname])
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


class LangTopLevelNameIndex(object):
    """A wrapper around the plain-dictionary toplevelname_index for a
    LangZone dir to provide better performance for continual updating
    and some simpler access.

        {ilk -> toplevelname -> blobnames}

    # Problem

    A 'toplevelname_index' is a merge of {blobname -> ilk -> toplevelnames}
    data for all resources in its dir.  As those resources are
    continually re-scanned (e.g. as a file is edited in Komodo), it
    would be too expensive to update this index everytime.

    # Solution
    
    Keep a list of "recent updates" and only merge them into the main
    data when that buf hasn't been updated in "a while" and when needed
    for saving the index. Note: Buffer *removals* are not put on-deck,
    but removed immediately.

    # .get_blobnames(..., ilk=None)
    
    Originally the toplevelname_index stored {toplevelname -> blobnames}.
    The per-"ilk" level was added afterwards to support occassional ilk
    filtering for PHP (and possible eventually other langs).
    
    .get_blobnames() still behaves like a {toplevelname -> blobnames}
    mapping, but it provides an optional "ilk" keyword arg to limit the
    results to that ilk.

    # Notes on locking

    This class does not guard its datastructures with locking. It is up
    to the LangZone using this to guard against simultaneous access on
    separate threads.
    """
    def __init__(self, data=None, timeout=90):
        # toplevelname_index data: {ilk -> toplevelname -> blobnames}
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
            #       {blobname -> ilk -> toplevelnames},
            #       # Lazily generated pivot, a.k.a. 'res_data_pivot'
            #       {ilk -> toplevelname -> blobnames}
            #      ]
        }

    def __repr__(self):
        num_toplevelnames = sum(len(v) for v in self._data.itervalues())
        return ("<LangTopLevelNameIndex: %d top-level name(s), "
                "%d update(s) on-deck>"
                    % (num_toplevelnames, len(self._on_deck)))

    def merge(self):
        """Merge all on-deck changes with `self.data'."""
        for base, (timestamp, res_data,
                   res_data_pivot) in self._on_deck.items():
            if res_data_pivot is None:
                res_data_pivot = self._pivot_res_data(res_data)
            # res_data_pivot: {ilk -> toplevelname -> blobnames}
            # "bft" means blobnames_from_toplevelname
            for ilk, bft in res_data_pivot.iteritems():
                data_bft = self._data.setdefault(ilk, {})
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
            # res_data_pivot: {ilk -> toplevelname -> blobnames}
            # "bft" means blobnames_from_toplevelname
            for ilk, bft in res_data_pivot.iteritems():
                data_bft = self._data.setdefault(ilk, {})
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
            # old_res_data:   {blobname -> ilk -> toplevelnames}
            # self._data: {ilk -> toplevelname -> blobnames}
            for blobname, toplevelnames_from_ilk in old_res_data.iteritems():
                for ilk, toplevelnames in toplevelnames_from_ilk.iteritems():
                    for toplevelname in toplevelnames:
                        try:
                            self._data[ilk][toplevelname].remove(blobname)
                        except KeyError:
                            pass # ignore this for now, might indicate corruption
                        else:
                            if not self._data[ilk][toplevelname]:
                                del self._data[ilk][toplevelname]
                    if not self._data.get(ilk):
                        del self._data[ilk]

    def _pivot_res_data(self, res_data):
        # res_data:       {blobname -> ilk -> toplevelnames}
        # res_data_pivot: {ilk -> toplevelname -> blobnames}
        res_data_pivot = {}
        for blobname, toplevelnames_from_ilk in res_data.iteritems():
            for ilk, toplevelnames in toplevelnames_from_ilk.iteritems():
                pivot_bft = res_data_pivot.setdefault(ilk, {})
                for toplevelname in toplevelnames:
                    if toplevelname not in pivot_bft:
                        pivot_bft[toplevelname] = set([blobname])
                    else:
                        pivot_bft[toplevelname].add(blobname)
        return res_data_pivot

    def toplevel_cplns(self, prefix=None, ilk=None):
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
            if res_data_pivot is None:
                res_data_pivot = self._on_deck[base][2] \
                    = self._pivot_res_data(res_data)
            # res_data_pivot: {ilk -> toplevelname -> blobnames}
            if ilk is None:
                for i, bft in res_data_pivot.iteritems():
                    cplns += [(i, toplevelname) for toplevelname in bft]
            elif ilk in res_data_pivot:
                cplns += [(ilk, toplevelname)
                          for toplevelname in res_data_pivot[ilk]]

        # ...merged data
        # self._data: {ilk -> toplevelname -> blobnames}
        if ilk is None:
            for i, bft in self._data.iteritems():
                cplns += [(i, toplevelname) for toplevelname in bft]
        elif ilk in self._data:
            cplns += [(ilk, toplevelname)
                      for toplevelname in self._data[ilk]]

        # Naive implementation: Instead of maintaining a separate
        # 'toplevelprefix_index' (as we do for StdLibsZone and CatalogsZone)
        # for now we'll just gather all results and filter on the prefix
        # here. Only if this proves to be a perf issue will we add the
        # complexity of another index:
        #   {ilk -> prefix -> toplevelnames}
        if prefix is not None:
            cplns = [(i, t) for i, t in cplns if t.startswith(prefix)]

        return cplns

    def get_blobnames(self, toplevelname, default=None, ilk=None):
        """Return the blobnames defining the given toplevelname.

        If "ilk" is given then only symbols of that ilk will be considered.
        If not match is found the "default" is returned.
        """
        self.merge_expired(time.time())

        blobnames = set()
        # First check on-deck items.
        for base, (timestamp, res_data,
                   res_data_pivot) in self._on_deck.items():
            if res_data_pivot is None:
                res_data_pivot = self._on_deck[base][2] \
                    = self._pivot_res_data(res_data)
            # res_data_pivot: {ilk -> toplevelname -> blobnames}
            if ilk is None:
                for bft in res_data_pivot.itervalues():
                    if toplevelname in bft:
                        blobnames.update(bft[toplevelname])
            elif ilk in res_data_pivot:
                if toplevelname in res_data_pivot[ilk]:
                    blobnames.update(res_data_pivot[ilk][toplevelname])

        #TODO: Put lookup in merged data ahead of lookup in on-deck -- so
        #      we don't do on-deck work if not necessary.
        # Then, fallback to already merged data.
        # self._data: {ilk -> toplevelname -> blobnames}
        if ilk is None:
            for bft in self._data.itervalues():
                if toplevelname in bft:
                    blobnames.update(bft[toplevelname])
        elif ilk in self._data:
            if toplevelname in self._data[ilk]:
                blobnames.update(self._data[ilk][toplevelname])

        if blobnames:
            return blobnames
        return default


class LangZone(object):
    """Singleton zone managing a particular db/$lang/... area.

    # caching and memory control

    We cache all retrieved indices and blobs and maintain their latest
    access time. To try to manage memory consumption, we rely on a
    bookkeeper thread (the indexer) to periodically call .cull_mem() --
    which unloads cache items that have not been accessed in a while.

    (TODO:
    - Get the indexer to actually call .cull_mem() and .save()
      periodically.
    - Test that .cull_mem() actually results in the process releasing
      memory.)

    # robustness (TODO)

    Work should be done to improve robustness.
    - Collect filesystem interactions in one place.
    - Rationalize OSError handling.
    - Consider a journal system, if necessary/feasible. My hope is to
      get away without one and rely on graceful recovery. The db does
      not store critical info so can allow some loss of data (it can all
      be regenerated).
    """
    toplevelname_index_class = LangTopLevelNameIndex

    def __init__(self, mgr, lang):
        self.mgr = mgr
        self.db = mgr.db
        self.lang = lang
        self.base_dir = join(self.db.base_dir, "db",
                             util.safe_lang_from_lang(lang))
        self._check_lang(lang)
        self._hook_handlers = self.mgr.hook_handlers_from_lang(lang)

        self._lock = threading.RLock()

        self._dhash_from_dir_cache = {}
        self._dirslib_cache = {}
        self._ordered_dirslib_cache_keys = [] # most recent first

        # We cache the set of recent indeces and blobs in memory.
        #   {db-subpath: [index-object, <atime>]),
        #    ...}
        # For example:
        #   {'7bce640bc48751b128af5c8bf5df8412/res_index':
        #       [<res-index>, 1158289000]),
        #    ...}
        self._index_and_atime_from_dbsubpath = {}
        #TODO-PERF: Use set() object for this? Compare perf.
        self._is_index_dirty_from_dbsubpath = {} # set of dirty indeces
        ##TODO: blob caching and *use* this
        #self._blob_and_atime_from_dbsubpath = {}

        #XXX Need a 'dirty-set' for blobs? No, because currently
        #    .update_buf_data() saves blob changes to disk immediately. Not
        #    sure that is best for perf. Definitely not ideal for the
        #    "editset".

    def __repr__(self):
        return "<%s lang db>" % self.lang

    def _acquire_lock(self):
        self._lock.acquire()
    def _release_lock(self):
        self._lock.release()

    def _check_lang(self, lang):
        """Ensure that the given lang matches case exactly with the lang
        in the db. If this invariant is broken, then weird things with
        caching can result.
        """
        if exists(self.base_dir):
            lang_path = join(self.base_dir, "lang")
            try:
                fin = open(lang_path, 'r')
            except EnvironmentError, ex:
                self.db.corruption("LangZone._check_lang",
                    "could not open `%s': %s" % (lang_path, ex),
                    "recover")
                fin = open(lang_path, 'w')
                try:
                    fin.write(lang)
                finally:
                    fin.close()
            else:
                try:
                    lang_on_disk = fin.read().strip()
                finally:
                    fin.close()
                assert lang_on_disk == lang

    #TODO: If Database.dhash_from_dir() grows caching, then this
    #      shouldn't bother.
    def dhash_from_dir(self, dir):
        if dir not in self._dhash_from_dir_cache:
            self._dhash_from_dir_cache[dir] = self.db.dhash_from_dir(dir)
        return self._dhash_from_dir_cache[dir]

    def dfb_from_dir(self, dir, default=None):
        """Get the {blobname -> dbfile} mapping index for the given dir.
        
        'dfb' stands for 'dbfile_from_blobname'.
        This must be called with the lock held.
        """
        return self.load_index(dir, "blob_index", default)

    def get_buf_scan_time(self, buf):
        #TODO Canonicalize path (or assert that it is canonicalized)
        self._acquire_lock()
        try:
            dir, base = split(buf.path)
            res_index = self.load_index(dir, "res_index", {})
            if base not in res_index:
                return None
            return res_index[base][0]
        finally:
            self._release_lock()

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

            blob_from_lang = {}
            if res_data:
                try:
                    dbfile_from_blobname = self.dfb_from_dir(dir)
                except EnvironmentError, ex:
                    # DB corruption will be noted in remove_buf_data()
                    self.remove_buf_data(buf)
                    raise NotFoundInDatabase("%s buffer '%s' not found in database"
                                             % (buf.lang, buf.path))
                dhash = self.dhash_from_dir(dir)
                for blobname in res_data:
                    dbsubpath = join(dhash, dbfile_from_blobname[blobname])
                    try:
                        blob = self.load_blob(dbsubpath)
                    except ET.XMLParserError, ex:
                        self.db.corruption("LangZone.get_buf_data",
                            "could not parse dbfile for '%s' blob: %s"\
                                % (blobname, ex),
                            "recover")
                        self.remove_buf_data(buf)
                        raise NotFoundInDatabase(
                            "`%s' buffer `%s' blob was corrupted in database"
                            % (buf.path, blobname))
                    except EnvironmentError, ex:
                        self.db.corruption("LangZone.get_buf_data",
                            "could not read dbfile for '%s' blob: %s"\
                                % (blobname, ex),
                            "recover")
                        self.remove_buf_data(buf)
                        raise NotFoundInDatabase(
                            "`%s' buffer `%s' blob not found in database"
                            % (buf.path, blobname))
                    lang = blob.get("lang")
                    assert lang is not None
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
                self.db.corruption("LangZone.remove_path",
                    "could not read blob_index for '%s' dir: %s" % (dir, ex),
                    "recover")
                blob_index = {}

            is_hits_from_lpath_lang = self.lang in self.db.import_everything_langs
            if is_hits_from_lpath_lang:
                try:
                    toplevelname_index = self.load_index(dir, "toplevelname_index")
                except EnvironmentError, ex:
                    self.db.corruption("LangZone.remove_path",
                        "could not read toplevelname_index for '%s' dir: %s"
                            % (dir, ex),
                        "recover")
                    toplevelname_index = self.toplevelname_index_class()

            dhash = self.dhash_from_dir(dir)
            del res_index[base]
            for blobname in res_data:
                try:
                    dbfile = blob_index[blobname]
                except KeyError:
                    blob_index_path = join(dhash, "blob_index")
                    self.db.corruption("LangZone.remove_path",
                        "'%s' blob not in '%s'" \
                            % (blobname, blob_index_path),
                        "ignore")
                    continue
                del blob_index[blobname]
                for path in glob(join(self.base_dir, dhash, dbfile+".*")):
                    log.debug("fs-write: remove %s blob file '%s/%s'",
                              self.lang, dhash, basename(path))
                    os.remove(path)
            if is_hits_from_lpath_lang:
                toplevelname_index.remove(base, res_data)

            self.changed_index(dir, "res_index")
            self.changed_index(dir, "blob_index")
            if is_hits_from_lpath_lang:
                self.changed_index(dir, "toplevelname_index")
        finally:
            self._release_lock()
        #TODO Database.clean() should remove dirs that have no
        #     blob_index entries.    

    def remove_buf_data(self, buf):
        """Remove the given buffer from the database."""
        self.remove_path(buf.path)

    def update_buf_data(self, buf, scan_tree, scan_time, scan_error,
                        skip_scan_time_check=False):
        """Update this LangZone with the buffer data.

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
            # res_data: {blobname -> ilk -> toplevelnames}
            new_res_data = {}
            new_blobnames_and_blobs = []
            if scan_tree:
                for blob in scan_tree[0]:
                    lang = blob.get("lang")
                    assert blob.get("lang") == self.lang, "'%s' != '%s' (blob %r)" % (blob.get("lang"), self.lang, blob)
                    blobname = blob.get("name")
                    toplevelnames_from_ilk = new_res_data.setdefault(blobname, {})
                    for toplevelname, elem in blob.names.iteritems():
                        ilk = elem.get("ilk") or elem.tag
                        if ilk not in toplevelnames_from_ilk:
                            toplevelnames_from_ilk[ilk] = set([toplevelname])
                        else:
                            toplevelnames_from_ilk[ilk].add(toplevelname)
                    new_blobnames_and_blobs.append((blobname, blob))

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

                # Determine necessary changes to blob_index and the
                # dbfiles and then make them.
                dbfile_changes = []
                for blobname, blob in new_blobnames_and_blobs:
                    if blobname in old_res_data:
                        dbfile_changes.append(("update", blobname, blob))
                    else:
                        dbfile_changes.append(("add", blobname, blob))
                for blobname in old_res_data:
                    if blobname not in new_res_data:
                        dbfile_changes.append(("remove", blobname, None))

                dhash = self.dhash_from_dir(dir)
                for action, blobname, blob in dbfile_changes:
                    if action == "add":
                        dbfile = self.db.bhash_from_blob_info(
                                    buf.path, self.lang, blobname)
                        blob_index[blobname] = dbfile
                        blob_index_has_changed = True
                        dbdir = join(self.base_dir, dhash)
                        if not exists(dbdir):
                            self._mk_dbdir(dbdir, dir)
                        #XXX What to do on write failure?
                        log.debug("fs-write: %s blob '%s/%s'",
                                  self.lang, dhash, dbfile)
                        if blob.get("src") is None:
                            blob.set("src", buf.path)   # for defns_from_pos() support
                        ET.ElementTree(blob).write(join(dbdir, dbfile+".blob"))
                    elif action == "remove":
                        dbfile = blob_index[blobname]
                        del blob_index[blobname]
                        blob_index_has_changed = True
                        #XXX What to do on removal failure?
                        log.debug("fs-write: remove %s blob '%s/%s'",
                                  self.lang, dhash, dbfile)
                        os.remove(join(self.base_dir, dhash, dbfile+".blob"))
                    elif action == "update":
                        # Try to only change the dbfile on disk if it is
                        # different.
                        s = StringIO()
                        if blob.get("src") is None:
                            blob.set("src", buf.path)   # for defns_from_pos() support
                        ET.ElementTree(blob).write(s)
                        new_dbfile_content = s.getvalue()
                        dbfile = blob_index[blobname]
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
                            log.debug("fs-write: %s blob '%s/%s'",
                                      self.lang, dhash, dbfile)
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
        #TODO Database.clean() should remove dirs that have no
        #     blob_index entries.    

    def _mk_zone_skel(self):
        log.debug("fs-write: mkdir '%s'", self.base_dir)
        os.makedirs(self.base_dir)
        log.debug("fs-write: create 'lang'")
        fout = codecs.open(join(self.base_dir, "lang"), 'wb', 'utf-8')
        try:
            fout.write(self.lang)
        finally:
            fout.close()

    def _mk_dbdir(self, dbdir, dir):
        if not exists(self.base_dir):
            self._mk_zone_skel()
        log.debug("fs-write: mkdir '%s'", dbdir[len(self.base_dir)+1:])
        os.mkdir(dbdir)
        log.debug("fs-write: '%s/path'", dbdir[len(self.base_dir)+1:])
        fout = codecs.open(join(dbdir, "path"), 'wb', 'utf-8')
        try:
            fout.write(dir)
        finally:
            fout.close()

    def load_blob(self, dbsubpath):
        """This must be called with the lock held."""
        log.debug("TODO: LangZone.load_blob: add blob caching!")
        log.debug("fs-read: load %s blob '%s'", self.lang, dbsubpath)
        dbpath = join(self.base_dir, dbsubpath+".blob")
        blob = ET.parse(dbpath).getroot()
        for hook_handler in self._hook_handlers:
            try:
                hook_handler.post_db_load_blob(blob)
            except:
                log.exception("error running hook: %r.post_db_load_blob(%r)",
                              hook_handler, blob)
        return blob

    def load_index(self, dir, index_name, default=None):
        """Get the indicated index.

            "dir" is the dir path this index represents.
            "index_name" is the name of the index.
            "default" (default None) indicate the value to return for
                the index if the index doesn't exist. If not set (or
                None) then an OSError is raised if the index doesn't exist.

        The index is loaded from a pickle on disk, if necessary, put
        into the cache system, and returned.
        
        This must be called with the lock held.
        """
        self._acquire_lock()
        try:
            dbsubpath = join(self.db.dhash_from_dir(dir), index_name)

            # If index path is in the cache: return it, update its atime.
            now = time.time()
            if dbsubpath in self._index_and_atime_from_dbsubpath:
                log.debug("cache-read: load %s index '%s'", self.lang, dbsubpath)
                self._index_and_atime_from_dbsubpath[dbsubpath][1] = now
                return self._index_and_atime_from_dbsubpath[dbsubpath][0]

            # Otherwise, load it.
            log.debug("fs-read: load %s index '%s'", self.lang, dbsubpath)
            dbpath = join(self.base_dir, dbsubpath)
            index = self.db.load_pickle(dbpath, default)
            if index_name == "toplevelname_index":
                index = self.toplevelname_index_class(index)
            self._index_and_atime_from_dbsubpath[dbsubpath] = [index, now]
            return index
        finally:
            self._release_lock()

    def changed_index(self, dir, index_name):
        """Note that we've changed this index (so it can be saved as
        appropriate).
        """
        self._acquire_lock()
        try:
            now = time.time()
            dbsubpath = join(self.db.dhash_from_dir(dir), index_name)
            self._index_and_atime_from_dbsubpath[dbsubpath][1] = now
            self._is_index_dirty_from_dbsubpath[dbsubpath] = True
        finally:
            self._release_lock()

    def save_index(self, dbsubpath, index):
        if isinstance(index, self.toplevelname_index_class):
            index = index.data
        self.db.save_pickle(join(self.base_dir, dbsubpath), index)

    def save(self):
        self._acquire_lock()
        try:
            for dbsubpath in self._is_index_dirty_from_dbsubpath:
                self.save_index(dbsubpath,
                    self._index_and_atime_from_dbsubpath[dbsubpath][0])
            self._is_index_dirty_from_dbsubpath = {}
        finally:
            self._release_lock()

    def cull_mem(self):
        """Drop indeces and tree from cache that have not been
        accessed in over 5 minutes.

        To attempt to keep memory consumption under control we want to
        ensure we don't keep everything cached from the db in memory
        until process completion. The plan is to have a thread
        periodically cull memory.
        """
        #TODO: Database.cull_mem(). Add it. Get indexer to call it.
        #TOTEST: Does Python/Komodo actually release this memory or
        #        are we kidding ourselves?
        self._acquire_lock()
        try:
            N = 30
            if len(self._index_and_atime_from_dbsubpath) < N:
                # Too few indeces in memory to bother culling.
                return

            now = time.time()
            for dbsubpath, (index, atime) \
                    in self._index_and_atime_from_dbsubpath.items():
                if now - atime > 300.0: # >5 minutes since last access
                    if dbsubpath in self._is_index_dirty_from_dbsubpath:
                        self.save_index(dbsubpath, index)
                        del self._is_index_dirty_from_dbsubpath[dbsubpath]
                    del self._index_and_atime_from_dbsubpath[dbsubpath]
        finally:
            self._release_lock()

        #XXX Database.clean(): Go through each $lang/dir/res_index and
        #    clean out files in the index but that don't actually exist
        #    anymore.
        #XXX Database.clean(): drop memory for indeces that are quite
        #    old (say haven't been accessed in 20 minutes).
        #XXX Database.check(): Shouldn't have too many cached indeces in
        #    memory. How old is the oldest one? Estimate memory size
        #    used by all loaded indeces?

    # TODO: When a directory no longer exists on the filesystem - should we
    #          1) remove the db data, or
    #          2) mark it as expired.
    #       Option 2 would work better for (network) mounted filesystems, as it
    #       could just be an intermittent issue.
    def clean(self):
        """Clean out any expired/old codeintel information."""
        base_dir = self.base_dir
        if not exists(base_dir):
            return
        for d in os.listdir(base_dir):
            path_path = join(base_dir, d, "path")
            if not exists(path_path):
                continue
            path = codecs.open(path_path, encoding="utf-8").read()
            if not exists(path):
                # Referenced directory no longer exists - so remove the db info.
                log.debug("clean:: scanned directory no longer exists: %r",
                          path)
                rmdir(join(base_dir, d))

    def get_lib(self, name, dirs):
        """
        Dev Notes:
        We make a lib for a particular sequence of dirs a singleton because:
        1. The sequence of dirs for a language's import path tends to
           not change, so the same object will tend to get used.
        2. This allows caching of filesystem lookups to be done naturally
           on the LangDirsLib instance.

        To ensure that this cache doesn't grow unboundedly we only allow
        there to be N cached LangDirsLib's. A good value for N is when
        there are relatively few cache misses. Ideally we'd want to
        count the number of cache misses (i.e. LangDirsLib instance
        creations) for a number of "typical" uses of codeintel -- i.e. a
        long running Komodo profile. Failing that we'll just use N=10.
        """
        assert isinstance(dirs, (tuple, list))
        canon_dirs = tuple(abspath(normpath(expanduser(d))) for d in dirs)
        if canon_dirs in self._dirslib_cache:
            return self._dirslib_cache[canon_dirs]

        langdirslib = LangDirsLib(self, self._lock, self.lang, name,
                                  canon_dirs)
        # Ensure that these directories are all *up-to-date*.
        langdirslib.ensure_all_dirs_scanned()
        
        N = 10
        while len(self._ordered_dirslib_cache_keys) >= N:
            cache_key = self._ordered_dirslib_cache_keys.pop()
            del self._dirslib_cache[cache_key]
        self._dirslib_cache[canon_dirs] = langdirslib
        self._ordered_dirslib_cache_keys.insert(0, canon_dirs)

        return langdirslib

