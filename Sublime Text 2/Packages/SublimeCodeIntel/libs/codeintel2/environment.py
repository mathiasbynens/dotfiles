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

"""Runtime environment handling for codeintel

"Environment" here means more than just the environment variables (i.e.
os.environ). It also means preferences/settings/conditions that are part
of the running environment for a codeintel Manager or Buffer.

Generally the relevant environment is used to get data such environment
variables and preferences (e.g., what Python interpreter is relevant,
what level of JS DOM APIs should be considered).

The Manager has an 'env' attribute (by default, an Environment instance)
and, optionally, a buffer can have a custom environment (also the 'env'
attribute). The latter is useful for sharing a project environment
across all buffers part of the same project.

For example, Buffers created for files in Komodo currently have a
KoCodeIntelEnvironment instance. All buffers belonging to the same project
share a single such instance that incorporates project settings. Buffers
not part of a project share a default instance that just uses global
Komodo settings.

Read the base Environment class for details on the API.
"""

import os
import logging


log = logging.getLogger("codeintel.environment")
#log.setLevel(logging.DEBUG)



class Environment(object):
    """The base Environment class. It defines the API that all types
    of "environments" in codeintel must implement and provides a base
    implementation that:
    - has no prefs
    - maps envvars to os.environ, and
    - has some basic file associations for 'assoc_patterns_from_lang()'.

    Every environment must have a 'cache' attribute that is a wide open
    dictionary. Various parts of the codeintel system can (and do) use
    this cache for maintain runtime calculated date.
    """
    def __init__(self):
        self.cache = {}
    def __repr__(self):
        return "<Environment>"

    def has_envvar(self, name):
        """Return True if the named envvar exists."""
        return name in os.environ
    def get_envvar(self, name, default=None):
        """Return the value of the named envvar, if it exists. Otherwise
        return the given default, if any, or None.
        """
        return os.environ.get(name, default)
    def get_all_envvars(self):
        """Return a dictionary of all environment variables."""
        return dict(os.environ)

    def has_pref(self, name):
        """Return True if the named pref exists."""
        return False
    def get_pref(self, name, default=None):
        """Return the value of the named pref, if it exists. Otherwise
        return the given default, if any, or None.
        """
        return default
    def get_all_prefs(self, name, default=None):
        """Return a list with the value of the named pref at each
        "pref-level". If not defined at a particular level the 'default'
        value will be placed at that index.
        
        Note: This was added to support Komodo's multi-level pref system.
        Most simple Environment classes only support one level.
        """
        return [self.get_pref(name, default)]
    def add_pref_observer(self, name, callback):
        pass
    def remove_pref_observer(self, name, callback):
        pass
    def remove_all_pref_observers(self):
        pass

    _default_assoc_patterns_from_lang = {
        "Python": ["*.py"],
        "Python3": ["*.py"],
        "JavaScript": ["*.js"],
        "PHP": ["*.php", "*.inc", "*.module"],
        "Perl": ["*.pm", "*.pl"],
        "Tcl": ["*.tcl"],
        "Ruby": ["*.rb"],
    }
    def assoc_patterns_from_lang(self, lang):
        """Return a list of filename patterns identifying the given
        language. Returns the empty list if don't have any info for that
        lang.
        """
        return self._default_assoc_patterns_from_lang.get(lang, [])

    def get_proj_base_dir(self):
        """Return the full path to the project base dir, or None if this
        environment does not represent a project.
        """
        return None


class SimplePrefsEnvironment(Environment):
    """A simple environment that supports basic key/value prefs and
    pref change observation.

    Whenever a pref changes, any registered callbacks for that pref name
    will be called as follows:
        callback(<env>, <pref-name>)

    Note: There is no support for *deleting* a pref. Just set it to
    None.  The reason for not supporting this is that it would require
    complicating pref observer notification to be able to distinguish
    setting pref to None and deleting it.
    """
    def __init__(self, **prefs):
        Environment.__init__(self)
        self._prefs = prefs
        self._pref_observer_callbacks_from_name = {}
    
    def set_pref(self, name, value):
        self._prefs[name] = value
        self._notify_pref_observers(name)
    def has_pref(self, name):
        return name in self._prefs
    def get_pref(self, name, default=None):
        if name not in self._prefs:
            return default
        return self._prefs[name]
    def get_all_prefs(self, name, default=None):
        return [self.get_pref(name, default)]

    #TODO: Add ability to be able to call add_pref_observer() without
    #      having to worry if have already done so for this name.
    def add_pref_observer(self, name, callback):
        if name not in self._pref_observer_callbacks_from_name:
            self._pref_observer_callbacks_from_name[name] = []
        self._pref_observer_callbacks_from_name[name].append(callback)
    def remove_pref_observer(self, name, callback):
        self._pref_observer_callbacks_from_name[name].remove(callback)
    def remove_all_pref_observers(self):
        self._pref_observer_callbacks_from_name = {}
    def _notify_pref_observers(self, name):
        for callback in self._pref_observer_callbacks_from_name.get(name, []):
            try:
                callback(self, name)
            except:
                log.exception("error in pref observer for pref '%s' change",
                              name)


class DefaultEnvironment(SimplePrefsEnvironment):
    """The default environment used by the Manager if no environment is
    provided.
    """
    _default_prefs = {
        "codeintel_selected_catalogs": ["pywin32"],
        "codeintel_max_recursive_dir_depth": 10,
    }

    def __init__(self):
        SimplePrefsEnvironment.__init__(self, **self._default_prefs)


