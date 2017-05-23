# coding=utf-8
import vdebug.log
import vdebug.opts
import vim
import re

class Dispatcher:
    def __init__(self,runner):
        self.runner = runner

    def visual_eval(self):
        if self.runner.is_alive():
            event = VisualEvalEvent()
            return event.execute(self.runner)

    def eval_under_cursor(self):
        if self.runner.is_alive():
            event = CursorEvalEvent()
            return event.execute(self.runner)

    def by_position(self):
        if self.runner.is_alive():
            event = self._get_event_by_position()
            if event is not None:
                return event.execute(self.runner)
            else:
                vdebug.log.Log("No executable event found at current cursor position",\
                        vdebug.log.Logger.DEBUG)
                return False

    def _get_event_by_position(self):
        buf_name = vim.current.buffer.name
        p = re.compile('.*[\\\/]([^\\\/]+)')
        m = p.match(buf_name)
        if m is None:
            return None

        window_name = m.group(1)
        if window_name == self.runner.ui.watchwin.name:
            lineno = vim.current.window.cursor[0]
            vdebug.log.Log("User action in watch window, line %s" % lineno,\
                    vdebug.log.Logger.DEBUG)
            line = self.runner.ui.watchwin.buffer[lineno-1].strip()
            if lineno == 1:
                return WatchWindowContextChangeEvent()
            elif line.startswith(vdebug.opts.Options.get('marker_closed_tree')):
                return WatchWindowPropertyGetEvent()
            elif line.startswith(vdebug.opts.Options.get('marker_open_tree')):
                return WatchWindowHideEvent()
        elif window_name == self.runner.ui.stackwin.name:
            return StackWindowLineSelectEvent()

class Event:
    """Base event class.
    """
    def execute(self,runner):
        pass

class VisualEvalEvent(Event):
    """Evaluate a block of code given by visual selection in Vim.
    """
    def execute(self,runner):
        selection = vim.eval("Vdebug_get_visual_selection()")
        runner.eval(selection)
        return True

class CursorEvalEvent(Event):
    """Evaluate the variable currently under the cursor.
    """
    char_regex = {
        "default" : "a-zA-Z0-9_.\[\]'\"",
        "ruby" : "$@a-zA-Z0-9_.\[\]'\"",
        "perl" : "$a-zA-Z0-9_{}'\"",
        "php" : "$@%a-zA-Z0-9_\[\]'\"\->"
    }

    var_regex = {
        "default" : "^[a-zA-Z_]",
        "ruby" : "^[$@a-zA-Z_]",
        "php" : "^[\$A-Z]",
        "perl" : "^[$@%]"
    }

    def execute(self,runner):
        lineno = vim.current.window.cursor[0]
        colno = vim.current.window.cursor[1]
        line = vim.current.buffer[lineno-1]
        lang = runner.api.language
        if lang in self.char_regex:
            reg = self.char_regex[lang]
        else:
            reg = self.char_regex['default']

        p = re.compile('['+reg+']')
        var = ""
        linelen = len(line)

        for i in range(colno,linelen):
            char = line[i]
            if p.match(char):
                var += char
            else:
                break

        if colno > 0:
            for i in range(colno-1,-1,-1):
                char = line[i]
                if p.match(char):
                    var = char + var
                else:
                    break

        if lang in self.var_regex:
            reg = self.var_regex[lang]
        else:
            reg = self.var_regex["default"]

        f = re.compile(reg)
        if f.match(var) is None:
            runner.ui.error("Cannot find a valid variable under the cursor")
            return False

        if len(var):
            runner.eval(var)
            return True
        else:
            runner.ui.error("Cannot find a valid variable under the cursor")
            return False

class StackWindowLineSelectEvent(Event):
    """Move the the currently selected file and line in the stack window
    """
    def execute(self,runner):
        lineno = vim.current.window.cursor[0]

        vdebug.log.Log("User action in stack window, line %s" % lineno,\
                vdebug.log.Logger.DEBUG)
        line = runner.ui.stackwin.buffer[lineno-1]
        if line.find(" @ ") == -1:
            return False
        filename_pos = line.find(" @ ") + 3
        file_and_line = line[filename_pos:]
        line_pos = file_and_line.rfind(":")
        file = vdebug.util.LocalFilePath(file_and_line[:line_pos])
        lineno = file_and_line[line_pos+1:]
        runner.ui.sourcewin.set_file(file)
        runner.ui.sourcewin.set_line(lineno)

class WatchWindowPropertyGetEvent(Event):
    """Open a tree node in the watch window.

    This retrieves the child nodes and displays them underneath.
    """
    def execute(self,runner):
        lineno = vim.current.window.cursor[0]
        line = vim.current.buffer[lineno-1]
        pointer_index = line.find(vdebug.opts.Options.get('marker_closed_tree'))
        step = len(vdebug.opts.Options.get('marker_closed_tree')) + 1

        eq_index = line.find('=')
        if eq_index == -1:
            raise EventError("Cannot read the selected property")

        name = line[pointer_index+step:eq_index-1]
        context_res = runner.api.property_get(name)
        rend = vdebug.ui.vimui.ContextGetResponseRenderer(context_res)
        output = rend.render(pointer_index - 1)
        if vdebug.opts.Options.get('watch_window_style') == 'expanded':
          runner.ui.watchwin.delete(lineno,lineno+1)
        runner.ui.watchwin.insert(output.rstrip(),lineno-1,True)

class WatchWindowHideEvent(Event):
    """Close a tree node in the watch window.
    """
    def execute(self,runner):
        lineno = vim.current.window.cursor[0]
        line = vim.current.buffer[lineno-1]
        pointer_index = line.find(vdebug.opts.Options.get('marker_open_tree'))

        buf_len = len(vim.current.buffer)
        end_lineno = buf_len - 1
        for i in range(lineno,end_lineno):
            buf_line = vim.current.buffer[i]
            char = buf_line[pointer_index]
            if char != " ":
                end_lineno = i - 1
                break
        runner.ui.watchwin.delete(lineno,end_lineno+1)
        if vdebug.opts.Options.get('watch_window_style') == 'expanded':
            append = "\n" + "".rjust(pointer_index) + "|"
        else:
            append = ""
        runner.ui.watchwin.insert(line.replace(\
                    vdebug.opts.Options.get('marker_open_tree'),\
                    vdebug.opts.Options.get('marker_closed_tree'),1) + \
                append,lineno-1,True)

class WatchWindowContextChangeEvent(Event):
    """Event used to trigger a watch window context change.

    The word under the VIM cursor is retrieved, and context_get called with the
    new context name.
    """

    def execute(self,runner):
        column = vim.current.window.cursor[1]
        line = vim.current.buffer[0]

        vdebug.log.Log("Finding context name at column %s" % column,\
                vdebug.log.Logger.DEBUG)

        tab_end_pos = self.__get_word_end(line,column)
        tab_start_pos = self.__get_word_start(line,column)

        if tab_end_pos == -1 or \
                tab_start_pos == -1:
            raise EventError("Failed to find context name under cursor")

        context_name = line[tab_start_pos:tab_end_pos]
        vdebug.log.Log("Context name: %s" % context_name,\
                vdebug.log.Logger.DEBUG)
        if context_name[0] == '*':
            runner.ui.say("This context is already showing")
            return False

        context_id = self.__determine_context_id(\
                runner.context_names,context_name)

        if context_id == -1:
            raise EventError("Could not resolve context name")
            return False
        else:
            runner.get_context(context_id)
            return True

    def __get_word_end(self,line,column):
        tab_end_pos = -1
        line_len = len(line)
        i = column
        while i < line_len:
            if line[i] == ']':
                tab_end_pos = i-1
                break
            i += 1
        return tab_end_pos

    def __get_word_start(self,line,column):
        tab_start_pos = -1
        j = column
        while j >= 0:
            if line[j] == '[':
                tab_start_pos = j+2
                break
            j -= 1
        return tab_start_pos

    def __determine_context_id(self,context_names,context_name):
        found_id = -1
        for id in context_names.keys():
            name = context_names[id]
            vdebug.log.Log(name +", "+context_name)
            if name == context_name:
                found_id = id
                break
        return found_id

class EventError(Exception):
    pass
