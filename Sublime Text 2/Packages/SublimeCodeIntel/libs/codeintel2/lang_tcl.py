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

"""Tcl support for CodeIntel"""

import sys
import os
import logging
from pprint import pprint
import re

import process

import SilverCity
from SilverCity.Lexer import Lexer
from SilverCity import ScintillaConstants

from codeintel2.citadel import ImportHandler, CitadelBuffer, CitadelLangIntel
from codeintel2.citadel_common import ScanRequest
from codeintel2.common import *
from codeintel2.parseutil import urlencode_path
from codeintel2.tree import tree_from_cix


#---- globals

lang = "Tcl"
log = logging.getLogger("codeintel.tcl")

keywords = ["after", "append", "apply", "array", "auto_execok",
            "auto_import", "auto_load", "auto_load_index", "auto_mkindex",
            "auto_qualify", "auto_reset", "bgerror", "binary", "break",
            "case", "catch", "cd", "chan", "clock", "close", "concat",
            "continue", "dde", "dict", "else", "then", "elseif",
            "encoding", "eof", "error", "eval", "exec", "exit", "expr",
            "fblocked", "fconfigure", "fcopy", "file", "fileevent",
            "flush", "for", "foreach", "format", "gets", "glob", "global",
            "history", "if", "incr", "info", "interp", "join", "lappend",
            "lassign", "lindex", "linsert", "list", "llength", "load",
            "lrange", "lrepeat", "lreplace", "lreverse", "lsearch", "lset",
            "lsort", "namespace", "open", "package", "parray", "pid",
            "pkg_compareExtension", "pkg_mkIndex", "proc", "puts", "pwd",
            "read", "regexp", "registry", "regsub", "rename", "return",
            "scan", "seek", "set", "socket", "source", "split", "string",
            "subst", "switch", "tcl_findLibrary", "tell", "time", "trace",
            "unknown", "unload", "unset", "update", "uplevel", "upvar",
            "variable", "vwait", "while",
            "bell", "bind", "bindtags", "button", "canvas", "checkbutton",
            "clipboard", "destroy", "entry", "event", "focus", "font",
            "frame", "grab", "grid", "image", "label", "labelframe",
            "listbox", "lower", "menu", "menubutton", "message", "option",
            "pack", "panedwindow", "place", "radiobutton", "raise",
            "scale", "scrollbar", "selection", "spinbox", "text", "tk",
            "tk_chooseColor", "tk_chooseDirectory", "tk_getOpenFile",
            "tk_getSaveFile", "tk_menuSetFocus", "tk_messageBox",
            "tk_popup", "tk_textCopy", "tk_textCut", "tk_textPaste",
            "tkwait", "toplevel", "ttk::button", "ttk::checkbutton",
            "ttk::combobox", "ttk::entry", "ttk::frame", "ttk::label",
            "ttk::labelframe", "ttk::menubutton", "ttk::notebook",
            "ttk::panedwindow", "ttk::progressbar", "ttk::radiobutton",
            "ttk::scrollbar", "ttk::separator", "ttk::sizegrip",
            "ttk::style", "ttk::treeview", "ttk::style", "winfo", "wm"]


line_end_re = re.compile("(?:\r\n|\r)")


#---- language support

class TclLexer(Lexer):
    lang = "Tcl"
    def __init__(self):
        self._properties = SilverCity.PropertySet()
        self._lexer = SilverCity.find_lexer_module_by_id(ScintillaConstants.SCLEX_TCL)
        self._keyword_lists = [
            SilverCity.WordList(' '.join(keywords))
        ]


class TclBuffer(CitadelBuffer):
    lang = "Tcl"
    cb_show_if_empty = True


class TclLangIntel(CitadelLangIntel):
    lang = "Tcl"

    def cb_import_data_from_elem(self, elem):
        #XXX Not handling symbol and alias
        module = elem.get("module")
        detail = "package require %s" % module
        return {"name": module, "detail": detail}    


class TclImportHandler(ImportHandler):
    # Tcl _does_ have a TCLLIBPATH environment variable for specifying
    # import path elements, but parsing isn't straighforward -- it uses
    # Tcl-syntax -- so we don't bother to separate "envPath" and "corePath"
    # for Tcl.
    PATH_ENV_VAR = None

    def _shellOutForPath(self, compiler):
        import process
        argv = [compiler]
        p = process.ProcessOpen(argv)
        output, stderr = p.communicate("puts [join $auto_path \\n]")
        retval = p.returncode
        path = [os.path.normpath(line) for line in output.splitlines(0)]
        if path and (path[0] == "" or path[0] == os.getcwd()):
            del path[0] # cwd handled separately
        return path

    def setCorePath(self, compiler=None, extra=None):
        if compiler is None:
            import which
            compiler = which.which("tclsh")
        self.corePath = self._shellOutForPath(compiler)

    def _findScannableFiles(self, (files, searchedDirs, skipRareImports),
                            dirname, names):
        if sys.platform.startswith("win"):
            cpath = dirname.lower()
        else:
            cpath = dirname
        if cpath in searchedDirs:
            while names:
                del names[0]
            return
        else:
            searchedDirs[cpath] = 1
        for i in range(len(names)-1, -1, -1): # backward so can del from list
            path = os.path.join(dirname, names[i])
            if os.path.isdir(path):
                pass
            elif os.path.splitext(names[i])[1] in (".tcl",):
                #XXX The list of extensions should be settable on
                #    the ImportHandler and Komodo should set whatever is
                #    set in prefs.
                #XXX This check for files should probably include
                #    scripts, which might likely not have the
                #    extension: need to grow filetype-from-content smarts.
                if skipRareImports and names[i] == "pkgIndex.tcl":
                    continue
                files.append(path)

    def genScannableFiles(self, path=None, skipRareImports=False,
                          importableOnly=False):
        if path is None:
            path = self._getPath()
        searchedDirs = {}
        for dirname in path:
            if dirname == os.curdir:
                continue
            files = []
            os.path.walk(dirname, self._findScannableFiles,
                         (files, searchedDirs, skipRareImports))
            for file in files:
                yield file


class TclCILEDriver(CILEDriver):
    lang = lang
    def __init__(self, *args):
        CILEDriver.__init__(self, *args)
        # We have circular imports here, so load it at runtime
        from codeintel2 import tclcile
        self.tclcile = tclcile

    def scan(self, request):
        request.calculateMD5()
        return self.tclcile.scan(request.content, request.path,
                             request.md5sum, request.mtime)

    def scan_purelang(self, buf):
        return self.tclcile.scan_purelang(buf.accessor.text, buf.path)



#---- internal support stuff



#---- registration

def register(mgr):
    """Register language support with the Manager."""
    mgr.set_lang_info(lang,
                      silvercity_lexer=TclLexer(),
                      buf_class=TclBuffer,
                      langintel_class=TclLangIntel,
                      import_handler_class=TclImportHandler,
                      cile_driver_class=TclCILEDriver)

