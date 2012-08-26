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
#
# Contributors:
#   Eric Promislow (EricP@ActiveState.com)

"""
    perlcile - a Code Intelligence Language Engine for the Perl language

    Module Usage:
        from perlcile import scan_purelang
        content = open("foo.pl", "r").read()
        scan_purelang(content, "foo.pl")
    
    Command-line Usage:
        perlcile.py [<options>...] [<Perl file>]

    Options:
        -h, --help          dump this help and exit
        -V, --version       dump this script's version and exit
        -v, --verbose       verbose output, use twice for more verbose output
        -f, --filename <path>   specify the filename of the file content
                            passed in on stdin, this is used for the "path"
                            attribute of the emitted <file> tag.
        --md5=<string>      md5 hash for the input
        --mtime=<secs>      modification time for output info, in #secs since
                            1/1/70.
        -L, --language <name>
                            the language of the file being scanned
        -c, --clock         print timing info for scans (CIX is not printed)

    One or more Perl files can be specified as arguments or content can be
    passed in on stdin. A directory can also be specified, in which case
    all .pl files in that directory are scanned.

    This is a Language Engine for the Code Intelligence (codeintel) system.
    Code Intelligence XML format. See:
        http://specs.activestate.com/Komodo_3.0/func/code_intelligence.html
        http://specs.tl.activestate.com/kd/kd-0100.html
    
    The command-line interface will return non-zero iff the scan failed.
"""

import os
import os.path
import sys
import getopt
from hashlib import md5
import re
import logging
import glob
import time
import stat

from ciElementTree import Element, SubElement, tostring
from SilverCity import ScintillaConstants

from codeintel2 import perl_lexer, perl_parser, util
from codeintel2.tree import pretty_tree_from_tree
from codeintel2.common import CILEError
from codeintel2 import parser_cix

#---- global data

_version_ = (0, 1, 0)
log = logging.getLogger("perlcile")
#log.setLevel(logging.DEBUG)

_gClockIt = 0   # if true then we are gathering timing data
_gClock = None  # if gathering timing data this is set to time retrieval fn
_gStartTime = None   # start time of current file being scanned

gProvideFullDocs = False


#---- internal support
# This code has intimate knowledge of the code objects defined in
# perl_parser.py

def scan_purelang(buf):
    content = buf.accessor.text.expandtabs(8)
    tokenizer = perl_lexer.PerlLexer(content, gProvideFullDocs)
    parser = perl_parser.Parser(tokenizer, provide_full_docs=gProvideFullDocs)
    parser.moduleName = buf.path
    parse_tree = parser.parse()
    tree = parser.produce_CIX()
    return tree

def scan_multilang(tokens, module_elem):
    """Build the Perl module CIX element tree.

        "tokens" is a generator of UDL tokens for this UDL-based
            multi-lang document.
        "module_elem" is the <module> element of a CIX element tree on
            which the Perl module should be built.

    This should return a list of the CSL tokens in the token stream.
    """
        
    tokenizer = perl_lexer.PerlMultiLangLexer(tokens)
    # "PerlHTML" is about all we need for whichever Perl-based
    # template language is being used.  This could just as easily be a
    # boolean that indicates whether we're processing a pure language
    # or a multi-lang one.
    
    parser = perl_parser.Parser(tokenizer, lang="PerlHTML", provide_full_docs=gProvideFullDocs)
    parser.moduleName = "" #Unknown
    parser.parse()
    parse_tree = parser.produce_CIX_NoHeader(module_elem)
    csl_tokens = tokenizer.get_csl_tokens()
    return csl_tokens, tokenizer.has_perl_code()

#---- mainline

def main(argv):
    logging.basicConfig()
    # Parse options.
    try:
        opts, args = getopt.getopt(argv[1:], "Vvhf:cL:",
            ["version", "verbose", "help", "filename=", "md5=", "mtime=",
             "clock", "language="])
    except getopt.GetoptError, ex:
        log.error(str(ex))
        log.error("Try `perlcile --help'.")
        return 1
    numVerboses = 0
    stdinFilename = None
    md5sum = None
    mtime = None
    lang = "Perl"
    global _gClockIt
    for opt, optarg in opts:
        if opt in ("-h", "--help"):
            sys.stdout.write(__doc__)
            return
        elif opt in ("-V", "--version"):
            ver = '.'.join([str(part) for part in _version_])
            print "perlcile %s" % ver
            return
        elif opt in ("-v", "--verbose"):
            numVerboses += 1
            if numVerboses == 1:
                log.setLevel(logging.INFO)
            else:
                log.setLevel(logging.DEBUG)
        elif opt in ("-f", "--filename"):
            stdinFilename = optarg
        elif opt in ("-L", "--language"):
            lang = optarg
        elif opt in ("--md5",):
            md5sum = optarg
        elif opt in ("--mtime",):
            mtime = optarg
        elif opt in ("-c", "--clock"):
            _gClockIt = 1
            global _gClock
            if sys.platform.startswith("win"):
                _gClock = time.clock
            else:
                _gClock = time.time

    if len(args) == 0:
        contentOnStdin = 1
        filenames = [stdinFilename or "<stdin>"]
    else:
        contentOnStdin = 0
        paths = []
        for arg in args:
            paths += glob.glob(arg)
        filenames = []
        for path in paths:
            if os.path.isfile(path):
                filenames.append(path)
            elif os.path.isdir(path):
                perlfiles = [os.path.join(path, n) for n in os.listdir(path)
                             if os.path.splitext(n)[1] in (".pl", ".pm")]
                perlfiles = [f for f in perlfiles if os.path.isfile(f)]
                filenames += perlfiles

    if 1:
        for filename in filenames:
            if contentOnStdin:
                log.debug("reading content from stdin")
                content = sys.stdin.read()
                log.debug("finished reading content from stdin")
                if mtime is None:
                    mtime = int(time.time())
            else:
                if mtime is None:
                    mtime = int(os.stat(filename)[stat.ST_MTIME])
                content = open(filename, 'r').read()

            if _gClockIt:
                sys.stdout.write("scanning '%s'..." % filename)
                global _gStartTime
                _gStartTime = _gClock()
            data = scan(content, filename, md5sum=md5sum, mtime=mtime, lang=lang)
            if _gClockIt:
                sys.stdout.write(" %.3fs\n" % (_gClock()-_gStartTime))
            elif data:
                sys.stdout.write(data)
    try:
        pass
    except KeyboardInterrupt:
        log.debug("user abort")
        return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))


