# -*- coding: utf-8 -*-
# puppet.py - sublimelint package for checking puppet files

import re

from base_linter import BaseLinter, INPUT_METHOD_TEMP_FILE

CONFIG = {
    'language': 'Puppet',
    'executable': 'puppet',
    'lint_args': ['parser', 'validate', '--color=false', '{filename}'],
    'test_existence_args': '-V',
    'input_method': INPUT_METHOD_TEMP_FILE
}


class Linter(BaseLinter):
    def parse_errors(self, view, errors, lines, errorUnderlines, violationUnderlines, warningUnderlines, errorMessages, violationMessages, warningMessages):
        for line in errors.splitlines():
            match = re.match(r'err: (?P<error>.+?(Syntax error at \'(?P<near>.+?)\'; expected \'.+\')) at /.+?:(?P<line>\d+)?', line)
            if not match:
                match = re.match(r'err: (?P<error>.+?(Could not match (?P<near>.+?))?) at /.+?:(?P<line>\d+)?', line)

            if match:
                error, line = match.group('error'), match.group('line')
                lineno = int(line)
                near = match.group('near')

                if near:
                    error = '{0}, near "{1}"'.format(error, near)
                    self.underline_regex(view, lineno, '(?P<underline>{0})'.format(re.escape(near)), lines, errorUnderlines)

                self.add_message(lineno, lines, error, errorMessages)
