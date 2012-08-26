#!/usr/bin/env python
# Copyright (c) 2010 ActiveState Software Inc.
# See LICENSE.txt for license details.

"""Python binary file scanner for CodeIntel"""

import os
import sys
import cStringIO as io
import optparse

from process import ProcessOpen


SCAN_PROCESS_TIMEOUT = 2.0

class BinaryScanError(Exception): pass

class TimedPopen(ProcessOpen):
    def wait(self):
        return super(TimedPopen, self).wait(SCAN_PROCESS_TIMEOUT)


def safe_scan(path, python):
    """
    Performs a "safe" out-of-process scan.
    It is more safe because if the module being scanned runs amuck,
    it will not ruin the main Komodo interpreter.
    
        "path"   - is a path to a binary module
        "python" - an absolute path to the interpreter to run the scanner
    
    Returns a CIX 2.0 string.
    
    In case of errors raises a BinaryScanError.
    """
    # indirectly calls "_main" defined below
    
    # this is needed to avoid picking up a stale .pyc file.
    myself = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "pybinary.py")
    
    proc = TimedPopen(cmd="%s %s %s" % (python, myself, path),
                      env=dict(PYTHONPATH=os.pathsep.join(sys.path)))
    
    out, err = proc.communicate()
    if err:
        raise BinaryScanError(err)
    
    return out
    

def scan(path):
    """
    Performs an in-process binary module scan. That means the module is
    loaded (imported) into the current Python interpreter.
    
        "path" - a path to a binary module to scan
    
    Returns a CIX 2.0 XML string.
    """
    
    from gencix.python import gencixcore as gencix
    
    name,_ = os.path.splitext(os.path.basename(path))
    dir = os.path.dirname(path)

    root = gencix.Element('codeintel', version='2.0', name=name)
    
    gencix.docmodule(name, root, usefile=True, dir=dir)
    gencix.perform_smart_analysis(root)
    gencix.prettify(root)
    
    tree = gencix.ElementTree(root)
    
    stream = io.StringIO()
    try:
        stream.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        tree.write(stream)
        return stream.getvalue()
    finally:
        stream.close()
    

def _main(argv):
    parser = optparse.OptionParser(usage="%prog mdoulepath")
    (options, args) = parser.parse_args(args=argv)
    if len(args) != 1:
        parser.error("Incorrect number of args")
    
    mod_path = os.path.abspath(args[0])
    if not os.path.isfile(mod_path):
        parser.error("'%s' is not a file" % mod_path)
    
    cix = scan(mod_path)
    print cix


if __name__ == '__main__':
    _main(sys.argv[1:])

