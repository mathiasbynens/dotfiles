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

"""Ruby support for CodeIntel"""

import os
from os.path import basename, splitext, isdir, join, normcase, \
                    normpath, exists, dirname
import time
import sys
import logging
import re
from pprint import pformat
from glob import glob
import weakref

from ciElementTree import Element, SubElement, tostring
import SilverCity
from SilverCity.Lexer import Lexer
from SilverCity import ScintillaConstants
from SilverCity.ScintillaConstants import (
    SCLEX_RUBY, SCE_RB_DEFAULT, SCE_RB_COMMENTLINE,
    SCE_RB_REGEX, SCE_RB_IDENTIFIER, SCE_RB_WORD, SCE_RB_OPERATOR,
    SCE_UDL_M_OPERATOR, SCE_UDL_SSL_DEFAULT, SCE_UDL_SSL_IDENTIFIER,
    SCE_UDL_SSL_OPERATOR, SCE_UDL_SSL_VARIABLE, SCE_UDL_SSL_WORD,
    SCE_UDL_TPL_OPERATOR
)
from SilverCity.Keywords import ruby_keywords

from codeintel2.common import *
from codeintel2.citadel import (ImportHandler, CitadelBuffer, CitadelEvaluator,
                                CitadelLangIntel)
from codeintel2.citadel_common import ScanRequest
from codeintel2.indexer import PreloadLibRequest
from codeintel2.parseutil import urlencode_path
from codeintel2.udl import UDLBuffer
from codeintel2.accessor import AccessorCache
from codeintel2 import rubycile
from codeintel2.langintel import (ParenStyleCalltipIntelMixin,
                                  ProgLangTriggerIntelMixin)

from codeintel2.lang_ruby_common import RubyCommonBufferMixin
from codeintel2.util import (isident, isdigit, banner, indent, markup_text,
                             hotshotit, makePerformantLogger)
from codeintel2.tree import tree_2_0_from_tree_0_1
from codeintel2.tree_ruby import RubyTreeEvaluator

if _xpcom_:
    from xpcom.server import UnwrapObject



#---- globals

lang = "Ruby"
log = logging.getLogger("codeintel.ruby")
#log.setLevel(logging.DEBUG)
makePerformantLogger(log)

CACHING = True #XXX obsolete, kill it

_trg_type_to_trg_char = {'lib-paths': ['\'', True],
                         'lib-subpaths': ['/', True],
                         'object-methods': ['.', False],
                         'literal-methods': ['.', False],
                         'available-modules': [' ', False],
                         'available-modules-and-classes': ['<', False],
                         'module-names': [':', False],
                         'instance-vars': ['@', True],
                         'class-vars': ['@', True],
                         'global-vars': ['$', True],
                         }


#---- language support

class RubyLexer(Lexer):
    lang = "Ruby"
    def __init__(self):
        self._properties = SilverCity.PropertySet()
        self._lexer = SilverCity.find_lexer_module_by_id(SCLEX_RUBY)
        self._keyword_lists = [
            SilverCity.WordList(ruby_keywords)
        ]


#TODO: This isn't used. Drop it.
class RubyCitadelEvaluator(CitadelEvaluator):
    def __init__(self, ctlr, buf, trg, expr, line, converted_dot_new=None):
        CitadelEvaluator.__init__(self, ctlr, buf, trg, expr, line)
        self.converted_dot_new = converted_dot_new

    def post_process_calltips(self, calltips):
        if self.converted_dot_new:
            # "Foo.new(" is really using "Foo.initialize(". We swapped
            # that for calltip evaluation, now swap it back.
            for i, c in enumerate(calltips):
                if c.startswith("initialize"):
                    calltips[i] = "new" + c[len("initialize"):]
        return calltips

    def post_process_cplns(self, cplns):
        """Skip operator-typical methods like "+", "===", etc.

        XXX Should we skip methods beginning with "_" and or "__foo__"
            as well?
        """
        cplns = [c for c in cplns if isident(c[1][0])]
        cplns.sort(key=lambda c: c[1].upper())
        return cplns


class RubyImportsEvaluator(Evaluator):
    def __init__(self, ctlr, buf, trg, import_handler, prefix):
        Evaluator.__init__(self, ctlr, buf, trg)
        self.import_handler = import_handler
        self.prefix = prefix

    def __str__(self):
        return "Ruby subimports of '%s'" % self.prefix

    def eval(self, mgr):
        self.ctlr.set_desc("subimports of '%s'" % self.prefix)
        cwd = dirname(self.buf.path) #XXX Should eventually use relevant env
        #TODO:XXX Update to use the newer `find_importables_in_dir`.
        #   `findSubImportsOnDisk` is deprecated.
        subimports = self.import_handler.findSubImportsOnDisk(
            self.prefix, cwd)
        if subimports:
            cplns = []
            for subimport in subimports:
                if subimport[-1] == '/':
                    cplns.append( ("directory", subimport[:-1]) )
                else:
                    cplns.append( ("module", subimport) )
            cplns.sort(key=lambda c: c[1].upper())
            self.ctlr.set_cplns(cplns)
        self.ctlr.done("success")


class RubyBuffer(CitadelBuffer, RubyCommonBufferMixin):
    lang = "Ruby"
    sce_prefixes = ["SCE_RB_"]

    cb_show_if_empty = True

    # Characters that should automatically invoke the current completion item:
    #XXX Figure out the appropriate set (get Eric to help).
    # - Cannot be '!' or '?' or '=' (I think) because those can be part of a
    #   method name.
    # - Cannot be "'" or '"' because that can get in the way. E.g.:
    #       require 'cgi<|>
    #   At this point the selected item can be "cgi-lib". Filling up
    #   with a quote would select "cgi-lib" instead of the possibly
    #   intended "cgi".
    # - Cannot be '.' because of '..' operator for ranges. E.g.:
    #       1..1000
    #   would result in (or whatever the first Fixnum method is):
    #       1.abs.1000
    cpln_fillup_chars = "~`@#$%^&*(+}[]|\\;:,<>/ "
    cpln_stop_chars = cpln_fillup_chars + "'\"."

    def __init__(self, mgr, accessor, env=None, path=None, *args, **kwargs):
        CitadelBuffer.__init__(self, mgr, accessor, env, path, *args, **kwargs)
        self.check_for_rails_app_path(path)

        # Skip styles are a bit different for Ruby:
        # - for *some* cases autocomplete *is* automatically triggered
        #   in a string
        # - you *can* trigger on a number
        self.implicit_completion_skip_styles = dict(
            (s, True) for s in self.comment_styles())
        self.completion_skip_styles = self.implicit_completion_skip_styles.copy()
        self.completion_skip_styles[SCE_RB_REGEX] = True

    @property
    def libs(self):
        return self.langintel.libs_from_buf(self)

class _CommonStyleClassifier(object):
    def __init__(self, buf):
        self.buf = buf
        
    @property
    def ignore_styles(self):
        return self.ignoreStyles

class _RubyStyleClassifier(_CommonStyleClassifier):
    # This class delegates mostly to its Buffer object.
    # class-specific methods first...

    def is_ruby_style_at_pos(self, pos):
        # All chars are in Ruby code in pure Ruby buffers,
        # no need to get the style at position pos
        return True
    
    def is_identifier_or_word_style(self, style):
        return style == SCE_RB_IDENTIFIER or style == SCE_RB_WORD
    
    def is_identifier_style(self, style):
        return style == SCE_RB_IDENTIFIER
    
    def is_operator_style(self, style):
        return style == SCE_RB_OPERATOR

    def is_default_style(self, style):
        return style == SCE_RB_DEFAULT
    
    def __getattr__(self, name):
        return getattr(self.buf, name)

    ignoreStyles =  (SCE_RB_DEFAULT, SCE_RB_COMMENTLINE)

class _UDLStyleClassifier(_CommonStyleClassifier):
    def __init__(self, buf):
        _CommonStyleClassifier.__init__(self, buf)
        self._implicit_completion_skip_styles = None
        self._completion_skip_styles = None
    
    def is_ruby_style_at_pos(self, pos):
        style = self.buf.accessor.style_at_pos(pos)
        return SCE_UDL_SSL_DEFAULT <= style <= SCE_UDL_SSL_VARIABLE

    @property
    def implicit_completion_skip_styles(self):
        if self._implicit_completion_skip_styles is None:
            #XXX - do we have access to the language info?
            self._implicit_completion_skip_styles = {

                ScintillaConstants.SCE_UDL_SSL_COMMENT : True,
                ScintillaConstants.SCE_UDL_SSL_COMMENTBLOCK : True,
                }
        return self._implicit_completion_skip_styles

    @property
    def completion_skip_styles(self):
        if self._completion_skip_styles is None:
            self._completion_skip_styles = {

                ScintillaConstants.SCE_UDL_SSL_COMMENT : True,
                ScintillaConstants.SCE_UDL_SSL_COMMENTBLOCK : True,
                ScintillaConstants.SCE_UDL_SSL_REGEX : True,
                }
        return self._completion_skip_styles

    def is_identifier_or_word_style(self, style):
        return style == SCE_UDL_SSL_IDENTIFIER or style == SCE_UDL_SSL_WORD

    def is_identifier_style(self, style):
        return style == SCE_UDL_SSL_IDENTIFIER
    
    def is_operator_style(self, style):
        return style == SCE_UDL_SSL_OPERATOR

    # These aren't properties in buffer.py, so they can't be here either.
    def comment_styles(self):
        return (ScintillaConstants.SCE_UDL_SSL_COMMENT,)

    def number_styles(self):
        return (ScintillaConstants.SCE_UDL_SSL_NUMBER,)

    def string_styles(self):
        return (ScintillaConstants.SCE_UDL_SSL_STRING, )
    
    def is_default_style(self, style):
        return style == SCE_UDL_SSL_DEFAULT

    ignoreStyles =  (ScintillaConstants.SCE_UDL_SSL_DEFAULT,
                     ScintillaConstants.SCE_UDL_SSL_COMMENT)

class RubyLangIntel(CitadelLangIntel,
                    ParenStyleCalltipIntelMixin,
                    ProgLangTriggerIntelMixin):
    lang = "Ruby"

    calltip_region_terminators = tuple(']});\r\n')
    # newlines are for ending calltips triggered on a space

    def libs_from_buf(self, buf):
        env = buf.env

        # A buffer's libs depend on its env and the buf itself so
        # we cache it on the env and key off the buffer.
        if "ruby-buf-libs" not in env.cache:
            env.cache["ruby-buf-libs"] = weakref.WeakKeyDictionary()
        cache = env.cache["ruby-buf-libs"] # <buf-weak-ref> -> <libs>

        if buf not in cache:
            libs = self._buf_indep_libs_from_env(env)[:]

            # - curdirlib (in Ruby '.' is *last* in the import path)
            cwd = dirname(buf.path)
            if cwd != "<Unsaved>":
                libs.append( self.mgr.db.get_lang_lib("Ruby", "curdirlib", [cwd]) )

            cache[buf] = libs
        return cache[buf]

    def _ruby_from_env(self, env):
        import which
        path = [d.strip() 
                for d in env.get_envvar("PATH", "").split(os.pathsep)
                if d.strip()]
        try:
            return which.which("ruby", path=path) 
        except which.WhichError:
            return None

    def _ruby_info_from_ruby(self, ruby, env):
        """Call the given Ruby and return:
            (<version>, <lib-dir>, <site-lib-dir>, <import-dirs>, <gem-dirs>)

        TODO: Unicode path issues?
        """
        import process

        # Ruby 1.5.2 does not support sys.version_info.
        info_cmd = "puts RUBY_VERSION; puts $:"
        argv = [ruby, "-e", info_cmd]
        log.debug("run `%s -e ...'", ruby)
        p = process.ProcessOpen(argv, env=env.get_all_envvars(), stdin=None)
        stdout, stderr = p.communicate()
        stdout_lines = stdout.splitlines(0)
        retval = p.returncode
        if retval:
            log.warn("failed to determine Ruby info:\n"
                     "  path: %s\n"
                     "  retval: %s\n"
                     "  stdout:\n%s\n"
                     "  stderr:\n%s\n",
                     ruby, retval, indent('\n'.join(stdout_lines)),
                     indent(stderr))

        ruby_ver = stdout_lines[0]
        short_ver = '.'.join(ruby_ver.split('.', 2)[:2])

        prefix = dirname(dirname(ruby))
        libdir = join(prefix, "lib", "ruby", short_ver)
        sitelibdir = join(prefix, "lib", "ruby", "site_ruby")
        # Need to normpath() these because they come out, e.g.:
        #   c:/ruby184/lib/ruby/site_ruby/1.8
        # on Windows. 
        import_path = [normpath(p) for p in stdout_lines[1:]]

        # Get the list of relevant Gem lib dirs.
        def gem_ver_from_ver_str(ver_str):
            parts = ver_str.split('.')
            try:
                parts = map(int, parts)
            except ValueError:
                return ver_str
            else:
                return tuple(parts)
        gems_dir = join(prefix, "lib", "ruby", "gems", short_ver, "gems")
        gem_ver_and_dir_from_name = {
            # "actionmailer": ((1,2,5), ".../actionmailer-1.2.5"),
        }
        for dir in glob(join(gems_dir, "*-*")):
            if not isdir(dir):
                continue
            name, ver_str = basename(dir).split('-', 1)
            gem_ver = gem_ver_from_ver_str(ver_str)
            if name in gem_ver_and_dir_from_name:
                if gem_ver > gem_ver_and_dir_from_name[name][0]:
                    gem_ver_and_dir_from_name[name] = (gem_ver, dir)
            else:
                gem_ver_and_dir_from_name[name] = (gem_ver, dir)
        log.debug("ruby gem dir info: %s", pformat(gem_ver_and_dir_from_name))
        gem_lib_dirs = []
        for name, (gem_ver, dir) in sorted(gem_ver_and_dir_from_name.items()):
            gem_lib_dir = join(dir, "lib")
            if isdir(gem_lib_dir):
                gem_lib_dirs.append(gem_lib_dir)

        return ruby_ver, libdir, sitelibdir, import_path, gem_lib_dirs

    def _extra_dirs_from_env(self, env):
        extra_dirs = set()
        for pref in env.get_all_prefs("rubyExtraPaths"):
            if not pref: continue
            #TODO: need to support Gems specially?
            extra_dirs.update(d.strip() for d in pref.split(os.pathsep)
                              if exists(d.strip()))
        return tuple(extra_dirs)

    def _buf_indep_libs_from_env(self, env):
        """Create the buffer-independent list of libs."""
        cache_key = "ruby-libs"
        if cache_key not in env.cache:
            env.add_pref_observer("ruby", self._invalidate_cache)
            env.add_pref_observer("rubyExtraPaths",
                                  self._invalidate_cache_and_rescan_extra_dirs)
            env.add_pref_observer("codeintel_selected_catalogs",
                                  self._invalidate_cache)
            db = self.mgr.db

            # Gather information about the current ruby.
            ruby = None
            if env.has_pref("ruby"):
                ruby = env.get_pref("ruby").strip() or None
            if not ruby or not exists(ruby):
                ruby = self._ruby_from_env(env)
            if not ruby:
                log.warn("no Ruby was found from which to determine the "
                         "import path")
                ver, libdir, sitelibdir, import_path, gem_lib_dirs \
                    = None, None, None, [], []
            else:
                ver, libdir, sitelibdir, import_path, gem_lib_dirs \
                    = self._ruby_info_from_ruby(ruby, env)

            libs = []

            # - extradirslib
            extra_dirs = self._extra_dirs_from_env(env)
            if extra_dirs:
                log.debug("Ruby extra lib dirs: %r", extra_dirs)
                libs.append( db.get_lang_lib("Ruby", "extradirslib",
                                extra_dirs) )

            # Figure out which sys.path dirs belong to which lib.
            paths_from_libname = {"sitelib": [], "envlib": [], "stdlib": []}
            STATE = "envlib"
            canon_libdir = libdir and normcase(libdir) or None
            canon_sitelibdir = sitelibdir and normcase(sitelibdir) or None
            for dir in import_path:
                canon_dir = normcase(dir)
                if dir == ".": # -> curdirlib (handled separately)
                    continue
                #TODO: need to support gems specially?
                elif dir.startswith(sitelibdir):
                    STATE = "sitelib"
                elif dir.startswith(libdir):
                    STATE = "stdlib"
                if not exists(dir):
                    continue
                paths_from_libname[STATE].append(dir)
            log.debug("Ruby %s paths for each lib:\n%s", ver, indent(pformat(paths_from_libname)))

            # - envlib, sitelib, gemlib, cataloglib, stdlib
            if paths_from_libname["envlib"]:
                libs.append( db.get_lang_lib("Ruby", "envlib", 
                                paths_from_libname["envlib"]) )
            if paths_from_libname["sitelib"]:
                libs.append( db.get_lang_lib("Ruby", "sitelib", 
                                paths_from_libname["sitelib"]) )
            if gem_lib_dirs:
                libs.append( db.get_lang_lib("Ruby", "gemlib", gem_lib_dirs) )
            catalog_selections = env.get_pref("codeintel_selected_catalogs")
            libs += [
                db.get_catalog_lib("Ruby", catalog_selections),
                db.get_stdlib("Ruby", ver)
            ]
            env.cache[cache_key] = libs

        return env.cache[cache_key]

    def _invalidate_cache(self, env, pref_name):
        for key in ("ruby-buf-libs", "ruby-libs"):
            if key in env.cache:
                log.debug("invalidate '%s' cache on %r", key, env)
                del env.cache[key]

    def _invalidate_cache_and_rescan_extra_dirs(self, env, pref_name):
        self._invalidate_cache(env, pref_name)
        extra_dirs = self._extra_dirs_from_env(env)
        if extra_dirs:
            extradirslib = self.mgr.db.get_lang_lib(
                "Ruby", "extradirslib", extra_dirs)
            request = PreloadLibRequest(extradirslib)
            self.mgr.idxr.stage_request(request, 1.0)

    # All Ruby trigger points occur at one of these characters:
    #   '.' (period)        [eval implemented]
    #   ' ' (space)
    #   '(' (open paren)    [eval implemented]
    #   ':' (colon)         "::" actually [eval implemented]
    #   '@' (at-sign)       "@..." for instance var,
    #                       "@@..." for class vars
    #   '$' (dollar sign)
    #   "'" (single-quote)  [eval implemented]
    #   '"' (double-quote)  [eval implemented]
    #   '/' (slash)         [eval implemented]
    #
    #   At least three characters into an identifier (\w_)+
    #
    #   spaces -- for class inheritance, include, & call-tips
    #
    trg_chars = tuple('. (:@$"\'/') # the full set
    calltip_trg_chars = tuple('( ')
    RUBY_KEYWORDS = dict((k, True) for k in ruby_keywords.split())
    
    def _get_prev_token_skip_ws(self, pos, accessor, styleClassifier):       
        prev_start_pos, prev_end_pos = accessor.contiguous_style_range_from_pos(pos - 1)
        if prev_start_pos == 0 or not styleClassifier.is_ruby_style_at_pos(prev_start_pos):
            return prev_start_pos, prev_end_pos
        prev_style = accessor.style_at_pos(prev_start_pos)
        if styleClassifier.is_default_style(prev_style):
            prev_start_pos, prev_end_pos = accessor.contiguous_style_range_from_pos(prev_start_pos - 1)
        return prev_start_pos, prev_end_pos
    
    def _get_token_before_namelist(self, pos, accessor, styleClassifier, lim=-1):
        """ Walk backwards skipping (name, comma) pairs.
        If lim is given and is positive stop once we reach 0, to avoid spending
        too much time here
        """
        while True:
            prev_start_pos, prev_end_pos = self._get_prev_token_skip_ws(pos, accessor, styleClassifier)
            if prev_start_pos == 0 or not styleClassifier.is_ruby_style_at_pos(prev_start_pos):
                return 0, 0
            prev_style = accessor.style_at_pos(prev_start_pos)
            if not styleClassifier.is_identifier_or_word_style(prev_style):
                return 0, 0
            prev_start_pos, prev_end_pos = self._get_prev_token_skip_ws(prev_start_pos, accessor, styleClassifier)
            if prev_start_pos == 0 or not styleClassifier.is_ruby_style_at_pos(prev_start_pos):
                return 0, 0
            elif not styleClassifier.is_operator_style(prev_style):
                return 0, 0
            op = accessor.text_range(prev_start_pos, prev_end_pos)
            if op != ",":
                return prev_start_pos, prev_end_pos
            lim -= 1
            if lim == 0:
                return 0, 0
    
    def _is_completable_name(self, pos, accessor, styleClassifier):
        """
         Ensure we are not in another trigger zone, we do
         this by checking that the preceeding text is not
         one of "." or "::"
         Also ignore words in block var names:
         {do or "{"}, "|", {name, ","}*
        """
        if pos == 0:
            return True
        prev_start_pos, prev_end_pos = self._get_prev_token_skip_ws(pos, accessor, styleClassifier)
        if prev_start_pos == 0 or not styleClassifier.is_ruby_style_at_pos(prev_start_pos):
            return True
        prev_style = accessor.style_at_pos(prev_start_pos)
        if not styleClassifier.is_operator_style(prev_style):
            return True
        op = accessor.text_range(prev_start_pos, prev_end_pos)
        if op in (".", "::"):
            return False
        if op == ",":
            prev_start_pos, prev_end_pos = self._get_token_before_namelist(prev_start_pos,
                                                                           accessor, styleClassifier,
                                                                           lim=5)
            if prev_start_pos <= 0:
                return False
            prev_style = accessor.style_at_pos(prev_start_pos)     
            if not styleClassifier.is_operator_style(prev_style):
                return True
            op = accessor.text_range(prev_start_pos, prev_end_pos)
        if op[-1] != "|": # last character
            return True
        elif op == "{|":
            # Special case due to the way the accessor combines tokens of same style
            return False
        # Now look back for either a brace or a 'do'
        prev_start_pos, prev_end_pos = self._get_prev_token_skip_ws(prev_start_pos, accessor, styleClassifier)
        if prev_start_pos == 0 or not styleClassifier.is_ruby_style_at_pos(prev_start_pos):
            return False
        op = accessor.text_range(prev_start_pos, prev_end_pos)
        return op not in ("{", "do")


    def trg_from_pos(self, buf, pos, implicit=True, DEBUG=False):
        """If the given position is a _likely_ trigger point, return the
        trigger type. Otherwise return None.
        """
        if pos <= 0:
            return None

        styleClassifier = (isinstance(buf, UDLBuffer) and _UDLStyleClassifier
                           or _RubyStyleClassifier)(buf)
        DEBUG = False  # not using 'logging' system, because want to be fast
        if DEBUG:
            print banner("Ruby trg_from_pos(pos=%r, implicit=%r)"
                         % (pos, implicit))
    
        accessor = buf.accessor
        last_pos = pos - 1
        last_ch = accessor.char_at_pos(last_pos)
        if DEBUG:
            print "  last_pos: %s" % last_pos
            print "  last_ch: %r" % last_ch
    
        # All Ruby trigger points occur at one of the trg_chars.
        # Also some require specific two (or more) character combos that
        # we can use to filter quickly.
        if last_ch not in self.trg_chars:
            # Can we do a complete-names?
            last_style = accessor.style_at_pos(last_pos)
            if last_ch.isalnum() or last_ch == '_':
                # Gather as long as they're identifier or word chars
                MIN_LENGTH = 3
                if styleClassifier.is_identifier_or_word_style(last_style):
                    start_pos, end_pos = accessor.contiguous_style_range_from_pos(last_pos)
                    #XXX Is end_pos pointing one past the end?
                    if pos - start_pos == MIN_LENGTH or not implicit:
                        ident = accessor.text_range(start_pos, end_pos)
                        prefix = ident[:pos - start_pos]
                        if self._is_completable_name(start_pos, accessor, styleClassifier):
                            return Trigger("Ruby", TRG_FORM_CPLN,
                                           "names", 
                                           start_pos, implicit, length=0, prefix=prefix)
            if DEBUG:
                print "no: %r is not in %r"\
                      % (last_ch, self.trg_chars)
            return None
        elif last_ch == ' ':
            if last_pos <= 0:
                return None
            penultimate_ch = accessor.char_at_pos(last_pos-1)
            prev_style = accessor.style_at_pos(last_pos - 1)
            # Complex conditions, so express them this way to simplify
            if styleClassifier.is_operator_style(prev_style) and penultimate_ch == "<":
                pass
            elif styleClassifier.is_identifier_or_word_style(prev_style):
                #XXX Reject keywords
                pass
            else:
                if DEBUG:
                    print "no: %r is not '< ' or ending a word"\
                          "(i.e. 'include ')" % (penultimate_ch+last_ch)
                return None
        elif last_ch == ':' \
             and not (last_pos > 0
                      and accessor.char_at_pos(last_pos-1) == ':'):
            if DEBUG:
                penultimate_ch = (last_pos > 0 
                    and accessor.char_at_pos(last_pos-1) or '')
                print "no: %r is not '::'"\
                      % (penultimate_ch+last_ch)
            return None
    
        # Suppress triggering in some styles.
        TRIGGER_IN_STRING_CHARS = tuple('\'"/')
        last_style = accessor.style_at_pos(last_pos)
        if DEBUG:
            style_names = buf.style_names_from_style_num(last_style)
            print "  style: %s %s" % (last_style, style_names)
        suppress = False
        if implicit:
            if last_style in styleClassifier.implicit_completion_skip_styles:
                suppress = True
            elif last_style in styleClassifier.string_styles():
                if last_ch not in TRIGGER_IN_STRING_CHARS:
                    # The ', ", and / trigger chars *always* trigger in
                    # a string.
                    suppress = True
            elif last_ch in TRIGGER_IN_STRING_CHARS:
                supress = True
        elif last_style in styleClassifier.completion_skip_styles:
            # If the user requests code-completion and previous char is
            # in this style, suppress it.
            suppress = True

        if suppress:
            if DEBUG:
                print "no: completion is suppressed in style at %s: %s %s"\
                      % (last_pos, last_style, style_names)
            return None 
    
        WHITESPACE = tuple(' \t\n\r')
        EOL = tuple('\n\r')
        if last_ch == ' ':
            # This may be one of the following:
            #   class FOO < |       complete-available-modules-and-classes
            #       not implemented yet, "<" not in trg-char tuple.
            #   include |           complete-available-modules
            #   method              calltip-call-signature
            # Simplifying assumptions:
            # With whitespace allow for a completion list after '<'
            # in {class Name <}, but allow for any calltip after an identifier.
            #   (above) that the preceding char (stored in
            #   'penultimate_ch') is '<' or a word or identifier.
            # - The construct doesn't have to be on one line.
            LIMIT = 50
            text = accessor.text_range(max(0,last_pos-LIMIT), last_pos) # working text
            if DEBUG: print "  working text: %r" % text
            i = len(text)-1
            while i > 0: # Skip back to start of line.
                if text[i] in EOL: break
                i -= 1
            line = text[i:].lstrip()
            if DEBUG: print "  line: %r" % line
            if penultimate_ch == "<":
                if not line.startswith("class"): 
                    if DEBUG:
                        print "no: line does not start with 'class'"
                    return None
                if DEBUG:
                    print "complete-available-modules-and-classes"
                return Trigger("Ruby", TRG_FORM_CPLN,
                               "available-modules-and-classes", 
                               pos, implicit)
            elif line.strip() == "include":
                if DEBUG:
                    print "complete-available-modules"
                return Trigger("Ruby", TRG_FORM_CPLN, "available-modules",
                               pos, implicit)
            else: # maybe a calltip on a paren-free call
                if DEBUG:                    
                    print "calltip-call-signature"
                return Trigger("Ruby", TRG_FORM_CALLTIP, "call-signature",
                               pos, implicit)

        elif last_ch == '.':
            # This can be:
            #   FOO.|               complete-object-methods
            #   LITERAL.|           complete-literal-methods
            #   but bug62397: not for a fixnum
            # Examples:
            #   Foo.
            #   foo.
            #   @foo.
            #   ::foo.
            #   (foo + 1).    <-- We don't bother with this one for now
            #                     because CITDL processing won't resolve
            #                     the expression anyway.
            #   foo2.
            # Allow literals too:
            #   0.      3.14.
            #   1e6.    [].
            #   {}.     'foo'.      "bar".
            # Weird literals (pickaxe p319):
            #   %W{...}   # also q, Q, r, w, x, <empty> instead of 'W'
            #   0d123456, 0xff, -0b10_1010  # specific base laterals
            #   ?\M-a     # char literals 
            #   here docs
            #   symbols
            # Counter examples:
            #   foo  .          Don't allow whitespace in between.
            #                   No examples in Ruby stdlib that I can
            #                   see and more often interferes with range
            #                   operator.
            #   foo['bar'].     would need to find matching '[' and
            #                   ensure no ident char immediately
            #                   preceding (that's a heuristic)
            #   %W{foo}.        don't want to go there yet
            #
            #  def\w+CLASSNAME. Don't trigger on CLASSNAME, as we're in
            #                   a definition context, not a use one.
            if last_pos > 0:
                last_last_pos = last_pos - 1
                last_last_ch = accessor.char_at_pos(last_last_pos)
                if DEBUG:
                    print "  prev char = %r" % last_last_ch
                if last_last_ch in '"\'':
                    return Trigger("Ruby", TRG_FORM_CPLN,
                                   "literal-methods", pos, implicit,
                                   literal="String")
                elif last_last_ch == '}':
                    # Might be Hash literal:
                    #   @tk_windows = {}.<|>taint
                    # Need to rule out counter examples:
                    #   attributes.collect{|name, value| ...}.<|>to_s
                    #   FileTest.exist?("#{@filename}.<|>#{i}")
                    #   @result = Thread.new { perform_with_block }.<|>value
                    # Simplifying assumption (because too many counter
                    # examples are more common): only trigger on exactly
                    #   {}.<|>
                    if last_pos > 1 \
                       and accessor.char_at_pos(last_pos-2) == '{':
                        return Trigger("Ruby", TRG_FORM_CPLN,
                                       "literal-methods", pos, implicit,
                                       literal="Hash")
                    else: 
                        return None
                elif last_last_ch == ']':
                    # Might be Array literal:
                    #   @tk_table_list = [].<|>taint
                    #   [1,2,3].<|>
                    # Need to rule out counter examples:
                    #   @@services[host][port].stop
                    #   foo[blah].bang
                    # Algorithm: Look back on currently line for
                    # matching '['. If the char before that is a space,
                    # then consider it an Array. If can't find matching
                    # '[' on this line, then consider it an Array.
                    wrk_line = accessor.text_range(
                        accessor.line_start_pos_from_pos(last_pos),
                        last_last_pos)
                    block_count = 1
                    for ch in reversed(wrk_line):
                        if not block_count:
                            if ch in WHITESPACE or ch in '=,(':
                                return Trigger("Ruby", TRG_FORM_CPLN,
                                               "literal-methods", pos,
                                               implicit, literal="Array")
                            return None
                        if ch == '[':
                            block_count -= 1
                        elif ch == ']':
                            block_count += 1
                    else:
                        return Trigger("Ruby", TRG_FORM_CPLN,
                                       "literal-methods", pos,
                                       implicit, literal="Array")
                    return None
                elif isident(last_last_ch):
                    LIMIT = 50
                    text = accessor.text_range(max(0,last_pos-LIMIT), last_pos) # working text
                    if text.find("def") > -1:
                        # String.find fails faster than Regex.search
                        idx = max(text.rfind("\n"), text.rfind("\r"))
                        if idx > -1:
                            line = text[idx + 1:]
                        else:
                            line = text
                        if self._method_def_header.search(line):
                            if DEBUG: print "==> bailing out, defining something"
                            return None
                    return Trigger("Ruby", TRG_FORM_CPLN,
                                       "object-methods", pos, implicit)
                elif isdigit(last_last_ch):
                    # Could be a numeric literal or an ident.
                    wrk_line = accessor.text_range(
                        accessor.line_start_pos_from_pos(last_pos),
                        last_pos)
                    if DEBUG:
                        print "'<digit>.': numeric literal or identifier"
                        print "check for leading number in %r" % wrk_line
                    if self._leading_float_re.search(wrk_line):
                        return Trigger("Ruby", TRG_FORM_CPLN,
                                       "literal-methods", pos,
                                       implicit, literal="Float")
                    elif self._leading_number_re.search(wrk_line):
                        return (not implicit and
                                Trigger("Ruby", TRG_FORM_CPLN,
                                        "literal-methods", pos,
                                        implicit, literal="Fixnum")) or None
                    else:
                        return Trigger("Ruby", TRG_FORM_CPLN,
                                       "object-methods", pos, implicit)
                else:
                    return None

        elif last_ch == '(':
            # This may be:
            #   FOO(|           calltip-call-signature
            # - Want to be sure to exclude precedence parens after
            #   keywords: "if (", "while (", etc.
            # - XXX Are there instances of this trigger that we just
            #   want to drop here because of practical limitations in the
            #   Ruby codeintel handling -- as there are with Perl?
            LIMIT = 100
            text = accessor.text_range(max(0,last_pos-LIMIT), last_pos) # working text
            if DEBUG: print "  working text: %r" % text
            i = len(text)-1
            while i >= 0 and text[i] in WHITESPACE: # parse off whitespace
                i -= 1
            RUBY_SPECIAL_METHOD_END_CHARS = "?!" #XXX what about '='?
            if i >= 0 and not (isident(text[i]) or isdigit(text[i])
                               or text[i] in RUBY_SPECIAL_METHOD_END_CHARS):
                if DEBUG:
                    print "no: first non-ws char before "\
                          "trigger point is not an ident char: '%s'" % text[i]
                return None
            end = i+1
            if text[i] in RUBY_SPECIAL_METHOD_END_CHARS:
                i -= 1
            while i >= 0: # parse out the preceding identifier
                if isdigit(text[i]):
                    # might be an identifier, need to keep looking
                    pass
                elif not isident(text[i]):
                    # Identifier can be prefixed with '$', '@' or '@@'.
                    if i >= 1 and text[i-1:i+1] == "@@":
                        start = i-1
                    elif text[i] in "$@":
                        start = i
                    else:
                        start = i+1
                    identifier = text[start:end]
                    break
                i -= 1
            else:
                identifier = text[:end]
            if DEBUG: print "  identifier: %r" % identifier
            if not identifier:
                if DEBUG:
                    print "no: no identifier preceding trigger point"
                return None
            elif isdigit(identifier[0]):
                if DEBUG:
                    print "no: token preceding trigger "\
                          "point is not a legal identifier"
                return None
            if identifier in self.RUBY_KEYWORDS:
                if DEBUG:
                    print "no: no trigger on paren "\
                          "after keyword: %r" % identifier
                return None
            # Now we want to rule out subroutine definition lines, e.g.:
            #    def foo(
            #    def ClassName.foo(
            #    def self.foo(
            #    def (wacked+out).foo(
            line = text[:end].splitlines(0)[-1]
            if DEBUG:
                print "  trigger line: %r" % line
            if line.lstrip().startswith("def"):
                if DEBUG:
                    print "no: no trigger on Ruby func definition"
                return None
            if DEBUG: print "calltip-call-signature"
            return Trigger("Ruby", TRG_FORM_CALLTIP, "call-signature",
                           pos, implicit)

        elif last_ch in ('"', "'"):
            # This may be one of these:
            #   require '|              complete-lib-paths
            #   require "|              complete-lib-paths
            LIMIT = 50
            text = accessor.text_range(max(0,last_pos-LIMIT), last_pos) # working text
            if DEBUG: print "  working text: %r" % text
            i = len(text)-1
            # Parse off whitespace before quote.
            while i >= 0 and text[i] in WHITESPACE:
                i -= 1
            # Ensure that the "require" keyword immediately precedes the
            # quote.
            #XXX *Could* consider allowing preceding ';' or '#' rather
            #    than just whitespace.
            LEN_REQUIRE = 7 # len("require")
            i += 1 # point to one past "require"; simplifies indexing
            if i > LEN_REQUIRE and text[i-LEN_REQUIRE:i] == "require" \
               and text[i-1-LEN_REQUIRE] in WHITESPACE:
                pass
            elif i == LEN_REQUIRE and text[:i] == "require":
                pass
            else:
                if DEBUG:
                    print "no: quote not preceded by bare 'require'"
                return None
            if DEBUG: print "complete-lib-paths"
            return Trigger("Ruby", TRG_FORM_CPLN, "lib-paths",
                           pos, implicit)

        elif last_ch == '/':
            # This may be one of these:
            #   require 'foo/|          complete-lib-subpaths
            #   require "foo/|          complete-lib-subpaths
            # Simplifying assumption: this must all be on the same line.
            LIMIT = 75
            text = accessor.text_range(max(0,last_pos-LIMIT), last_pos) # working text
            if DEBUG: print "  working text: %r" % text
            # Get the current line.
            i = len(text)-1
            while i > 0: # Skip back to start of line.
                if text[i] in EOL: break
                elif not styleClassifier.is_ruby_style_at_pos(i):
                    # Did we get back more than one char?
                    if i < last_pos:
                        i += 1
                    break
                i -= 1
            line = text[i:].lstrip()
            if DEBUG: print "  line: %r" % line
            # Optimization: Just check that the line looks like a
            # require statement. This might miss things like:
            #       foo; require 'bar/baz'
            # but who does that? 80/20
            LEN_REQUIRE = 7 # len("require") == 7
            if not line.startswith("require") \
               or line[LEN_REQUIRE] not in WHITESPACE \
               or line[LEN_REQUIRE:].lstrip()[0] not in ("'", '"'):
                if DEBUG:
                    print "no: line doesn't start with "\
                          "/require\\s+['\"]/: <<%r>>" % line
                return None
            if DEBUG:
                print "complete-lib-subpaths"
            return Trigger("Ruby", TRG_FORM_CPLN, "lib-subpaths",
                           pos, implicit)

        elif last_ch == ':':
            # This may be:
            #   MODULE::|           complete-module-names
            # We've already checked (above) that the preceding character
            # is ':'.
            LIMIT = 50
            text = accessor.text_range(max(0,last_pos-LIMIT), last_pos) # working text
            if DEBUG: print "  working text: %r" % text
            # Just walk over the preceding token until we are pretty
            # sure it can be a variable name: there is a letter or
            # underscore in it.
            i = len(text) - 2 # len('::') == 2
            while i >= 0:
                if isident(text[i]):
                    break # good enough, could be an identifier
                elif isdigit(text[i]):
                    i -= 1 # might be an identifier, need to keep looking
                else:
                    if DEBUG:
                        print "no: '::' not preceded with "\
                              "identifier: %r" % text[i]
                    return None
            else:
                if DEBUG:
                    print "no: '::' not preceded with "\
                          "identifier: %r" % text[i]
                return None
            if DEBUG:
                print "complete-module-names"
            return Trigger("Ruby", TRG_FORM_CPLN, "module-names",
                           pos, implicit, length=2)

        elif last_ch == '@':
            # Is likely (always?) one of:
            #       @@|             complete-class-vars
            #       @|              complete-instance-vars
            if (last_pos > 0 and accessor.char_at_pos(last_pos-1) == '@'):
                if DEBUG: print "complete-class-vars"
                return Trigger("Ruby", TRG_FORM_CPLN, "class-vars",
                               pos, implicit, length=2)
            else:
                if DEBUG: print "complete-instance-vars"
                return Trigger("Ruby", TRG_FORM_CPLN, "instance-vars",
                               pos, implicit)

        elif last_ch == '$':
            # Is likely (always?) this:
            #       $|              complete-global-vars
            if DEBUG: print "complete-global-vars"
            return Trigger("Ruby", TRG_FORM_CPLN, "global-vars",
                           pos, implicit)

        return None


    # Match a Ruby number literal.
    # Limitations:
    # - 0d123456, 0xff, -0b10_1010  # specific base laterals
    _number_pat = r"""
          \d+\.\d+                  # float
        | \d+(\.\d+)?([eE][-+]?\d+)  # exp float
    """
    _leading_float_re = re.compile("(?<!\w)(%s)$" % _number_pat, re.X)
    _leading_number_re = re.compile("(?<!\w)\d+$")
    
    _method_def_header = re.compile(r'\bdef\s+\w+$')

    # Example Ruby "leading expressions":
    #   send
    #   File.open
    #   Zlib::Deflate.deflate
    #   0.step (XXX punt on numbers for now)
    #   @assigned
    #   @@foo
    #   $blah
    #   @assigned.foo
    #   @ingredients.has_key?
    #   $_  (XXX punt on the special vars for now)
    _leading_citdl_expr_pat = re.compile(r"""
        (
            (       # the set of those with @, @@, $ prefix
                (@@|@|\$)%(ident)s(\.%(ident)s)*    
            )
            |
            (       # or, the set of those without the prefix
                %(ident)s(::%(ident)s)*(\.%(ident)s)*
            )
            |       # or a literal
            (
                (?P<literal>\]|\}|\'|\"|%(number)s|(?<!\w)\d+)(?P<literal_tail>(\.%(ident)s)*)
            )
        )
        [?!]?       # methods can end with '?' or '!' (XXX what about '='?)
        \s*$        # anchored at the end of the string
        """ % {"ident": "((?!\d)\w+)", "number": _number_pat}, re.X)

    #@hotshotit
    def preceding_trg_from_pos(self, buf, pos, curr_pos, DEBUG=False):
        """ Cases where we're interested in continuing a trigger:

        Examples:
        
            GIVEN                                   TRG AT
            -----                                   ----------
        ident1.<$>iden<|>t2 ...                     .
           allow and ignore spaces after '.'
        ident1::<$>iden<|>t2 ...                    ::
           allow and ignore spaces after '::'
        class ident1 <<$> ide<|>nt2                 ' ' after "<"
           allow and ignore spaces after '<'
        require '<$>no-slash-path<|>                '
        require 'path/<$>rest<|>                    /
        <$>iden<|>                                  start of word

        pos is marked by "<$>"
        curr_pos indicated by "<|>"
        """
        
        
        styleClassifierClass = (isinstance(buf, UDLBuffer) and _UDLStyleClassifier
                                or _RubyStyleClassifier)
        preceding_trg_terminators = None
        if styleClassifierClass == _UDLStyleClassifier:
            preceding_trg_terminators = {"%" : SCE_UDL_TPL_OPERATOR}
        trg = ProgLangTriggerIntelMixin.preceding_trg_from_pos(
                self, buf, pos, curr_pos,
                preceding_trg_terminators=preceding_trg_terminators,
                DEBUG=DEBUG)
        if trg is not None:
            return trg
        if DEBUG:
            print "preceding_trg_from_pos: pos=%d, curr_pos=%d" % (pos, curr_pos)
        styleClassifier = styleClassifierClass(buf)
        # Assume we're on an identifier that doesn't follow a
        # trigger character.  Find its start.
        accessor = buf.accessor
        curr_style = accessor.style_at_pos(curr_pos - 1)
        if styleClassifier.is_identifier_or_word_style(curr_style):
            # Check for one of the following:
            # class ident1 < ide<|>
            # ide<|>
            idx = curr_pos - 2
            for char_and_style in accessor.gen_char_and_style_back(idx, 0):
                if char_and_style[1] != curr_style:
                    break
                idx -= 1
            if idx <= 0:
                if DEBUG:
                    print "Moved to beginning of buffer"
                return None
            trg = self.trg_from_pos(buf, curr_pos, implicit=False, DEBUG=DEBUG)
            return trg
        elif DEBUG:
            print "Ignore current style %d" % curr_style
    
    
    def citdl_expr_from_trg(self, buf, trg):
        """Parse out the leading Ruby expression and return a CITDL
        expression for it.
        
        We parse out the Ruby expression preceding the given position
        (typically a calltip/autocomplete trigger position), simplify the
        expression (by removing whitespace, etc.) and translate that to an
        appropriate CITDL (*) expression. Returns None if there is no
        appropriate such expression.
        
        Optimization Notes:
        - We can throw out Ruby expressions with function calls
          because CodeIntel does not currently handle return values.
        - Abort at hash and list indexing: the types of elements in these
          objects are not tracked by CodeIntel.
        - Currently we don't really make use of the styling info because we
          abort at indexing, function call arguments, etc. where recognizing
          string/number/regex boundaries would be useful. This info might be
          useful later if this algorithm is beefed up.

        Examples:
        
            GIVEN                                   CITDL EXPR
            -----                                   ----------
            send(<|>                                send
            foo.instance_of?(<|>                    foo.instance_of?
            File.open(<|>                           File.open
            Zlib::Deflate.deflate(<|>               Zlib::Deflate.deflate
            @assigned.<|>                           @assigned
            @@foo.<|>                               @foo
            $blah.<|>                               @blah
            YAML::PRIVATE_TYPES[r].call(<|>         <punt because of []>
            [$2].pack(<|>                           <punt>
            @db_class::<|>WidgetClassName           <punt: looks to be rare>
    
            0.<|>                                   Fixnum
            '...'.<|>  "...".<|>                    String
            [].step(<|>                             Array.step
            {}.step(<|>                             Hash.step

        * http://specs.tl.activestate.com/kd/kd-0100.html#citdl
        """
        DEBUG = False
        pos = trg.pos
        styleClassifier = (isinstance(buf, UDLBuffer) and _UDLStyleClassifier
                           or _RubyStyleClassifier)(buf)
        accessor = buf.accessor
        last_pos = pos - 1

        buflen = accessor.length()
        end_pos = pos
        if trg.form == TRG_FORM_DEFN:
            # Move pos forward until at the end of the current expression
            trg_length = 0
            curr_style = accessor.style_at_pos(last_pos)
            if not styleClassifier.is_identifier_style(curr_style):
                return None
            idx = pos
            while idx < buflen:
                new_style = accessor.style_at_pos(idx)
                if new_style != curr_style:
                    end_pos = idx
                    break
                idx += 1
        else:
            trg_length = trg.length
            end_pos = pos - trg_length
        wrk_text = buf.accessor.text_range(max(0, pos-100), end_pos)
        if DEBUG:
            print banner("Ruby citdl_expr_from_trg")
            if pos > 100:
                print "...",
            print (wrk_text
                   + "<+>")
            print banner(None, '-')
    
        # Parse off a Ruby leading expression.
        match = self._leading_citdl_expr_pat.search(wrk_text)
        if not match:
            if trg.type == "names" and not trg.implicit:
                citdl_expr = ""
                if DEBUG:
                    print "trigger-type of current-names: match anything"
            else:
                citdl_expr = None
                if DEBUG:
                    print "could not match a trailing Ruby var"
        elif match.group("literal"):
            literal = match.group("literal")
            literal_tail = match.group("literal_tail")
            ruby_type_from_literal = {']': "Array", '}': "Hash", 
                                      '"': "String", "'": "String"}
            if DEBUG:
                print "leading literal (part): %r (tail=%r)"\
                      % (literal, literal_tail)
            try:
                ruby_type = ruby_type_from_literal[match.group('literal')]
            except KeyError:
                if '.' in literal or 'e' in literal or 'E' in literal:
                    ruby_type = "Float"
                else:
                    ruby_type = "Fixnum"
            citdl_expr = ruby_type + literal_tail 
        else:
            citdl_expr = match.group(0)
            if DEBUG:
                print "parsed out leading Ruby citdl_expr: %r" % citdl_expr
    
        if DEBUG:
            print "returning: %r" % citdl_expr
            print banner(None, '-')
        return citdl_expr

    _require_pat = re.compile(r'(?:require|load)\s+[\'"](.*?)$')
    def async_eval_at_trg(self, buf, trg, ctlr):
        if _xpcom_:
            trg = UnwrapObject(trg)
            ctlr = UnwrapObject(ctlr)
        ctlr.start(buf, trg)

        if trg.id == ("Ruby", TRG_FORM_CALLTIP, "call-signature"): # FOO(<|>
            line = buf.accessor.line_from_pos(trg.pos)
            citdl_expr = self.citdl_expr_from_trg(buf, trg)
            if citdl_expr is None:
                return None

            # Special case for class ".new" constructor:
            # "Foo.new(" is really using "Foo.initialize(".
            if citdl_expr.endswith(".new"):
                converted_dot_new = True 
                citdl_expr = citdl_expr[:-len(".new")] + ".initialize"
            else:
                converted_dot_new = False

            evalr = RubyTreeEvaluator(ctlr, buf, trg, citdl_expr, line,
                                      converted_dot_new=converted_dot_new)
            buf.mgr.request_eval(evalr)

        elif trg.form == TRG_FORM_DEFN or \
             (trg.form == TRG_FORM_CPLN and trg.type in (
                "object-methods",                   # FOO.|
                "module-names",                     # MODULE::|
                "literal-methods",		    # LITERAL.
             )):
            line = buf.accessor.line_from_pos(trg.pos)
            citdl_expr = self.citdl_expr_from_trg(buf, trg)
            if citdl_expr is None:
                ctlr.error("couldn't determine leading expression")
                ctlr.done("error")
                return
            evalr = RubyTreeEvaluator(ctlr, buf, trg, citdl_expr, line)
            buf.mgr.request_eval(evalr)

        elif trg.form == TRG_FORM_CPLN and trg.type in (
                "lib-paths",                # require '|, require "|
                "lib-subpaths",             # require 'foo/|, require "foo/
             ):
            if trg.type == "lib-subpaths":
                accessor = buf.accessor
                line = accessor.text_range(
                    accessor.line_start_pos_from_pos(trg.pos),
                    trg.pos-trg.length)
                match = self._require_pat.search(line)
                if not match:
                    return None # not a trigger point
                require_arg = match.group(1)
            else:
                require_arg = ""

            import_handler \
                = buf.mgr.citadel.import_handler_from_lang("Ruby")
            evalr = RubyImportsEvaluator(ctlr, buf, trg, import_handler,
                                         require_arg)
            buf.mgr.request_eval(evalr)

        elif trg.form == TRG_FORM_CPLN and trg.type == "names": # FOO|
            line = buf.accessor.line_from_pos(trg.pos)
            extra = trg.extra
            citdl_expr = extra.get("prefix")
            if citdl_expr is None:
                ctlr.error("couldn't determine leading expression")
                ctlr.done("error")
                return
            evalr = RubyTreeEvaluator(ctlr, buf, trg, citdl_expr, line)
            buf.mgr.request_eval(evalr)

        elif trg.form == TRG_FORM_CPLN and trg.type in (
                "available-modules-and-classes",    # class FOO < |
                "class-vars",                       # @@|
                "instance-vars",                    # @|
                "available-modules",                # include |
                "global-vars",                      # $|
             ):
            #XXX NYI. Should disable these at trg_from_pos else will get
            #    statusbar warnings.
            return None

        else:
            raise CodeIntelError("unexpected ruby trigger: %r" % trg)


    #---- code browser integration
    cb_import_group_title = "Requires and Includes"   

    def cb_import_data_from_elem(self, elem):
        # require 'zlib' -> <import module="zlib" symbol="*"/>
        # include Comparable -> <import symbol="Comparable"/>
        module = elem.get("module")
        symbol = elem.get("symbol")
        if not module:
            name = symbol
            detail = 'include %s' % symbol
        else:
            name = module
            detail = 'require "%s"' % module
        return {"name": name, "detail": detail}

    def calltip_verify_termination(self, accessor, ch, trg_pos, curr_pos):
        """Terminate on a newline if the trigger was a space"""
        return ch not in ('\r', '\n') or accessor.char_at_pos(trg_pos - 1) == ' '

class RubyImportHandler(ImportHandler):
    PATH_ENV_VAR = "RUBYLIB"
    sep = '/'
    # Dev Notes:
    # - ruby -e "puts $:"
    # - XXX What are the implications of Ruby GEMs?

    # Try to speed up self._getPath() a little bit.
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
        argv = [compiler, "-e", "puts $:"]
        # Ruby doesn't have an option (like Python's -E) to ignore env
        # vars.
        env = dict(os.environ)
        if "RUBYLIB" in env: del env["RUBYLIB"]
        if "RUBYLIB_PREFIX" in env: del env["RUBYLIB_PREFIX"]

        p = process.ProcessOpen(argv, env=env, stdin=None)
        output, stderr = p.communicate()
        retval = p.returncode
        path = output.splitlines(0)
        if sys.platform == "win32":
            path = [p.replace('/', '\\') for p in path]
        # Handle cwd separately.
        path = [p for p in path if p not in ("", ".", os.getcwd())]
        return path

    def setCorePath(self, compiler=None, extra=None):
        if compiler is None:
            import which
            try:
                compiler = which.which("ruby")
            except which.WhichError, ex:
                self.corePath = [] # could not determine
                return
        self.corePath = self._shellOutForPath(compiler)

    def findSubImportsOnDisk(self, module, cwd):
        from os.path import isdir, join, splitext, exists

        path = self._getPath(cwd)
        if os.sep != "/":
            mrelpath = module.replace("/", os.sep)
        else:
            mrelpath = module

        subimports = {} # use a dict to get a unique list
        for p in path:
            mdir = join(p, mrelpath)
            if not exists(mdir):
                continue
            for name in os.listdir(mdir):
                fullpath = join(mdir, name)
                if fullpath in path:
                    # Don't show dirs that would just lead back to the
                    # another dir on the import path.
                    continue
                elif isdir(fullpath):
                    subimports[name+"/"] = True
                elif splitext(name)[-1] in (".rb", ".so"):
                    subimports[splitext(name)[0]] = True
        return subimports.keys()

    def _findScannableFiles(self,
                            (files, searchedDirs, skipRareImports,
                             importableOnly),
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
        #XXX Handle skipRareImports???
        scannableExts = [".rb"]
        for i in range(len(names)-1, -1, -1): # backward so can del from list
            path = os.path.join(dirname, names[i])
            if os.path.isdir(path):
                pass
            elif os.path.splitext(names[i])[1] in scannableExts:
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
            if dirname in ("", "."):
                # Do NOT traverse the common '.' element of '$:'. It is
                # environment-dependent so not useful for the typical call
                # of this method.
                continue
            files = []
            os.path.walk(dirname, self._findScannableFiles,
                         (files, searchedDirs, skipRareImports,
                          importableOnly))
            for file in files:
                yield file

    def find_importables_in_dir(self, dir):
        """See citadel.py::ImportHandler.find_importables_in_dir() for
        details.

        Importables for Ruby look like this:
            {"shell":   ("shell.rb",   None, True),
             "weakref": ("weakref.rb", None, False),
             "rdoc":    (None,         None, True)}

        Notes:
        - Drop "plat" dir (e.g., "i686-linux" on linux). Using the
          existance of "$dir/rbconfig.rb" to indicate this is a plat
          dir. Optimization: Only look in dirs with a hyphen.

        TODO: log the fs-stat'ing a la codeintel.db logging.
        TODO: consider *.so files when have a story for binary modules
              on the fly
        """
        from os.path import join, isdir, splitext, exists

        if dir == "<Unsaved>":
            #TODO: stop these getting in here.
            return {}

        try:
            names = os.listdir(dir)
        except OSError, ex:
            return {}
        dirs, nondirs = set(), set()
        for name in names:
            if isdir(join(dir, name)):
                if '-' in name and exists(join(dir, name, "rbconfig.rb")):
                    # Looks like a plat dir: skip it.
                    continue
                dirs.add(name)
            else:
                nondirs.add(name)

        importables = {}
        for name in nondirs:
            base, ext = splitext(name)
            if ext != ".rb":
                continue
            if base in dirs:
                importables[base] = (name, None, True)
                dirs.remove(base)
            else:
                importables[base] = (name, None, False)
        for name in dirs:
            importables[name] = (None, None, True)

        return importables


def _blob_scope_from_codeintel_tree(tree):
    if tree.tag == "codeintel":
        node = tree.findall("file/scope")
    # node = tree.getroot().getchildren()[0].getchildren()[0].getchildren()[0];
    return node and node[0]

class RubyCILEDriver(CILEDriver):
    lang = lang

    def scan(self, request):
        request.calculateMD5()
        return rubycile.scan(request.content, request.path,
                             request.md5sum, request.mtime)

    def scan_purelang(self, buf):
        tree = rubycile.scan_purelang(buf.accessor.text, buf.path)
        blob_scope = _blob_scope_from_codeintel_tree(tree)
        rubycile.check_insert_rails_env(buf.path, blob_scope)
        return tree

    def scan_multilang(self, buf, csl_cile_driver=None):
        """Scan the given multilang (UDL-based) buffer and return a CIX
        element tree.

            "buf" is the multi-lang Buffer instance (e.g.
                lang_rhtml.RHTMLBuffer for RHTML).
            "csl_cile_driver" (optional) is the CSL (client-side language)
                CILE driver. While scanning, CSL tokens should be gathered and,
                if any, passed to the CSL scanner like this:
                    csl_cile_driver.scan_csl_tokens(
                        file_elem, blob_name, csl_tokens)
                The CSL scanner will append a CIX <scope ilk="blob">
                element to the <file> element.
        """
        tree = Element("codeintel", version="2.0")
        path = buf.path
        if sys.platform == "win32":
            path = path.replace('\\', '/')
        file = SubElement(tree, "file", lang=buf.lang, path=path)
        module = SubElement(file, "scope", ilk="blob", lang="Ruby", 
                            name=basename(buf.path))

        #XXX When running inside Komodo we'll have to either implement
        #    SciMozAccessor.gen_tokens() or adapt rubycile to work with
        #    a SciMoz styled text stream. Whichever is easier and
        #    faster.
        csl_tokens, has_ruby_code = \
            rubycile.scan_multilang(buf.accessor.gen_tokens(), module)
        rubycile.check_insert_rails_env(path, module)

        # if the Ruby module node contains no children, remove it (bug 64897)
        if not has_ruby_code:
            assert len(module) == 0
            file.remove(module)
        
        if csl_cile_driver and csl_tokens:
            csl_cile_driver.scan_csl_tokens(file, basename(buf.path),
                                            csl_tokens)

        #XXX While still generating CIX 0.1, need to convert to CIX 2.0.
        #XXX Trent: This can all be deleted now, right?
        # tree = tree_2_0_from_tree_0_1(tree)

        return tree



#---- internal support stuff




#---- registration

def register(mgr):
    """Register language support with the Manager."""
    mgr.set_lang_info(lang,
                      silvercity_lexer=RubyLexer(),
                      buf_class=RubyBuffer,
                      langintel_class=RubyLangIntel,
                      import_handler_class=RubyImportHandler,
                      cile_driver_class=RubyCILEDriver,
                      is_cpln_lang=True)

