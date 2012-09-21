# (c) 2005 Divmod, Inc.  See LICENSE file for details

class Message(object):
    message = ''
    message_args = ()
    def __init__(self, filename, lineno):
        self.filename = filename
        self.lineno = lineno
    def __str__(self):
        return '%s:%s: %s' % (self.filename, self.lineno, self.message % self.message_args)


class UnusedImport(Message):
    message = '%r imported but unused'
    def __init__(self, filename, lineno, name):
        Message.__init__(self, filename, lineno)
        self.message_args = (name,)


class RedefinedWhileUnused(Message):
    message = 'redefinition of unused %r from line %r'
    def __init__(self, filename, lineno, name, orig_lineno):
        Message.__init__(self, filename, lineno)
        self.message_args = (name, orig_lineno)


class ImportShadowedByLoopVar(Message):
    message = 'import %r from line %r shadowed by loop variable'
    def __init__(self, filename, lineno, name, orig_lineno):
        Message.__init__(self, filename, lineno)
        self.message_args = (name, orig_lineno)


class ImportStarUsed(Message):
    message = "'from %s import *' used; unable to detect undefined names"
    def __init__(self, filename, lineno, modname):
        Message.__init__(self, filename, lineno)
        self.message_args = (modname,)


class UndefinedName(Message):
    message = 'undefined name %r'
    def __init__(self, filename, lineno, name):
        Message.__init__(self, filename, lineno)
        self.message_args = (name,)



class UndefinedExport(Message):
    message = 'undefined name %r in __all__'
    def __init__(self, filename, lineno, name):
        Message.__init__(self, filename, lineno)
        self.message_args = (name,)



class UndefinedLocal(Message):
    message = "local variable %r (defined in enclosing scope on line %r) referenced before assignment"
    def __init__(self, filename, lineno, name, orig_lineno):
        Message.__init__(self, filename, lineno)
        self.message_args = (name, orig_lineno)


class DuplicateArgument(Message):
    message = 'duplicate argument %r in function definition'
    def __init__(self, filename, lineno, name):
        Message.__init__(self, filename, lineno)
        self.message_args = (name,)


class RedefinedFunction(Message):
    message = 'redefinition of function %r from line %r'
    def __init__(self, filename, lineno, name, orig_lineno):
        Message.__init__(self, filename, lineno)
        self.message_args = (name, orig_lineno)


class LateFutureImport(Message):
    message = 'future import(s) %r after other statements'
    def __init__(self, filename, lineno, names):
        Message.__init__(self, filename, lineno)
        self.message_args = (names,)


class UnusedVariable(Message):
    """
    Indicates that a variable has been explicity assigned to but not actually
    used.
    """

    message = 'local variable %r is assigned to but never used'
    def __init__(self, filename, lineno, names):
        Message.__init__(self, filename, lineno)
        self.message_args = (names,)
