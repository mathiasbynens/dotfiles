/**
 * Use require('os') to access this module.
 */
var os = {};

/**
 * Returns the system uptime in seconds.
 */
os.uptime = function() {}

/**
 * Returns the total amount of system memory in bytes.
 */
os.totalmem = function() {}

/**
 * Returns the hostname of the operating system.
 */
os.hostname = function() {}

/**
 * Returns an array of objects containing information about each CPU/core
 * installed: model, speed (in MHz), and times (an object containing the
 * number of CPU ticks spent in: user, nice, sys, idle, and irq).
 */
os.cpus = function() {}

/**
 * Returns an array containing the 1, 5, and 15 minute load averages.
 */
os.loadavg = function() {}

/**
 * Returns the operating system release.
 */
os.release = function() {}

/**
 * Returns the operating system name.
 */
os.type = function() {}

/**
 * Returns the amount of free system memory in bytes.
 */
os.freemem = function() {}


exports = os;

