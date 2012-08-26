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

r"""Handling for citadel parts of CodeIntel.

The origin of the name "citadel": In early dev of codeintel naming for
various things generally began with "CI" for CodeIntel. The (simple) syntax
for defining type guesses (the things that are evaluated against the CIDB)
was (and is) called CITDL (CodeIntel Type Definition Language) -- pronounced
"citadel", in an attempt to be mnemonic. In dev for Komodo 4, the codeintel
system is being generalized to support languages that don't fit in the
CIDB/CITDL-framework so "citadel" is the umbrella term for CIDB/CITDL-based
stuff in the codeintel system.
"""

import os
from os.path import (isfile, isdir, exists, dirname, abspath, join, basename)
import sys
import logging
import time
import re
import traceback
import threading
from pprint import pprint

import ciElementTree as ET
import codeintel2
from codeintel2.buffer import Buffer
from codeintel2.common import *
from codeintel2.indexer import ScanRequest
from codeintel2.langintel import LangIntel
#from codeintel2.scheduler import BatchUpdater



#---- globals

log = logging.getLogger("codeintel.citadel")
#log.setLevel(logging.INFO)



#---- module interface

class CitadelLangIntel(LangIntel):
    """Shared smarts for "citadel"-language content.

    "Citadel" languages are those whose scanning and completion
    evaluation is based on CIDB/CITDL/CIX.
    """


class CitadelBuffer(Buffer):
    """Virtual base class for language Buffers whose completion evaluation
    is based on CIDB/CITDL/CIX.

    CitadelBuffers have the following additional API:
        .defns_from_pos(..) Returns a list of citdl expressions for position.
        .scan(...)          Force a scan of the buffer.
        .scan_time          Time of the last scan (or None if not in the db)
        .scan_error         A string describing why the last scan failed
                            (or None if it didn't fail or there hasn't
                            been a scan)
        .blob_from_lang     Mapping of language to blob (a.k.a. the
                            module Element). This will synchronously
                            scan if there is not scan data already
                            available.

        .tree/.cix          CIX Element tree and serialized CIX of this
                            buffer's scan data.

        .scoperef_from_pos()
        .scoperef_from_blob_and_line()
                            Routines for getting the current scope in
                            the blob scan data. Used for completion eval
                            and code browsing.

        # Two convenience routines for working with the db.
        .load()             Load data about this buffer into the db.
        .unload()           Remove data about this buffer from the db.

    """
    # Local cache for buf data that is stored in the db. Each one of
    # these has a property for access.
    _scan_time_cache = None
    _scan_error_cache = None
    _blob_from_lang_cache = None

    def __init__(self, *args, **kwargs):
        Buffer.__init__(self, *args, **kwargs)
        self._scan_lock = threading.RLock()

    # Scanning can happen on different threads so access to scan data
    # must be guarded.
    def acquire_lock(self):
        self._scan_lock.acquire()
    def release_lock(self):
        self._scan_lock.release()

    _have_checked_db = False
    def _load_buf_data_once(self, skip_once_check=False):
        """Get persisted data for this buffer from the db.
        Raises NotFoundInDatabase is not there.
        """
        if skip_once_check or not self._have_checked_db:
            self._have_checked_db = True
            self._scan_time_cache, self._scan_error_cache, \
                self._blob_from_lang_cache = self.mgr.db.get_buf_data(self)

    def defn_trg_from_pos(self, pos, lang=None):
        """Return a list of CI definitions for the CITDL expression
        at the given pos.
        """
        if lang is None:
            lang = self.lang
        return Trigger(lang, TRG_FORM_DEFN, "defn", pos, False, length=0)

    def defns_from_trg(self, trg, timeout=None, ctlr=None):
        self.async_eval_at_trg(trg, ctlr)
        ctlr.wait(timeout)
        if not ctlr.is_done():
            ctlr.done("timed out")
            ctlr.abort()
            raise EvalTimeout("eval for %s timed-out" % trg)
        return ctlr.defns # -> list of Definition's

    @property
    def scan_time(self):
        """The time of the last scan data. 
        
        This may be the time of the scan or the modification time of the
        buffer content at the last scan.  Typically this is set via the
        'mtime' optional argument to scan().

        This returns None if this file hasn't been scanned.
        """
        self.acquire_lock()
        try:
            if self._scan_time_cache is None:
                try:
                    self._load_buf_data_once()
                except NotFoundInDatabase:
                    pass
            return self._scan_time_cache
        finally:
            self.release_lock()

    @property
    def scan_error(self):
        "A string describing why the last scan failed, or None if it didn't."
        self.acquire_lock()
        try:
            if self._scan_error_cache is None:
                try:
                    self._load_buf_data_once()
                except NotFoundInDatabase:
                    pass
            return self._scan_error_cache
        finally:
            self.release_lock()

    @property
    def blob_from_lang(self):
        self.acquire_lock()
        try:
            if self._blob_from_lang_cache is None:
                try:
                    self._load_buf_data_once()
                except NotFoundInDatabase:
                    self.release_lock()
                    try:
                        self.scan()
                    finally:
                        self.acquire_lock()
                    self._load_buf_data_once(True)
            return self._blob_from_lang_cache
        finally:
            self.release_lock()

    @property
    def tree(self):
        """The CIX tree for this buffer. Will lazily scan if necessary."""
        self.acquire_lock()
        try:
            # SIDE-EFFECT: scan if necessary
            blob_from_lang = self.blob_from_lang

            tree = ET.Element("codeintel", version="2.0")
            path = self.path
            if os.sep != '/':
                path = path.replace(os.sep, '/')
            file = ET.SubElement(tree, "file", path=path,
                                 lang=self.lang,
                                 mtime=str(self._scan_time_cache))
            if self._scan_error_cache:
                file.set("error", self._scan_error_cache)
            if blob_from_lang:
                for lang, blob in sorted(blob_from_lang.items()):
                    file.append(blob)
            return tree
        finally:
            self.release_lock()

    @property
    def cix(self):
        """The CIX for this buffer. Will lazily scan if necessary."""
        return ET.tostring(self.tree)

    def scan(self, mtime=None, skip_scan_time_check=False):
        """Scan the current buffer.

            "mtime" is the modification time of the buffer content. If
                not given the current time will be used.

        The results are stored on the buffer to be retrieved via the
        scan_time/scan_error/blob_from_lang properties.
        """
        if self.path is None:
            raise CodeIntelError("cannot scan %s buffer: 'path' is not set (setting "
                                 "a fake path starting with '<Unsaved>' is okay)"
                                 % self.lang)

        cile_driver = self.mgr.citadel.cile_driver_from_lang(self.lang)
        if mtime is None:
            mtime = time.time()

        #TODO: Eventually would like the CILEDriver scan methods to have
        #      a signature more inline with
        #      blob_from_lang/scan_time/scan_error. I.e. drop
        #      <file error="..."> mechanism in favour of just raising
        #      CILEError.
        scan_tree = None
        try:
            scan_tree = cile_driver.scan_purelang(self)
        except CodeIntelError, ex:
            exc_info = sys.exc_info()
            exc_class, exc, tb = sys.exc_info()
            tb_path, tb_lineno, tb_func = traceback.extract_tb(tb)[-1][:3]
            scan_error = "%s (%s:%s in %s)" % (exc, tb_path, tb_lineno, tb_func)
        except Exception, ex:
            msg = "unexpected error scanning `%s'" % basename(self.path)
            log.exception(msg)
            exc_info = sys.exc_info()
            exc_class, exc, tb = sys.exc_info()
            tb_path, tb_lineno, tb_func = traceback.extract_tb(tb)[-1][:3]
            scan_error = "%s: %s (%s:%s in %s)"\
                         % (msg, exc, tb_path, tb_lineno, tb_func)
        else:
            scan_error = scan_tree[0].get("error")

        self.acquire_lock()
        try:
            self._scan_time_cache = mtime
            self._scan_error_cache = scan_error
        finally:
            self.release_lock()

        # Put it into the database.
        self.mgr.db.update_buf_data(self, scan_tree, mtime, scan_error,
                                    skip_scan_time_check=skip_scan_time_check)
        self._load_buf_data_once(True)

    def scoperef_from_pos(self, pos):
        """Return the scoperef for the given position in this buffer.

        A "scoperef" is a 2-tuple:
            (<blob>, <lpath>)
        where <blob> is the ciElementTree blob for the buffer content
        and <lpath> is an ordered list of names into the blob
        identifying the scope.
        
        For example, given this "foo.py":

            class Foo:
                baz = 42
                def bar(self):
                    print "bar bar!"

        the scoperef for the print line would be:

            (<Python blob 'foo'>, ["Foo", "bar"])

        If no relevant scope is found (e.g. for example, in markup
        content in PHP) then None is returned.
        """
        try:
            blob = self.blob_from_lang[self.lang]
        except KeyError:
            return None
        line = self.accessor.line_from_pos(pos) + 1 # convert to 1-based
        return self.scoperef_from_blob_and_line(blob, line)

    def scoperef_from_blob_and_line(self, blob, line): # line is 1-based
        lpath = []
        scope = blob
        while True:
            next_scope_could_be = None
            # PERF: Could make this a binary search if a scope has *lots* of
            # subscopes.
            for subscope in scope.findall("scope"):
                start = int(subscope.get("line"))
                if line < start:
                    break
                end = subscope.get("lineend") and int(subscope.get("lineend"))
                
                if end is not None:
                    if end < line:
                        next_scope_could_be = None
                    else:
                        next_scope_could_be = subscope
                else:
                    next_scope_could_be = subscope
            if next_scope_could_be is not None:
                lpath.append(next_scope_could_be.get("name"))
                scope = next_scope_could_be
            else:
                break
        return (blob, lpath)

    def scan_if_necessary(self):
        # SIDE-EFFECT: results in `self.scan()` if not in the db.
        self.blob_from_lang

    def unload(self):
        """Remove this buffer from the database."""
        self.mgr.db.remove_buf_data(self)

    #XXX Move citdl_expr_from_trg() here (see PythonBuffer)?


class BinaryBuffer(CitadelBuffer):
    def __init__(self, lang, mgr, env, path):
                                          #mgr, accessor, env, path, encoding
        self.lang = lang
        super(BinaryBuffer, self).__init__(mgr, None, env, path, None)
        
    def scan(self, mtime=None, skip_scan_time_check=False):
        if self.path is None:
            raise CodeIntelError("cannot scan %s buffer: 'path' is not set (setting "
                                 "a fake path starting with '<Unsaved>' is okay)"
                                 % self.lang)

        cile_driver = self.mgr.citadel.cile_driver_from_lang(self.lang)
        if mtime is None:
            mtime = time.time()

        scan_tree = None
        try:
            scan_tree = cile_driver.scan_binary(self)
        except CodeIntelError, ex:
            exc_info = sys.exc_info()
            exc_class, exc, tb = sys.exc_info()
            tb_path, tb_lineno, tb_func = traceback.extract_tb(tb)[-1][:3]
            scan_error = "%s (%s:%s in %s)" % (exc, tb_path, tb_lineno, tb_func)
        except Exception, ex:
            msg = "unexpected error scanning `%s'" % basename(self.path)
            log.exception(msg)
            exc_info = sys.exc_info()
            exc_class, exc, tb = sys.exc_info()
            tb_path, tb_lineno, tb_func = traceback.extract_tb(tb)[-1][:3]
            scan_error = "%s: %s (%s:%s in %s)"\
                         % (msg, exc, tb_path, tb_lineno, tb_func)
        else:
            scan_error = scan_tree[0].get("error")

        self.acquire_lock()
        try:
            self._scan_time_cache = mtime
            self._scan_error_cache = scan_error
        finally:
            self.release_lock()

        # Put it into the database.
        self.mgr.db.update_buf_data(self, scan_tree, mtime, scan_error,
                                    skip_scan_time_check=skip_scan_time_check)
        self._load_buf_data_once(True)
        
        #TODO: potential race condition here with Buffer.cached_sections().
        self._sections_cache = None

    def string_styles(self):
        return []
        
    def comment_styles(self):
        return []
        
    def number_styles(self):
        return []
        

class ImportHandler:
    """Virtual base class for language-specific "import"-statement handlers.
    
    The basic job of an import handler is to convert an import statement (i.e.
    a row in the 'import' table) into a row in the CIDB 'module' table. Doing
    this depends on language-specific import semantics.
    
    A fundamental part of import resolution is the search path. Here the
    search path is broken into three parts:
        - "core" path: built-in to the interpreter/compiler, generally
          dependent on the installation location.
        - "env" path: additional directories specified in a special
          environment variable, e.g. PYTHONPATH, PERL5LIB
        - "custom" path: additional "out-of-band" directories
    
    Each language-specific ImportHandler is a singleton as doled out by
    Citadel.import_handler_from_lang().
    """
    lang = None

    #DEPRECATED
    PATH_ENV_VAR = None
    corePath = None
    envPath = None
    customPath = None

    def __init__(self, mgr):
        self.mgr = mgr

    #DEPRECATED
    def setCustomPath(self, path):
        """Specify some custom search directories."""
        self.customPath = path

    #DEPRECATED
    def setEnvPath(self, value=None):
        """Specify the value of the PATH-style environment variable.
        
            "value" is the appropriate environment variable value, e.g.:
                "C:\trentm\mylib;C:\shared\lib-python". If value is None then
                the value will be retrieved from os.environ.

        This will lazily be called if necessary.
        """
        path = []
        if value is None:
            if self.PATH_ENV_VAR:
                path = os.environ.get(self.PATH_ENV_VAR, "").split(os.pathsep)
        else:
            path = value.split(os.pathsep)
        self.envPath = path

    #DEPRECATED
    def setCorePath(self, compiler=None, extra=None):
        """Specify the data needed to determine the core search path.
        
            "compiler" is the path to the language compiler/interpreter.
                If not specified then the first appropriate
                compiler/interpreter on the path is used.
            "extra" (optional) can be used to specify required extra
                data for determining the core import path.  For example,
                the PHP-specific implementation uses this to specify the
                "php.ini"-config-file path.

        This will lazily be called if necessary.
        """
        # Sub-classes must implement this and set self.corePath as a
        # result (to [] if it could not be determined).
        raise NotImplementedError("setCorePath: pure virtual method call")

    #DEPRECATED: still used by `genScannableFiles` implementations.
    def _getPath(self, cwd=None):
        """Put all the path pieces together and return that list.
        
        If "cwd" is specified, it is prepended to the list. (In many languages
        the directory of the file with the import statement is first on the
        module search path.)
        """
        if self.corePath is None: self.setCorePath()
        if self.envPath is None: self.setEnvPath()
        if cwd is not None:
            path = [cwd]
        else:
            path = []
        if self.customPath:
            path += self.customPath
        path += self.envPath
        path += self.corePath
        return path

    #DEPRECATED: Though still used in one place by `lang_ruby.py`.
    def findSubImportsOnDisk(self, module, cwd):
        """Return a list of importable submodules to the given module.
        
        The returned list is a list of strings that would be appropriate for
        direct use in the language's specific import statement. I.e.: for
        Perl:
            ["ConnCache", "Protocol", "UserAgent", ...]
        not:
            ["ConnCache.pm", "Protocol.pm", "UserAgent.pm", ...]
        For PHP, however, including the .php extension might be appropriate.
        """
        raise NotImplementedError("findSubImportsOnDisk: pure virtual method call")

    #DEPRECATED: `indexer.py` is still using this
    def genScannableFiles(self, path=None, skipRareImports=False,
                          importableOnly=False):
        """Generate scannable files on the import path.
        
            "path" (optional) is an import path to load. If not specified
                the default import path is used.
            "skipRareImports" (optional, default false) is a boolean
                indicating if files unlikely to be imported/searched-for/used
                should be skipped. This can be specified to speed up, for
                example, scanning *all* files during a batch update of a
                language installation.
            "importableOnly" (optional, default false) is a boolean
                indicating if only those files that are importable from
                the given path should be included. For example a Python
                file in a subdirectory cannot be imported if that dir
                does not have a package-defining "__init__.py" file.
        """
        raise NotImplementedError("genScannableFiles: pure virtual method call")

    #---- new citree-based eval stuff

    # The string that separates dir levels in import names. For example,
    # this would be '.' for Python (import foo.bar), '::' for Perl
    # (use Foo::Bar;), '/' for Ruby, etc. Must be set for each language.
    sep = None
    
    def find_importables_in_dir(self, dir):
        """Return a mapping of
            import-name -> (path, subdir-import-name, is-dir-import)
        for all possible importable "things" in the given dir. Each part
        is explained below.
        
        The "import-name" is the string that you'd use in the particular
        language's import statement:
                        import statement        import-name     path
                        ----------------        -----------     ----
            Python:     import foo              foo             foo.py
            Perl:       use Foo;                Foo             Foo.pm
            Ruby:       require 'foo'           foo             foo.rb
            PHP:        require("foo.php")      foo.php         foo.php
                        require("foo.inc")      foo.inc         foo.inc
        
        For the simple case of a directly imported file in this dir, the
        "subdir-import-name" isn't relevant so None is used:
            Python:     "foo": ("foo.py", None, ...)
            Perl:       "Foo": ("Foo.pm", None, ...)
            Ruby:       "foo": ("foo.rb", None, ...)
            PHP:        "foo.php": ("foo.php", None, ...)
                        "foo.inc": ("foo.inc", None, ...)

        In addition to importable files in the given dir, this function
        must also provide the link to imports in *sub-directories*.  In
        Python a special "__init__.py" in subdirs is actually imported
        when a dir is specified. Here the "subdir-import-name" becomes
        relevant:
            Python:     "bar": ("bar/__init__.py", "__init__", False)

        In most languages there isn't a special file to indicate this.
        However the dir name *can* appear as part of an import
        statement. The "is-dir-import" boolean is used to indicate that
        the "import-name" can be used as part of a multi-level import
        statement:
            Perl:       "Bar": (None, None, True)
            Ruby:       "bar": (None, None, True)
            PHP:        "bar": (None, None, True)

        Some of these latter languages occassionally have an importable
        file *and* a sub-directory of the same name.
            Perl:       LWP.pm and LWP/... in the stdlib
            Ruby:       shell.rb and shell/... in the stdlib
        In these cases:
            Perl:       "LWP": ("LWP.pm", None, True)
            Ruby:       "shell": ("shell.rb", None, True)

        """
        raise NotImplementedError("find_importables_in_dir: virtual method")
    
    def import_blob_name(self, import_name, libs, ctlr):
        """Return the blob tree for the given import name and libs.

            "import_name" is the name used in the language's
                import/use/require statement under which blob
                information is generally keyed in the database.
            "libs" is an order list of libraries in which to search for
                the blob. See database/database.py's module docstring
                for info on the Library API.
            "ctlr" is the EvalController instance. Logging is done
                on this, and ctlr.is_aborted() may be used to abort
                processing.
        """
        for lib in libs:
            blob = lib.get_blob(import_name)
            if blob is not None:
                ctlr.info("is blob '%s' from %s? yes", import_name, lib)
                return blob
            else:
                ctlr.info("is blob '%s' from %s? no", import_name, lib)
        else:
            raise CodeIntelError("could not find data for %s blob '%s'"
                                 % (self.lang, import_name))



class CitadelEvaluator(Evaluator):
    """A Citadel evaluator -- i.e. the guy that knows how to translate
    a CITDL expression into a list of completions or a calltip.
    """
    citadel = None
    have_requested_reeval_already = False # sentinel to trap infinite loop

    def __init__(self, ctlr, buf, trg, expr, line):
        Evaluator.__init__(self, ctlr, buf, trg)
        self.lang = buf.lang #XXX should use trg.lang instead (multi-lang differs)
        self.path = buf.path
        self.cwd = dirname(self.path)
        self.expr = expr #XXX should be rigorous and use citdl_expr
        self.line = line # 0-based

    def __str__(self):
        return "'%s' at %s#%s" % (self.expr, basename(self.path), self.line+1)

    def post_process_cplns(self, cplns):
        """Hook for sub-classes to post-process the list of completions.
        
        Implementations may modify the list in place.
        
        Note that a common operation that all implementations should
        generally do (and the default impl. *does*) is to sort the list
        of completions case-insensitively by value and with punctuation
        characters sorting last (see bug 77954). Sorting is necessary
        to have type-ahead-find work properly in Scintilla's autocomplete
        UI and case-insensitive sorting is necessary if using Scintilla's
        SCI_AUTOCSETIGNORECASE(true) -- which Komodo is.
        """
        from codeintel2.util import OrdPunctLast
        cplns.sort(key=lambda c: OrdPunctLast(c[1]))
        return cplns

    def post_process_calltips(self, calltips):
        """Hook for sub-classes to post-process the list of calltips.
        
        Implementations may modify the list in place.
        """
        return calltips

    def post_process_defns(self, defns):
        """Hook for sub-classes to post-process the list of defns.
        
        Implementations may modify the list in place.
        """
        return defns

    def request_reeval(self):
        """Used for an on_complete callback to CitadelBuffer.scan_and_load()."""
        assert not self.have_requested_reeval_already, \
            "invalid eval usage: cannot request re-eval more than once"
        self.have_requested_reeval_already = True

        if self.ctlr.is_aborted():
            self.ctlr.done("aborting")
            return
        self.ctlr.info("request re-eval of %s", self)
        self.mgr.request_reeval(self)

    def import_resolution_failure(self, name, path):
        """Called by import-resolution code to offer ability to react to
        a module import not resolving in the CIDB.
        
        The nice-to-have plan was to request a scan of this module and then
        re-evaluate at this trigger when that was finished. If well behaved
        this would give the best completion GOOBE to the user: the first
        time may be slow, but it just works.

        PUNTing on that for now because (1) of fear of this not being
        well-behaved: repeated (and hence performance intensive) attempted
        scanning of a module that doesn't quite make it into to the CIDB.
        Could monitor that with a "3 strikes" rule or something. Also (2),
        the *real* solution should involve re-scanning of modules that
        are newer than our scan info. This logic belongs on a Buffer for
        that module (or something). Revisit when/if refactoring codeintel
        the next time through.
        """
        self.ctlr.warn("no info on import '%s'", name)
        #log.warn("XXX Currently not reacting to import resolution failure. "
        #         "Try to do that later. (path=%s)" % path)


    #---- the guts of the evaluation

    def debug(self, msg, *args):
        self.ctlr.debug(msg, *args)
    def info(self, msg, *args):
        self.ctlr.info(msg, *args)
    def warn(self, msg, *args):
        self.ctlr.warn(msg, *args) #XXX why was this "info"?
    def error(self, msg, *args):
        self.ctlr.error(msg, *args)


class Citadel(object):
    """The manager of Citadel-parts of the CodeIntel system. This is a
    singleton canonically available from Manager.citadel.
    
    Usage
    -----

    Typically all interaction with a Citadel is done via a Manager instance.
    Here is what the Manager should be doing.

        citadel = Citadel(mgr, ...)
        
        #XXX Obsolete
        # Upgrade the CIDB, if necessary via appropriate usage of:
        #   .cidb_upgrade_info()
        #   .upgrade_cidb()
        #   .reset_cidb()

        citadel.initialize()

        # Use the citadel. The most common methods are:
        #   .{add|stage}_scan_request()
        # and making batch updates (described below).

        # Must be finalized to ensure no thread hangs.
        citadel.finalize()

    Making Batch Updates
    --------------------
    
        citadel.batch_update_request(...) # make one or more request
        citadel.batch_update_start(...)   # start the update

    By default .batch_update_start() will block until the update is complete.
    This (and other control of the update process) can be customized by
    passing in your own controller.
    """
    MIN_CIDB_VERSION = (1, 0)  # minimum supported database version

    def __init__(self, mgr):
        self.mgr = mgr

        self._import_handler_from_lang = {}
        self._cile_driver_from_lang = {}
        self._is_citadel_cpln_from_lang = {}

        self._scheduler = None # the scheduler thread, started as required
        self.batch_updater = None
        # Boolean indicating if a late-created main scheduler should NOT be
        # started immediately (because a BatchScheduler is already running).
        self._wait_to_start_scheduler = False

    def set_lang_info(self, lang, cile_driver_class, is_cpln_lang=False):
        self._cile_driver_from_lang[lang] = cile_driver_class(self.mgr)
        if is_cpln_lang:
            self._is_citadel_cpln_from_lang[lang] = True

    def cile_driver_from_lang(self, lang):
        """Return the CILE driver for this language.
        
        Raises KeyError if there isn't one registered.
        """
        return self._cile_driver_from_lang[lang]

    def is_citadel_cpln_lang(self, lang):
        """Return true if the given lang is a Citadel-based completion
        lang.
        """
        return lang in self._is_citadel_cpln_from_lang
    def get_citadel_cpln_langs(self):
        return self._is_citadel_cpln_from_lang.keys()

    def finalize(self):
        pass

    def batch_update(self, join=True, updater=None):
        """Do a batch update.
        
            "join" (optional, default True) indicates if this should
                block until complete. If False this will return immediately
                and you must manually .join() on the updater.
            "updater" (optional) is an BatchUpdater instance (generally
                a customized subclass of) used to do the update process.
        """
        if self.batch_updater is not None:
            raise CodeIntelError("cannot start batch update: another batch "
                                 "update is in progress")

        assert join or updater is not None, \
               ("cannot specify join=False and updater=None because "
                "you must manually wait on the updater if join is False.")
        if updater is None:
            updater = BatchUpdater()
        assert isinstance(updater, BatchUpdater), \
                ("given controller is not an instance of "
                 "BatchUpdater: %r" % updater)

        if self._scheduler is not None:
            self._scheduler.pause()
        else:
            self._wait_to_start_scheduler = True

        self.batch_updater = updater
        updater.start(self, on_complete=self._batch_update_completed)
        if join:
            updater.join()

    def _batch_update_completed(self):
        self._wait_to_start_scheduler = False
        if self._scheduler is not None:
            if self._scheduler.isAlive():
                self._scheduler.resume()
            else:
                self._scheduler.start()
        self.batch_updater = None

    #_SHOW_PROGRESS_ON_ONE_LINE = True
    #def batchUpdateProgress(self, stage, obj):
    #    """Called when progress is made on a set of batch update requests.
    #    
    #        "stage" is a string defining the current processing stage.
    #        "obj" is some object relevant to a particular stage to describe
    #            is state of progress.
    #    
    #    Subclasses can override this for custom handling.
    #    """
    #    if self._batchProgressQuiet:
    #        return
    #
    #    cache = self._batchProgressCache or {}
    #    if stage == "Preparing database": # a.k.a. removing db indices
    #        name, current, total = obj
    #        line = "%s: %s" % (stage, name)
    #    elif stage == "Restoring indices":
    #        name, current, total = obj
    #        line = "%s: %s" % (stage, name)
    #    elif stage == "Gathering files":
    #        line = "Gathering files: %s files" % obj
    #    elif stage == "Scanning": # 'obj' is a request object
    #        # Scanning: [#####        ] (1/12) ...tel\xsltcile.py ETA: 5 min
    #        remaining = self._batch_scheduler.getNumFilesToProcess()+1
    #        total = cache.setdefault("total_files", remaining)
    #        # Progress meter section
    #        percent = float(total-remaining)/float(total)
    #        METER_WIDTH = 20
    #        meterTemplate = "%%-%ds" % METER_WIDTH
    #        meter = meterTemplate % ("#"*int(METER_WIDTH*percent))
    #        # Count and file section
    #        # 79: display width; 25: other stuff, e.g. "Scanning", "ETA: ..."
    #        file = obj.path
    #        COUNT_AND_FILE_WIDTH = 79 - 25 - METER_WIDTH
    #        count = "(%d/%d)" % (total-remaining+1, total)
    #        FILE_WIDTH = COUNT_AND_FILE_WIDTH - len(count) - 1
    #        if len(file) > FILE_WIDTH:
    #            file = "..."+file[-FILE_WIDTH+3:]
    #        countAndFile = "%s %s" % (count, file)
    #        # ETA section
    #        now = time.time()
    #        if "starttime" in cache:
    #            elapsedsecs = now - cache["starttime"]
    #            totalsecs = elapsedsecs / percent
    #            remainsecs = totalsecs - elapsedsecs
    #            if remainsecs < 60.0:
    #                eta = "ETA: %d sec" % int(remainsecs)
    #            elif (remainsecs/60.0 < 60.0):
    #                eta = "ETA: %d min" % int(remainsecs/60.0)
    #            else:
    #                eta = "ETA: %d hr" % int(remainsecs/3600.0)
    #        else:
    #            cache["starttime"] = now
    #            eta = ""
    #        # Put sections together
    #        line_template = "Scanning: [%%s] %%-%ds %%s" % COUNT_AND_FILE_WIDTH
    #        line = line_template % (meter, countAndFile, eta)
    #    else:
    #        line = "%s: %s" % (stage, obj)
    #    if self._SHOW_PROGRESS_ON_ONE_LINE and "last_line" in cache:
    #        length = len(cache["last_line"])
    #        sys.stdout.write( "\b \b"*length )
    #    sys.stdout.write(line)
    #    if not self._SHOW_PROGRESS_ON_ONE_LINE:
    #        sys.stdout.write('\n')
    #    cache["last_line"] = line
    #    self._batchProgressCache = cache
    #
    #def batchUpdateCompleted(self, reason):
    #    """Called when a set of batch update requests are completed.
    #    
    #    Subclasses can override this for custom handling.
    #    """
    #    if self._batchProgressQuiet:
    #        return
    #
    #    cache = self._batchProgressCache or {}
    #    if "starttime" in cache:
    #        totalsecs = time.time() - cache["starttime"]
    #        if totalsecs < 60.0:
    #            elapsed = "%d seconds" % int(totalsecs)
    #        elif (totalsecs/60.0 < 60.0):
    #            elapsed = "%d minute(s)" % int(totalsecs/60.0)
    #        else:
    #            elapsed = "%d hour(s)" % int(totalsecs/3600.0)
    #    else:
    #        elapsed = None
    #    errors = self._lastBatchUpdateErrors
    #    if self._SHOW_PROGRESS_ON_ONE_LINE and "last_line" in cache:
    #        length = len(cache["last_line"])
    #        sys.stdout.write( "\b \b"*length )
    #    if reason == "completed":
    #        sys.stdout.write("Batch update completed.")
    #    elif reason == "stopped":
    #        sys.stdout.write("Batch update was cancelled.")
    #    elif reason == "error":
    #        sys.stdout.write("Batch update errored out.")
    #    else:
    #        sys.stdout.write("Batch update completed (%s)." % reason)
    #    if elapsed: sys.stdout.write(" Running time: %s." % elapsed)
    #    if errors: sys.stdout.write(" There were %d errors:" % len(errors))
    #    sys.stdout.write("\n")
    #    if errors:
    #        print "\t"+"\n\t".join(errors)

    def import_handler_from_lang(self, lang):
        """Return an "import"-handler for the given language.

        Returns None if don't know how to handle imports for this language.
        Each language-specific ImportHandler object is a singleton.

        TODO: move this to Manager class.
        """
        if lang not in self._import_handler_from_lang:
            try:
                self._import_handler_from_lang[lang] \
                    = self.mgr.import_handler_class_from_lang[lang](self.mgr)
            except KeyError:
                raise CodeIntelError("there is no registered ImportHandler "
                                     "class for language '%s'" % lang)
        return self._import_handler_from_lang[lang]


