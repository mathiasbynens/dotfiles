# coding=utf-8

import vdebug.dbgp
import vdebug.log
import vdebug.ui.vimui
import socket
import vim
import vdebug.breakpoint
import vdebug.opts
import vdebug.util

class Runner:
    """ Class that stitches together all the debugger components.

    This instantiates the connection and debugger vdebug.ui, and provides
    an interface that Vim can use to send commands.
    """

    def __init__(self):
        self.api = None
        vdebug.opts.Options.set(vim.eval('g:vdebug_options'))
        self.breakpoints = vdebug.breakpoint.Store()
        self.keymapper = vdebug.util.Keymapper()
        self.ui = vdebug.ui.vimui.Ui(self.breakpoints)
        self.saved_code = ''

    def open(self):
        """ Open the connection and debugging vdebug.ui.

        If either of these are already open, the current
        connection or vdebug.ui is used.
        """
        try:
            if self.ui.is_modified():
                self.ui.error("Modified buffers must be saved before debugging")
                return
            vdebug.opts.Options.set(vim.eval('g:vdebug_options'))

            if vdebug.opts.Options.isset('debug_file'):
                vdebug.log.Log.set_logger(vdebug.log.FileLogger(\
                        vdebug.opts.Options.get('debug_file_level'),\
                        vdebug.opts.Options.get('debug_file')))
            self.listen(\
                    vdebug.opts.Options.get('server'),\
                    vdebug.opts.Options.get('port',int),\
                    vdebug.opts.Options.get('timeout',int))

            self.ui.open()
            self.keymapper.map()
            self.ui.set_listener_details(\
                    vdebug.opts.Options.get('server'),\
                    vdebug.opts.Options.get('port'),\
                    vdebug.opts.Options.get('ide_key'))

            addr = self.api.conn.address
            vdebug.log.Log("Found connection from " + str(addr),vdebug.log.Logger.INFO)
            self.ui.set_conn_details(addr[0],addr[1])

            self.set_features()
            self.breakpoints.update_lines(self.ui.get_breakpoint_sign_positions())
            self.breakpoints.link_api(self.api)

            cn_res = self.api.context_names()
            self.context_names = cn_res.names()
            vdebug.log.Log("Available context names: %s" %\
                    str(self.context_names),vdebug.log.Logger.DEBUG)

            if vdebug.opts.Options.get('break_on_open',int) == 1:
                status = self.api.step_into()
            else:
                status = self.api.run()
            self.refresh(status)
        except Exception:
            self.close()
            raise

    def set_features(self):
        """Evaluate vim dictionary of features and pass to debugger.

        Errors are caught if the debugger doesn't like the feature name or
        value. This doesn't break the loop, so multiple features can be set
        even in the case of an error."""
        features = vim.eval('g:vdebug_features')
        for name, value in features.iteritems():
            try:
                self.api.feature_set(name, value)
            except vdebug.dbgp.DBGPError, e:
                error_str = "Failed to set feature %s: %s" %(name,str(e.args[0]))
                self.ui.error(error_str)

    def save_code(self,code):
        """Save a code snippet for later display in the watch window.
        """
        self.saved_code = code
        return code

    def refresh(self,status):
        """The main action performed after a deubugger step.

        Updates the status window, current stack, source
        file and line and watch window."""
        if not self.is_alive():
            self.ui.error("Cannot update: no connection")
        else:

            if str(status) == "interactive":
                self.ui.error("Debugger engine says it is in interactive mode,"+\
                        "which is not supported: closing connection")
                self.close_connection()
            elif str(status) in ("stopping","stopped"):
                self.ui.statuswin.set_status("stopped")
                self.ui.say("Debugging session has ended")
                self.close_connection(False)
                if vdebug.opts.Options.get('continuous_mode', int) != 0:
                    self.open()
                    return
            else:
                vdebug.log.Log("Getting stack information")
                self.ui.statuswin.set_status(status)
                stack_res = self.update_stack()
                stack = stack_res.get_stack()

                self.cur_file = vdebug.util.RemoteFilePath(stack[0].get('filename'))
                self.cur_lineno = stack[0].get('lineno')

                vdebug.log.Log("Moving to current position in source window")
                self.ui.set_source_position(\
                        self.cur_file,\
                        self.cur_lineno)

                if self.saved_code != '':
                    self.eval(self.saved_code)
                else:
                    self.get_context(0)

    def get_context(self,context_id = 0):
        self.ui.watchwin.clean()
        self.ui.tracewin.clean()
        name = self.context_names[context_id]
        vdebug.log.Log("Getting %s variables" % name)
        context_res = self.api.context_get(context_id)

        rend = vdebug.ui.vimui.ContextGetResponseRenderer(\
                context_res,"%s at %s:%s" \
                %(name,self.ui.sourcewin.file,self.cur_lineno),\
                self.context_names, context_id)

        self.ui.watchwin.accept_renderer(rend)

        if self.ui.tracewin.is_tracing():
            try:
                context_res = self.api.eval(self.ui.tracewin.get_trace_expression())
                rend = vdebug.ui.vimui.ContextGetResponseRenderer(\
                        context_res,"Trace of: '%s'" \
                        %context_res.get_code())
                self.ui.tracewin.render(rend)
            except vdebug.dbgp.EvalError:
                self.ui.tracewin.render_in_error_case()


    def toggle_breakpoint_window(self):
        """Open or close the breakpoint window.

        The window appears as a horizontal split below the
        currently selected window."""
        if self.ui.breakpointwin.is_open:
            self.ui.breakpointwin.destroy()
        else:
            self.ui.breakpointwin.create()

    def is_alive(self):
        """Whether the connection is open."""
        if self.api is not None and \
            self.api.conn.isconnected():
                return True
        return False

    def run(self):
        """Tell the debugger to run.

        It will run until the end of the execution or until a
        breakpoint is reached."""
        if not self.is_alive():
            self.open()
        else:
            vdebug.log.Log("Running")
            self.ui.statuswin.set_status("running")
            res = self.api.run()
            self.refresh(res)

    def step_over(self):
        """Step over to the next statement."""
        if not self.is_alive():
            self.open()
        else:
            vdebug.log.Log("Stepping over")
            self.ui.statuswin.set_status("running")
            res = self.api.step_over()
            self.refresh(res)

    def step_into(self):
        """Step into the next statement."""
        if not self.is_alive():
            self.open()
        else:
            vdebug.log.Log("Stepping into statement")
            self.ui.statuswin.set_status("running")
            res = self.api.step_into()
            self.refresh(res)

    def step_out(self):
        """Step out of the current context."""
        if not self.is_alive():
            self.open()
        else:
            vdebug.log.Log("Stepping out of statement")
            self.ui.statuswin.set_status("running")
            res = self.api.step_out()
            self.refresh(res)

    def remove_breakpoint(self,args):
        """Remove a breakpoint, by ID or "*"."""
        if args is None:
            args = ""
        args = args.strip()
        if len(args) == 0:
            self.ui.error("ID or '*' required to remove a breakpoint: run "+\
                    "':BreakpointWindow' to see breakpoints and their IDs")
            return

        if args == '*':
            self.breakpoints.clear_breakpoints()
        else:
            arg_parts = args.split(" ")
            for id in arg_parts:
                self.breakpoints.remove_breakpoint_by_id(id)

    def set_breakpoint(self,args):
        bp = vdebug.breakpoint.Breakpoint.parse(self.ui,args)
        if bp.type == "line":
            id = self.breakpoints.find_breakpoint(\
                    bp.get_file(),\
                    bp.get_line())
            if id is not None:
                self.breakpoints.remove_breakpoint_by_id(id)
                return
        self.breakpoints.add_breakpoint(bp)

    def trace(self,code):
        """Evaluate a snippet of code and show the response on the watch window.
        """
        if not self.is_alive():
            self.ui.error("Tracing an expression is only possible when Vdebug is running")
            return
        if not code:
            self.ui.error("You must supply an expression to trace, with `:VdebugTrace expr`")
            return

        if self.ui.tracewin.is_open:
            self.ui.tracewin.clean()
        else:
            self.ui.tracewin.create()

        try:
            vdebug.log.Log("Tracing code: "+code)
            context_res = self.api.eval(code)
            rend = vdebug.ui.vimui.ContextGetResponseRenderer(\
                    context_res,"Eval of: '%s'" \
                    %context_res.get_code())
            self.ui.tracewin.accept_renderer(rend)
        except vdebug.dbgp.EvalError:
            self.ui.tracewin.write('(expression not currently valid)')
        self.ui.tracewin.set_trace_expression(code)

    def eval(self,code):
        """Evaluate a snippet of code and show the response on the watch window.
        """
        if not self.is_alive():
            self.ui.error("Evaluating code is only possible when Vdebug is running")
            return
        try:
            vdebug.log.Log("Evaluating code: "+code)
            context_res = self.api.eval(code)
            rend = vdebug.ui.vimui.ContextGetResponseRenderer(\
                    context_res,"Eval of: '%s'" \
                    %context_res.get_code())
            self.ui.watchwin.clean()
            self.ui.watchwin.accept_renderer(rend)
        except vdebug.dbgp.EvalError:
            self.ui.error("Failed to evaluate invalid code, '%s'" % code)

    def run_to_cursor(self):
        """Tell the debugger to run to the current cursor position.

        This fails if the current window is not the source window.
        """
        row = self.ui.get_current_row()
        file = self.ui.get_current_file()
        vdebug.log.Log(file)
        vdebug.log.Log(self.ui.sourcewin.get_file())
        if file != self.ui.sourcewin.get_file():
            self.ui.error("Run to cursor only works in the source window!")
            return
        vdebug.log.Log("Running to position: line %s of %s" %(row,file))
        bp = vdebug.breakpoint.TemporaryLineBreakpoint(self.ui,file,row)
        self.api.breakpoint_set(bp.get_cmd())
        self.run()

    def listen(self,server,port,timeout):
        """Open the vdebug.dbgp API with connection.

        Uses existing connection if possible.
        """
        if self.is_alive():
            vdebug.log.Log("Cannot open a new connection \
                while one already exists",\
                vdebug.log.Logger.ERROR)
            return
        else:
            while True:
                ide_key = vdebug.opts.Options.get('ide_key')
                check_ide_key = True
                if len(ide_key) == 0:
                    check_ide_key = False

                connection = vdebug.dbgp.Connection(server,port,\
                        timeout,vdebug.util.InputStream())

                self.api = vdebug.dbgp.Api(connection)
                if check_ide_key and ide_key != self.api.idekey:
                    print "Ignoring debugger connection with IDE key '%s'" \
                            % self.api.idekey
                    self.api.detach()
                else:
                    break

    def update_stack(self):
        """Update the stack window with the current stack info.
        """
        if not self.is_alive():
            self.ui.error("Cannot update the stack: no debugger connection")
        else:
            self.ui.stackwin.clean()
            res = self.api.stack_get()
            renderer = vdebug.ui.vimui.StackGetResponseRenderer(res)
            self.ui.stackwin.accept_renderer(renderer)
            return res

    def detach(self):
        """Detach the debugger engine, and allow it to continue execution.
        """
        if not self.is_alive():
            self.ui.error("Cannot detach: no debugger connection")
        else:
            self.ui.say("Detaching the debugger")
            self.api.detach()

    def close_connection(self,stop = True):
        """ Close the connection to the debugger.
        """
        self.breakpoints.unlink_api()
        self.ui.mark_as_stopped()
        try:
            if self.is_alive():
                vdebug.log.Log("Closing the connection")
                if stop:
                    if vdebug.opts.Options.get('on_close') == 'detach':
                        try:
                            self.api.detach()
                        except vdebug.dbgp.CmdNotImplementedError:
                            self.ui.error('Detach is not supported by the debugger, stopping instead')
                            vdebug.opts.Options.overwrite('on_close','stop')
                            self.api.stop()
                    else:
                        self.api.stop()
                self.api.conn.close()
                self.api = None
            else:
                self.api = None
        except EOFError:
            self.api = None
            self.ui.say("Connection has been closed")
        except socket.error:
            self.api = None
            self.ui.say("Connection has been closed")

    def close(self):
        """ Close both the connection and vdebug.ui.
        """
        self.close_connection()
        self.ui.close()
        self.keymapper.unmap()
