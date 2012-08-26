import _SilverCity
from _SilverCity import *

def get_default_stylesheet_location():
    """get_default_stylesheet_location() => file path

    Returns the path of the default cascading style sheet (CSS) file
    that is installed with the rest of the SilverCity package."""

    import os

    css_file = os.path.join(os.path.dirname(__file__), 'default.css')
    if not os.path.exists(css_file):
        raise Exception('Default CSS file could not be found at %s' % css_file)
    
    return css_file

import LanguageInfo
LanguageInfo.do_registration()
