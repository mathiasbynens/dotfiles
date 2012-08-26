import ScintillaConstants
import Utils

def generate_handler_name(state):
    return 'handle_' + state[4:].lower()
    
class DispatchHandler:
    def __init__(self, state_prefix):
        self.handlers = {}
        if state_prefix is not None:
            for constant in Utils.list_states(state_prefix):
                self.handlers[getattr(ScintillaConstants, constant)] = \
                    generate_handler_name(constant)

    def event_handler(self, style, **kwargs):
        kwargs.update({'style' : style})
        handler = self.handlers.get(style, None)

        if handler is None:
            self.handle_other(**kwargs)
        else:
            getattr(self, handler, self.handle_other)(**kwargs)
