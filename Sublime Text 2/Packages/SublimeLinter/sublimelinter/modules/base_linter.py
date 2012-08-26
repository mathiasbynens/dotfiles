# -*- coding: utf-8 -*-
# base_linter.py - base class for linters

import os
import os.path
import json
import re
import subprocess

import sublime

# If the linter uses an executable that takes stdin, use this input method.
INPUT_METHOD_STDIN = 1

# If the linter uses an executable that does not take stdin but you wish to use
# a temp file so that the current view can be linted interactively, use this input method.
# If the current view has been saved, the tempfile will have the same name as the
# view's file, which is necessary for some linters.
INPUT_METHOD_TEMP_FILE = 2

# If the linter uses an executable that does not take stdin and you wish to have
# linting occur only on file load and save, use this input method.
INPUT_METHOD_FILE = 3

CONFIG = {
    # The display language name for this linter.
    'language': '',

    # Linters may either use built in code or use an external executable. This item may have
    # one of the following values:
    #
    #   string - An external command (or path to a command) to execute
    #   None - The linter is considered to be built in
    #
    # Alternately, your linter class may define the method get_executable(),
    # which should return the three-tuple (<enabled>, <executable>, <message>):
    #   <enabled> must be a boolean than indicates whether the executable is available and usable.
    #   If <enabled> is True, <executable> must be one of:
    #       - A command string (or path to a command) if an external executable will be used
    #       - None if built in code will be used
    #       - False if no suitable executable can be found or the linter should be disabled
    #         for some other reason.
    #   <message> is the message that will be shown in the console when the linter is
    #   loaded, to aid the user in knowing what the status of the linter is. If None or an empty string,
    #   a default message will be returned based on the value of <executable>. Otherwise it
    #   must be a string.
    'executable': None,

    # If an external executable is being used, this item specifies the arguments
    # used when checking the existence of the executable to determine if the linter can be enabled.
    # If more than one argument needs to be passed, use a tuple/list.
    # Defaults to '-v' if this item is missing.
    'test_existence_args': '-v',

    # If an external executable is being used, this item specifies the arguments to be passed
    # when linting. If there is more than one argument, use a tuple/list.
    # If the input method is anything other than INPUT_METHOD_STDIN, put a {filename} placeholder in
    # the args where the filename should go.
    #
    # Alternately, if your linter class may define the method get_lint_args(), which should return
    # None for no arguments or a tuple/list for one or more arguments.
    'lint_args': None,

    # If an external executable is being used, the method used to pass input to it. Defaults to STDIN.
    'input_method': INPUT_METHOD_STDIN
}

TEMPFILES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.tempfiles'))

JSON_MULTILINE_COMMENT_RE = re.compile(r'\/\*[\s\S]*?\*\/')
JSON_SINGLELINE_COMMENT_RE = re.compile(r'\/\/[^\n\r]*')

if not os.path.exists(TEMPFILES_DIR):
    os.mkdir(TEMPFILES_DIR)


class BaseLinter(object):
    '''A base class for linters. Your linter module needs to do the following:

            - Set the relevant values in CONFIG
            - Override built_in_check() if it uses a built in linter. You may return
              whatever value you want, this value will be passed to parse_errors().
            - Override parse_errors() and populate the relevant lists/dicts. The errors
              argument passed to parse_errors() is the output of the executable run through strip().

       If you do subclass and override __init__, be sure to call super(MyLinter, self).__init__(config).
    '''

    JSC_PATH = '/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Resources/jsc'

    LIB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'libs'))

    JAVASCRIPT_ENGINES = ['node', 'jsc']
    JAVASCRIPT_ENGINE_NAMES = {'node': 'node.js', 'jsc': 'JavaScriptCore'}
    JAVASCRIPT_ENGINE_WRAPPERS_PATH = os.path.join(LIB_PATH, 'jsengines')

    def __init__(self, config):
        self.language = config['language']
        self.enabled = False
        self.executable = config.get('executable', None)
        self.test_existence_args = config.get('test_existence_args', ['-v'])
        self.js_engine = None

        if isinstance(self.test_existence_args, basestring):
            self.test_existence_args = (self.test_existence_args,)

        self.input_method = config.get('input_method', INPUT_METHOD_STDIN)
        self.filename = None
        self.lint_args = config.get('lint_args', [])

        if isinstance(self.lint_args, basestring):
            self.lint_args = [self.lint_args]

    def check_enabled(self, view):
        if hasattr(self, 'get_executable'):
            try:
                self.enabled, self.executable, message = self.get_executable(view)

                if self.enabled and not message:
                    message = 'using "{0}"'.format(self.executable) if self.executable else 'built in'
            except Exception as ex:
                self.enabled = False
                message = unicode(ex)
        else:
            self.enabled, message = self._check_enabled(view)

        return (self.enabled, message or '<unknown reason>')

    def _check_enabled(self, view):
        if self.executable is None:
            return (True, 'built in')
        elif isinstance(self.executable, basestring):
            self.executable = self.get_mapped_executable(view, self.executable)
        elif isinstance(self.executable, bool) and self.executable == False:
            return (False, 'unknown error')
        else:
            return (False, 'bad type for CONFIG["executable"]')

        # If we get this far, the executable is external. Test that it can be executed
        # and capture stdout and stderr so they don't end up in the system log.
        try:
            args = [self.executable]
            args.extend(self.test_existence_args)
            subprocess.Popen(args, startupinfo=self.get_startupinfo(),
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()
        except OSError:
            return (False, '"{0}" cannot be found'.format(self.executable))

        return (True, 'using "{0}" for executable'.format(self.executable))

    def _get_lint_args(self, view, code, filename):
        if hasattr(self, 'get_lint_args'):
            return self.get_lint_args(view, code, filename) or []
        else:
            lintArgs = self.lint_args or []
            settings = view.settings().get('SublimeLinter', {}).get(self.language, {})

            if settings:
                args = settings.get('lint_args', [])
                lintArgs.extend(args)

                cwd = settings.get('working_directory')

                if cwd and os.path.isabs(cwd) and os.path.isdir(cwd):
                    os.chdir(cwd)

            return [arg.format(filename=filename) for arg in lintArgs]

    def built_in_check(self, view, code, filename):
        return ''

    def executable_check(self, view, code, filename):
        args = [self.executable]
        tempfilePath = None

        if self.input_method == INPUT_METHOD_STDIN:
            args.extend(self._get_lint_args(view, code, filename))

        elif self.input_method == INPUT_METHOD_TEMP_FILE:
            if filename:
                filename = os.path.basename(filename)
            else:
                filename = 'view{0}'.format(view.id())

            tempfilePath = os.path.join(TEMPFILES_DIR, filename)

            with open(tempfilePath, 'w') as f:
                f.write(code)

            args.extend(self._get_lint_args(view, code, tempfilePath))
            code = ''

        elif self.input_method == INPUT_METHOD_FILE:
            args.extend(self._get_lint_args(view, code, filename))
            code = ''

        else:
            return ''

        try:
            process = subprocess.Popen(args,
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       startupinfo=self.get_startupinfo())
            result = process.communicate(code)[0]
        finally:
            if tempfilePath:
                os.remove(tempfilePath)

        return result.strip()

    def parse_errors(self, view, errors, lines, errorUnderlines, violationUnderlines, warningUnderlines, errorMessages, violationMessages, warningMessages):
        pass

    def add_message(self, lineno, lines, message, messages):
        # Assume lineno is one-based, ST2 wants zero-based line numbers
        lineno -= 1
        lines.add(lineno)
        message = message[0].upper() + message[1:]

        # Remove trailing period from error message
        if message[-1] == '.':
            message = message[:-1]

        if lineno in messages:
            messages[lineno].append(message)
        else:
            messages[lineno] = [message]

    def underline_range(self, view, lineno, position, underlines, length=1):
        # Assume lineno is one-based, ST2 wants zero-based line numbers
        lineno -= 1
        line = view.full_line(view.text_point(lineno, 0))
        position += line.begin()

        for i in xrange(length):
            underlines.append(sublime.Region(position + i))

    def underline_regex(self, view, lineno, regex, lines, underlines, wordmatch=None, linematch=None):
        # Assume lineno is one-based, ST2 wants zero-based line numbers
        lineno -= 1
        lines.add(lineno)
        offset = 0
        line = view.full_line(view.text_point(lineno, 0))
        lineText = view.substr(line)

        if linematch:
            match = re.match(linematch, lineText)

            if match:
                lineText = match.group('match')
                offset = match.start('match')
            else:
                return

        iters = re.finditer(regex, lineText)
        results = [(result.start('underline'), result.end('underline')) for result in iters
                    if not wordmatch or result.group('underline') == wordmatch]

        # Make the lineno one-based again for underline_range
        lineno += 1

        for start, end in results:
            self.underline_range(view, lineno, start + offset, underlines, end - start)

    def underline_word(self, view, lineno, position, underlines):
        # Assume lineno is one-based, ST2 wants zero-based line numbers
        lineno -= 1
        line = view.full_line(view.text_point(lineno, 0))
        position += line.begin()

        word = view.word(position)
        underlines.append(word)

    def run(self, view, code, filename=None):
        self.filename = filename

        if self.executable is None:
            errors = self.built_in_check(view, code, filename)
        else:
            errors = self.executable_check(view, code, filename)

        lines = set()
        errorUnderlines = []  # leave this here for compatibility with original plugin
        errorMessages = {}
        violationUnderlines = []
        violationMessages = {}
        warningUnderlines = []
        warningMessages = {}

        self.parse_errors(view, errors, lines, errorUnderlines, violationUnderlines, warningUnderlines, errorMessages, violationMessages, warningMessages)
        return lines, errorUnderlines, violationUnderlines, warningUnderlines, errorMessages, violationMessages, warningMessages

    def get_mapped_executable(self, view, default):
        map = view.settings().get('sublimelinter_executable_map')

        if map:
            lang = self.language.lower()

            if lang in map:
                return map[lang]

        return default

    def get_startupinfo(self):
        info = None

        if os.name == 'nt':
            info = subprocess.STARTUPINFO()
            info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            info.wShowWindow = subprocess.SW_HIDE

        return info

    def execute_get_output(self, args):
        try:
            return subprocess.Popen(args, self.get_startupinfo()).communicate()[0]
        except:
            return ''

    def jsc_path(self):
        '''Return the path to JavaScriptCore. Use this method in case the path
           has to be dynamically calculated in the future.'''
        return self.JSC_PATH

    def find_file(self, filename, view):
        '''Find a file with the given name, starting in the view's directory,
           then ascending the file hierarchy up to root.'''
        path = view.file_name()

        # quit if the view is temporary
        if not path:
            return None

        dirname = os.path.dirname(path)

        while True:
            path = os.path.join(dirname, filename)

            if os.path.isfile(path):
                with open(path, 'r') as f:
                    return f.read()

            # if we hit root, quit
            parent = os.path.dirname(dirname)

            if parent == dirname:
                return None
            else:
                dirname = parent

    def strip_json_comments(self, json_str):
        stripped_json = JSON_MULTILINE_COMMENT_RE.sub('', json_str)
        stripped_json = JSON_SINGLELINE_COMMENT_RE.sub('', stripped_json)
        return json.dumps(json.loads(stripped_json))

    def get_javascript_args(self, view, linter, code):
        path = os.path.join(self.LIB_PATH, linter)
        options = self.get_javascript_options(view)

        if options == None:
            options = json.dumps(view.settings().get('%s_options' % linter) or {})

        self.get_javascript_engine(view)
        engine = self.js_engine

        if (engine['name'] == 'jsc'):
            args = [engine['wrapper'], '--', path + os.path.sep, str(code.count('\n')), options]
        else:
            args = [engine['wrapper'], path + os.path.sep, options]

        return args

    def get_javascript_options(self, view):
        '''Subclasses should override this if they want to provide options
           for a Javascript-based linter. If the subclass cannot provide
           options, it should return None (or not return anything).'''
        return None

    def get_javascript_engine(self, view):
        if self.js_engine == None:
            for engine in self.JAVASCRIPT_ENGINES:
                if engine == 'node':
                    try:
                        path = self.get_mapped_executable(view, 'node')
                        subprocess.call([path, '-v'], startupinfo=self.get_startupinfo())
                        self.js_engine = {
                            'name': engine,
                            'path': path,
                            'wrapper': os.path.join(self.JAVASCRIPT_ENGINE_WRAPPERS_PATH, engine + '.js'),
                        }
                        break
                    except OSError:
                        pass

                elif engine == 'jsc':
                    if os.path.exists(self.jsc_path()):
                        self.js_engine = {
                            'name': engine,
                            'path': self.jsc_path(),
                            'wrapper': os.path.join(self.JAVASCRIPT_ENGINE_WRAPPERS_PATH, engine + '.js'),
                        }
                        break

        if self.js_engine != None:
            return (True, self.js_engine['path'], 'using {0}'.format(self.JAVASCRIPT_ENGINE_NAMES[self.js_engine['name']]))

        # Didn't find an engine, tell the user
        engine_list = ', '.join(self.JAVASCRIPT_ENGINE_NAMES.values())
        return (False, '', 'One of the following Javascript engines must be installed: ' + engine_list)
