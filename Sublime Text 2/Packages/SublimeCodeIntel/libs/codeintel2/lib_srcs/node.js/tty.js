/**
 * Use require('tty') to access this module.
 */
var tty = {};

/**
 * Returns true or false depending on if the fd is associated with a
 * terminal.
 * @param fd
 */
tty.isatty = function(fd) {}

/**
 * ioctls the window size settings to the file descriptor.
 * @param fd
 * @param row
 * @param col
 */
tty.setWindowSize = function(fd, row, col) {}

/**
 * Spawns a new process with the executable pointed to by path as the
 * session leader to a new pseudo terminal.
 * @param path
 * @param args=[]
 * @returns child_process.ChildProcess
 */
tty.open = function(path, args) {}

/**
 * mode should be true or false. This sets the properties of the current
 * process's stdin fd to act either as a raw device or default.
 * @param mode
 */
tty.setRawMode = function(mode) {}

/**
 * Returns [row, col] for the TTY associated with the file descriptor.
 * @param fd
 */
tty.getWindowSize = function(fd) {}


                /* return value of tty.open */
                var child_process = require('child_process');
                exports = tty;

