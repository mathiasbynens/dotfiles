/**
 * These object are available in all modules. Some of these objects aren't
 * actually in the global scope but in the module scope - this will be
 * noted.
 */
var global_objects = {};

/**
 * The global namespace object.
 */
global_objects.global = 0;

/**
 * Used to print to stdout and stderr. See the stdio section.
 */
global_objects.console = 0;

/**
 * The process object. See the process object section.
 */
global_objects.process = 0;

/**
 * To require modules. See the Modules section. require isn't actually a
 * global but rather local to each module.
 */
global_objects.require = function() {}

/**
 * The filename of the script being executed. This is the absolute path,
 * and not necessarily the same filename passed in as a command line
 * argument.
 */
global_objects.__filename = 0;

global_objects.clearTimeout = function(t) {}

/**
 * The timer functions are global variables. See the timers section.
 * @param t
 */
global_objects.clearInterval = function(t) {}

/**
 * A reference to the current module. In particular module.exports is the
 * same as the exports object. See src/node.js for more information. module
 * isn't actually a global but rather local to each module.
 */
global_objects.module = 0;

global_objects.setInterval = function(cb, ms) {}

/**
 * The dirname of the script being executed.
 */
global_objects.__dirname = 0;

global_objects.setTimeout = function(cb, ms) {}


exports = global_objects;

