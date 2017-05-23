import sys
import os
import inspect

directory = os.path.dirname(inspect.getfile(inspect.currentframe()))
sys.path.append(directory)

import socket
import traceback
import vdebug.runner
import vdebug.event
import vim

class DebuggerInterface:
    """Acts as a facade layer to the debugger client.

    Most methods are just redirected to the Runner class. Fatal 
    exceptions are caught and handled here.
    """
    def __init__(self):
        self.runner = vdebug.runner.Runner()
        self.event_dispatcher = vdebug.event.Dispatcher(self.runner)

    def __del__(self):
        self.runner.close_connection()

    def run(self):
        """Tell the debugger to run, until the next breakpoint or end of script.
        """
        try:
            self.runner.run()
        except Exception, e:
            self.handle_exception(e)

    def run_to_cursor(self):
        """Run to the current VIM cursor position.
        """
        try:
            self.runner.run_to_cursor()
        except Exception, e:
            self.handle_exception(e)

    def step_over(self):
        """Step over to the next statement.
        """
        try:
            self.runner.step_over()
        except Exception, e:
            self.handle_exception(e)

    def step_into(self):
        """Step into a statement on the current line.
        """
        try:
            self.runner.step_into()
        except Exception, e:
            self.handle_exception(e)

    def step_out(self):
        """Step out of the current statement.
        """
        try:
            self.runner.step_out()
        except Exception, e:
            self.handle_exception(e)

    def handle_opt(self,option,value = None):
        """Set an option, overwriting the existing value.
        """
        try:
            if value is None:
                return self.runner.ui.say(vdebug.opts.Options.get_for_print(option))
            else:
                self.runner.ui.say("Setting vdebug option '%s' to: %s"\
                                    %(option,value))
                vim.command('let g:vdebug_options["%s"] = "%s"' %(option,value))
                return vdebug.opts.Options.overwrite(option,value)

        except Exception, e:
            self.handle_exception(e)


    def handle_return_keypress(self):
        """React to a <enter> keypress event.
        """
        try:
            return self.event_dispatcher.by_position()
        except Exception, e:
            self.handle_exception(e)

    def handle_double_click(self):
        """React to a mouse double click event.
        """
        try:
            return self.event_dispatcher.by_position()
        except Exception, e:
            self.handle_exception(e)

    def handle_visual_eval(self):
        """React to eval during visual selection.
        """
        try:
            return self.event_dispatcher.visual_eval()
        except Exception, e:
            self.handle_exception(e)

    def handle_trace(self,args = None):
        """Trace a code snippet specified by args.
        """
        try:
            return self.runner.trace(args)
        except Exception as e:
            self.handle_exception(e)

    def handle_eval(self,args):
        """Evaluate a code snippet specified by args.
        """
        try:
            return self.runner.eval(args)
        except Exception, e:
            self.handle_exception(e)

    def eval_under_cursor(self):
        """Evaluate the property under the cursor.
        """
        try:
            return self.event_dispatcher.eval_under_cursor()
        except Exception, e:
            self.handle_exception(e)

    def save_eval(self,args):
        """Save a code snippet for later display in the watch window.
        """
        try:
            return self.runner.save_code(args)
        except Exception as e:
            self.handle_exception(e)

    def toggle_breakpoint_window(self):
        """Open or close the breakpoint window.
        """
        try:
            return self.runner.toggle_breakpoint_window()
        except Exception, e:
            self.handle_exception(e)

    def set_breakpoint(self,args = None):
        """Set a breakpoint, specified by args.
        """
        try:
            self.runner.set_breakpoint(args)
        except Exception, e:
            self.handle_exception(e)

    def remove_breakpoint(self,args = None):
        """Remove one or more breakpoints, specified by args.
        """
        try:
            self.runner.remove_breakpoint(args)
        except Exception, e:
            self.handle_exception(e)

    def get_context(self):
        """Get all the variables in the default context
        """
        try:
            self.runner.get_context()
        except Exception, e:
            self.handle_exception(e)


    def detach(self):
        """Detach the debugger, so the script runs to the end.
        """
        try:
            self.runner.detach()
            self.runner.close_connection()
        except Exception, e:
            self.handle_exception(e)

    def close(self):
        """Close the connection, or the UI if already closed.
        """
        if self.runner.is_alive():
            self.runner.close_connection()
        else:
            self.runner.close()

    """ Exception handlers """

    def handle_timeout(self):
        """Handle a timeout, which is pretty normal. 
        """
        self.runner.close()
        self.runner.ui.say("No connection was made")

    def handle_interrupt(self):
        """Handle a user interrupt, which is pretty normal. 
        """
        self.runner.close()
        self.runner.ui.say("Connection cancelled")

    def handle_socket_end(self):
        """Handle a socket closing, which is pretty normal.
        """
        self.runner.ui.say("Connection to the debugger has been closed")
        self.runner.close_connection()

    def handle_vim_error(self,e):
        """Handle a VIM error.

        This should NOT occur under normal circumstances.
        """
        self.runner.ui.error("A Vim error occured: "+\
                str(e)+\
                "\n"+ traceback.format_exc())

    def handle_readable_error(self,e):
        """Simply print an error, since it is human readable enough.
        """
        self.runner.ui.error(str(e))

    def handle_dbgp_error(self,e):
        """Simply print an error, since it is human readable enough.
        """
        self.runner.ui.error(str(e.args[0]))

    def handle_general_exception(self):
        """Handle an unknown error of any kind.
        """
        self.runner.ui.error("An error occured: "+\
                str(sys.exc_info()[0])+\
                "\n"+ traceback.format_exc())

    def handle_exception(self,e):
        """Switch on the exception type to work out how to handle it.
        """
        if isinstance(e,vdebug.dbgp.TimeoutError):
            self.handle_timeout()
        elif isinstance(e,vdebug.util.UserInterrupt):
            try:
                self.handle_interrupt()
            except:
                pass
        elif isinstance(e,vdebug.event.EventError):
            self.handle_readable_error(e)
        elif isinstance(e,vdebug.breakpoint.BreakpointError):
            self.handle_readable_error(e)
        elif isinstance(e,vdebug.log.LogError):
            self.handle_readable_error(e)
        elif isinstance(e,vdebug.dbgp.DBGPError):
            self.handle_dbgp_error(e)
        elif isinstance(e,(EOFError,socket.error)):
            self.handle_socket_end()
        elif isinstance(e,KeyboardInterrupt):
            print "Keyboard interrupt - debugging session cancelled"
            try:
                self.runner.close()
            except:
                pass
        else:
            self.handle_general_exception()
        """
        elif isinstance(e,vim.error):
            self.handle_vim_error(e)
        """
