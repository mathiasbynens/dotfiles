import vdebug.opts
import vdebug.log
import vim
import re
import os
import urllib
import time

class Keymapper:
    """Map and unmap key commands for the Vim user interface.
    """

    exclude = ["run","set_breakpoint","eval_visual"]

    def __init__(self):
        self._reload_keys()
        self.is_mapped = False
        self.existing = []

    def run_key(self):
        return self.keymaps['run']

    def close_key(self):
        return self.keymaps['close']

    def map(self):
        if self.is_mapped:
            return
        self._store_old_map()
        self._reload_keys()
        for func in self.keymaps:
            if func not in self.exclude:
                key = self.keymaps[func]
                map_cmd = "noremap %s%s :python debugger.%s()<cr>" %\
                    (self.leader,key,func)
                vim.command(map_cmd)
        self.is_mapped = True

    def _reload_keys(self):
        self.keymaps = vim.eval("g:vdebug_keymap")
        self.leader = vim.eval("g:vdebug_leader_key")

    def _store_old_map(self):
        vim.command('let tempfile=tempname()')
        tempfile = vim.eval("tempfile")
        vim.command('mkexrc! %s' % (tempfile))
        regex = re.compile(r'^([nvxsoilc]|)(nore)?map!?')
        split_regex = re.compile(r'\s+')
        keys = set(v for (k,v) in self.keymaps.items() if k not in self.exclude)
        special = set(["<buffer>", "<silent>", "<special>", "<script>", "<expr>", "<unique>"])
        for line in open(tempfile, 'r'):
            if not regex.match(line):
                continue
            parts = split_regex.split(line)[1:]
            for p in parts:
                if p in special:
                    continue
                elif p in keys:
                    vdebug.log.Log("Storing existing key mapping, '%s' " % line,
                                   vdebug.log.Logger.DEBUG)
                    self.existing.append(line)
                else:
                    break
        os.remove(tempfile)

    def unmap(self):
        if self.is_mapped:
            self.is_mapped = False

            for func in self.keymaps:
                key = self.keymaps[func]
                if func not in self.exclude:
                    vim.command("unmap %s%s" %(self.leader,key))
            for mapping in self.existing:
                vdebug.log.Log("Remapping key with '%s' " % mapping,\
                        vdebug.log.Logger.DEBUG)
                vim.command(mapping)

class FilePath:
    is_win = False

    """Normalizes a file name and allows for remote and local path mapping.
    """
    def __init__(self,filename):
        if filename is None or \
            len(filename) == 0:
            raise FilePathError("Missing or invalid file name")
        filename = urllib.unquote(filename)
        if filename.startswith('file:'):
            filename = filename[5:]
            if filename.startswith('///'):
                filename = filename[2:]

        p = re.compile('^/?[a-zA-Z]:')
        if p.match(filename):
            self.is_win = True
            if filename[0] == "/":
                filename = filename[1:]
            filename = filename.replace('/', '\\')

        self.local = self._create_local(filename)
        self.remote = self._create_remote(filename)

    def _create_local(self,f):
        """Create the file name as a locally valid version.

        Uses the "local_path" and "remote_path" options.
        """
        ret = f

        if vdebug.opts.Options.isset('path_maps'):
            sorted_path_maps = sorted(vdebug.opts.Options.get('path_maps', dict).iteritems(), key=lambda l: len(l[0]), reverse=True)
            for remote, local in sorted_path_maps:
                if remote in ret:
                    vdebug.log.Log("Replacing remote path (%s) " % remote +\
                            "with local path (%s)" % local ,\
                            vdebug.log.Logger.DEBUG)
                    ret = ret.replace(remote,local,1)

                    # determine remote path separator and replace by local
                    local_sep = self._findSeparator(local)
                    remote_sep = self._findSeparator(remote)
                    if local_sep and remote_sep and remote_sep != local_sep:
                        ret = ret.replace(remote_sep, local_sep)
                    break

        return ret

    def _create_remote(self,f):
        """Create the file name valid for the remote server.

        Uses the "local_path" and "remote_path" options.
        """
        ret = f

        if vdebug.opts.Options.isset('path_maps'):
            sorted_path_maps = sorted(vdebug.opts.Options.get('path_maps', dict).iteritems(), key=lambda l: len(l[0]), reverse=True)
            for remote, local in sorted_path_maps:
                if local in ret:
                    vdebug.log.Log("Replacing local path (%s) " % local +\
                            "with remote path (%s)" % remote ,\
                            vdebug.log.Logger.DEBUG)
                    ret = ret.replace(local,remote,1)
                    # replace remaining local separators with URL '/' separators
                    ret = ret.replace('\\', '/')
                    break

        if ret.startswith('/'):
            return "file://"+ret
        else:
            return "file:///"+ret

    def as_local(self,quote = False):
        if quote:
            return urllib.quote(self.local)
        else:
            return self.local

    def as_remote(self):
        return self.remote

    def _findSeparator(self, path):
        for sep in '\\/':
            if sep in path:
                return sep
        return None

    def __eq__(self,other):
        if isinstance(other,FilePath):
            if other.as_local() == self.as_local():
                return True
        return False

    def __ne__(self,other):
        if isinstance(other,FilePath):
            if other.as_local() == self.as_local():
                return False
        return True

    def __add__(self,other):
        return self.as_local() + other

    def __radd__(self,other):
        return other + self.as_local()

    def __str__(self):
        return self.as_local()

    def __repr__(self):
        return str(self)

class LocalFilePath(FilePath):
    def _create_local(self,f):
        """Create the file name as a locally valid version.

        Uses the "local_path" and "remote_path" options.
        """
        return f

class RemoteFilePath(FilePath):
    def _create_remote(self,f):
        """Create the file name valid for the remote server.

        Uses the "local_path" and "remote_path" options.
        """
        return f

class FilePathError(Exception):
    pass

class InputStream:
    """Get a character from Vim's input stream.

    Used to check for keyboard interrupts."""

    def probe(self):
        try:
            vim.eval("getchar(0)")
            time.sleep(0.1)
        except: # vim.error
            raise UserInterrupt()

class UserInterrupt(Exception):
    """Raised when a user interrupts connection wait."""
