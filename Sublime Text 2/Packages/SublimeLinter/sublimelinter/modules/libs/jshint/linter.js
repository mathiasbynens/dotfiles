/*jshint node: true */
/*globals LINTER_PATH load */

var JSHINT = require("./jshint").JSHINT;

exports.lint = function (code, config) {
    var results = [];

    try {
        JSHINT(code, config);
    } catch (e) {
        results.push({line: 1, character: 1, reason: e.message});
    } finally {
        JSHINT.errors.forEach(function (error) {
            if (error) {
                results.push(error);
            }
        });
    }

    return results;
};
