# -*- coding: utf-8 -*-
# html.py - sublimelint package for checking html files

# Example error messages
#
# line 1 column 1 - Warning: missing <!DOCTYPE> declaration
# line 200 column 1 - Warning: discarding unexpected </div>
# line 1 column 1 - Warning: inserting missing 'title' element

import re
import subprocess

from base_linter import BaseLinter

CONFIG = {
    'language': 'HTML',
    'executable': 'tidy',
    'lint_args': '-eq'
}


class Linter(BaseLinter):
    def get_executable(self, view):
        try:
            path = self.get_mapped_executable(view, 'tidy')
            version_string = subprocess.Popen([path, '-v'], startupinfo=self.get_startupinfo(), stdout=subprocess.PIPE).communicate()[0]

            if u'HTML5' in version_string:
                return (True, path, 'using tidy for executable')

            return (False, '', 'tidy is not ready for HTML5')
        except OSError:
            return (False, '', 'tidy cannot be found')

    def parse_errors(self, view, errors, lines, errorUnderlines, violationUnderlines, warningUnderlines, errorMessages, violationMessages, warningMessages):
        for line in errors.splitlines():
            match = re.match(r'^line\s(?P<line>\d+)\scolumn\s\d+\s-\s(?P<error>.+)', line)

            if match:
                error, line = match.group('error'), match.group('line')
                self.add_message(int(line), lines, error, errorMessages)
