/**
 * This module provides utilities for dealing with query strings. It
 * provides the following methods:
 */
var querystring = {};

/**
 * Deserialize a query string to an object. Optionally override the default
 * separator and assignment characters.
 * @param str
 * @param sep='&amp;'
 * @param eq='='
 */
querystring.parse = function(str, sep, eq) {}

/**
 * Serialize an object to a query string. Optionally override the default
 * separator and assignment characters.
 * @param obj
 * @param sep='&amp;'
 * @param eq='='
 */
querystring.stringify = function(obj, sep, eq) {}

/**
 * The unescape function used by querystring.parse, provided so that it
 * could be overridden if necessary.
 * @param str
 */
querystring.unescape = function(str) {}

/**
 * The escape function used by querystring.stringify, provided so that it
 * could be overridden if necessary.
 * @param str
 */
querystring.escape = function(str) {}


exports = querystring;

