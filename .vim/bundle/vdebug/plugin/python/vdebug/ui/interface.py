class Ui:
    """Abstract for the UI, used by the debugger
    """
    watchwin  = None
    stackwin  = None
    statuswin = None
    logwin    = None
    sourcewin = None
    tracewin  = None

    def __init__(self):
        self.is_open = False

    def __del__(self):
        self.close()

    def open(self):
        pass

    def say(self,string):
        pass

    def close(self):
        pass

    def log(self):
        pass

class Window:
    """Abstract for UI windows
    """
    name = "WINDOW"
    is_open = False

    def __del__(self):
        self.destroy()

    def on_create(self):
        """ Callback for after the window is created """
        pass

    def on_destroy(self):
        """ Callback for after the window is destroyed """
        pass

    def create(self):
        """ Create the window """
        pass

    def write(self, msg):
        """ Write string in the window """
        pass

    def insert(self, msg, position = None):
        """ Insert a string somewhere in the window """
        pass

    def destroy(self):
        """ Close window """
        pass

    def clean(self):
        """ clean all data in buffer """
        pass
