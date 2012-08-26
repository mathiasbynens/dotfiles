''' sublime_pylint.py - sublimelint package for checking python files

pylint is not available as a checker that runs in the background
as it generally takes much too long.
'''

from StringIO import StringIO
import tempfile

try:
    from pylint import checkers
    from pylint import lint
    PYLINT_AVAILABLE = True
except ImportError:
    PYLINT_AVAILABLE = False

from base_linter import BaseLinter

CONFIG = {
    'language': 'pylint'
}


class Linter(BaseLinter):
    def get_executable(self, view):
        return (PYLINT_AVAILABLE, None, 'built in' if PYLINT_AVAILABLE else 'the pylint module could not be imported')

    def built_in_check(self, view, code, filename):
        linter = lint.PyLinter()
        checkers.initialize(linter)

        # Disable some errors.
        linter.load_command_line_configuration([
            '--module-rgx=.*',  # don't check the module name
            '--reports=n',      # remove tables
            '--persistent=n',   # don't save the old score (no sense for temp)
        ])

        temp = tempfile.NamedTemporaryFile(suffix='.py')
        temp.write(code)
        temp.flush()

        output_buffer = StringIO()
        linter.reporter.set_output(output_buffer)
        linter.check(temp.name)
        report = output_buffer.getvalue().replace(temp.name, 'line ')

        output_buffer.close()
        temp.close()

        return report

    def remove_unwanted(self, errors):
        '''remove unwanted warnings'''
        ## todo: investigate how this can be set by a user preference
        #  as it appears that the user pylint configuration file is ignored.
        lines = errors.split('\n')
        wanted = []
        unwanted = ["Found indentation with tabs instead of spaces",
                    "************* Module"]

        for line in lines:
            for not_include in unwanted:
                if not_include in line:
                    break
            else:
                wanted.append(line)

        return '\n'.join(wanted)

    def parse_errors(self, view, errors, lines, errorUnderlines, violationUnderlines, warningUnderlines, errorMessages, violationMessages, warningMessages):
        errors = self.remove_unwanted(errors)

        for line in errors.splitlines():
            info = line.split(":")

            try:
                lineno = info[1]
            except IndexError:
                print info

            message = ":".join(info[2:])
            self.add_message(int(lineno), lines, message, errorMessages)
