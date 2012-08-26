# -*- coding: utf-8 -*-
# perl.py - sublimelint package for checking perl files

import re
import subprocess

from base_linter import BaseLinter

CONFIG = {
    'language': 'Perl'
}


class Linter(BaseLinter):
    PERLCRITIC_RE = re.compile(r'\[(?P<pbp>.+)\] (?P<error>.+?) at line (?P<line>\d+), column (?P<column>\d+).+?')
    PERL_RE = re.compile(r'(?P<error>.+?) at .+? line (?P<line>\d+)(, near "(?P<near>.+?)")?')

    def __init__(self, config):
        super(Linter, self).__init__(config)
        self.linter = None

    def get_executable(self, view):
        self.linter = view.settings().get('perl_linter', 'perlcritic')

        if self.linter == 'perl':
            linter_name = 'Perl'
        else:
            linter_name = 'Perl::Critic'

        try:
            path = self.get_mapped_executable(view, self.linter)
            subprocess.call([path, '--version'], startupinfo=self.get_startupinfo())
            return (True, path, 'using {0}'.format(linter_name))
        except OSError:
            return (False, '', '{0} is required'.format(linter_name))

    def get_lint_args(self, view, code, filename):
        if self.linter == 'perl':
            return ['-c']
        else:
            return ['--verbose', '8']

    def parse_errors(self, view, errors, lines, errorUnderlines, violationUnderlines, warningUnderlines, errorMessages, violationMessages, warningMessages):
        for line in errors.splitlines():
            if self.linter == 'perl':
                match = self.PERL_RE.match(line)
            else:
                match = self.PERLCRITIC_RE.match(line)

            if match:
                error, line = match.group('error'), match.group('line')
                lineno = int(line)

                if self.linter == 'perl':
                    near = match.group('near')

                    if near:
                        error = '{0}, near "{1}"'.format(error, near)
                        self.underline_regex(view, lineno, '(?P<underline>{0})'.format(re.escape(near)), lines, errorUnderlines)
                else:
                    column = match.group('column')
                    column = int(column) - 1
                    self.underline_word(view, lineno, column, errorUnderlines)

                self.add_message(lineno, lines, error, errorMessages)
