/**
 * To use the HTTP server and client one must require('http').
 */
var http = {};

/**
 * Since most requests are GET requests without bodies, Node provides this
 * convenience method. The only difference between this method and
 * http.request() is that it sets the method to GET and calls req.end()
 * automatically.
 * @param options
 * @param callback
 * @returns http.ClientRequest
 */
http.get = function(options, callback) {}

/**
 * This object is created internally by a HTTP server -- not by the user --
 * and passed as the first argument to a 'request' listener.
 */
http.ServerRequest = function() {}
http.ServerRequest.prototype = {}
/**
 * Pauses request from emitting events. Useful to throttle back an upload.
 */
http.ServerRequest.prototype.pause = function() {}
/**
 * Set the encoding for the request body. Either 'utf8' or 'binary'.
 * Defaults to null, which means that the 'data' event will emit a Buffer
 * object..
 * @param encoding=null
 */
http.ServerRequest.prototype.setEncoding = function(encoding) {}
/**
 * Resumes a paused request.
 */
http.ServerRequest.prototype.resume = function() {}
/**
 * Request URL string. This contains only the URL that is present in the
 * actual HTTP request. If the request is:
 */
http.ServerRequest.prototype.url = 0;
/**
 * Read only; HTTP trailers (if present). Only populated after the 'end'
 * event.
 */
http.ServerRequest.prototype.trailers = 0;
/**
 * Read only.
 */
http.ServerRequest.prototype.headers = 0;
/**
 * The net.Stream object associated with the connection.
 */
http.ServerRequest.prototype.connection = 0;
/**
 * The request method as a string. Read only. Example: 'GET', 'DELETE'.
 */
http.ServerRequest.prototype.method = 0;
/**
 * The HTTP protocol version as a string. Read only. Examples: '1.1',
 * '1.0'. Also request.httpVersionMajor is the first integer and
 * request.httpVersionMinor is the second.
 */
http.ServerRequest.prototype.httpVersion = 0;

/**
 * This object is created when making a request with http.request(). It is
 * passed to the 'response' event of the request object.
 */
http.ClientResponse = function() {}
http.ClientResponse.prototype = {}
/**
 * Pauses response from emitting events. Useful to throttle back a
 * download.
 */
http.ClientResponse.prototype.pause = function() {}
/**
 * Set the encoding for the response body. Either 'utf8', 'ascii', or
 * 'base64'. Defaults to null, which means that the 'data' event will emit
 * a Buffer object..
 * @param encoding=null
 */
http.ClientResponse.prototype.setEncoding = function(encoding) {}
/**
 * Resumes a paused response.
 */
http.ClientResponse.prototype.resume = function() {}
/**
 * The response trailers object. Only populated after the 'end' event.
 */
http.ClientResponse.prototype.trailers = 0;
/**
 * The response headers object.
 */
http.ClientResponse.prototype.headers = 0;
/**
 * The 3-digit HTTP response status code. E.G. 404.
 */
http.ClientResponse.prototype.statusCode = 0;
/**
 * The HTTP version of the connected-to server. Probably either '1.1' or
 * '1.0'. Also response.httpVersionMajor is the first integer and
 * response.httpVersionMinor is the second.
 */
http.ClientResponse.prototype.httpVersion = 0;

/**
 * Node maintains several connections per server to make HTTP requests.
 * This function allows one to transparently issue requests.
 * @param options
 * @param callback
 * @returns http.ClientRequest
 */
http.request = function(options, callback) {}

http.Agent = function() {}
http.Agent.prototype = {}
/**
 * A queue of requests waiting to be sent to sockets.
 */
http.Agent.prototype.queue = 0;
/**
 * An array of sockets currently in use by the Agent. Do not modify.
 */
http.Agent.prototype.sockets = 0;
/**
 * By default set to 5. Determines how many concurrent sockets the agent
 * can have open.
 */
http.Agent.prototype.maxSockets = 0;

/**
 * This is an EventEmitter with the following events:
 */
http.Server = function() {}
http.Server.prototype = {}
/**
 * Stops the server from accepting new connections.
 */
http.Server.prototype.close = function() {}
/**
 * Start a UNIX socket server listening for connections on the given path.
 * @param path
 * @param callback
 */
http.Server.prototype.listen = function(path, callback) {}

/**
 * Returns a new web server object.
 * @param requestListener {__events__.request}
 * @returns http.Server
 */
http.createServer = function(requestListener) {}

/**
 * This object is created internally by a HTTP server--not by the user. It
 * is passed as the second parameter to the 'request' event. It is a
 * Writable Stream.
 */
http.ServerResponse = function() {}
http.ServerResponse.prototype = {}
/**
 * Removes a header that's queued for implicit sending.
 * @param name
 */
http.ServerResponse.prototype.removeHeader = function(name) {}
/**
 * This method signals to the server that all of the response headers and
 * body has been sent; that server should consider this message complete.
 * The method, response.end(), MUST be called on each response.
 * @param data
 * @param encoding
 */
http.ServerResponse.prototype.end = function(data, encoding) {}
/**
 * Reads out a header that's already been queued but not sent to the
 * client. Note that the name is case insensitive. This can only be called
 * before headers get implicitly flushed.
 * @param name
 */
http.ServerResponse.prototype.getHeader = function(name) {}
/**
 * Sends a response header to the request. The status code is a 3-digit
 * HTTP status code, like 404. The last argument, headers, are the response
 * headers. Optionally one can give a human-readable reasonPhrase as the
 * second argument.
 * @param statusCode
 * @param reasonPhrase
 * @param headers
 */
http.ServerResponse.prototype.writeHead = function(statusCode, reasonPhrase, headers) {}
/**
 * If this method is called and response.writeHead() has not been called,
 * it will switch to implicit header mode and flush the implicit headers.
 * @param chunk
 * @param encoding='utf8'
 */
http.ServerResponse.prototype.write = function(chunk, encoding) {}
/**
 * Sends a HTTP/1.1 100 Continue message to the client, indicating that the
 * request body should be sent. See the checkContinue event on Server.
 */
http.ServerResponse.prototype.writeContinue = function() {}
/**
 * This method adds HTTP trailing headers (a header but at the end of the
 * message) to the response.
 * @param headers
 */
http.ServerResponse.prototype.addTrailers = function(headers) {}
/**
 * Sets a single header value for implicit headers. If this header already
 * exists in the to-be-sent headers, it's value will be replaced. Use an
 * array of strings here if you need to send multiple headers with the same
 * name.
 * @param name
 * @param value
 */
http.ServerResponse.prototype.setHeader = function(name, value) {}
/**
 * When using implicit headers (not calling response.writeHead()
 * explicitly), this property controls the status code that will be send to
 * the client when the headers get flushed.
 */
http.ServerResponse.prototype.statusCode = 0;

/**
 * This object is created internally and returned from http.request(). It
 * represents an in-progress request whose header has already been queued.
 * The header is still mutable using the setHeader(name, value),
 * getHeader(name), removeHeader(name) API. The actual header will be sent
 * along with the first data chunk or when closing the connection.
 */
http.ClientRequest = function() {}
http.ClientRequest.prototype = {}
/**
 * Sends a chunk of the body. By calling this method many times, the user
 * can stream a request body to a server--in that case it is suggested to
 * use the ['Transfer-Encoding', 'chunked'] header line when creating the
 * request.
 * @param chunk
 * @param encoding='utf8'
 */
http.ClientRequest.prototype.write = function(chunk, encoding) {}
/**
 * Aborts a request. (New since v0.3.8.)
 */
http.ClientRequest.prototype.abort = function() {}
/**
 * Finishes sending the request. If any parts of the body are unsent, it
 * will flush them to the stream. If the request is chunked, this will send
 * the terminating '0\r\n\r\n'.
 * @param data
 * @param encoding
 */
http.ClientRequest.prototype.end = function(data, encoding) {}

/**
 * http.request() uses a special Agent for managing multiple connections to
 * an HTTP server. Normally Agent instances should not be exposed to user
 * code, however in certain situations it's useful to check the status of
 * the agent. The http.getAgent() function allows you to access the agents.
 * @param host
 * @param port
 * @returns http.Agent
 */
http.getAgent = function(host, port) {}


/** @__local__ */ var __events__ = {};
/**
 * Emitted each time there is request. Note that there may be multiple
 * requests per connection (in the case of keep-alive connections). request
 * is an instance of http.ServerRequest and response is an instance of
 * http.ServerResponse
 * @param request {http.ServerRequest}
 * @param response {http.ServerResponse}
 */
__events__.request = function(request, response) {};
/**
 * When a new TCP stream is established. stream is an object of type
 * net.Stream. Usually users will not want to access this event. The stream
 * can also be accessed at request.connection.
 * @param stream {net.Stream}
 */
__events__.connection = function(stream) {};
/**
 * Emitted when the server closes.
 * @param errno {Number}
 */
__events__.close = function(errno) {};
/**
 * Emitted each time a request with an http Expect: 100-continue is
 * received. If this event isn't listened for, the server will
 * automatically respond with a 100 Continue as appropriate.
 * @param request {http.ServerRequest}
 * @param response {http.ServerResponse}
 */
__events__.checkContinue = function(request, response) {};
/**
 * Emitted each time a client requests a http upgrade. If this event isn't
 * listened for, then clients requesting an upgrade will have their
 * connections closed.
 * @param head {buffer.Buffer}
 * @param request {http.ServerRequest}
 * @param socket {net.Socket}
 */
__events__.upgrade = function(head, request, socket) {};
/**
 * If a client connection emits an 'error' event - it will forwarded here.
 * @param exception {Error}
 */
__events__.clientError = function(exception) {};
/**
 * Emitted when a piece of the message body is received.
 * @param chunk {String}
 */
__events__.data = function(chunk) {};
/**
 * Emitted exactly once for each request. After that, no more 'data' events
 * will be emitted on the request.
 */
__events__.end = function() {};
/**
 * Indicates that the underlaying connection was terminated before
 * response.end() was called or able to flush.
 * @param err {Error}
 */
__events__.close = function(err) {};
/**
 * Emitted each time a server responds to a request with an upgrade. If
 * this event isn't being listened for, clients receiving an upgrade header
 * will have their connections closed.
 * @param head {buffer.Buffer}
 * @param response {http.ServerResponse}
 * @param socket {net.Socket}
 */
__events__.upgrade = function(head, response, socket) {};
/**
 * Emitted when the server sends a '100 Continue' HTTP response, usually
 * because the request contained 'Expect: 100-continue'. This is an
 * instruction that the client should send the request body.
 */
__events__.continue = function() {};
/**
 * Emitted when a response is received to this request. This event is
 * emitted only once. The response argument will be an instance of
 * http.ClientResponse.
 * @param response {http.ClientResponse}
 */
__events__.response = function(response) {};
/**
 * Emitted when a piece of the message body is received.
 * @param chunk {String}
 */
__events__.data = function(chunk) {};
/**
 * Emitted exactly once for each message. No arguments. After emitted no
 * other events will be emitted on the response.
 */
__events__.end = function() {};

                var events = require('events');
                http.Server.prototype = new events.EventEmitter();
                http.ServerRequest.prototype = new events.EventEmitter();
                http.ClientRequest.prototype = new events.EventEmitter();
                http.ClientResponse.prototype = new events.EventEmitter();
                var stream = require('stream');
                http.ServerResponse.prototype = new stream.WritableStream();
                exports = http;

