# -*- coding: utf-8 -*-
# git_commit_message.py - sublimelint package for checking Git commit messages

from base_linter import BaseLinter


CONFIG = {
    'language': 'Git Commit Message'
}


class ErrorType:
    WARNING = 'warning'
    VIOLATION = 'violation'
    ERROR = 'error'


class Linter(BaseLinter):

    def built_in_check(self, view, code, filename):
        lines = code.splitlines()
        lineno = 0
        real_lineno = 0
        first_line_of_message = None
        first_line_of_body = None
        errors = []

        for line in lines:
            real_lineno += 1

            if line.startswith('#'):
                continue

            if line.startswith('diff --git'):
                break

            lineno += 1

            if first_line_of_message is None:
                if line.strip():
                    first_line_of_message = lineno

                    if len(line) > 68:
                        errors.append({
                            'type': ErrorType.ERROR,
                            'message': 'Subject line must be 68 characters or less (github will truncate).',
                            'lineno': real_lineno,
                            'col': 68,
                        })
                    elif len(line) > 50:
                        errors.append({
                            'type': ErrorType.WARNING,
                            'message': 'Subject line should be 50 characters or less.',
                            'lineno': real_lineno,
                            'col': 50,
                        })
                    elif lineno != 1:
                        errors.append({
                            'type': ErrorType.ERROR,
                            'message': 'Subject must be on first line.',
                            'lineno': real_lineno,
                        })
                    elif line[0].upper() != line[0]:
                        errors.append({
                            'type': ErrorType.VIOLATION,
                            'message': 'Subject line should be capitalized.',
                            'lineno': real_lineno,
                        })
            elif first_line_of_body is None:
                if len(line):
                    first_line_of_body = lineno

                    if lineno == first_line_of_message + 1:
                        if len(line):
                            errors.append({
                                'message': 'Leave a blank line between the message subject and body.',
                                'lineno': first_line_of_message + 1,
                            })
                    elif lineno > first_line_of_message + 2:
                        errors.append({
                            'message': 'Leave exactly 1 blank line between the message subject and body.',
                            'lineno': real_lineno,
                        })
            if first_line_of_body is not None:
                if len(line) > 72:
                    errors.append({
                        'message': 'Lines must not exceed 72 characters.',
                        'lineno': real_lineno,
                        'col': 72,
                    })

        return errors

    def parse_errors(self, view, errors, lines, errorUnderlines, violationUnderlines, warningUnderlines, errorMessages, violationMessages, warningMessages):
        for error in errors:
            error_type = error.get('type', ErrorType.ERROR)
            col = error.get('col', 0)

            messages = {
                ErrorType.WARNING: warningMessages,
                ErrorType.VIOLATION: violationMessages,
                ErrorType.ERROR: errorMessages,
            }[error_type]
            underlines = {
                ErrorType.WARNING: warningUnderlines,
                ErrorType.VIOLATION: violationUnderlines,
                ErrorType.ERROR: errorUnderlines,
            }[error_type]

            self.add_message(error['lineno'], lines, error['message'], messages)
            self.underline_range(view, error['lineno'], col, underlines, length=1)
