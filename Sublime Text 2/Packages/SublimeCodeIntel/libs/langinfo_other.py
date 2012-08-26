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

"""LangInfo definitions for languages that don't fit in the other
langinfo_*.py files.
"""

import re
from langinfo import LangInfo



class MakefileLangInfo(LangInfo):
    name = "Makefile"
    conforms_to_bases = ["Text"]
    exts = [".mak"]
    filename_patterns = [re.compile(r'^[Mm]akefile.*$')]

class _CSSLangInfoCommon(LangInfo):
    conforms_to_bases = ["Text"]
    exts = [".css"]
    default_encoding = "utf-8"
    # http://www.w3.org/International/questions/qa-css-charset
    # http://www.w3.org/TR/CSS21/syndata.html#charset
    # http://www.w3.org/TR/CSS2/syndata.html#q23            
    # I.e., look for:
    #   @charset "<IANA defined charset name>";
    # at the start of the CSS document.
    encoding_decl_pattern = re.compile(r'\A@charset "(?P<encoding>[\w-]+)";')

class CSSLangInfo(_CSSLangInfoCommon):
    name = "CSS"
    exts = [".css"]

class SCSSLangInfo(_CSSLangInfoCommon):
    name = "SCSS"
    exts = [".scss"]

class LessLangInfo(_CSSLangInfoCommon):
    name = "Less"
    exts = [".less"]


class CIXLangInfo(LangInfo):
    """Komodo Code Intelligence XML dialect.

    This is used to define the code structure of scanned programming
    language content.
    """
    name = "CIX"
    conforms_to_bases = ["XML"]
    exts = [".cix"]

class DiffLangInfo(LangInfo):
    name = "Diff"
    conforms_to_bases = ["Text"]
    exts = [".patch", ".diff"]
    has_significant_trailing_ws = True

class IDLLangInfo(LangInfo):
    #TODO: clarify if this is the math thing or the COM-IDL thing
    name = "IDL"
    conforms_to_bases = ["Text"]
    exts = [".idl"]

class ApacheConfigLangInfo(LangInfo):
    name = "Apache Config"
    komodo_name = "Apache"
    conforms_to_bases = ["Text"]
    exts = [".conf"]
    filename_patterns = [".htaccess"]

class APDLLangInfo(LangInfo):
    """ANSYS Parametric Design Language

    http://www.mece.ualberta.ca/tutorials/ansys/AT/APDL/APDL.html
    """
    name = "APDL"
    conforms_to_bases = ["Text"]
    exts = [".mac"]

class POVRayLangInfo(LangInfo):
    """The "Persistence of Vision Raytracer"
    http://www.povray.org
    """
    name = "POVRay"
    conforms_to_bases = ["Text"]
    exts = [".pov"]

class MatlabLangInfo(LangInfo):
    """A high-performance language for technical computing.
    http://www.mathworks.com/
    """
    name = "Matlab"
    conforms_to_bases = ["Text"]
    exts = [".m", ".mat"]

class ForthLangInfo(LangInfo):
    """Forth is a structured, imperative, stack-based, computer programming
    language.
    http://en.wikipedia.org/wiki/Forth_(programming_language)
    http://www.forth.org/
    """
    name = "Forth"
    conforms_to_bases = ["Text"]
    exts = [".forth"]


class FlagshipLangInfo(LangInfo):
    """ Flagship is a commercial compiler for Clipper (dBASE III compiler)
    http://www.fship.com/
    http://en.wikipedia.org/wiki/Clipper_(programming_language)
    """
    name = "Flagship"
    conforms_to_bases = ["Text"]
    exts = [".prg"]

class SQLLangInfo(LangInfo):
    #TODO: describe: what SQL spec does this conform to?
    #TODO: should we have other SQL langs? E.g. for PostgreSQL, etc.?
    name = "SQL"
    conforms_to_bases = ["Text"]
    exts = [".sql"]

class PLSQLLangInfo(LangInfo):
    #TODO: describe how different from SQLLangInfo
    name = "PL-SQL"
    conforms_to_bases = ["Text"]
    #exts = [".sql"]
    is_minor_variant = SQLLangInfo

class MSSQLLangInfo(LangInfo):
    #TODO: describe how diff from SQLLangInfo
    name = "MSSQL"
    conforms_to_bases = ["Text"]

class MySQLLangInfo(LangInfo):
    name = "MySQL"
    conforms_to_bases = ["Text"]
    exts = [".sql"]
    is_minor_variant = SQLLangInfo


class NSISLangInfo(LangInfo):
    """Nullsoft Scriptable Install System
    http://nsis.sourceforge.net/
    """
    name = "NSIS"
    komodo_name = "Nsis"
    conforms_to_bases = ["Text"]
    exts = [".nsi"]


class VimLangInfo(LangInfo):
    """Vim configuration"""
    name = "Vim"
    conforms_to_bases = ["Text"]
    exts = [".vim"]
    filename_patterns = [".vimrc"]

class INILangInfo(LangInfo):
    name = "INI"
    conforms_to_bases = ["Text"]
    exts = [".ini"]

class LogLangInfo(LangInfo):
    name = "log"
    conforms_to_bases = ["Text"]
    exts = [".log"]

class CobolLangInfo(LangInfo):
    name = "COBOL"
    conforms_to_bases = ["Text"]
    exts = [".cbl"]

class NimrodLangInfo(LangInfo):
    name = "Nimrod"
    conforms_to_bases = ["Text"]
    exts = [".nim"]

class PowerProLangInfo(LangInfo):
    name = "PowerPro"
    conforms_to_bases = ["Text"]

class SMLLangInfo(LangInfo):
    name = "SML"
    conforms_to_bases = ["Text"]
    exts = [".sml"]

class SorcusLangInfo(LangInfo):
    name = "Sorcus"
    conforms_to_bases = ["Text"]

class TACLLangInfo(LangInfo):
    name = "TACL"
    conforms_to_bases = ["Text"]
    exts = [".tacl"]

class TALLangInfo(LangInfo):
    name = "TAL"
    conforms_to_bases = ["Text"]
    exts = [".tal"]
