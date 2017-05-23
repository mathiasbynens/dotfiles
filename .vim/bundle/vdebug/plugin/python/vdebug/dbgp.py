import sys
if sys.hexversion >= 0x02050000:
    import xml.etree.ElementTree as ET
else:
    import elementtree.ElementTree as ET
import socket
import vdebug.log
import base64
import time

""" Response objects for the DBGP module."""

class Response:
    """Contains response data from a command made to the debugger."""
    ns = '{urn:debugger_protocol_v1}'

    def __init__(self,response,cmd,cmd_args,api):
        self.response = response
        self.cmd = cmd
        self.cmd_args = cmd_args
        self.xml = None
        self.api = api
        if "<error" in self.response:
            self.__parse_error()

    def __parse_error(self):
        """Parse an error message which has been returned
        in the response, then raise it as a DBGPError."""
        xml = self.as_xml()
        err_el = xml.find('%serror' % self.ns)
        if err_el is None:
            raise DBGPError("Could not parse error from return XML",1)
        else:
            code = err_el.get("code")
            if code is None:
                raise ResponseError(
                        "Missing error code in response",
                        self.response)
            elif int(code) == 4:
                raise CmdNotImplementedError('Command not implemented')
            msg_el = err_el.find('%smessage' % self.ns)
            if msg_el is None:
                raise ResponseError(
                        "Missing error message in response",
                        self.response)
            raise DBGPError(msg_el.text,code)

    def get_cmd(self):
        """Get the command that created this response."""
        return self.cmd

    def get_cmd_args(self):
        """Get the arguments to the command."""
        return self.cmd_args

    def as_string(self):
        """Return the full response as a string.

        There is a __str__ method, which will render the
        whole object as a string and should be used for
        displaying.
        """
        return self.response

    def as_xml(self):
        """Get the response as element tree XML.

        Returns an xml.etree.ElementTree.Element object.
        """
        if self.xml == None:
            self.xml = ET.fromstring(self.response)
            self.__determine_ns()
        return self.xml

    def __determine_ns(self):
        tag_repr = str(self.xml.tag)
        if tag_repr[0] != '{':
            raise DBGPError('Invalid or missing XML namespace',1)
        else:
            ns_parts = tag_repr.split('}')
            self.ns = ns_parts[0] + '}'

    def __str__(self):
        return self.as_string()

class ContextNamesResponse(Response):
    def names(self):
        names = {}
        for c in list(self.as_xml()):
            names[int(c.get('id'))] = c.get('name')
        return names

class TraceResponse(Response):
    """Response object returned by the trace command."""

    def __str__(self):
        return self.as_xml().get('trace')


class StatusResponse(Response):
    """Response object returned by the status command."""

    def __str__(self):
        return self.as_xml().get('status')

class StackGetResponse(Response):
    """Response object used by the stack_get command."""

    def get_stack(self):
        return list(self.as_xml())

class ContextGetResponse(Response):
    """Response object used by the context_get command.

    The property nodes are converted into ContextProperty
    objects, which are much easier to use."""

    def __init__(self,response,cmd,cmd_args,api):
        Response.__init__(self,response,cmd,cmd_args,api)
        self.properties = []

    def get_context(self):
        for c in list(self.as_xml()):
            self.create_properties(ContextProperty(c))

        return self.properties

    def create_properties(self,property):
        self.properties.append(property)
        for p in property.children:
            self.create_properties(p)

class EvalResponse(ContextGetResponse):
    """Response object returned by the eval command."""
    def __init__(self,response,cmd,cmd_args,api):
        try:
            ContextGetResponse.__init__(self,response,cmd,cmd_args,api)
        except DBGPError, e:
            if int(e.args[1]) == 206:
                raise EvalError()
            else:
                raise e

    def get_context(self):
        code = self.get_code()
        for c in list(self.as_xml()):
            self.create_properties(EvalProperty(c,code,self.api.language))

        return self.properties

    def get_code(self):
        cmd = self.get_cmd_args()
        parts = cmd.split('-- ')
        return base64.decodestring(parts[1])


class BreakpointSetResponse(Response):
    """Response object returned by the breakpoint_set command."""

    def get_id(self):
        return int(self.as_xml().get('id'))

    def __str__(self):
        return self.as_xml().get('id')

class FeatureGetResponse(Response):
    """Response object specifically for the feature_get command."""

    def is_supported(self):
        """Whether the feature is supported or not."""
        xml = self.as_xml()
        return int(xml.get('supported'))

    def __str__(self):
        if self.is_supported():
            xml = self.as_xml()
            return xml.text
        else:
            return "* Feature not supported *"

class Api:
    """Api for eBGP commands.

    Uses a Connection object to read and write with the debugger,
    and builds commands and returns the results.
    """

    conn = None
    transID = 0

    def __init__(self,connection):
        """Create a new Api using a Connection object.

        The Connection object specifies the debugger connection,
        and the Protocol provides a OO api to interacting
        with it.

        connection -- The Connection object to use
        """
        self.language = None
        self.protocol = None
        self.idekey = None
        self.startfile = None
        self.conn = connection
        if self.conn.isconnected() == 0:
            self.conn.open()
        self.__parse_init_msg(self.conn.recv_msg())

    def __parse_init_msg(self,msg):
        """Parse the init message from the debugger"""
        xml = ET.fromstring(msg)
        self.language = xml.get("language")
        if self.language is None:
            raise ResponseError(
                "Invalid XML response from debugger",
                msg)
        self.language = self.language.lower()
        self.idekey = xml.get("idekey")
        self.version = xml.get("api_version")
        self.startfile = xml.get("fileuri")

    def send_cmd(self,cmd,args = '',
            res_cls = Response):
        """Send a command to the debugger.

        This method automatically adds a unique transaction
        ID to the command which is required by the debugger.

        Returns a Response object, which contains the
        response message and command.

        cmd -- the command name, e.g. 'status'
        args -- arguments for the command, which is optional 
                for certain commands (default '')
        """
        args = args.strip()
        send = cmd.strip()
        self.transID += 1
        send += ' -i '+ str(self.transID)
        if len(args) > 0:
            send += ' ' + args
        vdebug.log.Log("Command: "+send,\
                vdebug.log.Logger.DEBUG)
        self.conn.send_msg(send)
        msg = self.conn.recv_msg()
        vdebug.log.Log("Response: "+msg,\
                vdebug.log.Logger.DEBUG)
        return res_cls(msg,cmd,args,self)

    def status(self):
        """Get the debugger status.

        Returns a Response object.
        """
        return self.send_cmd('status','',StatusResponse)

    def feature_get(self,name):
        """Get the value of a feature from the debugger.

        See the DBGP documentation for a list of features.

        Returns a FeatureGetResponse object.

        name -- name of the feature, e.g. encoding
        """
        return self.send_cmd(
                'feature_get',
                '-n '+str(name),
                FeatureGetResponse)

    def feature_set(self,name,value):
        """Set the value of a debugger feature.

        See the DBGP documentation for a list of features.

        Returns a Response object.

        name -- name of the feature, e.g. encoding
        value -- new value for the feature
        """
        return self.send_cmd(
                'feature_set',
                '-n ' + str(name) + ' -v ' + str(value))

    def run(self):
        """Tell the debugger to start or resume
        execution."""
        return self.send_cmd('run','',StatusResponse)

    def eval(self,code):
        """Tell the debugger to start or resume
        execution."""
        code_enc = base64.encodestring(code)
        args = '-- %s' % code_enc

        """ The python engine incorrectly requires length.
        if self.language == 'python':
            args = ("-l %i " % len(code_enc) ) + args"""
            
        return self.send_cmd('eval',args,EvalResponse)

    def step_into(self):
        """Tell the debugger to step to the next
        statement.

        If there's a function call, the debugger engine
        will break on the first statement in the function.
        """
        return self.send_cmd('step_into','',StatusResponse)

    def step_over(self):
        """Tell the debugger to step to the next
        statement.

        If there's a function call, the debugger engine
        will stop at the next statement after the function call.
        """
        return self.send_cmd('step_over','',StatusResponse)

    def step_out(self):
        """Tell the debugger to step out of the statement.

        The debugger will step out of the current scope.
        """
        return self.send_cmd('step_out','',StatusResponse)

    def stop(self):
        """Tell the debugger to stop execution.

        The script is terminated immediately."""
        return self.send_cmd('stop','',StatusResponse)

    def stack_get(self):
        """Get the stack information.
        """
        return self.send_cmd('stack_get','',StackGetResponse)

    def context_get(self,context = 0):
        """Get the context variables.
        """
        return self.send_cmd('context_get',\
                '-c %i' % int(context),\
                ContextGetResponse)

    def context_names(self):
        """Get the context types.
        """
        return self.send_cmd('context_names','',ContextNamesResponse)

    def property_get(self,name):
        """Get a property.
        """
        return self.send_cmd('property_get','-n %s -d 0' % name,ContextGetResponse)

    def detach(self):
        """Tell the debugger to detach itself from this
        client.

        The script is not terminated, but runs as normal
        from this point."""
        ret = self.send_cmd('detach','',StatusResponse)
        self.conn.close()
        return ret

    def breakpoint_set(self,cmd_args):
        """Set a breakpoint.

        The breakpoint type is defined by the arguments, see the
        Breakpoint class for more detail."""
        return self.send_cmd('breakpoint_set',cmd_args,\
                BreakpointSetResponse)

    def breakpoint_list(self):
        return self.send_cmd('breakpoint_list')

    def breakpoint_remove(self,id):
        """Remove a breakpoint by ID.

        The ID is that returned in the response from breakpoint_set."""
        return self.send_cmd('breakpoint_remove','-d %i' % id,Response)

"""Connection module for managing a socket connection
between this client and the debugger."""

class Connection:
    """DBGP connection class, for managing the connection to the debugger.

    The host, port and socket timeout are configurable on object construction.
    """

    sock = None
    address = None
    isconned = 0

    def __init__(self, host = '', port = 9000, timeout = 30, input_stream = None):
        """Create a new Connection.

        The connection is not established until open() is called.

        host -- host name where debugger is running (default '')
        port -- port number which debugger is listening on (default 9000)
        timeout -- time in seconds to wait for a debugger connection before giving up (default 30)
        input_stream -- object for checking input stream and user interrupts (default None)
        """
        self.port = port
        self.host = host
        self.timeout = timeout
        self.input_stream = input_stream

    def __del__(self):
        """Make sure the connection is closed."""
        self.close()

    def isconnected(self):
        """Whether the connection has been established."""
        return self.isconned

    def open(self):
        """Listen for a connection from the debugger. Listening for the actual
        connection is handled by self.listen()."""
        print 'Waiting for a connection (Ctrl-C to cancel, this message will self-destruct in ',self.timeout,' seconds...)'
        serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            serv.setblocking(0)
            serv.bind((self.host, self.port))
            serv.listen(5)
            (self.sock, self.address) = self.listen(serv, self.timeout)
            self.sock.settimeout(None)
        except socket.timeout:
            serv.close()
            raise TimeoutError("Timeout waiting for connection")
        except:
            serv.close()
            raise

        self.isconned = 1
        serv.close()

    def listen(self, serv, timeout):
        """Non-blocking listener. Provides support for keyboard interrupts from
        the user. Although it's non-blocking, the user interface will still
        block until the timeout is reached.

        serv -- Socket server to listen to.
        timeout -- Seconds before timeout.
        """
        start = time.time()
        while True:
            if (time.time() - start) > timeout:
                raise socket.timeout
            try:
                """Check for user interrupts"""
                if self.input_stream is not None:
                    self.input_stream.probe()
                return serv.accept()
            except socket.error:
                pass

    def close(self):
        """Close the connection."""
        if self.sock != None:
            vdebug.log.Log("Closing the socket",\
                            vdebug.log.Logger.DEBUG)
            self.sock.close()
            self.sock = None
        self.isconned = 0

    def __recv_length(self):
        """Get the length of the proceeding message."""
        length = ''
        while 1:
            c = self.sock.recv(1)
            if c == '':
                self.close()
                raise EOFError('Socket Closed')
            if c == '\0':
                return int(length)
            if c.isdigit():
                length = length + c

    def __recv_null(self):
        """Receive a null byte."""
        while 1:
            c = self.sock.recv(1)
            if c == '':
                self.close()
                raise EOFError('Socket Closed')
            if c == '\0':
                return

    def __recv_body(self, to_recv):
        """Receive a message of a given length.

        to_recv -- length of the message to receive
        """
        body = ''
        while to_recv > 0:
            buf = self.sock.recv(to_recv)
            if buf == '':
                self.close()
                raise EOFError('Socket Closed')
            to_recv -= len(buf)
            body = body + buf
        return body

    def recv_msg(self):
        """Receive a message from the debugger.

        Returns a string, which is expected to be XML.
        """
        length = self.__recv_length()
        body     = self.__recv_body(length)
        self.__recv_null()
        return body

    def send_msg(self, cmd):
        """Send a message to the debugger.

        cmd -- command to send
        """
        self.sock.send(cmd + '\0')

class ContextProperty:

    ns = '{urn:debugger_protocol_v1}'

    def __init__(self,node,parent = None,depth = 0):
        self.parent = parent
        self.__determine_type(node)
        self._determine_displayname(node)
        self.encoding = node.get('encoding')
        self.depth = depth

        self.size = node.get('size')
        self.value = ""
        self.is_last_child = False

        self._determine_children(node)
        self.__determine_value(node)
        self.__init_children(node)
        if self.type == 'scalar':
            self.size = len(self.value) - 2

    def __determine_value(self,node):
        if self.has_children:
            self.value = ""
            return

        self.value = self._get_enc_node_text(node,'value')
        if self.value is None:
            if self.encoding == 'base64':
                if node.text is None:
                    self.value = ""
                else:
                    self.value = base64.decodestring(node.text)
            elif not self.is_uninitialized() \
                    and not self.has_children:
                self.value = node.text

        if self.value is None:
            self.value = ""

        self.num_crs = self.value.count('\n')
        if self.type.lower() in ("string","str","scalar"):
            self.value = '`%s`' % self.value.replace('`','\\`')

    def __determine_type(self,node):
        type = node.get('classname')
        if type is None:
            type = node.get('type')
        if type is None:
            type = 'unknown'
        self.type = type

    def _determine_displayname(self,node):
        display_name = node.get('fullname')
        if display_name == None:
            display_name = self._get_enc_node_text(node,'fullname',"")
        if display_name == '::':
            display_name = self.type
        self.display_name = display_name

    def _get_enc_node_text(self,node,name,default =
            None):
        n = node.find('%s%s' %(self.ns, name))
        if n is not None and n.text is not None:
            if n.get('encoding') == 'base64':
                val = base64.decodestring(n.text)
            else:
                val = n.text
        else:
            val = None
        if val is None:
            return default
        else:
            return val

    def _determine_children(self,node):
        children = node.get('numchildren')
        if children is None:
            children = node.get('children')
        if children is None:
            children = 0
        else:
            children = int(children)
        self.num_declared_children = children
        self.has_children = children > 0
        self.children = []

    def __init_children(self,node):
        if self.has_children:
            idx = 0
            tagname = '%sproperty' % self.ns
            children = list(node)
            if children is not None:
                for c in children:
                    if c.tag == tagname:
                        idx += 1
                        p = self._create_child(c,self,self.depth+1)
                        self.children.append(p)
                        if idx == self.num_declared_children:
                            p.mark_as_last_child()

    def _create_child(self,node,parent,depth):
        return ContextProperty(node,parent,depth)

    def mark_as_last_child(self):
        self.is_last_child = True

    def is_uninitialized(self):
        if self.type == 'uninitialized':
            return True
        else:
            return False

    def child_count(self):
        return len(self.children)

    def type_and_size(self):
        size = None
        if self.has_children:
            size = self.num_declared_children
        elif self.size is not None:
            size = self.size

        if size is None:
            return self.type
        else:
            return "%s [%s]" %(self.type,size)

class EvalProperty(ContextProperty):
    def __init__(self,node,code,language,parent=None,depth=0):
        self.code = code
        self.language = language.lower()
        if parent is None:
            self.is_parent = True
        else:
            self.is_parent = False
        ContextProperty.__init__(self,node,parent,depth)

    def _create_child(self,node,parent,depth):
        return EvalProperty(node,self.code,self.language,parent,depth)

    def _determine_displayname(self,node):
        if self.is_parent:
            self.display_name = self.code
        else:
            if self.language == 'php' or \
                    self.language == 'perl':
                if self.parent.type == 'array':
                    if node.get('name').isdigit():
                        self.display_name = self.parent.display_name + \
                            "[%s]" % node.get('name')
                    else:
                        self.display_name = self.parent.display_name + \
                            "['%s']" % node.get('name')
                else:
                    self.display_name = self.parent.display_name + \
                        "->"+node.get('name')
            else:
                name = node.get('name')
                if name is None:
                    name = "?"
                    name = self._get_enc_node_text(node,'name','?')
                if self.parent.type == 'list':
                    self.display_name = self.parent.display_name + name
                else:
                    self.display_name = self.parent.display_name + \
                        "." + name


""" Errors/Exceptions """
class TimeoutError(Exception):
    pass

class DBGPError(Exception):
    """Raised when the debugger returns an error message."""
    pass

class CmdNotImplementedError(Exception):
    """Raised when the debugger returns an error message."""
    pass

class EvalError(Exception):
    """Raised when some evaluated code is invalid."""
    pass

class ResponseError(Exception):
    """An error caused by an unexpected response from the
    debugger (e.g. invalid format XML)."""
    pass

class TraceError(Exception):
    """Raised when trace is out of domain."""
    pass
