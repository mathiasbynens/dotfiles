/**
 * A stream is an abstract interface implemented by various objects in
 * Node. For example a request to an HTTP server is a stream, as is stdout.
 * Streams are readable, writable, or both. All streams are instances of
 * EventEmitter.
 */
var stream = {};

stream.ReadableStream = function() {}
stream.ReadableStream.prototype = {}
/**
 * Pauses the incoming 'data' events.
 */
stream.ReadableStream.prototype.pause = function() {}
/**
 * Makes the data event emit a string instead of a Buffer. encoding can be
 * 'utf8', 'ascii', or 'base64'.
 * @param encoding
 */
stream.ReadableStream.prototype.setEncoding = function(encoding) {}
/**
 * Resumes the incoming 'data' events after a pause().
 */
stream.ReadableStream.prototype.resume = function() {}
/**
 * A boolean that is true by default, but turns false after an 'error'
 * occurred, the stream came to an 'end', or destroy() was called.
 *
 * @type {Boolean}
 */
stream.ReadableStream.prototype.readable = 0;
/**
 * This is a Stream.prototype method available on all Streams.
 * @param destination
 * @param options
 */
stream.ReadableStream.prototype.pipe = function(destination, options) {}
/**
 * Closes the underlying file descriptor. Stream will not emit any more
 * events.
 */
stream.ReadableStream.prototype.destroy = function() {}
/**
 * After the write queue is drained, close the file descriptor.
 */
stream.ReadableStream.prototype.destroySoon = function() {}

stream.WritableStream = function() {}
stream.WritableStream.prototype = {}
/**
 * A boolean that is true by default, but turns false after an 'error'
 * occurred or end() / destroy() was called.
 *
 * @type {Boolean}
 */
stream.WritableStream.prototype.writable = 0;
/**
 * Same as the above except with a raw buffer.
 * @param buffer
 */
stream.WritableStream.prototype.write = function(buffer) {}
/**
 * Same as above but with a buffer.
 * @param buffer
 */
stream.WritableStream.prototype.end = function(buffer) {}
/**
 * After the write queue is drained, close the file descriptor.
 * destroySoon() can still destroy straight away, as long as there is no
 * data left in the queue for writes.
 */
stream.WritableStream.prototype.destroySoon = function() {}
/**
 * Closes the underlying file descriptor. Stream will not emit any more
 * events.
 */
stream.WritableStream.prototype.destroy = function() {}


/** @__local__ */ var __events__ = {};
/**
 * The 'data' event emits either a Buffer (by default) or a string if
 * setEncoding() was used.
 * @param data {buffer.Buffer}
 */
__events__.data = function(data) {};
/**
 * Emitted when the stream has received an EOF (FIN in TCP terminology).
 * Indicates that no more 'data' events will happen. If the stream is also
 * writable, it may be possible to continue writing.
 */
__events__.end = function() {};
/**
 * Emitted if there was an error receiving data.
 * @param exception {Error}
 */
__events__.error = function(exception) {};
/**
 * Emitted when the underlying file descriptor has been closed. Not all
 * streams will emit this. (For example, an incoming HTTP request will not
 * emit 'close'.)
 */
__events__.close = function() {};
/**
 * Emitted when a file descriptor is received on the stream. Only UNIX
 * streams support this functionality; all others will simply never emit
 * this event.
 * @param fd {Number}
 */
__events__.fd = function(fd) {};
/**
 * Emitted after a write() method was called that returned false to
 * indicate that it is safe to write again.
 */
__events__.drain = function() {};
/**
 * Emitted on error with the exception exception.
 * @param exception {Error}
 */
__events__.error = function(exception) {};
/**
 * Emitted when the underlying file descriptor has been closed.
 */
__events__.close = function() {};
/**
 * Emitted when the stream is passed to a readable stream's pipe method.
 * @param src {stream.ReadableStream}
 */
__events__.pipe = function(src) {};

                /* all streams inherit from EventEmitter */
                var events = require('events');
                stream.ReadableStream.prototype = new events.EventEmitter();
                stream.WritableStream.prototype = new events.EventEmitter();
                exports = stream;

