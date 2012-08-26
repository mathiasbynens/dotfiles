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

r"""Database of static info for (text) languages (e.g. Python, Perl, ...).

Basic usage:

    >>> import langinfo
    >>> py = langinfo.langinfo_from_lang("Python")
    >>> py.name
    'Python'
    >>> py.exts
    ['.py', '.pyw']
    >>> py.is_text
    True
    
Advanced usage:

    >>> lidb = langinfo.Database()
    >>> lidb.langinfo_from_lang("HTML")
    <HTML LangInfo>
    >>> db.langinfo_from_filename("Makefile")
    <Makefile LangInfo>
    >>> db.langinfo_from_ext(".pm")
    <Perl LangInfo>
    >>> db.langinfo_from_magic("#!/usr/bin/env ruby")
    <Ruby LangInfo>
    >>> db.langinfo_from_doctype(public_id="-//W3C//DTD HTML 4.01//EN")
    <HTML LangInfo>

The advanced usage allows one to customize how the langinfo database is
built. For example, specified 'dirs' will be searched for
'langinfo_*.py' files that can add to the database. (This can be used to
allow Komodo extensions to add/override language info.)
"""

# TODO:
# - add other Komodo languages
# - langinfo_komodo.py, langinfo_apple.py, langinfo_microsoft.py, 
#   langinfo_adobe.py
# - Python: .pth, .egg-info
# - some XML langs to add:  DocBook, Atom, Dita,
#   RDF, RSS (various versions?), RelaxNG, XML Schema, XSLT.
#   ODF, UBL (these mentioned by Tim Bray, http://www.tbray.org/ongoing/When/200x/2006/01/08/No-New-XML-Languages)
#   others?
#TODO: .wiki (for google code)
#TODO: .*rc files?
#TODO: .cvsignore
#TODO: .pyx? .pxd? .pyd?  (see tm/check/contrib/pyyaml/ext/)
#TODO: .deb, .rpm
# - .phpt (in PHP tree)
#TODO: http://en.wikipedia.org/wiki/Adobe_Flash#Related_file_formats_and_extensions
#TODO: text .nib's, .plist, .pbxuser, .pbxproj, .m, .strings,
#TODO: "/Library/Application Support/Apple/Developer Tools/Quartz Composer/Clips/Cubic.qtz"
#      not recognized as "data", but it *is* by `file`.

__version_info__ = (1, 0, 0)
__version__ = '.'.join(map(str, __version_info__))

import os
from os.path import join, dirname, abspath, basename, exists
import sys
import re
from pprint import pprint
from glob import glob
import traceback
import logging
import optparse
import types
import struct
import warnings
import operator



#---- exceptions and warnings

class LangInfoError(Exception):
    pass

class InvalidLangInfoWarning(Warning):
    pass
warnings.simplefilter("once", InvalidLangInfoWarning)


#---- globals

log = logging.getLogger("langinfo")
#log.setLevel(logging.DEBUG)


#---- module API

def langinfo_from_lang(lang):
    return get_default_database().langinfo_from_lang(lang)



#---- base LangInfo definition

class LangInfo(object):
    """Base language info class. A subclass of LangInfo defines static
    information about a particular text language (e.g. Python, Perl,
    CSS, ...).

    The following are the "core" attributes for a LangInfo. Subclasses
    can feel free to define others, as makes sense for that language.
    """
    name = None     # a display name (i.e. appropriate for prose, display)

    # Used for identifying files of this language.
    exts = None
    filename_patterns = None
    magic_numbers = None
    doctypes = None
    specialization_hints_from_lang = None
    # Values for Emacs `mode` var or Vi modeline `ft' or `filetype',
    # other than `name', that identify lang.
    emacs_modes = None
    vi_filetypes = None

    # An optional key for specifying precedence for `magic_numbers`
    # usage. If not given the key is `(name, 0)`. Then, for example,
    # to ensure magic number checks before Python, one could set
    #   _magic_number_precedence = ('Python', -1)
    _magic_number_precedence = None 

    # Some languages mandate a default encoding, e.g. for Python it is
    # ASCII, for XML UTF-8.
    default_encoding = None
    encoding_decl_pattern = None  # Regex matching an encoding declaration.

    # A set of lang names to which this language conforms. For example,
    # RDF conforms to XML. See `conforms_to()` below.
    #
    # This is based on the UTI (Uniform Type Identifier) conforms-to
    # idea from Mac OS X:
    #   http://arstechnica.com/reviews/os/macosx-10-4.ars/11
    #   http://developer.apple.com/macosx/uniformtypeidentifiers.html
    #   http://developer.apple.com/documentation/Carbon/Conceptual/understanding_utis/understand_utis_intro/chapter_1_section_1.html
    conforms_to_bases = None

    # Misc. properties
    has_significant_trailing_ws = False

    def __init__(self, db):
        self._db = db

    def __repr__(self):
        return "<%s LangInfo>" % self.name

    @property
    def is_text(self):
        """Convenience property to check if this lang is plain text."""
        return self.conforms_to("Text")

    def conforms_to(self, lang):
        """Returns True iff this language conforms to the given `lang`."""
        if lang == self.name:
            return True
        if self.conforms_to_bases:
            if lang in self.conforms_to_bases:
                return True
            for base in self.conforms_to_bases:
                try:
                    base_li = self._db.langinfo_from_lang(base)
                except LangInfoError:
                    pass
                else:
                    if base_li.conforms_to(lang):
                        return True
        return False

    def conformant_attr(self, attr):
        """Returns the value of the given attr, inheriting from the
        `conforms_to_bases` languages if not directly defined for this
        language.
        """
        if hasattr(self, attr):
            val = getattr(self, attr)
            if val is not None:
                return val
        for base in self.conforms_to_bases or []:
            try:
                base_li = self._db.langinfo_from_lang(base)
            except LangInfoError:
                pass
            else:
                val = base_li.conformant_attr(attr)
                if val is not None:
                    return val
        return None
        


#---- LangInfo classes (most are defined in separate langinfo_*.py files)

class TextLangInfo(LangInfo):
    name = "Text"
    exts = ['.txt', '.text']
    filename_patterns = ["README", "COPYING", "LICENSE", "MANIFEST"]



#---- the Database

class Database(object):
    def __init__(self, dirs=None):
        self._langinfo_from_norm_lang = {}
        self._langinfo_from_ext = None
        self._langinfo_from_filename = None
        self._langinfo_from_filename_re = None
        self._magic_table = None
        self._li_from_doctype_public_id = None
        self._li_from_doctype_system_id = None
        self._li_from_emacs_mode = None
        self._li_from_vi_filetype = None
        self._li_from_norm_komodo_lang = None

        self._load()
        if dirs is None:
            dirs = []
        dirs.insert(0, dirname(__file__) or os.curdir)
        for dir in dirs:
            self._load_dir(dir)
        self.dirs = dirs

    def langinfos(self):
        for li in self._langinfo_from_norm_lang.values():
            yield li

    def langinfo_from_lang(self, lang):
        norm_lang = self._norm_lang_from_lang(lang)
        if norm_lang not in self._langinfo_from_norm_lang:
            raise LangInfoError("no info on %r lang" % lang)
        return self._langinfo_from_norm_lang[norm_lang]

    def langinfo_from_komodo_lang(self, komodo_lang):
        """Return a langinfo for the given Komodo language name.
        
        There are some minor differences in Komodo language names and
        those in langinfo (e.g. "Django" in Komodo vs "Django HTML
        Template" in langinfo).
        """
        if self._li_from_norm_komodo_lang is None:
            self._build_tables()
        norm_komodo_lang = self._norm_lang_from_lang(komodo_lang)
        if norm_komodo_lang in self._li_from_norm_komodo_lang:
            return self._li_from_norm_komodo_lang[norm_komodo_lang]
        elif norm_komodo_lang in self._langinfo_from_norm_lang:
            return self._langinfo_from_norm_lang[norm_komodo_lang]
        raise LangInfoError("no info on %r komodo lang" % komodo_lang)

    def langinfo_from_emacs_mode(self, emacs_mode):
        if self._li_from_emacs_mode is None:
            self._build_tables()
        if emacs_mode in self._li_from_emacs_mode:
            return self._li_from_emacs_mode[emacs_mode]
        norm_lang = self._norm_lang_from_lang(emacs_mode)
        if norm_lang in self._langinfo_from_norm_lang:
            return self._langinfo_from_norm_lang[norm_lang]

    def langinfo_from_vi_filetype(self, vi_filetype):
        if self._li_from_vi_filetype is None:
            self._build_tables()
        if vi_filetype in self._li_from_vi_filetype:
            return self._li_from_vi_filetype[vi_filetype]
        norm_lang = self._norm_lang_from_lang(vi_filetype)
        if norm_lang in self._langinfo_from_norm_lang:
            return self._langinfo_from_norm_lang[norm_lang]

    def langinfo_from_ext(self, ext):
        """Return an appropriate LangInfo for the given filename extension, 
        or None.
        """
        if self._langinfo_from_ext is None:
            self._build_tables()
        if sys.platform in ("win32", "darwin"): # Case-insensitive filesystems.
            ext = ext.lower()
        return self._langinfo_from_ext.get(ext)

    def langinfo_from_filename(self, filename):
        """Return an appropriate LangInfo for the given filename, or None."""
        if self._langinfo_from_filename is None:
            self._build_tables()
        if filename in self._langinfo_from_filename:
            return self._langinfo_from_filename[filename]
        else:
            for regex, li in self._langinfo_from_filename_re.items():
                if regex.search(filename):
                    return li

    def langinfo_from_magic(self, head_bytes, shebang_only=False):
        """Attempt to identify the appropriate LangInfo from the magic number
        in the file. This mimics some of the behaviour of GNU file.

        @param head_bytes {string} is a string of 8-bit char bytes or a
            unicode string from the head of the document.
        @param shebang_only {boolean} can be set to true to only process
            magic number records for shebang lines (a minor perf
            improvement).
        """
        if self._magic_table is None:
            self._build_tables()

        for magic_number, li, sort_key in self._magic_table:
            try:
                start, format, pattern = magic_number
            except ValueError:
                # Silently drop bogus magic number decls.
                continue
            if shebang_only and format != "regex":
                continue
            if format == "string":
                end = start + len(pattern)
                if head_bytes[start:end] == pattern:
                    return li
            elif format == "regex":
                if pattern.search(head_bytes, start):
                    return li
            else:  # a struct format
                try:
                    length = struct.calcsize(format)
                except struct.error, ex:
                    warnings.warn("error in %s magic number struct format: %r"
                                      % (li, format),
                                  InvalidLangInfoWarning)
                end = start + length
                bytes = head_bytes[start:end]
                if len(bytes) == length:
                    if struct.unpack(format, bytes)[0] == pattern:
                        return li

    def langinfo_from_doctype(self, public_id=None, system_id=None):
        """Return a LangInfo instance matching any of the specified
        pieces of doctype info, or None if no match is found.
        
        The behaviour when doctype info from multiple LangInfo classes
        collide is undefined (in the current impl, the last one wins).

        Notes on doctype info canonicalization:
        - I'm not sure if there is specified canonicalization of
          doctype names or public-ids, but matching is done
          case-insensitively here.
        - Technically doctype system-id comparison is of URI (with
          non-trivial but well-defined canonicalization rules). For
          simplicity we just compare case-insensitively.
        """
        if self._li_from_doctype_public_id is None:
            self._build_tables()
        
        if public_id is not None \
           and public_id in self._li_from_doctype_public_id:
            return self._li_from_doctype_public_id[public_id]
        if system_id is not None \
           and system_id in self._li_from_doctype_system_id:
            return self._li_from_doctype_system_id[system_id]

    def specialized_langinfo_from_content(self, li, text):
        hints, specialized_li = self._specialization_hints_from_lang.get(
            li.name, (None, None))
        if not hints:
            return None
        for hint_str, hint_re in hints:
            if hint_str not in text:
                continue
            if hint_re and not hint_re.search(text):
                continue
            return specialized_li
        return None

    def _build_tables(self):
        self._langinfo_from_ext = {}
        self._langinfo_from_filename = {}
        self._langinfo_from_filename_re = {}
        self._magic_table = []  # list of (<magic-tuple>, <langinfo>, <sort-key>)
        self._li_from_doctype_public_id = {}
        self._li_from_doctype_system_id = {}
        self._li_from_emacs_mode = {}
        self._li_from_vi_filetype = {}
        self._li_from_norm_komodo_lang = {}
        self._specialization_hints_from_lang = {} # <lang> -> (<hint>, <specialized-langinfo>)

        for li in self._langinfo_from_norm_lang.values():
            if li.exts:
                for ext in li.exts:
                    if not ext.startswith('.'):
                        log.warn("exts must start with '.': ext %r for "
                                 "lang %r", ext, li.name)
                    if sys.platform in ("win32", "darwin"):
                        ext = ext.lower()
                    do_replace = True
                    if ext in self._langinfo_from_ext:
                        current_li = self._langinfo_from_ext[ext]
                        variant = getattr(li, "is_minor_variant", None)
                        if variant is not None:
                            log.debug("ext update: ext: %s, %r is a minor variant of %r",
                                      ext, li, current_li)
                        elif ext.startswith(".py"):
                            log.debug("ext update: ext: %s, %r is *not* a minor variant of %r",
                                  ext, li, current_li)
                        if variant is not None and variant.name == current_li.name:
                            log.debug("ext update: found variant for ext %s, li:%r, using:%r",
                                      ext, li, current_li)
                            do_replace = False
                        else:
                            variant = getattr(current_li, "is_minor_variant", None)
                            if variant is None or variant.name != li.name:
                                log.debug("ext conflict: %r for %r conflicts "
                                          "with the same for %r (%r wins)", ext, li,
                                          self._langinfo_from_ext[ext], li)
                            else:
                                log.debug("ext conflict: ext:%s, replace variant %r with %r",
                                          ext, current_li, li)
                    if do_replace:
                        self._langinfo_from_ext[ext] = li
            if li.filename_patterns:
                for pat in li.filename_patterns:
                    if isinstance(pat, basestring):
                        self._langinfo_from_filename[pat] = li
                    else:
                        self._langinfo_from_filename_re[pat] = li
            if li.magic_numbers:
                sort_key = li._magic_number_precedence or (li.name, 0)
                for mn in li.magic_numbers:
                    self._magic_table.append((mn, li, sort_key))
            if li.doctypes:
                for dt in li.doctypes:
                    try:
                        flavour, name, public_id, system_id = dt
                    except ValueError:
                        log.debug("invalid doctype tuple for %r: %r "
                                  "(dropping it)", li, dt)
                        continue
                    if public_id:
                        self._li_from_doctype_public_id[public_id] = li
                    if system_id:
                        self._li_from_doctype_system_id[system_id] = li
            if li.emacs_modes:
                for em in li.emacs_modes:
                    self._li_from_emacs_mode[em] = li
            if li.vi_filetypes:
                for em in li.vi_filetypes:
                    self._li_from_vi_filetypes[em] = li
            if hasattr(li, "komodo_name"):
                norm_komodo_lang = self._norm_lang_from_lang(li.komodo_name)
                self._li_from_norm_komodo_lang[norm_komodo_lang] = li
            if li.specialization_hints_from_lang:
                for lang, hint in li.specialization_hints_from_lang.items():
                    self._specialization_hints_from_lang[lang] = (hint, li)
        
        self._magic_table.sort(key=operator.itemgetter(2))

    def _norm_lang_from_lang(self, lang):
        return lang.lower()

    def _load(self):
        """Load LangInfo classes in this module."""
        for name, g in globals().items():
            if isinstance(g, (types.ClassType, types.TypeType)) \
               and issubclass(g, LangInfo) and g is not LangInfo:
                norm_lang = self._norm_lang_from_lang(g.name)
                self._langinfo_from_norm_lang[norm_lang] = g(self)

    def _load_dir(self, d):
        """Load LangInfo classes in langinfo_*.py modules in this dir."""
        for path in glob(join(d, "langinfo_*.py")):
            try:
                module = _module_from_path(path)
            except Exception, ex:
                log.warn("could not import `%s': %s", path, ex)
                #import traceback
                #traceback.print_exc()
                continue
            for name in dir(module):
                attr = getattr(module, name)
                if (not name.startswith("_")   # skip internal bases
                    and isinstance(attr, (types.ClassType, types.TypeType))
                    and issubclass(attr, LangInfo)
                    and attr is not LangInfo):
                    norm_lang = self._norm_lang_from_lang(attr.name)
                    self._langinfo_from_norm_lang[norm_lang] = attr(self)


#---- internal support stuff

_g_default_database = None
_g_default_dirs = None
def set_default_dirs(dirs):
    global _g_default_dirs, _g_default_database
    if dirs != _g_default_dirs:
        _g_default_dirs = dirs
        _g_default_database = None

def get_default_database():
    global _g_default_database, _g_default_database
    if _g_default_database is None:
        _g_default_database = Database(dirs=_g_default_dirs)
    return _g_default_database

# Recipe: module_from_path (1.0.1+)
def _module_from_path(path):
    import imp, os
    dir = os.path.dirname(path) or os.curdir
    name = os.path.splitext(os.path.basename(path))[0]
    iinfo = imp.find_module(name, [dir])
    return imp.load_module(name, *iinfo)



#---- self-test

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
    

