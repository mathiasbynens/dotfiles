/**
 * Use require('tls') to access this module.
 */
var tls = {};

/**
 * This is a constructor for the tls.Server class. The options object has
 * these possibilities:
 * @param options
 * @param secureConnectionListener
 * @returns tls.Server
 */
tls.createServer = function(options, secureConnectionListener) {}

/**
 * Creates a new client connection to the given port and host. (If host
 * defaults to localhost.) options should be an object which specifies
 * @param port
 * @param host
 * @param options
 * @param callback
 */
tls.connect = function(port, host, options, callback) {}

/**
 * This class is a subclass of net.Server and has the same methods on it.
 * Instead of accepting just raw TCP connections, this accepts encrypted
 * connections using TLS or SSL.
 */
tls.Server = function() {}
tls.Server.prototype = {}
/**
 * The number of concurrent connections on the server.
 */
tls.Server.prototype.connections = 0;
/**
 * Stops the server from accepting new connections. This function is
 * asynchronous, the server is finally closed when the server emits a
 * 'close' event.
 */
tls.Server.prototype.close = function() {}
/**
 * Set this property to reject connections when the server's connection
 * count gets high.
 */
tls.Server.prototype.maxConnections = 0;
/**
 * Begin accepting connections on the specified port and host. If the host
 * is omitted, the server will accept connections directed to any IPv4
 * address (INADDR_ANY).
 * @param port
 * @param host
 * @param callback
 */
tls.Server.prototype.listen = function(port, host, callback) {}


/** @__local__ */ var __events__ = {};
/**
 * This event is emitted after a new connection has been successfully
 * handshaked. The argument is a duplex instance of stream.Stream. It has
 * all the common stream methods and events.
 * @param cleartextStream {stream.Stream}
 */
__events__.secureConnection = function(cleartextStream) {};

exports = tls;

