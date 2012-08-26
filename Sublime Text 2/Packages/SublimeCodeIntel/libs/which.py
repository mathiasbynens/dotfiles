#!/usr/bin/env python
# Copyright (c) 2002-2007 ActiveState Software Inc.
# See LICENSE.txt for license details.
# Author:
#   Trent Mick (TrentM@ActiveState.com)
# Home:
#   http://trentm.com/projects/which/

r"""Find the full path to commands.

which(command, path=None, verbose=0, exts=None)
    Return the full path to the first match of the given command on the
    path.

whichall(command, path=None, verbose=0, exts=None)
    Return a list of full paths to all matches of the given command on
    the path.

whichgen(command, path=None, verbose=0, exts=None)
    Return a generator which will yield full paths to all matches of the
    given command on the path.
    
By default the PATH environment variable is searched (as well as, on
Windows, the AppPaths key in the registry), but a specific 'path' list
to search may be specified as well.  On Windows, the PATHEXT environment
variable is applied as appropriate.

If "verbose" is true then a tuple of the form
    (<fullpath>, <matched-where-description>)
is returned for each match. The latter element is a textual description
of where the match was found. For example:
    from PATH element 0
    from HKLM\SOFTWARE\...\perl.exe
"""

_cmdlnUsage = """
    Show the full path of commands.

    Usage:
        which [<options>...] [<command-name>...]

    Options:
        -h, --help      Print this help and exit.
        -V, --version   Print the version info and exit.

        -a, --all       Print *all* matching paths.
        -v, --verbose   Print out how matches were located and
                        show near misses on stderr.
        -q, --quiet     Just print out matches. I.e., do not print out
                        near misses.

        -p <altpath>, --path=<altpath>
                        An alternative path (list of directories) may
                        be specified for searching.
        -e <exts>, --exts=<exts>
                        Specify a list of extensions to consider instead
                        of the usual list (';'-separate list, Windows
                        only).

    Show the full path to the program that would be run for each given
    command name, if any. Which, like GNU's which, returns the number of
    failed arguments, or -1 when no <command-name> was given.

    Near misses include duplicates, non-regular files and (on Un*x)
    files without executable access.
"""

__revision__ = "$Id: which.py 14 2007-09-24 17:33:23Z trentm $"
__version_info__ = (1, 1, 3)
__version__ = '.'.join(map(str, __version_info__))
__all__ = ["which", "whichall", "whichgen", "WhichError"]

import os
import sys
import getopt
import stat


#---- exceptions

class WhichError(Exception):
    pass



#---- internal support stuff

def _getRegisteredExecutable(exeName):
    """Windows allow application paths to be registered in the registry."""
    registered = None
    if sys.platform.startswith('win'):
        if os.path.splitext(exeName)[1].lower() != '.exe':
            exeName += '.exe'
        import _winreg
        try:
            key = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\" +\
                  exeName
            value = _winreg.QueryValue(_winreg.HKEY_LOCAL_MACHINE, key)
            registered = (value, "from HKLM\\"+key)
        except _winreg.error:
            pass
        if registered and not os.path.exists(registered[0]):
            registered = None
    return registered

def _samefile(fname1, fname2):
    if sys.platform.startswith('win'):
        return ( os.path.normpath(os.path.normcase(fname1)) ==\
            os.path.normpath(os.path.normcase(fname2)) )
    else:
        return os.path.samefile(fname1, fname2)

def _cull(potential, matches, verbose=0):
    """Cull inappropriate matches. Possible reasons:
        - a duplicate of a previous match
        - not a disk file
        - not executable (non-Windows)
    If 'potential' is approved it is returned and added to 'matches'.
    Otherwise, None is returned.
    """
    for match in matches:  # don't yield duplicates
        if _samefile(potential[0], match[0]):
            if verbose:
                sys.stderr.write("duplicate: %s (%s)\n" % potential)
            return None
    else:
        is_darwin_app = (sys.platform == "darwin"
                         and potential[0].endswith(".app"))
        if not is_darwin_app \
           and not stat.S_ISREG(os.stat(potential[0]).st_mode):
            if verbose:
                sys.stderr.write("not a regular file: %s (%s)\n" % potential)
        elif not is_darwin_app and sys.platform != "win32" \
             and not os.access(potential[0], os.X_OK):
            if verbose:
                sys.stderr.write("no executable access: %s (%s)\n"\
                                 % potential)
        else:
            matches.append(potential)
            return potential

        
#---- module API

def whichgen(command, path=None, verbose=0, exts=None):
    """Return a generator of full paths to the given command.
    
    "command" is a the name of the executable to search for.
    "path" is an optional alternate path list to search. The default it
        to use the PATH environment variable.
    "verbose", if true, will cause a 2-tuple to be returned for each
        match. The second element is a textual description of where the
        match was found.
    "exts" optionally allows one to specify a list of extensions to use
        instead of the standard list for this system. This can
        effectively be used as an optimization to, for example, avoid
        stat's of "foo.vbs" when searching for "foo" and you know it is
        not a VisualBasic script but ".vbs" is on PATHEXT. This option
        is only supported on Windows.

    This method returns a generator which yields either full paths to
    the given command or, if verbose, tuples of the form (<path to
    command>, <where path found>).
    """
    matches = []
    if path is None:
        usingGivenPath = 0
        path = os.environ.get("PATH", "").split(os.pathsep)
        if sys.platform.startswith("win"):
            path.insert(0, os.curdir)  # implied by Windows shell
        if sys.platform == "darwin":
            path.insert(0, "/Network/Applications")
            path.insert(0, "/Applications")
    else:
        usingGivenPath = 1

    # Windows has the concept of a list of extensions (PATHEXT env var).
    if sys.platform.startswith("win"):
        if exts is None:
            exts = os.environ.get("PATHEXT", "").split(os.pathsep)
            # If '.exe' is not in exts then obviously this is Win9x and
            # or a bogus PATHEXT, then use a reasonable default.
            for ext in exts:
                if ext.lower() == ".exe":
                    break
            else:
                exts = ['.COM', '.EXE', '.BAT']
        elif not isinstance(exts, list):
            raise TypeError("'exts' argument must be a list or None")
    elif sys.platform == "darwin":
        if exts is None:
            exts = [".app"]
    else:
        if exts is not None:
            raise WhichError("'exts' argument is not supported on "\
                             "platform '%s'" % sys.platform)
        exts = []

    # File name cannot have path separators because PATH lookup does not
    # work that way.
    if os.sep in command or os.altsep and os.altsep in command:
        if os.path.exists(command):
            match = _cull((command, "explicit path given"), matches, verbose)
            if verbose:
                yield match
            else:
                yield match[0]
    else:
        for i in range(len(path)):
            dirName = path[i]
            # On windows the dirName *could* be quoted, drop the quotes
            if sys.platform.startswith("win") and len(dirName) >= 2\
               and dirName[0] == '"' and dirName[-1] == '"':
                dirName = dirName[1:-1]
            for ext in ['']+exts:
                absName = os.path.abspath(
                    os.path.normpath(os.path.join(dirName, command+ext)))
                if os.path.isfile(absName) \
                   or (sys.platform == "darwin" and absName.endswith(".app")
                       and os.path.isdir(absName)):
                    if usingGivenPath:
                        fromWhere = "from given path element %d" % i
                    elif not sys.platform.startswith("win"):
                        fromWhere = "from PATH element %d" % i
                    elif i == 0:
                        fromWhere = "from current directory"
                    else:
                        fromWhere = "from PATH element %d" % (i-1)
                    match = _cull((absName, fromWhere), matches, verbose)
                    if match:
                        if verbose:
                            yield match
                        else:
                            yield match[0]
        match = _getRegisteredExecutable(command)
        if match is not None:
            match = _cull(match, matches, verbose)
            if match:
                if verbose:
                    yield match
                else:
                    yield match[0]


def which(command, path=None, verbose=0, exts=None):
    """Return the full path to the first match of the given command on
    the path.
    
    "command" is a the name of the executable to search for.
    "path" is an optional alternate path list to search. The default it
        to use the PATH environment variable.
    "verbose", if true, will cause a 2-tuple to be returned. The second
        element is a textual description of where the match was found.
    "exts" optionally allows one to specify a list of extensions to use
        instead of the standard list for this system. This can
        effectively be used as an optimization to, for example, avoid
        stat's of "foo.vbs" when searching for "foo" and you know it is
        not a VisualBasic script but ".vbs" is on PATHEXT. This option
        is only supported on Windows.

    If no match is found for the command, a WhichError is raised.
    """
    try:
        match = whichgen(command, path, verbose, exts).next()
    except StopIteration:
        raise WhichError("Could not find '%s' on the path." % command)
    return match


def whichall(command, path=None, verbose=0, exts=None):
    """Return a list of full paths to all matches of the given command
    on the path.  

    "command" is a the name of the executable to search for.
    "path" is an optional alternate path list to search. The default it
        to use the PATH environment variable.
    "verbose", if true, will cause a 2-tuple to be returned for each
        match. The second element is a textual description of where the
        match was found.
    "exts" optionally allows one to specify a list of extensions to use
        instead of the standard list for this system. This can
        effectively be used as an optimization to, for example, avoid
        stat's of "foo.vbs" when searching for "foo" and you know it is
        not a VisualBasic script but ".vbs" is on PATHEXT. This option
        is only supported on Windows.
    """
    return list( whichgen(command, path, verbose, exts) )



#---- mainline

def main(argv):
    all = 0
    verbose = 0
    altpath = None
    exts = None
    try:
        optlist, args = getopt.getopt(argv[1:], 'haVvqp:e:',
            ['help', 'all', 'version', 'verbose', 'quiet', 'path=', 'exts='])
    except getopt.GetoptError, msg:
        sys.stderr.write("which: error: %s. Your invocation was: %s\n"\
                         % (msg, argv))
        sys.stderr.write("Try 'which --help'.\n")
        return 1
    for opt, optarg in optlist:
        if opt in ('-h', '--help'):
            print _cmdlnUsage
            return 0
        elif opt in ('-V', '--version'):
            print "which %s" % __version__
            return 0
        elif opt in ('-a', '--all'):
            all = 1
        elif opt in ('-v', '--verbose'):
            verbose = 1
        elif opt in ('-q', '--quiet'):
            verbose = 0
        elif opt in ('-p', '--path'):
            if optarg:
                altpath = optarg.split(os.pathsep)
            else:
                altpath = []
        elif opt in ('-e', '--exts'):
            if optarg:
                exts = optarg.split(os.pathsep)
            else:
                exts = []

    if len(args) == 0:
        return -1

    failures = 0
    for arg in args:
        #print "debug: search for %r" % arg
        nmatches = 0
        for match in whichgen(arg, path=altpath, verbose=verbose, exts=exts):
            if verbose:
                print "%s (%s)" % match
            else:
                print match
            nmatches += 1
            if not all:
                break
        if not nmatches:
            failures += 1
    return failures


if __name__ == "__main__":
    sys.exit( main(sys.argv) )


