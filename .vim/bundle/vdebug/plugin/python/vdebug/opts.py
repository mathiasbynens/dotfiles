
class Options:
    instance = None

    def __init__(self,options):
        self.options = options
    
    @classmethod
    def set(cls,options):
        """Create an Options instance with the provided dictionary of
        options"""
        cls.instance = Options(options)

    @classmethod
    def inst(cls):
        """Get the Options instance.
        """
        if cls.instance is None:
            raise OptionsError("No options have been set")
        return cls.instance

    @classmethod
    def get(cls,name,as_type = str):
        """Get an option by name.

        Raises an OptionsError if the option doesn't exist.
        """
        inst = cls.inst()
        if name in inst.options:
            return as_type(inst.options[name])
        else:
            raise OptionsError("No option with key '%s'" % name)

    @classmethod
    def get_for_print(cls, name):
        """Get an option by name and for human readable output.

        Raises an OptionsError if the option doesn't exist.
        """
        option = cls.get(name)
        if len(option) == 0:
            return "<empty>"
        else:
            return option


    @classmethod
    def overwrite(cls,name,value):
        inst = cls.inst()
        inst.options[name] = value

    @classmethod
    def isset(cls,name):
        """Checks whether the option exists and is set.

        By set, it means whether the option has length. All the option
        values are strings.
        """
        inst = cls.inst()
        if name in inst.options and \
            len(inst.options[name]) > 0:
            return True
        else:
            return False

class OptionsError(Exception):
    pass

