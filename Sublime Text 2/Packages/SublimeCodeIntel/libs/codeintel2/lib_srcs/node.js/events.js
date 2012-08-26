/**
 * Many objects in Node emit events: a net.Server emits an event each time
 * a peer connects to it, a fs.readStream emits an event when the file is
 * opened. All objects which emit events are instances of
 * events.EventEmitter. You can access this module by doing:
 * require("events");
 */
var events = {};

/**
 * To access the EventEmitter class, require('events').EventEmitter.
 */
events.EventEmitter = function() {}
events.EventEmitter.prototype = {}
/**
 * Adds a listener to the end of the listeners array for the specified
 * event.
 * @param event
 * @param listener
 */
events.EventEmitter.prototype.on = function(event, listener) {}
events.EventEmitter.prototype.addListener = function(event, listener) {}
/**
 * Removes all listeners from the listener array for the specified event.
 * @param event
 */
events.EventEmitter.prototype.removeAllListeners = function(event) {}
/**
 * By default EventEmitters will print a warning if more than 10 listeners
 * are added to it. This is a useful default which helps finding memory
 * leaks. Obviously not all Emitters should be limited to 10. This function
 * allows that to be increased. Set to zero for unlimited.
 * @param n
 */
events.EventEmitter.prototype.setMaxListeners = function(n) {}
/**
 * Returns an array of listeners for the specified event. This array can be
 * manipulated, e.g. to remove listeners.
 * @param event
 */
events.EventEmitter.prototype.listeners = function(event) {}
/**
 * Execute each of the listeners in order with the supplied arguments.
 * @param event
 * @param arg1
 * @param arg2
 */
events.EventEmitter.prototype.emit = function(event, arg1, arg2) {}
/**
 * Remove a listener from the listener array for the specified event.
 * Caution: changes array indices in the listener array behind the
 * listener.
 * @param event
 * @param listener
 */
events.EventEmitter.prototype.removeListener = function(event, listener) {}
/**
 * Adds a one time listener for the event. The listener is invoked only the
 * first time the event is fired, after which it is removed.
 * @param event
 * @param listener
 */
events.EventEmitter.prototype.once = function(event, listener) {}


/** @__local__ */ var __events__ = {};
/**
 * This event is emitted any time someone adds a new listener.
 * @param event {String}
 * @param listener {Function}
 */
__events__.newListener = function(listener, event) {};

exports = events;

