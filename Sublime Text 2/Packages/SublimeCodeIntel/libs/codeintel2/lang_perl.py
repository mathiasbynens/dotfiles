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

"""Perl support for CodeIntel"""

import os
from os.path import (normpath, join, exists, splitext, basename, isdir,
                     normcase, dirname, islink, isabs)
import sys
import logging
import time
from glob import glob
import re
from pprint import pprint, pformat
import weakref

import process
from ciElementTree import Element, SubElement, tostring
import SilverCity
from SilverCity.Lexer import Lexer
from SilverCity import ScintillaConstants

from codeintel2.common import *
from codeintel2.citadel import (ImportHandler, CitadelBuffer,
                                CitadelEvaluator, CitadelLangIntel)
from codeintel2.citadel_common import ScanRequest
from codeintel2.indexer import PreloadLibRequest
from codeintel2.parseutil import urlencode_path
from codeintel2 import perlcile
from codeintel2.util import isident, isdigit, banner, indent, markup_text
from codeintel2.tree_perl import (PerlTreeEvaluator,
                                  PerlPackageSubsTreeEvaluator,
                                  PerlPackageMembersTreeEvaluator)
from codeintel2.langintel import (ParenStyleCalltipIntelMixin,
                                  ProgLangTriggerIntelMixin)

if _xpcom_:
    from xpcom.server import UnwrapObject



#---- globals

line_end_re = re.compile("(?:\r\n|\r)")

lang = "Perl"
log = logging.getLogger("codeintel.perl")
#log.setLevel(logging.DEBUG)
CACHING = True #XXX obsolete, kill it



#---- language support

class PerlLexer(Lexer):
    lang = "Perl"
    def __init__(self):
        self._properties = SilverCity.PropertySet()
        self._lexer = SilverCity.find_lexer_module_by_id(ScintillaConstants.SCLEX_PERL)
        self._keyword_lists = [
            SilverCity.WordList(SilverCity.Keywords.perl_keywords)
        ]


#TODO: Merge handling of perl-complete-module-exports in with this one.
#      Will just need a boolean flag (on the trigger) indicating that
#      submodules should NOT be included.
class PerlImportsEvaluator(Evaluator):
    def __str__(self):
        return "Perl imports"

    def eval(self, mgr):
        try:
            prefix = self.trg.extra["prefix"]
            if prefix:
                self.ctlr.set_desc("subimports of '%s'" % prefix)
                prefix_tuple = tuple(prefix.split("::"))
            else:
                self.ctlr.set_desc("available imports")
                prefix_tuple = ()

            all_imports = set()
            for lib in self.buf.libs:
                # Reminder: A codeintel "blob" corresponds to a Perl module.
                all_imports.update(lib.get_blob_imports(prefix_tuple))
            
            if all_imports:
                cplns = [((is_dir_import and "directory" or "module"), name)
                         for name, is_dir_import in all_imports]
                cplns.sort(key=lambda i: i[1].upper())
                self.ctlr.set_cplns(cplns)
        finally:
            self.ctlr.done("success")


class PerlLangIntel(CitadelLangIntel,
                    ParenStyleCalltipIntelMixin,
                    ProgLangTriggerIntelMixin):
    lang = "Perl"

    # Add '=' to the default set for Perl. For example:
    #   my $foo =
    #     ^     ^
    #     |     `-- terminate calltip here
    #     `-- calltip triggers here
    # Because Perl doesn't have keywords args to functions this can work.
    calltip_region_terminators = tuple(']});=')
    preceding_trg_terminators = {';':None, '=':None}

    #XXX This cog regen is out-of-date. Re-write to parse perl.cix?
    # To regenerate this block:
    # - install the cog Python tool:
    #   http://www.nedbatchelder.com/code/cog/index.html
    # - run "cog -r lang_perl.py"
    #[[[cog
    #import cog
    #import os, sys
    #sys.path.insert(0, os.path.join(os.pardir, "codeintel"))
    #import cidb
    #dbpath = cidb.find_komodo_cidb_path()
    #sql = """SELECT symbol.name FROM file,scan,module,symbol
    #          WHERE file.compare_path LIKE '%perl.cix'
    #            AND scan.file_id=file.id AND module.scan_id=scan.id
    #            AND symbol.module_id=module.id AND symbol.type=0"""
    #cog.outl('_allow_trg_on_space_from_identifier = {')
    #for line in cidb.query(dbpath, 3, sql, "csv"):
    #    cog.outl('    "%s": 1,' % line.strip())
    #cog.outl('}')
    #]]]
    _allow_trg_on_space_from_identifier = {
        "-r": 1,
        "-w": 1,
        "-x": 1,
        "-o": 1,
        "-R": 1,
        "-W": 1,
        "-X": 1,
        "-O": 1,
        "-e": 1,
        "-z": 1,
        "-s": 1,
        "-f": 1,
        "-d": 1,
        "-l": 1,
        "-p": 1,
        "-S": 1,
        "-b": 1,
        "-c": 1,
        "-t": 1,
        "-u": 1,
        "-g": 1,
        "-k": 1,
        "-T": 1,
        "-B": 1,
        "-M": 1,
        "-A": 1,
        "-C": 1,
        "UNITCHECK": 1,
        "abs": 1,
        "accept": 1,
        "alarm": 1,
        "atan2": 1,
        "bind": 1,
        "binmode": 1,
        "bless": 1,
        "break": 1,
        "caller": 1,
        "chdir": 1,
        "chmod": 1,
        "chomp": 1,
        "chop": 1,
        "chown": 1,
        "chr": 1,
        "chroot": 1,
        "close": 1,
        "closedir": 1,
        "connect": 1,
        "continue": 1,
        "cos": 1,
        "crypt": 1,
        "dbmclose": 1,
        "dbmopen": 1,
        "default": 1,
        "defined": 1,
        "delete": 1,
        "die": 1,
        "do": 1,
        "dump": 1,
        "each": 1,
        "eof": 1,
        "eval": 1,
        "exec": 1,
        "exists": 1,
        "exit": 1,
        "exp": 1,
        "fcntl": 1,
        "fileno": 1,
        "flock": 1,
        "fork": 1,
        "format": 1,
        "formline": 1,
        "getc": 1,
        "getlogin": 1,
        "getpeername": 1,
        "getpgrp": 1,
        "getppid": 1,
        "getpriority": 1,
        "getpwnam": 1,
        "getgrnam": 1,
        "gethostbyname": 1,
        "getnetbyname": 1,
        "getprotobyname": 1,
        "getpwuid": 1,
        "getgrgid": 1,
        "getservbyname": 1,
        "gethostbyaddr": 1,
        "getnetbyaddr": 1,
        "getprotobynumber": 1,
        "getservbyport": 1,
        "getpwent": 1,
        "getgrent": 1,
        "gethostent": 1,
        "getnetent": 1,
        "getprotoent": 1,
        "getservent": 1,
        "setpwent": 1,
        "setgrent": 1,
        "sethostent": 1,
        "setnetent": 1,
        "setprotoent": 1,
        "setservent": 1,
        "endpwent": 1,
        "endgrent": 1,
        "endhostent": 1,
        "endnetent": 1,
        "endprotoent": 1,
        "endservent": 1,
        "getsockname": 1,
        "getsockopt": 1,
        "given": 1,
        "glob": 1,
        "gmtime": 1,
        "goto": 1,
        "grep": 1,
        "hex": 1,
        "import": 1,
        "index": 1,
        "int": 1,
        "ioctl": 1,
        "join": 1,
        "keys": 1,
        "kill": 1,
        "last": 1,
        "lc": 1,
        "lcfirst": 1,
        "length": 1,
        "link": 1,
        "listen": 1,
        "local": 1,
        "localtime": 1,
        "lock": 1,
        "log": 1,
        "lstat": 1,
        "m": 1,
        "map": 1,
        "mkdir": 1,
        "msgctl": 1,
        "msgget": 1,
        "msgrcv": 1,
        "msgsnd": 1,
        "my": 1,
        "next": 1,
        "no": 1,
        "oct": 1,
        "open": 1,
        "opendir": 1,
        "ord": 1,
        "our": 1,
        "pack": 1,
        "package": 1,
        "pipe": 1,
        "pop": 1,
        "pos": 1,
        "print": 1,
        "printf": 1,
        "prototype": 1,
        "push": 1,
        "q": 1,
        "qq": 1,
        "qr": 1,
        "qx": 1,
        "qw": 1,
        "quotemeta": 1,
        "rand": 1,
        "read": 1,
        "readdir": 1,
        "readline": 1,
        "readlink": 1,
        "readpipe": 1,
        "recv": 1,
        "redo": 1,
        "ref": 1,
        "rename": 1,
        "reset": 1,
        "return": 1,
        "reverse": 1,
        "rewinddir": 1,
        "rindex": 1,
        "rmdir": 1,
        "s": 1,
        "say": 1,
        "scalar": 1,
        "seek": 1,
        "seekdir": 1,
        "select": 1,
        "semctl": 1,
        "semget": 1,
        "semop": 1,
        "send": 1,
        "setpgrp": 1,
        "setpriority": 1,
        "setsockopt": 1,
        "shift": 1,
        "shmctl": 1,
        "shmget": 1,
        "shmread": 1,
        "shmwrite": 1,
        "shutdown": 1,
        "sin": 1,
        "sleep": 1,
        "socket": 1,
        "socketpair": 1,
        "sort": 1,
        "splice": 1,
        "split": 1,
        "sprintf": 1,
        "sqrt": 1,
        "srand": 1,
        "stat": 1,
        "state": 1,
        "study": 1,
        "substr": 1,
        "symlink": 1,
        "syscall": 1,
        "sysopen": 1,
        "sysread": 1,
        "sysseek": 1,
        "system": 1,
        "syswrite": 1,
        "tell": 1,
        "telldir": 1,
        "tie": 1,
        "tied": 1,
        "time": 1,
        "times": 1,
        "tr": 1,
        "truncate": 1,
        "uc": 1,
        "ucfirst": 1,
        "umask": 1,
        "undef": 1,
        "unlink": 1,
        "unpack": 1,
        "untie": 1,
        "unshift": 1,
        "utime": 1,
        "values": 1,
        "vec": 1,
        "wait": 1,
        "waitpid": 1,
        "wantarray": 1,
        "warn": 1,
        "when": 1,
        "write": 1,
        "y": 1,
    }
    #[[[end]]]

    # Match a subroutine definition. Used by trg_from_pos()
    _sub_pat = re.compile(r"\bsub\s+(\w+(::|'))*\w+$")
    # All Perl trigger points occur at one of these characters:
    #   ' ' (space)         only supported for built-in functions
    #   '(' (open paren)
    #   '>' (greater than)  "->" actually
    #   ':' (colon)         "::" actually
    trg_chars = tuple(' (>:')
    calltip_trg_chars = tuple(' (')

    def trg_from_pos(self, buf, pos, implicit=True):
        """
        Implemented triggers
            calltip-space-call-signature
            calltip-call-signature
            complete-package-members
            complete-*-subs meaning the actual trigger is one of:
                complete-package-subs
                complete-object-subs
            complete-available-imports

        Not yet implemented:
            complete-module-exports
        """
        DEBUG = False  # not using 'logging' system, because want to be fast
        if DEBUG:
            print banner("trg_from_pos(pos=%r, implicit=%r)"
                         % (pos, implicit))
    
        accessor = buf.accessor
        last_pos = pos - 1
        last_ch = accessor.char_at_pos(last_pos)
        if DEBUG:
            print "  last_pos: %s" % last_pos
            print "  last_ch: %r" % last_ch
    
        # All Perl trigger points occur at one of the trg_chars.
        if last_ch not in self.trg_chars:
            if DEBUG:
                print "no: %r is not in %r" % (last_ch, self.trg_chars)
            return None
        elif last_ch == ':' \
             and not (last_pos > 0
                      and accessor.char_at_pos(last_pos-1) == ':'):
            if DEBUG:
                penultimate_ch = (last_pos > 0
                                  and accessor.char_at_pos(last_pos-1) or '')
                print "no: %r is not '::'" % (penultimate_ch+last_ch)
            return None
        elif last_ch == '>' \
             and not (last_pos > 0 and accessor.char_at_pos(last_pos-1) == '-'):
            if DEBUG:
                penultimate_ch = (last_pos > 0
                                  and accessor.char_at_pos(last_pos-1) or '')
                print "no: %r is not '->'" % (penultimate_ch+last_ch)
            return None
    
        # We should never trigger in some styles (strings, comments, etc.).
        last_style = accessor.style_at_pos(last_pos)
        if DEBUG:
            last_style_names = buf.style_names_from_style_num(last_style)
            print "  style: %s %s" % (last_style, last_style_names)
        if (implicit and last_style in buf.implicit_completion_skip_styles
            or last_style in buf.completion_skip_styles):
            if DEBUG:
                print "no: completion is suppressed "\
                      "in style at %s: %s %s"\
                      % (last_pos, last_style, last_style_names)
            return None
    
        WHITESPACE = tuple(' \t\n\r')
        if last_ch == ' ':
            # This can be either "calltip-space-call-signature",
            # "complete-available-imports", or None (or
            # "complete-module-exports" when that is implemented).
            #
            # calltip-call-signature:
            #   Perl syntax allows a parameter list to be passed to a
            #   function name without enclosing parens. From a quick perusal
            #   of sample Perl code (from a default ActivePerl install)
            #   calling function this way seems to be limited to a number of
            #   core Perl built-ins or some library methods. For efficiency
            #   Komodo will maintain an explicit list of such function names
            #   for which a calltip with trigger without parentheses.
            #   XXX May want to make this a user-configurable list.
            # 
            # complete-available-imports:
            #   After 'use', 'require' or 'no' by itself on a line.
            #
            LIMIT = 50
            text = accessor.text_range(max(0,last_pos-LIMIT), last_pos) # working text
            if DEBUG: print "  working text: %r" % text
            i = len(text)-1
            if i >= 0 and not (isident(text[i]) or isdigit(text[i])):
                if DEBUG:
                    print "no: two before trigger point is not "\
                          "an ident char: '%s'" % text[i]
                return None
            while i >= 0: # parse out the preceding identifier
                if not isident(text[i]):
                    identifier = text[i+1:]
                    # Whitespace is allowed between a Perl variable special
                    # char and the variable name, e.g.: "$ myvar", "@  mylist"
                    j = i
                    while j >= 0 and text[j] in WHITESPACE: # parse off whitespace
                        j -= 1
                    if j >= 0:
                        preceding_ch = text[j]
                    else:
                        preceding_ch = None
                    break
                i -= 1
            else:
                preceding_ch = None
                identifier = text
            if DEBUG: print "  identifier: %r" % identifier
            if not identifier:
                if DEBUG:
                    print "no: no identifier preceding trigger point"
                return None
            if DEBUG: print "  preceding char: %r" % preceding_ch
            if identifier in ("use", "require", "no"):
                return Trigger("Perl", TRG_FORM_CPLN,
                               "available-imports", pos, implicit, prefix="")
            if preceding_ch and preceding_ch in "$@&%\\*": # indicating a Perl variable
                if DEBUG:
                    print "no: triggering on space after Perl "\
                          "variables not supported"
                return None
            if identifier not in self._allow_trg_on_space_from_identifier:
                if DEBUG:
                    print ("no: identifier not in set for which "
                           "space-triggering is supported "
                           "(_allow_trg_on_space_from_identifier)")
                return None
            # Specifically disallow trigger on defining a sub matching one of
            # space-trigger names, i.e.: 'sub split <|>'. Optmization: Assume
            # that there is exacly one space between 'sub' and the subroutine
            # name. Almost all examples in the Perl lib seem to follow this.
            if i >= 3 and text[i-3:i+1] == "sub ":
                if DEBUG:
                    print "no: do not trigger in sub definition"
                return None
            if DEBUG: print "calltip-space-call-signature"
            return Trigger("Perl", TRG_FORM_CALLTIP,
                           "space-call-signature", pos, implicit)
    
        elif last_ch == '(':
            # This can be either "calltip-call-signature" or None (or
            # "complete-module-exports" when that is implemented).
            LIMIT = 100
            text = accessor.text_range(max(0,last_pos-LIMIT), last_pos) # working text
            if DEBUG: print "  working text: %r" % text
            i = len(text)-1
            while i >= 0 and text[i] in WHITESPACE: # parse off whitespace
                i -= 1
            if i >= 0 and not (isident(text[i]) or isdigit(text[i])):
                if DEBUG:
                    print "no: first non-ws char before "\
                          "trigger point is not an ident char: '%s'" % text[i]
                return None
            end = i+1
            while i >= 0: # parse out the preceding identifier
                if not isident(text[i]):
                    identifier = text[i+1:end]
                    # Whitespace is allowed between a Perl variable special
                    # char and the variable name, e.g.: "$ myvar", "@  mylist"
                    j = i
                    while j >= 0 and text[j] in WHITESPACE: # parse off whitespace
                        j -= 1
                    if j >= 0:
                        preceding_ch = text[j]
                    else:
                        preceding_ch = None
                    break
                i -= 1
            else:
                preceding_ch = None
                identifier = text[:end]
            if DEBUG: print "  identifier: %r" % identifier
            if DEBUG:
                assert ' ' not in identifier, "parse error: space in identifier: %r" % identifier
            if not identifier:
                if DEBUG:
                    print "no: no identifier preceding trigger point"
                return None
            if DEBUG: print "  preceding char: %r" % preceding_ch
            if preceding_ch and preceding_ch in "$@%\\*":
                # '&foo(' *is* a trigger point, but the others -- '$foo(',
                # '&$foo(', etc. -- are not because current CodeIntel wouldn't
                # practically be able to determine the method to which $foo
                # refers.
                if DEBUG:
                    print "no: calltip trigger on Perl var not supported"
                return None
            if identifier in ("if", "else", "elsif", "while", "for",
                              "sub", "unless", "my", "our"):
                if DEBUG:
                    print "no: no trigger on anonymous sub or control structure"
                return None
            # Now we want to rule out the subroutine definition lines, e.g.:
            #    sub FOO(<|>
            #    sub FOO::BAR(<|>
            #    sub FOO'BAR(<|>
            #    sub FOO::BAR::BAZ(<|>
            # Note: Frankly 80/20 rules out the last three.
            line = text[:end].splitlines(0)[-1]
            if DEBUG:
                print "  trigger line: %r" % line
            if "sub " in line: # only use regex if "sub " on that line
                if DEBUG:
                    print "  *could* be a subroutine definition"
                if self._sub_pat.search(line):
                    if DEBUG:
                        print "no: no trigger on Perl sub definition"
                    return None
            if DEBUG: print "calltip-call-signature"
            return Trigger("Perl", TRG_FORM_CALLTIP, "call-signature",
                           pos, implicit)
    
        elif last_ch == '>':
            # Must be "complete-package-subs", "complete-object-subs"
            # or None. Note that we have already checked (above) that the
            # trigger string is '->'. Basically, as long as the first
            # non-whitespace char preceding the '->' is an identifier char,
            # then this is a trigger point.
            LIMIT = 50
            text = accessor.text_range(max(0,last_pos-1-LIMIT), last_pos-1) # working text
            if DEBUG: print "  working text: %r" % text
            i = len(text)-1
            while i >= 0 and text[i] in WHITESPACE: # parse off whitespace
                i -= 1
            if i < 0:
                if DEBUG:
                    print "no: no non-whitespace text preceding '->'"
                return None
            elif not (isident(text[i]) or text[i].isdigit()):
                if DEBUG:
                    print "no: first non-ws char before "\
                          "trigger point is not an ident char: '%s'" % text[i]
                return None
            # At this point we know it is either "complete-package-subs"
            # or "complete-object-subs". We don't really care to take
            # the time to distinguish now -- trg_from_pos is supposed to be
            # quick -- and we don't have to. 
            if DEBUG: print "complete-*-subs"
            return Trigger("Perl", TRG_FORM_CPLN, "*-subs", pos, implicit,
                           length=2)
    
        elif last_ch == ':':
            # Must be "complete-package-members" or
            # "complete-available-imports" or None. Note that we have
            # already checked (above) that the trigger string is '::'.
            # Basically, as long as the first char preceding the '::' is
            # an identifier char or one of Perl's funny variable
            # identifying characters, then this is a trigger point.
            LIMIT = 50
            text = accessor.text_range(max(0,last_pos-1-LIMIT), last_pos-1) # working text
            if DEBUG: print "  working text: %r" % text
            i = len(text)-1
            if i < 0:
                if DEBUG:
                    print "no: no text preceding '::'"
                return None
            ch = text[i]
            if not (isident(ch) or isdigit(ch) or ch == '$'):
                # Technically should allow '@', '%' and '&' in there, but
                # there a total of 5 of all of this in the Perl std lib.
                # 80/20 rule.
                if DEBUG:
                    print "no: first char before trigger "\
                          "point is not an ident char or '$': '%s'" % ch
                return None
            # Check if this is in a 'use' or 'require' statement.
            while i > 0 and text[i-1] not in WHITESPACE: # skip to whitespace
                i -= 1
            prefix = text[i:pos-2]
            while i > 0 and text[i-1]     in WHITESPACE: # skip over whitespace
                i -= 1
            start_idx = end_idx = i
            while start_idx > 0 and (isident(text[start_idx-1])
                                     or text[start_idx-1] in '$@%'):
                start_idx -= 1
            ident = text[start_idx:end_idx]
            if ident in ("use", "require", "no"):
                if DEBUG:
                    print "complete-available-imports (prefix=%r)" % prefix
                return Trigger("Perl", TRG_FORM_CPLN, "available-imports",
                               pos, implicit, length=2, prefix=prefix)
            if DEBUG: print "complete-package-members (prefix=%r)" % prefix
            return Trigger("Perl", TRG_FORM_CPLN, "package-members", pos,
                           implicit, length=2, prefix=prefix)
    
        return None


    _perl_var_pat = re.compile(
        r"((?P<prefix>[$@%\\*&]+)\s*)?(?P<scope>(::)?\b((?!\d)\w*?(::|'))*)(?P<name>(?!\d)\w+)$")
    def citdl_expr_and_prefix_filter_from_trg(self, buf, trg):
        """Parse out the Perl expression at the given trigger and return
        a CITDL expression for it (and possibly a variable prefixj
        filter).
        
        Returns a 2-tuple:
            (<CITDL-expression>, <variable-prefix-filter>)
    
        For all triggers except TRG_FORM_DEFN, we parse out the Perl
        expression preceding the trigger position, simplify the
        expression (by removing whitespace, etc.) and translate that to
        an appropriate CITDL (*) expression. Set to None if there is no
        appropriate such expression. For TRG_FORM_DEFN triggers we first
        move forward to the end of the current word.
        
        As well, a variable prefix filter may be returned, useful for
        post-processing of completions. For example:
        
            Perl code           CITDL expression    prefix filter
            ---------           ----------------    -------------
            Foo::Bar<|>::       Foo::Bar            None
            $Foo::Bar<|>::      Foo::Bar            $

        Optimization Notes:
        - We can throw out Perl expressions with function calls
          because CodeIntel does not currently handle return values.
        - We can throw out Perl exprs that span an EOL: 80/20 rule. (We
          currently don't throw these away, though.)
        - Abort at hash and list indexing: the types of elements in these
          objects are not tracked by CodeIntel.
        - Punt on Perl references, e.g. \$foo, \@bar. XXX I wonder if I can
          just ignore references and assume the user is doing the right
          thing. I.e. I just presume that a reference is dereferenced
          properly when required. Dunno.
        - Currently we don't really make use of the styling info because we
          abort at indexing, function call arguments, etc. where recognizing
          string/number/regex boundaries would be useful. This info might be
          useful later if this algorithm is beefed up.
        - Ignore ampersand, e.g. &foo. This is just an old way to call perl
          functions - bug 87870, we can just ignore it for codeintel.
        
        Examples:
       
            GIVEN                       LEADING EXPR            CITDL EXPR
            -----                       ------------            ----------
            split <|>                   split                   split
            chmod(<|>                   chmod                   chmod
            $Foo::bar(<|>               $Foo::bar               Foo.$bar
            &$make_coffee(<|>           &$make_coffee           $make_coffee
            Win32::OLE-><|>             Win32::OLE              Win32::OLE
            Win32::OLE->GetObject(<|>   Win32::OLE->GetObject   Win32::OLE.GetObject
            split join <|>              join                    join
            foo->bar(<|>                foo->bar                foo.bar
    
        Note that the trigger character is sometimes necessary to resolve
        ambiguity. Given "Foo::Bar" without the trailing trigger char, we
        cannot know if the CITDL should be "Foo.Bar" or "Foo::Bar":
    
            GIVEN               CITDL EXPR
            -----               ----------
            Foo::Bar::<|>       Foo::Bar
            $Foo::Bar::<|>      Foo::Bar
            Foo::Bar-><|>       Foo::Bar
            Foo::Bar(<|>        Foo.Bar
            Foo::Bar <|>        Foo.Bar
            $Foo::Bar-><|>      Foo.$Bar
            $Foo::Bar(<|>       Foo.$Bar
            $Foo::Bar <|>       Foo.$Bar
    
        * http://specs.tl.activestate.com/kd/kd-0100.html#citdl
        """
        DEBUG = False
        if DEBUG:
            print
            print banner("citdl_expr_and_prefix_filter_from_trg @ %d"
                         % trg.pos)
            print markup_text(buf.accessor.text, trg_pos=trg.pos)
            print banner(None, '-')

        if trg.implicit:
            skip_styles = buf.implicit_completion_skip_styles
        else:
            skip_styles = {}
        filter, citdl = None, []

        accessor = buf.accessor
        LIMIT = max(0, trg.pos-100) # working text area
        if trg.form == TRG_FORM_DEFN:
            # "Go to Definition" triggers can be in the middle of an
            # expression. If so we want to move forward to the end of
            # the current *part*. E.g., given:
            #   $fo<+>o->bar()
            # move forward to:
            #   $foo<|>->bar()
            # and NOT to:
            #   $foo->bar<|>()
            #
            # Perl package names are considered one "part":
            #   $Fo<+>o::Bar->blah()           $Foo::Bar<|>->blah()
            #
            # Note: I suspect there are some problems with the
            # subsequent parsing on when/if to convert "Foo::Bar" to
            # "Foo.Bar" since codeintel2 changed Perl cpln eval.
            p = trg.pos
            length = accessor.length()
            while p < length:
                if not _is_perl_var_char(accessor.char_at_pos(p)):
                    break
                p += 1
            # Gracefully handle some situations where we are positioned
            # after a trigger string. E.g. "Foo::Bar::<|> "
            if p >= 2 and accessor.text_range(p-2, p) in ("->", "::"):
                p = p - 2

            if DEBUG:
                print "'defn'-trigger: adjust position %d" % (p-trg.pos)
        else:
            p = trg.pos - trg.length

        p -= 1
        while p >= LIMIT:
            # Parse off a perl variable/identifier.
            if DEBUG:
                print "look for Perl var at end of %r"\
                      % accessor.text_range(LIMIT, p+1)
            match = self._perl_var_pat.search(
                accessor.text_range(LIMIT, p+1))
            if not match:
                if DEBUG:
                    if p-LIMIT > 20:
                        segment = '...'+accessor.text_range(p-20, p+1)
                    else:
                        segment = accessor.text_range(LIMIT, p+1)
                    print "could not match a Perl var off %r" % segment
                citdl = None
                break
            prefix = match.group("prefix") or ""
            if "&" in prefix:
                prefix = prefix.replace("&", "")
            scope = match.group("scope")
            name = match.group("name")

            trg_ch = None
            try:
                #TODO:PERF: Use the available faster accessor methods here.
                trg_ch = accessor.char_at_pos(p+1)
            except IndexError, ex:
                if trg.form != TRG_FORM_DEFN:
                    log.warn("text does not include trailing trigger "
                             "char to resolve possible ambiguities in '%s'",
                             match.group(0))
            if trg_ch == ':':
                #XXX fix off-by-one here
                # Foo::Bar<|>::       Foo::Bar
                # $Foo::Bar<|>::      Foo::Bar
                citdl.insert(0, scope+name) # intentionally drop prefix
                # The prefix string is relevant for filtering the list of
                # members for AutoComplete. E.g. if the prefix char is '&' then
                # only subs should be shown. If '%', then only hashes.
                filter = prefix
            elif trg_ch == '-' and not prefix:
                #XXX fix off-by-one here
                # Foo::Bar<|>->       Foo::Bar
                citdl.insert(0, scope+name)
            else:
                #XXX fix off-by-one here
                # Foo::Bar<|>(        Foo.Bar
                # Foo::Bar<|>         Foo.Bar         # trigger char is a space here
                # $Foo::Bar<|>->      Foo.$Bar
                # $Foo::Bar<|>(       Foo.$Bar
                # $Foo::Bar<|>        Foo.$Bar        # trigger char is a space here
                citdl.insert(0, prefix+name)
                if scope:
                    scope = scope[:-2] # drop trailing '::'
                    if scope:
                        citdl.insert(0, scope)
            p -= len(match.group(0))
            if DEBUG:
                print "parse out Perl var: %r (prefix=%r, scope=%r, "\
                      "name=%r): %r" % (match.group(0), prefix, scope,
                                        name, citdl)
    
            # Preceding characters will determine if we stop or continue.
            WHITESPACE = tuple(" \t\n\r\v\f")
            while p >= LIMIT and accessor.char_at_pos(p) in WHITESPACE:
                #if DEBUG: print "drop whitespace: %r" % text[p]
                p -= 1
            if p >= LIMIT and accessor.style_at_pos(p) in skip_styles:
                if DEBUG:
                    style = accessor.style_at_pos(p)
                    style_names = buf.style_names_from_style_num(style)
                    print "stop at style to ignore: %r (%s %s)"\
                          % (accessor.char_at_pos(p), style, style_names)
                break
            elif p >= LIMIT+1 and accessor.text_range(p-1, p+1) == '->':
                if DEBUG: print "parse out '->'"
                p -= 2
                while p >= LIMIT and accessor.char_at_pos(p) in WHITESPACE:
                    #if DEBUG: print "drop whitespace: %r" % text[p]
                    p -= 1
                continue
            else:
                break
    
        if citdl:
            retval = ('.'.join(citdl), filter)
        else:
            retval = (None, filter)
        if DEBUG:
            print "returning: %r" % (retval,)
            banner("done")
        return retval

    def async_eval_at_trg(self, buf, trg, ctlr):
        if _xpcom_:
            trg = UnwrapObject(trg)
            ctlr = UnwrapObject(ctlr)
        assert trg.lang == "Perl"
        ctlr.start(buf, trg)

        if trg.id == ("Perl", TRG_FORM_CPLN, "available-imports"):
            evalr = PerlImportsEvaluator(ctlr, buf, trg)
            buf.mgr.request_eval(evalr)
            return

        # Remaining triggers all use this parsed CITDL expr.
        # Extract the leading CITDL expression (and possible filter,
        # i.e. '$', '@', ...).
        try:
            citdl_expr, filter \
                = self.citdl_expr_and_prefix_filter_from_trg(buf, trg)
        except CodeIntelError, ex:
            ctlr.error(str(ex))
            ctlr.done("error")
            return

        # Perl's trg_from_pos doesn't distinguish btwn "package-subs" 
        # and "object-subs" trigger type -- calling them both "*-subs".
        # Let's do so here.
        if trg.type == "*-subs":
            assert citdl_expr
            if isident(citdl_expr[0]):
                trg.type = "package-subs"
            else:
                trg.type = "object-subs"

        if trg.id == ("Perl", TRG_FORM_CPLN, "package-members"):
            # [prefix]SomePackage::<|>
            # Note: This trigger has the "prefix" extra attr which could
            #       be used instead of the leading CITDL expr parse.
            line = buf.accessor.line_from_pos(trg.pos)
            evalr = PerlPackageMembersTreeEvaluator(ctlr, buf, trg, citdl_expr,
                                                    line, filter)
            buf.mgr.request_eval(evalr)
        elif trg.id == ("Perl", TRG_FORM_CPLN, "package-subs"):
            # SomePackage-><|>
            assert not filter, "shouldn't be Perl filter prefix for " \
                "'complete-package-subs': %r" % filter
            line = buf.accessor.line_from_pos(trg.pos)
            evalr = PerlPackageSubsTreeEvaluator(ctlr, buf, trg, citdl_expr, line)
            buf.mgr.request_eval(evalr)
        #TODO: Might want to handle TRG_FORM_DEFN differently.
        else:
            if citdl_expr is None:
                ctlr.info("no CITDL expression found for %s" % trg)
                ctlr.done("no trigger")
                return
            line = buf.accessor.line_from_pos(trg.pos)
            evalr = PerlTreeEvaluator(ctlr, buf, trg, citdl_expr,
                                      line, filter)
            buf.mgr.request_eval(evalr)


    def libs_from_buf(self, buf):
        env = buf.env

        # A buffer's libs depend on its env and the buf itself so
        # we cache it on the env and key off the buffer.
        if "perl-buf-libs" not in env.cache:
            env.cache["perl-buf-libs"] = weakref.WeakKeyDictionary()
        cache = env.cache["perl-buf-libs"] # <buf-weak-ref> -> <libs>

        if buf not in cache:
            # - curdirlib
            # Using the dirname of this buffer isn't always right, but
            # hopefully is a good first approximation.
            cwd = dirname(buf.path)
            if cwd == "<Unsaved>":
                libs = []
            else:
                libs = [ self.mgr.db.get_lang_lib("Perl", "curdirlib", [cwd]) ]

            libs += self._buf_indep_libs_from_env(env)
            cache[buf] = libs
        return cache[buf]

    def _perl_from_env(self, env):
        import which
        path = [d.strip() 
                for d in env.get_envvar("PATH", "").split(os.pathsep)
                if d.strip()]
        try:
            return which.which("perl", path=path) 
        except which.WhichError:
            return None

    def _perl_info_from_perl(self, perl, env):
        """Call the given Perl and return:
            (<version>, <config_dirs>, <import_path>)
        where <config_dirs> is a dict with (relevant) dirs from
        Config.pm.
        """
        import process

        info_cmd = (r'use Config;'
                    r'print "version:$Config{version}\n";'
                    r'print "siteprefix:$Config{siteprefix}\n";'
                    r'print "archlib:$Config{archlib}\n";'
                    r'print "privlib:$Config{privlib}\n";'
                    r'print "vendorarch:$Config{vendorarch}\n";'
                    r'print "vendorlib:$Config{vendorlib}\n";'
                    r'print join("\n", @INC);')
        argv = [perl, "-e", info_cmd]
        log.debug("run `%s -e ...'", perl)
        p = process.ProcessOpen(argv, env=env.get_all_envvars(), stdin=None)
        stdout, stderr = p.communicate()
        stdout_lines = stdout.splitlines(0)
        retval = p.returncode
        if retval:
            log.warn("failed to determine Perl info:\n"
                     "  path: %s\n"
                     "  retval: %s\n"
                     "  stdout:\n%s\n"
                     "  stderr:\n%s\n",
                     perl, retval, indent('\n'.join(stdout_lines)),
                     indent(stderr))

        perl_ver = stdout_lines[0].split(':', 1)[1]
        config_dirs = dict(
            siteprefix = stdout_lines[1].split(':', 1)[1],
            archlib    = stdout_lines[2].split(':', 1)[1],
            privlib    = stdout_lines[3].split(':', 1)[1],
            vendorarch = stdout_lines[4].split(':', 1)[1],
            vendorlib  = stdout_lines[5].split(':', 1)[1],
        )
        import_path = stdout_lines[6:]

        return perl_ver, config_dirs, import_path

    def _extra_dirs_from_env(self, env):
        extra_dirs = set()
        for pref in env.get_all_prefs("perlExtraPaths"):
            if not pref: continue
            extra_dirs.update(d.strip() for d in pref.split(os.pathsep)
                              if exists(d.strip()))
        return tuple(extra_dirs)

    def _buf_indep_libs_from_env(self, env):
        """Create the buffer-independent list of libs."""
        cache_key = "perl-libs"
        if cache_key not in env.cache:
            env.add_pref_observer("perl", self._invalidate_cache)
            env.add_pref_observer("perlExtraPaths",
                                  self._invalidate_cache_and_rescan_extra_dirs)
            env.add_pref_observer("codeintel_selected_catalogs",
                                  self._invalidate_cache)
            db = self.mgr.db

            # Gather information about the current perl.
            perl = None
            if env.has_pref("perl"):
                perl = env.get_pref("perl").strip() or None
            if not perl or not exists(perl):
                perl = self._perl_from_env(env)
            if not perl:
                log.warn("no Perl was found from which to determine the "
                         "import path")
                perl_ver, config_dirs, import_path = None, {}, []
            else:
                perl_ver, config_dirs, import_path \
                    = self._perl_info_from_perl(perl, env)
                
            libs = []

            # - extradirslib
            extra_dirs = self._extra_dirs_from_env(env)
            if extra_dirs:
                log.debug("Perl extra lib dirs: %r", extra_dirs)
                libs.append( db.get_lang_lib("Perl", "extradirslib",
                                extra_dirs) )
            
            # Figuring out where the lib and sitelib dirs are is hard --
            # or at least complex from my P.O.V.
            # - For ActivePerl (on Linux, at least):
            #      $ perl -e 'print join "\n", @INC'
            #      /home/trentm/opt/ActivePerl-5.8.8.818/site/lib
            #           (sitearch, sitelib, siteprefix)
            #      /home/trentm/opt/ActivePerl-5.8.8.818/lib
            #           (archlib, privlib)
            #      . (???, we'll handle with curdirlib)
            # - For /usr/bin/perl on skink (ubuntu 6):
            #      $ /usr/bin/perl -e 'print join "\n", @INC'
            #      /etc/perl (???)
            #      /usr/local/lib/perl/5.8.7 (sitearch, siteprefix)
            #      /usr/local/share/perl/5.8.7 (sitelib, siteprefix)
            #      /usr/lib/perl5 (vendorarch)
            #      /usr/share/perl5 (vendorlib)
            #      /usr/lib/perl/5.8 (archlib)
            #      /usr/share/perl/5.8 (privlib)
            #      /usr/local/lib/site_perl (???, siteprefix)
            paths_from_libname = {"sitelib": [], "envlib": [], "stdlib": []}
            for dir in import_path:
                dir = normpath(dir)
                if dir == ".": # -> curdirlib (handled separately)
                    continue
                if islink(dir):
                    # Note: this doesn't handle multiple levels of
                    # links.
                    link_value = os.readlink(dir)
                    if isabs(link_value):
                        dir = link_value
                    else:
                        dir = normpath(join(dirname(dir), link_value))

                if not isdir(dir):
                    log.debug("perl @INC value '%s' is not a dir: dropping it",
                              dir)
                    continue
                for config_dir_name in ("archlib", "privlib",
                                        "vendorarch", "vendorlib"):
                    if config_dirs[config_dir_name] \
                       and dir.startswith(config_dirs[config_dir_name]):
                        paths_from_libname["stdlib"].append(dir)
                        break
                else:
                    if config_dirs["siteprefix"] \
                         and dir.startswith(config_dirs["siteprefix"]):
                        paths_from_libname["sitelib"].append(dir)
                    else:
                        paths_from_libname["envlib"].append(dir)
            log.debug("Perl %s paths for each lib:\n%s",
                      perl_ver, indent(pformat(paths_from_libname)))

            # - envlib, sitelib, cataloglib, stdlib
            if paths_from_libname["envlib"]:
                libs.append( db.get_lang_lib("Perl", "envlib", 
                                paths_from_libname["envlib"]) )
            if paths_from_libname["sitelib"]:
                libs.append( db.get_lang_lib("Perl", "sitelib", 
                                paths_from_libname["sitelib"]) )
            catalog_selections = env.get_pref("codeintel_selected_catalogs")
            libs += [
                db.get_catalog_lib("Perl", catalog_selections),
                db.get_stdlib("Perl", perl_ver)
            ]
            env.cache[cache_key] = libs

        return env.cache[cache_key]

    def _invalidate_cache(self, env, pref_name):
        for key in ("perl-buf-libs", "perl-libs"):
            if key in env.cache:
                log.debug("invalidate '%s' cache on %r", key, env)
                del env.cache[key]

    def _invalidate_cache_and_rescan_extra_dirs(self, env, pref_name):
        self._invalidate_cache(env, pref_name)
        extra_dirs = self._extra_dirs_from_env(env)
        if extra_dirs:
            extradirslib = self.mgr.db.get_lang_lib(
                "Perl", "extradirslib", extra_dirs)
            request = PreloadLibRequest(extradirslib)
            self.mgr.idxr.stage_request(request, 1.0)

    #---- code browser integration
    cb_import_group_title = "Uses and Requires"   

    def cb_import_data_from_elem(self, elem):
        alias = elem.get("alias")
        symbol = elem.get("symbol")
        module = elem.get("module")
        if symbol:
            if symbol == "*":
                name = module
                detail = "use %s" % module
            elif symbol == "**":
                name = module
                detail = "use %s qw(:<tag>)" % module
            else:
                name = "::".join([module, symbol])
                detail = "use %s qw(%s)" % (module, symbol)
        else:
            name = module
            # This is either "use Foo ();" or "require Foo;". A search
            # the of the Perl 5.8 site lib should that the latter is about
            # 6 times more likely -- lets use that.
            detail = "require %s" % module
        return {"name": name, "detail": detail}


class PerlBuffer(CitadelBuffer):
    lang = "Perl"
    sce_prefixes = ["SCE_PL_"]

    cb_show_if_empty = True

    # 'cpln_fillup_chars' exclusions for Perl:
    # - cannot be '-' for "complete-*-subs" because:
    #       attributes::->import(__PACKAGE__, \$x, 'Bent');
    # - cannot be '{' for "complete-object-subs" because:
    #       my $d = $self->{'escape'};
    # - shouldn't be ')' because:
    #       $dumper->dumpValue(\*::);
    # - shouldn't be ':' (bug 65292)
    cpln_fillup_chars = "~`!@#$%^&*(=+}[]|\\;'\",.<>?/ "
    cpln_stop_chars = "-~`!@#$%^&*()=+{}[]|\\;:'\",.<>?/ "

    def __init__(self, *args, **kwargs):
        CitadelBuffer.__init__(self, *args, **kwargs)

        # Some Perl styles in addition to the usual comment and string styles
        # in which completion triggering should not happen.
        self.completion_skip_styles[ScintillaConstants.SCE_PL_REGEX] = True

    @property
    def libs(self):
        return self.langintel.libs_from_buf(self)

    @property
    def stdlib(self):
        return self.libs[-1]


class PerlImportHandler(ImportHandler):
    PATH_ENV_VAR = "PERL5LIB"
    sep = "::"

    # Try to speed up self._getPath() a little bit. This is called
    # *very* frequently for Perl.
    def __init__(self, mgr):
        ImportHandler.__init__(self, mgr)
        self._pathCache = None
        self._findModuleOnDiskCache = {}

    if CACHING:
        def _getPath(self, cwd=None):
            if self._pathCache is None:
                self._pathCache = ImportHandler._getPath(self) # intentionally exclude cwd
            if cwd:
                return [cwd] + self._pathCache
            else:
                return self._pathCache

    def _shellOutForPath(self, compiler):
        import process
        sep = "--WomBa-woMbA--"
        argv = [compiler, "-e", "print join('%s', @INC);" % sep]
        env = dict(os.environ)
        if "PERL5LIB" in env: del env["PERL5LIB"]
        if "PERLLIB" in env: del env["PERLLIB"]

        p = process.ProcessOpen(argv, env=env, stdin=None)
        output, error = p.communicate()
        retval = p.returncode
        if retval:
            raise CodeIntelError("could not determine Perl import path: %s"
                                 % error)
        path = [normpath(d) for d in output.split(sep)]
        # cwd handled separately
        path = [p for p in path if p not in (os.curdir, os.getcwd())]
        return path

    def setCorePath(self, compiler=None, extra=None):
        if compiler is None:
            import which
            compiler = which.which("perl")
        self.corePath = self._shellOutForPath(compiler)

    def _findScannableFiles(self,
                            (files, searchedDirs, skipTheseDirs, skipRareImports),
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
        if skipRareImports:
            # Skip .pl files when scanning a Perl lib/sitelib.
            scannableExts = (".pm",)
        else:
            scannableExts = (".pl", ".pm")
        for i in range(len(names)-1, -1, -1): # backward so can del from list
            path = join(dirname, names[i])
            if isdir(path):
                if normcase(path) in skipTheseDirs:
                    del names[i]
                elif skipRareImports and not ('A' <= names[i][0] <= 'Z'):
                    # Perl good practice dictates that all module directories
                    # begin with a capital letter. Therefore, we skip dirs
                    # that start with a lower case.
                    del names[i]
            elif splitext(names[i])[1] in scannableExts:
                #XXX The list of extensions should be settable on
                #    the ImportHandler and Komodo should set whatever is
                #    set in prefs.
                #XXX This check for files should probably include
                #    scripts, which might likely not have the
                #    extension: need to grow filetype-from-content smarts.
                files.append(path)

    def genScannableFiles(self, path=None, skipRareImports=False,
                          importableOnly=False):
        if path is None:
            path = self._getPath()
        searchedDirs = {}
        for dirname in path:
            if dirname == os.curdir:
                # Do NOT traverse the common '.' element of @INC. It is
                # environment-dependent so not useful for the typical call
                # of this method.
                continue
            skipTheseDirs = [join(dirname, "auto")]
            skipTheseDirs = [normcase(d) for d in skipTheseDirs]
            files = []
            os.path.walk(dirname, self._findScannableFiles,
                         (files, searchedDirs, skipTheseDirs,
                          skipRareImports))
            for file in files:
                yield file

    def find_importables_in_dir(self, dir):
        """See citadel.py::ImportHandler.find_importables_in_dir() for
        details.

        Importables for Perl look like this:
            {"Shell": ("Shell.pm", None, False),
             "LWP":   ("LWP.pm",   None, True),
             "XML":   (None,       None, True)}

        Notes:
        - Drop the "auto" dir (it holds the binary module bits).
        - Keep non-capitalized dirs and modules (e.g. want "strict" in
          cplns for "use <|>").
        """
        from os.path import join, isdir, splitext

        if dir == "<Unsaved>":
            #TODO: stop these getting in here.
            return {}

        #TODO: log the fs-stat'ing a la codeintel.db logging.
        try:
            names = os.listdir(dir)
        except OSError, ex:
            return {}
        dirs, nondirs = set(), set()
        for name in names:
            if isdir(join(dir, name)):
                dirs.add(name)
            else:
                nondirs.add(name)

        importables = {}
        dirs.discard("auto")
        for name in nondirs:
            base, ext = splitext(name)
            if ext != ".pm":
                continue
            if base in dirs:
                importables[base] = (name, None, True)
                dirs.remove(base)
            else:
                importables[base] = (name, None, False)
        for name in dirs:
            importables[name] = (None, None, True)

        return importables


class PerlCILEDriver(CILEDriver):
    lang = lang

    def scan_purelang(self, buf):
        return perlcile.scan_purelang(buf)
    
    def scan_multilang(self, buf, csl_cile_driver=None):
        """Scan the given multilang (UDL-based) buffer and return a CIX
        element tree, and shuffle any CSL tokens to the CSL CileDriver.
        """
        tree = Element("codeintel", version="2.0")
        path = buf.path
        if sys.platform == "win32":
            path = path.replace('\\', '/')
        file_node = SubElement(tree, "file", lang=buf.lang, path=path)
        # module = SubElement(file_node, "scope", ilk="blob", lang="Perl", name=basename(path))
        csl_tokens, has_perl_code = perlcile.scan_multilang(buf.accessor.gen_tokens(), file_node)
        blob_node = file_node.getchildren()[0]
        if not has_perl_code:
            assert len(blob_node) == 0
            # The CILE clients don't want to hear there's no perl code in the buffer
            file_node.remove(blob_node)
        else:
            blob_node.set('name', basename(path))
        if csl_cile_driver and csl_tokens:
            csl_cile_driver.scan_csl_tokens(file_node, basename(buf.path),
                                            csl_tokens)
        return tree



#---- internal support stuff

def _is_perl_var_char(char):
    return "a" <= char <= "z" or "A" <= char <= "Z" \
           or char in "_:$%@"



#---- registration

def register(mgr):
    """Register language support with the Manager."""
    mgr.set_lang_info(lang,
                      silvercity_lexer=PerlLexer(),
                      buf_class=PerlBuffer,
                      langintel_class=PerlLangIntel,
                      import_handler_class=PerlImportHandler,
                      cile_driver_class=PerlCILEDriver,
                      is_cpln_lang=True)

