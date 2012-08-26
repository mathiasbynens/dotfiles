/*jshint node:true */

/*
    usage: node /path/to/node.js /path/to/linter/ ["{option1:true,option2:false}"]
    */

var _fs = require('fs'),
    _util = require('util'),
    _path = require('path'),
    linterPath = process.argv[2].replace(/\/$/, '') + '/',
    _linter = require(linterPath + 'linter');

function run() {
    var code = '',
        results,
        config = JSON.parse(process.argv[3] || '{}'),
        filename = process.argv[4] || '';

    if (filename) {
        results = _linter.lint(_fs.readFileSync(filename, 'utf-8'), config, linterPath);
        _util.puts(JSON.stringify(results));
    } else {
        process.stdin.resume();
        process.stdin.setEncoding('utf8');

        process.stdin.on('data', function (chunk) {
            code += chunk;
        });

        process.stdin.on('end', function () {
            results = _linter.lint(code, config, linterPath);
            _util.puts(JSON.stringify(results));
        });
    }
}

run();
