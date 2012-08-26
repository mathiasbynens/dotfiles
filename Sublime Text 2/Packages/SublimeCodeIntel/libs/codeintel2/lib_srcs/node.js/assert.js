/**
 * This module is used for writing unit tests for your applications, you
 * can access it with require('assert').
 */
var assert = {};

/**
 * Tests shallow, coercive non-equality with the not equal comparison
 * operator ( != ).
 * @param actual
 * @param expected
 * @param message
 */
assert.notEqual = function(actual, expected, message) {}

/**
 * Expects block not to throw an error, see assert.throws for details.
 * @param block
 * @param error
 * @param message
 */
assert.doesNotThrow = function(block, error, message) {}

/**
 * Tests if value is a true value, it is equivalent to assert.equal(true,
 * value, message);
 * @param value
 * @param message
 */
assert.ok = function(value, message) {}

/**
 * Tests if value is not a false value, throws if it is a true value.
 * Useful when testing the first argument, error in callbacks.
 * @param value
 */
assert.ifError = function(value) {}

/**
 * Tests shallow, coercive equality with the equal comparison operator ( ==
 * ).
 * @param actual
 * @param expected
 * @param message
 */
assert.equal = function(actual, expected, message) {}

/**
 * Tests for any deep inequality.
 * @param actual
 * @param expected
 * @param message
 */
assert.notDeepEqual = function(actual, expected, message) {}

/**
 * Tests strict non-equality, as determined by the strict not equal
 * operator ( !== )
 * @param actual
 * @param expected
 * @param message
 */
assert.notStrictEqual = function(actual, expected, message) {}

/**
 * Tests if actual is equal to expected using the operator provided.
 * @param actual
 * @param expected
 * @param message
 * @param operator
 */
assert.fail = function(actual, expected, message, operator) {}

/**
 * Expects block to throw an error. error can be constructor, regexp or
 * validation function.
 * @param block
 * @param error
 * @param message
 */
assert.throws = function(block, error, message) {}

/**
 * Tests strict equality, as determined by the strict equality operator (
 * === )
 * @param actual
 * @param expected
 * @param message
 */
assert.strictEqual = function(actual, expected, message) {}

/**
 * Tests for deep equality.
 * @param actual
 * @param expected
 * @param message
 */
assert.deepEqual = function(actual, expected, message) {}


exports = assert;

