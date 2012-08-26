# -*- coding: utf-8 -*-
# java.py - sublimelint package for checking java files

import os
import os.path
import re

from base_linter import BaseLinter, INPUT_METHOD_FILE

CONFIG = {
    'language': 'Java',
    'executable': 'javac',
    'test_existence_args': '-version',
    'input_method': INPUT_METHOD_FILE
}

ERROR_RE = re.compile(r'^(?P<path>.*\.java):(?P<line>\d+): (?P<warning>warning: )?(?:\[\w+\] )?(?P<error>.*)')
MARK_RE = re.compile(r'^(?P<mark>\s*)\^$')


class Linter(BaseLinter):
    def parse_errors(self, view, errors, lines, errorUnderlines,
                     violationUnderlines, warningUnderlines, errorMessages,
                     violationMessages, warningMessages):
        it = iter(errors.splitlines())

        for line in it:
            match = re.match(ERROR_RE, line)

            if match:
                path = os.path.abspath(match.group('path'))

                if path != self.filename:
                    continue

                lineNumber = int(match.group('line'))
                warning = match.group('warning')
                error = match.group('error')

                if warning:
                    messages = warningMessages
                    underlines = warningUnderlines
                else:
                    messages = errorMessages
                    underlines = errorUnderlines

                # Skip forward until we find the marker
                position = -1

                while True:
                    line = it.next()
                    match = re.match(MARK_RE, line)

                    if match:
                        position = len(match.group('mark'))
                        break

                self.add_message(lineNumber, lines, error, messages)
                self.underline_range(view, lineNumber, position, underlines)
