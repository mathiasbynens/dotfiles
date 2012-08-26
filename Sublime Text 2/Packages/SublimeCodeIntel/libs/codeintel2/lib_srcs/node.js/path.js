/**
 * This module contains utilities for dealing with file paths. Use
 * require('path') to use it. It provides the following methods:
 */
var path = {};

/**
 * Normalize a string path, taking care of '..' and '.' parts.
 * @param p
 */
path.normalize = function(p) {}

/**
 * Resolves to to an absolute path.
 * @param from 
 * @param to
 */
path.resolve = function(from , to) {}

/**
 * Join all arguments together and normalize the resulting path.
 * @param path1
 * @param path2
 */
path.join = function(path1, path2) {}

/**
 * Test whether or not the given path exists. Then, call the callback
 * argument with either true or false. Example:
 * @param p
 * @param callback
 */
path.exists = function(p, callback) {}

/**
 * Return the last portion of a path. Similar to the Unix basename command.
 * @param p
 * @param ext
 */
path.basename = function(p, ext) {}

/**
 * Return the extension of the path. Everything after the last '.' in the
 * last portion of the path. If there is no '.' in the last portion of the
 * path or the only '.' is the first character, then it returns an empty
 * string. Examples:
 * @param p
 */
path.extname = function(p) {}

/**
 * Synchronous version of path.exists.
 * @param p
 */
path.existsSync = function(p) {}

/**
 * Return the directory name of a path. Similar to the Unix dirname
 * command.
 * @param p
 */
path.dirname = function(p) {}


exports = path;

