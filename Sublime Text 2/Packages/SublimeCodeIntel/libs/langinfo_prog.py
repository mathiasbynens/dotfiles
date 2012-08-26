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

"""LangInfo definitions for some programming languages."""

import re
from langinfo import LangInfo


class _PythonCommonLangInfo(LangInfo):
    conforms_to_bases = ["Text"]
    exts = ['.py', '.pyw']
    default_encoding = "ascii"  #TODO: link to ref defining default encoding
    # http://www.python.org/dev/peps/pep-0263/
    encoding_decl_pattern = re.compile(r"coding[:=]\s*(?P<encoding>[-\w.]+)")

# Where there's a conflict in extensions, put the main
# LangInfo entry last.
class PythonLangInfo(_PythonCommonLangInfo):
    name = "Python"
    magic_numbers = [
        (0, "regex", re.compile(r'\A#!.*python(?!3).*$', re.I | re.M))
    ]

class Python3LangInfo(_PythonCommonLangInfo):
    name = "Python3"
    magic_numbers = [
        (0, "regex", re.compile(r'\A#!.*python3.*$', re.I | re.M))
    ]
    is_minor_variant = PythonLangInfo

class CompiledPythonLangInfo(LangInfo):
    name = "Compiled Python"
    exts = ['.pyc', '.pyo']

class PerlLangInfo(LangInfo):
    name = "Perl"
    conforms_to_bases = ["Text"]
    exts = ['.pl', '.pm', '.t']
    magic_numbers = [
        (0, "regex", re.compile(r'\A#!.*perl.*$', re.I | re.M)),
    ]
    filename_patterns = ["Construct", "Conscript"] # Cons make-replacement tool files

    # http://search.cpan.org/~rgarcia/encoding-source-0.02/lib/encoding/source.pm
    default_encoding = "iso8859-1"
    # Perl >= 5.8.0
    #   http://perldoc.perl.org/encoding.html
    #   use encoding "<encoding-name>";
    #   "Somewhat broken."
    # Perl >= 5.9.5
    #   http://search.cpan.org/~rgarcia/encoding-source-0.02/lib/encoding/source.pm
    #   use encoding::source "<encoding-name>";
    #   "This is like the encoding pragma, but done right."
    encoding_decl_pattern = re.compile(
        r"""use\s+encoding(?:::source)?\s+(['"])(?P<encoding>[\w-]+)\1""")


class PHPLangInfo(LangInfo):
    name = "PHP"
    conforms_to_bases = ["Text"]
    exts = [".php", ".inc",
            ".phtml"]  # .phtml commonly used for Zend Framework view files
    magic_numbers = [
        (0, "string", "<?php"),
        (0, "regex", re.compile(r'\A#!.*php.*$', re.I | re.M)),
    ]
    #TODO: PHP files should inherit the HTML "<meta> charset" check
    #      and the XML prolog encoding check.

    keywords = set([
            # existed in php4
            "bool", "boolean", "catch", "define", "double", "false", "float",
            "int", "integer", "null", "object", "parent", "real",
            "self", "string", "this", "true", "virtual",
            # new to php5
            "abstract", "final", "implements", "instanceof", "interface",
            "public", "private", "protected", "throw", "try",
            # http://www.php.net/manual/en/reserved.php#reserved.keywords
            "__file__", "__line__", "_function_", "_class_",
            "and", "array", "as", "break", "case", "cfunction", "class",
            "const", "continue", "declare", "default", "die", "do", "echo",
            "else", "elseif", "empty", "enddeclare", "endfor", "endforeach",
            "endif", "endswitch", "endwhile", "eval", "exit", "extends",
            "for", "foreach", "function", "global", "if", "include",
            "include_once", "isset", "list", "new", "old_function", "or",
            "print", "require", "require_once", "return", "static",
            "switch", "unset", "use", "var", "while", "xor",
            # new to php 5.3
            "__dir__", "__namespace__", "goto", "namespace",
            ])

class TclLangInfo(LangInfo):
    name = "Tcl"
    conforms_to_bases = ["Text"]
    exts = ['.tcl']
    magic_numbers = [
        (0, "regex", re.compile(r'\A#!.*(tclsh|wish|expect).*$', re.I | re.M)),
        # As suggested here: http://www.tcl.tk/man/tcl8.4/UserCmd/tclsh.htm
        # Make sure we properly catch shebang lines like this:
        #   #!/bin/sh
        #   # the next line restarts using tclsh \
        #   exec tclsh "$0" "$@"
        (0, "regex", re.compile(r'\A#!.*^exec [^\r\n|\n|\r]*?(tclsh|wish|expect)',
                                re.I | re.M | re.S)),
    ]
    _magic_number_precedence = ("Bourne shell", -1) # check before "Bourne shell"

class RubyLangInfo(LangInfo):
    name = "Ruby"
    conforms_to_bases = ["Text"]
    exts = ['.rb']
    filename_patterns = ["Rakefile"]
    magic_numbers = [
        (0, "regex", re.compile('\A#!.*ruby.*$', re.I | re.M)),
    ]
    #TODO: http://blade.nagaokaut.ac.jp/cgi-bin/scat.rb/ruby/ruby-core/12900
    #      Ruby uses similar (same?) coding decl as Python.

class _JSLikeLangInfo(LangInfo):
    conforms_to_bases = ["Text"]
    # Support for Node (server side JavaScript).
    magic_numbers = [
        (0, "regex", re.compile(r'\A#!.*node.*$', re.I | re.M))
    ]

    # These are the keywords that are used in most JavaScript environments.
    common_keywords = set(["break",
                           "case", "catch", "const", "continue",
                           "debugger", "default", "delete", "do",
                           "else", "export",
                           "false", "finally", "for", "function",
                           "if", "import", "in", "instanceof",
                           "let",
                           "new", "null",
                           "return",
                           "switch",
                           "this", "throw", "true", "try", "typeof",
                           "undefined",
                           "var", "void",
                           "while", "with",
                           "yield",
                          ])
    keywords = common_keywords.union(
                # Additional JavaScript reserved keywords.
                set(["abstract", "boolean", "byte",
                    "char", "class",
                    "double",
                    "enum", "extends",
                    "float",
                    "goto",
                    "implements", "int", "interface",
                    "long",
                    "native",
                    "package", "private", "protected", "public",
                    "short", "static", "super", "synchronized",
                    "transient"
                    ]))

class JavaScriptLangInfo(_JSLikeLangInfo):
    name = "JavaScript"
    exts = ['.js', '.jsm']

class NodeJSLangInfo(_JSLikeLangInfo):
    name = "Node.js"
    exts = ['.js']

class CoffeeScriptLangInfo(_JSLikeLangInfo):
    name = "CoffeeScript"
    exts = ['.coffee']
    def __init__(self, _database):
        _JSLikeLangInfo.__init__(self, _database)
        # Clone and modify the JS keywords
        self.common_keywords = set().union(self.common_keywords)
        try:
            self.common_keywords.remove("var")
        except KeyError:
            pass

class CLangInfo(LangInfo):
    #TODO: rationalize with C++ and Komodo's usage
    name = "C"
    conforms_to_bases = ["Text"]
    exts = [
        ".c", 
        ".xs",  # Perl extension modules. *Are* they legal C?
    ]
    #TODO: Note for Jan:
    # .xs files are *NOT* legal C or C++ code.  However, they are
    # similar enough that I find it useful to edit them using c-mode or
    # c++-mode in Emacs.

class CPlusPlusLangInfo(LangInfo):
    #TODO: consider breaking out headers and have separate
    #      scintilla_lexer attr
    name = "C++"
    conforms_to_bases = ["Text"]
    exts = [
              ".c++", ".cpp", ".cxx",
        ".h", ".h++", ".hpp", ".hxx",
        ".xs",  # Perl extension modules. *Are* they legal C++?
    ]

class HLSLLangInfo(LangInfo):
    """High Level Shader Language is a proprietary shading language developed by
    Microsoft for use with the Microsoft Direct3D API.
    
    http://en.wikipedia.org/wiki/HLSL
    """
    name = "HLSL"
    conforms_to_bases = ["Text"]
    exts = ['.hlsl', '.cg', '.fx']

    # Keywords,etc. from http://www.emeditor.com/pub/hlsl.esy
    _intrinsic_function_names = """asm_fragment
        bool
        column_major
        compile
        compile_fragment
        const
        discard
        do
        double
        else
        extern
        false
        float
        for
        half
        if 
        in
        inline
        inout
        int
        matrix
        out
        pixelfragment
        return
        register
        row_major
        sampler
        sampler1D
        sampler2D
        sampler3D
        samplerCUBE
        sampler_state
        shared
        stateblock
        stateblock_state
        static
        string
        struct
        texture
        texture1D
        texture2D
        texture3D
        textureCUBE
        true
        typedef
        uniform
        vector
        vertexfragment
        void
        volatile
        while""".split()
    _keywords_case_insensitive = "asm decl pass technique".split()
    _keywords_case_sensitive = """asm_fragment
        bool
        column_major
        compile
        compile_fragment
        const
        discard
        do
        double
        else
        extern
        false
        float
        for
        half
        if 
        in
        inline
        inout
        int
        matrix
        out
        pixelfragment
        return
        register
        row_major
        sampler
        sampler1D
        sampler2D
        sampler3D
        samplerCUBE
        sampler_state
        shared
        stateblock
        stateblock_state
        static
        string
        struct
        texture
        texture1D
        texture2D
        texture3D
        textureCUBE
        true
        typedef
        uniform
        vector
        vertexfragment
        void
        volatile
        while
        """.split()
    _reserved_words = """auto
        break
        case
        catch
        char
        class
        const_cast
        continue
        default
        delete
        dynamic_cast
        enum
        explicit
        friend
        goto
        long
        mutable
        namespace
        new
        operator
        private
        protected
        public
        reinterpret_cast
        short
        signed
        sizeof
        static_cast
        switch
        template
        this
        throw
        try
        typename
        union
        unsigned
        using
        virtual""".split()

    keywords = set(_intrinsic_function_names
        + _keywords_case_insensitive
        + _keywords_case_sensitive
        + _reserved_words)

class ADALangInfo(LangInfo):
    name = "Ada"
    conforms_to_bases = ["Text"]
    exts = [".ada"]

class NTBatchLangInfo(LangInfo):
    name = "Batch"
    conforms_to_bases = ["Text"]
    exts = [".bat", ".cmd"]  #TODO ".com"?

class BashLangInfo(LangInfo):
    name = "Bash"
    conforms_to_bases = ["Text"]
    exts = [".sh"]
    filename_patterns = [".bash_profile", ".bashrc", ".bash_logout"]
    magic_numbers = [
        (0, "regex", re.compile(r'\A#!.*/\bbash\b$', re.I | re.M)),
    ]

class SHLangInfo(LangInfo):
    name = "Bourne shell"
    conforms_to_bases = ["Text"]
    magic_numbers = [
        (0, "regex", re.compile(r'\A#!.*/\bsh\b$', re.I | re.M)),
    ]
    

class TCSHLangInfo(LangInfo):
    name = "tcsh"
    conforms_to_bases = ["Text"]
    magic_numbers = [
        (0, "regex", re.compile(r'\A#!.*/\btcsh\b$', re.M)),
    ]
    filename_patterns = ["csh.cshrc", "csh.login", "csh.logout",
                         ".tcshrc", ".cshrc", ".login", ".logout"]

class CSharpLangInfo(LangInfo):
    name = "C#"
    conforms_to_bases = ["Text"]
    exts = [".cs"]

class ErlangLangInfo(LangInfo):
    name = "Erlang"
    conforms_to_bases = ["Text"]
    exts = [".erl"]

class Fortran77LangInfo(LangInfo):
    name = "Fortran 77"
    conforms_to_bases = ["Text"]
    exts = [".f"]

class Fortran95LangInfo(LangInfo):
    name = "Fortran"
    conforms_to_bases = ["Text"]
    exts = [".f95"]

class JavaLangInfo(LangInfo):
    name = "Java"
    conforms_to_bases = ["Text"]
    exts = [".java", ".jav"]

class LispLangInfo(LangInfo):
    name = "Lisp"
    conforms_to_bases = ["Text"]
    exts = [".lis"]

class LuaLangInfo(LangInfo):
    name = "Lua"
    conforms_to_bases = ["Text"]
    exts = [".lua"]

class PascalLangInfo(LangInfo):
    name = "Pascal"
    conforms_to_bases = ["Text"]
    exts = [".pas"]

class SmalltalkLangInfo(LangInfo):
    name = "Smalltalk"
    conforms_to_bases = ["Text"]
    exts = [".st"]

class ActionScriptLangInfo(LangInfo):
    """ActionScript source code

    http://en.wikipedia.org/wiki/Adobe_Flash#Related_file_formats_and_extensions
    """
    name = "ActionScript"
    conforms_to_bases = ["Text"]
    exts = [".as", ".asc"]

class AssemblerLangInfo(LangInfo):
    name = "Assembler"
    conforms_to_bases = ["Text"]
    exts = [".asm"]

class EiffelLangInfo(LangInfo):
    name = "Eiffel"
    conforms_to_bases = ["Text"]
    exts = [".e"]

class HaskellLangInfo(LangInfo):
    name = "Haskell"
    conforms_to_bases = ["Text"]
    exts = [".hs"]

class PowerShellLangInfo(LangInfo):
    """Windows PowerShell
    http://www.microsoft.com/windowsserver2003/technologies/management/powershell/default.mspx
    """
    name = "PowerShell"
    conforms_to_bases = ["Text"]
    exts = [".ps1"]

class SchemeLangInfo(LangInfo):
    name = "Scheme"
    conforms_to_bases = ["Text"]
    exts = [".scm"]

class VHDLLangInfo(LangInfo):
    """TODO: desc, reference"""
    name = "VHDL"
    conforms_to_bases = ["Text"]
    exts = [".vhdl"]

class VerilogLangInfo(LangInfo):
    """TODO: desc, reference"""
    name = "Verilog"
    conforms_to_bases = ["Text"]



#---- "Basic"-based languages

class _BasicLangInfo(LangInfo):
    conforms_to_bases = ["Text"]

class FreeBasicLangInfo(_BasicLangInfo):
    """http://www.freebasic.net/"""
    name = "FreeBASIC"
    komodo_name = "FreeBasic"
    exts = [".bas"]

class PureBasicLangInfo(_BasicLangInfo):
    """http://www.purebasic.com/"""
    name = "PureBasic"
    exts = [".pb"]

class PowerBasicLangInfo(_BasicLangInfo):
    """TOOD: ref?
    TODO: which if this and PureBasic should win '.pb' ext? 
    """
    name = "PowerBasic"
    exts = [".pb"]

class BlitzBasicLangInfo(_BasicLangInfo):
    """http://www.blitzbasic.com/Products/blitzmax.php"""
    name = "BlitzBasic"
    exts = [".bb"]


class VisualBasicLangInfo(_BasicLangInfo):
    name = "VisualBasic"  #TODO: should name be "Visual Basic"?
    exts = [".vb"]

class VBScriptLangInfo(_BasicLangInfo):
    name = "VBScript"
    exts = [".vbs"]



#---- less common languages (AFAICT)

class BaanLangInfo(LangInfo):
    """Baan is the scripting language used for the Baan ERP system
    (currently known as SSA ERP according to the Wikipedia article
    below).

    http://en.wikipedia.org/wiki/Baan
    http://baan.ittoolbox.com/
    """
    name = "Baan"
    conforms_to_bases = ["Text"]
    exts = [".bc"]

class REBOLLangInfo(LangInfo):
    """http://www.rebol.com/"""
    name = "REBOL"
    conforms_to_bases = ["Text"]
    exts = [".r"]

class CamlLangInfo(LangInfo):
    """http://caml.inria.fr/"""
    name = "Caml"
    komodo_name = "Objective Caml"
    conforms_to_bases = ["Text"]
    exts = [".ml", ".mli"]

