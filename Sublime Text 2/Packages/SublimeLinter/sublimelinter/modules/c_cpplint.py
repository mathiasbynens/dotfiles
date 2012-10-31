# -*- coding: utf-8 -*-
# cpp.py - sublimelint package for checking C++ files (based on ruby.py)

import re

from base_linter import BaseLinter, INPUT_METHOD_TEMP_FILE

CONFIG = {
    'language': 'c_cpplint',
    'executable': 'cpplint.py',
    'test_existence_args': ['--help'],
    'lint_args': '{filename}',
    'input_method': INPUT_METHOD_TEMP_FILE
}


class Linter(BaseLinter):
    def parse_errors(self, view, errors, lines, errorUnderlines, violationUnderlines, warningUnderlines, errorMessages, violationMessages, warningMessages):
	for line in errors.splitlines():
	    match = re.match(r'^.+:(?P<line>\d+):\s+(?P<error>.+)', line)

	    if match:
		error, line = match.group('error'), match.group('line')
		self.add_message(int(line), lines, error, errorMessages)
