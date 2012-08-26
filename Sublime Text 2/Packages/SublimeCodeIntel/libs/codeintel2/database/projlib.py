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

import sys
import os
from os.path import (join, dirname, exists, expanduser, splitext, basename,
                     split, abspath, isabs, isdir, isfile)
import threading
from hashlib import md5
from pprint import pprint, pformat
import logging
import codecs
import weakref

from codeintel2.common import *



#---- globals

log = logging.getLogger("codeintel.db")



#---- Database zone and lib implementations

class ProjectZone(object):
    """Manage a 'db/projs/<proj-hash>/...' area of the database.

    A project zone works with a project object(*) to provide quick
    mapping of a (lang, blobname) to a file in the project, if any.

    # Dealing with updating

    Knowing when a file has been removed from a project is fairly easy:
    we hit it in the cache, then do a quick stat (or query on the
    project) to ensure it it still there.

    Knowing when a file has been added to a project is harder. Fully
    hooking into Komodo's file system-level dir watching and various
    in-Komodo update notifications is hard (doesn't translate well to
    simply requiring an API on the project object) and isn't perfect
    anyway. Ideally .dirs_from_basename() is all handled by the project
    object and we don't have to worry about it. However, Komodo Projects
    aren't currently setup to do this well, so codeintel is taking the
    burden of caching.

    The planned solution is to attempt a reasonable job of creating the
    dirs_from_basename cache and then providing a manual interface
    (perhaps right-click on Project -> "Refresh Status") to update.

    (*) The project object is required to have the following API:
        TODO: spec the API.
    """
    def __init__(self, mgr, db, proj):
        self.mgr = mgr
        self.db = db
        self.proj = proj

        self.name = basename(proj.path)
        self.base_dir = join(self.db.base_dir, "db", "projs", 
                             md5(proj.path).hexdigest())
        self._proj_lib_from_lang = weakref.WeakValueDictionary()
        self._idx_lock = threading.RLock()
        self._dirs_from_basename = None
        self._is_idx_dirty = False

    def __repr__(self):
        return "<proj '%s' zone>" % self.name

    def __del__(self):
        try:
            self.save()
        except:
            log.exception("error saving %s" % self)

    def get_dirs_from_basename(self):
        self._idx_lock.acquire()
        try:
            if self._dirs_from_basename is None:
                log.debug("fs-read: load %s 'dirs_from_basename' index", self)
                self._dirs_from_basename = self.db.load_pickle(
                    join(self.base_dir, "dirs_from_basename"), {})
            return self._dirs_from_basename
        finally:
            self._idx_lock.release()
    def set_dirs_from_basename(self, value):
        self._idx_lock.acquire()
        try:
            old_value = self.dirs_from_basename
            self._dirs_from_basename = value
            if old_value != value:
                #PERF: can this be smarter? Would have to be on
                #      .update() for that.
                self._is_idx_dirty = True
        finally:
            self._idx_lock.release()
    dirs_from_basename = property(get_dirs_from_basename,
        set_dirs_from_basename, None, "index of basenames in project")

    def _mk_dbdir(self):
        log.debug("fs-write: mkdir '%s'", self.base_dir)
        os.makedirs(self.base_dir)
        log.debug("fs-write: '%s/path'", self.base_dir)
        fout = codecs.open(join(self.base_dir, "path"), 'wb', 'utf-8')
        try:
            fout.write(self.proj.path)
        finally:
            fout.close()

    def save(self):
        self._idx_lock.acquire()
        try:
            if self._is_idx_dirty:
                if not exists(self.base_dir):
                    self._mk_dbdir()
                self.db.save_pickle(join(self.base_dir, "dirs_from_basename"),
                    self._dirs_from_basename)
                self._is_idx_dirty = False
        finally:
            self._idx_lock.release()

    def update(self, nice=False):
        """Update the index for the list of files in the project.

            "nice" (default False) is a boolean indicating if this
                update process should attempt to keep the CPU load low.
        """
        if nice:
            XXX
        #XXX Update this to handle includes, excludes,
        #    static-project-entries. I.e. move this logic to the
        #    project where it can handle this stuff.
        dirs_from_basename = {}
        for dirpath, dirnames, filenames in os.walk(self.proj.base_dir):
            for filename in filenames:
                dirs_from_basename.setdefault(filename, []).append(dirpath)
        self.dirs_from_basename = dirs_from_basename

    def _likely_filename_from_lang_and_blobname(self, lang, blobname):
        #XXX Need to canonicalize filename.
        #XXX Shouldn't be hardcoding this stuff here. Defer out to the
        #    lang_*.py modules.
        #XXX Do we have to worry about multi-level imports here? E.g.,
        #       Python:  os.path
        #       Perl:    LWP::UserAgent
        #       Ruby:    yaml/context
        #       PHP:     blah/blam.php
        if lang in ("Python", "Python3"):
            return blobname+".py"
        else:
            XXX

    def has_blob(self, lang, blobname):
        lang_lib = self._lang_lib_for_blob(lang, blobname)
        if lang_lib is None:
            return False
        return lang_lib.has_blob(blobname)

    def get_blob(self, lang, blobname):
        lang_lib = self._lang_lib_for_blob(lang, blobname)
        if lang_lib is None:
            return None
        return lang_lib.get_blob(blobname)

    def _lang_lib_for_blob(self, lang, blobname):
        filename = self._likely_filename_from_lang_and_blobname(lang, blobname)
        try:
            dirs = self.dirs_from_basename[filename]
        except KeyError:
            return None
        else:
            #XXX This may be a perf issue because of a possibly large
            #    number of created LangDirsLib's -- which was unexpected
            #    when the LangDirsLibs caching was designed on LangZone.
            #    The cache size may need to be increased or some other
            #    scheme considered.
            return self.db.get_lang_lib(lang, "proj '%s' lib" % self.name,
                                        dirs,
                                        sublang=lang) # for PHP

    def get_lib(self, lang):
        proj_lib = self._proj_lib_from_lang.get(lang)
        if proj_lib is None:
            proj_lib = ProjectLib(self, lang)
            self._proj_lib_from_lang[lang] = proj_lib
        return proj_lib

class ProjectLib(object):
    # Light lang-specific wrapper around a ProjectZone (akin to
    # CatalogLig).
    def __init__(self, proj_zone, lang):
        self.proj_zone = proj_zone
        self.lang = lang
    def __repr__(self):
        return "<proj '%s' %s lib>" % (self.proj_zone.name, self.lang)
    def has_blob(self, blobname):
        return self.proj_zone.has_blob(self.lang, blobname)
    def get_blob(self, blobname):
        return self.proj_zone.get_blob(self.lang, blobname)
