# -*- coding: utf-8 -*-
# cpp.py - sublimelint package for checking C++ files

import re

from base_linter import BaseLinter, INPUT_METHOD_TEMP_FILE

CONFIG = {
    'language': 'C',
    'executable': 'cppcheck',
    'lint_args': ['--enable=style', '--quiet', '{filename}'],
    'input_method': INPUT_METHOD_TEMP_FILE
}


class Linter(BaseLinter):
    CPPCHECK_RE = re.compile(r'\[.+?:(\d+?)\](.+)')

    def __init__(self, config):
	super(Linter, self).__init__(config)

    def parse_errors(self, view, errors, lines, errorUnderlines,
		     violationUnderlines, warningUnderlines,
		     errorMessages, violationMessages,
		     warningMessages):
	# Go through each line in the output of cppcheck
	for line in errors.splitlines():
	    match = self.CPPCHECK_RE.match(line)
	    if match:
		# The regular expression matches the line number and
		# the message as its two groups.
		lineno, message = match.group(1), match.group(2)
		# Remove the colon at the beginning of the message
		if len(message) > 0 and message[0] == ':':
		    message = message[1:].strip()
		lineno = int(lineno)
		self.add_message(lineno, lines, message, errorMessages)
