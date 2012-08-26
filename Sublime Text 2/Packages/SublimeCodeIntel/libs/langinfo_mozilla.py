# Copyright (c) 2009 ActiveState Software Inc.
# See the file LICENSE.txt for licensing information.

"""LangInfo definitions for languages coming out of the Mozilla project and
that don't logically fit in the other `langinfo_*.py` files.
"""

import re
from langinfo import LangInfo



class StringPropertiesLangInfo(LangInfo):
    """A properties file commonly used in the Mozilla project with
    `nsIStringBundleService`.
    
    Note: The Java world also uses ".properties".
        http://java.sun.com/docs/books/tutorial/i18n/resbundle/propfile.html
    This looks to be the same format. I'm guessing that Mozilla's use
    of the extension for string bundles is derived from this.
    """
    name = "String Properties"
    conforms_to_bases = ["Text"]
    exts = [".properties"]

class ChromeManifestLangInfo(LangInfo):
    """A Mozilla chrome manifest file."""
    name = "Chrome Manifest"
    conforms_to_bases = ["Text"]
    # Can't claim ".manifest" extension, because ".manifest" XML files are
    # common on Windows for UAC.
    filename_patterns = [
        "chrome.manifest",
        # These for Komodo's benefit:
        "chrome.p.manifest",    # Suggested usage by 'koext' tool.
        "devbuild.manifest",    # Komodo: in common usage
    ]
 

class XPTLangInfo(LangInfo):
    """Mozilla XPCOM Type info file.
    
    XPT files are the result of compiling .idl files with "xpidl".
    http://www.mozilla.org/scriptable/typelib_tools.html
    """
    name = "XPT"
    exts = [".xpt"]
