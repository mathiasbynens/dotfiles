import ScintillaConstants

def list_states(state_prefix):
    """list_states("SCE_P_") => ['SCE_P_DEFAULT', 'SCE_P_COMMENTLINE', ...]

    Return a list of Scintilla constants beginning with the given prefix.
    """
    return [constant for constant in dir(ScintillaConstants)
                if constant.startswith(state_prefix)]
