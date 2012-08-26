/*jslint node: true, sloppy: true */
/*globals LINTER_PATH, load */

var CSSLint = require("./csslint-node").CSSLint;

exports.lint = function (code, config) {
    var results = [];

    var ruleset = {};

    // rules that are `false` will be ignored.
    for (var ruleName in config) {

        if (config[ruleName] === 'warning') {
            ruleset[ruleName] = 1;
        // Rules set to `true` or 'error' will be considered errors
        } else if (config[ruleName]) {
            ruleset[ruleName] = 2;
        }

    }

    var report = CSSLint.verify(code, ruleset);

    report.messages.forEach(function (message) {
        if (message) {

            // message.type // warning|error
            // message.line
            // message.col
            // message.message
            // message.evidence // Requires sanitizing as it can include CR, LF
            // message.rule // The rule object

            // We don't pass on the rollup messages
            if (message.rollup !== true) {
                results.push({
                    'line': message.line,
                    'character': message.col,
                    'type': message.type,
                    'reason': message.message
                });
            }
        }
    });

    return results;
};
