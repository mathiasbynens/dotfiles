# 
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
#
# Contributors:
#   Eric Promislow (EricP@ActiveState.com)
#
# This code has intimate knowledge of the code objects defined in
# parser_data.py
# 

import os
from os.path import basename, splitext, isfile, isdir, join

from ciElementTree import Element, SubElement, tostring
from codeintel2 import util



def get_common_attrs(node):
    attrs = {}
    attrs = {"name": node.name}
    try:
        attrs["line"] = str(node.line_num);
    except AttributeError:
        pass
    try:
        attrs["lineend"] = str(node.lineend);
    except AttributeError:
        pass
    try:
        if node.is_classmethod:
            attrs["attributes"] = "__classmethod__"
        elif node.is_constructor:
            attrs["attributes"] = "__ctor__"
        else:
            attrs["attributes"] = node.attributes;
    except AttributeError:
        pass
        
    return attrs

def sort_by_lines(adict):
    intermed = [(adict[k].line_num, adict[k].type, k) for k in adict.keys()]
    intermed.sort()
    return intermed


#### ElementTree-based CIX routines

def get_arguments_cix(parse_tree_node, cix_node):
    for c in parse_tree_node.args:
        attrs = get_common_attrs(c)
        attrs['name'] = c.get_full_name()
        if not c.arg_attrs is None:
            attrs['attributes'] = c.arg_attrs
        SubElement(cix_node, 'variable', ilk='argument', **attrs)

def get_docstring_cix(parse_tree_node, cix_node):
    if len(parse_tree_node.doc_lines) >= 1:
        summarylines = util.parseDocSummary(parse_tree_node.doc_lines)
        if len(summarylines) > 0:
            cix_node.set("doc", "\n".join(summarylines))

def get_imports_cix(parse_tree_node, cix_node):
    for imp in getattr(parse_tree_node, "imports", []):
        SubElement(cix_node, "import", module=imp.name, line=str(imp.line_num), symbol="*")

# These bring all the names in a namespace into the calling namespace.
def get_includes_cix(parse_tree_node, cix_node):
    for incl in getattr(parse_tree_node, "includes", []):
        SubElement(cix_node, "import", symbol=incl.name, line=str(incl.line_num))

def get_signature_cix(parse_tree_node, cix_node):
    signature = getattr(parse_tree_node, 'signature', '')
    if len(signature) > 0:
        cix_node.set('signature', signature)
        

def get_var_cix(cix_node, var_type, **attrs):
    var_cix_node = SubElement(cix_node, 'variable', **attrs)
    if var_type:
        var_cix_node.set('citdl', var_type)

def _local_varname_test(var_name):
    return var_name[0].islower() or var_name[0] == "_"

def _local_varname_test_true(true):
    return True

def _get_vars_helper(parse_tree_node, cix_node, kind_name, attr_attrs=None,
                    var_test=_local_varname_test_true):
    for line_no, var_type, var_name in sort_by_lines(getattr(parse_tree_node,
                                                             kind_name, {})):
        attrs = {"name": var_name, "line":str(line_no)}
        if attr_attrs:
            if var_test(var_name):
                attrs["attributes"] = attr_attrs
        get_var_cix(cix_node, var_type, **attrs)

def get_globals_cix(parse_tree_node, cix_node):
    _get_vars_helper(parse_tree_node, cix_node, 'global_vars')

def get_vars_cix(parse_tree_node, cix_node):
    _get_vars_helper(parse_tree_node, cix_node, 'local_vars', "__local__",
                    _local_varname_test)
    _get_vars_helper(parse_tree_node, cix_node, 'aliases',
                    "__alias__")
    _get_vars_helper(parse_tree_node, cix_node, 'class_vars', "__local__")
    _get_vars_helper(parse_tree_node, cix_node, 'instance_vars',
                    "__instancevar__ __local__")

def common_module_class_cix(parse_tree_node, cix_node, class_ref_fn=None, **additional_attrs):
    attrs = get_common_attrs(parse_tree_node)
    attrs.update(additional_attrs)
    if not attrs.has_key('ilk'):
        attrs['ilk'] = 'class'
    class_cix_node = SubElement(cix_node, 'scope', **attrs)
    get_docstring_cix(parse_tree_node, class_cix_node)
    get_signature_cix(parse_tree_node, class_cix_node)
    get_imports_cix(parse_tree_node, class_cix_node)
    get_includes_cix(parse_tree_node, class_cix_node)
    get_vars_cix(parse_tree_node, class_cix_node)
    if class_ref_fn:
        class_ref_fn(parse_tree_node, class_cix_node)
    visit_children_get_cix(parse_tree_node, class_cix_node)

def classref_etree_cix(parse_tree_node, cix_node):
    classrefs = [(len(ref) > 2 and ref[2] or ref[0])
                 for ref in parse_tree_node.classrefs]
    if len(classrefs) > 0:
        cix_node.set('classrefs', " ".join(classrefs))
def class_etree_cix(parse_tree_node, cix_node):
    common_module_class_cix(parse_tree_node, cix_node, classref_etree_cix)

def method_etree_cix(parse_tree_node, cix_node):
    attrs = get_common_attrs(parse_tree_node)
    method_cix_node = SubElement(cix_node, 'scope', ilk='function', **attrs)
    get_docstring_cix(parse_tree_node, method_cix_node)
    get_signature_cix(parse_tree_node, method_cix_node)
    #XXX: Get classrefs, doc, symbols(?)
    get_arguments_cix(parse_tree_node, method_cix_node)
    get_imports_cix(parse_tree_node, method_cix_node)
    get_includes_cix(parse_tree_node, method_cix_node)
    get_vars_cix(parse_tree_node, method_cix_node)
    visit_children_get_cix(parse_tree_node, method_cix_node)

def module_etree_cix(parse_tree_node, cix_node):
    common_module_class_cix(parse_tree_node, cix_node, ilk='namespace')

cb_etree_hash = {"Module" : module_etree_cix,
                 "Class" : class_etree_cix,
                 "Method" : method_etree_cix}

def visit_children_get_cix(parse_tree_node, cix_node):
    for c in parse_tree_node.children:
        cb_etree_hash[c.class_name](c, cix_node)

def produce_elementTree_cix(parse_tree, filename, target_lang, gen_lang="Python"):
    cix_root = Element("codeintel", version="2.0")
    fileAttrs = {"lang": target_lang,
                 "path": filename,
                 }
    file_cix_node = SubElement(cix_root, "file", **fileAttrs)
    module_cix_node = SubElement(file_cix_node, "scope", ilk='blob',
                                 lang=gen_lang,
                                 name=splitext(basename(filename))[0])
    produce_elementTree_contents_cix(parse_tree, module_cix_node)
    return cix_root

def produce_elementTree_contents_cix(parse_tree, cix_node):
    get_docstring_cix(parse_tree, cix_node)
    get_imports_cix(parse_tree, cix_node)
    get_includes_cix(parse_tree, cix_node)
    get_globals_cix(parse_tree, cix_node)
    get_vars_cix(parse_tree, cix_node)
    visit_children_get_cix(parse_tree, cix_node)
    return cix_node
