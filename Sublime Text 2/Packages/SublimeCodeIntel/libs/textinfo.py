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

r"""Determine information about text files.

This module efficiently determines the encoding of text files (see
_classify_encoding for details), accurately identifies binary files, and
provides detailed meta information of text files.

    >>> import textinfo
    >>> path = __file__
    >>> if path.endswith(".pyc"): path = path[:-1]
    >>> ti = textinfo.textinfo_from_path(path)
    >>> ti.__class__
    <class 'textinfo.TextInfo'>
    >>> ti.encoding
    'utf-8'
    >>> ti.file_type_name
    'regular file'
    >>> ti.is_text
    True
    >>> ti.lang
    'Python'
    >>> ti.langinfo
    <Python LangInfo>
    
...plus a number of other useful information gleaned from the file. To see
a list of all useful attributes see

    >> list(ti.as_dict().keys())
    ['encoding', 'file_type', ...]

Note: This module requires at least Python 2.5 to use
`codecs.lookup(<encname>).name`.
"""

_cmdln_doc = """Determine information about text files.
"""

# TODO:
# - [high prio] prefs integration
# - aggegrate "is there an explicit encoding decl in this file" from XML, HTML,
#   lang-specific, emacs and vi vars decls (as discussed with Shane)
# - fix ti with unicode paths Windows (check on Linux too)
# - '-L|--dereference' option a la `file` and `ls`
# - See: http://webblaze.cs.berkeley.edu/2009/content-sniffing/
# - Shift-JIS encoding is not detected for
#   http://public.activestate.com/pub/apc/perl-current/lib/Pod/Simple/t/corpus/s2763_sjis.txt
#   [Jan wrote]
#   > While the document isn't identified by filename extension as POD,
#   > it does contain POD and a corresponding =encoding directive.
#   Could potentially have a content heuristic check for POD.
#

# ----------------
# Current Komodo (4.2) Encoding Determination Notes (used for reference,
# but not absolutely followed):
#
# Working through koDocumentBase._detectEncoding:
#   encoding_name = pref:encodingDefault (on first start is set
#       to encoding from locale.getdefaultlocale() typically,
#       fallback to iso8859-1; default locale typically ends up being:
#           Windows: cp1252
#           Mac OS X: mac-roman
#           (modern) Linux: UTF-8)
#   encoding = the python name for this
#   tryencoding = pref:encoding (no default, explicitly set
#       encoding) -- i.e. if there are doc prefs for this
#       path, then give this encoding a try. If not given,
#       then utf-8 for XML/XSLT/VisualBasic and
#       pref:encodingDefault for others (though this is
#       all prefable via the 'languages' pref struct).
#   tryxmldecl
#   trymeta (HTML meta)
#   trymodeline
#   autodetect (whether to try at all)
#
#   if autodetect or tryencoding:
#       koUnicodeEncoding.autoDetectEncoding()
#   else:
#       if encoding.startswith('utf'): # note this is pref:encodingDefault
#           check bom
#           presume encoding is right (give up if conversion fails)
#       else:
#           presume encoding is right (given up if fails)
#
# Working through koUnicodeEncoding.autoDetectEncoding:
#   if tryxmldecl: ...
#   if tryhtmlmeta: ...
#   if trymodeline: ...
#   use bom: ...
# ----------------

__version_info__ = (0, 1, 0)
__version__ = '.'.join(map(str, __version_info__))

import os
from os.path import join, dirname, abspath, basename, exists
import sys
import re
from pprint import pprint
import traceback
import warnings
import logging
import optparse
import codecs
import locale

import langinfo




#---- exceptions and warnings

class TextInfoError(Exception):
    pass

class TextInfoConfigError(TextInfoError):
    pass

class ChardetImportWarning(ImportWarning):
    pass
warnings.simplefilter("once", ChardetImportWarning)



#---- globals

log = logging.getLogger("textinfo")

# For debugging:
DEBUG_CHARDET_INFO = False  # gather chardet info



#---- module API

def textinfo_from_filename(path):
    """Determine test info for the given path **using the filename only**.
    
    No attempt is made to stat or read the file.
    """
    return TextInfo.init_from_filename(path)

def textinfo_from_path(path, encoding=None, follow_symlinks=False,
                       quick_determine_lang=False):
    """Determine text info for the given path.
    
    This raises EnvironmentError if the path doesn't not exist or could
    not be read.
    """
    return TextInfo.init_from_path(path, encoding=encoding, 
                                   follow_symlinks=follow_symlinks,
                                   quick_determine_lang=quick_determine_lang)



#---- main TextInfo class

class TextInfo(object):
    path = None
    file_type_name = None # e.g. "regular file", "directory", ...
    file_type = None      # stat.S_IFMT(os.stat(path).st_mode)
    file_mode = None      # stat.S_IMODE(os.stat(path).st_mode)
    is_text = None

    encoding = None
    has_bom = None   # whether the text has a BOM (Byte Order Marker)
    encoding_bozo = False
    encoding_bozo_reasons = None

    lang = None         # e.g. "Python", "Perl", ...
    langinfo = None     # langinfo.LangInfo instance or None

    # Enable chardet-based heuristic guessing of encoding as a last
    # resort for file types known to not be binary.
    CHARDET_ENABLED = True
    CHARDET_THRESHHOLD = 0.9  # >=90% confidence to avoid false positives.

    @classmethod
    def init_from_filename(cls, path, lidb=None):
        """Create an instance using only the filename to initialize."""
        if lidb is None:
            lidb = langinfo.get_default_database()
        self = cls()
        self.path = path
        self._classify_from_filename(lidb)
        return self

    @classmethod
    def init_from_path(cls, path, encoding=None, lidb=None,
                       follow_symlinks=False,
                       quick_determine_lang=False,
                       env=None):
        """Create an instance using the filename and stat/read info
        from the given path to initialize.

        @param follow_symlinks {boolean} can be set to True to have
            the textinfo returned for a symlink be for linked-to file. By
            default the textinfo is for the symlink itself.
        @param quick_determine_lang {boolean} can be set to True to have
            processing stop as soon as the language has been determined.
            Note that this means some fields will not be populated.
        @param env {runtime environment} A "runtime environment" class
            whose behaviour is used to influence processing. Currently
            it is just used to provide a hook for lang determination
            by filename (for Komodo).
        """
        if lidb is None:
            lidb = langinfo.get_default_database()
        self = cls()
        self.path = path
        self._accessor = PathAccessor(path, follow_symlinks=follow_symlinks)
        try:
            #TODO: pref: Is a preference specified for this path?

            self._classify_from_stat(lidb)
            if self.file_type_name != "regular file":
                # Don't continue if not a regular file.
                return self

            #TODO: add 'pref:treat_as_text' a la TextMate (or
            #      perhaps that is handled in _classify_from_filename())

            self._classify_from_filename(lidb, env)
            if self.is_text is False:
                return self
            if self.lang and quick_determine_lang:
                return self

            if not self.lang:
                self._classify_from_magic(lidb)
                if self.is_text is False:
                    return self
            if self.lang and quick_determine_lang:
                return self

            self._classify_encoding(lidb, suggested_encoding=encoding)
            if self.is_text is None and self.encoding:
                self.is_text = True
            if self.is_text is False:
                return self
            self.text = self._accessor.text

            if self.text:  # No `self.text' with current UTF-32 hack.
                self._classify_from_content(lidb)
            return self
        finally:
            # Free the memory used by the accessor.
            del self._accessor 

    def __repr__(self):
        if self.path:
            return "<TextInfo %r>" % self.path
        else:
            return "<TextInfo %r>"\
                   % _one_line_summary_from_text(self.content, 30)

    def as_dict(self):
        return dict((k,v) for k,v in self.__dict__.items()
                    if not k.startswith('_'))

    def as_summary(self):
        """One-liner string summary of text info."""
        d = self.as_dict()
        info = []
        if self.file_type_name and self.file_type_name != "regular file":
            info.append(self.file_type_name)
        else:
            info.append(self.lang or "???")
            if not self.is_text:
                info.append("binary")
            elif self.encoding:
                enc = self.encoding
                if self.has_bom:
                    enc += " (bom)"
                info.append(enc)
            if DEBUG_CHARDET_INFO and hasattr(self, "chardet_info") \
               and self.chardet_info["encoding"]:
                info.append("chardet:%s/%.1f%%"
                            % (self.chardet_info["encoding"],
                               self.chardet_info["confidence"] * 100.0))
        return "%s: %s" % (self.path, ', '.join(info))

    def _classify_from_content(self, lidb):

        #TODO: Plan:
        # - eol_* attrs (test cases for this!)

        head = self.text[:self._accessor.HEAD_SIZE]
        tail = self.text[-self._accessor.TAIL_SIZE:]

        # If lang is unknown, attempt to guess from XML prolog or
        # shebang now that we've successfully decoded the buffer.
        if self.langinfo is None:
            (self.has_xml_prolog, xml_version,
             xml_encoding) = self._get_xml_prolog_info(head)
            if self.has_xml_prolog:
                self.xml_version = xml_version
                self.xml_encoding = xml_encoding
                self.langinfo = lidb.langinfo_from_lang("XML")
                self.lang = self.langinfo.name
            elif self.text.startswith("#!"):
                li = lidb.langinfo_from_magic(self.text, shebang_only=True)
                if li:
                    self.langinfo = li
                    self.lang = li.name

        # Extract Emacs local vars and Vi(m) modeline info and, if the
        # lang is still unknown, attempt to use them to determine it.
        self.emacs_vars = self._get_emacs_head_vars(head)
        self.emacs_vars.update(self._get_emacs_tail_vars(tail))
        self.vi_vars = self._get_vi_vars(head)
        if not self.vi_vars:
            self.vi_vars = self._get_vi_vars(tail)
        if self.langinfo is None and "mode" in self.emacs_vars:
            li = lidb.langinfo_from_emacs_mode(self.emacs_vars["mode"])
            if li:
                self.langinfo = li
                self.lang = li.name
        if self.langinfo is None and "filetype" in self.vi_vars \
           or "ft" in self.vi_vars:
            vi_filetype = self.vi_vars.get("filetype") or self.vi_vars.get("ft")
            li = lidb.langinfo_from_vi_filetype(vi_filetype)
            if li:
                self.langinfo = li
                self.lang = li.name

        if self.langinfo is not None:
            if self.langinfo.conforms_to("XML"):
                if not hasattr(self, "has_xml_prolog"):
                    (self.has_xml_prolog, self.xml_version,
                     self.xml_encoding) = self._get_xml_prolog_info(head)
                (self.has_doctype_decl, self.doctype_decl,
                 self.doctype_name, self.doctype_public_id,
                 self.doctype_system_id) = self._get_doctype_decl_info(head)
                
                # If this is just plain XML, we try to use the doctype
                # decl to choose a more specific XML lang.
                if self.lang == "XML" and self.has_doctype_decl:
                    li = lidb.langinfo_from_doctype(
                            public_id=self.doctype_public_id,
                            system_id=self.doctype_system_id)
                    if li and li.name != "XML":
                        self.langinfo = li
                        self.lang = li.name
                
            elif self.langinfo.conforms_to("HTML"):
                (self.has_doctype_decl, self.doctype_decl,
                 self.doctype_name, self.doctype_public_id,
                 self.doctype_system_id) = self._get_doctype_decl_info(head)

                # Allow promotion to XHTML (or other HTML flavours) based
                # on doctype.
                if self.lang == "HTML" and self.has_doctype_decl:
                    li = lidb.langinfo_from_doctype(
                            public_id=self.doctype_public_id,
                            system_id=self.doctype_system_id)
                    if li and li.name != "HTML":
                        self.langinfo = li
                        self.lang = li.name

                # Look for XML prolog and promote HTML -> XHTML if it
                # exists. Note that this wins over a plain HTML doctype.
                (self.has_xml_prolog, xml_version,
                 xml_encoding) = self._get_xml_prolog_info(head)
                if self.has_xml_prolog:
                    self.xml_version = xml_version
                    self.xml_encoding = xml_encoding
                    if self.lang == "HTML":
                        li = lidb.langinfo_from_lang("XHTML")
                        self.langinfo = li
                        self.lang = li.name

        # Attempt to specialize the lang.
        if self.langinfo is not None:
            li = lidb.specialized_langinfo_from_content(self.langinfo, self.text)
            if li:
                self.langinfo = li
                self.lang = li.name

    def _classify_from_magic(self, lidb):
        """Attempt to classify from the file's magic number/shebang
        line, doctype, etc.

        Note that this is done before determining the encoding, so we are
        working with the *bytes*, not chars.
        """
        self.has_bom, bom, bom_encoding = self._get_bom_info()
        if self.has_bom:
            # If this file has a BOM then, unless something funny is
            # happening, this will be a text file encoded with
            # `bom_encoding`. We leave that to `_classify_encoding()`.
            return

        # Without a BOM we assume this is an 8-bit encoding, for the
        # purposes of looking at, e.g. a shebang line.
        #
        # UTF-16 and UTF-32 without a BOM is rare; we won't pick up on,
        # e.g. Python encoded as UCS-2 or UCS-4 here (but
        # `_classify_encoding()` should catch most of those cases).
        head_bytes = self._accessor.head_bytes
        li = lidb.langinfo_from_magic(head_bytes)
        if li:
            log.debug("lang from magic: %s", li.name)
            self.langinfo = li
            self.lang = li.name
            self.is_text = li.is_text
            return
        
        (has_doctype_decl, doctype_decl, doctype_name, doctype_public_id,
         doctype_system_id) = self._get_doctype_decl_info(head_bytes)
        if has_doctype_decl:
            li = lidb.langinfo_from_doctype(public_id=doctype_public_id,
                                            system_id=doctype_system_id)
            if li:
                log.debug("lang from doctype: %s", li.name)
                self.langinfo = li
                self.lang = li.name
                self.is_text = li.is_text
                return

    def _classify_encoding(self, lidb, suggested_encoding=None):
        """To classify from the content we need to separate text from
        binary, and figure out the encoding. This is an imperfect task.
        The algorithm here is to go through the following heroics to attempt
        to determine an encoding that works to decode the content. If all
        such attempts fail, we presume it is binary.

        1. Use the BOM, if it has one.
        2. Try the given suggested encoding (if any).
        3. Check for EBCDIC encoding.
        4. Lang-specific (if we know the lang already):
            * if this is Python, look for coding: decl and try that
            * if this is Perl, look for use encoding decl and try that
            * ...
        5. XML: According to the XML spec the rule is the XML prolog
           specifies the encoding, or it is UTF-8.
        6. HTML: Attempt to use Content-Type meta tag. Try the given
           charset, if any.
        7. Emacs-style "coding" local var.
        8. Vi[m]-style "fileencoding" local var.
        9. Heuristic checks for UTF-16 without BOM.
        10. Give UTF-8 a try, it is a pretty common fallback.
            We must do this before a possible 8-bit
            `locale.getpreferredencoding()` because any UTF-8 encoded
            document will decode with an 8-bit encoding (i.e. will decode,
            just with bogus characters).
        11. Lang-specific fallback. E.g., UTF-8 for XML, ascii for Python.
        12. chardet (http://chardet.feedparser.org/), if CHARDET_ENABLED == True
        13. locale.getpreferredencoding()
        14. iso8859-1 (in case `locale.getpreferredencoding()` is UTF-8
            we must have an 8-bit encoding attempt).
            TODO: Is there a worry for a lot of false-positives for
            binary files.

        Notes:
        - A la Universal Feed Parser, if some
          supposed-to-be-authoritative encoding indicator is wrong (e.g.
          the BOM, the Python 'coding:' decl for Python),
          `self.encoding_bozo` is set True and a reason is appended to
          the `self.encoding_bozo_reasons` list.
        """
        # 1. Try the BOM.
        if self.has_bom is not False:  # Was set in `_classify_from_magic()`.
            self.has_bom, bom, bom_encoding = self._get_bom_info()
            if self.has_bom:
                self._accessor.strip_bom(bom)
                # Python doesn't currently include a UTF-32 codec. For now
                # we'll *presume* that a UTF-32 BOM is correct. The
                # limitation is that `self.text' will NOT get set
                # because we cannot decode it.
                if bom_encoding in ("utf-32-le", "utf-32-be") \
                   or self._accessor.decode(bom_encoding):
                    log.debug("encoding: encoding from BOM: %r", bom_encoding)
                    self.encoding = bom_encoding
                    return
                else:
                    log.debug("encoding: BOM encoding (%r) was *wrong*",
                              bom_encoding)
                    self._encoding_bozo(
                        u"BOM encoding (%s) could not decode %s"
                         % (bom_encoding, self._accessor))

        head_bytes = self._accessor.head_bytes
        if DEBUG_CHARDET_INFO:
            sys.path.insert(0, os.path.expanduser("~/tm/check/contrib/chardet"))
            import chardet
            del sys.path[0]
            self.chardet_info = chardet.detect(head_bytes)

        # 2. Try the suggested encoding.
        if suggested_encoding is not None:
            norm_suggested_encoding = _norm_encoding(suggested_encoding)
            if self._accessor.decode(suggested_encoding):
                self.encoding = norm_suggested_encoding
                return
            else:
                log.debug("encoding: suggested %r encoding didn't work for %s",
                          suggested_encoding, self._accessor)

        # 3. Check for EBCDIC.
        #TODO: Not sure this should be included, chardet may be better
        #      at this given different kinds of EBCDIC.
        EBCDIC_MAGIC = '\x4c\x6f\xa7\x94'
        if self._accessor.head_4_bytes == EBCDIC_MAGIC:
            # This is EBCDIC, but I don't know if there are multiple kinds
            # of EBCDIC. Python has a 'ebcdic-cp-us' codec. We'll use
            # that for now.
            norm_ebcdic_encoding = _norm_encoding("ebcdic-cp-us")
            if self._accessor.decode(norm_ebcdic_encoding):
                log.debug("EBCDIC encoding: %r", norm_ebcdic_encoding)
                self.encoding = norm_ebcdic_encoding
                return
            else:
                log.debug("EBCDIC encoding didn't work for %s",
                          self._accessor)

        # 4. Lang-specific (if we know the lang already).
        if self.langinfo and self.langinfo.conformant_attr("encoding_decl_pattern"):
            m = self.langinfo.conformant_attr("encoding_decl_pattern") \
                    .search(head_bytes)
            if m:
                lang_encoding = m.group("encoding")
                norm_lang_encoding = _norm_encoding(lang_encoding)
                if self._accessor.decode(norm_lang_encoding):
                    log.debug("encoding: encoding from lang-spec: %r",
                              norm_lang_encoding)
                    self.encoding = norm_lang_encoding
                    return
                else:
                    log.debug("encoding: lang-spec encoding (%r) was *wrong*",
                              lang_encoding)
                    self._encoding_bozo(
                        u"lang-spec encoding (%s) could not decode %s"
                         % (lang_encoding, self._accessor))

        # 5. XML prolog
        if self.langinfo and self.langinfo.conforms_to("XML"):
            has_xml_prolog, xml_version, xml_encoding \
                = self._get_xml_prolog_info(head_bytes)
            if xml_encoding is not None:
                norm_xml_encoding = _norm_encoding(xml_encoding)
                if self._accessor.decode(norm_xml_encoding):
                    log.debug("encoding: encoding from XML prolog: %r",
                              norm_xml_encoding)
                    self.encoding = norm_xml_encoding
                    return
                else:
                    log.debug("encoding: XML prolog encoding (%r) was *wrong*",
                              norm_xml_encoding)
                    self._encoding_bozo(
                        u"XML prolog encoding (%s) could not decode %s"
                         % (norm_xml_encoding, self._accessor))
            
        # 6. HTML: Attempt to use Content-Type meta tag.
        if self.langinfo and self.langinfo.conforms_to("HTML"):
            has_http_content_type_info, http_content_type, http_encoding \
                = self._get_http_content_type_info(head_bytes)
            if has_http_content_type_info and http_encoding:
                norm_http_encoding = _norm_encoding(http_encoding)
                if self._accessor.decode(norm_http_encoding):
                    log.debug("encoding: encoding from HTTP content-type: %r",
                              norm_http_encoding)
                    self.encoding = norm_http_encoding
                    return
                else:
                    log.debug("encoding: HTTP content-type encoding (%r) was *wrong*",
                              norm_http_encoding)
                    self._encoding_bozo(
                        u"HTML content-type encoding (%s) could not decode %s"
                         % (norm_http_encoding, self._accessor))

        # 7. Emacs-style local vars.
        emacs_head_vars = self._get_emacs_head_vars(head_bytes)
        emacs_encoding = emacs_head_vars.get("coding")
        if not emacs_encoding:
            tail_bytes = self._accessor.tail_bytes
            emacs_tail_vars = self._get_emacs_tail_vars(tail_bytes)
            emacs_encoding = emacs_tail_vars.get("coding")
        if emacs_encoding:
            norm_emacs_encoding = _norm_encoding(emacs_encoding)
            if self._accessor.decode(norm_emacs_encoding):
                log.debug("encoding: encoding from Emacs coding var: %r",
                          norm_emacs_encoding)
                self.encoding = norm_emacs_encoding
                return
            else:
                log.debug("encoding: Emacs coding var (%r) was *wrong*",
                          norm_emacs_encoding)
                self._encoding_bozo(
                    u"Emacs coding var (%s) could not decode %s"
                     % (norm_emacs_encoding, self._accessor))

        # 8. Vi[m]-style local vars.
        vi_vars = self._get_vi_vars(head_bytes)
        vi_encoding = vi_vars.get("fileencoding") or vi_vars.get("fenc")
        if not vi_encoding:
            vi_vars = self._get_vi_vars(self._accessor.tail_bytes)
            vi_encoding = vi_vars.get("fileencoding") or vi_vars.get("fenc")
        if vi_encoding:
            norm_vi_encoding = _norm_encoding(vi_encoding)
            if self._accessor.decode(norm_vi_encoding):
                log.debug("encoding: encoding from Vi[m] coding var: %r",
                          norm_vi_encoding)
                self.encoding = norm_vi_encoding
                return
            else:
                log.debug("encoding: Vi[m] coding var (%r) was *wrong*",
                          norm_vi_encoding)
                self._encoding_bozo(
                    u"Vi[m] coding var (%s) could not decode %s"
                     % (norm_vi_encoding, self._accessor))

        # 9. Heuristic checks for UTF-16 without BOM.
        utf16_encoding = None
        head_odd_bytes  = head_bytes[0::2]
        head_even_bytes = head_bytes[1::2]
        head_markers = ["<?xml", "#!"]
        for head_marker in head_markers:
            length = len(head_marker)
            if head_odd_bytes.startswith(head_marker) \
               and head_even_bytes[0:length] == '\x00'*length:
                utf16_encoding = "utf-16-le"
                break
            elif head_even_bytes.startswith(head_marker) \
               and head_odd_bytes[0:length] == '\x00'*length:
                utf16_encoding = "utf-16-be"
                break
        internal_markers = ["coding"]
        for internal_marker in internal_markers:
            length = len(internal_marker)
            try:
                idx = head_odd_bytes.index(internal_marker)
            except ValueError:
                pass
            else:
                if head_even_bytes[idx:idx+length] == '\x00'*length:
                    utf16_encoding = "utf-16-le"
            try:
                idx = head_even_bytes.index(internal_marker)
            except ValueError:
                pass
            else:
                if head_odd_bytes[idx:idx+length] == '\x00'*length:
                    utf16_encoding = "utf-16-be"
        if utf16_encoding:
            if self._accessor.decode(utf16_encoding):
                log.debug("encoding: guessed encoding: %r", utf16_encoding)
                self.encoding = utf16_encoding
                return

        # 10. Give UTF-8 a try.
        norm_utf8_encoding = _norm_encoding("utf-8")
        if self._accessor.decode(norm_utf8_encoding):
            log.debug("UTF-8 encoding: %r", norm_utf8_encoding)
            self.encoding = norm_utf8_encoding
            return   

        # 11. Lang-specific fallback (e.g. XML -> utf-8, Python -> ascii, ...).
        # Note: A potential problem here is that a fallback encoding here that
        # is a pre-Unicode Single-Byte encoding (like iso8859-1) always "works"
        # so the subsequent heuristics never get tried.
        fallback_encoding = None
        fallback_lang = None
        if self.langinfo:
            fallback_lang = self.langinfo.name
            fallback_encoding = self.langinfo.conformant_attr("default_encoding")
        if fallback_encoding:
            if self._accessor.decode(fallback_encoding):
                log.debug("encoding: fallback encoding for %s: %r",
                          fallback_lang, fallback_encoding)
                self.encoding = fallback_encoding
                return
            else:
                log.debug("encoding: %s fallback encoding (%r) was *wrong*",
                          fallback_lang, fallback_encoding)
                self._encoding_bozo(
                    u"%s fallback encoding (%s) could not decode %s"
                     % (fallback_lang, fallback_encoding, self._accessor))

        # 12. chardet (http://chardet.feedparser.org/)
        # Note: I'm leary of using this b/c (a) it's a sizeable perf
        # hit and (b) false positives -- for example, the first 8kB of
        # /usr/bin/php on Mac OS X 10.4.10 is ISO-8859-2 with 44%
        # confidence. :)
        # Solution: (a) Only allow for content we know is not binary
        # (from langinfo association); and (b) can be disabled via
        # CHARDET_ENABLED class attribute.
        if self.CHARDET_ENABLED and self.langinfo and self.langinfo.is_text:
            try:
                import chardet
            except ImportError:
                warnings.warn("no chardet module to aid in guessing encoding",
                              ChardetImportWarning)
            else:
                chardet_info = chardet.detect(head_bytes)
                if chardet_info["encoding"] \
                   and chardet_info["confidence"] > self.CHARDET_THRESHHOLD:
                    chardet_encoding = chardet_info["encoding"]
                    norm_chardet_encoding = _norm_encoding(chardet_encoding)
                    if self._accessor.decode(norm_chardet_encoding):
                        log.debug("chardet encoding: %r", chardet_encoding)
                        self.encoding = norm_chardet_encoding
                        return
     
        # 13. locale.getpreferredencoding()
        # Typical values for this:
        #   Windows:    cp1252 (aka windows-1252)
        #   Mac OS X:   mac-roman
        #   Linux:      UTF-8 (modern Linux anyway)
        #   Solaris 8:  464 (aka ASCII)
        locale_encoding = locale.getpreferredencoding()
        if locale_encoding:
            norm_locale_encoding = _norm_encoding(locale_encoding)
            if self._accessor.decode(norm_locale_encoding):
                log.debug("encoding: locale preferred encoding: %r",
                          locale_encoding)
                self.encoding = norm_locale_encoding
                return

        # 14. iso8859-1
        norm_fallback8bit_encoding = _norm_encoding("iso8859-1")
        if self._accessor.decode(norm_fallback8bit_encoding):
            log.debug("fallback 8-bit encoding: %r", norm_fallback8bit_encoding)
            self.encoding = norm_fallback8bit_encoding
            return

        # We couldn't find an encoding that works. Give up and presume
        # this is binary content.
        self.is_text = False

    def _encoding_bozo(self, reason):
        self.encoding_bozo = True
        if self.encoding_bozo_reasons is None:
            self.encoding_bozo_reasons = []
        self.encoding_bozo_reasons.append(reason)

    # c.f. http://www.xml.com/axml/target.html#NT-prolog
    _xml_prolog_pat = re.compile(
        r'''<\?xml
            (   # strict ordering is reqd but we'll be liberal here
                \s+version=['"](?P<ver>.*?)['"]
            |   \s+encoding=['"](?P<enc>.*?)['"]
            )+
            .*? # other possible junk
            \s*\?>
        ''',
        re.VERBOSE | re.DOTALL
    )
    def _get_xml_prolog_info(self, head_bytes):
        """Parse out info from the '<?xml version=...' prolog, if any.
        
        Returns (<has-xml-prolog>, <xml-version>, <xml-encoding>). Examples:

            (False, None, None)
            (True, "1.0", None)
            (True, "1.0", "UTF-16")
        """
        # Presuming an 8-bit encoding. If it is UTF-16 or UTF-32, then
        # that should have been picked up by an earlier BOM check or via
        # the subsequent heuristic check for UTF-16 without a BOM.
        if not head_bytes.startswith("<?xml"):
            return  (False, None, None)

        # Try to extract more info from the prolog.
        match = self._xml_prolog_pat.match(head_bytes)
        if not match:
            if log.isEnabledFor(logging.DEBUG):
                log.debug("`%s': could not match XML prolog: '%s'", self.path,
                          _one_line_summary_from_text(head_bytes, 40))
            return (False, None, None)
        xml_version = match.group("ver")
        xml_encoding = match.group("enc")
        return (True, xml_version, xml_encoding)

    _html_meta_tag_pat = re.compile("""
        (<meta
        (?:\s+[\w-]+\s*=\s*(?:".*?"|'.*?'))+  # attributes
        \s*/?>)
        """,
        re.IGNORECASE | re.VERBOSE
    )
    _html_attr_pat = re.compile(
        # Currently requiring XML attrs (i.e. quoted value).
        '''(?:\s+([\w-]+)\s*=\s*(".*?"|'.*?'))'''
    )
    _http_content_type_splitter = re.compile(";\s*")
    def _get_http_content_type_info(self, head_bytes):
        """Returns info extracted from an HTML content-type meta tag if any.
        Returns (<has-http-content-type-info>, <content-type>, <charset>).

        For example:
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        yields:
            (True, "text/html", "utf-8")
        """
        # Presuming an 8-bit encoding. If it is UTF-16 or UTF-32, then
        # that should have been picked up by an earlier BOM check.
        # Otherwise we rely on `chardet` to cover us.

        # Parse out '<meta ...>' tags, then the attributes in them.
        for meta_tag in self._html_meta_tag_pat.findall(head_bytes):
            meta = dict( (k.lower(), v[1:-1])
                for k,v in self._html_attr_pat.findall(meta_tag))
            if "http-equiv" in meta \
               and meta["http-equiv"].lower() == "content-type":
                content = meta.get("content", "")
                break
        else:
            return (False, None, None)

        # We found a http-equiv="Content-Type" tag, parse its content
        # attribute value.
        parts = [p.strip() for p in self._http_content_type_splitter.split(content)]
        if not parts:
            return (False, None, None)
        content_type = parts[0] or None
        for p in parts[1:]:
            if p.lower().startswith("charset="):
                charset = p[len("charset="):]
                if charset and charset[0] in ('"', "'"):
                    charset = charset[1:]
                if charset and charset[-1] in ('"', "'"):
                    charset = charset[:-1]
                break
        else:
            charset = None

        return (True, content_type, charset)

    #TODO: Note that this isn't going to catch the current HTML 5
    #      doctype:  '<!DOCTYPE html>'
    _doctype_decl_re = re.compile(r'''
        <!DOCTYPE
        \s+(?P<name>[a-zA-Z_:][\w:.-]*)
        \s+(?:
            SYSTEM\s+(["'])(?P<system_id_a>.*?)\2
            |
            PUBLIC
            \s+(["'])(?P<public_id_b>.*?)\4
            # HTML 3.2 and 2.0 doctypes don't include a system-id.
            (?:\s+(["'])(?P<system_id_b>.*?)\6)?
        )
        (\s*\[.*?\])?        
        \s*>
        ''', re.IGNORECASE | re.DOTALL | re.UNICODE | re.VERBOSE)
    def _get_doctype_decl_info(self, head):
        """Parse out DOCTYPE info from the given XML or HTML content.
        
        Returns a tuple of the form:
            (<has-doctype-decl>, <doctype-decl>,
             <name>, <public-id>, <system-id>)
        
        The <public-id> is normalized as per this comment in the XML 1.0
        spec:
            Before a match is attempted, all strings of white space in the
            public identifier must be normalized to single space
            characters (#x20), and leading and trailing white space must
            be removed.
        
        Examples:
            (False, None, None, None, None)
            (True, '<!DOCTYPE greeting SYSTEM "hello.dtd">',
             'greeting', None, 'hello.dtd'),
            (True,
             '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">',
             'html',
             '-//W3C//DTD XHTML 1.0 Transitional//EN',
             'http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd')
        
        Here is the spec for DOCTYPE decls in XML:
            http://www.xml.com/axml/target.html#NT-doctypedecl
        We loosely follow this to allow for some decls in HTML that isn't
        proper XML. As well, we are only parsing out decls that reference
        an external ID, as opposed to those that define entities locally.
        """
        if "<!DOCTYPE" not in head:  # quick out
            return (False, None, None, None, None)
        m = self._doctype_decl_re.search(head)
        if not m:
            return (False, None, None, None, None)
        
        d = m.groupdict()
        name = d.get("name")
        system_id = d.get("system_id_a") or d.get("system_id_b")
        public_id = d.get("public_id_b")
        if public_id:
            public_id = re.sub("\s+", ' ', public_id.strip())  # normalize
        return (True, m.group(0), name, public_id, system_id)

    _emacs_vars_head_pat = re.compile("-\*-\s*(.*?)\s*-\*-")

    _emacs_head_vars_cache = None
    def _get_emacs_head_vars(self, head_bytes):
        """Return a dictionary of emacs-style local variables in the head.

        "Head" emacs vars on the ones in the '-*- ... -*-' one-liner.
        
        Parsing is done loosely according to this spec (and according to
        some in-practice deviations from this):
        http://www.gnu.org/software/emacs/manual/html_node/emacs/Specifying-File-Variables.html#Specifying-File-Variables
        """
        # Presuming an 8-bit encoding. If it is UTF-16 or UTF-32, then
        # that should have been picked up by an earlier BOM check.
        # Otherwise we rely on `chardet` to cover us.
        
        if self._emacs_head_vars_cache is not None:
            return self._emacs_head_vars_cache

        # Search the head for a '-*-'-style one-liner of variables.
        emacs_vars = {}
        if "-*-" in head_bytes:
            match = self._emacs_vars_head_pat.search(head_bytes)
            if match:
                emacs_vars_str = match.group(1)
                if '\n' in emacs_vars_str:
                    raise ValueError("local variables error: -*- not "
                                     "terminated before end of line")
                emacs_var_strs = [s.strip() for s in emacs_vars_str.split(';')
                                  if s.strip()]
                if len(emacs_var_strs) == 1 and ':' not in emacs_var_strs[0]:
                    # While not in the spec, this form is allowed by emacs:
                    #   -*- Tcl -*-
                    # where the implied "variable" is "mode". This form
                    # is only allowed if there are no other variables.
                    emacs_vars["mode"] = emacs_var_strs[0].strip()
                else:
                    for emacs_var_str in emacs_var_strs:
                        try:
                            variable, value = emacs_var_str.strip().split(':', 1)
                        except ValueError:
                            log.debug("emacs variables error: malformed -*- "
                                      "line: %r", emacs_var_str)
                            continue
                        # Lowercase the variable name because Emacs allows "Mode"
                        # or "mode" or "MoDe", etc.
                        emacs_vars[variable.lower()] = value.strip()

        # Unquote values.
        for var, val in emacs_vars.items():
            if len(val) > 1 and (val.startswith('"') and val.endswith('"')
               or val.startswith('"') and val.endswith('"')):
                emacs_vars[var] = val[1:-1]

        self._emacs_head_vars_cache = emacs_vars    
        return emacs_vars

    # This regular expression is intended to match blocks like this:
    #    PREFIX Local Variables: SUFFIX
    #    PREFIX mode: Tcl SUFFIX
    #    PREFIX End: SUFFIX
    # Some notes:
    # - "[ \t]" is used instead of "\s" to specifically exclude newlines
    # - "(\r\n|\n|\r)" is used instead of "$" because the sre engine does
    #   not like anything other than Unix-style line terminators.
    _emacs_vars_tail_pat = re.compile(r"""^
        (?P<prefix>(?:[^\r\n|\n|\r])*?)
        [\ \t]*Local\ Variables:[\ \t]*
        (?P<suffix>.*?)(?:\r\n|\n|\r)
        (?P<content>.*?\1End:)
        """, re.IGNORECASE | re.MULTILINE | re.DOTALL | re.VERBOSE)

    _emacs_tail_vars_cache = None
    def _get_emacs_tail_vars(self, tail_bytes):
        r"""Return a dictionary of emacs-style local variables in the tail.

        "Tail" emacs vars on the ones in the multi-line "Local
        Variables:" block.

        >>> TextInfo()._get_emacs_tail_vars('# Local Variables:\n# foo: bar\n# End:')
        {'foo': 'bar'}
        >>> TextInfo()._get_emacs_tail_vars('# Local Variables:\n# foo: bar\\\n#  baz\n# End:')
        {'foo': 'bar baz'}
        >>> TextInfo()._get_emacs_tail_vars('# Local Variables:\n# quoted: "bar "\n# End:')
        {'quoted': 'bar '}
    
        Parsing is done according to this spec (and according to some
        in-practice deviations from this):
            http://www.gnu.org/software/emacs/manual/html_chapter/emacs_33.html#SEC485
        """
        # Presuming an 8-bit encoding. If it is UTF-16 or UTF-32, then
        # that should have been picked up by an earlier BOM check.
        # Otherwise we rely on `chardet` to cover us.
        
        if self._emacs_tail_vars_cache is not None:
            return self._emacs_tail_vars_cache
        
        emacs_vars = {}
        if "Local Variables" not in tail_bytes:
            self._emacs_tail_vars_cache = emacs_vars    
            return emacs_vars

        match = self._emacs_vars_tail_pat.search(tail_bytes)
        if match:
            prefix = match.group("prefix")
            suffix = match.group("suffix")
            lines = match.group("content").splitlines(0)
            #print "prefix=%r, suffix=%r, content=%r, lines: %s"\
            #      % (prefix, suffix, match.group("content"), lines)

            # Validate the Local Variables block: proper prefix and suffix
            # usage.
            for i, line in enumerate(lines):
                if not line.startswith(prefix):
                    log.debug("emacs variables error: line '%s' "
                              "does not use proper prefix '%s'"
                              % (line, prefix))
                    return {}
                # Don't validate suffix on last line. Emacs doesn't care,
                # neither should we.
                if i != len(lines)-1 and not line.endswith(suffix):
                    log.debug("emacs variables error: line '%s' "
                              "does not use proper suffix '%s'"
                              % (line, suffix))
                    return {}

            # Parse out one emacs var per line.
            continued_for = None
            for line in lines[:-1]: # no var on the last line ("PREFIX End:")
                if prefix: line = line[len(prefix):] # strip prefix
                if suffix: line = line[:-len(suffix)] # strip suffix
                line = line.strip()
                if continued_for:
                    variable = continued_for
                    if line.endswith('\\'):
                        line = line[:-1].rstrip()
                    else:
                        continued_for = None
                    emacs_vars[variable] += ' ' + line
                else:
                    try:
                        variable, value = line.split(':', 1)
                    except ValueError:
                        log.debug("local variables error: missing colon "
                                  "in local variables entry: '%s'" % line)
                        continue
                    # Do NOT lowercase the variable name, because Emacs only
                    # allows "mode" (and not "Mode", "MoDe", etc.) in this block.
                    value = value.strip()
                    if value.endswith('\\'):
                        value = value[:-1].rstrip()
                        continued_for = variable
                    else:
                        continued_for = None
                    emacs_vars[variable] = value

        # Unquote values.
        for var, val in emacs_vars.items():
            if len(val) > 1 and (val.startswith('"') and val.endswith('"')
               or val.startswith('"') and val.endswith('"')):
                emacs_vars[var] = val[1:-1]

        self._emacs_tail_vars_cache = emacs_vars    
        return emacs_vars

    # Note: It might nice if parser also gave which of 'vi, vim, ex' and
    # the range in the accessor.
    _vi_vars_pats_and_splitters = [
        (re.compile(r'[ \t]+(vi|vim([<>=]?\d{3})?|ex):\s*set? (?P<rhs>.*?)(?<!\\):', re.M),
         re.compile(r'[ \t]+')),
        (re.compile(r'[ \t]+(vi|vim([<>=]?\d{3})?|ex):\s*(?P<rhs>.*?)$', re.M),
         re.compile(r'[ \t:]+')),
        (re.compile(r'^(vi|vim([<>=]?\d{3})?):\s*set? (?P<rhs>.*?)(?<!\\):', re.M),
         re.compile(r'[ \t]+')),
    ]
    _vi_vars_cache = None
    def _get_vi_vars(self, bytes):
        r"""Return a dict of Vi[m] modeline vars.

        See ":help modeline" in Vim for a spec.

            >>> TextInfo()._get_vi_vars("/* vim: set ai tw=75: */")
            {'ai': None, 'tw': 75}
            >>> TextInfo()._get_vi_vars("vim: set ai tw=75: bar")
            {'ai': None, 'tw': 75}

            >>> TextInfo()._get_vi_vars("vi: set foo:bar")
            {'foo': None}
            >>> TextInfo()._get_vi_vars(" vi: se foo:bar")
            {'foo': None}
            >>> TextInfo()._get_vi_vars(" ex: se foo:bar")
            {'foo': None}

            >>> TextInfo()._get_vi_vars(" vi:noai:sw=3 tw=75")
            {'tw': 75, 'sw': 3, 'noai': None}
            >>> TextInfo()._get_vi_vars(" vi:noai:sw=3 tw=75")
            {'tw': 75, 'sw': 3, 'noai': None}

            >>> TextInfo()._get_vi_vars("ex: se foo:bar")
            {}

        Some edge cases:

            >>> TextInfo()._get_vi_vars(r"/* vi:set dir=c\:\tmp: */")
            {'dir': 'c:\\tmp'}
        """
        # Presume 8-bit encoding... yada yada.
        
        if self._vi_vars_cache is not None:
            return self._vi_vars_cache
        
        vi_vars = {}
        
        #TODO: Consider reducing support to just "vi:" for speed. This
        #      function takes way too much time.
        if "vi:" not in bytes and "ex:" not in bytes and "vim:" not in bytes:
            self._vi_vars_cache = vi_vars
            return vi_vars
        
        for pat, splitter in self._vi_vars_pats_and_splitters:
            match = pat.search(bytes)
            if match:
                for var_str in splitter.split(match.group("rhs")):
                    if '=' in var_str:
                        name, value = var_str.split('=', 1)
                        try:
                            vi_vars[name] = int(value)
                        except ValueError:
                            vi_vars[name] = value.replace('\\:', ':')
                    else:
                        vi_vars[var_str] = None
                break
        self._vi_vars_cache = vi_vars
        return vi_vars

    def _get_bom_info(self):
        r"""Returns (<has-bom>, <bom>, <bom-encoding>). Examples:

            (True, '\xef\xbb\xbf', "utf-8") 
            (True, '\xff\xfe', "utf-16-le") 
            (False, None, None)
        """
        boms_and_encodings = [ # in order from longest to shortest
            (codecs.BOM_UTF32_LE, "utf-32-le"),
            (codecs.BOM_UTF32_BE, "utf-32-be"),
            (codecs.BOM_UTF8, "utf-8"),
            (codecs.BOM_UTF16_LE, "utf-16-le"),
            (codecs.BOM_UTF16_BE, "utf-16-be"),
        ]
        head_4 = self._accessor.head_4_bytes
        for bom, encoding in boms_and_encodings:
            if head_4.startswith(bom):
                return (True, bom, encoding)
                break
        else:
            return (False, None, None)

    def _classify_from_filename(self, lidb, env):
        """Classify from the path *filename* only.
        
        Sets `lang' and `langinfo', if can be determined.
        """
        filename = basename(self.path)
        
        if env is not None:
            li = env.langinfo_from_filename(filename)
            if li:
                log.debug("lang from env: `%s' -> `%s'", filename, li.name)
                self.langinfo = li
                self.lang = li.name
                self.is_text = li.is_text
                return

        # ...from the ext
        idx = 0
        while True:
            idx = filename.find('.', idx)
            if idx == -1:
                break
            ext = filename[idx:]
            li = lidb.langinfo_from_ext(ext)
            if li:
                log.debug("lang from ext: `%s' -> `%s'", ext, li.name)
                self.langinfo = li
                self.lang = li.name
                self.is_text = li.is_text
                return
            idx += 1

        # ...from file basename
        li = lidb.langinfo_from_filename(filename)
        if li:
            log.debug("lang from filename: `%s' -> `%s'", filename, li.name)
            self.langinfo = li
            self.lang = li.name
            self.is_text = li.is_text
            return

    def _classify_from_stat(self, lidb):
        """Set some `file_*' attributes from stat mode."""
        from stat import S_ISREG, S_ISDIR, S_ISLNK, S_ISFIFO, S_ISSOCK, \
                         S_ISBLK, S_ISCHR, S_IMODE, S_IFMT
        stat = self._accessor.stat
        st_mode = stat.st_mode
        self.file_type = S_IFMT(st_mode)
        self.file_mode = S_IMODE(st_mode)
        self.file_stat = stat
        if S_ISREG(st_mode):
            self.file_type_name = "regular file"
        elif S_ISDIR(st_mode):
            self.file_type_name = "directory"
        elif S_ISLNK(st_mode):
            self.file_type_name = "symbolic link"
        elif S_ISFIFO(st_mode):
            self.file_type_name = "fifo"
        elif S_ISSOCK(st_mode):
            self.file_type_name = "socket"
        elif S_ISBLK(st_mode):
            self.file_type_name = "block special"
        elif S_ISCHR(st_mode):
            self.file_type_name = "character special"


def _norm_encoding(encoding):
    """Normalize the encoding name -- where "normalized" is what
    Python's codec's module calls it.

    Interesting link:
        The IANA-registered set of character sets.
        http://www.iana.org/assignments/character-sets
    """
    try:
        # This requires Python >=2.5.
        return codecs.lookup(encoding).name
    except LookupError:
        return encoding


#---- accessor API
# The idea here is to abstract accessing the text file content being
# classified to allow, e.g. classifying content without a file, from
# a Komodo buffer, etc.

class Accessor(object):
    """Virtual base class defining Accessor API for accessing
    text content.
    """
    # API:
    #   prop head_bytes -> head 8k bytes
    #   prop head_4_bytes -> head 4 bytes (useful for BOM detection) 
    #   prop tail_bytes -> tail 8k bytes
    #   def bytes_range(start, end) -> bytes in that range

    HEAD_SIZE = pow(2, 13) # 8k
    TAIL_SIZE = pow(2, 13) # 8k

    encoding = None
    text = None

    _unsuccessful_encodings = None
    def decode(self, encoding):
        """Decodes bytes with the given encoding and, if successful,
        sets `self.text` with the decoded result and returns True.
        Otherwise, returns False.

        Side-effects: On success, sets `self.text` and `self.encoding`.
       
        Optimization: First an attempt is made to decode
        `self.head_bytes` instead of all of `self.bytes`. This allows
        for the normal usage in `TextInfo._classify_encoding()` to *not*
        bother fully reading binary files that could not be decoded.

        Optimization: Decoding attempts are cached to not bother
        attempting a failed decode twice.
        """
        if self._unsuccessful_encodings is None:
            self._unsuccessful_encodings = set()
        if encoding in self._unsuccessful_encodings:
            return False
        elif encoding == self.encoding:
            return True

        head_bytes = self.head_bytes
        try:
            head_bytes.decode(encoding, 'strict')
        except LookupError, ex:
            log.debug("encoding lookup error: %r", encoding)
            self._unsuccessful_encodings.add(encoding)
            return False
        except UnicodeError, ex:
            # If the decode failed in the last few bytes, it might be
            # because a multi-surrogate was cutoff by the head. Ignore
            # the error here, if it is truly not of this encoding, the
            # full file decode will fail.
            if ex.start >= self.HEAD_SIZE - 5:
                # '5' because the max num bytes to encode a single char
                # in any encoding is 6 bytes (in UTF-8).
                pass
            else:
                self._unsuccessful_encodings.add(encoding)
                return False
        try:
            self.text = self.bytes.decode(encoding, 'strict')
        except UnicodeError, ex:
            self._unsuccessful_encodings.add(encoding)
            return False
        self.encoding = encoding
        return True


class PathAccessor(Accessor):
    """Accessor API for a path."""
    (READ_NONE,             # _file==None, file not opened yet
     READ_HEAD,             # _bytes==<head bytes>
     READ_TAIL,             # _bytes==<head>, _bytes_tail==<tail>
     READ_ALL) = range(4)   # _bytes==<all>, _bytes_tail==None, _file closed
    _read_state = READ_NONE # one of the READ_* states
    _file = None
    _bytes = None
    _bytes_tail = None

    def __init__(self, path, follow_symlinks=False):
        self.path = path
        self.follow_symlinks = follow_symlinks

    def __str__(self):
        return "path `%s'" % self.path 

    _stat_cache = None
    @property
    def stat(self):
        if self._stat_cache is None:
            if self.follow_symlinks:
                self._stat_cache = os.stat(self.path)
            else:
                self._stat_cache = os.lstat(self.path)
        return self._stat_cache

    @property
    def size(self):
        return self.stat.st_size

    def __del__(self):
        self.close()

    def close(self):
        if self._file and not self._file.closed:
            self._file.close()

    def _read(self, state):
        """Read up to at least `state`."""
        #TODO: If `follow_symlinks` is False and this is a symlink we
        #      must use os.readlink() here.
        # It is the job of the caller to only call _read() if necessary.
        assert self._read_state < state

        try:
            if self._read_state == self.READ_NONE:
                assert self._file is None and self._bytes is None
                self._file = open(self.path, 'rb')
                if state == self.READ_HEAD:
                    self._bytes = self._file.read(self.HEAD_SIZE)
                    self._read_state = (self.size <= self.HEAD_SIZE
                        and self.READ_ALL or self.READ_HEAD)
                elif state == self.READ_TAIL:
                    if self.size <= self.HEAD_SIZE + self.TAIL_SIZE:
                        self._bytes = self._file.read()
                        self._read_state = self.READ_ALL
                    else:
                        self._bytes = self._file.read(self.HEAD_SIZE)
                        self._file.seek(-self.TAIL_SIZE, 2) # 2 == relative to end
                        self._bytes_tail = self._file.read(self.TAIL_SIZE)
                        self._read_state = self.READ_TAIL
                elif state == self.READ_ALL:
                    self._bytes = self._file.read()
                    self._read_state = self.READ_ALL
    
            elif self._read_state == self.READ_HEAD:
                if state == self.READ_TAIL:
                    if self.size <= self.HEAD_SIZE + self.TAIL_SIZE:
                        self._bytes += self._file.read()
                        self._read_state = self.READ_ALL
                    else:
                        self._file.seek(-self.TAIL_SIZE, 2) # 2 == relative to end
                        self._bytes_tail = self._file.read(self.TAIL_SIZE)
                        self._read_state = self.READ_TAIL
                elif state == self.READ_ALL:
                    self._bytes += self._file.read()
                    self._read_state = self.READ_ALL
                    
            elif self._read_state == self.READ_TAIL:
                assert state == self.READ_ALL
                self._file.seek(self.HEAD_SIZE, 0) # 0 == relative to start
                remaining_size = self.size - self.HEAD_SIZE - self.TAIL_SIZE
                assert remaining_size > 0, \
                    "negative remaining bytes to read from '%s': %d" \
                    % (self.path, self.size)
                self._bytes += self._file.read(remaining_size)
                self._bytes += self._bytes_tail
                self._bytes_tail = None
                self._read_state = self.READ_ALL
                    
            if self._read_state == self.READ_ALL:
                self.close()
        except Exception, ex:
            log.warn("Could not read file: %r due to: %r", self.path, ex)
            raise

    def strip_bom(self, bom):
        """This should be called by the user of this class to strip a
        detected BOM from the bytes for subsequent decoding and
        analysis.
        """
        assert self._bytes[:len(bom)] == bom
        self._bytes = self._bytes[len(bom):]

    @property
    def head_bytes(self):
        """The first 8k raw bytes of the document."""
        if self._read_state < self.READ_HEAD:
            self._read(self.READ_HEAD)
        return self._bytes[:self.HEAD_SIZE]

    @property
    def head_4_bytes(self):
        if self._read_state < self.READ_HEAD:
            self._read(self.READ_HEAD)
        return self._bytes[:4]

    @property
    def tail_bytes(self):
        if self._read_state < self.READ_TAIL:
            self._read(self.READ_TAIL)
        if self._read_state == self.READ_ALL:
            return self._bytes[-self.TAIL_SIZE:]
        else:
            return self._bytes_tail

    def bytes_range(self, start, end):
        if self._read_state < self.READ_ALL:
            self._read(self.READ_ALL)
        return self._bytes[start:end]

    @property
    def bytes(self):
        if self._read_state < self.READ_ALL:
            self._read(self.READ_ALL)
        return self._bytes



#---- internal support stuff

# Recipe: regex_from_encoded_pattern (1.0)
def _regex_from_encoded_pattern(s):
    """'foo'    -> re.compile(re.escape('foo'))
       '/foo/'  -> re.compile('foo')
       '/foo/i' -> re.compile('foo', re.I)
    """
    if s.startswith('/') and s.rfind('/') != 0:
        # Parse it: /PATTERN/FLAGS
        idx = s.rfind('/')
        pattern, flags_str = s[1:idx], s[idx+1:]
        flag_from_char = {
            "i": re.IGNORECASE,
            "l": re.LOCALE,
            "s": re.DOTALL,
            "m": re.MULTILINE,
            "u": re.UNICODE,
        }
        flags = 0
        for char in flags_str:
            try:
                flags |= flag_from_char[char]
            except KeyError:
                raise ValueError("unsupported regex flag: '%s' in '%s' "
                                 "(must be one of '%s')"
                                 % (char, s, ''.join(flag_from_char.keys())))
        return re.compile(s[1:idx], flags)
    else: # not an encoded regex
        return re.compile(re.escape(s))

# Recipe: text_escape (0.2)
def _escaped_text_from_text(text, escapes="eol"):
    r"""Return escaped version of text.

        "escapes" is either a mapping of chars in the source text to
            replacement text for each such char or one of a set of
            strings identifying a particular escape style:
                eol
                    replace EOL chars with '\r' and '\n', maintain the actual
                    EOLs though too
                whitespace
                    replace EOL chars as above, tabs with '\t' and spaces
                    with periods ('.')
                eol-one-line
                    replace EOL chars with '\r' and '\n'
                whitespace-one-line
                    replace EOL chars as above, tabs with '\t' and spaces
                    with periods ('.')
    """
    #TODO:
    # - Add 'c-string' style.
    # - Add _escaped_html_from_text() with a similar call sig.
    import re
    
    if isinstance(escapes, basestring):
        if escapes == "eol":
            escapes = {'\r\n': "\\r\\n\r\n", '\n': "\\n\n", '\r': "\\r\r"}
        elif escapes == "whitespace":
            escapes = {'\r\n': "\\r\\n\r\n", '\n': "\\n\n", '\r': "\\r\r",
                       '\t': "\\t", ' ': "."}
        elif escapes == "eol-one-line":
            escapes = {'\n': "\\n", '\r': "\\r"}
        elif escapes == "whitespace-one-line":
            escapes = {'\n': "\\n", '\r': "\\r", '\t': "\\t", ' ': '.'}
        else:
            raise ValueError("unknown text escape style: %r" % escapes)

    # Sort longer replacements first to allow, e.g. '\r\n' to beat '\r' and
    # '\n'.
    escapes_keys = escapes.keys()
    try:
        escapes_keys.sort(key=lambda a: len(a), reverse=True)
    except TypeError:
        # Python 2.3 support: sort() takes no keyword arguments
        escapes_keys.sort(lambda a,b: cmp(len(a), len(b)))
        escapes_keys.reverse()
    def repl(match):
        val = escapes[match.group(0)]
        return val
    escaped = re.sub("(%s)" % '|'.join([re.escape(k) for k in escapes_keys]),
                     repl,
                     text)

    return escaped


def _one_line_summary_from_text(text, length=78,
        escapes={'\n':"\\n", '\r':"\\r", '\t':"\\t"}):
    r"""Summarize the given text with one line of the given length.
    
        "text" is the text to summarize
        "length" (default 78) is the max length for the summary
        "escapes" is a mapping of chars in the source text to
            replacement text for each such char. By default '\r', '\n'
            and '\t' are escaped with their '\'-escaped repr.
    """
    if len(text) > length:
        head = text[:length-3]
    else:
        head = text
    escaped = _escaped_text_from_text(head, escapes)
    if len(text) > length:
        summary = escaped[:length-3] + "..."
    else:
        summary = escaped
    return summary


# Recipe: paths_from_path_patterns (0.5)
def _should_include_path(path, includes, excludes):
    """Return True iff the given path should be included."""
    from os.path import basename
    from fnmatch import fnmatch

    base = basename(path)
    if includes:
        for include in includes:
            if fnmatch(base, include):
                try:
                    log.debug("include `%s' (matches `%s')", path, include)
                except (NameError, AttributeError):
                    pass
                break
        else:
            try:
                log.debug("exclude `%s' (matches no includes)", path)
            except (NameError, AttributeError):
                pass
            return False
    for exclude in excludes:
        if fnmatch(base, exclude):
            try:
                log.debug("exclude `%s' (matches `%s')", path, exclude)
            except (NameError, AttributeError):
                pass
            return False
    return True

def _walk(top, topdown=True, onerror=None, follow_symlinks=False):
    """A version of `os.walk()` with a couple differences regarding symlinks.
    
    1. follow_symlinks=False (the default): A symlink to a dir is
       returned as a *non*-dir. In `os.walk()`, a symlink to a dir is
       returned in the *dirs* list, but it is not recursed into.
    2. follow_symlinks=True: A symlink to a dir is returned in the
       *dirs* list (as with `os.walk()`) but it *is conditionally*
       recursed into (unlike `os.walk()`).
       
       A symlinked dir is only recursed into if it is to a deeper dir
       within the same tree. This is my understanding of how `find -L
       DIR` works.

    TODO: put as a separate recipe
    """
    from os.path import join, isdir, islink, abspath

    # We may not have read permission for top, in which case we can't
    # get a list of the files the directory contains.  os.path.walk
    # always suppressed the exception then, rather than blow up for a
    # minor reason when (say) a thousand readable directories are still
    # left to visit.  That logic is copied here.
    try:
        names = os.listdir(top)
    except OSError, err:
        if onerror is not None:
            onerror(err)
        return

    dirs, nondirs = [], []
    if follow_symlinks:
        for name in names:
            if isdir(join(top, name)):
                dirs.append(name)
            else:
                nondirs.append(name)
    else:
        for name in names:
            path = join(top, name)
            if islink(path):
                nondirs.append(name)
            elif isdir(path):
                dirs.append(name)
            else:
                nondirs.append(name)

    if topdown:
        yield top, dirs, nondirs
    for name in dirs:
        path = join(top, name)
        if follow_symlinks and islink(path):
            # Only walk this path if it links deeper in the same tree.
            top_abs = abspath(top)
            link_abs = abspath(join(top, os.readlink(path)))
            if not link_abs.startswith(top_abs + os.sep):
                continue
        for x in _walk(path, topdown, onerror, follow_symlinks=follow_symlinks):
            yield x
    if not topdown:
        yield top, dirs, nondirs

_NOT_SPECIFIED = ("NOT", "SPECIFIED")
def _paths_from_path_patterns(path_patterns, files=True, dirs="never",
                              recursive=True, includes=[], excludes=[],
                              skip_dupe_dirs=False,
                              follow_symlinks=False,
                              on_error=_NOT_SPECIFIED):
    """_paths_from_path_patterns([<path-patterns>, ...]) -> file paths

    Generate a list of paths (files and/or dirs) represented by the given path
    patterns.

        "path_patterns" is a list of paths optionally using the '*', '?' and
            '[seq]' glob patterns.
        "files" is boolean (default True) indicating if file paths
            should be yielded
        "dirs" is string indicating under what conditions dirs are
            yielded. It must be one of:
              never             (default) never yield dirs
              always            yield all dirs matching given patterns
              if-not-recursive  only yield dirs for invocations when
                                recursive=False
            See use cases below for more details.
        "recursive" is boolean (default True) indicating if paths should
            be recursively yielded under given dirs.
        "includes" is a list of file patterns to include in recursive
            searches.
        "excludes" is a list of file and dir patterns to exclude.
            (Note: This is slightly different than GNU grep's --exclude
            option which only excludes *files*.  I.e. you cannot exclude
            a ".svn" dir.)
        "skip_dupe_dirs" can be set True to watch for and skip
            descending into a dir that has already been yielded. Note
            that this currently does not dereference symlinks.
        "follow_symlinks" is a boolean indicating whether to follow
            symlinks (default False). To guard against infinite loops
            with circular dir symlinks, only dir symlinks to *deeper*
            are followed.
        "on_error" is an error callback called when a given path pattern
            matches nothing:
                on_error(PATH_PATTERN)
            If not specified, the default is look for a "log" global and
            call:
                log.error("`%s': No such file or directory")
            Specify None to do nothing.

    Typically this is useful for a command-line tool that takes a list
    of paths as arguments. (For Unix-heads: the shell on Windows does
    NOT expand glob chars, that is left to the app.)

    Use case #1: like `grep -r`
      {files=True, dirs='never', recursive=(if '-r' in opts)}
        script FILE     # yield FILE, else call on_error(FILE)
        script DIR      # yield nothing
        script PATH*    # yield all files matching PATH*; if none,
                        # call on_error(PATH*) callback
        script -r DIR   # yield files (not dirs) recursively under DIR
        script -r PATH* # yield files matching PATH* and files recursively
                        # under dirs matching PATH*; if none, call
                        # on_error(PATH*) callback

    Use case #2: like `file -r` (if it had a recursive option)
      {files=True, dirs='if-not-recursive', recursive=(if '-r' in opts)}
        script FILE     # yield FILE, else call on_error(FILE)
        script DIR      # yield DIR, else call on_error(DIR)
        script PATH*    # yield all files and dirs matching PATH*; if none,
                        # call on_error(PATH*) callback
        script -r DIR   # yield files (not dirs) recursively under DIR
        script -r PATH* # yield files matching PATH* and files recursively
                        # under dirs matching PATH*; if none, call
                        # on_error(PATH*) callback

    Use case #3: kind of like `find .`
      {files=True, dirs='always', recursive=(if '-r' in opts)}
        script FILE     # yield FILE, else call on_error(FILE)
        script DIR      # yield DIR, else call on_error(DIR)
        script PATH*    # yield all files and dirs matching PATH*; if none,
                        # call on_error(PATH*) callback
        script -r DIR   # yield files and dirs recursively under DIR
                        # (including DIR)
        script -r PATH* # yield files and dirs matching PATH* and recursively
                        # under dirs; if none, call on_error(PATH*)
                        # callback

    TODO: perf improvements (profile, stat just once)
    """
    from os.path import basename, exists, isdir, join, normpath, abspath, \
                        lexists, islink, realpath
    from glob import glob

    assert not isinstance(path_patterns, basestring), \
        "'path_patterns' must be a sequence, not a string: %r" % path_patterns
    GLOB_CHARS = '*?['

    if skip_dupe_dirs:
        searched_dirs = set()

    for path_pattern in path_patterns:
        # Determine the set of paths matching this path_pattern.
        for glob_char in GLOB_CHARS:
            if glob_char in path_pattern:
                paths = glob(path_pattern)
                break
        else:
            if follow_symlinks:
                paths = exists(path_pattern) and [path_pattern] or []
            else:
                paths = lexists(path_pattern) and [path_pattern] or []
        if not paths:
            if on_error is None:
                pass
            elif on_error is _NOT_SPECIFIED:
                try:
                    log.error("`%s': No such file or directory", path_pattern)
                except (NameError, AttributeError):
                    pass
            else:
                on_error(path_pattern)

        for path in paths:
            if (follow_symlinks or not islink(path)) and isdir(path):
                if skip_dupe_dirs:
                    canon_path = normpath(abspath(path))
                    if follow_symlinks:
                        canon_path = realpath(canon_path)
                    if canon_path in searched_dirs:
                        continue
                    else:
                        searched_dirs.add(canon_path)

                # 'includes' SHOULD affect whether a dir is yielded.
                if (dirs == "always"
                    or (dirs == "if-not-recursive" and not recursive)
                   ) and _should_include_path(path, includes, excludes):
                    yield path

                # However, if recursive, 'includes' should NOT affect
                # whether a dir is recursed into. Otherwise you could
                # not:
                #   script -r --include="*.py" DIR
                if recursive and _should_include_path(path, [], excludes):
                    for dirpath, dirnames, filenames in _walk(path, 
                            follow_symlinks=follow_symlinks):
                        dir_indeces_to_remove = []
                        for i, dirname in enumerate(dirnames):
                            d = join(dirpath, dirname)
                            if skip_dupe_dirs:
                                canon_d = normpath(abspath(d))
                                if follow_symlinks:
                                    canon_d = realpath(canon_d)
                                if canon_d in searched_dirs:
                                    dir_indeces_to_remove.append(i)
                                    continue
                                else:
                                    searched_dirs.add(canon_d)
                            if dirs == "always" \
                               and _should_include_path(d, includes, excludes):
                                yield d
                            if not _should_include_path(d, [], excludes):
                                dir_indeces_to_remove.append(i)
                        for i in reversed(dir_indeces_to_remove):
                            del dirnames[i]
                        if files:
                            for filename in sorted(filenames):
                                f = join(dirpath, filename)
                                if _should_include_path(f, includes, excludes):
                                    yield f

            elif files and _should_include_path(path, includes, excludes):
                yield path


class _NoReflowFormatter(optparse.IndentedHelpFormatter):
    """An optparse formatter that does NOT reflow the description."""
    def format_description(self, description):
        return description or ""

# Recipe: pretty_logging (0.1) in C:\trentm\tm\recipes\cookbook
class _PerLevelFormatter(logging.Formatter):
    """Allow multiple format string -- depending on the log level.

    A "fmtFromLevel" optional arg is added to the constructor. It can be
    a dictionary mapping a log record level to a format string. The
    usual "fmt" argument acts as the default.
    """
    def __init__(self, fmt=None, datefmt=None, fmtFromLevel=None):
        logging.Formatter.__init__(self, fmt, datefmt)
        if fmtFromLevel is None:
            self.fmtFromLevel = {}
        else:
            self.fmtFromLevel = fmtFromLevel
    def format(self, record):
        record.lowerlevelname = record.levelname.lower()
        if record.levelno in self.fmtFromLevel:
            #XXX This is a non-threadsafe HACK. Really the base Formatter
            #    class should provide a hook accessor for the _fmt
            #    attribute. *Could* add a lock guard here (overkill?).
            _saved_fmt = self._fmt
            self._fmt = self.fmtFromLevel[record.levelno]
            try:
                return logging.Formatter.format(self, record)
            finally:
                self._fmt = _saved_fmt
        else:
            return logging.Formatter.format(self, record)

def _setup_logging(stream=None):
    """Do logging setup:

    We want a prettier default format:
         do: level: ...
    Spacing. Lower case. Skip " level:" if INFO-level. 
    """
    hdlr = logging.StreamHandler(stream)
    defaultFmt = "%(name)s: %(levelname)s: %(message)s"
    infoFmt = "%(name)s: %(message)s"
    fmtr = _PerLevelFormatter(fmt=defaultFmt,
                              fmtFromLevel={logging.INFO: infoFmt})
    hdlr.setFormatter(fmtr)
    logging.root.addHandler(hdlr)
    log.setLevel(logging.INFO)


#---- mainline

def main(argv):
    usage = "usage: %prog PATHS..."
    version = "%prog "+__version__
    parser = optparse.OptionParser(usage=usage,
        version=version, description=_cmdln_doc,
        formatter=_NoReflowFormatter())
    parser.add_option("-v", "--verbose", dest="log_level",
                      action="store_const", const=logging.DEBUG,
                      help="more verbose output")
    parser.add_option("-q", "--quiet", dest="log_level",
                      action="store_const", const=logging.WARNING,
                      help="quieter output")
    parser.add_option("-r", "--recursive", action="store_true",
                      help="recursively descend into given paths")
    parser.add_option("-L", "--dereference", dest="follow_symlinks",
                      action="store_true",
                      help="follow symlinks, i.e. show info about linked-to "
                           "files and descend into linked dirs when recursive")
    parser.add_option("-Q", "--quick-determine-lang", action="store_true",
                      help="Skip some processing to attempt to determine "
                           "language. Things like specialization, emacs/vi "
                           "local vars, full decoding, are skipped.")
    parser.add_option("--encoding", help="suggested encoding for input files")
    parser.add_option("-f", "--format",
                      help="format of output: summary (default), dict")
    parser.add_option("-x", "--exclude", dest="excludes", action="append",
        metavar="PATTERN",
        help="path pattern to exclude for recursive search (by default SCC "
             "control dirs are skipped)")
    parser.set_defaults(log_level=logging.INFO, encoding=None, recursive=False,
                        follow_symlinks=False, format="summary",
                        excludes=[".svn", "CVS", ".hg", ".git", ".bzr"],
                        quick_determine_lang=False)
    opts, args = parser.parse_args()
    log.setLevel(opts.log_level)
    if opts.log_level > logging.INFO:
        warnings.simplefilter("ignore", ChardetImportWarning)

    if args:
        path_patterns = args
    elif sys.stdin.isatty():
        parser.print_help()
        return 0
    else:
        def args_from_stdin():
            for line in sys.stdin:
                yield line.rstrip("\r\n")
        path_patterns = args_from_stdin()

    for path in _paths_from_path_patterns(path_patterns, excludes=opts.excludes,
                    recursive=opts.recursive, 
                    dirs="if-not-recursive",
                    follow_symlinks=opts.follow_symlinks):
        try:
            ti = textinfo_from_path(path, encoding=opts.encoding,
                                    follow_symlinks=opts.follow_symlinks,
                                    quick_determine_lang=opts.quick_determine_lang)
        except OSError, ex:
            log.error("%s: %s", path, ex)
            continue
        if opts.format == "summary":
            print ti.as_summary()
        elif opts.format == "dict":
            d = ti.as_dict()
            if "text" in d:
                del d["text"]
            pprint(d)
        else:
            raise TextInfoError("unknown output format: %r" % opts.format)


if __name__ == "__main__":
    _setup_logging()
    try:
        if "--self-test" in sys.argv:
            import doctest
            retval = doctest.testmod()[0]
        else:
            retval = main(sys.argv)
    except SystemExit:
        pass
    except KeyboardInterrupt:
        sys.exit(1)
    except:
        exc_info = sys.exc_info()
        if log.isEnabledFor(logging.DEBUG):
            import traceback
            print
            traceback.print_exception(*exc_info)
        else:
            if hasattr(exc_info[0], "__name__"):
                #log.error("%s: %s", exc_info[0].__name__, exc_info[1])
                log.error(exc_info[1])
            else:  # string exception
                log.error(exc_info[0])
        sys.exit(1)
    else:
        sys.exit(retval)
