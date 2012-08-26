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


#TODO: docstring

import os
from os.path import join, dirname, abspath, isabs
import logging



#---- globals

log = logging.getLogger("codeintel.db")
#log.setLevel(logging.DEBUG)


#---- Resource classes
# For abstraction and canonicalization of paths.

class Resource(object):
    """A reference to a resource for the database.

    Typically this is just a path to a file on the local disk. However
    the intention is to also support remote file urls (TODO) and unsaved
    files (TODO).

    This class also provides canonicalization on comparison of resource
    paths.
    """
    
    def __init__(self, path):
        self.path = path

    @property
    def canon_path(self):
        # normalize os.altsep to os.sep? or even consider normalizing to
        # all '/'. This gets more complicated if have URL resources for
        # remote files: subclassing.
        XXX


class AreaResource(Resource):
    """A resource that is at a relative path under some area.

    For example, at 'template/Perl.pl' under 'the Komodo user data
    dir' or at 'catalog/baz.cix' under 'the codeintel2 package dir'.

    TODO: change ctor sig to AreaResource([area, ] path). More logical
    to have input be in same order as .area_path.
    """
    # The known path areas. We only have use for the one right now.
    _path_areas = {
        "ci-pkg-dir": dirname(dirname(abspath(__file__))),
    }
    _ordered_area_items = [(d,a) for a,d in _path_areas.items()]
    _ordered_area_items.sort(key=lambda i: len(i[0]), reverse=True)

    @classmethod
    def area_and_subpath_from_path(cls, path):
        #XXX Need to worry about canonicalization!
        for area_dir, area in cls._ordered_area_items:
            if (path.startswith(area_dir)
                # Ensure we are matching at a dir boundary. This implies
                # a limitation that there *is* a subpath. I'm fine with
                # that.
                and path[len(area_dir)] in (os.sep, os.altsep)):
                return area, path[len(area_dir)+1:]
        return None, path

    def __init__(self, path, area=None):
        """Create an area-relative resource.

            "path" is either the full path to the resource, or a
                relative path under the given area name. "area" must be
                specified for the latter.
            "area" (optional) can be given to specify under which area
                this resource resides. If not given, the best-fit of the
                known path areas will be used.
        """
        if area is not None:
            if area not in self._path_areas:
                raise ValueError("unknown path area: `%s'" % area)
            self.area = area
            if isabs(path):
                area_base = self._path_areas[area]
                if not path.startswith(area_base):
                    raise ValueError("cannot create AreaResource: `%s' is "
                                     "not under `%s' area (%s)" 
                                     % (path, area, area_base))
                self.subpath = path[len(area_base)+1:]
            else:
                self.subpath = path
        elif isinstance(path, tuple): # as per AreaResource.area_path
            self.area, self.subpath = path 
        else:
            self.area, self.subpath = self.area_and_subpath_from_path(path)

    def __str__(self):
        if self.area:
            return "[%s]%s%s" % (self.area, os.sep, self.subpath)
        else:
            return self.subpath

    def __repr__(self):
        return "AreaResource(%r, %r)" % (self.path, self.area)

    @property
    def area_path(self):
        return (self.area, self.subpath)

    @property
    def path(self):
        if self.area is None:
            return self.subpath
        else:
            return join(self._path_areas[self.area], self.subpath)


