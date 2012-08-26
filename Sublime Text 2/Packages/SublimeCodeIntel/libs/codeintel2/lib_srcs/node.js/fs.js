/**
 * File I/O is provided by simple wrappers around standard POSIX functions.
 * To use this module do require('fs'). All the methods have asynchronous
 * and synchronous forms.
 */
var fs = {};

/**
 * Asynchronous rename(2). No arguments other than a possible exception are
 * given to the completion callback.
 * @param path1
 * @param path2
 * @param callback
 */
fs.rename = function(path1, path2, callback) {}

/**
 * Synchronous version of string-based fs.write(). Returns the number of
 * bytes written.
 * @param fd
 * @param str
 * @param position
 * @param encoding='utf8'
 */
fs.writeSync = function(fd, str, position, encoding) {}

/**
 * WriteStream is a Writable Stream.
 */
fs.WriteStream = function() {}
fs.WriteStream.prototype = {}

/**
 * Synchronous chmod(2).
 * @param path
 * @param mode
 */
fs.chmodSync = function(path, mode) {}

/**
 * Objects returned from fs.stat() and fs.lstat() are of this type.
 */
fs.Stats = function() {}
fs.Stats.prototype = {}

/**
 * Asynchronous chmod(2). No arguments other than a possible exception are
 * given to the completion callback.
 * @param path
 * @param mode
 * @param callback
 */
fs.chmod = function(path, mode, callback) {}

/**
 * Synchronous readdir(3). Returns an array of filenames excluding '.' and
 * '..'.
 * @param path
 */
fs.readdirSync = function(path) {}

/**
 * Synchronous readlink(2). Returns the resolved path.
 * @param path
 */
fs.readlinkSync = function(path) {}

/**
 * Synchronous close(2).
 * @param fd
 */
fs.closeSync = function(fd) {}

/**
 * Asynchronous close(2). No arguments other than a possible exception are
 * given to the completion callback.
 * @param fd
 * @param callback
 */
fs.close = function(fd, callback) {}

/**
 * Asynchronous file open. See open(2). Flags can be 'r', 'r+', 'w', 'w+',
 * 'a', or 'a+'. mode defaults to 0666. The callback gets two arguments
 * (err, fd).
 * @param path
 * @param flags
 * @param mode
 * @param callback
 */
fs.open = function(path, flags, mode, callback) {}

/**
 * Synchronous lstat(2). Returns an instance of fs.Stats.
 * @param path
 * @returns Stats
 */
fs.lstatSync = function(path) {}

/**
 * Synchronous link(2).
 * @param srcpath
 * @param dstpath
 */
fs.linkSync = function(srcpath, dstpath) {}

/**
 * Synchronous stat(2). Returns an instance of fs.Stats.
 * @param path
 * @returns Stats
 */
fs.statSync = function(path) {}

/**
 * Asynchronous mkdir(2). No arguments other than a possible exception are
 * given to the completion callback.
 * @param path
 * @param mode
 * @param callback
 */
fs.mkdir = function(path, mode, callback) {}

/**
 * Asynchronously reads the entire contents of a file. Example:
 * @param filename
 * @param encoding
 * @param callback
 */
fs.readFile = function(filename, encoding, callback) {}

/**
 * Write buffer to the file specified by fd.
 * @param fd
 * @param buffer
 * @param offset
 * @param length
 * @param position
 * @param callback
 */
fs.write = function(fd, buffer, offset, length, position, callback) {}

/**
 * Synchronous realpath(2). Returns the resolved path.
 * @param path
 */
fs.realpathSync = function(path) {}

/**
 * Asynchronously writes data to a file, replacing the file if it already
 * exists. data can be a string or a buffer.
 * @param filename
 * @param data
 * @param encoding='utf8'
 * @param callback
 */
fs.writeFile = function(filename, data, encoding, callback) {}

/**
 * Asynchronous rmdir(2). No arguments other than a possible exception are
 * given to the completion callback.
 * @param path
 * @param callback
 */
fs.rmdir = function(path, callback) {}

/**
 * Stop watching for changes on filename.
 * @param filename
 */
fs.unwatchFile = function(filename) {}

/**
 * Asynchronous fstat(2). The callback gets two arguments (err, stats)
 * where stats is a fs.Stats object.
 * @param fd
 * @param callback
 */
fs.fstat = function(fd, callback) {}

/**
 * ReadStream is a Readable Stream.
 */
fs.ReadStream = function() {}
fs.ReadStream.prototype = {}

/**
 * Asynchronous realpath(2). The callback gets two arguments (err,
 * resolvedPath).
 * @param path
 * @param callback
 */
fs.realpath = function(path, callback) {}

/**
 * Asynchronous stat(2). The callback gets two arguments (err, stats) where
 * stats is a `fs.Stats` object. It looks like this:
 * @param path
 * @param callback
 */
fs.stat = function(path, callback) {}

/**
 * Synchronous version of string-based fs.read. Returns the number of
 * bytesRead.
 * @param fd
 * @param length
 * @param position
 * @param encoding
 */
fs.readSync = function(fd, length, position, encoding) {}

/**
 * Asynchronous ftruncate(2). No arguments other than a possible exception
 * are given to the completion callback.
 * @param fd
 * @param len
 * @param callback
 */
fs.truncate = function(fd, len, callback) {}

/**
 * Asynchronous lstat(2). The callback gets two arguments (err, stats)
 * where stats is a fs.Stats object. lstat() is identical to stat(), except
 * that if path is a symbolic link, then the link itself is stat-ed, not
 * the file that it refers to.
 * @param path
 * @param callback
 */
fs.lstat = function(path, callback) {}

/**
 * Synchronous fstat(2). Returns an instance of fs.Stats.
 * @param fd
 * @returns Stats
 */
fs.fstatSync = function(fd) {}

/**
 * The synchronous version of fs.writeFile.
 * @param filename
 * @param data
 * @param encoding='utf8'
 */
fs.writeFileSync = function(filename, data, encoding) {}

/**
 * Asynchronous symlink(2). No arguments other than a possible exception
 * are given to the completion callback.
 * @param linkdata
 * @param path
 * @param callback
 */
fs.symlink = function(linkdata, path, callback) {}

/**
 * Synchronous symlink(2).
 * @param linkdata
 * @param path
 */
fs.symlinkSync = function(linkdata, path) {}

/**
 * Synchronous rmdir(2).
 * @param path
 */
fs.rmdirSync = function(path) {}

/**
 * Asynchronous link(2). No arguments other than a possible exception are
 * given to the completion callback.
 * @param srcpath
 * @param dstpath
 * @param callback
 */
fs.link = function(srcpath, dstpath, callback) {}

/**
 * Asynchronous readdir(3). Reads the contents of a directory. The callback
 * gets two arguments (err, files) where files is an array of the names of
 * the files in the directory excluding '.' and '..'.
 * @param path
 * @param callback
 */
fs.readdir = function(path, callback) {}

/**
 * Returns a new ReadStream object (See Readable Stream).
 * @param path
 * @param options
 * @returns stream.ReadableStream
 */
fs.createReadStream = function(path, options) {}

/**
 * Synchronous version of fs.readFile. Returns the contents of the
 * filename.
 * @param filename
 * @param encoding
 */
fs.readFileSync = function(filename, encoding) {}

/**
 * Asynchronous unlink(2). No arguments other than a possible exception are
 * given to the completion callback.
 * @param path
 * @param callback
 */
fs.unlink = function(path, callback) {}

/**
 * Synchronous ftruncate(2).
 * @param fd
 * @param len
 */
fs.truncateSync = function(fd, len) {}

/**
 * Read data from the file specified by fd.
 * @param fd
 * @param buffer
 * @param offset
 * @param length
 * @param position
 * @param callback
 */
fs.read = function(fd, buffer, offset, length, position, callback) {}

/**
 * Synchronous rename(2).
 * @param path1
 * @param path2
 */
fs.renameSync = function(path1, path2) {}

/**
 * Synchronous mkdir(2).
 * @param path
 * @param mode
 */
fs.mkdirSync = function(path, mode) {}

/**
 * Watch for changes on filename. The callback listener will be called each
 * time the file is accessed.
 * @param filename
 * @param options
 * @param listener
 */
fs.watchFile = function(filename, options, listener) {}

/**
 * Returns a new WriteStream object (See Writable Stream).
 * @param path
 * @param options
 * @returns stream.WritableStream
 */
fs.createWriteStream = function(path, options) {}

/**
 * Synchronous open(2).
 * @param path
 * @param flags
 * @param mode
 */
fs.openSync = function(path, flags, mode) {}

/**
 * Asynchronous readlink(2). The callback gets two arguments (err,
 * resolvedPath).
 * @param path
 * @param callback
 */
fs.readlink = function(path, callback) {}

/**
 * Synchronous unlink(2).
 * @param path
 */
fs.unlinkSync = function(path) {}


/** @__local__ */ var __events__ = {};
/**
 * fd is the file descriptor used by the WriteStream.
 * @param fd {Number}
 */
__events__.open = function(fd) {};

                /* see http://nodejs.org/docs/v0.4.2/api/fs.html#fs.Stats */
                fs.Stats.prototype = {
                    isFile: function() {},
                    isDirectory: function() {},
                    isBlockDevice: function() {},
                    isCharacterDevice: function() {},
                    isSymbolicLink: function() {},
                    isFIFO: function() {},
                    isSocket: function() {}
                };
                /* required for createReadStream() / createWriteStream() */
                var stream = require('stream');
                exports = fs;

