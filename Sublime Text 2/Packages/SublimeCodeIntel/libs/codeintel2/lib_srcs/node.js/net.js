/**
 * The net module provides you with an asynchronous network wrapper. It
 * contains methods for creating both servers and clients (called streams).
 * You can include this module with require("net");
 */
var net = {};

/**
 * This object is an abstraction of of a TCP or UNIX socket. net.Socket
 * instances implement a duplex Stream interface. They can be created by
 * the user and used as a client (with connect()) or they can be created by
 * Node and passed to the user through the 'connection' event of a server.
 * Construct a new socket object.
 */
net.Socket = function() {}
net.Socket.prototype = {}
/**
 * Disables the Nagle algorithm. By default TCP connections use the Nagle
 * algorithm, they buffer data before sending it off. Setting noDelay will
 * immediately fire off data each time socket.write() is called.
 * @param noDelay=true
 */
net.Socket.prototype.setNoDelay = function(noDelay) {}
/**
 * Pauses the reading of data. That is, 'data' events will not be emitted.
 * Useful to throttle back an upload.
 */
net.Socket.prototype.pause = function() {}
/**
 * Half-closes the socket. I.E., it sends a FIN packet. It is possible the
 * server will still send some data.
 * @param data
 * @param encoding
 */
net.Socket.prototype.end = function(data, encoding) {}
/**
 * Sets the socket to timeout after timeout milliseconds of inactivity on
 * the socket. By default net.Socket do not have a timeout.
 * @param timeout
 * @param callback
 */
net.Socket.prototype.setTimeout = function(timeout, callback) {}
/**
 * Resumes reading after a call to pause().
 */
net.Socket.prototype.resume = function() {}
/**
 * This function has been removed in v0.3. It used to upgrade the
 * connection to SSL/TLS. See the TLS section for the new API.
 */
net.Socket.prototype.setSecure = function() {}
/**
 * Returns the bound address and port of the socket as reported by the
 * operating system. Returns an object with two properties, e.g.
 * {"address":"192.168.57.1", "port":62053}
 */
net.Socket.prototype.address = function() {}
/**
 * The string representation of the remote IP address. For example,
 * '74.125.127.100' or '2001:4860:a005::68'.
 */
net.Socket.prototype.remoteAddress = 0;
/**
 * For UNIX sockets, it is possible to send a file descriptor through the
 * socket. Simply add the fileDescriptor argument and listen for the 'fd'
 * event on the other end.
 * @param data
 * @param encoding
 * @param fileDescriptor
 * @param callback
 */
net.Socket.prototype.write = function(data, encoding, fileDescriptor, callback) {}
/**
 * Opens the connection for a given socket. If port and host are given,
 * then the socket will be opened as a TCP socket, if host is omitted,
 * localhost will be assumed. If a path is given, the socket will be opened
 * as a unix socket to that path.
 * @param path
 * @param callback
 */
net.Socket.prototype.connect = function(path, callback) {}
/**
 * Ensures that no more I/O activity happens on this socket. Only necessary
 * in case of errors (parse error or so).
 */
net.Socket.prototype.destroy = function() {}
/**
 * Sets the encoding (either 'ascii', 'utf8', or 'base64') for data that is
 * received.
 * @param encoding=null
 */
net.Socket.prototype.setEncoding = function(encoding) {}
/**
 * Enable/disable keep-alive functionality, and optionally set the initial
 * delay before the first keepalive probe is sent on an idle socket. Set
 * initialDelay (in milliseconds) to set the delay between the last data
 * packet received and the first keepalive probe. Setting 0 for
 * initialDelay will leave the value unchanged from the default (or
 * previous) setting.
 * @param enable=false
 * @param initialDelay
 */
net.Socket.prototype.setKeepAlive = function(enable, initialDelay) {}
/**
 * net.Socket has the property that socket.write() always works. This is to
 * help users get up an running quickly. The computer cannot necessarily
 * keep up with the amount of data that is written to a socket - the
 * network connection simply might be too slow. Node will internally queue
 * up the data written to a socket and send it out over the wire when it is
 * possible. (Internally it is polling on the socket's file descriptor for
 * being writable).
 */
net.Socket.prototype.bufferSize = 0;

/**
 * Tests if input is an IP address. Returns 0 for invalid strings, returns
 * 4 for IP version 4 addresses, and returns 6 for IP version 6 addresses.
 * @param input
 */
net.isIP = function(input) {}

/**
 * Returns true if input is a version 6 IP address, otherwise returns
 * false.
 * @param input
 */
net.isIPv6 = function(input) {}

/**
 * Returns true if input is a version 4 IP address, otherwise returns
 * false.
 * @param input
 */
net.isIPv4 = function(input) {}

/**
 * Creates a new TCP server. The connectionListener argument is
 * automatically set as a listener for the 'connection' event.
 * @param options
 * @param connectionListener
 * @returns net.Server
 */
net.createServer = function(options, connectionListener) {}

/**
 * This class is used to create a TCP or UNIX server.
 */
net.Server = function() {}
net.Server.prototype = {}
/**
 * Stop accepting connections for the given number of milliseconds (default
 * is one second). This could be useful for throttling new connections
 * against DoS attacks or other oversubscription.
 * @param msecs
 */
net.Server.prototype.pause = function(msecs) {}
/**
 * Start a server listening for connections on the given file descriptor.
 * @param fd
 */
net.Server.prototype.listenFD = function(fd) {}
/**
 * The number of concurrent connections on the server.
 */
net.Server.prototype.connections = 0;
/**
 * Set this property to reject connections when the server's connection
 * count gets high.
 */
net.Server.prototype.maxConnections = 0;
/**
 * Stops the server from accepting new connections. This function is
 * asynchronous, the server is finally closed when the server emits a
 * 'close' event.
 */
net.Server.prototype.close = function() {}
/**
 * Returns the bound address and port of the server as reported by the
 * operating system. Useful to find which port was assigned when giving
 * getting an OS-assigned address. Returns an object with two properties,
 * e.g. {"address":"127.0.0.1", "port":2121}
 */
net.Server.prototype.address = function() {}
/**
 * Start a UNIX socket server listening for connections on the given path.
 * @param path
 * @param callback
 */
net.Server.prototype.listen = function(path, callback) {}

/**
 * Construct a new socket object and opens a socket to the given location.
 * When the socket is established the 'connect' event will be emitted.
 * @param arguments
 */
net.createConnection = function(arguments) {}


/** @__local__ */ var __events__ = {};
/**
 * Emitted when a new connection is made. socket is an instance of
 * net.Socket.
 * @param socket {net.Socket}
 */
__events__.connection = function(socket) {};
/**
 * Emitted when the server closes.
 */
__events__.close = function() {};
/**
 * Emitted when a socket connection successfully is established. See
 * connect().
 */
__events__.connect = function() {};
/**
 * Emitted when data is received. The argument data will be a Buffer or
 * String. Encoding of data is set by socket.setEncoding(). (See the
 * Readable Stream section for more information.)
 * @param data {buffer.Buffer}
 */
__events__.data = function(data) {};
/**
 * Emitted when the other end of the socket sends a FIN packet.
 */
__events__.end = function() {};
/**
 * Emitted if the socket times out from inactivity. This is only to notify
 * that the socket has been idle. The user must manually close the
 * connection.
 */
__events__.timeout = function() {};
/**
 * Emitted when the write buffer becomes empty. Can be used to throttle
 * uploads.
 */
__events__.drain = function() {};
/**
 * Emitted when an error occurs. The 'close' event will be called directly
 * following this event.
 * @param exception {Error}
 */
__events__.error = function(exception) {};
/**
 * Emitted once the socket is fully closed. The argument had_error is a
 * boolean which says if the socket was closed due to a transmission error.
 * @param had_error {Boolean}
 */
__events__.close = function(had_error) {};

                /* net.Server inherits from EventEmitter */
                var events = require('events');
                net.Server.prototype = new events.EventEmitter();
                net.Socket.prototype = new events.EventEmitter();
                exports = net;

