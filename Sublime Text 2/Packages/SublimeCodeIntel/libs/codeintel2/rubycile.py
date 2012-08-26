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
    rubycile - a Code Intelligence Language Engine for the Ruby language

    Module Usage:
        from rubycile import scan_purelang
        content = open("foo.rb", "r").read()
        scan_purelang(content, "foo.rb")
    
    Command-line Usage:
        rubycile.py [<options>...] [<Ruby files>...]

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

    One or more Ruby files can be specified as arguments or content can be
    passed in on stdin. A directory can also be specified, in which case
    all .rb files in that directory are scanned.

    This is a Language Engine for the Code Intelligence (codeintel) system.
    Code Intelligence XML format. See:
        http://specs.tl.activestate.com/kd/kd-0100.html
    
    The command-line interface will return non-zero iff the scan failed.
"""

import os
from os.path import abspath, basename, dirname, splitext, isfile, isdir, join
import sys
import getopt
import re
import logging
import glob
import time
import stat

from ciElementTree import Element, SubElement, tostring
from SilverCity import ScintillaConstants

from codeintel2 import ruby_lexer, ruby_parser, util
from codeintel2.common import CILEError
from codeintel2 import parser_cix


#---- exceptions

class RubyCILEError(CILEError):
    pass


#---- global data

_version_ = (0, 1, 0)
log = logging.getLogger("rubycile")
#log.setLevel(logging.DEBUG)

dcLog = logging.getLogger("rubycile.dircache")
#dcLog.setLevel(logging.DEBUG)

_gClockIt = 0   # if true then we are gathering timing data
_gClock = None  # if gathering timing data this is set to time retrieval fn
_gStartTime = None   # start time of current file being scanned

gProduceOldCIX = False  #XXX Temporary -- the old format should be pulled out.

# from codeintel2.util import hotshotit

class _DirInfo:
    """
    This class stats a directory to determine when files have
    been added to or removed from it.  Update times are
    platform-dependent.  For example, the Python docs state
    that on Windows update resolution on the st_mtime
    attribute is 2-seconds, but I've observed it to be closer to
    30 seconds.
    """
    def __init__(self, ptn):
        self._data = {}
        self._ptn = ptn

    def get_files(self, dirname):
        if not self._data.has_key(dirname):
            self._create(dirname)
        else:
            new_time = self._changed(dirname)
            if new_time:
                self._update(dirname, new_time)
                dcLog.debug("==> " + "\t\n".join(self._data[dirname]['flist']))
        return self._data[dirname]['flist']

    def _changed(self, dirname):
        new_time = self._mtime(dirname)
        if new_time > self._data[dirname]['mtime']:
            return new_time
        return 0

    def _create(self, dirname):
        self._data[dirname] = {'mtime' : self._mtime(dirname),
                               'flist' : self._files(dirname),
                               }

    def _files(self, dirname):
        return glob.glob(join(dirname, self._ptn))

    def _mtime(self, dirname):
        try:
            return os.stat(dirname)[stat.ST_MTIME]
        except OSError:
            return 0

    def _update(self, dirname, mtime):
        self._data[dirname]['mtime'] = mtime
        self._data[dirname]['flist'] = self._files(dirname)

_modelDirInfo = _DirInfo("*.rb")

def rails_role_from_path(path):
    apath = abspath(path)
    aplist = apath.split(os.path.sep)
    # Allow for someone to built a rails app at root...
    if len(aplist) < 3:
        return None
    elif (aplist[-3] == "app" and
        (aplist[-2] == "controllers" and aplist[-1].endswith(".rb")
         or aplist[-2] == "helpers" and aplist[-1].endswith("_helper.rb")
         or aplist[-2] == "models" and aplist[-1].endswith(".rb"))):
        role_parts = aplist[-3:]
    elif (len(aplist) >= 4
          and aplist[-4] == "app" and aplist[-3] == "views"
          and aplist[-1].endswith((".html.erb", ".rhtml"))):
        role_parts = aplist[-4:]
    elif (aplist[-3] == "db" and
          aplist[-2] == "migrate" and
          aplist[-1].endswith(".rb") and
          aplist[-1][0].isdigit()):
        role_parts = aplist[-3:]
    elif (aplist[-3] == "test" and
          aplist[-2] in ("functional", "integration", "unit") and
          aplist[-1].endswith(".rb")):
        role_parts = aplist[-3:]
    else:
        return None
    return role_parts

def check_insert_rails_env(path, blob_scope):
    role_parts = rails_role_from_path(path)
    if role_parts is None:
        return
    add_models = False
    if len(role_parts) > 1 and role_parts[0] == "app":
        if role_parts[1] == "views":
            # This stuff only works if the evaluator will load class names as well
            # as namespace names.
            blob_scope.insert(0, Element("import", symbol="ActionView::Base"))
        elif len(role_parts) > 2:
            if role_parts[1] in ("controllers", "models"):
                if role_parts[1] == "controllers":
                    if role_parts[2] != "application.rb":
                        blob_scope.insert(0, Element("import", module="./application", symbol='*'))
                    # For loading models
                    apath = abspath(path)
                    add_models = True
                    models_dir = join(dirname(dirname(apath)), "models")
                    rel_part = "../"
                    # For loading migrations
                    modelName = "*"
                else:
                    # add requires for each migration file
                    # Here's how it works:
                    # If the file is app/models/my_thing.rb,
                    # For each file foo in ../../db/migrate/*.rb,
                    # Try to load module=foo, symbol=inflector.camelcase(drop_ext(basename(filename)))
                    modelName = ruby_parser.get_inflector().camelize(splitext(basename(path))[0])
                # Load the migration modules
                apath = abspath(path)
                migration_dir = join(dirname(dirname(dirname(apath))), "db", "migrate")
                migration_files = _modelDirInfo.get_files(migration_dir)
                idx = 0
                for migration_file in migration_files:
                    idx += 1
                    base_part = "../../db/migrate/" + splitext(basename(migration_file))[0]
                    blob_class = blob_scope.find("scope")
                    assert blob_class.get('ilk') == 'class'
                    blob_class.insert(idx, Element("import", module=base_part, symbol=modelName))
    elif (len(role_parts) > 2
          and ((role_parts[0] == "db" and role_parts[1] == "migrate"
                and role_parts[2][0].isdigit())
                or role_parts[0] == "test")):
        apath = abspath(path)
        add_models = True
        models_dir = join(dirname(dirname(dirname(apath))), "app", "models")
        rel_part = "../../app/"
        if role_parts[0] == "test" and role_parts[1] == 'functional':
            # Each file functional/foo_controller_test.rb will contain a line reading
            # require 'foo'
            # but codeintel won't know where to look for this foo, so we'll tell it explicitly
            # Use 'index' to throw an exception because
            # RubyCommonBufferMixin.check_for_rails_app_path specified this pattern.
            end_part = role_parts[2].index("_test.rb")
            controller_file = rel_part + "controllers/" + role_parts[2][0:end_part]
            blob_scope.insert(0, Element("import", module=controller_file, symbol='*'))
            modelName = '*'
        #XXX - tests can't see migration dirs yet.
        #migration_dir = join(dirname(dirname(dirname(apath))), "db", "migrate")

    if add_models:
        model_files = _modelDirInfo.get_files(models_dir)
        idx = 0
        for model_file in model_files:
            idx += 1
            base_part = rel_part + "models/" + splitext(basename(model_file))[0]
            blob_scope.insert(idx, Element("import", module=base_part, symbol='*'))


# @hotshotit
def scan_purelang(content, filename):
    content = content.expandtabs(8)
    tokenizer = ruby_lexer.RubyLexer(content)
    parser = ruby_parser.Parser(tokenizer, "Ruby")
    parse_tree = parser.parse()
    tree = parser_cix.produce_elementTree_cix(parse_tree, filename,
                                              "Ruby", "Ruby")
    rails_migration_class_nodes = parser.rails_migration_class_tree()
    if rails_migration_class_nodes:
        blob_node = tree.getchildren()[0].getchildren()[0]
        for parse_tree_node in rails_migration_class_nodes:
            assert parse_tree_node.class_name == "Class"
            parser_cix.common_module_class_cix(parse_tree_node, blob_node, class_ref_fn=None, attributes="__fabricated__")
            # parser_cix.class_etree_cix(rails_migration_class_tree, blob_node)
    return tree


def scan_multilang(tokens, module_elem):
    """Build the Ruby module CIX element tree.

        "tokens" is a generator of UDL tokens for this UDL-based
            multi-lang document.
        "module_elem" is the <module> element of a CIX element tree on
            which the Ruby module should be built.

    This should return a tuple of:
    * the list of the CSL tokens in the token stream,
    * whether or not the document contains any Ruby tokens (style UDL_SSL...)
    """
        
    tokenizer = ruby_lexer.RubyMultiLangLexer(tokens)
    parser = ruby_parser.Parser(tokenizer, "RHTML")
    parse_tree = parser.parse()
    parser_cix.produce_elementTree_contents_cix(parse_tree, module_elem)
    csl_tokens = tokenizer.get_csl_tokens()
    return csl_tokens, tokenizer.has_ruby_code()


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
        log.error("Try `rubycile --help'.")
        return 1
    numVerboses = 0
    stdinFilename = None
    md5sum = None
    mtime = None
    lang = "Ruby"
    global _gClockIt
    for opt, optarg in opts:
        if opt in ("-h", "--help"):
            sys.stdout.write(__doc__)
            return
        elif opt in ("-V", "--version"):
            ver = '.'.join([str(part) for part in _version_])
            print "rubycile %s" % ver
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
            if isfile(path):
                filenames.append(path)
            elif isdir(path):
                rbfiles = [join(path, n) for n in os.listdir(path)
                           if splitext(n)[1] == ".rb"]
                rbfiles = [f for f in rbfiles if isfile(f)]
                filenames += rbfiles

    try:
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
            data = scan_purelang(content, filename)
            # data = scan(content, filename, md5sum, mtime, lang=lang)
            if _gClockIt:
                sys.stdout.write(" %.3fs\n" % (_gClock()-_gStartTime))
            elif data:
                sys.stdout.write(data)
    except KeyboardInterrupt:
        log.debug("user abort")
        return 1
    if 0: #except Exception, ex:
        log.error(str(ex))
        if log.isEnabledFor(logging.DEBUG):
            print
            import traceback
            traceback.print_exception(*sys.exc_info())
        return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))

