# coding=utf-8
import vdebug.ui.interface
import vdebug.util
import vim
import vdebug.log
import vdebug.opts

class Ui(vdebug.ui.interface.Ui):
    """Ui layer which manages the Vim windows.
    """

    def __init__(self,breakpoints):
        vdebug.ui.interface.Ui.__init__(self)
        self.is_open = False
        self.breakpoint_store = breakpoints
        self.emptybuffer = None
        self.breakpointwin = BreakpointWindow(self,'rightbelow 7new')
        self.current_tab = "1"
        self.tabnr = None

    def is_modified(self):
       modified = int(vim.eval('&mod'))
       if modified:
           return True
       else:
           return False

    def open(self):
        if self.is_open:
            return
        self.is_open = True

        try:
            existing_buffer = True
            cur_buf_name = vim.eval("bufname('%')")
            if cur_buf_name is None:
                existing_buffer = False
                cur_buf_name = ''

            self.current_tab = vim.eval("tabpagenr()")

            vim.command('silent tabnew')
            self.empty_buf_num = vim.eval('bufnr("%")')
            if existing_buffer:
                vim.command('call Vdebug_edit("%s")' % cur_buf_name)

            self.tabnr = vim.eval("tabpagenr()")

            srcwin_name = self.__get_srcwin_name()


            self.watchwin = WatchWindow(self,'vertical belowright new')
            self.watchwin.create()

            self.stackwin = StackWindow(self,'belowright new')
            self.stackwin.create()

            self.statuswin = StatusWindow(self,'belowright new')
            self.statuswin.create()
            self.statuswin.set_status("loading")

            self.tracewin = TraceWindow(self,'rightbelow 7new')

            self.watchwin.set_height(20)
            self.statuswin.set_height(5)

            logwin = LogWindow(self,'rightbelow 6new')

            vdebug.log.Log.set_logger(\
                    vdebug.log.WindowLogger(\
                    vdebug.opts.Options.get('debug_window_level'),\
                    logwin))

            winnr = self.__get_srcwinno_by_name(srcwin_name)
            self.sourcewin = SourceWindow(self,winnr)
            self.sourcewin.focus()
        except Exception, e:
            self.is_open = False
            raise e

    def set_source_position(self,file,lineno):
        self.sourcewin.set_file(file)
        self.sourcewin.set_line(lineno)
        self.sourcewin.place_pointer(lineno)

    def mark_as_stopped(self):
        if self.is_open:
            if self.sourcewin:
                self.sourcewin.remove_pointer()
            if self.statuswin:
                self.statuswin.set_status("stopped")
                self.remove_conn_details()

    def set_conn_details(self,addr,port):
        self.statuswin.insert("Connected to %s:%s" %(addr,port),2,True)

    def remove_conn_details(self):
        self.statuswin.insert("Not connected",2,True)

    def set_listener_details(self,addr,port,idekey):
        details = "Listening on %s:%s" %(addr,port)
        if len(idekey):
            details += " (IDE key: %s)" % idekey
        self.statuswin.insert(details,1,True)

    def get_current_file(self):
        return vdebug.util.LocalFilePath(vim.current.buffer.name)

    def get_current_row(self):
        return vim.current.window.cursor[0]

    def get_current_line(self):
        return self.get_line(self.get_current_row())

    def get_line(self,row):
        return vim.eval("getline(" + str(row) + ")")

    def register_breakpoint(self,breakpoint):
        if breakpoint.type == 'line':
            self.place_breakpoint(breakpoint.id,\
                    breakpoint.file,breakpoint.line)
        if self.breakpointwin.is_open:
            self.breakpointwin.add_breakpoint(breakpoint)

    def place_breakpoint(self,sign_id,file,line):
        vim.command('sign place '+str(sign_id)+\
                ' name=breakpt line='+str(line)+\
                ' file='+file.as_local())

    def remove_breakpoint(self,breakpoint):
        id = breakpoint.id
        vim.command('sign unplace %i' % id)
        if self.breakpointwin.is_open:
            self.breakpointwin.remove_breakpoint(id)

    def get_breakpoint_sign_positions(self):
        sign_lines = self.command('sign place').split("\n")
        positions = {}
        for line in sign_lines:
            if "name=breakpt" in line:
                attributes = line.strip().split()
                lineinfo = attributes[0].split('=')
                idinfo = attributes[1].split('=')
                positions[idinfo[1]] = lineinfo[1]
        return positions

    # Execute a vim command and return the output.
    def command(self,cmd):
        vim.command('redir => _tmp')
        vim.command('silent %s' % cmd)
        vim.command('redir END')
        return vim.eval('_tmp')

    def say(self,string):
        """ Vim picks up Python prints, so just print """
        print str(string)
        vdebug.log.Log(string,vdebug.log.Logger.INFO)

    def error(self,string):
        vim.command('echohl Error | echo "'+\
                str(string).replace('"','\\"')+\
                '" | echohl None')
        vdebug.log.Log(string,vdebug.log.Logger.ERROR)

    def close(self):
        if not self.is_open:
            return
        self.is_open = False

        vdebug.log.Log.remove_logger('WindowLogger')
        if self.tabnr:
            vim.command('silent! '+self.tabnr+'tabc!')
        if self.current_tab:
            vim.command('tabn '+self.current_tab)

        if self.empty_buf_num:
            vim.command('bw' + self.empty_buf_num)

        if self.watchwin:
            self.watchwin.destroy()
        if self.stackwin:
            self.stackwin.destroy()
        if self.statuswin:
            self.statuswin.destroy()
        if self.tracewin:
            self.tracewin.destroy()

        self.watchwin  = None
        self.stackwin  = None
        self.statuswin = None
        self.tracewin  = None


    def __get_srcwin_name(self):
        return vim.current.buffer.name

    def __get_srcwinno_by_name(self,name):
        i = 1
        vdebug.log.Log("Searching for win by name %s" % name,\
                vdebug.log.Logger.INFO)
        for w in vim.windows:
            vdebug.log.Log("Win %d, name %s" %(i,w.buffer.name),\
                vdebug.log.Logger.INFO)
            if w.buffer.name == name:
                break
            else:
                i += 1

        vdebug.log.Log("Returning window number %d" % i,\
                vdebug.log.Logger.INFO)
        return i

    def __get_buf_list(self):
        return vim.eval("range(1, bufnr('$'))")

class SourceWindow(vdebug.ui.interface.Window):

    file = None
    pointer_sign_id = '6145'
    breakpoint_sign_id = '6146'

    def __init__(self,ui,winno):
        self.winno = str(winno)

    def focus(self):
        vim.command(self.winno+"wincmd w")

    def command(self,cmd,silent = True):
        self.focus()
        if silent:
            prepend = "silent "
        else:
            prepend = ""
        command_str = prepend + self.winno + "wincmd " + cmd
        vim.command(command_str)

    def set_file(self,file):
        if file == self.file:
            return
        self.file = file
        vdebug.log.Log("Setting source file: "+file,vdebug.log.Logger.INFO)
        self.focus()
        vim.command('call Vdebug_edit("%s")' % str(file).replace("\\", "\\\\"))

    def set_line(self,lineno):
        self.focus()
        vim.command("normal %sgg" % str(lineno))

    def get_file(self):
        self.focus()
        self.file = vdebug.util.LocalFilePath(vim.eval("expand('%:p')"))
        return self.file

    def clear_signs(self):
        vim.command('sign unplace *')

    def place_pointer(self,line):
        vdebug.log.Log("Placing pointer sign on line "+str(line),\
                vdebug.log.Logger.INFO)
        self.remove_pointer()
        vim.command('sign place '+self.pointer_sign_id+\
                ' name=current line='+str(line)+\
                ' file='+self.file)

    def remove_pointer(self):
        vim.command('sign unplace %s' % self.pointer_sign_id)

class Window(vdebug.ui.interface.Window):
    name = "WINDOW"
    open_cmd = "new"
    creation_count = 0

    def __init__(self,ui,open_cmd):
        self.buffer = None
        self.ui = ui
        self.open_cmd = open_cmd
        self.is_open = False

    def getwinnr(self):
        return int(vim.eval("bufwinnr('"+self.name+"')"))

    def set_height(self,height):
        height = int(height)
        minheight = int(vim.eval("&winminheight"))
        if height < minheight:
            height = minheight
        if height <= 0:
            height = 1
        self.command('set winheight=%i' % height)

    def write(self, msg, return_focus = True, after = "normal G"):
        if not self.is_open:
            self.create()
        if return_focus:
            prev_win = vim.eval('winnr()')
        if self.buffer_empty():
            self.buffer[:] = str(msg).split('\n')
        else:
            self.buffer.append(str(msg).split('\n'))
        self.command(after)
        if return_focus:
            vim.command('%swincmd W' % prev_win)

    def insert(self, msg, lineno = None, overwrite = False, allowEmpty = False):
        if not self.is_open:
            self.create()
        """ insert into current position in buffer"""
        if len(msg) == 0 and allowEmpty == False:
            return
        if self.buffer_empty():
            self.buffer[:] = str(msg).split('\n')
        else:
            if lineno == None:
                (lineno, rol) = vim.current.window.cursor
            remaining_buffer = str(msg).split('\n')
            if overwrite:
                lfrom = lineno + 1
            else:
                lfrom = lineno
            remaining_buffer.extend(self.buffer[lfrom:])
            del self.buffer[lineno:]
            if self.buffer_empty():
                self.buffer[:] = remaining_buffer
            else:
                for line in remaining_buffer:
                    self.buffer.append(line)
            self.command(str(lfrom))

    def delete(self,start_line,end_line):
        try:
            self.buffer[end_line]
            remaining_buffer = self.buffer[end_line:]
            del self.buffer[start_line:]
            self.buffer.append(remaining_buffer)
        except IndexError:
            del self.buffer[start_line:]

    def buffer_empty(self):
        if len(self.buffer) == 1 \
                and len(self.buffer[0]) == 0:
            return True
        else:
            return False

    def create(self):
        """ create window """
        vim.command('silent ' + self.open_cmd + ' ' + self.name)
        vim.command("setlocal buftype=nofile modifiable "+ \
                "winfixheight winfixwidth")
        self.buffer = vim.current.buffer
        self.is_open = True
        self.creation_count += 1
        self.on_create()

    def destroy(self):
        """ destroy window """
        if self.buffer == None or len(dir(self.buffer)) == 0:
            return
        self.is_open = False
        if int(vim.eval('buffer_exists("'+self.name+'")')) == 1:
            vim.command('bwipeout ' + self.name)
        self.on_destroy()

    def clean(self):
        """ clean all datas in buffer """
        if self.is_open:
            self.buffer[:] = []

    def command(self, cmd):
        """ go to my window & execute command """
        winnr = self.getwinnr()
        if winnr != int(vim.eval("winnr()")):
            vim.command(str(winnr) + 'wincmd w')
        vim.command(cmd)

    def accept_renderer(self,renderer):
        self.write(renderer.render())

class BreakpointWindow(Window):
    name = "DebuggerBreakpoints"
    is_visible = False
    header = """===========================================================
 ID      | TYPE        | DATA
==========================================================="""

    def on_create(self):
        self.clean()
        self.write(self.header)
        self.command('setlocal syntax=debugger_breakpoint')
        for bp in self.ui.breakpoint_store.get_sorted_list():
            self.add_breakpoint(bp)
        if self.creation_count == 1:
            cmd = 'silent! au BufWinLeave %s :silent! bdelete %s' %(self.name,self.name)
            vim.command('%s | python debugger.runner.ui.breakpointwin.is_open = False' % cmd)

    def add_breakpoint(self,breakpoint):
        bp_str = " %-7i | %-11s | " %(breakpoint.id,breakpoint.type)
        if breakpoint.type == 'line':
            bp_str += "%s:%s" %(breakpoint.file,str(breakpoint.line))
        elif breakpoint.type == 'conditional':
            bp_str += "%s:%s when (%s)" \
                %(breakpoint.file,str(breakpoint.line),breakpoint.condition)
        elif breakpoint.type == 'exception':
            bp_str += "Exception: %s" % breakpoint.exception
        elif breakpoint.type == 'call' or \
                breakpoint.type == 'return':
            bp_str += "Function: %s" % breakpoint.function

        self.write(bp_str)

    def remove_breakpoint(self,breakpoint_id):
        i = 0
        for l in self.buffer:
            bp_str = " %i " % breakpoint_id
            bp_id_len = len(bp_str)
            if l[:bp_id_len] == bp_str:
                del self.buffer[i]
            i += 1

class LogWindow(Window):
    name = "DebuggerLog"

    def on_create(self):
        self.command('setlocal syntax=debugger_log')
        if self.creation_count == 1:
            cmd = 'silent! au BufWinLeave %s :silent! bdelete %s' %(self.name,self.name)
            vim.command('%s | python vdebug.log.Log.remove_logger("WindowLogger")' % cmd)

    def write(self, msg, return_focus = True):
        Window.write(self, msg,return_focus=True)

class StackWindow(Window):
    name = "DebuggerStack"

    def on_create(self):
        self.command('inoremap <buffer> <cr> <esc>'+\
                ':python debugger.handle_return_keypress()<cr>')
        self.command('nnoremap <buffer> <cr> '+\
                ':python debugger.handle_return_keypress()<cr>')
        self.command('nnoremap <buffer> <2-LeftMouse> '+\
                ':python debugger.handle_double_click()<cr>')
        self.command('setlocal syntax=debugger_stack')
        if self.creation_count == 1:
            cmd = 'silent! au BufWinLeave %s :silent! bdelete %s' %(self.name,self.name)
            vim.command('%s | python debugger.runner.ui.stackwin.is_open = False' % cmd)

    def write(self, msg, return_focus = True):
        Window.write(self, msg, after="normal gg")

class WatchWindow(Window):
    name = "DebuggerWatch"

    def on_create(self):
        self.command('inoremap <buffer> <cr> <esc>'+\
                ':python debugger.handle_return_keypress()<cr>')
        self.command('nnoremap <buffer> <cr> '+\
                ':python debugger.handle_return_keypress()<cr>')
        self.command('nnoremap <buffer> <2-LeftMouse> '+\
                ':python debugger.handle_double_click()<cr>')
        self.command('setlocal syntax=debugger_watch')
        if self.creation_count == 1:
            cmd = 'silent! au BufWinLeave %s :silent! bdelete %s' %(self.name,self.name)
            vim.command('%s | python debugger.runner.ui.watchwin.is_open = False' % cmd)

    def write(self, msg, return_focus = True):
        Window.write(self, msg, after="normal gg")

class StatusWindow(Window):
    name = "DebuggerStatus"

    def on_create(self):
        keys = vdebug.util.Keymapper()
        output = "Status: starting\nListening on port\nNot connected\n\n"
        output += "Press %s to start debugging, " %(keys.run_key())
        output += "%s to stop/close. " %(keys.close_key())
        output += "Type :help Vdebug for more information."

        self.write(output)

        self.command('setlocal syntax=debugger_status')
        if self.creation_count == 1:
            cmd = 'au BufWinLeave %s :silent! bdelete %s' %(self.name,self.name)
            vim.command('%s | python debugger.runner.ui.statuswin.is_open = False' % cmd)

    def set_status(self,status):
        self.insert("Status: "+str(status),0,True)

class TraceWindow(WatchWindow):
    name = "DebuggerTrace"

    def on_create(self):
        if self.creation_count == 1:
            cmd = 'silent! au BufWinLeave %s :silent! bdelete %s' %(self.name,self.name)
            vim.command('%s | python debugger.runner.ui.tracewin.is_open = False' % cmd)
        self.command('setlocal syntax=debugger_watch')

    def set_trace_expression(self, trace_expression):
        self._trace_expression = trace_expression

    def is_tracing(self):
        if self.is_open:
            return self._trace_expression is not None

    def get_trace_expression(self):
        return self._trace_expression

    def render(self, renderer):
        self._last_context_rendered = renderer
        self.accept_renderer(renderer)

    def render_in_error_case(self):
        if self._last_context_rendered is None:
            self.write(str(self._trace_expression))
        else:
            self.write('(prev)' + str(self._last_context_rendered))

    def on_destroy(self):
        self._trace_expression = None
        self._last_context_rendered = None


class ResponseRenderer:
    def __init__(self,response):
        self.response = response

    def render(self):
        pass

class StackGetResponseRenderer(ResponseRenderer):
    def render(self):
        stack = self.response.get_stack()
        string = ""
        for s in stack:
            if s.get('where'):
                where = s.get('where')
            else:
                where = 'main'
            file = vdebug.util.FilePath(s.get('filename'))
            line = "[%(num)s] %(where)s @ %(file)s:%(line)s" \
                    %{'num':s.get('level'),'where':where,\
                    'file':str(file.as_local()),'line':s.get('lineno')}
            string += line + "\n"
        return string


class ContextGetResponseRenderer(ResponseRenderer):

    def __init__(self,response,title = None,contexts = {},current_context = 0):
        ResponseRenderer.__init__(self,response)
        self.title = title
        self.contexts = contexts
        self.current_context = current_context

    def render(self,indent = 0):
        res = self.__create_tabs()

        if self.title:
            res += "- %s\n\n" % self.title

        properties = self.response.get_context()
        num_props = len(properties)
        vdebug.log.Log("Writing %i properties to the context window" % num_props,\
                vdebug.log.Logger.INFO )
        for idx, prop in enumerate(properties):
            final = False
            try:
                next_prop = properties[idx+1]
            except IndexError:
                final = True
                next_prop = None
            res += self.__render_property(prop,next_prop,final,indent)

        vdebug.log.Log("Writing to context window:\n"+res,vdebug.log.Logger.DEBUG)

        return res

    def __create_tabs(self):
        res = []
        if self.contexts:
            for id,name in self.contexts.iteritems():
                if self.current_context == id:
                    name = "*"+name
                res.append("[ %s ]" % name)
        if res:
            return " ".join(res) + "\n\n"
        else:
            return ""

    def __render_property(self,p,next_p,last = False,indent = 0):
        line = "%(indent)s %(marker)s %(name)s = (%(type)s)%(value)s" \
                %{'indent':"".rjust((p.depth * 2)+indent),\
                'marker':self.__get_marker(p),'name':p.display_name.encode('latin1'),\
                'type':p.type_and_size(),'value': " " + p.value}
        line = line.rstrip() + "\n"

        if vdebug.opts.Options.get('watch_window_style') == 'expanded':
            depth = p.depth
            if next_p and not last:
                next_depth = next_p.depth
                if depth == next_depth:
                    next_sep = "|"
                    num_spaces = depth * 2
                elif depth > next_depth:
                    if not p.is_last_child:
                       line += "".rjust(depth * 2 +indent) + " |\n"
                       line += "".rjust(depth * 2 +indent) + " ...\n"
                    next_sep = "/"
                    num_spaces = (depth * 2) - 1
                else:
                    next_sep = "\\"
                    num_spaces = (depth * 2) + 1

                line += "".rjust(num_spaces+indent) + " " + next_sep + "\n"
            elif depth > 0:
                if not p.is_last_child:
                   line += "".rjust(depth * 2 +indent) + " |\n"
                   line += "".rjust(depth * 2 +indent) + " ...\n"
                line += "".rjust((depth * 2) - 1 + indent) + " /" + "\n"
        return line

    def __get_marker(self,property):
        char = vdebug.opts.Options.get('marker_default')
        if property.has_children:
            if property.child_count() == 0:
                char = vdebug.opts.Options.get('marker_closed_tree')
            else:
                char = vdebug.opts.Options.get('marker_open_tree')
        return char
