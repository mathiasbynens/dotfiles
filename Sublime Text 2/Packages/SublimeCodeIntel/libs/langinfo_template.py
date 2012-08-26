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

"""LangInfo definitions for template languages."""

import re
from langinfo import LangInfo


class RHTMLLangInfo(LangInfo):
    name = "RHTML"
    conforms_to_bases = ["Text"]
    exts = [".rhtml"]


class EJSLangInfo(LangInfo):
    name = "EJS"
    conforms_to_bases = ["Text"]
    exts = [".ejs"]


class DjangoTemplateLangInfo(LangInfo):
    name = "Django Template"
    conforms_to_bases = ["Text"]
    section_regexes = [
        ("import", re.compile(r'\{\%[ \t]+(load\b.*?)\%\}')),
        ("class", re.compile(r'\{\%[ \t]+(block\b.*?)\%\}')),
    ]

class DjangoHTMLTemplateLangInfo(DjangoTemplateLangInfo):
    name = "Django HTML Template"
    komodo_name = "Django"
    specialization_hints_from_lang = {
        "HTML": [
            ('{%', re.compile(r'\{\%[ \t]+\b(block|if)\b.*?\%\}')),
            ('{{', re.compile(r'\{\{.*?\}\}')),
        ],
    }

class DjangoXHTMLTemplateLangInfo(DjangoTemplateLangInfo):
    name = "Django XHTML Template"
    specialization_hints_from_lang = {
        "XHTML": [
            ('{%', re.compile(r'\{\%[ \t]+\b(block|if)\b.*?\%\}')),
            ('{{', re.compile(r'\{\{.*?\}\}')),
        ],
    }

class DjangoTextTemplateLangInfo(DjangoTemplateLangInfo):
    name = "Django Text Template"
    specialization_hints_from_lang = {
        "Text": [
            ('{%', re.compile(r'\{\%[ \t]+\b(block|if)\b.*?\%\}')),
            ('{{', re.compile(r'\{\{.*?\}\}')),
        ],
    }

class DjangoXMLTemplateLangInfo(DjangoTemplateLangInfo):
    name = "Django XML Template"
    specialization_hints_from_lang = {
        "XML": [
            ('{%', re.compile(r'\{\%[ \t]+\b(block|if)\b.*?\%\}')),
            ('{{', re.compile(r'\{\{.*?\}\}')),
        ],
    }


class EpMojoHTMLTemplateLangInfo(LangInfo):
    #TODO: How to best handle relationship with HTML?
    #TODO: How to enable detection?
    name = "ep (Mojo) HTML Template"
    komodo_name = "EpMojo"
    conforms_to_bases = ["Text"]
    # This ext is a Komodo-ism, but helpful for getting codeintel tests
    # working for Template Toolkit.
    exts = [".ep"]


class MasonHTMLTemplateLangInfo(LangInfo):
    #TODO: How to best handle relationship with HTML?
    #TODO: How to enable detection?
    name = "Mason HTML Template"
    komodo_name = "Mason"
    conforms_to_bases = ["Text"]
    # This ext is a Komodo-ism, but helpful for getting codeintel tests
    # working for Template Toolkit.
    exts = [".mason.html"]


class TemplateToolkitLangInfo(LangInfo):
    #TODO: link to lang page
    #TODO: Is template toolkit just for HTML files?
    name = "Template Toolkit HTML Template"  # a little long
    komodo_name = "TemplateToolkit"
    conforms_to_bases = ["Text"]
    # This ext is a Komodo-ism, but helpful for getting codeintel tests
    # working for Template Toolkit.
    exts = [".ttkt.html"]


class SmartyLangInfo(LangInfo):
    """http://www.smarty.net/"""
    name = "Smarty Template"
    komodo_name = "Smarty"
    conforms_to_bases = ["Text"]
    exts = [".tpl"]


class CakePHPTemplate(LangInfo):
    """CakePHP view template files.
    
    CakePHP is a PHP framework with an MVC system. By convention "view"
    files (they are PHP) use the .ctp extension.
    http://book.cakephp.org/view/22/cakephp-conventions#view-conventions-26
    """
    name = "CakePHP Template"
    conforms_to_bases = ["PHP"]
    exts = [".ctp"]

