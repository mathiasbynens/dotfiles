# -*- coding: utf-8 -*-
# javascript.py - sublimelint package for checking Javascript files

import json
import re
import subprocess

from base_linter import BaseLinter, INPUT_METHOD_TEMP_FILE

CONFIG = {
    'language': 'JavaScript'
}


class Linter(BaseLinter):
    GJSLINT_RE = re.compile(r'Line (?P<line>\d+),\s*E:(?P<errnum>\d+):\s*(?P<message>.+)')

    def __init__(self, config):
        super(Linter, self).__init__(config)
        self.linter = None

    def get_executable(self, view):
        self.linter = view.settings().get('javascript_linter', 'jshint')

        if (self.linter in ('jshint', 'jslint')):
            return self.get_javascript_engine(view)
        elif (self.linter == 'gjslint'):
            try:
                path = self.get_mapped_executable(view, 'gjslint')
                subprocess.call([path, '--help'], startupinfo=self.get_startupinfo())
                self.input_method = INPUT_METHOD_TEMP_FILE
                return (True, path, 'using gjslint')
            except OSError:
                return (False, '', 'gjslint cannot be found')
        else:
            return (False, '', '"{0}" is not a valid javascript linter'.format(self.linter))

    def get_lint_args(self, view, code, filename):
        if (self.linter == 'gjslint'):
            args = []
            gjslint_options = view.settings().get("gjslint_options", [])
            args.extend(gjslint_options)
            args.extend(['--nobeep', filename])
            return args
        elif (self.linter in ('jshint', 'jslint')):
            return self.get_javascript_args(view, self.linter, code)
        else:
            return []

    def get_javascript_options(self, view):
        if self.linter == 'jshint':
            rc_options = self.find_file('.jshintrc', view)

            if rc_options != None:
                rc_options = self.strip_json_comments(rc_options)
                return json.dumps(json.loads(rc_options))

    def parse_errors(self, view, errors, lines, errorUnderlines, violationUnderlines, warningUnderlines, errorMessages, violationMessages, warningMessages):
        if (self.linter == 'gjslint'):
            ignore = view.settings().get('gjslint_ignore', [])

            for line in errors.splitlines():
                match = self.GJSLINT_RE.match(line)

                if match:
                    line, errnum, message = match.group('line'), match.group('errnum'), match.group('message')

                    if (int(errnum) not in ignore):
                        self.add_message(int(line), lines, message, errorMessages)

        elif (self.linter in ('jshint', 'jslint')):
            try:
                errors = json.loads(errors.strip() or '[]')
            except ValueError:
                raise ValueError("Error from {0}: {1}".format(self.linter, errors))

            for error in errors:
                lineno = error['line']
                self.add_message(lineno, lines, error['reason'], errorMessages)
                self.underline_range(view, lineno, error['character'] - 1, errorUnderlines)
