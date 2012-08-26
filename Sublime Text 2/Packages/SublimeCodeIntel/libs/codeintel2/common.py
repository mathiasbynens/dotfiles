#!python
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

"""Code Intelligence: common definitions"""
# Dev Notes:
# - XXX Need some good top-level logging control functions for this package.
# - XXX Rationalize exceptions.
# - XXX Coding style name changes.

__all__ = [
    "Trigger", "Definition", "CILEDriver", "Evaluator",
    "EvalController", "LogEvalController",

    "canonicalizePath", "parseAttributes", "isUnsavedPath",

    "TRG_FORM_CPLN", "TRG_FORM_CALLTIP", "TRG_FORM_DEFN",

    "PRIORITY_CONTROL", "PRIORITY_IMMEDIATE", "PRIORITY_CURRENT",
    "PRIORITY_OPEN", "PRIORITY_BACKGROUND",

    "CodeIntelDeprecationWarning",
    "CodeIntelError", "NotATriggerError", "EvalError", "EvalTimeout",
    "VirtualMethodError", "CitadelError", "NoBufferAccessorError",
    "CILEError", "CIXError", "CIDBError", "DatabaseError",
    "CorruptDatabase", "NotFoundInDatabase", "CITDLError",
    "NoModuleEntry", "NoCIDBModuleEntry",

    "ENABLE_HEURISTICS",
    "_xpcom_",
]

import os
from os.path import dirname, join, normpath, exists, basename
import sys
import re
import stat
import time
import threading
import logging
import warnings

import SilverCity
from SilverCity.Lexer import Lexer
from SilverCity import ScintillaConstants

if "CODEINTEL_NO_PYXPCOM" in os.environ:
    _xpcom_ = False
else:
    try:
        from xpcom import components
        from xpcom.server import UnwrapObject
        _xpcom_ = True
    except ImportError:
        _xpcom_ = False

#XXX Should only do this hack for non-Komodo local codeintel usage.
#XXX We need to have a better mechanism for rationalizing and sharing
#    common lexer style classes. For now we'll just HACKily grab from
#    Komodo's styles.py. Some of this is duplicating logic in
#    KoLanguageServiceBase.py.
_ko_src_dir = normpath(join(dirname(__file__), *([os.pardir]*3)))
sys.path.insert(0, join(_ko_src_dir, "schemes"))
try:
    import styles
finally:
    del sys.path[0]
    del _ko_src_dir


#---- general codeintel pragmas

# Allow the CILEs to generate type guesses based on type names (e.g.
# "event" is an Event in JS).
ENABLE_HEURISTICS = True 



#---- warnings

class CodeIntelDeprecationWarning(DeprecationWarning):
    pass
# Here is how to disable these warnings in your code:
#   import warnings
#   from codeintel2.common import CodeIntelDeprecationWarning
#   warnings.simplefilter("ignore", CodeIntelDeprecationWarning)
warnings.simplefilter("ignore", CodeIntelDeprecationWarning) # turn off for now



#---- exceptions

class CodeIntelError(Exception):
    """Base Code Intelligence system error."""
    pass
Error = CodeIntelError #XXX Remove uses of this in favour of CodeIntelError.

class NotATriggerError(CodeIntelError):
    pass
class EvalError(CodeIntelError):
    pass
class EvalTimeout(EvalError):
    pass

class VirtualMethodError(CodeIntelError):
    #TODO: pull out the method and class name from the stack for errmsg
    #      tell user what needs to be implemented
    pass

class CitadelError(CodeIntelError):
    pass

class NoBufferAccessorError(CodeIntelError):
    """The accessor has no buffer/content to access."""
    pass

class CILEError(CitadelError):
    """CILE processing error."""
    #XXX Should add some relevant data to the exception. Perhaps
    #    the request should be passed in and this c'tor can extract
    #    data it wants to keep.  This could be used to facilitate
    #    submitting bug reports on our Language Engines.
    pass


class CIXError(CitadelError):
    """Code Intelligence XML error."""
    pass

class CIDBError(CitadelError):
    """Code Intelligence Database error."""
    #TODO: Transition to DatabaseError and ensure that the change in
    #      base class doesn't cause problems.
    pass

class DatabaseError(CodeIntelError):
    pass

class CorruptDatabase(DatabaseError):
    """Corruption in some part of the database was found."""
    #XXX Should add attributes that indicate which part
    #    was corrupt and/or one of a known set of possible corrupts.
    #    Then add a Database.recover() function that could attempt
    #    to recover with that argument.
    pass

class NotFoundInDatabase(DatabaseError):
    """No data for the buffer was found in the database."""
    pass


class CITDLError(CitadelError):  #XXX Just drop in favour of CitadelError?
    """CITDL syntax error."""
    pass


class NoModuleEntry(CIDBError):
    """There is no entry for this module in the CIDB.
    
    The "module_path" second constructor argument (possibly None) is required
    to allow completion handling (which will be trapping these errors) to use
    that path to kick off a scan for it. This shouldn't be a burden as the
    import handlers that raise this will just have looked for this path.
    """
    def __init__(self, module_name, module_path):
        CIDBError.__init__(self)
        self.module_name = module_name # the module name
        self.module_path = module_path
    def __str__(self):
        path_info = ""
        if self.module_path:
            path_info = " (%s)" % os.path.basename(self.module_path)
        return "no module entry for '%s'%s in CIDB"\
               % (self.module_name, path_info)

class NoCIDBModuleEntry(CIDBError): #XXX change name to NoModuleEntryForPath
    """There is no module entry for the given path in the CIDB."""
    def __init__(self, path):
        CIDBError.__init__(self)
        self.path = path
    def __str__(self):
        return "no module entry for '%s' in CIDB"\
               % os.path.basename(self.path)



#---- globals

# Trigger forms.
TRG_FORM_CPLN, TRG_FORM_CALLTIP, TRG_FORM_DEFN = range(3)

# Priorities at which scanning requests can be scheduled.
PRIORITY_CONTROL = 0        # Special sentinal priority to control scheduler
PRIORITY_IMMEDIATE = 1      # UI is requesting info on this file now
PRIORITY_CURRENT = 2        # UI requires info on this file soon
PRIORITY_OPEN = 3           # UI will likely require info on this file soon
PRIORITY_BACKGROUND = 4     # info may be needed sometime

#TODO: these are unused, drop them
# CIDB base type constants
BT_CLASSREF, BT_INTERFACEREF = range(2)

#TODO: These are unused, drop them, the symbolType2Name below and its dead
#      usage in cb.py.
# CIDB symbol type constants
(ST_FUNCTION, ST_CLASS, ST_INTERFACE, ST_VARIABLE, ST_ARGUMENT) = range(5)
_symbolType2Name = {
    ST_FUNCTION: "function",
    ST_CLASS: "class",
    ST_INTERFACE: "interface",
    ST_VARIABLE: "variable",
    ST_ARGUMENT: "argument"
}



#---- common codeintel base classes

class Trigger(object):
    if _xpcom_:
        _com_interfaces_ = [components.interfaces.koICodeIntelTrigger]

    lang = None  # e.g. "Python", "CSS"
    form = None  # TRG_FORM_CPLN or TRG_FORM_CALLTIP
    type = None  # e.g. "object-members"
    pos = None
    implicit = None
    # The number characters of the trigger. For most (but not all) triggers
    # there is a clear distinction between a trigger token and a preceding
    # context token. For example:
    #       foo.<|>         # trigger token is '.', length = 1
    #       Foo::Bar-><|>   # trigger token is '->', length = 2
    # This default to 1.
    length = None
    retriggerOnCompletion = False

    def __init__(self, lang, form, type, pos, implicit, length=1,
                 **extra):
        self.lang = lang
        self.form = form
        self.type = type
        self.pos = pos
        self.implicit = implicit
        self.length = length
        self.extra = extra # Trigger-specific extra data, if any

    @property
    def id(self):
        return (self.lang, self.form, self.type)

    __name = None
    @property
    def name(self):
        """A more user-friendly name for this trigger, e.g.
        'python-complete-object-members'
        """
        if self.__name is None:
            form_str = {TRG_FORM_CPLN: "complete",
                        TRG_FORM_DEFN: "defn",
                        TRG_FORM_CALLTIP: "calltip"}[self.form]
            self.__name = "%s-%s-%s" % (self.lang.lower(), form_str,
                                        self.type)
        return self.__name

    def __repr__(self):
        explicit_str = (not self.implicit) and " (explicit)" or ""
        return "<Trigger '%s' at %d%s>" % (self.name, self.pos, explicit_str)

    def is_same(self, trg):
        """Return True iff the given trigger is (effectively) the same
        as this one.
        
        Dev Note: "Effective" is currently left a little fuzzy. Just
        comparing enough to fix Komodo Bug 55378.
        """
        if _xpcom_:
            trg = UnwrapObject(trg)
        if (self.pos == trg.pos
            and self.type == trg.type
            and self.form == trg.form
            and self.lang == trg.lang):
            return True
        else:
            return False


class Definition(object):
    if _xpcom_:
        _com_interfaces_ = [components.interfaces.koICodeIntelDefinition]

    lang = None        # e.g. "Python", "CSS"
    path = None        # e.g. "/usr/local/..."
    blobname = None    # e.g. "sys"
    lpath = None       # lookup tuple in blob, e.g. ["MyClass", "afunc"]
    name = None        # e.g. "path"
    line = None        # e.g. 345 (1-based)
    ilk = None         # e.g. "function"
    citdl = None       # e.g. "int"
    signature = None   # e.g. "function xyz(...)"
    doc = None         # e.g. "Xyz is just nasty stuff..."
    attributes = None  # e.g. "local private"
    returns = None     # e.g. "int"

    def __init__(self, lang, path, blobname, lpath, name, line, ilk,
                 citdl, doc, signature=None, attributes=None,
                 returns=None):
        self.lang = lang
        self.path = path
        self.blobname = blobname
        self.lpath = lpath
        self.name = name
        self.line = line
        self.ilk = ilk
        self.citdl = citdl
        self.doc = doc
        self.signature = signature
        self.attributes = attributes
        self.returns = returns

    def __repr__(self):
        if self.path is None:
            return "<Definition: %s '%s' at %s#%s>"\
                    % (self.ilk, self.name, self.blobname, self.line)
        else:
            return "<Definition: %s '%s' at %s#%s in %s>"\
                    % (self.ilk, self.name, self.blobname, self.line,
                       basename(self.path))


class CILEDriver(object):
    """Base class for all CILE drivers.
    
    CILE stands for "CodeIntel Language Engine". A CILE is the thing that
    knows how to convert content of a specific language to CIX (the XML data
    loaded into the CIDB, then used for completion, code browsers, etc.)
    
    A CILE *driver* is a class that implements this interface on top of a
    language's CILE. A CILE might be a Python module, a separate executable,
    whatever.
    """
    def __init__(self, mgr):
        self.mgr = mgr

    #DEPRECATED
    def scan(self, request):
        """Scan the given file and return data as a CIX document.

            "request" is a ScanRequest instance.

        This method MUST be re-entrant. The scheduler typically runs a pool
        of scans simultaneously so individual drivers can be called into from
        multiple threads.
        
        If the scan was successful, returns a CIX document (XML). Note: the
        return value should be unicode string, i.e. NOT an encoded byte
        string -- encoding to UTF-8 is done as necessary elsewhere.
        
        Raises a CILEError if there was a problem scanning. I.e. a driver
        should be resistant to CILE hangs and crashes.
        """
        raise VirtualMethodError("CILEDriver.scan")

    def scan_purelang(self, buf):
        """Scan the given buffer and return a CIX element tree.

            "buf" is an instance of this language's Buffer class.
        """
        raise VirtualMethodError("CILEDriver.scan_purelang")

    def scan_binary(self, buf):
        """Scan the given binary buffer and return a CIX element tree.

            "buf" is an instance of this language's BinaryBuffer clas
        """
        raise VirtualMethodError("CILEDriver.scan_binary")

    def scan_multilang(self, buf, csl_cile_driver=None):
        """Scan the given multilang (UDL-based) buffer and return a CIX
        element tree.

            "buf" is the multi-lang UDLBuffer instance (e.g.
                lang_rhtml.RHTMLBuffer for RHTML).
            "csl_cile_driver" (optional) is the CSL (client-side language)
                CILE driver. While scanning, CSL tokens should be gathered and,
                if any, passed to the CSL scanner like this:
                    csl_cile_driver.scan_csl_tokens(
                        file_elem, blob_name, csl_tokens)
                The CSL scanner will append a CIX <scope ilk="blob">
                element to the <file> element.

        A language that supports being part of a multi-lang document
        must implement this method.
        """
        raise VirtualMethodError("CILEDriver.scan_multilang")

    def scan_csl_tokens(self, file_elem, blob_name, csl_tokens):
        """Generate a CIX <scope ilk="blob"> tree for the given CSL
        (client-side language) tokens and append the blob to the given
        file element.

        A language that supports being a client-side language in a
        multi-lang document must implement this method. Realistically
        this just means JavaScript for now, but could eventually include
        Python for the new Mozilla DOM_AGNOSTIC work.
        """
        raise VirtualMethodError("CILEDriver.scan_csl_tokens")


class EvalController(object):
    """A class for interaction with an asynchronous evaluation of completions
    or calltips. Typically for "interesting" interaction on would subclass
    this and pass an instance of that class to Buffer.async_eval_at_trg().
    """
    if _xpcom_:
        _com_interfaces_ = [components.interfaces.koICodeIntelEvalController]

    def __init__(self):
        self.complete_event = threading.Event() # use a pool?
        self._done = False
        self._aborted = False
        self.buf = None
        self.trg = None
        self.cplns = None
        self.calltips = None
        self.defns = None
        self.desc = None

    def close(self):
        """Done with this eval controller, clear any references"""
        pass

    def start(self, buf, trg):
        """Called by the evaluation engine to indicate the beginning of
        evaluation and to pass in data the controller might need.
        """
        self.buf = buf
        self.trg = trg

    def set_desc(self, desc):
        self.desc = desc

    def done(self, reason):
        """Called by the evaluation engine to indicate completion handling
        has finished."""
        self.info("done eval: %s", reason)
        self._done = True
        self.buf = None
        self.trg = None
        self.complete_event.set()
    def is_done(self):
        return self._done

    def abort(self):
        """Signal to completion handling system to abort the current
        completion session.
        """
        self._aborted = True
    def is_aborted(self):
        return self._aborted

    def wait(self, timeout=None):
        """Block until this completion session is done or
        until the timeout is reached.
        """
        self.complete_event.wait(timeout)

    def debug(self, msg, *args): pass
    def info(self, msg, *args): pass
    def warn(self, msg, *args): pass
    def error(self, msg, *args): pass

    #XXX Perhaps this capturing should be in a sub-class used only for
    #    testing. Normal IDE behaviour is to fwd the data in set_*().
    def set_cplns(self, cplns):
        self.cplns = cplns
    def set_calltips(self, calltips):
        self.calltips = calltips
    def set_defns(self, defns):
        self.defns = defns


class LogEvalController(EvalController):
    def __init__(self, logger_or_log_name=None):
        if isinstance(logger_or_log_name, logging.getLoggerClass()):
            self.logger = logger_or_log_name
        else:
            self.logger = logging.getLogger(logger_or_log_name)
        EvalController.__init__(self)

    def debug(self, msg, *args):
        self.logger.debug(msg, *args)
    def info(self, msg, *args):
        self.logger.info(msg, *args)
    def warn(self, msg, *args):
        self.logger.warn(msg, *args)
    def error(self, msg, *args):
        self.logger.error(msg, *args)


class Evaluator(object):
    """To do asynchronous autocomplete/calltip evaluation you create an
    Evaluator instance (generally a specialized subclass of) and pass it
    to Manager.request_eval() and/or Manager.request_reeval().
    
    At a minimum a subclass must implement the eval() method making sure
    that the rules described for Buffer.async_eval_at_trg() are followed
    (see buffer.py). Typically this just means:
    - ensuring ctlr.done() is called,
    - reacting to ctrl.is_aborted(), and
    - optionally calling the other EvalController methods as appropriate.

    A subclass should also implement readable __str__ output.

    The manager handles:
    - co-ordinating a queue of evaluation requests
    - only ever running one evaluation at a time (because it only makes sense
      in an IDE to have one on the go)
    - calling the evaluator's eval() method in a subthread
    - calling ctlr.done(<reason>) if the eval terminates with an exception
    
    One important base class is the CitadelEvaluator (see citadel.py) that
    knows how to do CITDL evaluation using the CIDB. Citadel languages
    (e.g. Perl, Python, ...) will generally use CitadelEvaluators for most
    of their triggers.
    """
    def __init__(self, ctlr, buf, trg):
        assert isinstance(ctlr, EvalController)
        self.ctlr = ctlr
        #assert isinstance(buf, Buffer) # commented out to avoid circular dep
        self.buf = buf
        assert isinstance(trg, Trigger)
        self.trg = trg

    def eval(self):
        self.ctlr.done("eval not implemented")
        raise VirtualMethodError("Evaluator.eval")

    def close(self):
        """Done with this evaluator, clear any references"""
        if self.ctlr is not None:
            self.ctlr.close()


#---- helper methods

#TODO: drop this (see note above)
def symbolType2Name(st):
    return _symbolType2Name[st]

#TODO: drop this, see similar func in parseutil.py
def xmlattrstr(attrs):
    """Construct an XML-safe attribute string from the given attributes
    
        "attrs" is a dictionary of attributes
    
    The returned attribute string includes a leading space, if necessary,
    so it is safe to use the string right after a tag name.
    """
    #XXX Should this be using 
    from xml.sax.saxutils import quoteattr
    s = ''
    names = attrs.keys()
    names.sort() # dump attrs sorted by key, not necessary but is more stable
    for name in names:
        s += ' %s=%s' % (name, quoteattr(str(attrs[name])))
    return s


def isUnsavedPath(path):
    """Return true if the given path is a special <Unsaved>\sub\path file."""
    tag = "<Unsaved>"
    length = len(tag)
    if path.startswith(tag) and (len(path)==length or path[length] in "\\/"):
        return True
    else:
        return False

#TODO: move this utils.py
_uriMatch = re.compile("^\w+://")
def canonicalizePath(path, normcase=True):
    r"""Return what CodeIntel considers a canonical version of the given path.
    
        "path" is the path to canonicalize.
        "normcase" (optional, default True) is a boolean indicating if the
            case should be normalized.
    
    "Special" paths are ones of the form "<Tag>\sub\path". Supported special
    path tags:
        <Unsaved>       Used when the given path isn't a real file: e.g.
                        unsaved document buffers.

    Raises a ValueError if it cannot be converted to a canonical path.
    
    >>> canonicalizePath(r"C:\Python22\Lib\os.py")  # normcase on Windows
    'c:\\python22\\lib\\os.py'
    >>> canonicalizePath(r"<Unsaved>\Python-1.py")
    '<Unsaved>\\python-1.py'
    >>> canonicalizePath("<Unsaved>")
    '<Unsaved>'
    >>> canonicalizePath("<Unsaved>\\")
    '<Unsaved>'
    >>> canonicalizePath("ftp://ftp.ActiveState.com/pub")
    'ftp://ftp.ActiveState.com/pub'
    """
    if path is None:
        raise ValueError("cannot canonicalize path, path is None")
    if path.startswith('<'):  # might be a special path
        first, rest = None, None
        for i in range(1, len(path)):
            if path[i] in "\\/":
                first, rest = path[:i], path[i+1:]
                break
        else:
            first, rest = path, None
        if first.endswith('>'):
            tag = first
            subpath = rest
            if tag == "<Unsaved>":
                pass # leave tag unchanged
            else:
                raise ValueError("unknown special path tag: %s" % tag)
            cpath = tag
            if subpath:
                subpath = os.path.normpath(subpath)
                if normcase:
                    subpath = os.path.normcase(subpath)
                cpath = os.path.join(cpath, subpath)
            return cpath
    if _uriMatch.match(path): # ftp://, koremote://
        #XXX Should we normcase() a UR[LI]
        return path
    else:
        cpath = os.path.normpath(os.path.abspath(path))
        if normcase:
            cpath = os.path.normcase(cpath)
        return cpath

#TODO: move this utils.py
def parseAttributes(attrStr=None):
    """Parse the given attributes string (from CIX) into an attribute dict."""
    attrs = {}
    if attrStr is not None:
        for token in attrStr.split():
            if '=' in token:
                key, value = token.split('=', 1)
            else:
                key, value = token, 1
            attrs[key] = value
    return attrs



#---- self-test code

if __name__ == '__main__':
    def _test():
        import doctest, common
        return doctest.testmod(common)
    _test()
