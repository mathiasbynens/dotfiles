/*jslint node: true, sloppy: true */
/*globals LINTER_PATH, load */

var JSLINT = require("./jslint").JSLINT;

exports.lint = function (code, config) {
    var results = [];

    try {
        JSLINT(code, config);
    } catch (e) {
        results.push({line: 1, character: 1, reason: e.message});
    } finally {
        JSLINT.errors.forEach(function (error) {
            if (error) {
                results.push(error);
            }
        });
    }

    return results;
};
