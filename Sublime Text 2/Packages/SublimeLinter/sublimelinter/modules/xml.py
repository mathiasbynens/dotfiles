# -*- coding: utf-8 -*-
# xml.py - sublimelint package for checking xml files

import re

from base_linter import BaseLinter

CONFIG = {
    'language': 'XML',
    'executable': 'xmllint',
    'lint_args': ['-noout', '-']
}


class Linter(BaseLinter):
    def parse_errors(self, view, errors, lines, errorUnderlines, violationUnderlines, warningUnderlines, errorMessages, violationMessages, warningMessages):

        for line in errors.splitlines():
            match = re.match(r'\-\:(?P<line>\d+): (?P<error>.+)', line)

            if match:
                error, line = match.group('error'), match.group('line')
                self.add_message(int(line), lines, error, errorMessages)
