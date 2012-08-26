/**
 * The process object is a global object and can be accessed from anywhere.
 * It is an instance of EventEmitter.
 */
var process = {};

/**
 * Sets the user identity of the process. (See setuid(2).) This accepts
 * either a numerical ID or a username string. If a username is specified,
 * this method blocks while resolving it to a numerical ID.
 * @param id
 */
process.setuid = function(id) {}

/**
 * On the next loop around the event loop call this callback. This is not a
 * simple alias to setTimeout(fn, 0), it's much more efficient.
 * @param callback
 */
process.nextTick = function(callback) {}

/**
 * A Writable Stream to stdout.
 */
process.stdout = 0;

/**
 * The PID of the process.
 */
process.pid = 0;

/**
 * Returns an object describing the memory usage of the Node process.
 */
process.memoryUsage = function() {}

/**
 * Send a signal to a process. pid is the process id and signal is the
 * string describing the signal to send. Signal names are strings like
 * 'SIGINT' or 'SIGUSR1'. If omitted, the signal will be 'SIGTERM'. See
 * kill(2) for more information.
 * @param pid
 * @param signal='SIGTERM'
 */
process.kill = function(pid, signal) {}

/**
 * Gets the group identity of the process. (See getgid(2).) This is the
 * numerical group id, not the group name.
 */
process.getgid = function() {}

/**
 * Getter/setter to set what is displayed in 'ps'.
 */
process.title = 0;

/**
 * Sets or reads the process's file mode creation mask. Child processes
 * inherit the mask from the parent process. Returns the old mask if mask
 * argument is given, otherwise returns the current mask.
 * @param mask
 */
process.umask = function(mask) {}

/**
 * What platform you're running on. 'linux2', 'darwin', etc.
 */
process.platform = 0;

/**
 * A compiled-in property that exposes NODE_VERSION.
 */
process.version = 0;

/**
 * Ends the process with the specified code. If omitted, exit uses the
 * 'success' code 0.
 * @param code=0
 */
process.exit = function(code) {}

/**
 * An object containing the user environment. See environ(7).
 */
process.env = 0;

/**
 * Returns the current working directory of the process.
 */
process.cwd = function() {}

/**
 * A compiled-in property that exposes NODE_PREFIX.
 */
process.installPrefix = 0;

/**
 * Sets the group identity of the process. (See setgid(2).) This accepts
 * either a numerical ID or a groupname string. If a groupname is
 * specified, this method blocks while resolving it to a numerical ID.
 * @param id
 */
process.setgid = function(id) {}

/**
 * An array containing the command line arguments. The first element will
 * be 'node', the second element will be the name of the JavaScript file.
 * The next elements will be any additional command line arguments.
 */
process.argv = 0;

/**
 * Changes the current working directory of the process or throws an
 * exception if that fails.
 * @param directory
 */
process.chdir = function(directory) {}

/**
 * Gets the user identity of the process. (See getuid(2).) This is the
 * numerical userid, not the username.
 */
process.getuid = function() {}

/**
 * A Readable Stream for stdin. The stdin stream is paused by default, so
 * one must call process.stdin.resume() to read from it.
 */
process.stdin = 0;

/**
 * A writable stream to stderr. Writes on this stream are blocking.
 */
process.stderr = 0;

/**
 * This is the absolute pathname of the executable that started the
 * process.
 */
process.execPath = 0;


/** @__local__ */ var __events__ = {};
/**
 * Emitted when the process is about to exit. This is a good hook to
 * perform constant time checks of the module's state (like for unit
 * tests). The main event loop will no longer be run after the 'exit'
 * callback finishes, so timers may not be scheduled.
 */
__events__.exit = function() {};
/**
 * Emitted when an exception bubbles all the way back to the event loop. If
 * a listener is added for this exception, the default action (which is to
 * print a stack trace and exit) will not occur.
 * @param err {Object}
 */
__events__.uncaughtException = function(err) {};

exports = process;

