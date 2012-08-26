# -*- coding: utf-8 -*-
# php.py - sublimelint package for checking php files

import re

from base_linter import BaseLinter

CONFIG = {
    'language': 'PHP',
    'executable': 'php',
    'lint_args': ['-l', '-d display_errors=On', '-d log_errors=Off']
}


class Linter(BaseLinter):
    def parse_errors(self, view, errors, lines, errorUnderlines, violationUnderlines, warningUnderlines, errorMessages, violationMessages, warningMessages):
        for line in errors.splitlines():
            match = re.match(r'^Parse error:\s*(?:\w+ error,\s*)?(?P<error>.+?)\s+in\s+.+?\s*line\s+(?P<line>\d+)', line)

            if match:
                error, line = match.group('error'), match.group('line')
                self.add_message(int(line), lines, error, errorMessages)
