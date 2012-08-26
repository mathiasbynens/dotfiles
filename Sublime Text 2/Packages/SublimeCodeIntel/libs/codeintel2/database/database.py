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

"""The new database for codeintel2.

# Usage

There is a single Database instance on the codeintel Manager (mgr.db).
All entry points to the database are via this instance.

There are two common modes of interaction:

1. Getting info for a particular buffer. E.g., for a code browser or for
   information on a current file. Here all interaction can be done via a
   few methods on the main Database class.

    Database.get_buf_data(buf)
    Database.get_buf_scan_time(buf)
    Database.update_buf_data(buf, ...)
    Database.remove_buf_data(buf)

2. Working with a blob (a.k.a. module) given a list of libs.
   Typically this is done during completion evaluation (i.e. detemining
   what completions to show for "foo."). Here a particular environment
   will have a list of "libs", all of them from the main Database
   instance, via, e.g.:
   
    Database.get_stdlib(...)
    Database.get_catalog_lib(...)
    Database.get_lang_lib(...)
    etc.

   A "lib" instance has the following standard interface:

    .has_blob(blobname)
        Returns True iff a so-named blob is provided by this lib.

    .get_blob(blobname)
        Returns the so-named blob (the importable section of a CIX
        element tree) provided by this lib, or None if it isn't.

    .get_blob_imports(prefix)
        Returns a set of blobnames to complete the given import prefix.
        This is generally used for completion on import statements, e.g.
            import <|>      # lib.get_blob_imports(prefix=())
            import foo.<|>  # lib.get_blob_imports(prefix=('foo',))
        Note that prefix has to be a tuple (rather than a list) because
        the method is automatically cached.
        
        Items in the returned set a 2-tuples, (<import-name>,
        <is-dir-import>), where <is-dir-import> is a boolean indicating
        if this is a prefix for a multidir import. For example, in
        Perl's stdlib there is an "HTTP::Request" module, but no "HTTP"
        module. One of returned items would be:
            ("HTTP", True)
        The set can have both (e.g. Perl's LWP.pm and LWP/UserAgent.pm):
            ("LWP", False)   # for "use LWP;"
            ("LWP", True)     # prefix for "use LWP::UserAgent;"

    .hits_from_lpath(lpath, ctlr=None, curr_buf=None)
        Returns all "hits" for the given lookup path in all blobs in
        this lib.  This is to support "import-everything" semantics
        necessary for langs like JavaScript (no explicit local import
        statements) and PHP (with auto-loading anything can happen). It
        is possible that other langs may not support this.

    .toplevel_cplns(prefix=None, ilk=None, ctlr=None):
        Find all toplevel names starting with the given prefix in all
        blobs in this lib and return a list of completions:
            (<ilk>, <name>)
        where <ilk> is, e.g., "class" or "function" or "variable", etc.
        'ilk' can be specified to restrict the results to names of that
        ilk. If prefix is None then *all* toplevel names are returned.
    
   where "blob" is the generic internal name used for "the token with
   which you import", e.g.:
  
        LANGUAGE    IMPORT STATEMENT        BLOBNAME
        --------    ----------------        --------
        Python      import foo              foo
        Perl        use Foo;                Foo
        PHP         include("foo.php");     foo.php


# Database structure

The database is divided into *zones*, primarily along
common-implementation lines. E.g. dir under "db" is a zone.


<base-dir>/                 # E.g. ~/.komodo/6.0/codeintel
    README.txt
    VERSION
    db/
        # Any dir at this level is an independent database for a
        # single DB "zone".

        # API Catalogs zone -- codeintel API data loaded from .cix files
        # in one of the db_catalog_dirs.
        catalogs/
            res_index   # cix-path -> (res_id, last-updated, name, 
                        #              {lang -> blobname -> ilk -> toplevelnames})
            blob_index              # {lang -> blobname -> (dbfile, res_id)}
            toplevelname_index      # {lang -> ilk -> toplevelname -> res_id -> blobnames}
            toplevelprefix_index    # {lang -> ilk -> prefix -> res_id -> toplevelnames}
            <safe-lang>/
                <dbfiles>

        # Codeintel includes .cix files for a number of language stdlibs
        # (all in "codeintel2/stdlibs/<lang>[-<ver>].cix"). These are
        # loaded here (as needed). 
        stdlibs/
            res_index                   # cix-path -> last-updated
            vers_and_names_from_lang(lang) # ordered list of (ver, name)
            <stdlib-name>/
                blob_index              # {blobname -> dbfile}
                toplevelname_index      # {ilk -> toplevelname -> blobnames}
                toplevelprefix_index    # {ilk -> prefix -> toplevelnames}
                <dbfiles>

        # Language-specific zones (data for all scanned resources that
        # don't belong to a project).  Sub-separation is done by source
        # dir to not have too many dbfiles in a directory and to match
        # the fact the import lookup is generally by dir.
        # Note: the 'toplevelname_index' is to support
        # "import-everything" semantics (i.e. lib.hits_from_lpath()).
        <safe-lang-name>/
            lang
            <dir-hash>/                 # md5 of dir path
                path
                res_index               # basename -> scan_time, scan_error,
                                        #             {blobname -> ilk -> toplevelnames}
                blob_index              # {blobname -> dbfile}
                toplevelname_index      # {ilk -> toplevelname -> blobnames}
                <dbfiles>
            ...

        # Multi-lang zones (e.g. RHTML has Ruby and JavaScript) differ a
        # little bit but are mostly the same as single-lang zones.
        <safe-multi-lang-name>/
            lang
            <dir-hash>/                 # md5 of dir path
                path
                res_index               # basename
                                        #   -> scan_time, scan_error,
                                        #      {lang -> blobname -> ilk -> toplevelnames}
                blob_index              # {lang -> blobname -> dbfile}
                toplevelname_index      # {lang -> ilk -> toplevelname -> blobnames}
                <dbfiles>

        # Project-support
        # (OBSOLETE, not used)
        projs/
            <proj-path-hash>/
                path                # project file path
                dirs_from_basename  # index of basenames in project
                update_time         #XXX time 'dirs_from_basename' last updated

                TODO: Eventually could have a project catalog made up
                      from '.cix' files in the project tree.


# Actions

Optimizing the following actions on the database determines the db
structure.

1. Add resource. [done by database updating: various places]
2. Remove resource. [done by database updating: various places]
3. Update resource. [done by database updating: various places]
4. Has blob (for a given lang). [done by import handling during
   completion eval]
5. Load blob. [done by import handling during completion eval]
6. Where is given top-level name defined.
7. What are the top-level names matching the given prefix and ilk.


# Logging

There are some logging rules for this module to support the test suite.
- All writes to the filesystem should have a log message that begins
  with "fs-write: ".
- All reads from the filesystem should have a log message that begins
  with "fs-read: ". (TODO)

Note: Currently only doing this for LangZone stuff. This will be easier
if/when add fs interaction is moved to one place (on the Database
class).


# TODO

- bullet proof all db interaction for fs failure, corruption, etc.
  (see notes in test2/test_db.py)
- add search_index for object browser functionality
- add torture tests for this
- investigate (1) removing 'lang' redundancy in DB where possible (shouldn't
  be necessary for single-lang libraries), (2) using lang-id's instead of
  the language name to improve perf.


# Database.clean() and .check() TODO

- dbfiles for paths viewed as another language will persist in the DB
  (although I think the index entries will have been removed). 
  These should be cleaned out.
- check for collisions in catalog: same lang, same blobname provided by
  two CIX files
"""

import sys
import os
from os.path import (join, dirname, exists, expanduser, splitext, basename,
                     split, abspath, isabs, isdir, isfile)
import cPickle as pickle
from cPickle import UnpicklingError
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
from codeintel2.util import dedent, safe_lang_from_lang, banner
from codeintel2.tree import tree_from_cix_path
from codeintel2.database.util import rmdir
from codeintel2.database.stdlib import StdLibsZone
from codeintel2.database.catalog import CatalogsZone
from codeintel2.database.langlib import LangZone
from codeintel2.database.multilanglib import MultiLangZone
from codeintel2.database.projlib import ProjectZone



#---- globals

log = logging.getLogger("codeintel.db")
#log.setLevel(logging.DEBUG)


#---- Database zone and lib implementations

class Database(object):
    """Manages the persistence data store for codeintel. This is a
    singleton instance, available from 'Manager().db'.

    The main data stored here is citree data for code blobs (i.e.
    importable modules). However, this intends to be usable for other
    types of data (e.g. things that might be useful for codeintel on
    non-programming languages like HTML, XML (e.g. schema info) and
    CSS).

    Dev Notes:
    - We'll start with just custom methods for different types of things
      and only "go generic" if it seems helpful.
    """
    # Database version.
    # VERSION is the version of this Database code. The property
    # "version" is the version of the database on disk. The patch-level
    # version number should be used for small upgrades to the database.
    #
    # db change log:
    # - 2.0.22: (Node.js core API documentation parser changes)
    # - 2.0.21: (PHP namespace top-level-name performance tweaks)
    # - 2.0.20: (PHP namespace class inheritance scanning)
    #   http://bugs.activestate.com/show_bug.cgi?id=84840
    # - 2.0.19: (Tcl statements include lassign)
    #   http://bugs.activestate.com/show_bug.cgi?id=75267
    # - 2.0.18: (PHP Alternative Control Syntax)
    #   http://bugs.activestate.com/show_bug.cgi?id=78957
    # - 2.0.17: (PHP variables) Parse complex variable definitions.
    #   http://bugs.activestate.com/show_bug.cgi?id=74625
    #   PHP stdlibs were also updated.
    # - 2.0.16: (PHP constants) Adding "ilk='constant'" attribute to
    #   PHP variables that are marked as constants.
    # - 2.0.15: (PHP/JS import-everything semantics.) Add
    #   "toplevelprefix_index" to stdlibs and catalogs zones. Currently
    #   not adding this index for (multi)lang zones (see comment in
    #   LangTopLevelNameIndex.toplevel_cplns()).
    # - 2.0.14: (PHP/JS import-everything semantics.) Update
    #   "toplevelname_index" for multilang, stdlibs and catalogs zones.
    # - 2.0.13: (PHP/JS import-everything semantics.) Update
    #   "toplevelname_index" for lang zone.
    # - 2.0.12: Only generate "toplevelname_index" for some langs. Use
    #   ".blob" extension for blobs in StdLibsZone. Use "blob_index" in
    #   StdLibsZone (as with other zones). Support "toplevelname_index"
    #   in StdLibsZone.
    # - 2.0.11: Update (Multi)LangZone's with "toplevelname_index" to
    #   support "import everything" semantics.
    # - 2.0.10: Manually adding a "src" attribute to blobs in
    #   (Multi)LangZone's. Needed for "Goto Definition" in determining
    #   file location.
    # - 2.0.9: 'blob_index' renamings in (Multi)LangZone's in prep for
    #   `lib.hits_from_lpath()' implementations.
    # - 2.0.8: Add catalog 'name' to CatalogsZone res_index. Needed for
    #   proper filtering on selection in CatalogsZone.update().
    # - 2.0.7: refactor to CatalogsZone and db/catalogs/... (i.e., plural)
    # - 2.0.6: Catalog zone updates to support catalog selection.
    # - 2.0.5: Fix to <bhash>.lpaths determination for JS. Only affected
    #   catalog zone.
    # - 2.0.4: Updates to catalog-zone indeces for "top-level names"
    #   caching (to support fast .hits_from_lpath()).
    # - 2.0.3: Add ".blob" to dbfile filenames in preparation for
    #   persisted cache keys (which will be stored as <bhash>.<key>
    #   next to the <bhash>.blob).
    # - 2.0.2: added scan_error to res_index in LangZone and MultiLangZone,
    #   add "lang" file to lang zones for reverse safe_lang -> lang lookup
    # - 2.0.1: s/VERSION.txt/VERSION/, made PHP a MultiLangZone
    VERSION = "2.0.22"

    LEN_PREFIX = 3 # Length of prefix in 'toplevelprefix_index' indeces.

    # Possible return values from .upgrade_info().
    (UPGRADE_NOT_NECESSARY,
     UPGRADE_NOT_POSSIBLE,
     UPGRADE_NECESSARY) = range(3)

    def __init__(self, mgr, base_dir=None, catalog_dirs=None,
                 event_reporter=None,
                 import_everything_langs=None):
        """
            "base_dir" (optional) specifies the base directory for
                the codeintel database. If not given it will default to
                '~/.codeintel'.
            "catalog_dirs" (optional) is a list of catalog dirs in
                addition to the std one to use for the CatalogsZone. All
                *.cix files in a catalog dir are made available.
            "event_reporter" (optional) is a callback that will be called
                    event_reporter(<event-desc-string>)
                before "significant" long processing events in the DB. This
                may be useful to forward to a status bar in a GUI.
            "import_everything_langs" (optional) is a set of lang names
                for which the `lib.hits_from_lpath()' API should be
                supported. This method is typically used to support
                "import-everything" cpln eval semantics.  Supporting it
                requires the 'toplevelname_index' indeces which adds
                significant space and perf burdens. If not specified,
                only JavaScript and PHP are included in the set.
        """
        self.mgr = mgr
        self._lock = threading.RLock() # XXX Perhaps use per-zone locks?

        self._catalogs_zone = None
        self._stdlibs_zone = None
        self._lang_zone_from_lang = {}
        self._proj_zone_from_proj_path = weakref.WeakValueDictionary()

        if base_dir is None:
            self.base_dir = expanduser(join("~", ".codeintel"))
        elif not isabs(base_dir):
            self.base_dir = abspath(base_dir)
        else:
            self.base_dir = base_dir
        
        self.catalog_dirs = catalog_dirs
        self.event_reporter = event_reporter

        if import_everything_langs is None:
            self.import_everything_langs = set(["JavaScript", "PHP"])
        else:
            self.import_everything_langs = import_everything_langs
        assert isinstance(self.import_everything_langs, set)

        self.corruptions = [] # list of noted errors during db operation

    def acquire_lock(self):
        self._lock.acquire()
    def release_lock(self):
        self._lock.release()

    @property
    def version(self):
        """Return the version of the db on disk (or None if cannot
        determine).
        """
        path = join(self.base_dir, "VERSION")
        try:
            fin = open(path, 'r')
        except EnvironmentError, ex:
            return None
        try:
            return fin.read().strip()
        finally:
            fin.close()

    def upgrade_info(self):
        """Returns information indicating if a db upgrade is necessary
        and possible.
        
        Returns one of the following:
            (UPGRADE_NOT_NECESSARY, None)
            (UPGRADE_NOT_POSSIBLE, "<reason>")
            (UPGRADE_NECESSARY, None)
        """
        if self.version == self.VERSION:
            return (Database.UPGRADE_NOT_NECESSARY, None)
        # Presuming that we *have* an upgrade path from the current
        # version.
        return (Database.UPGRADE_NECESSARY, None)

    def create(self):
        log.info("create db in `%s'", self.base_dir)
        self.acquire_lock()
        try:
            log.debug("fs-write: create db skeleton in '%s'", self.base_dir)
            if not exists(self.base_dir):
                os.makedirs(self.base_dir)
            open(join(self.base_dir, "README.txt"), 'w').write(dedent("""
                This is a database for the Code Intelligence system (a
                subsystem of SublimeCodeIntel). Do NOT modify anything in here
                unless you know what you are doing.

                See http://github.com/Kronuz/SublimeCodeIntel for details.
            """))
            open(join(self.base_dir, "VERSION"), 'w').write(self.VERSION)
            config_file = join(self.base_dir, "config")
            if not exists(config_file):
                open(config_file, 'w').write("{}")
            os.mkdir(join(self.base_dir, "db"))
        finally:
            self.release_lock()

    def reset(self, backup=True):
        """Move the given database out of the way to make way for a new one.

            "backup" (optional, default True) is a boolean indicating if
                the original database should be backed up. If so, the backup
                is $base_dir+".err".
        """
        self.acquire_lock()
        try:
            if exists(self.base_dir):
                #TODO: make this more bullet proof
                if backup:
                    err_base_dir = self.base_dir + ".err"
                    log.info("backing up db to '%s'", err_base_dir)
                    if os.path.exists(err_base_dir):
                        rmdir(err_base_dir)
                        for i in range(10): # Try to avoid OSError from slow-deleting NTFS
                            if not os.path.exists(err_base_dir): break
                            time.sleep(1)
                    if os.path.exists(err_base_dir): # couldn't remove it
                        log.warn("couldn't remove old '%s' (skipping backup)",
                                 err_base_dir)
                        rmdir(self.base_dir)
                    else:
                        os.rename(self.base_dir, err_base_dir)
                else:
                    rmdir(self.base_dir)

            self.create()
        finally:
            self.release_lock()

    def upgrade(self):
        """Upgrade the current database.
        
        Typically this is only called if .upgrade_info() returns
        UPGRADE_NECESSARY.
        """
        self.acquire_lock()
        try:
            # 'version' is the DB ver on disk, 'VERSION' is the target ver.
            curr_ver = self.version
            while curr_ver != self.VERSION:
                try:
                    result_ver, upgrader, upgrader_arg \
                        = self._result_ver_and_upgrader_and_arg_from_curr_ver[curr_ver]
                except KeyError:
                    raise DatabaseError("cannot upgrade from db v%s: no "
                                        "upgrader for this version"
                                        % curr_ver)
                log.info("upgrading from db v%s to db v%s ...",
                         curr_ver, result_ver)
                if upgrader_arg is not None:
                    upgrader(self, curr_ver, result_ver, upgrader_arg)
                else:
                    upgrader(self, curr_ver, result_ver)
                curr_ver = result_ver
        finally:
            self.release_lock()

    def _upgrade_wipe_db(self, curr_ver, result_ver):
        """Sometimes it is justified to just wipe the DB and start over."""
        assert result_ver == self.VERSION
        if exists(self.base_dir):
            log.debug("fs-write: wipe db")
            rmdir(self.base_dir)
        self.create()

    def _upgrade_wipe_db_catalogs(self, curr_ver, result_ver):
        catalog_dir = join(self.base_dir, "db", "catalogs")
        if exists(catalog_dir):
            log.debug("fs-write: wipe db/catalogs")
            rmdir(catalog_dir)
        open(join(self.base_dir, "VERSION"), 'w').write(result_ver)

    def _upgrade_wipe_db_langzones(self, curr_ver, result_ver):
        for lang in self._gen_langs_in_db():
            safe_lang = safe_lang_from_lang(lang)
            langzone_dir = join(self.base_dir, "db", safe_lang)
            if exists(langzone_dir):
                log.debug("fs-write: wipe db/%s", safe_lang)
                rmdir(langzone_dir)
        open(join(self.base_dir, "VERSION"), 'w').write(result_ver)

    def _upgrade_wipe_db_langs(self, curr_ver, result_ver, langs):
        for lang in langs:
            safe_lang = safe_lang_from_lang(lang)
            # stdlibs zone
            self.get_stdlibs_zone().remove_lang(lang)

            # API catalogs zone
            #TODO: CatalogsZone needs a .remove_lang(). Until then we just
            #      remove the whole thing.

            # (multi)langzone
            langzone_dir = join(self.base_dir, "db", safe_lang)
            if exists(langzone_dir):
                log.debug("fs-write: wipe db/%s", safe_lang)
                rmdir(langzone_dir)

        catalog_dir = join(self.base_dir, "db", "catalogs")
        if exists(catalog_dir):
            log.debug("fs-write: wipe db/catalogs")
            rmdir(catalog_dir)

        open(join(self.base_dir, "VERSION"), 'w').write(result_ver)

    _result_ver_and_upgrader_and_arg_from_curr_ver = {
        None: (VERSION, _upgrade_wipe_db, None),
        "2.0.1": (VERSION, _upgrade_wipe_db, None),
        "2.0.2": (VERSION, _upgrade_wipe_db, None),
        "2.0.3": (VERSION, _upgrade_wipe_db, None),
        "2.0.4": (VERSION, _upgrade_wipe_db, None),
        "2.0.5": (VERSION, _upgrade_wipe_db, None),
        "2.0.6": (VERSION, _upgrade_wipe_db, None),
        "2.0.7": (VERSION, _upgrade_wipe_db, None),
        "2.0.8": (VERSION, _upgrade_wipe_db, None),
        "2.0.9": (VERSION, _upgrade_wipe_db, None),
        "2.0.10": (VERSION, _upgrade_wipe_db, None),
        "2.0.11": (VERSION, _upgrade_wipe_db, None),
        "2.0.12": (VERSION, _upgrade_wipe_db, None),
        "2.0.13": (VERSION, _upgrade_wipe_db, None),
        # Techically only needed to wipe 'stdlibs' and 'catalogs' for
        # PHP and JavaScript, but this is easier.
        "2.0.14": (VERSION, _upgrade_wipe_db, None),
        "2.0.15": (VERSION, _upgrade_wipe_db_langs, ["PHP"]),
        "2.0.16": (VERSION, _upgrade_wipe_db_langs, ["PHP"]),
        "2.0.17": (VERSION, _upgrade_wipe_db_langs, ["PHP"]),
        "2.0.18": (VERSION, _upgrade_wipe_db_langs, ["Tcl"]),
        "2.0.19": (VERSION, _upgrade_wipe_db_langs, ["PHP"]),
        "2.0.20": (VERSION, _upgrade_wipe_db_langs, ["PHP"]),
        "2.0.21": (VERSION, _upgrade_wipe_db_langs, ["Node.js"]),
    }

    def report_event(self, desc):
        """Report a "significant" event in database processing.

        Various parts of the database can call this with a string
        description before performing some significant event. If
        this database was created with an event-reporter callback
        then it will be passed on.

        Guidelines:
        - report an event before doing a *long* action (e.g. importing a
          stdlib CIX file)
        """
        log.info("event: %s", desc)
        if self.event_reporter:
            try:
                self.event_reporter(desc)
            except Exception, ex:
                log.exception("error calling event reporter: %s", ex)

    def save(self):
        # Dev Notes:
        # - This is being called by the Manager.finalize().
        # - Don't need to call .save() for StdLibsZone because it saves
        #   immediately when updating (lazily on first use).
        # - XXX The plan is that a bookkeeper thread should also
        #   periodically call this.
        if self._catalogs_zone:
            self._catalogs_zone.save()
        for lang_zone in self._lang_zone_from_lang.values():
            lang_zone.save()

    def cull_mem(self):
        #XXX Not yet being called. The plan is that a bookkeeper thread
        #    should periodically call this.
        if self._catalogs_zone:
            self._catalogs_zone.cull_mem()
        for lang_zone in self._lang_zone_from_lang.values():
            lang_zone.cull_mem()

    _non_lang_db_dirs = ["catalogs", "stdlibs", "projs"]
    def _gen_langs_in_db(self):
        for d in os.listdir(join(self.base_dir, "db")):
            if d in self._non_lang_db_dirs:
                continue
            lang_path = join(self.base_dir, "db", d, "lang")
            if not exists(lang_path):
                log.warn("unexpected lang-zone db dir without 'lang' file: "
                         "`%s' (skipping)" % dirname(lang_path))
                continue
            fin = open(lang_path, 'r')
            try:
                lang = fin.read().strip()
            finally:
                fin.close()
            yield lang

    # Unused yet.
    def clean(self):
        """Clean out any expired/old codeintel information."""
        # TODO: Do other zones need cleaning?
        for lang in self._gen_langs_in_db():
            if not self.mgr.is_citadel_lang(lang):
                continue
            lang_zone = self._get_lang_zone(lang)
            lang_zone.clean()

    def check(self):
        """Return a list of internal consistency errors (if any) for the
        database.
        """
        errors = []

        for corruption in self.corruptions:
            errors.append("database corruption during '%s': %s (resolution: %s)"
                          % corruption)

        if self.version != self.VERSION:
            errors.append("VERSION mismatch: current DB version, '%s', is "
                          "not the latest, '%s'"
                          % (self.version, self.VERSION))

        errors += self._check_catalogszone()

        #TODO: check stdlibs zone

        for lang in self._gen_langs_in_db():
            if not self.mgr.is_citadel_lang(lang):
                continue
            lang_zone = self._get_lang_zone(lang)
            if not exists(lang_zone.base_dir):
                continue
            if isinstance(lang_zone, MultiLangZone):
                errors += self._check_multilangzone(lang_zone)
            else:
                errors += self._check_langzone(lang_zone)

        projs_dir = join(self.base_dir, "db", "projs")
        if exists(projs_dir):
            for dir in [join(projs_dir, d) for d in os.listdir(projs_dir)]:
                if not isdir(dir):
                    continue
                errors += self._check_proj_dir(dir)

        return errors

    def _check_catalogszone(self):
        log.debug("check catalogs zone...")
        #TODO: check toplevelname_index
        errors = []
        catalogs_zone = self.get_catalogs_zone()
        cix_path_from_res_id = {}
        for cix_path, res_data in catalogs_zone.res_index.items():
            res_id, last_updated, name, toplevelnames_from_blobname_from_lang \
                = res_data
            if res_id in cix_path_from_res_id:
                errors.append("catalogs zone: res_id %s used for both "
                              "'%s' and '%s'", cix_path_from_res_id[res_id],
                              cix_path)
            cix_path_from_res_id[res_id] = cix_path
        return errors

    def _check_proj_dir(self, proj_dir):
        log.debug("check '%s' proj zone...", basename(proj_dir))
        errors = []
        path_path = join(proj_dir, "path")
        if not exists(path_path):
            errors.append("proj zone: '%s/path' datafile does not exist"
                          % basename(proj_dir))
        return errors

    def _check_langzone(self, lang_zone):
        # Each blobname in the 'res_index' should have an entry and
        # dbfile in 'blob_index'.
        log.debug("check '%s' lang zone...", lang_zone.lang)
        errors = []

        for d in os.listdir(lang_zone.base_dir):
            if not isdir(join(lang_zone.base_dir, d)):
                continue

            path_path = join(lang_zone.base_dir, d, "path")
            if not exists(path_path):
                errors.append("%s lang zone: 'path' datafile does not "
                              "exist in '%s' dbdir" % (lang_zone.lang, d))
                path = d
            else:
                path = codecs.open(path_path, encoding="utf-8").read()
            res_index = lang_zone.load_index(path, "res_index", {})
            blob_index = lang_zone.load_index(path, "blob_index", {})
            #TODO
            #toplevelname_index = lang_zone.load_index(
            #        path, "toplevelname_index", {})

            all_blobnames = {}
            for filename, (scan_time, scan_error, res_data) \
                    in res_index.items():
                # res_data: {blobname -> ilk -> toplevelnames}
                for blobname in res_data:
                    if blobname in all_blobnames:
                        errors.append("%s lang zone: blob '%s' provided "
                                      "by more than one file in '%s' dir"
                                      % (lang_zone.lang, blobname, path))
                        continue
                    all_blobnames[blobname] = True
                    try:
                        dbfile = blob_index[blobname]
                    except KeyError:
                        errors.append(
                            "%s lang zone: blob '%s' provided by '%s' is "
                            "not in '%s/blob_index' index" 
                            % (lang_zone.lang, blobname,
                               join(path, filename), d))
                        continue
                    if not exists(join(lang_zone.base_dir, d, dbfile+".blob")):
                        errors.append(
                            "%s lang zone: dbfile for blob '%s' provided "
                            "by '%s' does not exist (%s)"
                            % (lang_zone.lang, blobname,
                               join(path, filename),
                               join(d, dbfile)))
                    # Note: Could check that the dbfile actually
                    # includes a valid tree providing the named
                    # blob. That would make .check() very slow for
                    # large db's though.

        return errors

    def _check_multilangzone(self, lang_zone):
        # Each blobname in the 'res_index' should have an entry and
        # dbfile in 'blob_index'.
        log.debug("check '%s' multilang zone...", lang_zone.lang)
        errors = []

        for d in os.listdir(lang_zone.base_dir):
            if not isdir(join(lang_zone.base_dir, d)):
                continue

            path_path = join(lang_zone.base_dir, d, "path")
            if not exists(path_path):
                errors.append("%s lang zone: 'path' datafile does not "
                              "exist in '%s' dbdir" % (lang_zone.lang, d))
                path = d
            else:
                path = codecs.open(path_path, encoding="utf-8").read()
            res_index = lang_zone.load_index(path, "res_index", {})
            blob_index = lang_zone.load_index(path, "blob_index", {})
            #toplevelname_index = lang_zone.load_index(
            #        path, "toplevelname_index", {})

            all_langs_and_blobnames = {}
            for filename, (scan_time, scan_error, res_data) \
                    in res_index.items():
                # res_data: {lang -> blobname -> ilk -> toplevelnames}
                for lang, blobname in (
                     (lang, tfifb.keys()[0]) # only one blob per lang in a resource
                     for lang, tfifb in res_data.items()
                    ):
                    if (lang, blobname) in all_langs_and_blobnames:
                        errors.append("%s lang zone: %s blob '%s' provided "
                                      "by more than one file in '%s' dir"
                                      % (lang_zone.lang, lang, blobname, path))
                        continue
                    all_langs_and_blobnames[(lang, blobname)] = True
                    try:
                        dbfile = blob_index[lang][blobname]
                    except KeyError:
                        errors.append(
                            "%s lang zone: %s blob '%s' provided by '%s' is "
                            "not in '%s/blob_index'" 
                            % (lang_zone.lang, lang, blobname,
                               join(path, filename), d))
                        continue
                    if not exists(join(lang_zone.base_dir, d, dbfile+".blob")):
                        errors.append(
                            "%s lang zone: dbfile for %s blob '%s' provided "
                            "by '%s' does not exist (%s)"
                            % (lang_zone.lang, lang, blobname,
                               join(path, filename), join(d, dbfile)))
                    # Note: Could check that the dbfile actually
                    # includes a valid tree providing the named
                    # blob. That would make .check() very slow for
                    # large db's though.

        return errors

    def corruption(self, action, desc, resolution):
        """Note a corruption in the database during operation.

            "action" is a string describing during what db action was
                being done when the corruption was discovered. Typically
                this is the method name.
            "desc" is a description of the corruption.
            "resolution" is a description of what was done to resolve or
                work-around the problem. Common resolutions:
                    'ignore'    work around the prob and continue on
                    'recover'
                    'remove buf data'

        This is called by internal database handlers.
        """
        log.warn("database corruption during '%s': %s (resolution: %s)",
                 action, desc, resolution)
        self.corruptions.append( (action, desc, resolution) )

    def get_catalogs_zone(self):
        if self._catalogs_zone is None:
            self._catalogs_zone = CatalogsZone(self.mgr, self.catalog_dirs)
        return self._catalogs_zone

    def get_catalog_lib(self, lang, selections=None):
        """Get a lang-specific handler for the catalog of loaded CIX files.
        
            "lang" is the language.
            "selections" (optional) is a set of catalog names (or full
                path to the CIX files) to use.  Essentially it is a
                filter.  If not specified, all available catalogs for
                this language are used. Otherwise only the selected
                catalogs are used. A catalog "name" is the
                (case-normalized) basename of the .cix file.
        """
        return self.get_catalogs_zone().get_lib(lang, selections)

    def get_stdlibs_zone(self):
        if self._stdlibs_zone is None:
            self._stdlibs_zone = StdLibsZone(self)
        return self._stdlibs_zone

    def get_stdlib(self, lang, ver=None):
        """Get a stdlib zone for the given language and version.

        On first get of a stdlib for a particular language, all
        available stdlibs for that lang are updated, if necessary.
        """
        return self.get_stdlibs_zone().get_lib(lang, ver)

    def _get_lang_zone(self, lang):
        if lang not in self._lang_zone_from_lang:
            if self.mgr.is_multilang(lang):
                self._lang_zone_from_lang[lang] = MultiLangZone(self.mgr, lang)
            else:
                self._lang_zone_from_lang[lang] = LangZone(self.mgr, lang)
        return self._lang_zone_from_lang[lang]

    def get_lang_lib(self, lang, name, dirs, sublang=None):
        """Get a language-specific zone handler for the given
        directories.

            "lang" is the language name, e.g. "Python".
            "name" is a user-friendly name for this particular lang-lib,
                e.g. "envlib" for set of dirs in PYTHONPATH or "sitelib"
                for the dirs in the Perl sitelib. This name is just used
                for logging and debugging.
            "dirs" is the ordered set of directories in this lib.
            "sublang" is used for multi-lang libs to indicate
                sub-language for which lookups will be done. For
                example, to get a PHP lang lib for which .has_blob()
                will search for PHP content (rather than JavaScript)
                sublang must be 'PHP'.  (For single-lang libs
                this should be None.)
        """
        assert isinstance(dirs, (tuple, list))
        lang_zone = self._get_lang_zone(lang)
        if isinstance(lang_zone, MultiLangZone):
            return lang_zone.get_lib(name, dirs, sublang)
        else:
            return lang_zone.get_lib(name, dirs)

    def get_proj_zone(self, proj):
        """Get a project zone handler for the given project.

            "proj" is an object representing the project. It should have
                the following interface:
                    proj.path       path to project file
                TODO: determine needed interface
        """
        proj_path = proj.path
        proj_zone = self._proj_zone_from_proj_path.get(proj_path)
        if proj_zone is None:
            proj_zone = ProjectZone(self.mgr, self, proj)
            self._proj_zone_from_proj_path[proj_path] = proj_zone
        return proj_zone

    def get_proj_lib(self, proj, lang):
        return self.get_proj_zone(proj).get_lib(lang)

    def load_blob(self, dbsubpath):
        """Load the blob and all persisted blob cache keys from disk."""
        log.debug("fs-read: load blob `%s'", dbsubpath[len(self.base_dir)+1:])
        blob = ET.parse(dbsubpath+".blob").getroot()
        blob_files = glob(dbsubpath+".*")
        for blob_cache_file in blob_files:
            ext = splitext(blob_cache_file)[1]
            if ext == ".blob": continue # this is the blob ET itself
            cache_key = ext[1:]
            try:
                blob.cache[cache_key] = self.load_pickle(blob_cache_file)
            except (UnpicklingError, ImportError), ex:
                log.warn("error unpickling `%s' (skipping): %s",
                         blob_cache_file, ex)
        return blob

    def load_pickle(self, path, default=None):
        """Load the given pickle path.

        Note that attempting to unpickle a non-pickle file can raise
        cPickle.UnpicklingError or ImportError. For example:
            >>> import cPickle as pickle
            >>> pickle.load(open("foo.txt", 'rb'))
            Traceback (most recent call last):
              File "<stdin>", line 1, in ?
            ImportError: No module named odeintel: INFO: eval 'raven' at raven.py#29
        """
        if exists(path):
            log.debug("fs-read: load pickle `%s'", path[len(self.base_dir)+1:])
            fin = open(path, 'rb')
            try:
                return pickle.load(fin)
            finally:
                fin.close()
        elif default is not None:
            return default
        else:
            raise OSError("`%s' does not exist" % path)

    def save_pickle(self, path, obj):
        if not exists(dirname(path)):
            log.debug("fs-write: mkdir '%s'",
                      dirname(path)[len(self.base_dir)+1:])
            try:
                os.makedirs(dirname(path))
            except OSError, ex:
                log.warn("error creating `%s': %s", dirname(path), ex)
        log.debug("fs-write: '%s'", path[len(self.base_dir)+1:])
        fout = open(path, 'wb')
        try:
            pickle.dump(obj, fout, 2)
        finally:
            fout.close()


    #---- Convenience methods for getting database hash keys.
    # MD5 hexdigests are used to generate keys into the db (typically
    # file paths).

    #TODO:PERF: evaluate perf improvement with caching of this
    def bhash_from_blob_info(self, res_path, lang, blobname):
        """Return a unique name for a blob dbfile.
        
        This is used as the filename for the dbfile for this blob.
        """
        s = ':'.join([res_path, lang, blobname])
        if isinstance(s, unicode):
            s = s.encode(sys.getfilesystemencoding())
        return md5(s).hexdigest()

    #TODO:PERF: evaluate perf improvement with caching of this
    def dhash_from_dir(self, dir):
        """Return a hash path to use internally in the db for the given dir."""
        if isinstance(dir, unicode):
            dir = dir.encode(sys.getfilesystemencoding())
        return md5(dir).hexdigest()


    #---- The following are convenience methods for working with a
    #     particular LangZone and a buffer.
    
    def get_buf_scan_time(self, buf):
        """Return the mtime for the given buffer in the database or
        return None.
        """
        return self._get_lang_zone(buf.lang).get_buf_scan_time(buf)

    def get_buf_data(self, buf):
        """Return the tree for the given buffer in the database or
        raise NotFoundInDatabase.
        """
        return self._get_lang_zone(buf.lang).get_buf_data(buf)

    def remove_buf_data(self, buf):
        """Remove data for this buffer from the database.

        If this resource isn't in the database, then this is a no-op.
        """
        self._get_lang_zone(buf.lang).remove_buf_data(buf)

    def update_buf_data(self, buf, scan_tree, scan_time, scan_error,
                        skip_scan_time_check=False):
        """Add or update data for this buffer into the database."""
        self._get_lang_zone(buf.lang).update_buf_data(
            buf, scan_tree, scan_time, scan_error,
            skip_scan_time_check=skip_scan_time_check)

