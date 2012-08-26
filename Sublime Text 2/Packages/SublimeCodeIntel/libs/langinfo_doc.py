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

"""LangInfo definitions for some document languages."""

import re
from langinfo import LangInfo



class HTMLLangInfo(LangInfo):
    name = "HTML"
    conforms_to_bases = ["Text"]
    exts = ['.html', '.htm']
    magic_numbers = [
        (0, "string", "<!DOCTYPE html "),
        (0, "string", "<html"),
    ]
    # The default encoding is iso-8859-1 or utf-8 depending on the
    # Content-Type (provided by an HTTP header or defined in a <meta>
    # tag). See here for a good summary:
    #   http://feedparser.org/docs/character-encoding.html#advanced.encoding.intro
    # We'll just use UTF-8. Safer. It is the future.
    default_encoding = "utf-8"
    doctypes = [
        # <flavour>, <common-name>, <public-id>, <system-id>
        ("HTML 4.01 Strict", "HTML",
         "-//W3C//DTD HTML 4.01//EN",
         "http://www.w3.org/TR/html4/strict.dtd"),
        ("HTML 4.01 Transitional", "HTML",
         "-//W3C//DTD HTML 4.01 Transitional//EN",
         "http://www.w3.org/TR/html4/loose.dtd"),
        ("HTML 4.01 Frameset", "HTML",
         "-//W3C//DTD HTML 4.01 Frameset//EN",
         "http://www.w3.org/TR/html4/frameset.dtd"),
        ("HTML 3.2", "HTML",
         "-//W3C//DTD HTML 3.2 Final//EN", None),
        ("HTML 2.0", "HTML",
         "-//IETF//DTD HTML//EN", None),
    ]

class HTML5LangInfo(HTMLLangInfo):
    name = "HTML5"
    magic_numbers = [
        (0, "string", "<!DOCTYPE html>"),
    ]
    _magic_number_precedence = ('HTML', -1)
    doctypes = [
        # <flavour>, <common-name>, <public-id>, <system-id>
        ("HTML 5", "HTML5",
         "-//W3C//DTD HTML 5//EN",
         "http://www.w3.org/TR/html5/html5.dtd"),
    ]
    

class XHTMLLLangInfo(LangInfo):
    name = "XHTML"
    conforms_to_bases = ["XML", "HTML"]
    exts = ['.xhtml']
    doctypes = [
        # <flavour>, <common-name>, <public-id>, <system-id>
        ("XHTML 1.0 Strict", "html",
         "-//W3C//DTD XHTML 1.0 Strict//EN",
         "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"),
        ("XHTML 1.0 Transitional", "html",
         "-//W3C//DTD XHTML 1.0 Transitional//EN",
         "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"),
        ("XHTML 1.0 Frameset", "html",
         "-//W3C//DTD XHTML 1.0 Frameset//EN",
         "http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd"),
    ]


class XMLLangInfo(LangInfo):
    name = "XML"
    conforms_to_bases = ["Text"]
    exts = ['.xml']
    default_encoding = "utf-8"
    magic_numbers = [
        (0, "string", "<?xml"),
    ]

class XSLTLangInfo(LangInfo):
    name = "XSLT"
    conforms_to_bases = ["XML"]
    exts = ['.xsl', '.xslt']
    #PERF: Only want to include this if necessary (for perf), i.e. if
    #      `exts` isn't sufficient.
    #magic_numbers = [
    #    (0, "regex", re.compile(r'^<xsl:stylesheet ', re.M))
    #]

class XULLangInfo(LangInfo):
    name = "XUL"
    conforms_to_bases = ["XML"]
    exts = ['.xul']
    doctypes = [
        # <flavour>, <common-name>, <public-id>, <system-id>
        (None, "window", "-//MOZILLA//DTD XUL V1.0//EN",
         "http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul"),
    ]

class XBLLangInfo(LangInfo):
    """eXtensible Binding Language"""
    name = "XBL"
    conforms_to_bases = ["XML"]
    exts = ['.xbl']
    # doctype:
    #   <!DOCTYPE bindings PUBLIC "-//MOZILLA//DTD XBL V1.0//EN" "http://www.mozilla.org/xbl">
    doctypes = [
        # <flavour>, <common-name>, <public-id>, <system-id>
        (None, "bindings", "-//MOZILLA//DTD XBL V1.0//EN",
         "http://www.mozilla.org/xbl"),
    ]


class SGMLLangInfo(LangInfo):
    name = "SGML"
    conforms_to_bases = ["Text"]
    exts = ['.sgml', '.ent']
    magic_numbers = [
        (0, "string", "<!subdoc"), #TODO: should be case-insensitive
        #TODO: How to get these to have lower precedence than HTML
        #      doctype
        #(0, "string", "<!doctype"), #TODO: should be case-insensitive
        #(0, "string", "<!--"),
    ]

class YAMLLangInfo(LangInfo):
    name = "YAML"
    conforms_to_bases = ["Text"]
    exts = ['.yaml', '.yml']
    has_significant_trailing_ws = True
    #TODO: default encoding?

class JSONLangInfo(LangInfo):
    name = "JSON"
    conforms_to_bases = ["JavaScript"]
    exts = [".json"]

    section_regexes = [
        ("namespace", re.compile(r'"(?P<name>[^"]*?)"\s*:\s*{', re.M)),
    ]

class DTDLangInfo(LangInfo):
    name = "DTD"
    conforms_to_bases = ["Text"]
    exts = [".dtd"]

class PODLangInfo(LangInfo):
    """Plain Old Documentation format common in the Perl world."""
    name = "POD"
    conforms_to_bases = ["Text"]
    exts = [".pod"]
    # http://search.cpan.org/~nwclark/perl-5.8.8/pod/perlpod.pod
    encoding_decl_pattern = re.compile(r"^=encoding\s+(?P<encoding>[-\w.]+)", re.M)

class ASN1LangInfo(LangInfo):
    name = "ASN.1"
    komodo_name = "ASN1"
    conforms_to_bases = ["Text"]
    exts = [".asn1"]

class PostScriptLangInfo(LangInfo):
    name = "PostScript"
    conforms_to_bases = ["Text"]
    exts = [".ps"]


class TeXLangInfo(LangInfo):
    name = "TeX"
    conforms_to_bases = ["Text"]
    #TODO: who should win .tex? TeX or LaTeX?
    #exts = [".tex"]

class LaTeXLangInfo(LangInfo):
    name = "LaTeX"
    conforms_to_bases = ["Text"]
    exts = [".tex"]

class ConTeXLangInfo(LangInfo):
    name = "ConTeX"
    conforms_to_bases = ["Text"]

class GettextPOLangInfo(LangInfo):
    """GNU Gettext PO

    http://www.gnu.org/software/gettext/manual/gettext.html#PO-Files
    """
    name = "PO"
    conforms_to_bases = ["Text"]
    exts = [".po"]
    default_encoding = "utf-8"

class TracWikiLangInfo(LangInfo):
    name = "TracWiki"
    conforms_to_bases = ["Text"]
    exts = [".tracwiki"]
    # Headers consist of the same # of equal signs at the start and end of the line.
    # An optional id is allowed after the closing = (to indicate an id attr)
    # A "!" in the header escapes *all* the immediately following = chars.
    section_regexes = [
        ("header",
         re.compile(r'''
            ^
            \s*
            (={1,5})
            \s*
            (?P<name>(?:!=+|
                        [^=!]+|
                        !)+?
            )
            \s*
            \1
            (?:\s|\#|$)
         ''', re.M|re.X)),
    ]

class ReStructureTextLangInfo(LangInfo):
    name = "reStructuredText"
    conforms_to_bases = ["Text"]
    exts = [".rst"]

class MarkdownLangInfo(LangInfo):
    """'A text-to-HTML conversion tool [and format] for web writers'

    http://daringfireball.net/projects/markdown/
    """
    name = "Markdown"
    conforms_to_bases = ["Text"]
    exts = [
        # from other editors and what Github's markup processing supports
        ".md", ".markdown", ".mdown", ".mkdn", ".mkd",
        # from <http://www.file-extensions.org/mdml-file-extension>
        ".mdml",
    ]

class RichTextFormatLangInfo(LangInfo):
    """Rich Text Format"""
    name = "RTF"
    conforms_to_bases = ["Text"]
    exts = [".rtf"]
    magic_numbers = [
        (0, "string", r"{\rtf"),
    ]


class TroffLangInfo(LangInfo):
    """'the Text Processor for Typesetters'

    This is the format of man pages on Un*x.
    http://www.troff.org/
    """
    name = "troff"
    conforms_to_bases = ["Text"]
    magic_numbers = [
        (0, "string", '.\\"'),
        (0, "string", "'\\\""),
        (0, "string", "'.\\\""),
        (0, "string", "\\\""),
        (0, "string", "'''"),
    ]
    has_significant_trailing_ws = True

