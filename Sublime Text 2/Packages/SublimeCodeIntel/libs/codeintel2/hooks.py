#!/usr/bin/env python
# Copyright (c) 2006-2008 ActiveState Software Inc.
# See LICENSE.txt for license details.

"""Parts of the codeintel system may provide hooks for customization
by external modules. Implementing a hook is done by adding a
`CodeIntelHookHandler` instance with the manager, like this:

    ---- codeintel_foo.py ----
    # My codeintel 'foo' hook.
    
    from codeintel2.hooks import HookHandler
    
    class FooHookHandler(HookHandler):
        name = "foo"
        langs = ["Python"]  # only hook into handling for Python code

        # Add implementation of one or more hooks (see below)...
    
    def register(mgr):
        # This will be called by the Manager on startup.
        mgr.add_hook_handler(FooHookHandler(mgr))
    --------------------------
"""

from pprint import pformat

from codeintel2.common import *


class HookHandler(object):
    """Virtual base class for all hook handlers."""
    name = None     # sub-classes must define a meaningful name (a string)

    # Sub-classes must define the list of language names they operate
    # on. E.g.,
    #   langs = ["Perl"]
    #   langs = ["HTML", "XML"]
    #   langs = ["*"]   # Means operate on all languages. Use sparingly!
    langs = None
    
    def __init__(self, mgr):
        self.mgr = mgr

    # Hook: `post_db_load_blob(blob)'
    #
    # Called just after a blob is loaded from the the codeintel database.
    # Note that this hook is not currently called for blobs from API
    # Catalogs or in language stdlibs.
    #
    # A "blob" is a ciElementTree (a slight tweak to an ElementTree
    # object) representing the scan info for code of a single language
    # in a single file.
    #
    # The hook-handler may modify (in-place) or just look at the blob.
    # The resulting changes to the blob, if any, are NOT saved to the
    # database.
    # Potential uses for this hook might be to add implicit state to
    # a file for a certain framework, e.g. adding context info to a
    # Django template, adding implicit imports to a PHP Zend Framework
    # controller file.
    def post_db_load_blob(self, blob):
        pass


